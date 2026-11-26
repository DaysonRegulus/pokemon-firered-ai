from collections import deque
import numpy as np
from skimage.metrics import structural_similarity as ssim


# =====================================================================
# MATHEMATICALLY CALIBRATED MILESTONE REGISTRY
# Only macro-geographic milestones and major landmarks are rewarded.
# Trivial interiors (bedrooms, NPC houses, gatehouses) yield 0.0 to prevent
# artificial handholding and preserve balance with combat (+10) and RND signals.
# =====================================================================
MILESTONE_MAP_REWARDS = {
    # 1. Starting Settlement Exit (Outdoor Breakthrough)
    (3, 0): (10.0, "Pallet Town Overworld"),

    # 2. Overland Routes
    (3, 19): (20.0, "Route 1"),
    (3, 40): (20.0, "Route 22"),
    (3, 20): (30.0, "Route 2"),
    (3, 21): (40.0, "Route 3"),
    (3, 22): (40.0, "Route 4"),
    (3, 23): (40.0, "Route 5"),
    (3, 24): (40.0, "Route 6"),
    (3, 25): (40.0, "Route 7"),
    (3, 26): (40.0, "Route 8"),
    (3, 27): (50.0, "Route 9"),
    (3, 28): (50.0, "Route 10"),
    (3, 29): (50.0, "Route 11"),
    (3, 30): (50.0, "Route 12"),
    (3, 31): (50.0, "Route 13"),
    (3, 32): (50.0, "Route 14"),
    (3, 33): (50.0, "Route 15"),
    (3, 34): (50.0, "Route 16"),
    (3, 35): (50.0, "Route 17"),
    (3, 36): (50.0, "Route 18"),
    (3, 37): (50.0, "Route 19"),
    (3, 38): (50.0, "Route 20"),
    (3, 39): (50.0, "Route 21"),
    (3, 41): (60.0, "Route 23"),
    (3, 42): (40.0, "Route 24"),
    (3, 43): (40.0, "Route 25"),

    # 3. Major Cities & Regional Hubs
    (3, 1): (50.0, "Viridian City"),
    (3, 2): (100.0, "Pewter City"),
    (3, 3): (120.0, "Cerulean City"),
    (3, 4): (150.0, "Vermilion City"),
    (3, 5): (150.0, "Lavender Town"),
    (3, 6): (180.0, "Celadon City"),
    (3, 7): (200.0, "Fuchsia City"),
    (3, 8): (250.0, "Cinnabar Island"),
    (3, 10): (220.0, "Saffron City"),
    (3, 9): (300.0, "Indigo Plateau"),

    # 4. Major Dungeons & Complex Labyrinths
    (1, 0): (30.0, "Viridian Forest"),
    (1, 1): (40.0, "Mt. Moon (1F)"),
    (1, 2): (40.0, "Mt. Moon (B1F)"),
    (1, 3): (40.0, "Mt. Moon (B2F)"),
    (1, 4): (50.0, "Rock Tunnel (1F)"),
    (1, 5): (50.0, "Rock Tunnel (B1F)"),
    (1, 6): (50.0, "Pokémon Tower (1F)"),
    (1, 13): (60.0, "Seafoam Islands (1F)"),
    (1, 18): (80.0, "Victory Road (1F)"),
    (1, 22): (30.0, "Diglett's Cave"),

    # 5. Major Gym Arenas (Entering the Gym Challenge)
    (6, 2): (25.0, "Pewter Gym (Brock Arena)"),
    (5, 1): (50.0, "Viridian Gym Arena"),
}

# 6. Gym Leader Defeat Badges (Scaled from +250.0 for Brock to +600.0 for Giovanni)
BADGE_REWARDS = [
    (250.0, "Boulder Badge (Brock - Pewter Gym)"),
    (300.0, "Cascade Badge (Misty - Cerulean Gym)"),
    (350.0, "Thunder Badge (Lt. Surge - Vermilion Gym)"),
    (400.0, "Rainbow Badge (Erika - Celadon Gym)"),
    (450.0, "Soul Badge (Koga - Fuchsia Gym)"),
    (500.0, "Marsh Badge (Sabrina - Saffron Gym)"),
    (550.0, "Volcano Badge (Blaine - Cinnabar Gym)"),
    (600.0, "Earth Badge (Giovanni - Viridian Gym)"),
]


class ScreenshotManager:
    def __init__(self, max_bank_size=1000, similarity_threshold=0.1, verbosity=True):
        self.reference_bank = deque(maxlen=max_bank_size)
        self.similarity_threshold = similarity_threshold
        self.verbosity = verbosity

    def is_new_location(self, screenshot):
        """
        Compare the screenshot with reference bank to check if it's a new location.
        """
        for reference in self.reference_bank:
            similarity = ssim(screenshot, reference, win_size=7, channel_axis=-1)
            if similarity > self.similarity_threshold:
                return False
        return True

    def add_to_bank(self, screenshot):
        """
        Add the screenshot to the reference bank.
        """
        self.reference_bank.append(screenshot)
        if self.verbosity:
            print(f"[INFO][SCREENSHOT] New location added to bank. Bank size: {len(self.reference_bank)}")


class RewardManager:
    def __init__(
        self,
        env,
        screenshot_manager,
        exploration_mode="SSIM",
        exploration_multiplier=1,
        hp_oppn_multiplier=1,
        hp_loss_multiplier=1,
        hp_heal_multiplier=1,
        level_gain_multiplier=10,
        frame_skip=5,
    ):
        self.env = env
        self.exploration_mode = exploration_mode
        self.screenshot_manager = screenshot_manager if exploration_mode == "LEGACY_SSIM" else None

        # State tracking
        self.prev_party_hp = [0] * 6
        self.prev_oppn_hp = [0] * 6
        self.prev_total_hp = 0
        self.prev_party_lvl = [0] * 6
        self.prev_oppn_lvl = [0] * 6  # Tracking all opponent Pokémon
        self.pending_faint = [False] * 6

        # Flags and settings
        self.initialized = False
        self.frame_skip = frame_skip
        self.frame_count = 0
        self.faint_count_this_step = 0  # Variable to communicate with Env Wrapper

        # Multipliers
        self.exploration_multiplier = exploration_multiplier
        self.hp_oppn_multiplier = hp_oppn_multiplier
        self.hp_loss_multiplier = hp_loss_multiplier
        self.hp_heal_multiplier = hp_heal_multiplier
        self.level_gain_multiplier = level_gain_multiplier

        # Milestone tracking (calibrated, no handholding)
        self.visited_maps = set()
        self.awarded_badges = set()
        self.prev_badge_byte = 0

        self.verbosity = {
            'hp': True,
            'faint': True,
            'exploration': False,
            'general': True,
            'milestone': True,
        }

        BASE = 0x02000000

        self.hp_addresses = [
            0x20242DA - BASE,
            0x202433E - BASE,
            0x20243A2 - BASE,
            0x2024406 - BASE,
            0x202446A - BASE,
            0x20244CE - BASE,
        ]

        self.lvl_addresses = [
            0x20242D8 - BASE,
            0x202433C - BASE,
            0x20243A0 - BASE,
            0x2024404 - BASE,
            0x2024468 - BASE,
            0x20244CC - BASE,
        ]

        self.oppn_hp_addresses = [
            0x2024082 - BASE,
            0x20240E6 - BASE,
            0x202414A - BASE,
            0x20241AE - BASE,
            0x2024212 - BASE,
            0x2024276 - BASE,
        ]

        self.oppn_lvl_addresses = [
            0x2024080 - BASE,
            0x20240E4 - BASE,
            0x2024148 - BASE,
            0x20241AC - BASE,
            0x2024210 - BASE,
            0x2024274 - BASE,
        ]

    def _is_valid_overworld_sb1(self, ram, sb1_ptr):
        """
        Verifies GBA is in overworld callback (cb2 == 0x080565C9) and sb1_ptr points
        inside valid EWRAM SaveBlock1 bounds with FLAG_SYS_POKEMON_GET active.
        Prevents phantom badge reads during non-overworld transitions or DMA shifts.
        """
        if not (0x20000 <= sb1_ptr < len(ram) - 0x1000):
            return False
        cb2 = int.from_bytes(ram[0x430F4:0x430F8], "little")
        if cb2 != 0x080565C9:
            return False
        sys_flags_byte = int(ram[sb1_ptr + 0xEE0 + 261])
        return bool(sys_flags_byte & 0x01)

    def initialize(self):
        ram = self.env.unwrapped.get_ram()
        BASE = 0x02000000
        self.prev_party_hp = [self.get_hp(ram, i) for i in range(6)]
        self.prev_oppn_hp = [self.get_oppn_hp(ram, i) for i in range(6)]
        self.prev_total_hp = sum(self.prev_party_hp)
        self.prev_party_lvl = [self.get_lvl(ram, i) for i in range(6)]
        self.prev_oppn_lvl = [self.get_oppn_lvl(ram, i) for i in range(6)]
        self.prev_total_lvl = sum(l for l in self.prev_party_lvl if 0 < l <= 100)
        self.prev_party_count = sum(1 for l in self.prev_party_lvl if 0 < l <= 100)
        self.prev_fainted_count = sum(
            1 for hp, l in zip(self.prev_party_hp, self.prev_party_lvl) if 0 < l <= 100 and hp == 0
        )
        self.pending_faint = [False] * 6
        self.faint_count_this_step = 0

        # Initialize spawn map to prevent false discovery on initial frame
        spawn_bank = int(ram[0x02031DBC - BASE])
        spawn_num = int(ram[0x02031DBD - BASE])
        self.visited_maps = {(spawn_bank, spawn_num)}

        # Initialize existing badges to prevent false re-rewarding
        sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], "little") - BASE
        if self._is_valid_overworld_sb1(ram, sb1_ptr):
            self.prev_badge_byte = int(ram[sb1_ptr + 0xEE0 + 260])
            self.awarded_badges = {i for i in range(8) if (self.prev_badge_byte & (1 << i))}
        else:
            self.prev_badge_byte = 0
            self.awarded_badges = set()

        self.initialized = True

    def capture_screenshot(self, obs):
        """
        Capture the current screenshot from the observation.
        The observation from the environment contains the frame data.
        """
        return obs

    def get_hp(self, ram, index):
        addr = self.hp_addresses[index]
        return int(ram[addr]) | (int(ram[addr + 1]) << 8)

    def get_lvl(self, ram, index):
        addr = self.lvl_addresses[index]
        return int(ram[addr])

    def get_oppn_hp(self, ram, index):
        addr = self.oppn_hp_addresses[index]
        return int(ram[addr]) | (int(ram[addr + 1]) << 8)

    def get_oppn_lvl(self, ram, index):
        addr = self.oppn_lvl_addresses[index]
        return int(ram[addr])

    def calculate_avg_level(self, levels):
        valid_levels = [lvl for lvl in levels if 0 < lvl <= 100]
        return sum(valid_levels) / len(valid_levels) if valid_levels else 0

    def get_level_multiplier(self, player_avg, opponent_avg):
        """Calculates the multiplier `z` based on average level comparison."""
        if opponent_avg <= player_avg - 4:
            return 0
        elif opponent_avg <= player_avg - 2:
            return 0.5
        elif opponent_avg >= player_avg + 4:
            return 2
        elif opponent_avg <= player_avg:
            return 1
        elif opponent_avg > player_avg:
            return 1.5
        return 1

    def calculate_rewards(self):
        if not self.initialized:
            self.initialize()
            return 0

        self.frame_count += 1
        if self.frame_count % self.frame_skip != 0:
            return 0  # Skip reward calculation for this frame

        ram = self.env.unwrapped.get_ram()
        total_reward = 0

        self.faint_count_this_step = 0

        # Capture and process exploration reward (legacy in-env method)
        if self.exploration_mode == "LEGACY_SSIM" and self.screenshot_manager is not None:
            screenshot = self.capture_screenshot(self.env.unwrapped.get_screen())
            if self.screenshot_manager.is_new_location(screenshot):
                self.screenshot_manager.add_to_bank(screenshot)
                total_reward += self.exploration_multiplier
                if self.verbosity['exploration']:
                    print(f"[REWARD][EXPLORATION] New location discovered (+{self.exploration_multiplier:.2f})")

        # Retrieve party/opponent levels & counts (order-invariant across slot swaps)
        current_party_lvl = [self.get_lvl(ram, i) for i in range(6)]
        valid_party_lvls = [lvl for lvl in current_party_lvl if 0 < lvl <= 100]
        curr_party_count = len(valid_party_lvls)
        current_total_lvl = sum(valid_party_lvls)
        current_oppn_lvl = [self.get_oppn_lvl(ram, i) for i in range(6)]
        player_avg_level = self.calculate_avg_level(current_party_lvl)
        opponent_avg_level = self.calculate_avg_level(current_oppn_lvl)

        # Compute scaling multiplier
        faint_multiplier = self.get_level_multiplier(player_avg_level, opponent_avg_level)

        # Calculate HP rewards and penalties
        current_party_hp = [self.get_hp(ram, i) for i in range(6)]
        current_total_hp = sum(current_party_hp)
        current_oppn_hp = [self.get_oppn_hp(ram, i) for i in range(6)]
        curr_fainted_count = sum(
            1 for hp, lvl in zip(current_party_hp, current_party_lvl) if 0 < lvl <= 100 and hp == 0
        )

        # Check for fainted Pokémon (party-order invariant: prevents slot-swap faint spam)
        if curr_party_count == self.prev_party_count and curr_fainted_count > self.prev_fainted_count:
            newly_fainted = curr_fainted_count - self.prev_fainted_count
            total_reward -= 5 * newly_fainted
            if self.verbosity['faint']:
                print(f"[PENALTY][FAINT] {newly_fainted} party Pokémon fainted (-{5 * newly_fainted})")

        # --- Opponent Fainting Check ---
        for i in range(6):
            if (
                self.prev_oppn_hp[i] > 0
                and current_oppn_hp[i] == 0
                and self.prev_oppn_lvl[i] > 0
                and current_oppn_lvl[i] > 0
            ):
                self.pending_faint[i] = True

            elif self.pending_faint[i]:
                if current_oppn_hp[i] == 0:
                    # Reward for fainting an opponent Pokémon
                    faint_reward = 10 * faint_multiplier
                    total_reward += faint_reward
                    self.faint_count_this_step += 1  # Increment counter for logging

                    if self.verbosity['faint']:
                        print(f"[REWARD][FAINT] Opponent Pokémon fainted (+{faint_reward})")
                        print(f"[DEBUG][FAINT] Average Party Level: {player_avg_level}; Average Opponent Level: {opponent_avg_level}")
                        print(
                            f"[DEBUG][PENDING] prev_hp={self.prev_oppn_hp[i]} "
                            f"curr_hp={current_oppn_hp[i]} "
                            f"prev_lvl={self.prev_oppn_lvl[i]} "
                            f"curr_lvl={current_oppn_lvl[i]}"
                        )

                    # prevent repeated faint triggers
                    self.prev_oppn_hp[i] = 0

                self.pending_faint[i] = False

        # --- Level Gain Reward (party-order invariant: prevents [5, 3] <-> [3, 5] swap farming) ---
        if curr_party_count == self.prev_party_count and curr_party_count > 0:
            level_diff = current_total_lvl - self.prev_total_lvl
            if 0 < level_diff <= 10:
                total_reward += level_diff * self.level_gain_multiplier
                if self.verbosity['general']:
                    print(f"[REWARD][LEVEL] Total party level increased by {level_diff} (+{level_diff * self.level_gain_multiplier:.2f})")

        # --- New Pokémon Catch Reward ---
        if self.prev_party_count > 0 and curr_party_count > self.prev_party_count:
            newly_caught = curr_party_count - self.prev_party_count
            total_reward += 10 * newly_caught
            if self.verbosity['general']:
                print(f"[REWARD][CATCH] {newly_caught} new Pokémon caught (+{10 * newly_caught})")

        # --- Mathematically Calibrated Milestone Rewards (No Handholding, Scaled to Combat/RND Signals) ---
        BASE = 0x02000000
        current_map_bank = int(ram[0x02031DBC - BASE])
        current_map_num = int(ram[0x02031DBD - BASE])
        current_map = (current_map_bank, current_map_num)

        if current_map not in self.visited_maps:
            self.visited_maps.add(current_map)
            # Only reward legitimate macro milestones in the registry.
            # Trivial interiors (bedrooms, random NPC houses, gatehouses) yield 0.0 to prevent handholding.
            if current_map in MILESTONE_MAP_REWARDS:
                reward_val, area_name = MILESTONE_MAP_REWARDS[current_map]
                total_reward += reward_val
                if self.verbosity.get('milestone', True):
                    print(f"[MILESTONE][DISCOVERY] Milestone Reached: {area_name} (+{reward_val:.1f})")

        # --- Massive Milestone: Defeating Gym Leaders / Winning Gym Badges (+250.0 to +600.0) ---
        sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], "little") - BASE
        if self._is_valid_overworld_sb1(ram, sb1_ptr):
            current_badge_byte = int(ram[sb1_ptr + 0xEE0 + 260])
            for b_idx in range(8):
                if (current_badge_byte & (1 << b_idx)) and (b_idx not in self.awarded_badges):
                    self.awarded_badges.add(b_idx)
                    badge_reward, badge_name = BADGE_REWARDS[b_idx]
                    total_reward += badge_reward
                    if self.verbosity.get('milestone', True):
                        print(f"[MILESTONE][GYM_LEADER] Defeated Gym Leader! Earned {badge_name} (+{badge_reward:.1f})")
            self.prev_badge_byte = current_badge_byte

        # Store new values
        self.prev_party_hp = current_party_hp
        self.prev_total_hp = current_total_hp
        self.prev_oppn_hp = current_oppn_hp
        self.prev_party_lvl = current_party_lvl
        self.prev_total_lvl = current_total_lvl
        self.prev_party_count = curr_party_count
        self.prev_fainted_count = curr_fainted_count
        self.prev_oppn_lvl = current_oppn_lvl

        return total_reward

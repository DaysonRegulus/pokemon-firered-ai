from collections import deque
import numpy as np
from skimage.metrics import structural_similarity as ssim


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

        self.verbosity = {
            'hp': True,
            'faint': True,
            'exploration': False,
            'general': True,
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
            0x20242D7 - BASE,
            0x202433B - BASE,
            0x202439F - BASE,
            0x2024403 - BASE,
            0x2024467 - BASE,
            0x20244CB - BASE,
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
            0x202407F - BASE,
            0x20240E3 - BASE,
            0x2024147 - BASE,
            0x20241AB - BASE,
            0x202420F - BASE,
            0x2024273 - BASE,
        ]

    def initialize(self):
        ram = self.env.unwrapped.get_ram()
        self.prev_party_hp = [self.get_hp(ram, i) for i in range(6)]
        self.prev_oppn_hp = [self.get_oppn_hp(ram, i) for i in range(6)]
        self.prev_total_hp = sum(self.prev_party_hp)
        self.prev_party_lvl = [self.get_lvl(ram, i) for i in range(6)]
        self.prev_oppn_lvl = [self.get_oppn_lvl(ram, i) for i in range(6)]
        self.prev_total_lvl = sum(self.prev_party_lvl)
        self.initialized = True

    def capture_screenshot(self, obs):
        """
        Capture the current screenshot from the observation.
        The observation from the environment contains the frame data.
        """
        return obs

    def get_hp(self, ram, index):
        addr = self.hp_addresses[index]
        return ram[addr] + (ram[addr + 1] << 8)

    def get_lvl(self, ram, index):
        addr = self.lvl_addresses[index]
        return (ram[addr] << 8) + ram[addr + 1]

    def get_oppn_hp(self, ram, index):
        addr = self.oppn_hp_addresses[index]
        return ram[addr] + (ram[addr + 1] << 8)

    def get_oppn_lvl(self, ram, index):
        addr = self.oppn_lvl_addresses[index]
        return (ram[addr] << 8) + ram[addr + 1]

    def calculate_avg_level(self, levels):
        valid_levels = [lvl for lvl in levels if lvl > 0]
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

        # Retrieve and compute average levels
        current_party_lvl = [self.get_lvl(ram, i) for i in range(6)]
        current_total_lvl = sum(current_party_lvl)
        current_oppn_lvl = [self.get_oppn_lvl(ram, i) for i in range(6)]
        player_avg_level = self.calculate_avg_level(current_party_lvl)
        opponent_avg_level = self.calculate_avg_level(current_oppn_lvl)

        # Compute scaling multiplier
        faint_multiplier = self.get_level_multiplier(player_avg_level, opponent_avg_level)

        # Calculate HP rewards and penalties
        current_party_hp = [self.get_hp(ram, i) for i in range(6)]
        current_total_hp = sum(current_party_hp)
        current_oppn_hp = [self.get_oppn_hp(ram, i) for i in range(6)]

        # Check for fainted Pokémon
        for i in range(6):
            if self.prev_party_hp[i] > 0 and current_party_hp[i] == 0:
                # Penalty for own Pokémon fainting
                total_reward -= 5
                if self.verbosity['faint']:
                    print(f"[PENALTY][FAINT] Pokémon {i + 1} fainted (-5)")

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

        # --- Level Gain Reward ---
        level_diff = 0
        for i in range(6):
            if self.prev_party_lvl[i] > 0:  # Only count level-ups for Pokémon that were already in the party
                level_diff += current_party_lvl[i] - self.prev_party_lvl[i]

        if level_diff > 0:
            total_reward += level_diff * self.level_gain_multiplier
            if self.verbosity['general']:
                print(f"[REWARD][LEVEL] Total party level increased by {level_diff} (+{level_diff * self.level_gain_multiplier:.2f})")

        # --- New Pokémon Catch Reward ---
        for i in range(6):
            if current_party_lvl[i] > 0 and self.prev_party_lvl[i] == 0:
                total_reward += 10  # Fixed reward for catching a new Pokémon
                if self.verbosity['general']:
                    print(f"[REWARD][CATCH] A new Pokémon was caught in slot {i + 1} (+10)")

        # Store new values
        self.prev_party_hp = current_party_hp
        self.prev_total_hp = current_total_hp
        self.prev_oppn_hp = current_oppn_hp
        self.prev_party_lvl = current_party_lvl
        self.prev_total_lvl = current_total_lvl
        self.prev_oppn_lvl = current_oppn_lvl

        return total_reward

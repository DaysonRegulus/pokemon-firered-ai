import retro
import numpy as np
import gymnasium as gym  # Import Gymnasium
from collections import deque
from skimage.metrics import structural_similarity as ssim

np.random.seed(42)

class ActionFilterWrapper(gym.ActionWrapper):
    def __init__(self, env):
        super().__init__(env)
        # Original button layout of the environment
        self.original_buttons = ["B", "null", "SELECT", "START", "UP", "DOWN", "LEFT", "RIGHT", "A", "null", "L", "R"]
        # Specify allowed buttons
        self.allowed_buttons = ["B", "null", "UP", "DOWN", "LEFT", "RIGHT", "A"]
        # Get the indices of allowed buttons
        self.allowed_indices = [self.original_buttons.index(button) for button in self.allowed_buttons]
        # Keep the original action space intact
        self.action_space = gym.spaces.MultiBinary(len(self.original_buttons))
    
    def action(self, action):
        """
        Filter the input action to only allow the specified buttons.
        """
        filtered_action = np.zeros_like(action, dtype=action.dtype)
        for index in self.allowed_indices:
            filtered_action[index] = action[index]
        return filtered_action
    
class CustomRewardEnv(gym.Wrapper):
    def __init__(self, base_env, env_id=0):
        super().__init__(base_env)
        self.base_env = base_env
        screenshot_manager = ScreenshotManager(max_bank_size=1000, similarity_threshold=0.1, verbosity=True)
        self.reward_manager = RewardManager(self.base_env, screenshot_manager)
        self.env_id = env_id  # Store the environment ID
        
        # Override print function
        self.original_print = print  # Store original print function
        self._patch_print_function()  # Apply custom print
        
    def _patch_print_function(self):
        """
        Modify print so all log messages automatically get prefixed with [env_id].
        """
        def custom_print(*args, **kwargs):
            self.original_print(f"[{self.env_id}]", *args, **kwargs)  # Add [env_id] before every print
        
        global print  # Modify the global print function inside this class
        print = custom_print
        
    def reset(self, **kwargs):
        """
        Reset the environment and initialize RewardManager.
        Returns a tuple: (observations, info).
        """
        obs, info = self.base_env.reset(**kwargs)
        self.reward_manager.initialize()  # Initialize custom reward logic
        return obs, info

    def step_wait(self):
        """
        Perform additional actions between steps (if needed), this can often be left empty.
        """
        # You can add custom logic here if necessary.
        pass

    def step(self, action):
        """
        Take a step in the environment, calculate custom rewards, and return updated values.
        """
        obs, reward, done, truncated, info = self.base_env.step(action)  # Step in base environment
        custom_reward = self.reward_manager.calculate_rewards()
        if custom_reward is None:
            raise ValueError("RewardManager.calculate_rewards() returned None.")
        reward += custom_reward  # Combine custom and base rewards
        #print(f"Action: {action}, Reward: {reward}, Done: {done}")  # Debug
        return obs, reward, done, truncated, info

class ScreenshotManager:
    def __init__(self, max_bank_size=1000, similarity_threshold=0.2, verbosity=True):
        self.reference_bank = deque(maxlen=max_bank_size)
        self.similarity_threshold = similarity_threshold
        self.verbosity = verbosity

    def is_new_location(self, screenshot):
        """
        Compare the screenshot with reference bank to check if it's a new location.
        """
        for reference in self.reference_bank:
            similarity, _ = ssim(screenshot, reference, win_size=7, channel_axis=-1, full=True)
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
    def __init__(self, env, screenshot_manager, exploration_multiplier=1, hp_oppn_multiplier=1, hp_loss_multiplier=1, hp_heal_multiplier=1, level_gain_multiplier=10, frame_skip=20):
        self.env = env
        self.screenshot_manager = screenshot_manager
        self.prev_party_hp = [0] * 6
        self.prev_oppn_hp = 0
        self.prev_total_hp = 0
        self.prev_party_lvl = [0] * 6
        self.prev_oppn_lvl = [0] * 6  # Now tracking all opponent Pokémon
        self.initialized = False
        self.frame_skip = frame_skip
        self.frame_count = 0
        self.exploration_multiplier = exploration_multiplier
        self.hp_oppn_multiplier = hp_oppn_multiplier
        self.hp_loss_multiplier = hp_loss_multiplier
        self.hp_heal_multiplier = hp_heal_multiplier
        self.level_gain_multiplier = level_gain_multiplier
        self.verbosity = {
            'hp': True,
            'faint': True,
            'exploration': False,
            'general': True
        }

    def initialize(self):
        ram = self.env.unwrapped.get_ram()
        self.prev_party_hp = [self.get_hp(ram, i) for i in range(6)]
        self.prev_oppn_hp = [self.get_oppn_hp(ram, i) for i in range(6)]
        self.prev_total_hp = sum(self.prev_party_hp)
        self.prev_party_lvl = [self.get_lvl(ram, i) for i in range(6)]
        #print(f"[DEBUG] Initial Levels: {self.prev_party_lvl}")
        self.prev_oppn_lvl = [self.get_oppn_lvl(ram, i) for i in range(6)]
        self.prev_total_lvl = sum(self.prev_party_lvl)
        self.initialized = True

    def capture_screenshot(self, obs):
        """
        Capture the current screenshot from the observation.
        The observation from the environment contains the frame data.
        """
        return obs

    def get_relative_address(self, absolute_address):
        """
        Convert absolute address to relative address for the RAM.
        """
        base_address = 0x02000000  # Base address for the GBA RAM
        return absolute_address - base_address

    def get_hp(self, ram, index):
        hp_addresses = [0x20242DA, 0x202433E, 0x20243A2, 0x2024406, 0x202446A, 0x20244CE]
        relative_address = self.get_relative_address(hp_addresses[index])
        return ram[relative_address] + (ram[relative_address + 1] << 8)

    def get_lvl(self, ram, index):
        lvl_addresses = [0x20242D7, 0x202433B, 0x202439F, 0x2024403, 0x2024467, 0x20244CB]
        relative_address = self.get_relative_address(lvl_addresses[index])
        level = (ram[relative_address] << 8) + ram[relative_address + 1]
        #print(f"[DEBUG] Pokémon {index + 1} Level Address: {relative_address}, Level: {level}")
        return level

    def get_oppn_hp(self, ram, index):
        """Get opponent Pokémon HP for all 6 slots."""
        oppn_hp_addresses = [0x2024082, 0x20240E6, 0x202414A, 0x20241AE, 0x2024212, 0x2024276]
        relative_address = self.get_relative_address(oppn_hp_addresses[index])
        return ram[relative_address] + (ram[relative_address + 1] << 8)

    def get_oppn_lvl(self, ram, index):
        oppn_lvl_addresses = [0x202407F, 0x20240E3, 0x2024147, 0x20241AB, 0x202420F, 0x2024273]
        relative_address = self.get_relative_address(oppn_lvl_addresses[index])
        level = (ram[relative_address] << 8) + ram[relative_address + 1]
        return level
    
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
        return 1  # Default case (shouldn't happen)

    def calculate_rewards(self):
        if not self.initialized:
            self.initialize()
            return 0

        self.frame_count += 1
        if self.frame_count % self.frame_skip != 0:
            return 0  # Skip reward calculation for this frame

        ram = self.env.unwrapped.get_ram()
        total_reward = 0
        
        # Capture and process exploration reward
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
            if self.prev_oppn_hp[i] > 0 and current_oppn_hp[i] == 0:
                # Reward for fainting an opponent Pokémon
                faint_reward = 10 * faint_multiplier
                total_reward += faint_reward
                if self.verbosity['faint']:
                    print(f"[REWARD][FAINT] Opponent Pokémon fainted (+{faint_reward})")
                    print(f"[DEBUG][FAINT] Average Party Level: {player_avg_level}; Average Opponent Level: {opponent_avg_level}")
        
        '''        

        # Penalty for party HP loss
        if current_total_hp < self.prev_total_hp:
            hp_loss = self.prev_total_hp - current_total_hp
            total_reward -= hp_loss * self.hp_loss_multiplier
            if self.verbosity['hp']:
                print(f"[PENALTY][HP] Party HP decreased by {hp_loss} (-{hp_loss * self.hp_loss_multiplier:.2f})")        

        # Reward for healing
        if current_total_hp > self.prev_total_hp:
            # Check if healing is not due to white-out
            if all(hp == 0 for hp in self.prev_party_hp):  # Check if all Pokémon were fainted previously
                if self.verbosity['general']:
                    print("[INFO] Healing after white-out detected. No reward granted.")
            else:
                healed_hp = current_total_hp - self.prev_total_hp
                total_reward += healed_hp * self.hp_heal_multiplier
                if self.verbosity['hp']:
                    print(f"[REWARD][HP] Party healed by {healed_hp} (+{healed_hp * self.hp_heal_multiplier:.2f})")

        # Reward for reducing opponent HP
        if current_oppn_hp < self.prev_oppn_hp:
            oppn_hp_loss = self.prev_oppn_hp - current_oppn_hp
            total_reward += oppn_hp_loss * self.hp_oppn_multiplier
            if self.verbosity['hp']:
                print(f"[REWARD][HP] Opponent HP reduced by {oppn_hp_loss} (+{oppn_hp_loss * self.hp_oppn_multiplier:.2f})")
        
        '''

        # Calculate level rewards leftover code
        current_party_lvl = [self.get_lvl(ram, i) for i in range(6)]
        
        # --- Level Gain Reward (Fixed) ---
        level_diff = 0  # Track level gain only for existing Pokémon
        for i in range(6):
            if self.prev_party_lvl[i] > 0:  # Only count level-ups for Pokémon that were already in the party
                level_diff += current_party_lvl[i] - self.prev_party_lvl[i]

        if level_diff > 0:
            total_reward += level_diff * self.level_gain_multiplier
            if self.verbosity['general']:
                print(f"[REWARD][LEVEL] Total party level increased by {level_diff} (+{level_diff * self.level_gain_multiplier:.2f})")

        # --- New Pokémon Catch Reward (Fixed) ---
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
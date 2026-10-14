import numpy as np
import gymnasium as gym
from pokefirered.rewards import RewardManager, ScreenshotManager


class ActionFilterWrapper(gym.ActionWrapper):
    def __init__(self, env):
        super().__init__(env)
        # Original GBA layout: ["B", "null", "SELECT", "START", "UP", "DOWN", "LEFT", "RIGHT", "A", "null", "L", "R"]
        # The subset of buttons we actually want the AI to use:
        # 0:B, 4:UP, 5:DOWN, 6:LEFT, 7:RIGHT, 8:A
        self.target_indices = [0, 4, 5, 6, 7, 8]
        self.button_map = {
            0: 0,  # AI Button 0 -> Game Button 0 (B)
            1: 4,  # AI Button 1 -> Game Button 4 (UP)
            2: 5,  # AI Button 2 -> Game Button 5 (DOWN)
            3: 6,  # AI Button 3 -> Game Button 6 (LEFT)
            4: 7,  # AI Button 4 -> Game Button 7 (RIGHT)
            5: 8,  # AI Button 5 -> Game Button 8 (A)
        }
        # Shrink the action space to size 6
        self.action_space = gym.spaces.MultiBinary(6)

    def action(self, action):
        """
        Filter the input action to only allow the specified buttons.
        Maps the AI's 6 choices to the Game's 12 buttons.
        """
        full_action = np.zeros(12, dtype=np.int8)
        if isinstance(action, (int, np.integer)):
            if 0 <= action < len(self.button_map):
                full_action[self.button_map[int(action)]] = 1
            return full_action

        for i, val in enumerate(action):
            if val == 1:
                game_index = self.button_map[i]
                full_action[game_index] = 1
        return full_action


class StochasticFrameSkip(gym.Wrapper):
    """
    A wrapper for stochastic frame skipping.
    Repeats the selected action for n frames with sticky action probability.
    """
    def __init__(self, env, n=4, stickprob=0.25):
        super().__init__(env)
        self.n = n
        self.stickprob = stickprob
        self.curac = None
        self.rng = np.random.default_rng()

    def reset(self, **kwargs):
        self.curac = None
        return self.env.reset(**kwargs)

    def step(self, action):
        totrew = 0.0
        terminated, truncated = False, False
        for i in range(self.n):
            if self.curac is None or (i == 0 and self.rng.random() > self.stickprob):
                self.curac = action
            obs, rew, terminated, truncated, info = self.env.step(self.curac)
            totrew += rew
            if terminated or truncated:
                break
        return obs, totrew, terminated, truncated, info


class CustomRewardEnv(gym.Wrapper):
    def __init__(self, base_env, env_id=0, exploration_mode="SSIM"):
        super().__init__(base_env)
        self.base_env = base_env
        self.env_id = env_id

        if exploration_mode == "LEGACY_SSIM":
            self.screenshot_manager = ScreenshotManager(max_bank_size=1000, similarity_threshold=0.1, verbosity=True)
        else:
            self.screenshot_manager = None

        self.reward_manager = RewardManager(self.base_env, self.screenshot_manager, exploration_mode=exploration_mode)
        self.episode_faints = 0

    def reset(self, **kwargs):
        """
        Reset the environment and initialize RewardManager.
        Returns a tuple: (observation, info).
        """
        obs, info = self.base_env.reset(**kwargs)
        self.reward_manager.initialize()
        self.episode_faints = 0
        return obs, info

    def step(self, action):
        """
        Take a step in the environment, calculate custom rewards, and return updated values.
        """
        obs, reward, terminated, truncated, info = self.base_env.step(action)
        custom_reward = self.reward_manager.calculate_rewards()
        if custom_reward is None:
            raise ValueError("RewardManager.calculate_rewards() returned None.")
        reward += custom_reward

        faints_this_step = self.reward_manager.faint_count_this_step
        self.episode_faints += faints_this_step

        # Inject stats into the info dict for logging and callbacks
        info['faints_this_step'] = faints_this_step
        if self.screenshot_manager is not None:
            info['ssim_bank_size'] = len(self.screenshot_manager.reference_bank)
        else:
            info['ssim_bank_size'] = 0
        info['episode_faints'] = self.episode_faints

        # Extract Ground-Truth Player Coordinates from RAM for exploration tracking
        ram = self.base_env.unwrapped.get_ram()
        BASE = 0x02000000
        info['map_bank'] = int(ram[0x02031DBC - BASE])
        info['map_num'] = int(ram[0x02031DBD - BASE])
        info['pos_x'] = int(ram[0x02036E48 - BASE])
        info['pos_y'] = int(ram[0x02036E4A - BASE])

        rnd_reward = info.get("rnd_intrinsic_reward", 0)
        if rnd_reward != 0:
            print(f"[{self.env_id}][RND][REWARD] (+{rnd_reward:.4f})")

        if terminated or truncated:
            self.episode_faints = 0

        return obs, reward, terminated, truncated, info

import time
import GPUtil
import numpy as np
import psutil
from stable_baselines3.common.callbacks import BaseCallback
import torch


class ComprehensiveLoggingCallback(BaseCallback):
    """
    Logs hardware metrics (RAM, GPU load/mem), game stats (SSIM bank size, faints),
    speed (steps/sec), and tracks action distributions.
    """
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.action_counts = np.zeros(6)
        self.button_names = ["B", "UP", "DOWN", "LEFT", "RIGHT", "A"]

        # Speedometer
        self.last_time = time.time()
        self.last_step_count = 0

    def _on_step(self) -> bool:
        # 1. Log Hardware Usage every 1000 calls
        if self.n_calls % 1000 == 0:
            ram_usage = psutil.virtual_memory().percent
            try:
                gpus = GPUtil.getGPUs()
                gpu_load = gpus[0].load * 100 if gpus else 0
                gpu_mem = gpus[0].memoryUsed if gpus else 0
            except Exception:
                gpu_load = 0
                gpu_mem = 0

            self.logger.record("hardware/ram_usage", ram_usage)
            self.logger.record("hardware/gpu_load", gpu_load)
            self.logger.record("hardware/gpu_mem", gpu_mem)

            # --- Custom Speedometer ---
            current_time = time.time()
            steps_processed = len(self.locals["rewards"])
            self.last_step_count += steps_processed
            time_elapsed = current_time - self.last_time

            if time_elapsed > 1.0:
                steps_per_second = self.last_step_count / time_elapsed
                self.logger.record("custom/env_steps_per_sec", steps_per_second)
                self.last_time = current_time
                self.last_step_count = 0

        # 2. Log Custom Environment Metrics
        infos = self.locals.get('infos', [])
        if infos:
            avg_bank_size = np.mean([info.get('ssim_bank_size', 0) for info in infos])
            self.logger.record("custom/ssim_bank_size", avg_bank_size)

            real_faints_this_step = sum([info.get('faints_this_step', 0) for info in infos])
            self.logger.record("custom/opponent_faints_cumulative", real_faints_this_step)

        # 3. Log Action Distribution
        actions = self.locals.get('actions', None)
        if actions is not None:
            self.action_counts += np.sum(actions, axis=0)

        return True

    def _on_training_end(self) -> None:
        print("\n" + "=" * 40)
        print("ACTION DISTRIBUTION")
        print("=" * 40)
        for name, count in zip(self.button_names, self.action_counts):
            print(f"{name}: {int(count)}")
        print("=" * 40 + "\n")


class RewardTrackingCallback(BaseCallback):
    """
    Tracks extrinsic, intrinsic, and total rewards separately for TensorBoard.
    """
    def __init__(self, rnd_callback=None, verbose=0):
        super().__init__(verbose)
        self.rnd_callback = rnd_callback
        self.total_extrinsic = 0.0
        self.total_intrinsic = 0.0
        self.total_combined = 0.0

    def _on_step(self) -> bool:
        rewards = self.locals["rewards"]

        if self.rnd_callback is not None and self.rnd_callback.last_intrinsic is not None:
            intrinsic_rewards = self.rnd_callback.last_intrinsic
            extrinsic_rewards = self.rnd_callback.last_extrinsic
        else:
            intrinsic_rewards = np.zeros_like(rewards)
            extrinsic_rewards = rewards

        step_intrinsic = np.sum(intrinsic_rewards)
        step_extrinsic = np.sum(extrinsic_rewards)
        step_total = np.sum(rewards)

        self.total_intrinsic += step_intrinsic
        self.total_extrinsic += step_extrinsic
        self.total_combined += step_total

        self.logger.record("reward/intrinsic", step_intrinsic)
        self.logger.record("reward/extrinsic", step_extrinsic)
        self.logger.record("reward/total", step_total)

        return True

    def get_rewards(self):
        return {
            "extrinsic": self.total_extrinsic,
            "intrinsic": self.total_intrinsic,
            "total": self.total_extrinsic + self.total_intrinsic,
        }


class RNDCallback(BaseCallback):
    """
    Callback that computes RND curiosity reward and adds it to the policy rewards.
    Trains the RND predictor network on observations at the end of each rollout.
    """
    def __init__(self, rnd_module, beta=1.0, debug=True, verbose=0):
        super().__init__(verbose)
        self.rnd = rnd_module
        self.beta = beta
        self.debug = debug
        self.last_intrinsic = None
        self.last_total_reward = None
        self.last_extrinsic = None

    def _on_step(self) -> bool:
        obs = self.locals.get("new_obs", None)
        if obs is None:
            obs = self.locals.get("obs", None)

        if obs is None:
            return True

        obs = np.array(obs)

        # Take ONLY the last frame from frame stack
        if obs.ndim == 4:  # (N, C, H, W)
            obs = obs[:, -1:, :, :]

        obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=self.rnd.device)
        obs_tensor = obs_tensor / 255.0

        # Compute intrinsic reward
        intrinsic = self.rnd.compute_intrinsic_reward(obs_tensor)
        intrinsic = intrinsic.reshape(self.locals["rewards"].shape)

        scaled_intrinsic = self.beta * intrinsic
        original_rewards = self.locals["rewards"].copy()

        self.locals["rewards"] = self.locals["rewards"] + scaled_intrinsic

        self.last_intrinsic = scaled_intrinsic.copy()
        self.last_total_reward = self.locals["rewards"].copy()
        self.last_extrinsic = original_rewards.copy()

        infos = self.locals.get("infos", [])
        for i in range(len(infos)):
            infos[i]["rnd_intrinsic_reward"] = scaled_intrinsic[i]

        if self.debug and self.n_calls % 100 == 0:
            print(
                f"[RND][REWARD] mean={np.mean(intrinsic):.6f} "
                f"max={np.max(intrinsic):.6f} "
                f"min={np.min(intrinsic):.6f}"
            )

        return True

    def _on_rollout_end(self):
        obs = self.model.rollout_buffer.observations
        n_steps, n_envs, c, h, w = obs.shape
        obs = obs.reshape(n_steps * n_envs, c, h, w)

        # Take ONLY the last frame
        obs = obs[:, -1:, :, :]

        # Sample subset
        idx = np.random.choice(len(obs), size=min(1024, len(obs)), replace=False)
        obs = obs[idx]

        obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=self.rnd.device)
        obs_tensor = obs_tensor / 255.0

        loss = self.rnd.train(obs_tensor)
        if self.debug:
            print(f"[RND][LOSS] {loss:.6f}")

        self.logger.record("rnd/loss", loss)

from pathlib import Path
import time
from collections import deque
import numpy as np
import psutil
import GPUtil
import imageio
from stable_baselines3.common.callbacks import BaseCallback


class ComprehensiveLoggingCallback(BaseCallback):
    """
    Logs hardware metrics (RAM, GPU), FPS / SPS, cumulative faints, and action distribution.
    """
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.last_time = time.time()
        self.last_step_count = 0
        self.action_counts = np.zeros(6, dtype=int)
        self.button_names = ["B", "UP", "DOWN", "LEFT", "RIGHT", "A"]

    def _on_step(self) -> bool:
        # 1. Hardware Metrics
        ram_usage = psutil.virtual_memory().percent
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_load = gpus[0].load * 100
                gpu_mem = gpus[0].memoryUsed
            else:
                gpu_load = 0
                gpu_mem = 0
        except Exception:
            gpu_load = 0
            gpu_mem = 0

        self.logger.record("hardware/ram_usage", ram_usage)
        self.logger.record("hardware/gpu_load", gpu_load)
        self.logger.record("hardware/gpu_mem", gpu_mem)

        # 2. Custom Speedometer
        current_time = time.time()
        steps_processed = len(self.locals["rewards"])
        self.last_step_count += steps_processed
        time_elapsed = current_time - self.last_time

        if time_elapsed > 1.0:
            steps_per_second = self.last_step_count / time_elapsed
            self.logger.record("custom/env_steps_per_sec", steps_per_second)
            self.last_time = current_time
            self.last_step_count = 0

        # 3. Custom Environment Metrics
        infos = self.locals.get("infos", [])
        if infos:
            avg_bank_size = np.mean([info.get("ssim_bank_size", 0) for info in infos])
            self.logger.record("custom/ssim_bank_size", avg_bank_size)

            real_faints_this_step = sum([info.get("faints_this_step", 0) for info in infos])
            self.logger.record("custom/opponent_faints_cumulative", real_faints_this_step)

        # 4. Log Action Distribution
        actions = self.locals.get("actions", None)
        if actions is not None:
            self.action_counts += np.sum(actions, axis=0).astype(int)

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
    Callback that computes calibrated RND curiosity rewards and adds them to policy rewards.
    Trains the RND predictor network on rollout buffer observations at rollout end.
    """
    def __init__(self, rnd_module, beta=0.05, debug=True, verbose=0):
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

        obs_np = np.array(obs, dtype=np.float32)

        # Extract only the latest frame from the stack: shape (N, 1, 84, 84)
        if obs_np.ndim == 4:
            obs_np = obs_np[:, -1:, :, :]

        obs_np = obs_np / 255.0

        # Compute normalized intrinsic reward and raw error
        norm_reward, raw_error = self.rnd.compute_intrinsic_reward(obs_np)
        norm_reward = norm_reward.reshape(self.locals["rewards"].shape)

        scaled_intrinsic = self.beta * norm_reward
        original_rewards = self.locals["rewards"].copy()

        # Add intrinsic exploration bonus to policy rewards
        self.locals["rewards"] = self.locals["rewards"] + scaled_intrinsic

        self.last_intrinsic = scaled_intrinsic.copy()
        self.last_total_reward = self.locals["rewards"].copy()
        self.last_extrinsic = original_rewards.copy()

        infos = self.locals.get("infos", [])
        for i in range(len(infos)):
            infos[i]["rnd_intrinsic_reward"] = scaled_intrinsic[i]

        self.logger.record("rnd/reward_norm_mean", float(np.mean(norm_reward)))
        self.logger.record("rnd/reward_norm_max", float(np.max(norm_reward)))
        self.logger.record("rnd/raw_error_mean", float(np.mean(raw_error)))

        if self.debug and self.n_calls % 100 == 0:
            print(
                f"[RND] norm_r={np.mean(norm_reward):.3f} (max={np.max(norm_reward):.3f}) | "
                f"raw_err={np.mean(raw_error):.5f} | beta={self.beta}"
            )

        return True

    def _on_rollout_end(self):
        obs = self.model.rollout_buffer.observations
        n_steps, n_envs, c, h, w = obs.shape
        obs = obs.reshape(n_steps * n_envs, c, h, w)

        # Extract latest frame and scale to [0, 1]
        obs = obs[:, -1:, :, :].astype(np.float32) / 255.0

        loss = self.rnd.train_batch(obs, epochs=3, batch_size=256)
        if self.debug:
            print(f"[RND][TRAIN] Predictor Loss: {loss:.5f}")

        self.logger.record("rnd/loss", loss)


class RAMExplorationTrackerCallback(BaseCallback):
    """
    Ground-truth learning verification callback.
    Monitors player's (Map, X, Y) coordinates directly from GBA RAM.
    Tracks cumulative unique tiles, unique maps, and exploration novelty rate.
    """
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.global_visited_tiles = set()
        self.global_visited_maps = set()
        self.recent_discoveries = deque(maxlen=500)
        self.last_total_tiles = 0

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        for info in infos:
            if "pos_x" in info and "pos_y" in info and "map_bank" in info:
                tile = (info["map_bank"], info["map_num"], info["pos_x"], info["pos_y"])
                map_id = (info["map_bank"], info["map_num"])

                is_new = tile not in self.global_visited_tiles
                self.global_visited_tiles.add(tile)
                self.global_visited_maps.add(map_id)
                self.recent_discoveries.append(1 if is_new else 0)

        total_tiles = len(self.global_visited_tiles)
        total_maps = len(self.global_visited_maps)
        novelty_rate = float(np.mean(self.recent_discoveries)) if self.recent_discoveries else 0.0

        self.logger.record("exploration/unique_tiles_total", total_tiles)
        self.logger.record("exploration/unique_maps_total", total_maps)
        self.logger.record("exploration/novelty_rate", novelty_rate)

        if total_tiles > self.last_total_tiles and total_tiles % 25 == 0:
            print(f"[EXPLORATION MILESTONE] Total unique tiles visited: {total_tiles} | Maps: {total_maps}")
            self.last_total_tiles = total_tiles

        return True


class PeriodicVisualEvalCallback(BaseCallback):
    """
    Periodically executes an evaluation episode and saves an animated visual GIF.
    Allows the user to visually inspect the agent's progress without slowing down training.
    """
    def __init__(
        self,
        eval_freq=20480,
        max_eval_steps=400,
        record_dir="eval_recordings",
        env_name="PokemonFireRed-GBA",
        verbose=1,
    ):
        super().__init__(verbose)
        self.eval_freq = eval_freq
        self.max_eval_steps = max_eval_steps
        self.record_dir = Path(record_dir)
        self.record_dir.mkdir(parents=True, exist_ok=True)
        self.env_name = env_name
        self.eval_count = 0
        self.last_eval_step = 0

    def _on_step(self) -> bool:
        if self.num_timesteps - self.last_eval_step >= self.eval_freq:
            self.last_eval_step = self.num_timesteps
            self._record_eval_episode()
        return True

    def _on_training_end(self) -> None:
        if self.eval_count == 0 or (self.num_timesteps - self.last_eval_step >= self.eval_freq // 2):
            self._record_eval_episode()

    def _record_eval_episode(self):
        self.eval_count += 1
        timestep = self.num_timesteps
        print(f"\n[VISUAL EVAL] Capturing evaluation episode at step {timestep:,}...")

        from pokefirered.env_factory import create_vectorized_env

        eval_env = create_vectorized_env(
            env_name=self.env_name,
            num_envs=1,
            n_stack=2,
            exploration_mode="NONE",
        )

        frames = []
        obs = eval_env.reset()
        done = False
        step = 0
        total_eval_rew = 0.0

        while not done and step < self.max_eval_steps:
            # Capture high-res RGB emulator screen for GIF
            raw_screen = eval_env.env_method("get_screen")[0]
            frames.append(raw_screen)

            action, _ = self.model.predict(obs, deterministic=True)
            obs, reward, dones, infos = eval_env.step(action)

            total_eval_rew += float(reward[0])
            step += 1
            done = bool(dones[0])

        eval_env.close()

        gif_path = self.record_dir / f"eval_step_{timestep:07d}.gif"
        # Subsample frames to keep GIF compact (every 2nd frame at 15 fps)
        subsampled_frames = frames[::2]
        if subsampled_frames:
            imageio.mimsave(str(gif_path), subsampled_frames, fps=15, loop=0)
            print(f"[VISUAL EVAL] Saved visual recording to: {gif_path} (Frames: {len(subsampled_frames)})")

        self.logger.record("eval/episode_reward", total_eval_rew)
        self.logger.record("eval/episode_length", step)

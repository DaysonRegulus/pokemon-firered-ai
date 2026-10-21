"""
Training Benchmark Script for Pokemon FireRed AI.
Supports both on-policy PPO and off-policy Distributional QR-DQN with Prioritized Experience Replay (PER),
calibrated multi-modal curiosity (RND, SSIM, COORD), RAM exploration tracking, and periodic visual evaluation recordings.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import torch
from stable_baselines3 import PPO

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.callbacks import (
    ComprehensiveLoggingCallback,
    RewardTrackingCallback,
    RNDCallback,
    SSIMCallback,
    CoordinateExplorationCallback,
    RAMExplorationTrackerCallback,
    PeriodicVisualEvalCallback,
)
from pokefirered.coord_module import CoordinateExplorationModule
from pokefirered.env_factory import create_vectorized_env
from pokefirered.rnd import RNDModule
from pokefirered.ssim_module import OptimizedSSIMModule
from pokefirered.models import QRDQNAgent


def get_model_paths(model_dir: Path, env_name: str, algo: str, num_envs: int, exploration_mode: str):
    clean_mode = exploration_mode.replace("+", "_")
    prefix = f"{env_name}-{algo}-{clean_mode}-{num_envs}env"
    model_path = model_dir / prefix
    rnd_path = model_dir / f"{prefix}_rnd.pth"
    ssim_path = model_dir / f"{prefix}_ssim.pt"
    coord_path = model_dir / f"{prefix}_coord.pt"
    return model_path, rnd_path, ssim_path, coord_path


def parse_args():
    parser = argparse.ArgumentParser(description="Train Pokemon FireRed RL Agent")
    parser.add_argument("--env-name", type=str, default="PokemonFireRed-GBA", help="Retro env name")
    parser.add_argument("--algo", type=str, default="PPO", choices=["PPO", "QRDQN"], help="RL Algorithm: PPO or QRDQN (with PER)")
    parser.add_argument("--num-envs", type=int, default=8, help="Number of parallel environments (recommended: 8 or 12)")
    parser.add_argument(
        "--exploration",
        type=str,
        default="RND",
        help="Exploration mode: RND, SSIM, COORD, NONE, or hybrid combinations like RND+COORD, SSIM+COORD, RND+SSIM, RND+SSIM+COORD",
    )
    parser.add_argument("--timesteps", type=int, default=None, help="Explicit training steps (overrides dynamic curriculum)")
    parser.add_argument("--render-mode", type=str, default=None, choices=["human", None], help="Render mode")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Device (cuda/cpu)")
    parser.add_argument("--log-dir", type=str, default="logs", help="Tensorboard log directory")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints", help="Model checkpoints directory")
    parser.add_argument("--rnd-beta", type=float, default=0.05, help="Weight for normalized RND intrinsic reward (default: 0.05)")
    parser.add_argument("--ssim-beta", type=float, default=0.05, help="Weight for normalized SSIM intrinsic reward (default: 0.05)")
    parser.add_argument("--coord-beta", type=float, default=0.05, help="Weight for coordinate count intrinsic reward (default: 0.05)")
    parser.add_argument("--ent-coef", type=float, default=0.03, help="Entropy coefficient for PPO")
    parser.add_argument("--epsilon-start", type=float, default=1.0, help="Initial exploration rate for QR-DQN")
    parser.add_argument("--epsilon-end", type=float, default=0.05, help="Final exploration rate for QR-DQN")
    parser.add_argument("--epsilon-decay-steps", type=int, default=50_000, help="Epsilon decay steps for QR-DQN")
    parser.add_argument("--visual-eval", action="store_true", help="Enable periodic evaluation GIF recordings")
    parser.add_argument("--eval-freq", type=int, default=20480, help="Timestep frequency for periodic visual evaluations")
    parser.add_argument("--eval-steps", type=int, default=400, help="Maximum steps per visual evaluation episode")
    parser.add_argument(
        "--no-record-trajectories",
        action="store_false",
        dest="record_trajectories",
        default=True,
        help="Disable full step-by-step per-agent coordinate trajectory recording (recording is ENABLED by default)",
    )
    parser.add_argument("--fresh", action="store_true", help="Force train from scratch, ignoring existing checkpoints")
    return parser.parse_args()


def train_qrdqn(args, vec_env, model_path, rnd_path, ssim_path, coord_path, log_dir, checkpoint_dir, active_modes):
    """Executes off-policy QR-DQN training loop with PER and multi-modal curiosity."""
    in_channels = vec_env.observation_space.shape[0]
    num_actions = vec_env.action_space.n

    agent = QRDQNAgent(
        in_channels=in_channels,
        num_actions=num_actions,
        num_quantiles=32,
        learning_rate=1e-4,
        gamma=0.99,
        tau=0.005,
        kappa=1.0,
        buffer_size=50_000,
        batch_size=64,
        device=args.device,
    )

    model_file_pth = model_path.with_suffix(".pth")
    if not args.fresh and model_file_pth.exists():
        print(f"Loading existing QR-DQN model from {model_file_pth}...")
        agent.load(model_file_pth)

    # Initialize Exploration modules
    rnd_module = RNDModule(device=args.device) if "RND" in active_modes else None
    ssim_module = OptimizedSSIMModule(device=args.device) if "SSIM" in active_modes else None
    coord_module = CoordinateExplorationModule(beta=args.coord_beta) if "COORD" in active_modes else None

    if rnd_module is not None and rnd_path.exists():
        rnd_module.load(str(rnd_path))
    if ssim_module is not None and ssim_path.exists():
        ssim_module.load(str(ssim_path))
    if coord_module is not None and coord_path.exists():
        coord_module.load(str(coord_path))

    total_target_timesteps = args.timesteps or 20480
    target_iterations = max(1, total_target_timesteps // args.num_envs)
    total_steps = target_iterations * args.num_envs
    print(f"\n[QR-DQN + PER] Scheduled iterations: {target_iterations:,} ({total_steps:,} total environment steps across {args.num_envs} envs)\n")

    visited_tiles = set()
    visited_maps = set()
    total_extrinsic = 0.0
    total_intrinsic = 0.0

    rnd_rollout_buffer = [] if rnd_module is not None else None
    agent_trajectories = [[] for _ in range(args.num_envs)] if args.record_trajectories else []

    obs = vec_env.reset()
    start_time = time.time()

    for step in range(target_iterations):
        # Epsilon decay schedule
        progress = min(1.0, (step * args.num_envs) / max(1, args.epsilon_decay_steps))
        epsilon = args.epsilon_start - progress * (args.epsilon_start - args.epsilon_end)

        # Batch action selection for parallel environments
        actions = agent.select_actions(obs, epsilon=epsilon)
        next_obs, rewards, dones, infos = vec_env.step(actions)

        # Compute intrinsic curiosity bonuses vectorially
        obs_latest = next_obs[:, -1:, :, :].astype(np.float32) / 255.0

        r_rnd_vec = None
        if rnd_module is not None:
            r_rnd_vec, _ = rnd_module.compute_intrinsic_reward(obs_latest)
            if rnd_rollout_buffer is not None:
                rnd_rollout_buffer.append(obs_latest)
                if len(rnd_rollout_buffer) >= 32:  # 32 * num_envs = 256 samples
                    batch_rnd = np.concatenate(rnd_rollout_buffer, axis=0)
                    rnd_module.train_batch(batch_rnd, epochs=2, batch_size=64)
                    rnd_rollout_buffer.clear()

        r_ssim_vec = None
        if ssim_module is not None:
            r_ssim_vec, _ = ssim_module.compute_intrinsic_reward(obs_latest)

        r_coord_vec = None
        if coord_module is not None:
            map_banks = [infos[i].get("map_bank", 0) for i in range(args.num_envs)]
            map_nums = [infos[i].get("map_num", 0) for i in range(args.num_envs)]
            xs = [infos[i].get("pos_x", 0) for i in range(args.num_envs)]
            ys = [infos[i].get("pos_y", 0) for i in range(args.num_envs)]
            r_coord_vec, _ = coord_module.compute_intrinsic_reward(map_banks, map_nums, xs, ys)

        for i in range(args.num_envs):
            r_ext = float(rewards[i])
            r_int = 0.0

            if r_rnd_vec is not None:
                r_int += args.rnd_beta * float(r_rnd_vec[i])
            if r_ssim_vec is not None:
                r_int += args.ssim_beta * float(r_ssim_vec[i])
            if r_coord_vec is not None:
                r_int += args.coord_beta * float(r_coord_vec[i])

            # Ground-truth RAM coordinates tracking
            info = infos[i]
            if "pos_x" in info and "pos_y" in info and "map_bank" in info:
                raw_x = int(info["pos_x"])
                raw_y = int(info["pos_y"])
                mb = int(info["map_bank"])
                mn = int(info["map_num"])
                x = max(0, raw_x - 7) if raw_x >= 7 else raw_x
                y = max(0, raw_y - 7) if raw_y >= 7 else raw_y

                tile = (mb, mn, raw_x, raw_y)
                visited_tiles.add(tile)
                visited_maps.add((mb, mn))

                if args.record_trajectories and i < len(agent_trajectories):
                    agent_trajectories[i].append((mb, mn, x, y))

            total_extrinsic += r_ext
            total_intrinsic += r_int
            r_total = r_ext + r_int

            # Add transition to Prioritized Replay Buffer
            agent.buffer.add(obs[i], actions[i], r_total, next_obs[i], dones[i])

        # Optimize QR-DQN network with Quantile Huber loss
        metrics = agent.update()
        obs = next_obs

        if (step + 1) % 100 == 0 or step == target_iterations - 1:
            elapsed = time.time() - start_time
            curr_timesteps = (step + 1) * args.num_envs
            sps = curr_timesteps / max(0.001, elapsed)
            q_str = f"Q-loss: {metrics['qr_loss']:.4f} | Mean Q: {metrics['mean_q']:.3f}" if metrics else "Warmup"
            print(f"  [STEP {curr_timesteps:6d}/{total_steps:6d}] SPS: {sps:5.1f} | Eps: {epsilon:.3f} | {q_str} | Tiles: {len(visited_tiles)} | Maps: {len(visited_maps)}")

    elapsed = time.time() - start_time
    sps = total_steps / max(0.001, elapsed)

    print("\n" + "=" * 55)
    print(" QR-DQN + PER TRAINING SESSION COMPLETE - SUMMARY")
    print("=" * 55)
    print(f" Algorithm        : QR-DQN with Prioritized Experience Replay")
    print(f" Exploration Mode : {args.exploration}")
    print(f" Timesteps        : {total_steps:,}")
    print(f" Elapsed Time     : {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f" Average SPS      : {sps:.1f}")
    print(f" Extrinsic Reward : {total_extrinsic:.2f}")
    print(f" Intrinsic Reward : {total_intrinsic:.2f}")
    print(f" Total Reward     : {total_extrinsic + total_intrinsic:.2f}")
    print(f" Total Unique Tiles Discovered: {len(visited_tiles)}")
    print(f" Total Unique Maps Discovered:  {len(visited_maps)}")
    print("=" * 55 + "\n")

    # Save checkpoints & metrics summary
    agent.save(model_file_pth)
    if rnd_module is not None:
        rnd_module.save(str(rnd_path))
    if ssim_module is not None:
        ssim_module.save(str(ssim_path))
    if coord_module is not None:
        coord_module.save(str(coord_path))

    summary_data = {
        "algo": "QRDQN",
        "exploration": args.exploration,
        "num_envs": args.num_envs,
        "timesteps": total_steps,
        "elapsed_seconds": round(elapsed, 2),
        "sps": round(sps, 1),
        "extrinsic_reward": round(total_extrinsic, 2),
        "intrinsic_reward": round(total_intrinsic, 2),
        "total_reward": round(total_extrinsic + total_intrinsic, 2),
        "unique_tiles": len(visited_tiles),
        "unique_maps": len(visited_maps),
    }
    summary_file = checkpoint_dir / f"{model_path.stem}_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Summary metrics saved to {summary_file}")

    if args.record_trajectories and agent_trajectories:
        traj_file = checkpoint_dir / f"{model_path.stem}_trajectories.json"
        with open(traj_file, "w", encoding="utf-8") as f:
            json.dump(agent_trajectories, f)
        print(f"Full per-agent coordinate trajectories saved to: {traj_file}")


def main():
    import multiprocessing
    multiprocessing.freeze_support()
    args = parse_args()
    checkpoint_dir = PROJECT_ROOT / args.checkpoint_dir
    log_dir = PROJECT_ROOT / args.log_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    clean_mode = args.exploration.replace("+", "_")
    run_name = f"Pokemon_{args.algo}_{clean_mode}_{args.num_envs}env_{int(time.time())}"
    model_path, rnd_path, ssim_path, coord_path = get_model_paths(checkpoint_dir, args.env_name, args.algo, args.num_envs, args.exploration)

    active_modes = [m.strip().upper() for m in args.exploration.split("+")]

    print("=" * 65)
    print(f" Starting Training Session: {run_name}")
    print(f" Algorithm:    {args.algo}")
    print(f" Environments: {args.num_envs} | Exploration: {args.exploration} | Device: {args.device}")
    print(f" Active Modes: {active_modes}")
    print(f" Checkpoint:   {model_path}")
    print(f" TensorBoard:  {log_dir}")
    print("=" * 65)

    # Create vectorized environment
    print(f"Creating {args.num_envs} vectorized environments...")
    vec_env = create_vectorized_env(
        env_name=args.env_name,
        num_envs=args.num_envs,
        n_stack=2,
        render_mode=args.render_mode,
        exploration_mode="SSIM" if "LEGACY_SSIM" in active_modes else "NONE",
    )

    try:
        if args.algo == "QRDQN":
            train_qrdqn(args, vec_env, model_path, rnd_path, ssim_path, coord_path, log_dir, checkpoint_dir, active_modes)
            return

        # PPO Path
        rnd_module = RNDModule(device=args.device) if "RND" in active_modes else None
        ssim_module = OptimizedSSIMModule(device=args.device) if "SSIM" in active_modes else None
        coord_module = CoordinateExplorationModule(beta=args.coord_beta) if "COORD" in active_modes else None

        model_file_zip = model_path.with_suffix(".zip")
        if not args.fresh and model_file_zip.exists():
            print(f"Loading existing model from {model_file_zip}...")
            model = PPO.load(str(model_path), env=vec_env, device=args.device)
            model.tensorboard_log = str(log_dir)
            model.ent_coef = args.ent_coef
            if rnd_module is not None and rnd_path.exists():
                rnd_module.load(str(rnd_path))
            if ssim_module is not None and ssim_path.exists():
                ssim_module.load(str(ssim_path))
            if coord_module is not None and coord_path.exists():
                coord_module.load(str(coord_path))
        else:
            print("No existing model found. Initializing new PPO model...")
            model = PPO(
                policy="CnnPolicy",
                env=vec_env,
                learning_rate=2.5e-4,
                n_steps=1024,
                batch_size=512,
                n_epochs=4,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.1,
                ent_coef=args.ent_coef,
                verbose=1,
                tensorboard_log=str(log_dir),
                device=args.device,
            )

        target_steps = args.timesteps or 20480

        # Setup callbacks
        intrinsic_cbs = []
        if rnd_module is not None:
            intrinsic_cbs.append(RNDCallback(rnd_module, beta=args.rnd_beta, debug=True))
        if ssim_module is not None:
            intrinsic_cbs.append(SSIMCallback(ssim_module, beta=args.ssim_beta, debug=True))
        if coord_module is not None:
            intrinsic_cbs.append(CoordinateExplorationCallback(coord_module, beta=args.coord_beta, debug=True))

        reward_callback = RewardTrackingCallback(intrinsic_callbacks=intrinsic_cbs)
        logging_callback = ComprehensiveLoggingCallback()
        exploration_tracker = RAMExplorationTrackerCallback(
            record_trajectories=args.record_trajectories,
            num_envs=args.num_envs,
        )
        callbacks = [logging_callback, exploration_tracker] + intrinsic_cbs + [reward_callback]

        if args.visual_eval:
            callbacks.append(PeriodicVisualEvalCallback(
                eval_freq=args.eval_freq,
                max_eval_steps=args.eval_steps,
                env_name=args.env_name,
            ))

        start_time = time.time()
        model.learn(
            total_timesteps=target_steps,
            callback=callbacks,
            tb_log_name=run_name,
            reset_num_timesteps=False,
        )
        elapsed = time.time() - start_time
        sps = target_steps / elapsed if elapsed > 0 else 0
        rewards = reward_callback.get_rewards()

        print("\n" + "=" * 50)
        print(" PPO TRAINING RUN COMPLETE - SUMMARY")
        print("=" * 50)
        print(f" Exploration Mode : {args.exploration}")
        print(f" Timesteps        : {target_steps:,}")
        print(f" Elapsed Time     : {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f" Average SPS      : {sps:.1f}")
        print(f" Extrinsic Reward : {rewards['extrinsic']:.2f}")
        print(f" Intrinsic Reward : {rewards['intrinsic']:.2f}")
        print(f" Total Reward     : {rewards['total']:.2f}")
        print(f" Total Unique Tiles Discovered: {len(exploration_tracker.global_visited_tiles)}")
        print(f" Total Unique Maps Discovered:  {len(exploration_tracker.global_visited_maps)}")
        print("=" * 50 + "\n")

        summary_data = {
            "algo": "PPO",
            "exploration": args.exploration,
            "num_envs": args.num_envs,
            "timesteps": target_steps,
            "elapsed_seconds": round(elapsed, 2),
            "sps": round(sps, 1),
            "extrinsic_reward": round(float(rewards['extrinsic']), 2),
            "intrinsic_reward": round(float(rewards['intrinsic']), 2),
            "total_reward": round(float(rewards['total']), 2),
            "unique_tiles": len(exploration_tracker.global_visited_tiles),
            "unique_maps": len(exploration_tracker.global_visited_maps),
        }
        summary_file = checkpoint_dir / f"{model_path.stem}_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary_data, f, indent=2)

        model.save(str(model_path))
        if rnd_module is not None: rnd_module.save(str(rnd_path))
        if ssim_module is not None: ssim_module.save(str(ssim_path))
        if coord_module is not None: coord_module.save(str(coord_path))

        if args.record_trajectories:
            traj_file = checkpoint_dir / f"{model_path.stem}_trajectories.json"
            try:
                exploration_tracker.save_trajectories(traj_file)
            except Exception as e:
                print(f"[WARN] Failed to save trajectories: {e}")

    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current weights...")
    finally:
        vec_env.close()


if __name__ == "__main__":
    main()

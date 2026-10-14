"""
Training Benchmark Script for Pokemon FireRed AI.
Uses Stable-Baselines3 PPO with calibrated RND curiosity, RAM exploration tracking,
and periodic visual evaluation recordings.
"""
import argparse
import os
from pathlib import Path
import sys
import time
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


def get_model_paths(model_dir: Path, env_name: str, num_envs: int, exploration_mode: str):
    clean_mode = exploration_mode.replace("+", "_")
    prefix = f"{env_name}-{clean_mode}-{num_envs}env"
    model_path = model_dir / prefix
    rnd_path = model_dir / f"{prefix}_rnd.pth"
    ssim_path = model_dir / f"{prefix}_ssim.pt"
    coord_path = model_dir / f"{prefix}_coord.pt"
    return model_path, rnd_path, ssim_path, coord_path


def parse_args():
    parser = argparse.ArgumentParser(description="Train Pokemon FireRed RL Agent")
    parser.add_argument("--env-name", type=str, default="PokemonFireRed-GBA", help="Retro env name")
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
    parser.add_argument("--visual-eval", action="store_true", help="Enable periodic evaluation GIF recordings")
    parser.add_argument("--eval-freq", type=int, default=20480, help="Timestep frequency for periodic visual evaluations")
    parser.add_argument("--eval-steps", type=int, default=400, help="Maximum steps per visual evaluation episode")
    return parser.parse_args()


def main():
    args = parse_args()
    checkpoint_dir = PROJECT_ROOT / args.checkpoint_dir
    log_dir = PROJECT_ROOT / args.log_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    run_name = f"Pokemon_PPO_{int(time.time())}"
    model_path, rnd_path, ssim_path, coord_path = get_model_paths(checkpoint_dir, args.env_name, args.num_envs, args.exploration)

    active_modes = [m.strip().upper() for m in args.exploration.split("+")]

    print("=" * 65)
    print(f" Starting Training Session: {run_name}")
    print(f" Environments: {args.num_envs} | Exploration: {args.exploration} | Device: {args.device}")
    print(f" Active Modes: {active_modes}")
    print(f" Checkpoint:   {model_path}")
    print(f" TensorBoard:  {log_dir}")
    print(f" Visual Eval:  {'Enabled (every ' + str(args.eval_freq) + ' steps)' if args.visual_eval else 'Disabled'}")
    print("=" * 65)

    # Initialize Exploration modules
    rnd_module = None
    ssim_module = None
    coord_module = None

    if "RND" in active_modes:
        rnd_module = RNDModule(device=args.device)
    if "SSIM" in active_modes:
        ssim_module = OptimizedSSIMModule(device=args.device)
    if "COORD" in active_modes:
        coord_module = CoordinateExplorationModule(beta=args.coord_beta)

    # Create vectorized environment
    print(f"Creating {args.num_envs} vectorized environments...")
    vec_env = create_vectorized_env(
        env_name=args.env_name,
        num_envs=args.num_envs,
        n_stack=2,
        render_mode=args.render_mode,
        exploration_mode="SSIM" if "LEGACY_SSIM" in active_modes else "NONE",
    )

    # Load or initialize PPO model
    model_file_zip = model_path.with_suffix(".zip")
    if model_file_zip.exists():
        print(f"Loading existing model from {model_file_zip}...")
        model = PPO.load(str(model_path), env=vec_env, device=args.device)
        model.tensorboard_log = str(log_dir)
        model.ent_coef = args.ent_coef
        if rnd_module is not None and rnd_path.exists():
            print(f"Loading RND checkpoint from {rnd_path}...")
            rnd_module.load(str(rnd_path))
        if ssim_module is not None and ssim_path.exists():
            print(f"Loading SSIM bank checkpoint from {ssim_path}...")
            ssim_module.load(str(ssim_path))
        if coord_module is not None and coord_path.exists():
            print(f"Loading Coordinate counts checkpoint from {coord_path}...")
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

    # Dynamic curriculum step calculation
    if args.timesteps is not None:
        target_steps = args.timesteps
    else:
        growth_rate = 0.05
        min_steps = 4096
        current_lifetime = model.num_timesteps
        dynamic_steps = int(min_steps + (current_lifetime * growth_rate))
        target_steps = int(round(dynamic_steps / 2048) * 2048)
        if target_steps <= 0:
            target_steps = 2048

    print(f"\n[CURRICULUM] Lifetime steps so far: {model.num_timesteps:,}")
    print(f"[CURRICULUM] Steps scheduled for this run: {target_steps:,}\n")

    # Setup callbacks
    intrinsic_cbs = []
    if rnd_module is not None:
        rnd_cb = RNDCallback(rnd_module, beta=args.rnd_beta, debug=True)
        intrinsic_cbs.append(rnd_cb)
    if ssim_module is not None:
        ssim_cb = SSIMCallback(ssim_module, beta=args.ssim_beta, debug=True)
        intrinsic_cbs.append(ssim_cb)
    if coord_module is not None:
        coord_cb = CoordinateExplorationCallback(coord_module, beta=args.coord_beta, debug=True)
        intrinsic_cbs.append(coord_cb)

    reward_callback = RewardTrackingCallback(intrinsic_callbacks=intrinsic_cbs)
    logging_callback = ComprehensiveLoggingCallback()
    exploration_tracker = RAMExplorationTrackerCallback()
    callbacks = [logging_callback, exploration_tracker] + intrinsic_cbs + [reward_callback]

    if args.visual_eval:
        visual_eval_callback = PeriodicVisualEvalCallback(
            eval_freq=args.eval_freq,
            max_eval_steps=args.eval_steps,
            env_name=args.env_name,
        )
        callbacks.append(visual_eval_callback)

    try:
        model.learn(
            total_timesteps=target_steps,
            callback=callbacks,
            tb_log_name=run_name,
            reset_num_timesteps=False,
        )

        rewards = reward_callback.get_rewards()
        print("\n" + "=" * 50)
        print(" TRAINING RUN COMPLETE - SUMMARY")
        print("=" * 50)
        print(f" Extrinsic Reward : {rewards['extrinsic']:.2f}")
        print(f" Intrinsic Reward : {rewards['intrinsic']:.2f}")
        print(f" Total Reward     : {rewards['total']:.2f}")
        print(f" Total Unique Tiles Discovered: {len(exploration_tracker.global_visited_tiles)}")
        print(f" Total Unique Maps Discovered:  {len(exploration_tracker.global_visited_maps)}")
        print("=" * 50 + "\n")

        print(f"Saving model to {model_path}...")
        model.save(str(model_path))
        if rnd_module is not None:
            print(f"Saving RND model to {rnd_path}...")
            rnd_module.save(str(rnd_path))
        if ssim_module is not None:
            print(f"Saving SSIM bank to {ssim_path}...")
            ssim_module.save(str(ssim_path))
        if coord_module is not None:
            print(f"Saving Coordinate counts to {coord_path}...")
            coord_module.save(str(coord_path))
        print("Save complete.")

    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current weights...")
        model.save(str(model_path))
        if rnd_module is not None:
            rnd_module.save(str(rnd_path))
        if ssim_module is not None:
            ssim_module.save(str(ssim_path))
        if coord_module is not None:
            coord_module.save(str(coord_path))
    finally:
        vec_env.close()


if __name__ == "__main__":
    main()

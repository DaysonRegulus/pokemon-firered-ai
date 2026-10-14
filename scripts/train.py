"""
Training Benchmark Script for Pokemon FireRed AI.
Uses Stable-Baselines3 PPO with optional RND curiosity or SSIM visual exploration.
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
)
from pokefirered.env_factory import create_vectorized_env
from pokefirered.rnd import RNDModule


def get_model_paths(model_dir: Path, env_name: str, num_envs: int, exploration_mode: str):
    prefix = f"{env_name}-{exploration_mode}-{num_envs}env"
    model_path = model_dir / prefix
    rnd_path = model_dir / f"{prefix}_rnd.pth"
    return model_path, rnd_path


def parse_args():
    parser = argparse.ArgumentParser(description="Train Pokemon FireRed RL Agent")
    parser.add_argument("--env-name", type=str, default="PokemonFireRed-GBA", help="Retro env name")
    parser.add_argument("--num-envs", type=int, default=2, help="Number of parallel environments")
    parser.add_argument("--exploration", type=str, default="RND", choices=["RND", "SSIM", "NONE"], help="Exploration mode")
    parser.add_argument("--timesteps", type=int, default=None, help="Explicit training steps (overrides dynamic curriculum)")
    parser.add_argument("--render-mode", type=str, default=None, choices=["human", None], help="Render mode")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Device (cuda/cpu)")
    parser.add_argument("--log-dir", type=str, default="logs", help="Tensorboard log directory")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints", help="Model checkpoints directory")
    parser.add_argument("--rnd-beta", type=float, default=1.0, help="Weight for RND intrinsic reward")
    parser.add_argument("--ent-coef", type=float, default=0.03, help="Entropy coefficient for PPO")
    return parser.parse_args()


def main():
    args = parse_args()
    checkpoint_dir = PROJECT_ROOT / args.checkpoint_dir
    log_dir = PROJECT_ROOT / args.log_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    run_name = f"Pokemon_PPO_{int(time.time())}"
    model_path, rnd_path = get_model_paths(checkpoint_dir, args.env_name, args.num_envs, args.exploration)

    print("=" * 60)
    print(f" Starting Training Session: {run_name}")
    print(f" Environments: {args.num_envs} | Exploration: {args.exploration} | Device: {args.device}")
    print(f" Checkpoint:   {model_path}")
    print(f" TensorBoard:  {log_dir}")
    print("=" * 60)

    # Initialize RND module if requested
    rnd_module = None
    if args.exploration == "RND":
        rnd_module = RNDModule(device=args.device)

    # Create vectorized environment
    print("Creating vectorized environment...")
    vec_env = create_vectorized_env(
        env_name=args.env_name,
        num_envs=args.num_envs,
        n_stack=2,
        render_mode=args.render_mode,
        exploration_mode=args.exploration,
    )

    # Load or initialize PPO model
    model_file_zip = model_path.with_suffix(".zip")
    if model_file_zip.exists():
        print(f"Loading existing model from {model_file_zip}...")
        model = PPO.load(str(model_path), env=vec_env, device=args.device)
        model.tensorboard_log = str(log_dir)
        model.ent_coef = args.ent_coef
        if args.exploration == "RND" and rnd_path.exists():
            print(f"Loading RND checkpoint from {rnd_path}...")
            rnd_module.load(str(rnd_path))
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
    reward_callback = RewardTrackingCallback(rnd_callback=None)
    logging_callback = ComprehensiveLoggingCallback()
    callbacks = [reward_callback, logging_callback]

    if args.exploration == "RND":
        rnd_callback = RNDCallback(rnd_module, beta=args.rnd_beta, debug=True)
        reward_callback.rnd_callback = rnd_callback
        callbacks.append(rnd_callback)

    try:
        model.learn(
            total_timesteps=target_steps,
            callback=callbacks,
            tb_log_name=run_name,
            reset_num_timesteps=False,
        )

        rewards = reward_callback.get_rewards()
        print("\n" + "=" * 50)
        print(" TRAINING RUN COMPLETE - REWARD SUMMARY")
        print("=" * 50)
        print(f" Extrinsic Reward : {rewards['extrinsic']:.2f}")
        print(f" Intrinsic Reward : {rewards['intrinsic']:.2f}")
        print(f" Total Reward     : {rewards['total']:.2f}")
        print("=" * 50 + "\n")

        print(f"Saving model to {model_path}...")
        model.save(str(model_path))
        if args.exploration == "RND":
            print(f"Saving RND model to {rnd_path}...")
            rnd_module.save(str(rnd_path))
        print("Save complete.")

    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current weights...")
        model.save(str(model_path))
        if args.exploration == "RND":
            rnd_module.save(str(rnd_path))
    finally:
        vec_env.close()


if __name__ == "__main__":
    main()

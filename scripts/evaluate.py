"""
Evaluation and Rendering Script for Pokemon FireRed AI.
Loads a trained PPO policy checkpoint and runs it with live rendering.
"""
import argparse
from pathlib import Path
import sys
import time
from stable_baselines3 import PPO

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import create_vectorized_env

ENV_NAME = "PokemonFireRed-GBA"


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate trained Pokemon FireRed Agent")
    parser.add_argument("--model-path", type=str, required=True, help="Path to trained .zip model file")
    parser.add_argument("--episodes", type=int, default=3, help="Number of episodes to evaluate")
    parser.add_argument("--device", type=str, default="cuda", help="Device to run inference on (cuda/cpu)")
    parser.add_argument("--delay", type=float, default=0.016, help="Delay per step in seconds for human watching")
    parser.add_argument("--render-mode", type=str, default="human", choices=["human", "none"], help="Render mode")
    parser.add_argument("--max-steps", type=int, default=500, help="Max steps per episode")
    return parser.parse_args()


def main():
    args = parse_args()
    model_path = Path(args.model_path)
    if not model_path.exists() and model_path.with_suffix(".zip").exists():
        model_path = model_path.with_suffix(".zip")

    if not model_path.exists():
        print(f"Error: Model not found at '{model_path}'")
        sys.exit(1)

    render_mode = "human" if args.render_mode == "human" else None

    print("=" * 50)
    print(f" Evaluating Model: {model_path}")
    print(f" Device: {args.device} | Target Episodes: {args.episodes} | Render: {render_mode}")
    print("=" * 50)

    # Create a single environment
    env = create_vectorized_env(
        env_name=ENV_NAME,
        num_envs=1,
        n_stack=2,
        render_mode=render_mode,
        exploration_mode="NONE",
    )

    print(f"Loading weights from {model_path}...")
    model = PPO.load(str(model_path), env=env, device=args.device)

    for episode in range(1, args.episodes + 1):
        obs = env.reset()
        episode_reward = 0.0
        step_count = 0
        done = False

        print(f"\n--- Starting Episode {episode}/{args.episodes} ---")

        try:
            while not done:
                action, _states = model.predict(obs, deterministic=False)
                obs, reward, dones, infos = env.step(action)
                episode_reward += float(reward[0])
                step_count += 1
                done = bool(dones[0]) or (args.max_steps is not None and step_count >= args.max_steps)

                if reward[0] != 0:
                    print(f"Step {step_count} | Reward: {reward[0]:+.2f} | Total: {episode_reward:+.2f}")

                if infos[0].get("faints_this_step", 0) > 0:
                    print(f"[EVENT] Opponent Pokemon fainted at step {step_count}!")

                if args.delay > 0:
                    time.sleep(args.delay)

        except KeyboardInterrupt:
            print("\nEvaluation paused by user.")
            break

        print(f"Episode {episode} Finished! Total Steps: {step_count} | Total Reward: {episode_reward:.2f}")

    env.close()
    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()

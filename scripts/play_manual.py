"""
Interactive Manual Control Script.
Allows human play via keyboard to test controls, game events, RAM reading, and rewards.
Works natively on Windows (msvcrt) and Linux/macOS (termios).

Controls:
  W A S D : Movement (UP, LEFT, DOWN, RIGHT)
  Z       : B button (run / cancel)
  X       : A button (interact / confirm)
  Q       : Quit
"""
import sys
import time
from pathlib import Path
import retro
import retro.data

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import register_custom_integrations
from pokefirered.keyboard_input import KeyboardInput, key_to_action
from pokefirered.wrappers import ActionFilterWrapper, CustomRewardEnv

import argparse

ENV_NAME = "PokemonFireRed-GBA"


def parse_args():
    parser = argparse.ArgumentParser(description="Manual Control Mode for Pokemon FireRed")
    parser.add_argument("--render-mode", type=str, default="human", choices=["human", "none"], help="Render mode")
    parser.add_argument("--max-steps", type=int, default=None, help="Maximum steps to run before exiting")
    return parser.parse_args()


def main():
    args = parse_args()
    render_mode = "human" if args.render_mode == "human" else None

    print("\n" + "=" * 45)
    print(" Pokemon FireRed - Manual Test Mode")
    print("=" * 45)
    print("Controls:")
    print("  W A S D : Movement (UP, LEFT, DOWN, RIGHT)")
    print("  Z       : B button")
    print("  X       : A button")
    print("  Q       : Quit\n")

    register_custom_integrations()

    base_env = retro.make(
        ENV_NAME,
        render_mode=render_mode,
        inttype=retro.data.Integrations.ALL,
    )
    env = CustomRewardEnv(base_env, env_id=0, exploration_mode="NONE")
    env = ActionFilterWrapper(env)

    obs, info = env.reset()
    step_num = 0

    print("Game started. Press keys inside this console to send actions.")

    with KeyboardInput() as kbd:
        try:
            while True:
                key = kbd.get_key()
                if key == "q":
                    print("\nQuitting manual mode...")
                    break

                action = key_to_action(key)
                obs, reward, terminated, truncated, info = env.step(action)
                step_num += 1

                if args.max_steps is not None and step_num >= args.max_steps:
                    print(f"\nReached max steps ({args.max_steps}), exiting manual test...")
                    break

                if reward != 0:
                    print(f"[MANUAL] Step {step_num} | Reward: {reward:+.2f}")

                if info.get("faints_this_step", 0) > 0:
                    print(f"[MANUAL] Opponent faint detected at step {step_num}!")

                if terminated or truncated:
                    print("[MANUAL] Episode reset triggered.")
                    obs, info = env.reset()

                # Small throttle for smooth human rendering when idle
                time.sleep(0.016)

        except KeyboardInterrupt:
            print("\nStopped by user.")
        finally:
            env.close()


if __name__ == "__main__":
    main()

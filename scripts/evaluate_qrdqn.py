"""
Dedicated Evaluation, Live Rendering, and Inspection Script for QR-DQN in Pokemon FireRed AI.
Allows instant live evaluation of trained Distributional QR-DQN policies:
  - Run with simple shorthand: python scripts/evaluate_qrdqn.py --mode RND --render
  - Supports live Q-value / quantile inspection, warp detection, and oscillation analysis.
  - Supports GIF recording and milestone keyframe screenshots.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
import time
import imageio
import numpy as np
from PIL import Image
import torch

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import register_custom_integrations, create_vectorized_env
from pokefirered.models import QRDQNAgent

ENV_NAME = "PokemonFireRed-GBA"
ACTION_NAMES = ["B", "UP", "DOWN", "LEFT", "RIGHT", "A"]

PRESET_MODELS = {
    "NONE": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-NONE-8env.pth",
    "COORD": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-COORD-8env.pth",
    "RND": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-RND-8env.pth",
    "SSIM": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-SSIM-8env.pth",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate and Visually Inspect QR-DQN Pokemon FireRed Agent")
    parser.add_argument(
        "--mode",
        type=str,
        default="RND",
        choices=["RND", "SSIM", "COORD", "NONE"],
        help="Benchmark curiosity mode preset to evaluate (default: RND)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Explicit path to a .pth QR-DQN model checkpoint (overrides --mode)",
    )
    parser.add_argument(
        "--render",
        "-r",
        action="store_true",
        help="Enable live human render mode window (visualize gameplay live)",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=1,
        help="Number of episodes to evaluate (default: 1)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=1000,
        help="Maximum steps per episode (default: 1000)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.015,
        help="Delay per step in seconds for human watching (default: 0.015s)",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.05,
        help="Exploration rate for action selection (default: 0.05; use 0.0 for pure greedy)",
    )
    parser.add_argument(
        "--record-gif",
        action="store_true",
        help="Record and save animated evaluation GIF",
    )
    parser.add_argument(
        "--output-gif",
        type=str,
        default=None,
        help="Custom output path for recorded GIF",
    )
    parser.add_argument(
        "--save-keyframes",
        action="store_true",
        help="Save milestone keyframe screenshots",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Inference device (default: cuda)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    register_custom_integrations()

    # Determine model path
    if args.model_path is not None:
        model_path = Path(args.model_path)
    else:
        model_path = PRESET_MODELS.get(args.mode.upper(), PRESET_MODELS["RND"])

    if not model_path.exists():
        print(f"[ERROR] QR-DQN checkpoint not found at: {model_path}")
        print("Available presets in checkpoints/benchmark_pure/:")
        for k, v in PRESET_MODELS.items():
            print(f"  --mode {k:5s} -> {v.name} (exists: {v.exists()})")
        sys.exit(1)

    model_name = model_path.stem
    render_mode = "human" if args.render else None

    # Setup directories
    gif_dir = PROJECT_ROOT / "eval_recordings"
    gif_dir.mkdir(parents=True, exist_ok=True)
    output_gif = Path(args.output_gif) if args.output_gif else gif_dir / f"eval_qrdqn_{model_name}.gif"

    keyframes_dir = PROJECT_ROOT / "visual_evidence" / "benchmark_inspections" / model_name
    if args.save_keyframes:
        keyframes_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" POKÉMON FIRERED AI: DISTRIBUTIONAL QR-DQN EVALUATOR")
    print(f" Model Name   : {model_name}")
    print(f" Model Path   : {model_path}")
    print(f" Render Mode  : {'HUMAN (Interactive Window)' if args.render else 'HEADLESS'}")
    print(f" Device       : {args.device} | Epsilon: {args.epsilon} | Delay: {args.delay}s")
    print(f" Horizon      : {args.episodes} episode(s) up to {args.max_steps} steps")
    print("=" * 70)

    # Initialize environment
    env = create_vectorized_env(
        env_name=ENV_NAME,
        num_envs=1,
        n_stack=2,
        render_mode=render_mode,
        exploration_mode="NONE",
    )

    # Initialize QR-DQN Agent
    agent = QRDQNAgent(
        in_channels=env.observation_space.shape[0],
        num_actions=env.action_space.n,
        device=args.device,
    )
    agent.load(model_path)

    all_episode_summaries = []

    for episode in range(1, args.episodes + 1):
        obs = env.reset()
        episode_reward = 0.0
        step_count = 0
        done = False

        recorded_frames = []
        visited_coords = set()
        visited_maps = set()
        coord_history = []
        action_counter = Counter()

        last_map = None

        print(f"\n--- Starting Evaluation Episode {episode}/{args.episodes} ---")

        try:
            while not done:
                # Capture frame for GIF
                if args.record_gif:
                    raw_screen = env.env_method("get_screen")[0]
                    recorded_frames.append(raw_screen)

                # Q-value inspection on observation
                with torch.no_grad():
                    s_tensor = torch.as_tensor(obs[0:1], dtype=torch.float32, device=args.device) / 255.0
                    q_vals = agent.online_net.get_q_values(s_tensor)[0].cpu().numpy()

                action = agent.select_action(obs[0], epsilon=args.epsilon)
                obs, reward, dones, infos = env.step([action])
                info = infos[0]

                action_name = ACTION_NAMES[action] if action < len(ACTION_NAMES) else str(action)
                action_counter[action_name] += 1

                map_bank = info.get("map_bank", 0)
                map_num = info.get("map_num", 0)
                pos_x = info.get("pos_x", 0)
                pos_y = info.get("pos_y", 0)

                current_map = (map_bank, map_num)
                current_coord = (map_bank, map_num, pos_x, pos_y)

                visited_coords.add(current_coord)
                visited_maps.add(current_map)
                coord_history.append((pos_x, pos_y))

                episode_reward += float(reward[0])
                step_count += 1
                done = bool(dones[0]) or (args.max_steps is not None and step_count >= args.max_steps)

                # Check for room transitions (warp)
                is_warp = (last_map is not None and current_map != last_map)
                is_milestone = (step_count in [1, 50, 100, 200, 400, 600, 800, args.max_steps])

                if is_warp:
                    print(f"  [WARP DETECTED @ Step {step_count:4d}] Map: {last_map} -> {current_map} | Pos: ({pos_x}, {pos_y}) | Action: {action_name}")
                elif is_milestone:
                    q_str = " | ".join(f"{ACTION_NAMES[a]}:{q_vals[a]:.2f}" for a in range(len(ACTION_NAMES)))
                    print(f"  [Step {step_count:4d}/{args.max_steps}] Pos: ({pos_x:2d}, {pos_y:2d}) | Tiles: {len(visited_coords):3d} | Q: [{q_str}]")

                if args.save_keyframes and (is_warp or is_milestone):
                    raw_screen = env.env_method("get_screen")[0]
                    img = Image.fromarray(raw_screen)
                    tag = "warp" if is_warp else f"step_{step_count:04d}"
                    img_path = keyframes_dir / f"ep{episode}_{tag}_map{map_bank}_{map_num}_x{pos_x}_y{pos_y}.png"
                    img.save(str(img_path))

                last_map = current_map

                if args.render and args.delay > 0:
                    time.sleep(args.delay)

        except KeyboardInterrupt:
            print("\nEvaluation interrupted by user.")
            break

        # Oscillation / Pacing Metric
        oscillation_count = sum(1 for i in range(2, len(coord_history)) if coord_history[i] == coord_history[i - 2])
        oscillation_rate = (oscillation_count / max(1, len(coord_history) - 2)) * 100.0
        coord_counts = Counter(coord_history).most_common(5)

        summary = {
            "episode": episode,
            "model": model_name,
            "total_steps": step_count,
            "total_reward": round(episode_reward, 2),
            "unique_tiles_visited": len(visited_coords),
            "unique_maps_visited": len(visited_maps),
            "visited_maps_list": [list(m) for m in visited_maps],
            "reached_pallet_overworld": (3, 0) in visited_maps,
            "oscillation_rate_pct": round(oscillation_rate, 1),
            "action_distribution": dict(action_counter),
            "top_frequented_coords": [{"pos": pos, "visits": count} for pos, count in coord_counts],
        }
        all_episode_summaries.append(summary)

        print("\n" + "=" * 55)
        print(f" EPISODE {episode} BEHAVIORAL REPORT - {model_name}")
        print("=" * 55)
        print(f" Steps Run             : {step_count}")
        print(f" Reward Accumulated    : {episode_reward:.2f}")
        print(f" Unique Tiles Visited  : {len(visited_coords)}")
        print(f" Unique Maps Visited   : {len(visited_maps)} {list(visited_maps)}")
        print(f" Reached Pallet Town   : {'YES (Map 3,0)' if summary['reached_pallet_overworld'] else 'NO (Confined inside)'}")
        print(f" Oscillation Rate      : {oscillation_rate:.1f}%")
        print(f" Action Distribution   : {dict(action_counter)}")
        print(f" Top Frequented Tiles  : {coord_counts[:3]}")
        print("=" * 55 + "\n")

        # Save animated GIF if requested
        if args.record_gif and recorded_frames:
            print(f"Saving evaluation GIF to {output_gif} (subsampling 15 fps)...")
            subsampled = recorded_frames[::2]
            imageio.mimsave(str(output_gif), subsampled, fps=15, loop=0)
            print(f"GIF saved successfully ({len(subsampled)} frames).")

    env.close()

    # Save Behavioral Inspection JSON
    inspection_report_path = keyframes_dir / "behavioral_inspection.json" if args.save_keyframes else gif_dir / f"inspection_{model_name}.json"
    with open(inspection_report_path, "w", encoding="utf-8") as f:
        json.dump(all_episode_summaries, f, indent=2)
    print(f"Inspection metrics saved to: {inspection_report_path}\n")


if __name__ == "__main__":
    main()

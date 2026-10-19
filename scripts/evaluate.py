"""
Evaluation, Rendering, and Visual Inspection Script for Pokemon FireRed AI.
Loads a trained PPO policy checkpoint, runs evaluation episodes with optional live
rendering, records animated GIFs, captures keyframe images of agent behavior, and
generates structured behavioral reports.
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
from stable_baselines3 import PPO

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import create_vectorized_env

ENV_NAME = "PokemonFireRed-GBA"
ACTION_NAMES = ["B", "UP", "DOWN", "LEFT", "RIGHT", "A"]


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate and Visually Inspect Pokemon FireRed Agent")
    parser.add_argument("--model-path", type=str, required=True, help="Path to trained .zip model file")
    parser.add_argument("--episodes", type=int, default=1, help="Number of episodes to evaluate")
    parser.add_argument("--device", type=str, default="cuda", help="Device to run inference on (cuda/cpu)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay per step in seconds for human watching")
    parser.add_argument("--render-mode", type=str, default="none", choices=["human", "none"], help="Render mode")
    parser.add_argument("--max-steps", type=int, default=600, help="Max steps per episode")
    parser.add_argument("--record-gif", action="store_true", help="Record and save animated evaluation GIF")
    parser.add_argument("--output-gif", type=str, default=None, help="Output path for recorded GIF")
    parser.add_argument("--save-keyframes", action="store_true", help="Save milestone keyframe screenshots")
    parser.add_argument("--keyframes-dir", type=str, default=None, help="Directory to save keyframe screenshots")
    parser.add_argument("--deterministic", action="store_true", help="Use deterministic policy actions")
    return parser.parse_args()


def main():
    args = parse_args()
    model_path = Path(args.model_path)
    if not model_path.exists():
        if model_path.with_suffix(".pth").exists():
            model_path = model_path.with_suffix(".pth")
        elif model_path.with_suffix(".zip").exists():
            model_path = model_path.with_suffix(".zip")

    if not model_path.exists():
        print(f"Error: Model not found at '{model_path}'")
        sys.exit(1)

    render_mode = "human" if args.render_mode == "human" else None
    model_name = model_path.stem
    is_qrdqn = model_path.suffix == ".pth" or "QRDQN" in model_path.name

    if args.output_gif is None:
        gif_dir = PROJECT_ROOT / "eval_recordings"
        gif_dir.mkdir(parents=True, exist_ok=True)
        output_gif = gif_dir / f"eval_{model_name}.gif"
    else:
        output_gif = Path(args.output_gif)
        output_gif.parent.mkdir(parents=True, exist_ok=True)

    if args.keyframes_dir is None:
        keyframes_dir = PROJECT_ROOT / "visual_evidence" / "benchmark_inspections" / model_name
    else:
        keyframes_dir = Path(args.keyframes_dir)
    if args.save_keyframes:
        keyframes_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f" Visually Inspecting Policy: {model_name} ({'QR-DQN' if is_qrdqn else 'PPO'})")
    print(f" Model Path:      {model_path}")
    print(f" Device:          {args.device} | Episodes: {args.episodes} | Max Steps: {args.max_steps}")
    print(f" Deterministic:   {args.deterministic}")
    print(f" Record GIF:      {args.record_gif} -> {output_gif if args.record_gif else 'Disabled'}")
    print(f" Save Keyframes:  {args.save_keyframes} -> {keyframes_dir if args.save_keyframes else 'Disabled'}")
    print("=" * 60)

    env = create_vectorized_env(
        env_name=ENV_NAME,
        num_envs=1,
        n_stack=2,
        render_mode=render_mode,
        exploration_mode="NONE",
    )

    print(f"Loading weights from {model_path}...")
    if is_qrdqn:
        from pokefirered.models import QRDQNAgent
        agent = QRDQNAgent(
            in_channels=env.observation_space.shape[0],
            num_actions=env.action_space.n,
            device=args.device,
        )
        agent.load(model_path)
        model = None
    else:
        model = PPO.load(str(model_path), env=env, device=args.device)
        agent = None

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
        keyframe_saved_count = 0

        print(f"\n--- Starting Visual Evaluation Episode {episode}/{args.episodes} ---")

        try:
            while not done:
                # Capture high-res RGB emulator frame
                raw_screen = env.env_method("get_screen")[0]
                if args.record_gif:
                    recorded_frames.append(raw_screen)

                if is_qrdqn:
                    act = agent.select_action(obs[0], epsilon=0.0 if args.deterministic else 0.05)
                    action = [act]
                else:
                    action, _states = model.predict(obs, deterministic=args.deterministic)
                obs, reward, dones, infos = env.step(action)
                info = infos[0]

                action_idx = int(action[0])
                action_name = ACTION_NAMES[action_idx] if action_idx < len(ACTION_NAMES) else str(action_idx)
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

                # Check for significant events to save keyframes
                is_warp = (last_map is not None and current_map != last_map)
                is_milestone = (step_count in [1, 50, 100, 200, 300, 400, 500, args.max_steps])

                if args.save_keyframes and (is_warp or is_milestone):
                    img = Image.fromarray(raw_screen)
                    tag = "warp" if is_warp else f"step_{step_count:04d}"
                    img_path = keyframes_dir / f"ep{episode}_{tag}_map{map_bank}_{map_num}_x{pos_x}_y{pos_y}.png"
                    img.save(str(img_path))
                    keyframe_saved_count += 1

                if is_warp:
                    print(f"  [WARP DETECTED @ Step {step_count}] Map changed: {last_map} -> {current_map} | Pos: ({pos_x}, {pos_y})")

                last_map = current_map

                if args.delay > 0:
                    time.sleep(args.delay)

        except KeyboardInterrupt:
            print("\nEvaluation interrupted by user.")
            break

        # Behavioral Analysis
        # Calculate stuck / oscillation metric: fraction of steps where position matches position 2 or 4 steps ago
        oscillation_count = 0
        for i in range(2, len(coord_history)):
            if coord_history[i] == coord_history[i - 2]:
                oscillation_count += 1
        oscillation_rate = (oscillation_count / max(1, len(coord_history) - 2)) * 100.0

        # Most visited coordinates
        coord_counts = Counter(coord_history).most_common(5)

        summary = {
            "episode": episode,
            "total_steps": step_count,
            "total_reward": round(episode_reward, 2),
            "unique_tiles_visited": len(visited_coords),
            "unique_maps_visited": len(visited_maps),
            "visited_maps_list": list(visited_maps),
            "oscillation_rate_pct": round(oscillation_rate, 1),
            "action_distribution": dict(action_counter),
            "top_frequented_coords": [{"pos": pos, "visits": count} for pos, count in coord_counts],
            "reached_pallet_overworld": (3, 0) in visited_maps,
        }
        all_episode_summaries.append(summary)

        print("\n" + "-" * 50)
        print(f" EPISODE {episode} BEHAVIORAL REPORT")
        print("-" * 50)
        print(f" Steps Run             : {step_count}")
        print(f" Reward Accumulated    : {episode_reward:.2f}")
        print(f" Unique Tiles Visited  : {len(visited_coords)}")
        print(f" Unique Maps Visited   : {len(visited_maps)} {list(visited_maps)}")
        print(f" Reached Overworld     : {'YES (Map 3,0)' if summary['reached_pallet_overworld'] else 'NO (Confined inside)'}")
        print(f" Oscillation/Pacing %  : {oscillation_rate:.1f}%")
        print(f" Action Distribution   : {dict(action_counter)}")
        print(f" Top Frequented Tiles  : {coord_counts[:3]}")
        print("-" * 50)

        # Save animated GIF
        if args.record_gif and recorded_frames:
            print(f"Saving evaluation GIF to {output_gif} (subsampling 15 fps)...")
            subsampled = recorded_frames[::2]
            imageio.mimsave(str(output_gif), subsampled, fps=15, loop=0)
            print(f"GIF saved successfully ({len(subsampled)} frames).")

    env.close()

    # Save Behavioral Inspection JSON
    inspection_report_path = keyframes_dir / "behavioral_inspection.json" if args.save_keyframes else output_gif.parent / f"inspection_{model_name}.json"
    with open(inspection_report_path, "w", encoding="utf-8") as f:
        json.dump(all_episode_summaries, f, indent=2)
    print(f"\nInspection data written to: {inspection_report_path}\n")


if __name__ == "__main__":
    main()

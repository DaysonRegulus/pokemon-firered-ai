"""
Benchmark Exploration Swarm Visualizer (NONE vs SSIM vs RND vs COORD).
Rolls out the 4 trained benchmark policies for either PPO or QR-DQN (+ PER),
compositing authentic 32-bit GBA Pokémon FireRed/LeafGreen player avatars
differentiated by colors:
  - NONE (Control): Crimson Red (240, 60, 60)
  - SSIM (Perceptual): Bright Orange (255, 140, 0)
  - RND (Neural): Electric Cyan (0, 210, 255)
  - COORD (Spatial): Emerald Green (40, 230, 60)
Displays real-time side-by-side exploration divergence across Kanto.
"""
import argparse
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import torch
from stable_baselines3 import PPO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import register_custom_integrations, create_vectorized_env
from pokefirered.visualization import KantoWorldMapper, SwarmRenderer
from pokefirered.models import QRDQNAgent

BENCHMARK_PALETTE = {
    "NONE": (240, 60, 60),     # Crimson Red (Control Baseline)
    "SSIM": (255, 140, 0),    # Bright Orange (Perceptual Curiosity)
    "RND": (0, 210, 255),     # Electric Cyan (Neural RND Curiosity)
    "COORD": (40, 230, 60),   # Emerald Green (Count-based Spatial Curiosity)
}

BENCHMARK_MODELS_PPO = {
    "NONE": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-NONE-8env.zip",
    "SSIM": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-SSIM-8env.zip",
    "RND": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-RND-8env.zip",
    "COORD": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-COORD-8env.zip",
}

BENCHMARK_METRICS_PPO = {
    "NONE": {"tiles": 422, "maps": 5, "desc": "Control (422 tiles)"},
    "SSIM": {"tiles": 414, "maps": 5, "desc": "Perceptual (414 tiles)"},
    "RND": {"tiles": 368, "maps": 4, "desc": "Neural RND (368 tiles)"},
    "COORD": {"tiles": 580, "maps": 6, "desc": "Spatial (580 tiles)"},
}

BENCHMARK_MODELS_QRDQN = {
    "NONE": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-NONE-8env.pth",
    "SSIM": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-SSIM-8env.pth",
    "RND": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-RND-8env.pth",
    "COORD": PROJECT_ROOT / "checkpoints" / "benchmark_pure" / "PokemonFireRed-GBA-QRDQN-COORD-8env.pth",
}

BENCHMARK_METRICS_QRDQN = {
    "NONE": {"tiles": 357, "maps": 5, "desc": "Control (357 tiles)"},
    "COORD": {"tiles": 393, "maps": 4, "desc": "Spatial (393 tiles)"},
    "RND": {"tiles": 429, "maps": 5, "desc": "Neural RND (429 tiles)"},
    "SSIM": {"tiles": 478, "maps": 4, "desc": "Perceptual (478 tiles)"},
}

BASE_RAM = 0x02000000


def collect_real_policy_trajectories(
    model_path: Path,
    algo: str = "QRDQN",
    num_agents: int = 8,
    steps_per_agent: int = 240,
    device: str = "cpu"
) -> List[List[Tuple[int, int, int, int]]]:
    """
    Executes trained policy in parallel GBA emulators, recording
    ground-truth (bank, num, x, y) coordinates from RAM at every step.
    """
    print(f"  [ROLLOUT] Initializing {num_agents} GBA emulators for {model_path.name} ({algo})...")
    env = create_vectorized_env("PokemonFireRed-GBA", num_envs=num_agents, n_stack=2, exploration_mode="NONE")
    obs = env.reset()

    if algo == "PPO":
        model = PPO.load(str(model_path), env=env, device=device)
        agent = None
    else:
        agent = QRDQNAgent(
            in_channels=env.observation_space.shape[0],
            num_actions=env.action_space.n,
            device=device,
        )
        agent.load(model_path)
        model = None

    trajectories = [[] for _ in range(num_agents)]
    visited_tiles = set()

    t0 = time.time()
    for step in range(steps_per_agent):
        if algo == "PPO":
            actions, _ = model.predict(obs, deterministic=False)
        else:
            actions = agent.select_actions(obs, epsilon=0.05)
        obs, rewards, dones, infos = env.step(actions)

        # Extract real coordinates from infos / RAM
        for i in range(num_agents):
            info = infos[i]
            mb = int(info.get("map_bank", 4))
            mn = int(info.get("map_num", 0))

            # Read layout coordinates: display_coord - 7 or pos_x - 7
            raw_x = int(info.get("pos_x", 14))
            raw_y = int(info.get("pos_y", 14))
            x = max(0, raw_x - 7) if raw_x >= 7 else raw_x
            y = max(0, raw_y - 7) if raw_y >= 7 else raw_y

            coord = (mb, mn, x, y)
            trajectories[i].append(coord)
            visited_tiles.add(coord)

        if (step + 1) % 60 == 0 or step == steps_per_agent - 1:
            print(f"    Step {step+1:3d}/{steps_per_agent} | Cumulative unique tiles: {len(visited_tiles)}")

    env.close()
    elapsed = time.time() - t0
    print(f"  [OK] Rollout completed in {elapsed:.1f}s | {len(visited_tiles)} unique tiles visited.")
    return trajectories


def main():
    parser = argparse.ArgumentParser(description="Benchmark Exploration Swarm Visualizer")
    parser.add_argument("--algo", type=str, default="QRDQN", choices=["PPO", "QRDQN"], help="Algorithm to visualize (default: QRDQN)")
    parser.add_argument("--steps", type=int, default=240, help="Steps per agent (default: 240)")
    parser.add_argument("--num-agents", type=int, default=8, help="Number of agents per condition (default: 8)")
    parser.add_argument("--force-rollout", action="store_true", help="Force new evaluation rollout instead of loading saved training trajectories")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Inference device")
    args = parser.parse_args()

    register_custom_integrations()

    algo = args.algo.upper()
    print("=" * 80)
    print(f" POKÉMON FIRERED GBA: 4-WAY {algo} EXPLORATION SWARM VISUALIZER")
    print(" Comparing: NONE vs SSIM vs RND vs COORD")
    print(" Differentiated by Authentic Tinted GBA Avatars & Real Trajectories")
    print("=" * 80)

    output_dir = PROJECT_ROOT / "visual_evidence" / "swarm_visualizer"
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = PROJECT_ROOT / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    if algo == "QRDQN":
        models_dict = BENCHMARK_MODELS_QRDQN
        metrics_dict = BENCHMARK_METRICS_QRDQN
        video_path = output_dir / "qrdqn_swarm_comparison.mp4"
        gif_path = media_dir / "qrdqn_swarm_comparison.gif"
        showcase_gif = media_dir / "kanto_swarm_showcase.gif"
        title_prefix = "POKEMON FIRERED: QR-DQN (+ PER) BENCHMARK SWARM"
    else:
        models_dict = BENCHMARK_MODELS_PPO
        metrics_dict = BENCHMARK_METRICS_PPO
        video_path = output_dir / "benchmark_swarm_comparison.mp4"
        gif_path = media_dir / "benchmark_swarm_comparison.gif"
        showcase_gif = media_dir / "kanto_swarm_showcase.gif"
        title_prefix = "POKEMON FIRERED: PPO BENCHMARK SWARM"

    num_agents_per_mode = args.num_agents
    steps_per_agent = args.steps
    trajectories_by_mode: Dict[str, List[List[Tuple[int, int, int, int]]]] = {}

    for mode, model_path in models_dict.items():
        cache_file = output_dir / f"benchmark_trajectories_{algo}_{mode}.json"
        checkpoint_dir = model_path.parent
        train_traj_file = checkpoint_dir / f"{model_path.stem}_trajectories.json"

        # 1. Prioritize official recorded training trajectories from the benchmark run
        if train_traj_file.exists() and not args.force_rollout:
            print(f"\n[BENCHMARK TRAJECTORY] Loading recorded training trajectories for {mode} from {train_traj_file.name}...")
            with open(train_traj_file, "r", encoding="utf-8") as f:
                raw_trajs = json.load(f)

            trajectories_by_mode[mode] = []
            for agent_traj in raw_trajs[:num_agents_per_mode]:
                if len(agent_traj) > steps_per_agent:
                    # Stride evenly across the full 102.4k training history for cinematic timelapse
                    stride = len(agent_traj) / steps_per_agent
                    sampled = [agent_traj[int(i * stride)] for i in range(steps_per_agent)]
                    trajectories_by_mode[mode].append([(pt[0], pt[1], pt[2], pt[3]) for pt in sampled])
                else:
                    trajectories_by_mode[mode].append([(pt[0], pt[1], pt[2], pt[3]) for pt in agent_traj])
            total_logged_pts = len(raw_trajs[0]) * len(raw_trajs)
            print(f"  Loaded {len(trajectories_by_mode[mode])} agents (timelapsed from {total_logged_pts:,} training steps into {steps_per_agent} visual frames).")

        elif cache_file.exists() and not args.force_rollout:
            print(f"\n[CACHE] Loading real cached trajectories for {mode} from {cache_file.name}...")
            with open(cache_file, "r") as f:
                data = json.load(f)
                trajectories_by_mode[mode] = [
                    [(pt[0], pt[1], pt[2], pt[3]) for pt in traj]
                    for traj in data
                ]
            print(f"  Loaded {len(trajectories_by_mode[mode])} agents, {len(trajectories_by_mode[mode][0])} steps each.")
        else:
            print(f"\n[EXECUTION] Collecting real emulator trajectories for {mode}...")
            if not model_path.exists():
                raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
            trajs = collect_real_policy_trajectories(
                model_path=model_path,
                algo=algo,
                num_agents=num_agents_per_mode,
                steps_per_agent=steps_per_agent,
                device=args.device,
            )
            trajectories_by_mode[mode] = trajs

            # Save cache file
            with open(cache_file, "w") as f:
                json.dump(trajs, f)
            print(f"  Cached real trajectories to {cache_file.name}")

    # Build multi-condition legend and tiles dictionary
    custom_legend = [
        ("NONE", f"NONE: Control ({metrics_dict['NONE']['tiles']})"),
        ("COORD", f"COORD: Spatial ({metrics_dict['COORD']['tiles']})"),
        ("RND", f"RND: Neural ({metrics_dict['RND']['tiles']})"),
        ("SSIM", f"SSIM: Perceptual ({metrics_dict['SSIM']['tiles']})"),
    ]
    group_tiles = {
        "NONE": metrics_dict["NONE"]["tiles"],
        "COORD": metrics_dict["COORD"]["tiles"],
        "RND": metrics_dict["RND"]["tiles"],
        "SSIM": metrics_dict["SSIM"]["tiles"],
    }

    # Render Swarm Visualization
    print("\n" + "=" * 80)
    print(f" RENDERING 4-WAY COMPARATIVE SWARM ANIMATION ({algo})")
    print(f" Video Output: {video_path}")
    print(f" GIF Output:   {gif_path}")
    print(" Viewport:     760x480 (Widescreen)")
    print(" Pacing:       125ms per frame (~8 fps) with intro/outro holds")
    print("=" * 80)

    renderer = SwarmRenderer(viewport_w=760, viewport_h=480)
    renderer.generate_timelapse(
        trajectories_by_gen=trajectories_by_mode,
        output_video_path=video_path,
        output_gif_path=gif_path,
        fps=15,
        trail_length=14,
        gif_duration_ms=125,
        gif_frame_skip=2,
        intro_hold_frames=15,
        outro_hold_frames=30,
        custom_palette=BENCHMARK_PALETTE,
        custom_title=title_prefix,
        custom_legend=custom_legend,
        group_tiles=group_tiles
    )

    # Also update media/kanto_swarm_showcase.gif
    import shutil
    shutil.copyfile(gif_path, showcase_gif)
    print(f"[OK] Updated primary showcase GIF: {showcase_gif}")

    # Save keyframe inspections
    import cv2
    print("\nExtracting keyframe comparison stills for visual proof...")
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    keyframe_indices = [
        0,                                   # Intro (Red's house)
        min(45, total_frames - 1),           # Pallet Town divergence
        min(110, total_frames - 1),          # Route 1 frontier push
        min(180, total_frames - 1),          # Route 1 northern corridor
        total_frames - 1                     # Final comparative frontier
    ]
    keyframe_names = [
        f"{algo.lower()}_frame_000_intro.png",
        f"{algo.lower()}_frame_045_pallet_divergence.png",
        f"{algo.lower()}_frame_110_route1_advance.png",
        f"{algo.lower()}_frame_180_corridor_exploration.png",
        f"{algo.lower()}_frame_final_comparison.png",
    ]

    for k_idx, k_name in zip(keyframe_indices, keyframe_names):
        cap.set(cv2.CAP_PROP_POS_FRAMES, k_idx)
        ret, bgr_frame = cap.read()
        if ret:
            out_img_path = output_dir / k_name
            cv2.imwrite(str(out_img_path), bgr_frame)
            print(f"  Saved keyframe: {out_img_path.name} (frame {k_idx})")
    cap.release()

    print("\n" + "=" * 80)
    print(f" 4-WAY {algo} BENCHMARK SWARM VISUALIZATION EXPORT COMPLETE!")
    print(f" Video Path : {video_path}")
    print(f" GIF Path   : {gif_path}")
    print(f" Keyframes  : {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()

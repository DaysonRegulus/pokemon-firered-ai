"""
12-Environment Swarm Visualizer: Head-to-Head Comparison of RND vs SSIM on PPO and QR-DQN.
Loads recorded training trajectories from checkpoints/benchmark_12env and composites
authentic GBA player avatars across Kanto with color-coded badges and metrics.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Dict, List, Tuple
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.visualization import SwarmRenderer

PALETTE_4WAY = {
    "PPO_RND": (0, 210, 255),     # Electric Cyan
    "PPO_SSIM": (255, 140, 0),    # Bright Orange
    "QRDQN_RND": (50, 230, 80),   # Neon Lime Green
    "QRDQN_SSIM": (220, 50, 240), # Electric Magenta
}

PALETTE_PPO = {
    "PPO_RND": (0, 210, 255),
    "PPO_SSIM": (255, 140, 0),
}

PALETTE_QRDQN = {
    "QRDQN_RND": (50, 230, 80),
    "QRDQN_SSIM": (220, 50, 240),
}


def parse_args():
    parser = argparse.ArgumentParser(description="12-Environment Swarm Visualizer")
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="checkpoints/benchmark_12env",
        help="Checkpoints directory containing 12-env runs",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=240,
        help="Number of animation frames in timelapse (default: 240)",
    )
    parser.add_argument(
        "--num-agents",
        type=int,
        default=12,
        help="Number of agents to display per condition (default: 12)",
    )
    return parser.parse_args()


def load_condition_data(checkpoint_dir: Path, algo: str, mode: str, steps: int, max_agents: int):
    prefix = f"PokemonFireRed-GBA-{algo}-{mode}-12env"
    traj_file = checkpoint_dir / f"{prefix}_trajectories.json"
    summary_file = checkpoint_dir / f"{prefix}_summary.json"

    metrics = {"tiles": 0, "maps": 0, "sps": 0.0, "time": 0.0}
    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            metrics["tiles"] = data.get("unique_tiles", 0)
            metrics["maps"] = data.get("unique_maps", 0)
            metrics["sps"] = data.get("sps", 0.0)
            metrics["time"] = data.get("elapsed_seconds", 0.0)

    if not traj_file.exists():
        print(f"[WARN] Trajectory file not found: {traj_file}")
        return [], metrics

    with open(traj_file, "r", encoding="utf-8") as f:
        raw_trajs = json.load(f)

    trajectories = []
    for agent_traj in raw_trajs[:max_agents]:
        if len(agent_traj) > steps:
            stride = len(agent_traj) / steps
            sampled = [agent_traj[int(i * stride)] for i in range(steps)]
            trajectories.append([(pt[0], pt[1], pt[2], pt[3]) for pt in sampled])
        else:
            trajectories.append([(pt[0], pt[1], pt[2], pt[3]) for pt in agent_traj])

    total_logged = sum(len(t) for t in raw_trajs)
    print(f"  Loaded {len(trajectories)} agents for {algo}-{mode} (sampled from {total_logged:,} total steps -> {steps} frames).")
    return trajectories, metrics


def main():
    args = parse_args()
    checkpoint_dir = PROJECT_ROOT / args.checkpoint_dir
    output_dir = PROJECT_ROOT / "visual_evidence" / "swarm_visualizer"
    media_dir = PROJECT_ROOT / "media"
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(" 12-ENVIRONMENT HEAD-TO-HEAD SWARM VISUALIZER: RND vs SSIM")
    print(f" Checkpoint Source : {checkpoint_dir}")
    print(f" Agents per swarm  : {args.num_agents}")
    print(f" Frames in render  : {args.steps}")
    print("=" * 80 + "\n")

    conditions = [
        ("PPO", "RND", "PPO_RND"),
        ("PPO", "SSIM", "PPO_SSIM"),
        ("QRDQN", "RND", "QRDQN_RND"),
        ("QRDQN", "SSIM", "QRDQN_SSIM"),
    ]

    all_trajs = {}
    all_metrics = {}

    for algo, mode, label in conditions:
        print(f"Loading {label} ({algo} - {mode})...")
        trajs, metrics = load_condition_data(checkpoint_dir, algo, mode, args.steps, args.num_agents)
        if trajs:
            all_trajs[label] = trajs
            all_metrics[label] = metrics

    if not all_trajs:
        print("[ERROR] No trajectories found in checkpoint directory. Have the training runs finished?")
        return

    renderer = SwarmRenderer(viewport_w=760, viewport_h=480)

    # 1. Render 4-Way Cross-Algorithmic Factorial Comparison (if all 4 conditions present)
    if len(all_trajs) == 4:
        print("\n" + "=" * 80)
        print(" RENDERING 4-WAY CROSS-ALGORITHMIC SWARM (PPO-RND vs PPO-SSIM vs QRDQN-RND vs QRDQN-SSIM)")
        print("=" * 80)
        video_4way = output_dir / "benchmark_12env_4way_comparison.mp4"
        gif_4way = media_dir / "benchmark_12env_4way_comparison.gif"
        showcase_gif = media_dir / "kanto_swarm_showcase.gif"

        legend_4way = [
            ("PPO_RND", f"PPO RND: ({all_metrics['PPO_RND']['tiles']} tiles)"),
            ("PPO_SSIM", f"PPO SSIM: ({all_metrics['PPO_SSIM']['tiles']} tiles)"),
            ("QRDQN_RND", f"QR-DQN RND: ({all_metrics['QRDQN_RND']['tiles']} tiles)"),
            ("QRDQN_SSIM", f"QR-DQN SSIM: ({all_metrics['QRDQN_SSIM']['tiles']} tiles)"),
        ]
        tiles_4way = {k: all_metrics[k]["tiles"] for k in all_metrics}

        renderer.generate_timelapse(
            trajectories_by_gen=all_trajs,
            output_video_path=video_4way,
            output_gif_path=gif_4way,
            fps=15,
            trail_length=14,
            gif_duration_ms=125,
            gif_frame_skip=2,
            intro_hold_frames=15,
            outro_hold_frames=30,
            custom_palette=PALETTE_4WAY,
            custom_title="POKÉMON FIRERED: 12-ENV PPO vs QR-DQN BENCHMARK",
            custom_legend=legend_4way,
            group_tiles=tiles_4way,
        )
        shutil.copyfile(gif_4way, showcase_gif)
        print(f"[OK] Updated primary showcase GIF: {showcase_gif}")

        # Extract Keyframe Comparison Stills
        cap = cv2.VideoCapture(str(video_4way))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        keyframe_indices = [
            0,
            min(45, total_frames - 1),
            min(110, total_frames - 1),
            min(180, total_frames - 1),
            total_frames - 1,
        ]
        keyframe_names = [
            "12env_frame_000_intro.png",
            "12env_frame_045_pallet_divergence.png",
            "12env_frame_110_route1_advance.png",
            "12env_frame_180_corridor_exploration.png",
            "12env_frame_final_comparison.png",
        ]
        for k_idx, k_name in zip(keyframe_indices, keyframe_names):
            cap.set(cv2.CAP_PROP_POS_FRAMES, k_idx)
            ret, bgr_frame = cap.read()
            if ret:
                out_path = output_dir / k_name
                cv2.imwrite(str(out_path), bgr_frame)
                print(f"  Saved keyframe: {out_path.name}")
        cap.release()

    # 2. Render 2-Way PPO Comparison
    ppo_trajs = {k: all_trajs[k] for k in ["PPO_RND", "PPO_SSIM"] if k in all_trajs}
    if len(ppo_trajs) == 2:
        print("\n" + "=" * 80)
        print(" RENDERING 2-WAY PPO SWARM (RND vs SSIM)")
        print("=" * 80)
        video_ppo = output_dir / "ppo_12env_rnd_vs_ssim.mp4"
        gif_ppo = media_dir / "ppo_12env_rnd_vs_ssim.gif"
        legend_ppo = [
            ("PPO_RND", f"PPO RND: ({all_metrics['PPO_RND']['tiles']} tiles)"),
            ("PPO_SSIM", f"PPO SSIM: ({all_metrics['PPO_SSIM']['tiles']} tiles)"),
        ]
        tiles_ppo = {k: all_metrics[k]["tiles"] for k in ppo_trajs}
        renderer.generate_timelapse(
            trajectories_by_gen=ppo_trajs,
            output_video_path=video_ppo,
            output_gif_path=gif_ppo,
            fps=15,
            trail_length=14,
            gif_duration_ms=125,
            gif_frame_skip=2,
            intro_hold_frames=15,
            outro_hold_frames=30,
            custom_palette=PALETTE_PPO,
            custom_title="POKÉMON FIRERED: 12-ENV PPO (RND vs SSIM)",
            custom_legend=legend_ppo,
            group_tiles=tiles_ppo,
        )

    # 3. Render 2-Way QR-DQN Comparison
    qrdqn_trajs = {k: all_trajs[k] for k in ["QRDQN_RND", "QRDQN_SSIM"] if k in all_trajs}
    if len(qrdqn_trajs) == 2:
        print("\n" + "=" * 80)
        print(" RENDERING 2-WAY QR-DQN SWARM (RND vs SSIM)")
        print("=" * 80)
        video_qrdqn = output_dir / "qrdqn_12env_rnd_vs_ssim.mp4"
        gif_qrdqn = media_dir / "qrdqn_12env_rnd_vs_ssim.gif"
        legend_qrdqn = [
            ("QRDQN_RND", f"QR-DQN RND: ({all_metrics['QRDQN_RND']['tiles']} tiles)"),
            ("QRDQN_SSIM", f"QR-DQN SSIM: ({all_metrics['QRDQN_SSIM']['tiles']} tiles)"),
        ]
        tiles_qrdqn = {k: all_metrics[k]["tiles"] for k in qrdqn_trajs}
        renderer.generate_timelapse(
            trajectories_by_gen=qrdqn_trajs,
            output_video_path=video_qrdqn,
            output_gif_path=gif_qrdqn,
            fps=15,
            trail_length=14,
            gif_duration_ms=125,
            gif_frame_skip=2,
            intro_hold_frames=15,
            outro_hold_frames=30,
            custom_palette=PALETTE_QRDQN,
            custom_title="POKÉMON FIRERED: 12-ENV QR-DQN (RND vs SSIM)",
            custom_legend=legend_qrdqn,
            group_tiles=tiles_qrdqn,
        )

    print("\n" + "=" * 80)
    print(" ALL 12-ENV SWARM VISUALIZATIONS COMPLETE!")
    print(f" Media Directory  : {media_dir}")
    print(f" Video Directory  : {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()

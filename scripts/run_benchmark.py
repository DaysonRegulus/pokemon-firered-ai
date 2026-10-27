"""
Continuous Reinforcement Learning Benchmark: DQN (QR-DQN + PER) vs PPO
with Random Network Distillation (RND) and Dynamic Curriculum Horizon.

Alternating Generation Schedule:
- Gen 1: QR-DQN (4,096 steps) -> PPO (4,096 steps)
- Beyond Gen 1: Dynamic Curriculum formula:
    dynamic_steps = round((MIN_TIMESTEPS + lifetime * GROWTH_RATE) / 2048) * 2048
    with MIN_TIMESTEPS=4096, GROWTH_RATE=0.05.
- State Persistence:
    * QR-DQN: Models, optimizers, and Prioritized Replay Buffer (PER) transitions/priorities
    * PPO: Policy, optimizer, and cumulative num_timesteps
    * RND: Predictor, target, optimizer, and running normalization statistics
- Visual Evidence:
    * Per-generation MP4 and GIF swarm comparison animations
    * Stitched chronological video across generations
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
import cv2
import torch

# Force UTF-8 encoding on standard streams to avoid Windows cp1252 charmap errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def compute_dynamic_timesteps(
    lifetime_steps: int,
    min_steps: int = 4096,
    growth_rate: float = 0.05,
    quantize: int = 2048
) -> int:
    """Computes quantized dynamic curriculum training timesteps."""
    raw = min_steps + (lifetime_steps * growth_rate)
    quantized = int(round(raw / quantize) * quantize)
    return max(quantize, quantized)


def parse_args():
    parser = argparse.ArgumentParser(description="Continuous DQN vs PPO Benchmark with RND & Dynamic Curriculum")
    parser.add_argument("--generations", type=int, default=5, help="Total number of alternating generations (default: 5)")
    parser.add_argument("--num-envs", type=int, default=8, help="Number of parallel environments (default: 8)")
    parser.add_argument("--min-timesteps", type=int, default=4096, help="Base minimum timesteps for Gen 1 (default: 4096)")
    parser.add_argument("--growth-rate", type=float, default=0.05, help="Dynamic curriculum growth rate (default: 0.05)")
    parser.add_argument("--quantize", type=int, default=2048, help="Step quantization quantum (default: 2048)")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints/benchmark_rnd_curriculum", help="Checkpoints directory")
    parser.add_argument("--log-dir", type=str, default="logs/benchmark_rnd_curriculum", help="TensorBoard logs directory")
    parser.add_argument("--visual-dir", type=str, default="visual_evidence/benchmark_rnd_curriculum", help="Visual evidence directory")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Compute device")
    parser.add_argument("--ent-coef", type=float, default=0.08, help="Entropy coefficient for PPO (default: 0.08)")
    parser.add_argument("--epsilon-start", type=float, default=1.0, help="Initial exploration rate for QR-DQN (default: 1.0)")
    parser.add_argument("--epsilon-end", type=float, default=0.20, help="Final exploration rate / epsilon-floor for QR-DQN (default: 0.20)")
    parser.add_argument("--epsilon-decay-steps", type=int, default=5_000_000, help="Epsilon decay steps for QR-DQN (default: 5,000,000)")
    parser.add_argument("--fresh", action="store_true", help="Force fresh benchmark start, ignoring existing benchmark_state.json")
    parser.add_argument("--no-render", action="store_true", help="Disable per-generation swarm rendering and video stitching")
    return parser.parse_args()


def load_state(state_file: Path) -> Dict:
    """Loads benchmark execution state."""
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to read state file {state_file}: {e}")
    return {
        "last_completed_generation": 0,
        "completed_runs": {},  # key: f"gen{g}_{algo}" -> metrics dict
        "qrdqn_lifetime_steps": 0,
        "ppo_lifetime_steps": 0,
        "history": [],
    }


def save_state(state_file: Path, state: Dict):
    """Saves benchmark execution state atomically."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = state_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    temp_file.replace(state_file)


def render_generation_swarm(
    checkpoint_dir: Path,
    visual_dir: Path,
    gen: int,
    num_envs: int = 8,
    steps_render: int = 240
) -> Optional[Path]:
    """Renders side-by-side comparison of QR-DQN vs PPO for generation gen."""
    try:
        from pokefirered.visualization import SwarmRenderer
    except ImportError:
        print("[WARN] Could not import SwarmRenderer, skipping visual rendering.")
        return None

    prefix_dqn = f"PokemonFireRed-GBA-QRDQN-RND-{num_envs}env_gen{gen:03d}"
    prefix_ppo = f"PokemonFireRed-GBA-PPO-RND-{num_envs}env_gen{gen:03d}"

    traj_dqn_file = checkpoint_dir / f"{prefix_dqn}_trajectories.json"
    traj_ppo_file = checkpoint_dir / f"{prefix_ppo}_trajectories.json"
    sum_dqn_file = checkpoint_dir / f"{prefix_dqn}_summary.json"
    sum_ppo_file = checkpoint_dir / f"{prefix_ppo}_summary.json"

    if not traj_dqn_file.exists() or not traj_ppo_file.exists():
        print(f"[WARN] Missing trajectory files for Gen {gen}. Cannot render swarm.")
        return None

    with open(traj_dqn_file, "r", encoding="utf-8") as f:
        dqn_trajs = json.load(f)
    with open(traj_ppo_file, "r", encoding="utf-8") as f:
        ppo_trajs = json.load(f)

    dqn_metrics = {"tiles": 0, "sps": 0.0}
    if sum_dqn_file.exists():
        with open(sum_dqn_file, "r", encoding="utf-8") as f:
            d = json.load(f)
            dqn_metrics["tiles"] = d.get("unique_tiles", 0)
            dqn_metrics["sps"] = d.get("sps", 0.0)

    ppo_metrics = {"tiles": 0, "sps": 0.0}
    if sum_ppo_file.exists():
        with open(sum_ppo_file, "r", encoding="utf-8") as f:
            d = json.load(f)
            ppo_metrics["tiles"] = d.get("unique_tiles", 0)
            ppo_metrics["sps"] = d.get("sps", 0.0)

    def subsample(trajs, max_len):
        sampled_list = []
        for t in trajs:
            if len(t) > max_len:
                stride = len(t) / max_len
                sampled_list.append([t[int(i * stride)] for i in range(max_len)])
            else:
                sampled_list.append(t)
        return sampled_list

    sampled_dqn = subsample(dqn_trajs, steps_render)
    sampled_ppo = subsample(ppo_trajs, steps_render)

    trajectories_by_condition = {
        "QRDQN_RND": sampled_dqn,
        "PPO_RND": sampled_ppo,
    }

    palette = {
        "QRDQN_RND": (50, 230, 80),   # Neon Lime Green
        "PPO_RND": (0, 210, 255),     # Electric Cyan
    }

    legend = [
        ("QRDQN_RND", f"QR-DQN RND ({dqn_metrics['tiles']} tiles)"),
        ("PPO_RND", f"PPO RND ({ppo_metrics['tiles']} tiles)"),
    ]

    group_tiles = {
        "QRDQN_RND": dqn_metrics["tiles"],
        "PPO_RND": ppo_metrics["tiles"],
    }

    renderer = SwarmRenderer(viewport_w=760, viewport_h=480)
    video_path = visual_dir / f"benchmark_rnd_curriculum_gen{gen:03d}.mp4"
    gif_path = visual_dir / f"benchmark_rnd_curriculum_gen{gen:03d}.gif"

    renderer.generate_timelapse(
        trajectories_by_gen=trajectories_by_condition,
        output_video_path=video_path,
        output_gif_path=gif_path,
        fps=15,
        trail_length=14,
        gif_duration_ms=125,
        gif_frame_skip=2,
        custom_palette=palette,
        custom_title=f"POKEMON FIRERED: GENERATION {gen} SWARM (QR-DQN vs PPO)",
        custom_legend=legend,
        group_tiles=group_tiles,
    )
    print(f"[SWARM] Generated Gen {gen} visual evidence: {video_path} and {gif_path}")
    return video_path


def stitch_generation_videos(video_paths: List[Path], output_path: Path):
    """Stitches multiple generation MP4 videos into a single chronological timeline."""
    valid_videos = [p for p in video_paths if p.exists() and p.stat().st_size > 0]
    if not valid_videos:
        return
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cap0 = cv2.VideoCapture(str(valid_videos[0]))
    fps = cap0.get(cv2.CAP_PROP_FPS) or 15.0
    w = int(cap0.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap0.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap0.release()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

    total_frames = 0
    for v_path in valid_videos:
        cap = cv2.VideoCapture(str(v_path))
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            out.write(frame)
            total_frames += 1
        cap.release()

    out.release()
    print(f"[STITCH] Stitched {len(valid_videos)} video segments into: {output_path} ({total_frames} frames)")


def generate_report(checkpoint_dir: Path, history: List[Dict], state: Dict):
    """Compiles and updates the comprehensive Markdown benchmark report."""
    report_file = checkpoint_dir / "BENCHMARK_RND_CURRICULUM_REPORT.md"

    header = [
        "# Continuous Reinforcement Learning Benchmark: QR-DQN vs PPO",
        "## RND Exploration & Dynamic Curriculum Progression",
        f"\n**Last Updated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Cumulative QR-DQN Lifetime:** {state.get('qrdqn_lifetime_steps', 0):,} environment steps",
        f"- **Cumulative PPO Lifetime:**    {state.get('ppo_lifetime_steps', 0):,} environment steps",
        f"- **Completed Generations:**      {state.get('last_completed_generation', 0)}",
        "\n### Generation Progression Matrix\n",
        "| Gen | Algorithm | Steps This Gen | Cumulative Lifetime | SPS | Elapsed (s) | Unique Tiles | Maps | Intrinsic R | Extrinsic R |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for item in history:
        line = (
            f"| **{item.get('generation', 1)}** | "
            f"**{item.get('algo', 'PPO')}** | "
            f"{item.get('timesteps', 0):,} | "
            f"{item.get('cumulative_timesteps', 0):,} | "
            f"{item.get('sps', 0):.1f} | "
            f"{item.get('elapsed_seconds', 0):.1f}s | "
            f"**{item.get('unique_tiles', 0)}** | "
            f"{item.get('unique_maps', 0)} | "
            f"{item.get('intrinsic_reward', 0):.2f} | "
            f"{item.get('extrinsic_reward', 0):.2f} |"
        )
        header.append(line)

    content = "\n".join(header) + "\n"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[REPORT] Benchmark report updated at: {report_file}")


def main():
    args = parse_args()
    checkpoint_dir = PROJECT_ROOT / args.checkpoint_dir
    log_dir = PROJECT_ROOT / args.log_dir
    visual_dir = PROJECT_ROOT / args.visual_dir

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    visual_dir.mkdir(parents=True, exist_ok=True)

    state_file = checkpoint_dir / "benchmark_state.json"
    if args.fresh and state_file.exists():
        print("[RESET] Fresh run requested: Archiving previous benchmark state.")
        state_file.unlink()

    state = load_state(state_file)

    python_exe = sys.executable

    print("\n" + "=" * 80)
    print(" [BENCHMARK] PPO vs QR-DQN (+ PER) CONTINUOUS RND & DYNAMIC CURRICULUM")
    print(f" Target Generations : {args.generations}")
    print(f" Parallel Envs      : {args.num_envs}")
    print(f" Base Minimum Steps : {args.min_timesteps:,} (Gen 1 starting budget)")
    print(f" Growth Rate        : {args.growth_rate * 100:.1f}% of model lifetime")
    print(f" Step Quantization  : {args.quantize:,}")
    print(f" Checkpoint Dir     : {checkpoint_dir}")
    print(f" Visual Evidence    : {visual_dir}")
    print(f" Current State      : Last completed Gen {state['last_completed_generation']}")
    print(f" QR-DQN Lifetime    : {state['qrdqn_lifetime_steps']:,} steps")
    print(f" PPO Lifetime       : {state['ppo_lifetime_steps']:,} steps")
    print("=" * 80 + "\n")

    rendered_videos = []

    for gen in range(1, args.generations + 1):
        print(f"\n==================== [GENERATION {gen} / {args.generations}] ====================")

        # -------------------------------------------------------------
        # Phase 1: QR-DQN Execution for Generation `gen`
        # -------------------------------------------------------------
        key_dqn = f"gen{gen}_QRDQN"
        dqn_steps_for_gen = compute_dynamic_timesteps(
            state["qrdqn_lifetime_steps"],
            min_steps=args.min_timesteps,
            growth_rate=args.growth_rate,
            quantize=args.quantize
        )

        if key_dqn in state["completed_runs"]:
            print(f"[RESUME] Skipping QR-DQN Generation {gen}: Already completed in state.")
        else:
            print(f"\n>>> [GEN {gen}] LAUNCHING QR-DQN (+ PER) | Target Steps: {dqn_steps_for_gen:,}")
            cmd_dqn = [
                python_exe,
                str(PROJECT_ROOT / "scripts" / "train.py"),
                "--algo", "QRDQN",
                "--exploration", "RND",
                "--num-envs", str(args.num_envs),
                "--timesteps", str(dqn_steps_for_gen),
                "--generation", str(gen),
                "--checkpoint-dir", str(args.checkpoint_dir),
                "--log-dir", str(args.log_dir),
                "--device", args.device,
                "--epsilon-start", str(args.epsilon_start),
                "--epsilon-end", str(args.epsilon_end),
                "--epsilon-decay-steps", str(args.epsilon_decay_steps),
            ]
            if gen == 1 and state["qrdqn_lifetime_steps"] == 0:
                cmd_dqn.append("--fresh")

            env_vars = os.environ.copy()
            env_vars["PYTHONPATH"] = str(PROJECT_ROOT / "src")

            t0 = time.time()
            proc = subprocess.run(cmd_dqn, cwd=str(PROJECT_ROOT), env=env_vars)
            if proc.returncode != 0:
                print(f"[ERROR] QR-DQN Generation {gen} failed with exit code {proc.returncode}!")
                sys.exit(proc.returncode)

            # Read summary output
            summary_dqn = checkpoint_dir / f"PokemonFireRed-GBA-QRDQN-RND-{args.num_envs}env_gen{gen:03d}_summary.json"
            if summary_dqn.exists():
                with open(summary_dqn, "r", encoding="utf-8") as f:
                    metrics_dqn = json.load(f)
                state["completed_runs"][key_dqn] = metrics_dqn
                state["qrdqn_lifetime_steps"] = metrics_dqn.get("cumulative_timesteps", state["qrdqn_lifetime_steps"] + dqn_steps_for_gen)
                state["history"].append(metrics_dqn)
                save_state(state_file, state)
                generate_report(checkpoint_dir, state["history"], state)
            else:
                print(f"[ERROR] Expected summary file {summary_dqn} not found!")
                sys.exit(1)

        # -------------------------------------------------------------
        # Phase 2: PPO Execution for Generation `gen`
        # -------------------------------------------------------------
        key_ppo = f"gen{gen}_PPO"
        ppo_steps_for_gen = compute_dynamic_timesteps(
            state["ppo_lifetime_steps"],
            min_steps=args.min_timesteps,
            growth_rate=args.growth_rate,
            quantize=args.quantize
        )

        if key_ppo in state["completed_runs"]:
            print(f"[RESUME] Skipping PPO Generation {gen}: Already completed in state.")
        else:
            print(f"\n>>> [GEN {gen}] LAUNCHING PPO | Target Steps: {ppo_steps_for_gen:,}")
            cmd_ppo = [
                python_exe,
                str(PROJECT_ROOT / "scripts" / "train.py"),
                "--algo", "PPO",
                "--exploration", "RND",
                "--num-envs", str(args.num_envs),
                "--timesteps", str(ppo_steps_for_gen),
                "--generation", str(gen),
                "--checkpoint-dir", str(args.checkpoint_dir),
                "--log-dir", str(args.log_dir),
                "--device", args.device,
                "--ent-coef", str(args.ent_coef),
            ]
            if gen == 1 and state["ppo_lifetime_steps"] == 0:
                cmd_ppo.append("--fresh")

            env_vars = os.environ.copy()
            env_vars["PYTHONPATH"] = str(PROJECT_ROOT / "src")

            t0 = time.time()
            proc = subprocess.run(cmd_ppo, cwd=str(PROJECT_ROOT), env=env_vars)
            if proc.returncode != 0:
                print(f"[ERROR] PPO Generation {gen} failed with exit code {proc.returncode}!")
                sys.exit(proc.returncode)

            summary_ppo = checkpoint_dir / f"PokemonFireRed-GBA-PPO-RND-{args.num_envs}env_gen{gen:03d}_summary.json"
            if summary_ppo.exists():
                with open(summary_ppo, "r", encoding="utf-8") as f:
                    metrics_ppo = json.load(f)
                state["completed_runs"][key_ppo] = metrics_ppo
                state["ppo_lifetime_steps"] = metrics_ppo.get("cumulative_timesteps", state["ppo_lifetime_steps"] + ppo_steps_for_gen)
                state["history"].append(metrics_ppo)
                state["last_completed_generation"] = gen
                save_state(state_file, state)
                generate_report(checkpoint_dir, state["history"], state)
            else:
                print(f"[ERROR] Expected summary file {summary_ppo} not found!")
                sys.exit(1)

        # -------------------------------------------------------------
        # Phase 3: Visual Swarm Rendering & Timeline Stitching
        # -------------------------------------------------------------
        if not args.no_render:
            gen_mp4 = visual_dir / f"benchmark_rnd_curriculum_gen{gen:03d}.mp4"
            gen_gif = visual_dir / f"benchmark_rnd_curriculum_gen{gen:03d}.gif"

            if gen_mp4.exists() and gen_gif.exists():
                print(f"[SWARM] Gen {gen} visual evidence already exists, skipping re-render.")
                gen_video = gen_mp4
            else:
                print(f"\n>>> [GEN {gen}] RENDERING SWARM VISUALIZATIONS (QR-DQN vs PPO)...")
                gen_video = render_generation_swarm(checkpoint_dir, visual_dir, gen, num_envs=args.num_envs)

            if gen_video and gen_video.exists():
                rendered_videos.append(gen_video)
                stitched_video = visual_dir / "stitched_chronological_benchmark.mp4"
                all_gen_videos = [visual_dir / f"benchmark_rnd_curriculum_gen{g:03d}.mp4" for g in range(1, gen + 1)]
                stitch_generation_videos(all_gen_videos, stitched_video)

    print("\n" + "=" * 80)
    print(" [BENCHMARK COMPLETE] ALL GENERATIONS SUCCESSFULLY EXECUTED!")
    print(f" Summary Report:    {checkpoint_dir / 'BENCHMARK_RND_CURRICULUM_REPORT.md'}")
    print(f" Research Chronicle: {PROJECT_ROOT / 'RESEARCH_CHRONICLE.md'}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

"""
Benchmark Orchestrator for Pokemon FireRed AI: PPO vs QR-DQN (with PER) Exploration Comparison.
Executes pure exploration conditions sequentially from fresh initializations across algorithms:
- Algorithms: PPO vs QR-DQN + PER
- Explorations: NONE, COORD, RND, SSIM, RND+COORD, SSIM+COORD, RND+SSIM, RND+SSIM+COORD
Collects empirical metrics (SPS, unique tiles, maps, rewards, elapsed time)
and compiles a unified Markdown comparison report for the research paper.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

# Force UTF-8 encoding on standard streams to avoid Windows cp1252 charmap errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrate PPO vs QR-DQN Exploration Benchmarks")
    parser.add_argument("--timesteps", type=int, default=102400, help="Timesteps per condition (default: 102,400)")
    parser.add_argument("--num-envs", type=int, default=8, help="Number of parallel environments (default: 8)")
    parser.add_argument(
        "--algos",
        type=str,
        default="PPO,QRDQN",
        help="Comma-separated algorithms to benchmark (e.g. PPO,QRDQN)",
    )
    parser.add_argument(
        "--modes",
        type=str,
        default="NONE,COORD,RND,SSIM,RND+COORD,SSIM+COORD,RND+SSIM,RND+SSIM+COORD",
        help="Comma-separated exploration modes to benchmark",
    )
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints/benchmark_pure", help="Checkpoints directory")
    parser.add_argument("--log-dir", type=str, default="logs/benchmark_pure", help="TensorBoard logs directory")
    parser.add_argument("--visual-eval", action="store_true", help="Enable periodic evaluation GIFs")
    parser.add_argument("--eval-freq", type=int, default=25600, help="Frequency of visual evaluation GIFs")
    return parser.parse_args()


def main():
    args = parse_args()
    algos = [a.strip().upper() for a in args.algos.split(",") if a.strip()]
    modes = [m.strip().upper() for m in args.modes.split(",") if m.strip()]
    checkpoint_dir = PROJECT_ROOT / args.checkpoint_dir
    log_dir = PROJECT_ROOT / args.log_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    total_runs = len(algos) * len(modes)
    print("\n" + "=" * 80)
    print(" [BENCHMARK] PPO vs QR-DQN + PER FACTORIAL EXPLORATION BENCHMARK SUITE")
    print(f" Algorithms to run:   {algos}")
    print(f" Exploration Modes:   {modes}")
    print(f" Total Conditions:    {total_runs} runs")
    print(f" Timesteps per run:   {args.timesteps:,}")
    print(f" Parallel envs:       {args.num_envs}")
    print(f" Checkpoint dir:      {checkpoint_dir}")
    print(f" TensorBoard dir:     {log_dir}")
    print("=" * 80 + "\n")

    run_idx = 1
    results = []

    for algo in algos:
        for mode in modes:
            print(f"\n>>> [{run_idx}/{total_runs}] LAUNCHING: Algorithm={algo} | Exploration={mode}")
            cmd = [
                python_exe,
                str(PROJECT_ROOT / "scripts" / "train.py"),
                "--algo", algo,
                "--exploration", mode,
                "--num-envs", str(args.num_envs),
                "--timesteps", str(args.timesteps),
                "--checkpoint-dir", str(args.checkpoint_dir),
                "--log-dir", str(args.log_dir),
                "--fresh",
            ]
            if args.visual_eval:
                cmd.extend(["--visual-eval", "--eval-freq", str(args.eval_freq)])

            start_time = time.time()
            process = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
            elapsed = time.time() - start_time
            run_idx += 1

            if process.returncode != 0:
                print(f"[ERROR] Condition {algo}-{mode} exited with code {process.returncode}")
                continue

            clean_mode = mode.replace("+", "_")
            summary_file = checkpoint_dir / f"PokemonFireRed-GBA-{algo}-{clean_mode}-{args.num_envs}env_summary.json"
            if summary_file.exists():
                with open(summary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(data)
                    print(f"[OK] Completed {algo}-{mode}: {data.get('unique_tiles', 0)} tiles | SPS: {data.get('sps', 0)} | Time: {elapsed:.1f}s")
            else:
                print(f"[WARN] Summary file {summary_file} not found for {algo}-{mode}.")

    # Compile Final Report
    report_file = checkpoint_dir / "benchmark_factorial_comparison_report.md"
    print("\n" + "=" * 80)
    print(" [SUMMARY] PPO vs QR-DQN FACTORIAL COMPARISON REPORT")
    print("=" * 80)

    all_summary_files = sorted(checkpoint_dir.glob("PokemonFireRed-GBA-*-*-*_summary.json"))
    final_results = []
    if all_summary_files:
        for s_file in all_summary_files:
            try:
                with open(s_file, "r", encoding="utf-8") as f:
                    final_results.append(json.load(f))
            except Exception:
                pass
    if not final_results:
        final_results = results

    header = "| Algorithm | Curiosity Mode | Timesteps | SPS | Elapsed (min) | Unique Tiles | Maps | Extrinsic R | Intrinsic R |"
    separator = "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    lines = [header, separator]

    for r in final_results:
        elapsed_min = r.get('elapsed_seconds', 0) / 60.0
        line = (
            f"| **{r.get('algo', 'PPO')}** | **{r.get('exploration')}** | {r.get('timesteps'):,} | {r.get('sps', 0):.1f} | "
            f"{elapsed_min:.2f} | **{r.get('unique_tiles', 0)}** | {r.get('unique_maps', 0)} | "
            f"{r.get('extrinsic_reward', 0):.2f} | {r.get('intrinsic_reward', 0):.2f} |"
        )
        lines.append(line)

    markdown_report = "\n".join(lines)
    print(markdown_report)
    print("=" * 80)

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# PPO vs QR-DQN (+ PER) Factorial Exploration Benchmark Report\n\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Factorial Evaluation Matrix (2 Algorithms x 8 Curiosity Configurations)\n\n")
        f.write(markdown_report + "\n")

    print(f"\nReport written to: {report_file}\n")


if __name__ == "__main__":
    main()

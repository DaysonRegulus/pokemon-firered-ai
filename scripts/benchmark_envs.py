"""
Hardware Scalability Benchmark for Pokemon FireRed AI.
Sweeps different numbers of parallel environments to determine the optimal throughput (SPS)
and resource utilization on Windows (CPU cores, RAM, and GPU VRAM).
"""
import argparse
import os
from pathlib import Path
import sys
import time
import psutil
import torch
import numpy as np

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import create_vectorized_env
from pokefirered.rnd import RNDModule


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark parallel environment scaling")
    parser.add_argument("--envs", type=int, nargs="+", default=[2, 4, 8, 12, 16], help="List of env counts to test")
    parser.add_argument("--steps", type=int, default=1024, help="Total environment steps per benchmark run")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Device to use")
    return parser.parse_args()


def benchmark_configuration(num_envs: int, total_steps: int, device: str):
    print(f"\n---> Benchmarking {num_envs} Parallel Environments (Target: {total_steps} total steps)...")

    rnd = RNDModule(device=device)

    start_ram = psutil.virtual_memory().used / (1024 ** 2)

    vec_env = create_vectorized_env(
        num_envs=num_envs,
        n_stack=2,
        render_mode=None,
        exploration_mode="RND",
    )

    obs = vec_env.reset()
    steps_per_env = total_steps // num_envs
    actual_total_steps = steps_per_env * num_envs

    actions = np.zeros((num_envs, 6), dtype=np.int8)

    # Warmup
    for _ in range(5):
        vec_env.step(actions)

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    start_time = time.time()

    for _ in range(steps_per_env):
        # 1. Step environments
        obs, rewards, dones, infos = vec_env.step(actions)

        # 2. Compute RND intrinsic reward
        obs_frame = obs[:, -1:, :, :].astype(np.float32) / 255.0
        norm_r, raw_e = rnd.compute_intrinsic_reward(obs_frame)

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    elapsed = time.time() - start_time
    sps = actual_total_steps / elapsed

    peak_ram = psutil.virtual_memory().used / (1024 ** 2)
    ram_delta = max(0.0, peak_ram - start_ram)

    gpu_vram = 0.0
    if torch.cuda.is_available():
        gpu_vram = torch.cuda.max_memory_allocated() / (1024 ** 2)

    vec_env.close()
    time.sleep(1.0)  # Allow worker processes to terminate cleanly

    return {
        "num_envs": num_envs,
        "total_steps": actual_total_steps,
        "elapsed_sec": elapsed,
        "sps": sps,
        "ram_delta_mb": ram_delta,
        "gpu_vram_mb": gpu_vram,
    }


def main():
    args = parse_args()

    print("=" * 65)
    print(" POKEMON FIRERED AI - HARDWARE SCALABILITY BENCHMARK")
    print("=" * 65)
    print(f" CPU Physical Cores: {psutil.cpu_count(logical=False)}")
    print(f" CPU Logical Cores:  {psutil.cpu_count(logical=True)}")
    print(f" Total System RAM:   {psutil.virtual_memory().total / (1024**3):.2f} GB")
    if torch.cuda.is_available():
        print(f" GPU Device:         {torch.cuda.get_device_name(0)}")
        print(f" GPU Total VRAM:     {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    print(f" Test Envs:          {args.envs}")
    print(f" Steps Per Config:   {args.steps}")
    print("=" * 65)

    results = []
    for n in args.envs:
        try:
            res = benchmark_configuration(n, args.steps, args.device)
            results.append(res)
            print(f"  [RESULT] Envs: {n:2d} | SPS: {res['sps']:6.1f} steps/s | Time: {res['elapsed_sec']:5.2f}s | RAM Delta: {res['ram_delta_mb']:6.1f} MB | VRAM: {res['gpu_vram_mb']:5.1f} MB")
        except Exception as e:
            print(f"  [ERROR] Failed to run with {n} envs: {e}")

    if not results:
        print("\nNo successful benchmark results.")
        return

    # Sort by SPS
    best = max(results, key=lambda x: x["sps"])

    print("\n" + "=" * 70)
    print(" BENCHMARK SUMMARY & COMPARISON TABLE")
    print("=" * 70)
    print(f"| {'Envs':<6} | {'SPS (Steps/sec)':<16} | {'Time (s)':<10} | {'RAM Delta':<12} | {'GPU VRAM':<10} |")
    print(f"|{'-'*8}|{'-'*18}|{'-'*12}|{'-'*14}|{'-'*12}|")
    for r in results:
        marker = " (OPTIMAL)" if r["num_envs"] == best["num_envs"] else ""
        print(f"| {r['num_envs']:<6} | {r['sps']:<16.1f} | {r['elapsed_sec']:<10.2f} | {r['ram_delta_mb']:<9.1f} MB | {r['gpu_vram_mb']:<7.1f} MB |{marker}")
    print("=" * 70)
    print(f"\n>>> Recommended Environment Count: {best['num_envs']} envs ({best['sps']:.1f} steps/second) <<<\n")


if __name__ == "__main__":
    main()

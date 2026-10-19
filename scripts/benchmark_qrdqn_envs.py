"""
Hardware Scalability Benchmark for QR-DQN + PER + RND in Pokemon FireRed AI.
Sweeps different numbers of parallel environments to determine the optimal throughput (SPS)
and resource utilization on Windows (CPU cores, RAM, and GPU VRAM).
"""
import argparse
import gc
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
from pokefirered.models import QRDQNAgent


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark QR-DQN parallel environment scaling")
    parser.add_argument(
        "--envs",
        type=int,
        nargs="+",
        default=[2, 4, 6, 8, 10, 12, 14, 16],
        help="List of env counts to test (default: 2 4 6 8 10 12 14 16)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1024,
        help="Total environment steps per benchmark run (default: 1024)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Inference & training device",
    )
    return parser.parse_args()


def benchmark_configuration(num_envs: int, total_steps: int, device: str):
    print(f"\n---> Benchmarking {num_envs} Parallel Environments (Target: ~{total_steps} steps)...")

    # Baseline system memory before allocating this configuration
    start_ram = psutil.virtual_memory().used / (1024 ** 2)

    vec_env = create_vectorized_env(
        num_envs=num_envs,
        n_stack=2,
        render_mode=None,
        exploration_mode="RND",
    )

    in_channels = vec_env.observation_space.shape[0]
    num_actions = vec_env.action_space.n

    agent = QRDQNAgent(
        in_channels=in_channels,
        num_actions=num_actions,
        num_quantiles=32,
        learning_rate=1e-4,
        gamma=0.99,
        tau=0.005,
        kappa=1.0,
        buffer_size=20_000,
        batch_size=64,
        device=device,
    )
    rnd_module = RNDModule(device=device)

    obs = vec_env.reset()
    steps_per_env = max(1, total_steps // num_envs)
    actual_total_steps = steps_per_env * num_envs

    # 1. Warmup: Collect enough transitions to exceed batch_size (64) and compile CUDA kernels
    warmup_steps = max(10, 80 // num_envs)
    for _ in range(warmup_steps):
        actions = agent.select_actions(obs, epsilon=1.0)
        next_obs, rewards, dones, infos = vec_env.step(actions)
        obs_latest = next_obs[:, -1:, :, :].astype(np.float32) / 255.0
        r_rnd_vec, _ = rnd_module.compute_intrinsic_reward(obs_latest)
        for i in range(num_envs):
            agent.buffer.add(obs[i], actions[i], float(rewards[i]) + 0.05 * float(r_rnd_vec[i]), next_obs[i], dones[i])
        agent.update()
        obs = next_obs

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    # Reset CPU monitoring counter
    psutil.cpu_percent(interval=None)

    start_time = time.time()

    # 2. Timed Full QR-DQN + PER + RND Training Loop
    rnd_rollout_buffer = []
    for step in range(steps_per_env):
        # Action selection (GPU forward pass)
        actions = agent.select_actions(obs, epsilon=0.5)

        # Parallel emulator stepping (CPU multiprocessing)
        next_obs, rewards, dones, infos = vec_env.step(actions)

        # Vectorized RND curiosity bonus (GPU)
        obs_latest = next_obs[:, -1:, :, :].astype(np.float32) / 255.0
        r_rnd_vec, _ = rnd_module.compute_intrinsic_reward(obs_latest)

        rnd_rollout_buffer.append(obs_latest)
        if len(rnd_rollout_buffer) >= 32:
            batch_rnd = np.concatenate(rnd_rollout_buffer, axis=0)
            rnd_module.train_batch(batch_rnd, epochs=1, batch_size=64)
            rnd_rollout_buffer.clear()

        # Buffer ingestion
        for i in range(num_envs):
            r_total = float(rewards[i]) + 0.05 * float(r_rnd_vec[i])
            agent.buffer.add(obs[i], actions[i], r_total, next_obs[i], dones[i])

        # Prioritized quantile regression gradient update (GPU)
        agent.update()

        obs = next_obs

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    elapsed = time.time() - start_time
    sps = actual_total_steps / max(0.001, elapsed)
    iter_latency_ms = (elapsed / steps_per_env) * 1000.0

    cpu_pct = psutil.cpu_percent(interval=None)
    peak_ram_used = psutil.virtual_memory().used / (1024 ** 2)
    sys_ram_pct = psutil.virtual_memory().percent
    ram_delta = max(0.0, peak_ram_used - start_ram)

    gpu_vram = 0.0
    if torch.cuda.is_available():
        gpu_vram = torch.cuda.max_memory_allocated() / (1024 ** 2)

    # Clean shutdown and resource release
    vec_env.close()
    del vec_env
    del agent
    del rnd_module
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    time.sleep(1.0)  # Grace period for Windows process cleanup

    return {
        "num_envs": num_envs,
        "total_steps": actual_total_steps,
        "elapsed_sec": elapsed,
        "sps": sps,
        "iter_latency_ms": iter_latency_ms,
        "ram_delta_mb": ram_delta,
        "sys_ram_pct": sys_ram_pct,
        "gpu_vram_mb": gpu_vram,
        "cpu_pct": cpu_pct,
    }


def main():
    args = parse_args()

    print("=" * 75)
    print(" POKEMON FIRERED AI - QR-DQN HARDWARE SCALABILITY BENCHMARK")
    print("=" * 75)
    print(f" CPU Physical Cores: {psutil.cpu_count(logical=False)}")
    print(f" CPU Logical Cores:  {psutil.cpu_count(logical=True)}")
    print(f" Total System RAM:   {psutil.virtual_memory().total / (1024**3):.2f} GB")
    print(f" Current RAM Used:   {psutil.virtual_memory().used / (1024**3):.2f} GB ({psutil.virtual_memory().percent}%)")
    if torch.cuda.is_available():
        print(f" GPU Device:         {torch.cuda.get_device_name(0)}")
        print(f" GPU Total VRAM:     {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    print(f" Tested Envs:        {args.envs}")
    print(f" Steps Per Config:   {args.steps}")
    print("=" * 75)

    results = []
    for n in args.envs:
        try:
            res = benchmark_configuration(n, args.steps, args.device)
            results.append(res)
            print(
                f"  [RESULT] Envs: {n:2d} | SPS: {res['sps']:6.1f} steps/s | "
                f"Latency: {res['iter_latency_ms']:5.1f} ms/iter | Time: {res['elapsed_sec']:5.2f}s | "
                f"RAM Delta: {res['ram_delta_mb']:6.1f} MB | Sys RAM: {res['sys_ram_pct']:4.1f}% | "
                f"VRAM: {res['gpu_vram_mb']:5.1f} MB | CPU: {res['cpu_pct']:4.1f}%"
            )
        except Exception as e:
            print(f"  [ERROR] Failed to run with {n} envs: {e}")
            import traceback
            traceback.print_exc()

    if not results:
        print("\nNo successful benchmark results.")
        return

    # Find highest throughput
    best_sps = max(results, key=lambda x: x["sps"])

    # Multi-tasking candidate: <= 8 envs (matching 8 physical CPU cores)
    multitask_results = [r for r in results if r["num_envs"] <= 8]
    best_multitask = max(multitask_results, key=lambda x: x["sps"]) if multitask_results else results[0]

    print("\n" + "=" * 90)
    print(" QR-DQN BENCHMARK SUMMARY & HARDWARE SCALING ANALYSIS")
    print("=" * 90)
    print(f"| {'Envs':<5} | {'SPS':<8} | {'Iter Latency':<13} | {'Time (s)':<9} | {'RAM Delta':<11} | {'Sys RAM %':<10} | {'GPU VRAM':<9} | {'CPU %':<7} |")
    print(f"|{'-'*7}|{'-'*10}|{'-'*15}|{'-'*11}|{'-'*13}|{'-'*12}|{'-'*11}|{'-'*9}|")
    for r in results:
        marker = ""
        if r["num_envs"] == best_sps["num_envs"]:
            marker += " [MAX SPS]"
        if r["num_envs"] == best_multitask["num_envs"]:
            marker += " [BEST MULTITASK]"
        print(
            f"| {r['num_envs']:<5} | {r['sps']:<8.1f} | {r['iter_latency_ms']:<10.1f} ms | "
            f"{r['elapsed_sec']:<9.2f} | {r['ram_delta_mb']:<8.1f} MB | {r['sys_ram_pct']:<10.1f} | "
            f"{r['gpu_vram_mb']:<6.1f} MB | {r['cpu_pct']:<5.1f}% |{marker}"
        )
    print("=" * 90)

    print("\n>>> OPERATIONAL TAKEAWAYS & RECOMMENDATIONS <<<")
    print(f"1. Maximum Throughput (Dedicated Training): {best_sps['num_envs']} envs -> {best_sps['sps']:.1f} SPS")
    print(f"2. Multitasking Headroom (Background Work):   {best_multitask['num_envs']} envs -> {best_multitask['sps']:.1f} SPS (Leaves {16 - best_multitask['num_envs']} CPU threads free)")
    print(f"3. Scaling Efficiency: 2 envs ({results[0]['sps']:.1f} SPS) -> {best_sps['num_envs']} envs ({best_sps['sps']:.1f} SPS) = {best_sps['sps']/results[0]['sps']:.2f}x speedup\n")


if __name__ == "__main__":
    main()

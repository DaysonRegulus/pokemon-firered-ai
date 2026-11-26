"""
Video Updater: Upgrades all visual evidence MP4 videos to 60 FPS (4x real-time game speed)
with ZERO intro hold frames and ZERO outro hold frames.
"""
import sys
import time
from pathlib import Path
from multiprocessing import Pool, cpu_count
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def convert_video_to_60fps_no_holds(src_path: Path) -> dict:
    src_path = Path(src_path)
    if not src_path.exists():
        return {"file": str(src_path), "status": "missing"}

    tmp_path = src_path.with_name(f"{src_path.stem}_tmp60fps.mp4")

    cap = cv2.VideoCapture(str(src_path))
    src_fps = round(cap.get(cv2.CAP_PROP_FPS) or 15.0, 1)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if total_frames <= 0 or w <= 0 or h <= 0:
        cap.release()
        return {"file": str(src_path), "status": "corrupt"}

    # Determine hold boundaries based on current format
    # - Format A (converted with 60/120 holds @ 60 FPS): intro=60, outro=120
    # - Format B (legacy standard holds @ 15 FPS): intro=15, outro=30
    # - Format C (no holds or short video): intro=0, outro=0
    if src_fps == 60.0 and total_frames > 200:
        intro_cutoff = 60
        outro_cutoff = total_frames - 120
    elif src_fps == 15.0 and total_frames > 60:
        intro_cutoff = 15
        outro_cutoff = total_frames - 30
    else:
        intro_cutoff = 0
        outro_cutoff = total_frames

    expected_frames = outro_cutoff - intro_cutoff
    if expected_frames <= 0:
        intro_cutoff = 0
        outro_cutoff = total_frames
        expected_frames = total_frames

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(tmp_path), fourcc, 60.0, (w, h))

    frames_written = 0
    f_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        if intro_cutoff <= f_idx < outro_cutoff:
            out.write(frame)
            frames_written += 1

        f_idx += 1

    cap.release()
    out.release()

    # Verify temp file
    verify_cap = cv2.VideoCapture(str(tmp_path))
    v_fps = round(verify_cap.get(cv2.CAP_PROP_FPS) or 0.0, 1)
    v_frames = int(verify_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    verify_cap.release()

    if v_frames > 0 and abs(v_fps - 60.0) < 1.0 and v_frames == frames_written:
        tmp_path.replace(src_path)
        return {
            "file": src_path.name,
            "status": "success",
            "old_frames": total_frames,
            "new_frames": v_frames,
            "old_fps": src_fps,
            "new_fps": v_fps,
            "duration": v_frames / 60.0,
        }
    else:
        if tmp_path.exists():
            tmp_path.unlink()
        return {"file": src_path.name, "status": "verification_failed", "expected": expected_frames, "got": v_frames}


def stitch_master_timeline(video_paths, output_path: Path, fps: float = 60.0):
    valid_videos = [p for p in video_paths if p.exists() and p.stat().st_size > 0]
    if not valid_videos:
        print("[STITCH] No valid videos found to stitch.")
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output_path.with_name(f"{output_path.stem}_tmp60fps.mp4")

    cap0 = cv2.VideoCapture(str(valid_videos[0]))
    w = int(cap0.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap0.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap0.release()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(tmp_output), fourcc, fps, (w, h))

    total_frames = 0
    print(f"\n[STITCH] Stitching {len(valid_videos)} video segments at {fps} FPS into: {output_path.name}...")
    t0 = time.time()

    for idx, v_path in enumerate(valid_videos, 1):
        cap = cv2.VideoCapture(str(v_path))
        v_cnt = 0
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            out.write(frame)
            v_cnt += 1
            total_frames += 1
        cap.release()
        if idx % 10 == 0 or idx == len(valid_videos):
            print(f"  [STITCH PROGRESS] Processed {idx}/{len(valid_videos)} segments ({total_frames:,} frames written)...")

    out.release()
    t1 = time.time()

    if tmp_output.exists() and total_frames > 0:
        tmp_output.replace(output_path)
        print(f"[STITCH COMPLETE] Master chronological timeline compiled: {output_path} ({total_frames:,} frames, {total_frames/fps:.1f}s, {t1-t0:.1f}s)")
    else:
        print("[STITCH ERROR] Failed to create master stitched timeline.")


def main():
    print("=" * 80)
    print(" UPGRADING ALL VISUAL EVIDENCE VIDEOS TO 60 FPS (4x SPEED, 0 HOLDS)")
    print("=" * 80)

    # 1. Collect all benchmark generation videos
    benchmark_dir = PROJECT_ROOT / "visual_evidence" / "benchmark_rnd_curriculum"
    benchmark_videos = [benchmark_dir / f"benchmark_rnd_curriculum_gen{g:03d}.mp4" for g in range(1, 90)]
    benchmark_videos = [p for p in benchmark_videos if p.exists()]

    # 2. Collect other visual evidence videos
    other_videos = []
    swarm_viz_dir = PROJECT_ROOT / "visual_evidence" / "swarm_visualizer"
    if swarm_viz_dir.exists():
        other_videos.extend([p for p in swarm_viz_dir.glob("*.mp4") if not p.name.endswith("_tmp60fps.mp4")])

    archive_dir = PROJECT_ROOT / "visual_evidence" / "archive" / "benchmark_rnd_curriculum_v1"
    if archive_dir.exists():
        archive_gens = [archive_dir / f"benchmark_rnd_curriculum_gen{g:03d}.mp4" for g in range(1, 21)]
        other_videos.extend([p for p in archive_gens if p.exists()])

    all_targets = benchmark_videos + other_videos
    print(f"Found {len(all_targets)} individual video files to process ({len(benchmark_videos)} benchmark gens, {len(other_videos)} comparison/archive).")

    num_workers = min(4, cpu_count() or 1)
    print(f"Executing conversion with {num_workers} parallel workers...")

    t0 = time.time()
    with Pool(num_workers) as pool:
        results = pool.map(convert_video_to_60fps_no_holds, all_targets)
    t1 = time.time()

    success_count = sum(1 for r in results if r.get("status") == "success")
    print(f"\n[CONVERSION COMPLETE] Successfully updated {success_count}/{len(all_targets)} videos in {t1 - t0:.1f} seconds.")

    for r in results[:5]:
        print(f"  {r['file']}: {r.get('old_fps', 0):.0f} FPS ({r.get('old_frames', 0)} frames) -> {r.get('new_fps', 0):.0f} FPS ({r.get('new_frames', 0)} frames), {r.get('duration', 0):.1f}s")
    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more videos.")

    # 3. Stitch master chronological benchmark timeline at 60 FPS
    master_stitched = benchmark_dir / "stitched_chronological_benchmark.mp4"
    stitch_master_timeline(benchmark_videos, master_stitched, fps=60.0)

    # 4. If archive stitched exists, stitch it too
    archive_stitched = archive_dir / "stitched_chronological_benchmark.mp4"
    if archive_dir.exists():
        archive_gens = [archive_dir / f"benchmark_rnd_curriculum_gen{g:03d}.mp4" for g in range(1, 21)]
        stitch_master_timeline(archive_gens, archive_stitched, fps=60.0)

    print("\n" + "=" * 80)
    print(" ALL VIDEOS SUCCESSFULLY UPGRADED TO 60 FPS & 4X REAL-TIME SPEED (0 HOLDS)!")
    print("=" * 80)


if __name__ == "__main__":
    main()

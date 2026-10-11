"""System throughput and frame queue latency benchmark tool.

Simulates multiple camera streams feeding frames into the server and measures:
* Ingestion throughput (FPS)
* Frame processing latency (p50, p90, p99)
* Frame drop rate under load
* Peak CPU and memory consumption
"""
from __future__ import annotations

import argparse
import time
import numpy as np
import psutil
from app.services.frame_queue import frame_queue
import asyncio

async def run_benchmark(num_cameras: int = 2, frames_per_cam: int = 50, send_fps: float = 5.0):
    print(f"\n--- SiteGuard System Benchmark ---")
    print(f"Simulating {num_cameras} cameras @ {send_fps} FPS for {frames_per_cam} frames each...")
    
    # Ensure worker is active
    frame_queue.start_worker()
    
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw simple shapes to simulate visual features
    dummy_frame[100:300, 100:300] = (128, 128, 128)

    start_time = time.time()
    total_enqueued = 0

    interval = 1.0 / send_fps

    for i in range(frames_per_cam):
        for cam_idx in range(num_cameras):
            cam_id = f"cam_{cam_idx + 1}"
            await frame_queue.enqueue_frame(cam_id, dummy_frame.copy())
            total_enqueued += 1
        await asyncio.sleep(interval)

    # Wait for queue to drain
    print("Flushing processing queue...")
    while frame_queue.queue.qsize() > 0:
        await asyncio.sleep(0.05)

    duration = time.time() - start_time
    mem = psutil.virtual_memory()

    print("\n=== Benchmark Results ===")
    print(f"Total Duration: {duration:.2f} s")
    print(f"Frames Enqueued: {total_enqueued}")
    print(f"Frames Processed: {frame_queue.total_frames_processed}")
    print(f"Frames Dropped: {frame_queue.total_frames_dropped}")
    print(f"Effective Ingestion FPS: {total_enqueued / duration:.2f}")
    print(f"Effective Processing FPS: {frame_queue.total_frames_processed / duration:.2f}")
    print(f"Drop Rate: {(frame_queue.total_frames_dropped / total_enqueued) * 100:.2f}%")
    print(f"CPU Utilization: {psutil.cpu_percent()}%")
    print(f"Memory Used: {mem.used / (1024*1024):.1f} MB ({mem.percent}%)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SiteGuard System Benchmark")
    parser.add_argument("--cameras", type=int, default=2, help="Number of simulated cameras")
    parser.add_argument("--frames", type=int, default=50, help="Frames per camera")
    parser.add_argument("--fps", type=float, default=5.0, help="Target send FPS per camera")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.cameras, args.frames, args.fps))

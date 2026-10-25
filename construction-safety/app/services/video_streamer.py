"""Background video streamer simulation for SiteGuard.

Allows uploading construction site video files (.mp4, .avi, etc.) and
streaming them in a continuous loop through the real-time AI pipeline
as a virtual camera node.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import time
from typing import Any

import cv2
import numpy as np

from app.config import LATEST_DIR, VIDEOS_DIR
from app.database import record_camera_frame
from app.detection.tracker import reset_camera_tracker
from app.services.frame_queue import frame_queue

logger = logging.getLogger("siteguard.video_streamer")

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


class ActiveVideoStream:
    def __init__(
        self,
        camera_id: str,
        camera_name: str,
        location: str,
        video_path: Path,
        target_fps: float,
        loop: bool,
    ):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.location = location
        self.video_path = video_path
        self.target_fps = max(0.5, min(target_fps, 30.0))
        self.loop = loop
        self.task: asyncio.Task | None = None
        self.is_running = False
        self.current_frame = 0
        self.total_frames = 0
        self.loops_completed = 0
        self.started_at: float = 0.0


class VideoStreamerManager:
    """Manages virtual video camera streams running in background loops."""

    def __init__(self):
        self.active_streams: dict[str, ActiveVideoStream] = {}

    def list_available_videos(self) -> list[dict[str, Any]]:
        """Return list of video files in the videos directory."""
        results = []
        if not VIDEOS_DIR.exists():
            return results

        for p in sorted(VIDEOS_DIR.iterdir()):
            if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS:
                size_mb = round(p.stat().st_size / (1024 * 1024), 2)
                meta: dict[str, Any] = {
                    "filename": p.name,
                    "size_mb": size_mb,
                    "path": str(p),
                }
                # Probe video details with OpenCV
                cap = cv2.VideoCapture(str(p))
                if cap.isOpened():
                    meta["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    meta["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    meta["fps"] = round(cap.get(cv2.CAP_PROP_FPS), 1)
                    meta["total_frames"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration_sec = meta["total_frames"] / max(meta["fps"], 1.0)
                    meta["duration_sec"] = round(duration_sec, 1)
                    cap.release()
                results.append(meta)
        return results

    def save_video(self, filename: str, content: bytes) -> Path:
        """Save uploaded video bytes to videos directory."""
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
        if not any(safe_name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            safe_name += ".mp4"

        target_path = VIDEOS_DIR / safe_name
        target_path.write_bytes(content)
        logger.info("Saved uploaded video to %s (%d bytes)", target_path, len(content))
        return target_path

    async def start_stream(
        self,
        video_filename: str,
        camera_id: str = "CAM-VIDEO",
        camera_name: str = "Simulated Video Stream",
        location: str = "Test Video Zone",
        target_fps: float = 5.0,
        loop: bool = True,
    ) -> dict[str, Any]:
        """Start streaming a video file as a virtual camera node."""
        video_path = VIDEOS_DIR / video_filename
        if not video_path.is_file():
            raise FileNotFoundError(f"Video file '{video_filename}' not found.")

        # Stop existing stream on same camera_id if already running
        await self.stop_stream(camera_id)
        reset_camera_tracker(camera_id)
        frame_queue.safety_engine.reset_camera(camera_id)

        stream = ActiveVideoStream(
            camera_id=camera_id,
            camera_name=camera_name,
            location=location,
            video_path=video_path,
            target_fps=target_fps,
            loop=loop,
        )

        stream.task = asyncio.create_task(self._run_stream_loop(stream))
        self.active_streams[camera_id] = stream

        return {
            "status": "started",
            "camera_id": camera_id,
            "video": video_filename,
            "target_fps": stream.target_fps,
            "loop": stream.loop,
        }

    async def stop_stream(self, camera_id: str = "CAM-VIDEO") -> bool:
        """Stop an active video stream."""
        stream = self.active_streams.get(camera_id)
        if not stream:
            return False

        stream.is_running = False
        if stream.task and not stream.task.done():
            stream.task.cancel()
            try:
                await stream.task
            except asyncio.CancelledError:
                pass

        del self.active_streams[camera_id]
        reset_camera_tracker(camera_id)
        frame_queue.safety_engine.reset_camera(camera_id)
        logger.info("Stopped video stream for camera %s", camera_id)
        return True

    async def stop_all(self) -> None:
        """Stop all active video streams."""
        for cam_id in list(self.active_streams.keys()):
            await self.stop_stream(cam_id)

    def get_status(self) -> list[dict[str, Any]]:
        """Return status of all active video streams."""
        statuses = []
        for cam_id, stream in self.active_streams.items():
            statuses.append({
                "camera_id": cam_id,
                "camera_name": stream.camera_name,
                "video": stream.video_path.name,
                "is_running": stream.is_running,
                "target_fps": stream.target_fps,
                "current_frame": stream.current_frame,
                "total_frames": stream.total_frames,
                "loops_completed": stream.loops_completed,
                "uptime_sec": round(time.time() - stream.started_at, 1) if stream.started_at else 0,
            })
        return statuses

    async def _run_stream_loop(self, stream: ActiveVideoStream) -> None:
        """Continuous frame extraction and queue dispatch loop."""
        cap = cv2.VideoCapture(str(stream.video_path))
        if not cap.isOpened():
            logger.error("Failed to open video file %s", stream.video_path)
            return

        stream.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        stream.is_running = True
        stream.started_at = time.time()
        frame_interval = 1.0 / stream.target_fps

        logger.info(
            "Starting video stream '%s' for %s at %.1f FPS (total frames: %d, loop=%s)",
            stream.video_path.name,
            stream.camera_id,
            stream.target_fps,
            stream.total_frames,
            stream.loop,
        )

        try:
            while stream.is_running:
                t0 = time.time()
                ret, frame = cap.read()

                if not ret:
                    if stream.loop:
                        stream.loops_completed += 1
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        stream.current_frame = 0
                        reset_camera_tracker(stream.camera_id)
                        frame_queue.safety_engine.reset_camera(stream.camera_id)
                        ret, frame = cap.read()
                        if not ret:
                            logger.warning("Failed to rewind video %s", stream.video_path)
                            break
                    else:
                        logger.info("Video stream %s finished (loop=False)", stream.camera_id)
                        break

                stream.current_frame += 1

                # Save raw JPEG snapshot in latest directory
                ok, jpeg_bytes = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ok:
                    (LATEST_DIR / f"{stream.camera_id}.jpg").write_bytes(jpeg_bytes.tobytes())

                # Upsert camera row in SQLite DB
                record_camera_frame(stream.camera_id, stream.camera_name, stream.location)

                # Feed frame into asynchronous AI inference queue
                await frame_queue.enqueue_frame(stream.camera_id, frame)

                # Maintain target FPS timing
                elapsed = time.time() - t0
                sleep_sec = max(0.005, frame_interval - elapsed)
                await asyncio.sleep(sleep_sec)

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("Error in video stream loop %s: %s", stream.camera_id, exc, exc_info=True)
        finally:
            cap.release()
            stream.is_running = False
            logger.info("Video capture released for %s", stream.camera_id)


# Module singleton
video_streamer = VideoStreamerManager()

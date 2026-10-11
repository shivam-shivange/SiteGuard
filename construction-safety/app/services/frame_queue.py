"""Async frame queue and background inference worker.

Decouples camera HTTP frame ingestion from heavy CPU/GPU model inference.
If the inference worker falls behind incoming HTTP frames, older frames
are dropped from the queue to preserve real-time low-latency performance.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import cv2
import numpy as np

from app.config import LATEST_DIR, MAX_QUEUE_SIZE
from app.database import record_camera_processing
from app.detection.inference import camera_inference_engines
from app.detection.model_manager import model_manager
from app.services.event_manager import handle_incident_event, handle_incident_update
from app.services.safety_engine import SafetyEngine
from app.websocket_hub import ws_hub

logger = logging.getLogger("siteguard.frame_queue")


class FrameProcessingQueue:
    """Async queue for buffering incoming frames from cameras."""

    def __init__(self, maxsize: int = MAX_QUEUE_SIZE):
        self.queue: asyncio.Queue[tuple[str, float, np.ndarray]] = asyncio.Queue(maxsize=maxsize)
        self.safety_engine = SafetyEngine()
        self.worker_task: asyncio.Task | None = None
        self.total_frames_received = 0
        self.total_frames_processed = 0
        self.total_frames_dropped = 0

    async def enqueue_frame(self, camera_id: str, frame: np.ndarray) -> bool:
        """Enqueue frame for processing. Returns True if queued, False if dropped due to overflow."""
        self.total_frames_received += 1
        timestamp = time.time()

        if self.queue.full():
            try:
                # Drop oldest frame to maintain low latency
                _ = self.queue.get_nowait()
                self.total_frames_dropped += 1
                logger.warning("Frame queue full for camera %s; dropped oldest frame.", camera_id)
            except asyncio.QueueEmpty:
                pass

        try:
            self.queue.put_nowait((camera_id, timestamp, frame))
            return True
        except asyncio.QueueFull:
            self.total_frames_dropped += 1
            return False

    def start_worker(self) -> None:
        """Start the background inference processing loop."""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._processing_loop())
            logger.info("Frame processing queue worker started.")

    async def stop_worker(self) -> None:
        """Cancel and stop background worker task."""
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Frame processing queue worker stopped.")

    async def _processing_loop(self) -> None:
        """Main worker loop popping frames and executing inference."""
        while True:
            try:
                camera_id, timestamp, frame = await self.queue.get()
                self.total_frames_processed += 1

                # Execute sync inference in thread pool to avoid blocking asyncio event loop
                engine = camera_inference_engines.get_engine(camera_id)
                inference_result = await asyncio.to_thread(engine.process_frame, frame)

                annotated_frame = inference_result.get("annotated_frame")
                persons = inference_result.get("persons", [])
                stats = inference_result.get("stats", {})

                # Persist latest annotated frame and per-camera stats for the dashboard
                if annotated_frame is not None:
                    ok, encoded = cv2.imencode(".jpg", annotated_frame)
                    if ok:
                        (LATEST_DIR / f"{camera_id}.jpg").write_bytes(encoded.tobytes())
                record_camera_processing(
                    camera_id,
                    workers=stats.get("person_count", 0),
                    latency_ms=stats.get("inference_ms", 0.0),
                    processing_status="running" if model_manager.is_ready else model_manager.status,
                )

                # Update per-worker PPE monitoring; only confirmed episodes yield events
                events = self.safety_engine.update(camera_id, timestamp, persons)

                for ev in events:
                    violation_type = ",".join(ev["violations"])
                    if ev["action"] == "create":
                        incident = await handle_incident_event(
                            camera_id=ev["camera_id"],
                            violation_type=violation_type,
                            severity=ev["severity"],
                            track_id=ev["track_id"],
                            confidence=ev["confidence"],
                            annotated_frame=annotated_frame,
                        )
                        self.safety_engine.attach_incident(ev["camera_id"], ev["track_id"], incident["id"])
                    else:
                        await handle_incident_update(
                            incident_id=ev["incident_id"],
                            violation_type=violation_type,
                            severity=ev["severity"],
                            confidence=ev["confidence"],
                        )

                # Broadcast live status update over WebSocket
                ws_payload = {
                    "event_type": "FRAME_PROCESSED",
                    "camera_id": camera_id,
                    "timestamp": timestamp,
                    "person_count": stats.get("person_count", 0),
                    "violation_count": stats.get("violation_count", 0),
                    "inference_ms": stats.get("inference_ms", 0.0),
                    "fps": stats.get("fps", 0.0),
                }
                await ws_hub.broadcast(ws_payload)

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing frame in queue worker: %s", e, exc_info=True)


frame_queue = FrameProcessingQueue()

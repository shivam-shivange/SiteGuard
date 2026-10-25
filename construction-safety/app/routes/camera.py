"""Camera ingest and telemetry endpoints."""
from __future__ import annotations

import logging
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import LATEST_DIR, MAX_FRAME_BYTES
from app.database import record_camera_frame, record_heartbeat
from app.services.frame_cache import set_frame
from app.services.frame_queue import frame_queue

logger = logging.getLogger("siteguard.routes.camera")

router = APIRouter(prefix="/api/camera", tags=["Camera"])


class HeartbeatPayload(BaseModel):
    device_id: str
    rssi: int | None = None
    free_heap: int | None = None
    uptime: int | None = None
    fps: float | None = None
    firmware_version: str | None = "1.0.0"


def sanitize_camera_id(raw: str, default: str = "CAM-01") -> str:
    """Restrict camera IDs to [A-Za-z0-9_-] so they are safe as file names."""
    cleaned = "".join(ch for ch in raw[:32] if ch.isalnum() or ch in "_-")
    return cleaned or default


@router.post("/frame")
async def upload_frame(request: Request) -> dict[str, Any]:
    """Ingest a camera JPEG frame.

    Accepts either a raw ``image/jpeg`` body with ``X-Camera-ID``,
    ``X-Camera-Name`` and ``X-Camera-Location`` headers (ESP32-CAM firmware),
    or a ``multipart/form-data`` upload with ``file`` and ``camera_id`` fields.
    """
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()

    if content_type == "image/jpeg":
        contents = await request.body()
        camera_id = sanitize_camera_id(request.headers.get("x-camera-id", ""))
    elif content_type == "multipart/form-data":
        form = await request.form()
        upload = form.get("file")
        if upload is None or isinstance(upload, str):
            raise HTTPException(status_code=400, detail="Multipart upload requires a 'file' field.")
        if not (upload.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Expected JPEG image.")
        contents = await upload.read()
        camera_id = sanitize_camera_id(str(form.get("camera_id", "")), default="cam_1")
    else:
        raise HTTPException(status_code=415, detail="Send a raw image/jpeg body or a multipart/form-data upload.")

    if not contents:
        raise HTTPException(status_code=400, detail="Empty image.")
    if len(contents) > MAX_FRAME_BYTES:
        raise HTTPException(status_code=413, detail=f"Frame exceeds {MAX_FRAME_BYTES} byte limit.")

    frame = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Failed to decode JPEG frame.")

    # Apply camera rotation if requested (useful when board is mounted on its side)
    rot = CAMERA_ROTATIONS.get(camera_id, 0)
    if rot == 90:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rot == 180:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    elif rot in (270, -90):
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    name = request.headers.get("x-camera-name", camera_id)[:80]
    location = request.headers.get("x-camera-location", "Unassigned")[:120]
    record_camera_frame(camera_id, name, location)

    if rot != 0:
        _, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        jpg_data = encoded.tobytes()
        set_frame(camera_id, jpg_data)
        (LATEST_DIR / f"{camera_id}.jpg").write_bytes(jpg_data)
    else:
        set_frame(camera_id, contents)
        (LATEST_DIR / f"{camera_id}.jpg").write_bytes(contents)

    queued = await frame_queue.enqueue_frame(camera_id, frame)
    return {
        "status": "success" if queued else "queued_dropped",
        "camera_id": camera_id,
        "bytes_received": len(contents),
        "frame_shape": list(frame.shape),
    }


CAMERA_ROTATIONS: dict[str, int] = {}


@router.post("/rotate")
async def rotate_camera(payload: dict[str, Any]):
    """Set orientation angle (0, 90, 180, 270 degrees) for a camera node."""
    cam_id = sanitize_camera_id(str(payload.get("camera_id", "")))
    rot = int(payload.get("rotation", 0)) % 360
    CAMERA_ROTATIONS[cam_id] = rot
    return {"status": "success", "camera_id": cam_id, "rotation": rot}


@router.get("/rotations")
async def get_rotations() -> dict[str, Any]:
    """Get active rotation angles for all camera nodes."""
    return {"status": "success", "rotations": CAMERA_ROTATIONS}


@router.post("/heartbeat")
async def device_heartbeat(payload: HeartbeatPayload):
    """Receive heartbeat & telemetry from ESP32 camera node."""
    record_heartbeat(
        device_id=payload.device_id,
        rssi=payload.rssi,
        free_heap=payload.free_heap,
        uptime=payload.uptime,
        fps=payload.fps,
    )
    return {"status": "ok", "device_id": payload.device_id}

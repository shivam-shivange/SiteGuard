"""Dashboard overview and camera feed routes."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import CAMERA_OFFLINE_SEC, CONFIRM_RATIO, CONFIRM_WINDOW_SEC, LATEST_DIR, REQUIRED_PPE
from app.database import camera_summary, query
from app.detection.model_manager import model_manager
from app.routes.camera import sanitize_camera_id
from app.services.frame_queue import frame_queue

router = APIRouter(prefix="/api", tags=["Dashboard"])


def build_overview() -> dict[str, Any]:
    """Aggregate camera health and open incidents for the dashboard."""
    cameras = camera_summary(CAMERA_OFFLINE_SEC)
    active = query(
        "SELECT * FROM incidents WHERE status IN ('active', 'acknowledged') ORDER BY created_at DESC"
    )
    total = query("SELECT COUNT(*) AS count FROM incidents")[0]["count"]
    workers = frame_queue.safety_engine.worker_statuses(time.time())
    return {
        "system_status": "online",
        "processing_status": model_manager.status,
        "workers_detected": sum(c["workers"] for c in cameras if c["status"] == "online"),
        "active_violations": len(active),
        "total_incidents": total,
        "cameras_online": sum(c["status"] == "online" for c in cameras),
        "cameras_total": len(cameras),
        "cameras": cameras,
        "recent_incidents": active[:10],
        "workers": workers,
        "monitoring": {
            "required_ppe": REQUIRED_PPE,
            "window_sec": CONFIRM_WINDOW_SEC,
            "confirm_ratio": CONFIRM_RATIO,
        },
    }


@router.get("/dashboard/overview")
async def dashboard_overview():
    return build_overview()


@router.get("/workers")
async def list_workers():
    """Live PPE status of every worker currently tracked on camera."""
    return frame_queue.safety_engine.worker_statuses(time.time())


@router.get("/model/status")
async def model_status():
    return model_manager.info()


@router.get("/cameras")
async def list_cameras():
    return camera_summary(CAMERA_OFFLINE_SEC)


@router.get("/cameras/{camera_id}/latest-frame")
async def latest_frame(camera_id: str):
    safe_id = sanitize_camera_id(camera_id, default="")
    path = LATEST_DIR / f"{safe_id}.jpg"
    if not safe_id or not path.is_file():
        raise HTTPException(status_code=404, detail="No frame has been received from this camera")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

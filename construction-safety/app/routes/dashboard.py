"""Dashboard overview, camera feed, and live dynamic parameters routes."""
from __future__ import annotations

import asyncio
import time
from typing import Any
import psutil
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from app.config import (
    CAMERA_OFFLINE_SEC,
    CONFIRM_RATIO,
    CONFIRM_WINDOW_SEC,
    CLEAR_RATIO,
    LATEST_DIR,
    REQUIRED_PPE,
    TRACKER_NAME,
    CLASS_CONFIDENCE,
)
from app.database import camera_summary, delete_camera, query, execute, now
from app.detection.model_manager import model_manager
from app.routes.camera import sanitize_camera_id
from app.services.frame_cache import get_frame, get_frame_with_time
from app.services.frame_queue import frame_queue
from tools.safety_scorecard import generate_scorecard

router = APIRouter(prefix="/api", tags=["Dashboard"])


class SafetyRuleUpdate(BaseModel):
    window_sec: float | None = None
    confirm_ratio: float | None = None
    clear_ratio: float | None = None
    worker_timeout_sec: float | None = None
    required_ppe: list[str] | None = None


def build_overview() -> dict[str, Any]:
    """Aggregate live camera health, active worker violations, and hardware diagnostics."""
    current_time = time.time()
    cameras = camera_summary(CAMERA_OFFLINE_SEC)
    online_cams = [c for c in cameras if c.get("status") == "online"]

    # Active incidents currently open in database
    active = query(
        "SELECT * FROM incidents WHERE status IN ('active', 'acknowledged') ORDER BY created_at DESC"
    )
    total = query("SELECT COUNT(*) AS count FROM incidents")[0]["count"]
    resolved = query("SELECT COUNT(*) AS count FROM incidents WHERE status = 'resolved'")[0]["count"]
    recent_24h = query(
        "SELECT COUNT(*) AS count FROM incidents WHERE created_at >= datetime('now', '-1 day')"
    )[0]["count"]

    # Live workers tracked on camera
    workers = frame_queue.safety_engine.worker_statuses(current_time)
    live_violations = sum(1 for w in workers if w.get("status") == "violation")
    compliant_workers = sum(1 for w in workers if w.get("status") == "compliant")
    monitoring_workers = sum(1 for w in workers if w.get("status") == "monitoring")

    # Processing and pipeline activity
    is_active = (current_time - frame_queue.last_processed_at) < 5.0 if frame_queue.last_processed_at > 0 else False
    avg_fps = round(sum(c.get("fps", 0.0) for c in online_cams), 1) if online_cams else round(frame_queue.last_fps, 1)
    avg_latency = round(sum(c.get("latency_ms", 0.0) for c in online_cams) / len(online_cams), 1) if online_cams else round(frame_queue.last_inference_ms, 1)

    # Hardware stats
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
    except Exception:
        cpu_percent = 0.0
        ram_percent = 0.0

    scorecard = generate_scorecard()

    return {
        "system_status": "online",
        "processing_status": "active" if is_active else ("ready" if model_manager.is_ready else model_manager.status),
        "workers_detected": len(workers),
        "live_violations": live_violations,
        "active_violations": len(active),  # Unresolved incidents in DB
        "compliant_workers": compliant_workers,
        "monitoring_workers": monitoring_workers,
        "total_incidents": total,
        "resolved_incidents": resolved,
        "incidents_24h": recent_24h,
        "cameras_online": len(online_cams),
        "cameras_total": len(cameras),
        "cameras": cameras,
        "recent_incidents": active[:25],
        "workers": workers,
        "processing_metrics": {
            "fps": avg_fps,
            "latency_ms": avg_latency,
            "queue_size": frame_queue.queue.qsize(),
            "max_queue_size": frame_queue.queue.maxsize,
            "total_processed": frame_queue.total_frames_processed,
            "total_dropped": frame_queue.total_frames_dropped,
            "tracker": TRACKER_NAME.split("/")[-1].split("\\")[-1].replace(".yaml", "").upper(),
            "is_active": is_active,
            "last_processed_sec": round(current_time - frame_queue.last_processed_at, 1) if frame_queue.last_processed_at > 0 else None,
        },
        "system_metrics": {
            "cpu_percent": cpu_percent,
            "ram_percent": ram_percent,
        },
        "safety_scorecard": scorecard,
        "monitoring": {
            "required_ppe": frame_queue.safety_engine.required_ppe,
            "window_sec": frame_queue.safety_engine.window_sec,
            "confirm_ratio": frame_queue.safety_engine.confirm_ratio,
            "clear_ratio": frame_queue.safety_engine.clear_ratio,
            "worker_timeout_sec": frame_queue.safety_engine.worker_timeout_sec,
            "min_observations": frame_queue.safety_engine.min_observations,
            "class_confidence": CLASS_CONFIDENCE,
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


@router.delete("/cameras/{camera_id}")
async def remove_camera(camera_id: str):
    """Remove/unregister a camera (e.g. offline test camera)."""
    safe_id = sanitize_camera_id(camera_id, default="")
    if not safe_id:
        raise HTTPException(status_code=400, detail="Invalid camera ID")
    delete_camera(safe_id)
    return {"status": "success", "message": f"Camera {safe_id} removed"}


@router.get("/cameras/{camera_id}/latest-frame")
async def latest_frame(camera_id: str):
    safe_id = sanitize_camera_id(camera_id, default="")
    cached = get_frame(safe_id) if safe_id else None
    if cached is not None:
        return Response(content=cached, media_type="image/jpeg", headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        })

    path = LATEST_DIR / f"{safe_id}.jpg"
    if not safe_id or not path.is_file():
        raise HTTPException(status_code=404, detail="No frame has been received from this camera")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@router.get("/cameras/{camera_id}/stream")
async def camera_stream(camera_id: str):
    """Real-time multipart/x-mixed-replace MJPEG stream for butter-smooth mobile/web playback."""
    safe_id = sanitize_camera_id(camera_id, default="")
    if not safe_id:
        raise HTTPException(status_code=400, detail="Invalid camera ID")

    async def frame_generator():
        last_sent_time = 0.0
        while True:
            try:
                frame_bytes, frame_time = get_frame_with_time(safe_id)
                if frame_bytes and frame_time > last_sent_time:
                    last_sent_time = frame_time
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n"
                        + frame_bytes + b"\r\n"
                    )
                await asyncio.sleep(0.04)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.1)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


@router.post("/incidents/resolve-all")
async def resolve_all_incidents():
    """Batch resolve all open incidents."""
    execute("UPDATE incidents SET status = 'resolved', updated_at = ? WHERE status IN ('active', 'acknowledged')", (now(),))
    return {"status": "success", "message": "All open incidents resolved"}


@router.get("/config/rules")
async def get_safety_rules():
    """Fetch current dynamic safety rules and thresholds."""
    return {
        "window_sec": frame_queue.safety_engine.window_sec,
        "confirm_ratio": frame_queue.safety_engine.confirm_ratio,
        "clear_ratio": frame_queue.safety_engine.clear_ratio,
        "worker_timeout_sec": frame_queue.safety_engine.worker_timeout_sec,
        "required_ppe": frame_queue.safety_engine.required_ppe,
        "class_confidence": CLASS_CONFIDENCE,
        "tracker_name": TRACKER_NAME,
    }


@router.post("/config/rules")
async def update_safety_rules(update: SafetyRuleUpdate):
    """Dynamically adjust safety rules without server restart."""
    engine = frame_queue.safety_engine
    if update.window_sec is not None and update.window_sec > 0:
        engine.window_sec = float(update.window_sec)
    if update.confirm_ratio is not None and 0.0 < update.confirm_ratio <= 1.0:
        engine.confirm_ratio = float(update.confirm_ratio)
    if update.clear_ratio is not None and 0.0 <= update.clear_ratio < engine.confirm_ratio:
        engine.clear_ratio = float(update.clear_ratio)
    if update.worker_timeout_sec is not None and update.worker_timeout_sec > 0:
        engine.worker_timeout_sec = float(update.worker_timeout_sec)
    if update.required_ppe is not None:
        engine.required_ppe = update.required_ppe
    return {
        "status": "success",
        "rules": {
            "window_sec": engine.window_sec,
            "confirm_ratio": engine.confirm_ratio,
            "clear_ratio": engine.clear_ratio,
            "worker_timeout_sec": engine.worker_timeout_sec,
            "required_ppe": engine.required_ppe,
        },
    }

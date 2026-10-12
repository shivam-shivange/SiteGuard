"""API routes for uploading construction site videos and controlling looped test streaming."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import VIDEOS_DIR
from app.services.video_streamer import ALLOWED_EXTENSIONS, video_streamer

logger = logging.getLogger("siteguard.routes.video_stream")

router = APIRouter(prefix="/api/video", tags=["Video Stream Simulation"])


class StartStreamPayload(BaseModel):
    video_filename: str
    camera_id: str = "CAM-VIDEO"
    camera_name: str = "Simulated Video Stream"
    location: str = "Site Test Zone"
    target_fps: float = 5.0
    loop: bool = True


class StopStreamPayload(BaseModel):
    camera_id: str = "CAM-VIDEO"


@router.get("/list")
async def list_videos() -> dict[str, Any]:
    """List all uploaded video files available for testing."""
    videos = video_streamer.list_available_videos()
    return {"status": "success", "videos": videos}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a construction site video file for testing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded video file is empty.")

    saved_path = video_streamer.save_video(file.filename, content)
    return {
        "status": "success",
        "filename": saved_path.name,
        "size_mb": round(len(content) / (1024 * 1024), 2),
        "message": f"Video '{saved_path.name}' uploaded successfully. Ready to stream.",
    }


@router.post("/start")
async def start_video_stream(payload: StartStreamPayload) -> dict[str, Any]:
    """Start streaming an uploaded video file through the detection pipeline in a loop."""
    try:
        result = await video_streamer.start_stream(
            video_filename=payload.video_filename,
            camera_id=payload.camera_id,
            camera_name=payload.camera_name,
            location=payload.location,
            target_fps=payload.target_fps,
            loop=payload.loop,
        )
        return {"status": "success", "stream": result}
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        logger.error("Failed to start video stream: %s", err, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start stream: {err}")


@router.post("/stop")
async def stop_video_stream(payload: StopStreamPayload) -> dict[str, Any]:
    """Stop an active video stream."""
    stopped = await video_streamer.stop_stream(payload.camera_id)
    if not stopped:
        return {"status": "not_running", "message": f"No active stream for {payload.camera_id}"}
    return {"status": "success", "message": f"Stream {payload.camera_id} stopped."}


@router.get("/status")
async def video_stream_status() -> dict[str, Any]:
    """Get status of all currently active video streams."""
    return {"status": "success", "active_streams": video_streamer.get_status()}


@router.delete("/{filename}")
async def delete_video(filename: str) -> dict[str, Any]:
    """Delete an uploaded video file from storage."""
    target_path = VIDEOS_DIR / filename
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found.")

    # Stop any stream currently playing this video
    for cam_id, stream in list(video_streamer.active_streams.items()):
        if stream.video_path.name == filename:
            await video_streamer.stop_stream(cam_id)

    target_path.unlink()
    return {"status": "success", "message": f"Video '{filename}' deleted."}

"""System diagnostics and hardware profiling routes."""
from __future__ import annotations

import logging
import os
import platform
import psutil
from fastapi import APIRouter

from app.config import MODEL_PATH, TARGET_IMAGE_SIZE
from app.services.frame_queue import frame_queue

logger = logging.getLogger("siteguard.routes.system")

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SiteGuard API",
        "version": "2.0.0",
    }


@router.get("/metrics")
async def system_metrics():
    """Fetch current system usage (CPU, RAM, Frame Queue stats)."""
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()

    return {
        "system": {
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_usage_percent": cpu_percent,
            "memory_total_mb": round(memory.total / (1024 * 1024), 2),
            "memory_available_mb": round(memory.available / (1024 * 1024), 2),
            "memory_usage_percent": memory.percent,
        },
        "frame_queue": {
            "current_size": frame_queue.queue.qsize(),
            "max_size": frame_queue.queue.maxsize,
            "total_received": frame_queue.total_frames_received,
            "total_processed": frame_queue.total_frames_processed,
            "total_dropped": frame_queue.total_frames_dropped,
        },
        "model": {
            "model_path": MODEL_PATH,
            "input_size": TARGET_IMAGE_SIZE,
        },
    }

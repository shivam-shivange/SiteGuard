"""In-memory cache for live camera frames to provide zero-latency mobile streaming.

Avoids disk I/O bottlenecks and file-locking issues during rapid multi-client access.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from app.config import LATEST_DIR

_frame_cache: dict[str, bytes] = {}
_frame_times: dict[str, float] = {}


def set_frame(camera_id: str, jpeg_bytes: bytes) -> None:
    """Store latest JPEG frame bytes and timestamp in memory."""
    _frame_cache[camera_id] = jpeg_bytes
    _frame_times[camera_id] = time.time()


def get_frame(camera_id: str) -> Optional[bytes]:
    """Retrieve the latest frame bytes from memory cache or fallback to disk."""
    if camera_id in _frame_cache:
        return _frame_cache[camera_id]

    disk_path = LATEST_DIR / f"{camera_id}.jpg"
    if disk_path.is_file():
        try:
            data = disk_path.read_bytes()
            _frame_cache[camera_id] = data
            _frame_times[camera_id] = disk_path.stat().st_mtime
            return data
        except Exception:
            return None
    return None


def get_frame_with_time(camera_id: str) -> tuple[Optional[bytes], float]:
    """Return both the latest frame bytes and its timestamp."""
    data = get_frame(camera_id)
    t = _frame_times.get(camera_id, 0.0)
    return data, t

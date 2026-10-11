"""Incident event management module.

Handles recording safety incidents into SQLite database, managing snapshot
storage, and pushing real-time WebSocket notifications.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import cv2

from app.config import SNAPSHOT_DIR
from app.database import record_incident, update_incident_violations
from app.websocket_hub import ws_hub

logger = logging.getLogger("siteguard.event_manager")

SNAPSHOT_PATH = Path(SNAPSHOT_DIR)
SNAPSHOT_PATH.mkdir(parents=True, exist_ok=True)


async def handle_incident_event(
    camera_id: str,
    violation_type: str,
    severity: str,
    track_id: int | None,
    confidence: float,
    annotated_frame: Any | None = None,
) -> dict[str, Any]:
    """Save incident to DB, persist snapshot image if provided, and broadcast WS event."""
    severity = severity.lower()  # dashboard styles severities by lowercase class name
    snapshot_filename = None
    if annotated_frame is not None:
        timestamp_str = int(time.time() * 1000)
        safe_vtype = violation_type.lower().replace(" ", "_").replace("-", "_").replace(",", "+")
        snapshot_filename = f"{camera_id}_{safe_vtype}_{timestamp_str}.jpg"
        full_filepath = SNAPSHOT_PATH / snapshot_filename
        try:
            cv2.imwrite(str(full_filepath), annotated_frame)
        except Exception as e:
            logger.error("Failed to write snapshot image %s: %s", full_filepath, e)
            snapshot_filename = None

    incident_id = record_incident(
        camera_id=camera_id,
        violation_type=violation_type,
        severity=severity,
        track_id=track_id,
        confidence=confidence,
        snapshot_filename=snapshot_filename,
    )

    event_payload = {
        "event_type": "INCIDENT_ALERT",
        "id": incident_id,
        "camera_id": camera_id,
        "violation_type": violation_type,
        "severity": severity,
        "track_id": track_id,
        "confidence": confidence,
        "snapshot_filename": snapshot_filename,
        "timestamp": time.time(),
    }

    await ws_hub.broadcast(event_payload)
    logger.warning(
        "ALERT [%s]: Camera %s - Violation '%s' (Track ID: %s, Conf: %.2f)",
        severity,
        camera_id,
        violation_type,
        track_id,
        confidence,
    )
    return event_payload


async def handle_incident_update(
    incident_id: int,
    violation_type: str,
    severity: str,
    confidence: float,
) -> dict[str, Any] | None:
    """Update an open incident whose episode gained more missing PPE items."""
    incident = update_incident_violations(incident_id, violation_type, severity.lower(), confidence)
    if incident is not None:
        await ws_hub.broadcast("incident.updated", incident)
        logger.warning(
            "ALERT UPDATE: incident %s on camera %s now '%s'",
            incident_id, incident["camera_id"], violation_type,
        )
    return incident

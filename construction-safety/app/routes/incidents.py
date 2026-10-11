"""Incident query and reporting routes."""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import SNAPSHOT_DIR
from app.database import get_incident, get_incident_stats, query_incidents, update_incident_status
from app.websocket_hub import ws_hub

logger = logging.getLogger("siteguard.routes.incidents")

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


class IncidentStatusUpdate(BaseModel):
    status: Literal["acknowledged", "resolved"]


@router.get("/")
async def list_incidents(
    camera_id: str | None = Query(None, description="Filter by camera ID"),
    violation_type: str | None = Query(None, description="Filter by violation type"),
    limit: int = Query(50, ge=1, le=500, description="Max incidents to return"),
):
    """Fetch safety incidents with optional filtering."""
    incidents = query_incidents(camera_id=camera_id, violation_type=violation_type, limit=limit)
    return {"status": "success", "count": len(incidents), "incidents": incidents}


@router.get("/stats")
async def incident_statistics():
    """Fetch aggregated incident metrics and per-camera summaries."""
    stats = get_incident_stats()
    return {"status": "success", "data": stats}


@router.get("/{incident_id}")
async def read_incident(incident_id: int):
    """Fetch a single incident."""
    incident = get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}")
async def change_incident_status(incident_id: int, update: IncidentStatusUpdate):
    """Acknowledge or resolve an incident and notify dashboards."""
    if get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident = update_incident_status(incident_id, update.status)
    await ws_hub.broadcast("incident.updated", incident)
    return incident


@router.get("/{incident_id}/evidence")
async def incident_evidence(incident_id: int):
    """Download the evidence snapshot captured for an incident."""
    incident = get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    path = SNAPSHOT_DIR / (incident["evidence_path"] or "")
    if not incident["evidence_path"] or not path.is_file():
        raise HTTPException(status_code=404, detail="Evidence image not found")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)

"""Construction Safety Monitoring MVP backend."""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR, EVIDENCE_DIR, LATEST_DIR = BASE_DIR / "data", BASE_DIR / "data" / "evidence", BASE_DIR / "data" / "latest"
MODEL_PATH = BASE_DIR / "yolov8n_v1_best.pt"
DB_PATH = DATA_DIR / "safety.db"
MAX_FRAME_BYTES, CAMERA_OFFLINE_SECONDS = 3 * 1024 * 1024, 15
PERSISTENCE_SECONDS, COOLDOWN_SECONDS = 2.0, 30.0
for directory in (DATA_DIR, EVIDENCE_DIR, LATEST_DIR):
    directory.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(DATA_DIR / "ultralytics"))
from ultralytics import YOLO

connections: set[WebSocket] = set()
pending: dict[tuple[str, str, int], float] = {}
cooldowns: dict[tuple[str, str, int], float] = {}
camera_models: dict[str, YOLO] = {}
model_status = "loading"
model_error: str | None = None
MODEL_LABELS = {0: "Hardhat", 1: "Mask", 2: "NO-Hardhat", 3: "NO-Mask", 4: "NO-Safety Vest",
                5: "Person", 6: "Safety Cone", 7: "Safety Vest", 8: "machinery", 9: "vehicle"}
VIOLATION_LABELS = {"no-hardhat": "no_helmet", "no-safety vest": "no_safety_vest", "no-mask": "no_mask"}

def now() -> str:
    return datetime.now(UTC).isoformat()

def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def setup_database() -> None:
    with db() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS cameras (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL,
              last_frame_at TEXT, frame_count INTEGER NOT NULL DEFAULT 0,
              fps REAL NOT NULL DEFAULT 0, latency_ms REAL NOT NULL DEFAULT 0,
              workers INTEGER NOT NULL DEFAULT 0,
              processing_status TEXT NOT NULL DEFAULT 'processing_unavailable'
            );
            CREATE TABLE IF NOT EXISTS incidents (
              id INTEGER PRIMARY KEY AUTOINCREMENT, camera_id TEXT NOT NULL,
              worker_id INTEGER NOT NULL, violation TEXT NOT NULL, severity TEXT NOT NULL,
              confidence REAL NOT NULL, status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL, evidence_path TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at DESC);
        """)

def query(sql: str, values: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with db() as c:
        return [dict(row) for row in c.execute(sql, values).fetchall()]

def incident_by_id(incident_id: int) -> dict[str, Any]:
    found = query("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    if not found:
        raise HTTPException(404, "Incident not found")
    return found[0]

def camera_summary() -> list[dict[str, Any]]:
    cameras = query("SELECT * FROM cameras ORDER BY id")
    current = datetime.now(UTC)
    for camera in cameras:
        last = camera["last_frame_at"]
        camera["status"] = "online" if last and (current - datetime.fromisoformat(last)).total_seconds() <= CAMERA_OFFLINE_SECONDS else "offline"
    return cameras

async def broadcast(event: str, payload: dict[str, Any]) -> None:
    message = json.dumps({"event": event, "data": payload})
    for socket in connections.copy():
        try:
            await socket.send_text(message)
        except Exception:
            connections.discard(socket)

class Detection(BaseModel):
    worker_id: int = Field(ge=0)
    violation: str = Field(pattern=r"^no_(helmet|safety_vest|gloves|boots|goggles|mask)$")
    confidence: float = Field(ge=0, le=1)

class IncidentStatus(BaseModel):
    status: str = Field(pattern="^(acknowledged|resolved)$")

async def create_incident(camera_id: str, d: Detection, image: bytes) -> dict[str, Any] | None:
    key, current = (camera_id, d.violation, d.worker_id), time.monotonic()
    began = pending.setdefault(key, current)
    if current - began < PERSISTENCE_SECONDS or current - cooldowns.get(key, 0) < COOLDOWN_SECONDS:
        return None
    pending.pop(key, None)
    cooldowns[key] = current
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    name = f"{camera_id}_{d.worker_id}_{d.violation}_{stamp}.jpg"
    (EVIDENCE_DIR / name).write_bytes(image)
    created = now()
    with db() as c:
        cursor = c.execute(
            """INSERT INTO incidents (camera_id,worker_id,violation,severity,confidence,created_at,updated_at,evidence_path)
               VALUES (?,?,?,?,?,?,?,?)""",
            (camera_id, d.worker_id, d.violation,
             "high" if d.violation in {"no_helmet", "no_safety_vest"} else "medium",
             d.confidence, created, created, name))
        incident_id = cursor.lastrowid
    incident = incident_by_id(incident_id)
    await broadcast("incident.created", incident)
    return incident

def load_model() -> None:
    """Validate the model at startup without running inference until a frame arrives."""
    global model_status, model_error
    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH.name}")
        model = YOLO(MODEL_PATH)
        labels = {int(key): value for key, value in model.names.items()}
        if labels != MODEL_LABELS:
            raise ValueError(f"Unexpected model labels: {labels}")
        model_status, model_error = "ready", None
    except Exception as error:
        model_status, model_error = "error", str(error)

def infer(camera_id: str, frame: np.ndarray) -> tuple[np.ndarray, int, list[Detection], list[dict[str, Any]]]:
    """Run an independent ByteTrack state machine for each camera."""
    model = camera_models.get(camera_id)
    if model is None:
        model = YOLO(MODEL_PATH)
        camera_models[camera_id] = model
    result = model.track(frame, persist=True, tracker="bytetrack.yaml", conf=0.45, verbose=False)[0]
    annotated = result.plot()
    records: list[dict[str, Any]] = []
    people: list[tuple[int, tuple[float, float, float, float]]] = []
    violations: list[tuple[str, float, tuple[float, float, float, float], int]] = []
    if result.boxes is not None:
        track_ids = result.boxes.id.int().tolist() if result.boxes.id is not None else [-1] * len(result.boxes)
        for box, class_id, confidence, track_id in zip(result.boxes.xyxy.tolist(), result.boxes.cls.int().tolist(),
                                                        result.boxes.conf.tolist(), track_ids):
            label = MODEL_LABELS.get(class_id, str(class_id))
            record = {"label": label, "confidence": round(float(confidence), 3), "track_id": int(track_id),
                      "box": [round(float(value), 1) for value in box]}
            records.append(record)
            normalized = label.lower()
            if normalized == "person":
                people.append((int(track_id), tuple(box)))
            elif normalized in VIOLATION_LABELS:
                violations.append((VIOLATION_LABELS[normalized], float(confidence), tuple(box), int(track_id)))
    safety_events: list[Detection] = []
    for violation, confidence, box, track_id in violations:
        # PPE labels do not share ByteTrack IDs with persons; associate with the
        # nearest detected person's bounding-box centre when possible.
        center_x, center_y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        worker_id = track_id if track_id >= 0 else 0
        if people:
            worker_id = min(people, key=lambda item: ((item[1][0] + item[1][2]) / 2 - center_x) ** 2 +
                            ((item[1][1] + item[1][3]) / 2 - center_y) ** 2)[0]
            worker_id = worker_id if worker_id >= 0 else 0
        safety_events.append(Detection(worker_id=worker_id, violation=violation, confidence=confidence))
    return annotated, len(people), safety_events, records

@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_database()
    await asyncio.to_thread(load_model)
    yield

app = FastAPI(title="Construction Safety Monitoring API", version="0.1.0", lifespan=lifespan)

@app.get("/")
def home() -> dict[str, str]:
    return {"status": "online", "system": "Construction Safety Monitoring", "dashboard": "/dashboard", "docs": "/docs"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return (BASE_DIR / "dashboard.html").read_text(encoding="utf-8")

@app.post("/api/camera/frame")
async def receive_frame(request: Request) -> dict[str, Any]:
    """Receive validated JPEG frames; does not falsely label unprocessed frames safe."""
    global model_error, model_status
    if request.headers.get("content-type", "").split(";", 1)[0].lower() != "image/jpeg":
        raise HTTPException(415, "Content-Type must be image/jpeg")
    image = await request.body()
    if not image:
        raise HTTPException(400, "Empty image")
    if len(image) > MAX_FRAME_BYTES:
        raise HTTPException(413, f"Frame exceeds {MAX_FRAME_BYTES} byte limit")
    frame = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "Body is not a valid JPEG image")
    camera_id = request.headers.get("x-camera-id", "CAM-01").upper()[:32]
    camera_id = "".join(character for character in camera_id if character.isalnum() or character in "_-") or "CAM-01"
    name = request.headers.get("x-camera-name", camera_id)[:80]
    location = request.headers.get("x-camera-location", "Unassigned")[:120]
    timestamp = now()
    detected_objects: list[dict[str, Any]] = []
    safety_events: list[Detection] = []
    workers, processing_state, display_image = 0, model_status, image
    if model_status == "ready":
        try:
            annotated, workers, safety_events, detected_objects = await asyncio.to_thread(infer, camera_id, frame)
            success, encoded = cv2.imencode(".jpg", annotated)
            if success:
                display_image = encoded.tobytes()
            processing_state = "running"
        except Exception as error:
            processing_state = "error"
            model_error = str(error)
            model_status = "error"
    with db() as c:
        previous = c.execute("SELECT last_frame_at FROM cameras WHERE id=?", (camera_id,)).fetchone()
        fps = 0.0
        if previous and previous["last_frame_at"]:
            elapsed = (datetime.now(UTC) - datetime.fromisoformat(previous["last_frame_at"])).total_seconds()
            fps = round(1 / elapsed, 2) if elapsed > 0 else 0.0
        c.execute("""INSERT INTO cameras (id,name,location,last_frame_at,frame_count,fps,workers,processing_status)
            VALUES (?,?,?,?,1,?,?,?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name,location=excluded.location,last_frame_at=excluded.last_frame_at,
            frame_count=cameras.frame_count+1,fps=excluded.fps,workers=excluded.workers,processing_status=excluded.processing_status""",
            (camera_id, name, location, timestamp, fps, workers, processing_state))
    (LATEST_DIR / f"{camera_id}.jpg").write_bytes(display_image)
    camera = next(c for c in camera_summary() if c["id"] == camera_id)
    await broadcast("camera.frame", camera)
    incidents = [event for detection in safety_events if (event := await create_incident(camera_id, detection, display_image))]
    return {"status": "received", "camera_id": camera_id, "size": len(image), "workers": workers,
            "processing_status": processing_state, "detections": detected_objects, "incidents": incidents}

@app.post("/api/cameras/{camera_id}/detections")
async def submit_detections(camera_id: str, request: Request) -> dict[str, Any]:
    """Trusted detector/tracker submits a JPEG plus an X-Detections JSON header."""
    image = await request.body()
    if not image or cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_COLOR) is None:
        raise HTTPException(400, "A JPEG evidence image is required")
    try:
        raw_detections = json.loads(request.headers.get("x-detections", "[]"))
        detections = [Detection.model_validate(item) for item in raw_detections]
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise HTTPException(400, "X-Detections must be a JSON array of normalized violations") from error
    incidents = [result for d in detections if (result := await create_incident(camera_id.upper()[:32], d, image))]
    return {"confirmed_incidents": incidents, "pending_count": len(detections) - len(incidents)}

@app.get("/api/dashboard/overview")
def overview() -> dict[str, Any]:
    cameras = camera_summary()
    active = query("SELECT * FROM incidents WHERE status IN ('active','acknowledged') ORDER BY created_at DESC")
    total = query("SELECT COUNT(*) AS count FROM incidents")[0]["count"]
    return {"system_status": "online", "processing_status": model_status,
            "workers_detected": sum(c["workers"] for c in cameras), "active_violations": len(active),
            "total_incidents": total, "cameras_online": sum(c["status"] == "online" for c in cameras),
            "cameras_total": len(cameras), "cameras": cameras, "recent_incidents": active[:10]}

@app.get("/api/model/status")
def get_model_status() -> dict[str, Any]:
    return {"status": model_status, "path": MODEL_PATH.name, "classes": MODEL_LABELS, "error": model_error}

@app.get("/api/cameras")
def get_cameras() -> list[dict[str, Any]]:
    return camera_summary()

@app.get("/api/cameras/{camera_id}/latest-frame")
def latest_frame(camera_id: str) -> FileResponse:
    safe_id = "".join(character for character in camera_id.upper() if character.isalnum() or character in "_-")
    path = LATEST_DIR / f"{safe_id}.jpg"
    if not safe_id or not path.is_file():
        raise HTTPException(404, "No frame has been received from this camera")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

@app.get("/api/incidents")
def get_incidents(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    limit = min(max(limit, 1), 500)
    return query("SELECT * FROM incidents" + (" WHERE status=?" if status else "") + " ORDER BY created_at DESC LIMIT ?",
                 ((status, limit) if status else (limit,)))

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: int) -> dict[str, Any]:
    return incident_by_id(incident_id)

@app.patch("/api/incidents/{incident_id}")
async def update_incident(incident_id: int, update: IncidentStatus) -> dict[str, Any]:
    incident_by_id(incident_id)
    with db() as c:
        c.execute("UPDATE incidents SET status=?,updated_at=? WHERE id=?", (update.status, now(), incident_id))
    incident = incident_by_id(incident_id)
    await broadcast("incident.updated", incident)
    return incident

@app.get("/api/incidents/{incident_id}/evidence")
def evidence(incident_id: int) -> FileResponse:
    incident = incident_by_id(incident_id)
    path = EVIDENCE_DIR / (incident["evidence_path"] or "")
    if not incident["evidence_path"] or not path.is_file():
        raise HTTPException(404, "Evidence image not found")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)

@app.websocket("/ws/dashboard")
async def dashboard_events(socket: WebSocket) -> None:
    await socket.accept()
    connections.add(socket)
    await socket.send_json({"event": "dashboard.snapshot", "data": overview()})
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        connections.discard(socket)

"""SQLite database with WAL mode and connection reuse."""
from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import UTC, datetime
from typing import Any

from app.config import DB_PATH

logger = logging.getLogger("siteguard.db")

_local = threading.local()


def _connection() -> sqlite3.Connection:
    """Return a thread-local reusable connection with WAL and tuned PRAGMAs."""
    conn: sqlite3.Connection | None = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # WAL allows concurrent reads while writing – instant free perf win.
        conn.execute("PRAGMA journal_mode=WAL")
        # NORMAL sync is safe with WAL and much faster than FULL.
        conn.execute("PRAGMA synchronous=NORMAL")
        # 8 MB page cache (default is ~2 MB).
        conn.execute("PRAGMA cache_size=-8000")
        _local.conn = conn
        logger.debug("New DB connection (thread %s)", threading.current_thread().name)
    return conn


# ── Public helpers ─────────────────────────────────────────────────────

def setup() -> None:
    """Create tables and indices if they do not already exist."""
    conn = _connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cameras (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            last_frame_at TEXT,
            frame_count INTEGER NOT NULL DEFAULT 0,
            fps REAL NOT NULL DEFAULT 0,
            latency_ms REAL NOT NULL DEFAULT 0,
            workers INTEGER NOT NULL DEFAULT 0,
            processing_status TEXT NOT NULL DEFAULT 'processing_unavailable'
        );

        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            worker_id INTEGER NOT NULL,
            violation TEXT NOT NULL,
            severity TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            evidence_path TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_incidents_created_at
            ON incidents(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_incidents_status
            ON incidents(status);

        CREATE TABLE IF NOT EXISTS device_heartbeats (
            device_id TEXT PRIMARY KEY,
            rssi INTEGER,
            uptime_seconds INTEGER,
            fps REAL,
            free_heap INTEGER,
            last_seen TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'incharge')),
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL
        );
    """)
    # One site in-charge per camera (column added to pre-existing databases).
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(cameras)")}
    if "incharge_user_id" not in columns:
        conn.execute("ALTER TABLE cameras ADD COLUMN incharge_user_id INTEGER REFERENCES users(id)")
        conn.commit()
    logger.info("Database initialised at %s (WAL mode)", DB_PATH)


def query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute a SELECT and return all rows as dicts."""
    conn = _connection()
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def execute(sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
    """Execute a write statement, commit, and return the cursor."""
    conn = _connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor


def now() -> str:
    """UTC ISO-8601 timestamp."""
    return datetime.now(UTC).isoformat()


def init_db() -> None:
    """Alias for setup()."""
    setup()



def record_incident(
    camera_id: str,
    violation_type: str,
    severity: str,
    track_id: int | None,
    confidence: float,
    snapshot_filename: str | None = None,
) -> int:
    """Record safety incident into database."""
    current_time = now()
    cursor = execute(
        """
        INSERT INTO incidents (camera_id, worker_id, violation, severity, confidence, status, created_at, updated_at, evidence_path)
        VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """,
        (
            camera_id,
            track_id if track_id is not None else -1,
            violation_type,
            severity,
            confidence,
            current_time,
            current_time,
            snapshot_filename,
        ),
    )
    return cursor.lastrowid or 0


def record_heartbeat(
    device_id: str,
    rssi: int | None = None,
    free_heap: int | None = None,
    uptime: int | None = None,
    fps: float | None = None,
) -> None:
    """Record or update device telemetry heartbeat."""
    execute(
        """
        INSERT INTO device_heartbeats (device_id, rssi, free_heap, uptime_seconds, fps, last_seen)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(device_id) DO UPDATE SET
            rssi = excluded.rssi,
            free_heap = excluded.free_heap,
            uptime_seconds = excluded.uptime_seconds,
            fps = excluded.fps,
            last_seen = excluded.last_seen
        """,
        (device_id, rssi, free_heap, uptime, fps, now()),
    )


def query_incidents(
    camera_id: str | None = None,
    violation_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Query incidents with optional camera and violation filtering."""
    sql = "SELECT * FROM incidents WHERE 1=1"
    params: list[Any] = []
    if camera_id:
        sql += " AND camera_id = ?"
        params.append(camera_id)
    if violation_type:
        sql += " AND violation = ?"
        params.append(violation_type)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = query(sql, tuple(params))
    for r in rows:
        if "violation" in r:
            r["violation_type"] = r["violation"]
        if "worker_id" in r:
            r["track_id"] = r["worker_id"]
    return rows




def get_incident(incident_id: int) -> dict[str, Any] | None:
    """Fetch a single incident by ID."""
    rows = query("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    return rows[0] if rows else None


def update_incident_status(incident_id: int, status: str) -> dict[str, Any] | None:
    """Set an incident's status and return the updated row."""
    execute("UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?", (status, now(), incident_id))
    return get_incident(incident_id)


def update_incident_violations(incident_id: int, violation: str, severity: str, confidence: float) -> dict[str, Any] | None:
    """Rewrite an open incident's violation list (an episode gained items)."""
    execute(
        "UPDATE incidents SET violation = ?, severity = ?, confidence = ?, updated_at = ? WHERE id = ?",
        (violation, severity, confidence, now(), incident_id),
    )
    return get_incident(incident_id)


def record_camera_frame(camera_id: str, name: str, location: str) -> None:
    """Register a received frame: upsert the camera and update its arrival FPS."""
    timestamp = now()
    previous = query("SELECT last_frame_at FROM cameras WHERE id = ?", (camera_id,))
    fps = 0.0
    if previous and previous[0]["last_frame_at"]:
        elapsed = (datetime.fromisoformat(timestamp) - datetime.fromisoformat(previous[0]["last_frame_at"])).total_seconds()
        fps = round(1 / elapsed, 2) if elapsed > 0 else 0.0
    execute(
        """
        INSERT INTO cameras (id, name, location, last_frame_at, frame_count, fps)
        VALUES (?, ?, ?, ?, 1, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            location = excluded.location,
            last_frame_at = excluded.last_frame_at,
            frame_count = cameras.frame_count + 1,
            fps = excluded.fps
        """,
        (camera_id, name, location, timestamp, fps),
    )


def record_camera_processing(camera_id: str, workers: int, latency_ms: float, processing_status: str) -> None:
    """Store the latest inference results for a camera."""
    execute(
        "UPDATE cameras SET workers = ?, latency_ms = ?, processing_status = ? WHERE id = ?",
        (workers, round(latency_ms, 1), processing_status, camera_id),
    )


def camera_summary(offline_after_sec: float) -> list[dict[str, Any]]:
    """All cameras with an online/offline status derived from last frame time."""
    cameras = query("SELECT * FROM cameras ORDER BY id")
    current = datetime.now(UTC)
    for camera in cameras:
        last = camera["last_frame_at"]
        online = last and (current - datetime.fromisoformat(last)).total_seconds() <= offline_after_sec
        camera["status"] = "online" if online else "offline"
    return cameras


def delete_camera(camera_id: str) -> bool:
    """Remove a camera entry from database."""
    execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
    execute("DELETE FROM device_heartbeats WHERE device_id = ?", (camera_id,))
    return True


def get_incident_stats() -> dict[str, Any]:
    """Retrieve aggregated incident metrics."""
    total_inc = query("SELECT COUNT(*) as count FROM incidents")[0]["count"]
    per_violation_rows = query("SELECT violation, COUNT(*) as count FROM incidents GROUP BY violation")
    per_violation = {r["violation"]: r["count"] for r in per_violation_rows}
    recent_24h = query(
        "SELECT COUNT(*) as count FROM incidents WHERE created_at >= datetime('now', '-1 day')"
    )[0]["count"]
    return {
        "total_incidents": total_inc,
        "per_violation": per_violation,
        "recent_count_24h": recent_24h,
    }


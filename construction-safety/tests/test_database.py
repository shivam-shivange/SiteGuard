"""Unit tests for database operations."""
from __future__ import annotations

import pytest
from app.database import (
    get_incident_stats,
    init_db,
    query_incidents,
    record_heartbeat,
    record_incident,
)


def test_database_operations(tmp_path, monkeypatch):
    test_db = tmp_path / "test_safety.db"
    monkeypatch.setattr("app.database.DB_PATH", str(test_db))

    init_db()

    # Test recording incident
    inc_id = record_incident(
        camera_id="cam_db_test",
        violation_type="NO-Safety Vest",
        severity="WARNING",
        track_id=42,
        confidence=0.92,
        snapshot_filename="test_snap.jpg",
    )
    assert inc_id is not None and inc_id > 0

    # Query incidents
    results = query_incidents(camera_id="cam_db_test")
    assert len(results) >= 1
    assert results[0]["violation_type"] == "NO-Safety Vest"
    assert results[0]["track_id"] == 42

    # Heartbeat
    record_heartbeat("esp32_cam_1", rssi=-65, free_heap=180000, uptime=3600, fps=4.2)
    stats = get_incident_stats()
    assert stats["total_incidents"] >= 1

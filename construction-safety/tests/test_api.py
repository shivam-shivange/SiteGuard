"""Integration tests for FastAPI endpoints."""
from __future__ import annotations

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app

init_db()
client = TestClient(app)



def test_health_endpoint():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_metrics_endpoint():
    response = client.get("/api/system/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert "frame_queue" in data


def test_heartbeat_endpoint():
    payload = {
        "device_id": "test_esp32",
        "rssi": -70,
        "free_heap": 210000,
        "uptime": 120,
        "fps": 3.8,
    }
    response = client.post("/api/camera/heartbeat", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_camera_frame_upload():
    # Generate dummy encoded JPEG frame
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    _, encoded_img = cv2.imencode(".jpg", img)

    files = {"file": ("test.jpg", encoded_img.tobytes(), "image/jpeg")}
    data = {"camera_id": "cam_unit_test"}

    response = client.post("/api/camera/frame", data=data, files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] in ["success", "queued_dropped"]
    assert res["camera_id"] == "cam_unit_test"


def test_incidents_list_endpoint():
    response = client.get("/api/incidents/")
    assert response.status_code == 200
    assert "incidents" in response.json()


def test_latest_frame_and_mask_rules():
    from app.services.frame_cache import set_frame
    dummy_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb"
    set_frame("cam_unit_test", dummy_jpeg)

    # Verify latest-frame
    resp = client.get("/api/cameras/cam_unit_test/latest-frame")
    assert resp.status_code == 200
    assert resp.content == dummy_jpeg
    assert resp.headers["content-type"] == "image/jpeg"

    # Verify mask is in rules
    rules_resp = client.get("/api/config/rules")
    assert rules_resp.status_code == 200
    rules = rules_resp.json()
    assert "mask" in rules["required_ppe"]


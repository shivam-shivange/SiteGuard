import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_video_list():
    response = client.get("/api/video/list")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "videos" in data


def test_video_status():
    response = client.get("/api/video/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "active_streams" in data


def test_video_upload_invalid_extension():
    response = client.post(
        "/api/video/upload",
        files={"file": ("test.txt", b"dummy content", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported video format" in response.json()["detail"]

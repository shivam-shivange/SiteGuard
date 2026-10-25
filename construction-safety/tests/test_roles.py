"""Role-based access and camera in-charge notifications."""
from __future__ import annotations

import asyncio
import threading

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app import auth
from app.main import app
from app.services.event_manager import notify_incharge
from app.websocket_hub import ws_hub


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "roles.db"))
    monkeypatch.setattr(database, "_local", threading.local())
    database.init_db()
    auth.ensure_default_admin()
    database.record_camera_frame("CAM-A", "Gate", "North")
    database.record_camera_frame("CAM-B", "Crane", "South")
    return TestClient(app)


def _login(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}


def test_admin_assigns_incharge_and_incharge_sees_cameras(client):
    admin = _login(client, "admin", "admin123")
    user = client.post("/api/users", headers=admin, json={
        "username": "ravi", "display_name": "Ravi", "password": "secret1"}).json()
    assert client.put("/api/cameras/CAM-A/incharge", headers=admin, json={"user_id": user["id"]}).status_code == 200

    ravi = _login(client, "ravi", "secret1")
    assert client.get("/api/auth/me", headers=ravi).json()["cameras"] == ["CAM-A"]
    assert client.get("/api/users", headers=ravi).status_code == 403
    assert client.get("/api/users").status_code == 401


class _FakeSocket:
    def __init__(self):
        self.sent: list[str] = []

    async def send_text(self, text):
        self.sent.append(text)


def test_notification_reaches_only_camera_incharge(client):
    a = auth.create_user("a", "A", "incharge", "secret1")
    b = auth.create_user("b", "B", "incharge", "secret1")
    database.execute("UPDATE cameras SET incharge_user_id = ? WHERE id = 'CAM-A'", (a["id"],))

    sock_a, sock_b = _FakeSocket(), _FakeSocket()
    ws_hub._users[sock_a], ws_hub._users[sock_b] = a, b
    try:
        asyncio.run(notify_incharge({"camera_id": "CAM-A", "violation_type": "no_helmet",
                                     "severity": "high", "track_id": 1}))
    finally:
        ws_hub._users.pop(sock_a, None)
        ws_hub._users.pop(sock_b, None)

    assert len(sock_a.sent) == 1 and '"camera_name": "Gate"' in sock_a.sent[0]
    assert sock_b.sent == []

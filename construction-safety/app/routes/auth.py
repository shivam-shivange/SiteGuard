"""Login, user management and camera in-charge assignment."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app import auth
from app.database import execute, query
from app.routes.camera import sanitize_camera_id

router = APIRouter(prefix="/api", tags=["Auth"])


class LoginPayload(BaseModel):
    username: str
    password: str


class UserPayload(BaseModel):
    username: str
    display_name: str
    password: str
    role: str = "incharge"


class InchargePayload(BaseModel):
    user_id: int | None = None


@router.post("/auth/login")
async def login(payload: LoginPayload) -> dict[str, Any]:
    token = auth.login(payload.username.strip(), payload.password)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": token, "user": auth.user_for_token(token)}


@router.post("/auth/logout")
async def logout(authorization: str | None = Header(default=None)) -> dict[str, str]:
    token = auth._bearer(authorization)
    if token:
        auth.logout(token)
    return {"status": "success"}


@router.get("/auth/me")
async def me(user: dict = Depends(auth.current_user)) -> dict[str, Any]:
    return {**user, "cameras": auth.cameras_for_user(user)}


@router.get("/users")
async def list_users(_: dict = Depends(auth.require_admin)) -> list[dict[str, Any]]:
    return query("SELECT id, username, display_name, role, created_at FROM users ORDER BY id")


@router.post("/users")
async def add_user(payload: UserPayload, _: dict = Depends(auth.require_admin)) -> dict[str, Any]:
    if not payload.username.strip() or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Username required and password must be ≥ 6 characters")
    try:
        return auth.create_user(payload.username.strip(), payload.display_name.strip() or payload.username,
                                payload.role, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(auth.require_admin)) -> dict[str, str]:
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    execute("UPDATE cameras SET incharge_user_id = NULL WHERE incharge_user_id = ?", (user_id,))
    execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    execute("DELETE FROM users WHERE id = ?", (user_id,))
    return {"status": "success"}


@router.put("/cameras/{camera_id}/incharge")
async def assign_incharge(camera_id: str, payload: InchargePayload,
                          _: dict = Depends(auth.require_admin)) -> dict[str, Any]:
    safe_id = sanitize_camera_id(camera_id, default="")
    if not query("SELECT 1 FROM cameras WHERE id = ?", (safe_id,)):
        raise HTTPException(status_code=404, detail="Unknown camera")
    if payload.user_id is not None and not query(
        "SELECT 1 FROM users WHERE id = ? AND role = 'incharge'", (payload.user_id,)
    ):
        raise HTTPException(status_code=400, detail="User is not a site in-charge")
    execute("UPDATE cameras SET incharge_user_id = ? WHERE id = ?", (payload.user_id, safe_id))
    return {"status": "success", "camera_id": safe_id, "incharge_user_id": payload.user_id}

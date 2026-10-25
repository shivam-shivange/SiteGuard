"""Users, roles and session tokens.

Two roles exist:

* ``admin``    — sees every camera, manages users and assigns site in-charges.
* ``incharge`` — the person responsible for one or more cameras; receives
  violation notifications only for the cameras assigned to them.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from typing import Any

from fastapi import Header, HTTPException

from app.database import execute, now, query

logger = logging.getLogger("siteguard.auth")

ROLES = ("admin", "incharge")
_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _, expected = stored.partition("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return hmac.compare_digest(digest.hex(), expected)


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {k: user[k] for k in ("id", "username", "display_name", "role")}


def create_user(username: str, display_name: str, role: str, password: str) -> dict[str, Any]:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    cur = execute(
        "INSERT INTO users (username, display_name, role, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, display_name, role, hash_password(password), now()),
    )
    return public_user(query("SELECT * FROM users WHERE id = ?", (cur.lastrowid,))[0])


def ensure_default_admin() -> None:
    """Create the first admin account when the users table is empty."""
    if query("SELECT 1 FROM users LIMIT 1"):
        return
    password = os.getenv("SITEGUARD_ADMIN_PASSWORD", "admin123")
    create_user("admin", "Administrator", "admin", password)
    logger.warning("Created default admin account 'admin' — change its password via SITEGUARD_ADMIN_PASSWORD")


def login(username: str, password: str) -> str | None:
    rows = query("SELECT * FROM users WHERE username = ?", (username,))
    if not rows or not verify_password(password, rows[0]["password_hash"]):
        return None
    token = secrets.token_urlsafe(32)
    execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, rows[0]["id"], now()))
    return token


def logout(token: str) -> None:
    execute("DELETE FROM sessions WHERE token = ?", (token,))


def user_for_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    rows = query(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?", (token,)
    )
    return public_user(rows[0]) if rows else None


def cameras_for_user(user: dict[str, Any]) -> list[str]:
    if user["role"] == "admin":
        return [r["id"] for r in query("SELECT id FROM cameras")]
    return [r["id"] for r in query("SELECT id FROM cameras WHERE incharge_user_id = ?", (user["id"],))]


# ── FastAPI dependencies ───────────────────────────────────────────────

def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = user_for_token(_bearer(authorization))
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user


def require_admin(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = current_user(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user

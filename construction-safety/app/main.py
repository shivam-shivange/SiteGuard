"""SiteGuard FastAPI application entry point."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    ALLOWED_CORS_ORIGINS,
    BASE_DIR,
    ENABLE_CORS,
    SNAPSHOT_DIR,
)
from app.auth import ensure_default_admin, user_for_token
from app.database import init_db
from app.detection.model_manager import model_manager
from app.routes.auth import router as auth_router
from app.routes.camera import router as camera_router
from app.routes.dashboard import build_overview
from app.routes.dashboard import router as dashboard_router
from app.routes.incidents import router as incidents_router
from app.routes.system import router as system_router
from app.routes.video_stream import router as video_stream_router
from app.services.frame_queue import frame_queue
from app.services.video_streamer import video_streamer
from app.websocket_hub import ws_hub

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("siteguard.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing SiteGuard database...")
    init_db()
    ensure_default_admin()

    logger.info("Validating detection model...")
    await asyncio.to_thread(model_manager.load)

    logger.info("Starting background frame processing queue worker...")
    frame_queue.start_worker()

    yield

    logger.info("Stopping frame processing queue worker...")
    await frame_queue.stop_worker()
    logger.info("Stopping active video streams...")
    await video_streamer.stop_all()
    logger.info("SiteGuard application shutdown complete.")


app = FastAPI(
    title="SiteGuard Safety Monitoring API",
    description="AI-based construction worker safety compliance monitoring system.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS setup
if ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register API routers
app.include_router(auth_router)
app.include_router(camera_router)
app.include_router(incidents_router)
app.include_router(system_router)
app.include_router(dashboard_router)
app.include_router(video_stream_router)

# Mount snapshots directory
app.mount("/snapshots", StaticFiles(directory=SNAPSHOT_DIR), name="snapshots")


@app.get("/")
async def serve_dashboard():
    """Serve single page HTML dashboard."""
    return FileResponse(BASE_DIR / "dashboard.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time incident broadcasts.

    Pass ``?token=<session token>`` to also receive role-based notifications.
    """
    await ws_hub.connect(websocket, user_for_token(websocket.query_params.get("token")))
    try:
        while True:
            # Keep connection open and consume incoming client messages if any
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket connection error: %s", e)
        ws_hub.disconnect(websocket)


@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """Dashboard live-update socket; sends an initial snapshot on connect."""
    await ws_hub.connect(websocket)
    try:
        await websocket.send_json({"event": "dashboard.snapshot", "data": build_overview()})
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception as e:
        logger.error("Dashboard WebSocket error: %s", e)
        ws_hub.disconnect(websocket)

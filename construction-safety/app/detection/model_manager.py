"""Singleton YOLO model manager.

Validates the model at startup and exposes status information.  The
actual per-camera inference instances are managed by ``inference.py``
(each camera needs its own ByteTrack state), but this module ensures the
weights file is valid before any frame arrives.

Supports both PyTorch (.pt) and ONNX (.onnx) weight files.  ONNX is
strongly recommended on CPU-only hardware (2–4× faster via onnxruntime).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.config import MODEL_PATH, ONNX_MODEL_PATH, MODEL_LABELS

logger = logging.getLogger("siteguard.model")


class ModelManager:
    """Lightweight wrapper that validates weights at startup."""

    def __init__(self) -> None:
        self.status: str = "not_loaded"
        self.error: str | None = None
        self.active_path: Path | None = None

    # ── Which weights file to use ──────────────────────────────────────
    @staticmethod
    def resolve_path() -> Path:
        """Return the best available weights file (prefer ONNX on CPU)."""
        if ONNX_MODEL_PATH.is_file():
            return ONNX_MODEL_PATH
        if MODEL_PATH.is_file():
            return MODEL_PATH
        raise FileNotFoundError(
            f"No model found.  Expected {MODEL_PATH.name} or {ONNX_MODEL_PATH.name}"
        )

    # ── Startup validation ─────────────────────────────────────────────
    def load(self) -> None:
        """Validate the model file.  Called once at startup (in a thread)."""
        from ultralytics import YOLO

        try:
            path = self.resolve_path()
            logger.info("Validating model: %s", path.name)

            model = YOLO(str(path))
            labels = {int(k): v for k, v in model.names.items()}
            if labels != MODEL_LABELS:
                raise ValueError(f"Unexpected model labels: {labels}")

            self.active_path = path
            self.status = "ready"
            self.error = None
            logger.info("Model validated — %s (%s)", path.name, path.suffix)

        except Exception as exc:
            self.status = "error"
            self.error = str(exc)
            logger.error("Model validation failed: %s", exc)

    # ── Info dict for the /api/model/status endpoint ───────────────────
    @property
    def is_ready(self) -> bool:
        return self.status == "ready"

    def info(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "path": self.active_path.name if self.active_path else "none",
            "format": self.active_path.suffix if self.active_path else "none",
            "classes": MODEL_LABELS,
            "error": self.error,
        }


# Module-level singleton
model_manager = ModelManager()

"""Central configuration for the SiteGuard safety monitoring system.

Every tunable parameter lives here with sensible defaults.  Override any
value at runtime via environment variables prefixed with ``SITEGUARD_``.
"""
from __future__ import annotations

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EVIDENCE_DIR = DATA_DIR / "evidence"
LATEST_DIR = DATA_DIR / "latest"
MODEL_PATH = BASE_DIR / "yolov8n_v1_best.pt"
ONNX_MODEL_PATH = BASE_DIR / "yolov8n_v1_best.onnx"
VIDEOS_DIR = DATA_DIR / "videos"
DB_PATH = DATA_DIR / "safety.db"

for _d in (DATA_DIR, EVIDENCE_DIR, LATEST_DIR, VIDEOS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Keep Ultralytics config inside the project tree
os.environ.setdefault("YOLO_CONFIG_DIR", str(DATA_DIR / "ultralytics"))

# ── Server ─────────────────────────────────────────────────────────────
HOST: str = os.getenv("SITEGUARD_HOST", "0.0.0.0")
PORT: int = int(os.getenv("SITEGUARD_PORT", "8000"))

# ── Model labels (must match the trained .pt weights) ──────────────────
MODEL_LABELS: dict[int, str] = {
    0: "Hardhat", 1: "Mask", 2: "NO-Hardhat", 3: "NO-Mask",
    4: "NO-Safety Vest", 5: "Person", 6: "Safety Cone",
    7: "Safety Vest", 8: "machinery", 9: "vehicle",
}

# PPE item → (label when worn, label when missing).  The violation code for a
# missing item is "no_<item>", e.g. "no_helmet".
PPE_LABELS: dict[str, tuple[str, str]] = {
    "helmet":      ("Hardhat",     "NO-Hardhat"),
    "safety_vest": ("Safety Vest", "NO-Safety Vest"),
    "mask":        ("Mask",        "NO-Mask"),
}

# ── Per-class confidence thresholds ────────────────────────────────────
# Lower threshold for Person (must not miss workers); higher for violation
# classes (reduce false positives).
CLASS_CONFIDENCE: dict[str, float] = {
    "Person":         float(os.getenv("SITEGUARD_CONF_PERSON",    "0.35")),
    "Hardhat":        float(os.getenv("SITEGUARD_CONF_HARDHAT",   "0.40")),
    "NO-Hardhat":     float(os.getenv("SITEGUARD_CONF_NO_HARDHAT","0.50")),
    "Mask":           float(os.getenv("SITEGUARD_CONF_MASK",      "0.40")),
    "NO-Mask":        float(os.getenv("SITEGUARD_CONF_NO_MASK",   "0.50")),
    "Safety Vest":    float(os.getenv("SITEGUARD_CONF_VEST",      "0.40")),
    "NO-Safety Vest": float(os.getenv("SITEGUARD_CONF_NO_VEST",   "0.50")),
    "Safety Cone":    float(os.getenv("SITEGUARD_CONF_CONE",      "0.40")),
    "machinery":      float(os.getenv("SITEGUARD_CONF_MACHINERY", "0.45")),
    "vehicle":        float(os.getenv("SITEGUARD_CONF_VEHICLE",   "0.45")),
}

# Feed YOLO the lowest per-class threshold so it never pre-filters a
# detection that would pass a class-specific check.
MODEL_CONFIDENCE: float = min(CLASS_CONFIDENCE.values())

# Tighter NMS IoU than the Ultralytics default (0.7) to reduce duplicate
# overlapping boxes, especially for "NO-Safety Vest" overlapping "Person".
MODEL_IOU: float = float(os.getenv("SITEGUARD_MODEL_IOU", "0.40"))

# Tracker configuration (BoT-SORT with Re-ID embeddings for occlusion recovery)
TRACKER_CONFIG_PATH: Path = BASE_DIR / "app" / "detection" / "botsort_reid.yaml"
TRACKER_NAME: str = os.getenv("SITEGUARD_TRACKER", str(TRACKER_CONFIG_PATH) if TRACKER_CONFIG_PATH.is_file() else "botsort.yaml")

# ── Worker PPE monitoring ──────────────────────────────────────────────
# Each tracked worker is observed over a sliding window.  A PPE item is
# confirmed missing only when it is detected missing in at least
# CONFIRM_RATIO of the worker's frames across a full window, and is cleared
# again once that share drops to CLEAR_RATIO or below.  One incident is
# raised per worker per violation episode, never repeatedly while it lasts.
REQUIRED_PPE: list[str] = [
    item.strip() for item in os.getenv("SITEGUARD_REQUIRED_PPE", "helmet,safety_vest,mask").split(",")
    if item.strip() in PPE_LABELS
]
CONFIRM_WINDOW_SEC: float = float(os.getenv("SITEGUARD_CONFIRM_WINDOW", "10.0"))
CONFIRM_RATIO: float      = float(os.getenv("SITEGUARD_CONFIRM_RATIO", "0.7"))
CLEAR_RATIO: float        = float(os.getenv("SITEGUARD_CLEAR_RATIO", "0.3"))
# Fewest frames of a worker inside the window before any verdict is made.
MIN_OBSERVATIONS: int     = int(os.getenv("SITEGUARD_MIN_OBSERVATIONS", "3"))
# A worker unseen for this long has left the scene; their episode ends.
# Must exceed the camera's frame interval (2 s at 0.5 FPS).
WORKER_TIMEOUT_SEC: float = float(os.getenv("SITEGUARD_WORKER_TIMEOUT", "10.0"))
# Share of a PPE box that must lie inside a person box to belong to them.
PPE_CONTAINMENT_MIN: float = float(os.getenv("SITEGUARD_PPE_CONTAINMENT", "0.5"))

SEVERITY: dict[str, str] = {
    "no_helmet":      "high",
    "no_safety_vest": "high",
    "no_mask":        "medium",
}

# ── Frame processing ──────────────────────────────────────────────────
MAX_FRAME_BYTES: int  = int(os.getenv("SITEGUARD_MAX_FRAME", str(3 * 1024 * 1024)))
FRAME_QUEUE_SIZE: int = int(os.getenv("SITEGUARD_QUEUE_SIZE", "10"))
PREPROCESS: bool      = os.getenv("SITEGUARD_PREPROCESS", "true").lower() == "true"

# "sync"  – process inside the HTTP handler, return detections in response
# "async" – enqueue frame, return immediately, process in background worker
INFERENCE_MODE: str = os.getenv("SITEGUARD_INFERENCE_MODE", "sync")

# ── Camera ─────────────────────────────────────────────────────────────
CAMERA_OFFLINE_SEC: int = int(os.getenv("SITEGUARD_OFFLINE_SEC", "15"))
MAX_CAMERAS: int        = int(os.getenv("SITEGUARD_MAX_CAMERAS", "4"))

# ── CORS ───────────────────────────────────────────────────────────────
CORS_ORIGINS: list[str] = os.getenv("SITEGUARD_CORS", "*").split(",")
ALLOWED_CORS_ORIGINS: list[str] = CORS_ORIGINS
ENABLE_CORS: bool = True

# ── Backwards & Layer Compatibility Aliases ────────────────────────────
MAX_QUEUE_SIZE: int        = FRAME_QUEUE_SIZE
SNAPSHOT_DIR: Path         = EVIDENCE_DIR
TARGET_IMAGE_SIZE          = (640, 640)

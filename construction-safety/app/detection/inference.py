"""Inference engine — YOLO detection + ByteTrack tracking + IoU-based PPE association.

Key improvements over the original monolithic ``infer()`` function:

* **Per-class confidence filtering** after YOLO runs (the model receives
  the *lowest* threshold so nothing is silently dropped before we can
  apply class-specific logic).
* **Containment-based association** of every PPE box (worn *and* missing)
  with the ``Person`` box that contains it, so each tracked worker gets a
  per-frame PPE checklist instead of loose, unattributed violations.
* **Configurable NMS IoU** (tighter default of 0.40 vs Ultralytics' 0.70)
  to reduce duplicate overlapping detections.
* **Optional CLAHE preprocessing** to improve detection in poor lighting.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from app.config import (
    CLASS_CONFIDENCE,
    MAX_CAMERAS,
    MODEL_CONFIDENCE,
    MODEL_IOU,
    MODEL_LABELS,
    PPE_CONTAINMENT_MIN,
    PPE_LABELS,
    PREPROCESS,
)
from app.detection.model_manager import model_manager
from app.detection.preprocessor import preprocess

logger = logging.getLogger("siteguard.inference")

# Each camera needs its own YOLO instance so ByteTrack's ``persist=True``
# maintains an *independent* tracking state per camera.  YOLOv8n weights
# are only ~6 MB; the per-instance overhead is acceptable for ≤4 cameras.
_camera_models: dict[str, Any] = {}


# Lowercase model label -> (PPE item, "ok" | "missing")
_PPE_BY_LABEL: dict[str, tuple[str, str]] = {}
for _item, (_worn, _missing) in PPE_LABELS.items():
    _PPE_BY_LABEL[_worn.lower()] = (_item, "ok")
    _PPE_BY_LABEL[_missing.lower()] = (_item, "missing")

Box = tuple[float, float, float, float]


@dataclass
class InferenceResult:
    """Everything produced by a single frame's inference pass."""
    annotated_frame: np.ndarray
    worker_count: int
    persons: list[dict[str, Any]]
    raw_objects: list[dict[str, Any]]
    inference_ms: float = 0.0


# ── Private helpers ────────────────────────────────────────────────────

def _get_camera_model(camera_id: str) -> Any:
    """Return (or create) the per-camera YOLO instance."""
    if camera_id in _camera_models:
        return _camera_models[camera_id]

    if len(_camera_models) >= MAX_CAMERAS:
        oldest = next(iter(_camera_models))
        logger.warning(
            "Camera limit (%d) reached — reusing model from %s for %s "
            "(tracking state may be shared)",
            MAX_CAMERAS, oldest, camera_id,
        )
        return _camera_models[oldest]

    from ultralytics import YOLO

    path = str(model_manager.resolve_path())
    model = YOLO(path)
    _camera_models[camera_id] = model
    logger.info(
        "Created YOLO instance for camera %s (%d / %d)",
        camera_id, len(_camera_models), MAX_CAMERAS,
    )
    return model


def _containment(inner: Box, outer: Box) -> float:
    """Share of *inner*'s area that lies inside *outer*."""
    ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix2, iy2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    if ix1 >= ix2 or iy1 >= iy2:
        return 0.0
    area = max((inner[2] - inner[0]) * (inner[3] - inner[1]), 1e-6)
    return (ix2 - ix1) * (iy2 - iy1) / area


def _attach_ppe(
    people: list[tuple[int, Box]],
    ppe_boxes: list[tuple[str, str, float, Box]],
) -> list[dict[str, Any]]:
    """Build a per-person PPE checklist from loose PPE detections.

    Each PPE box (e.g. "NO-Hardhat" or "Safety Vest") goes to the person box
    that contains most of it, provided at least ``PPE_CONTAINMENT_MIN`` of it
    lies inside.  Boxes belonging to nobody are ignored.  If both the worn and
    missing label of one item land on the same person, the more confident wins.
    """
    persons = [{"track_id": tid, "bbox": [round(v, 1) for v in box], "ppe": {}} for tid, box in people]

    for item, state, conf, box in ppe_boxes:
        best, best_score = None, PPE_CONTAINMENT_MIN
        for person, (_, pbox) in zip(persons, people):
            score = _containment(box, pbox)
            if score >= best_score:
                best, best_score = person, score
        if best is None:
            continue
        current = best["ppe"].get(item)
        if current is None or conf > current[1]:
            best["ppe"][item] = (state, round(conf, 3))

    return persons


# ── Public API ─────────────────────────────────────────────────────────

def run_inference(camera_id: str, frame: np.ndarray) -> InferenceResult:
    """Run the full detection → tracking → association pipeline on one frame.

    This function is designed to be called via ``asyncio.to_thread`` so it
    does not block the event loop.
    """
    if not model_manager.is_ready:
        return InferenceResult(
            annotated_frame=frame, worker_count=0,
            persons=[], raw_objects=[],
        )

    t0 = time.perf_counter()

    # ── 1. Optional preprocessing ──────────────────────────────────────
    processed = preprocess(frame) if PREPROCESS else frame

    # ── 2. YOLO + ByteTrack ────────────────────────────────────────────
    model = _get_camera_model(camera_id)
    result = model.track(
        processed,
        persist=True,
        tracker="bytetrack.yaml",
        conf=MODEL_CONFIDENCE,
        iou=MODEL_IOU,
        verbose=False,
    )[0]

    annotated = result.plot()
    inference_ms = (time.perf_counter() - t0) * 1000

    # ── 3. Parse & class-filter detections ─────────────────────────────
    raw_objects: list[dict[str, Any]] = []
    people: list[tuple[int, Box]] = []
    ppe_boxes: list[tuple[str, str, float, Box]] = []

    if result.boxes is not None:
        track_ids = (
            result.boxes.id.int().tolist()
            if result.boxes.id is not None
            else [-1] * len(result.boxes)
        )
        for box, cls_id, conf, tid in zip(
            result.boxes.xyxy.tolist(),
            result.boxes.cls.int().tolist(),
            result.boxes.conf.tolist(),
            track_ids,
        ):
            label = MODEL_LABELS.get(cls_id, str(cls_id))

            # Per-class confidence gate
            if conf < CLASS_CONFIDENCE.get(label, MODEL_CONFIDENCE):
                continue

            raw_objects.append({
                "label": label,
                "confidence": round(float(conf), 3),
                "track_id": int(tid),
                "box": [round(float(v), 1) for v in box],
            })

            normalised = label.lower()
            if normalised == "person":
                people.append((int(tid), tuple(box)))
            elif normalised in _PPE_BY_LABEL:
                item, state = _PPE_BY_LABEL[normalised]
                ppe_boxes.append((item, state, float(conf), tuple(box)))

    # ── 4. Attach PPE detections to the person wearing (or lacking) them ─
    persons = _attach_ppe(people, ppe_boxes)

    logger.debug(
        "camera=%s workers=%d ppe_boxes=%d objects=%d %.0fms",
        camera_id, len(people), len(ppe_boxes),
        len(raw_objects), inference_ms,
    )

    return InferenceResult(
        annotated_frame=annotated,
        worker_count=len(people),
        persons=persons,
        raw_objects=raw_objects,
        inference_ms=inference_ms,
    )


# ── OO Interface for Frame Queue Integration ───────────────────────────

class CameraInferenceEngine:
    def __init__(self, camera_id: str):
        self.camera_id = camera_id

    def process_frame(self, frame: np.ndarray) -> dict[str, Any]:
        result = run_inference(self.camera_id, frame)
        missing = sum(
            1 for person in result.persons
            for state, _ in person["ppe"].values() if state == "missing"
        )
        return {
            "annotated_frame": result.annotated_frame,
            "persons": result.persons,
            "stats": {
                "person_count": result.worker_count,
                "violation_count": missing,
                "inference_ms": result.inference_ms,
                "fps": round(1000.0 / max(result.inference_ms, 1.0), 1),
            },
        }


class CameraInferenceEngineManager:
    def get_engine(self, camera_id: str) -> CameraInferenceEngine:
        return CameraInferenceEngine(camera_id)


camera_inference_engines = CameraInferenceEngineManager()


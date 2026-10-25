"""Worker ByteTrack tracker with spatial Re-ID and canonical ID management.

Key guarantees:
1. Tracks ONLY workers (Person class), ignoring non-person detections like
   cones, vehicles, or loose PPE.
2. Canonical 1-indexed worker numbering (Worker #1, Worker #2, Worker #3...).
3. Spatial Re-ID recovery across occlusions and momentary detector dropouts,
   keeping Worker IDs locked to the same individual.
4. Per-camera tracker instances with clean reset capability on video loop.
"""
from __future__ import annotations

import logging
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment

logger = logging.getLogger("siteguard.tracker")

Box = tuple[float, float, float, float]


def _iou_matrix(boxes1: list[Box] | np.ndarray, boxes2: list[Box] | np.ndarray) -> np.ndarray:
    """Compute IoU matrix between two sets of xyxy bounding boxes."""
    if len(boxes1) == 0 or len(boxes2) == 0:
        return np.zeros((len(boxes1), len(boxes2)), dtype=np.float32)

    b1 = np.asarray(boxes1, dtype=np.float32)
    b2 = np.asarray(boxes2, dtype=np.float32)

    ix1 = np.maximum(b1[:, None, 0], b2[None, :, 0])
    iy1 = np.maximum(b1[:, None, 1], b2[None, :, 1])
    ix2 = np.minimum(b1[:, None, 2], b2[None, :, 2])
    iy2 = np.minimum(b1[:, None, 3], b2[None, :, 3])

    iw = np.maximum(0.0, ix2 - ix1)
    ih = np.maximum(0.0, iy2 - iy1)
    inter = iw * ih

    a1 = (b1[:, 2] - b1[:, 0]) * (b1[:, 3] - b1[:, 1])
    a2 = (b2[:, 2] - b2[:, 0]) * (b2[:, 3] - b2[:, 1])
    union = a1[:, None] + a2[None, :] - inter

    return inter / np.maximum(union, 1e-6)


class WorkerTrack:
    """Internal state of one tracked worker."""

    def __init__(self, track_id: int, bbox: Box, score: float, frame_idx: int):
        self.track_id = track_id
        self.bbox = list(bbox)
        self.score = score
        self.velocity = [0.0, 0.0]  # [vx, vy] on box centroid
        self.hits = 1
        self.lost_frames = 0
        self.last_seen_frame = frame_idx

    def predict(self) -> Box:
        """Linear velocity prediction for the bounding box."""
        vx, vy = self.velocity
        return (
            self.bbox[0] + vx,
            self.bbox[1] + vy,
            self.bbox[2] + vx,
            self.bbox[3] + vy,
        )

    def update(self, bbox: Box, score: float, frame_idx: int) -> None:
        """Update track with a newly matched detection."""
        old_cx = (self.bbox[0] + self.bbox[2]) / 2.0
        old_cy = (self.bbox[1] + self.bbox[3]) / 2.0
        new_cx = (bbox[0] + bbox[2]) / 2.0
        new_cy = (bbox[1] + bbox[3]) / 2.0

        # Smooth velocity estimate
        dt = max(1, frame_idx - self.last_seen_frame)
        measured_vx = (new_cx - old_cx) / dt
        measured_vy = (new_cy - old_cy) / dt
        self.velocity = [
            0.7 * self.velocity[0] + 0.3 * measured_vx,
            0.7 * self.velocity[1] + 0.3 * measured_vy,
        ]

        self.bbox = list(bbox)
        self.score = score
        self.hits += 1
        self.lost_frames = 0
        self.last_seen_frame = frame_idx


class WorkerByteTracker:
    """Two-stage ByteTrack implementation optimized for construction workers."""

    def __init__(
        self,
        high_thresh: float = 0.35,
        low_thresh: float = 0.15,
        match_thresh: float = 0.65,
        track_buffer: int = 60,
        coast_frames: int = 2,
    ):
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.match_thresh = match_thresh
        self.track_buffer = track_buffer
        # Lost tracks are still reported for this many frames so a single
        # detector dropout does not make the worker vanish from the feed.
        self.coast_frames = coast_frames
        self.frame_idx = 0
        self.active_tracks: list[WorkerTrack] = []
        self.lost_tracks: list[WorkerTrack] = []
        self.next_canonical_id = 1

    def reset(self) -> None:
        """Reset all tracking states and restart worker IDs at 1."""
        self.frame_idx = 0
        self.active_tracks.clear()
        self.lost_tracks.clear()
        self.next_canonical_id = 1
        logger.info("Worker tracker reset — next worker will start at #1")

    def _allocate_id(self, occupied: set[int]) -> int:
        """Find the smallest available 1-based canonical ID not in occupied."""
        cand = 1
        while cand in occupied:
            cand += 1
        return cand

    def update(self, detections: list[tuple[Box, float]]) -> list[tuple[int, Box]]:
        """Process one frame's person detections.

        detections: list of ((x1, y1, x2, y2), score)
        Returns: list of (canonical_track_id, (x1, y1, x2, y2))
        """
        self.frame_idx += 1

        if not detections and not self.active_tracks and not self.lost_tracks:
            return []

        # Predict current locations for all existing tracks
        for t in self.active_tracks:
            t.predict()
        for t in self.lost_tracks:
            t.predict()

        high_dets = [d for d in detections if d[1] >= self.high_thresh]
        low_dets = [d for d in detections if self.low_thresh <= d[1] < self.high_thresh]

        # Combine active and recently lost tracks as match candidates
        track_pool = self.active_tracks + self.lost_tracks
        matched_pool_indices: set[int] = set()
        matched_high_indices: set[int] = set()

        # ── Step 1: First association with high-confidence detections ──
        if track_pool and high_dets:
            pool_boxes = [t.predict() for t in track_pool]
            high_boxes = [d[0] for d in high_dets]
            ious = _iou_matrix(pool_boxes, high_boxes)
            cost = 1.0 - ious

            row_ind, col_ind = linear_sum_assignment(cost)
            for r, c in zip(row_ind, col_ind):
                if cost[r, c] <= self.match_thresh:
                    track_pool[r].update(high_dets[c][0], high_dets[c][1], self.frame_idx)
                    matched_pool_indices.add(r)
                    matched_high_indices.add(c)

        # ── Step 2: Second association of unmatched tracks with low-confidence detections ──
        unmatched_pool_indices = [i for i in range(len(track_pool)) if i not in matched_pool_indices]
        if unmatched_pool_indices and low_dets:
            rem_boxes = [track_pool[i].predict() for i in unmatched_pool_indices]
            low_boxes = [d[0] for d in low_dets]
            ious = _iou_matrix(rem_boxes, low_boxes)
            cost = 1.0 - ious

            row_ind, col_ind = linear_sum_assignment(cost)
            for r, c in zip(row_ind, col_ind):
                if cost[r, c] <= 0.60:
                    orig_idx = unmatched_pool_indices[r]
                    track_pool[orig_idx].update(low_dets[c][0], low_dets[c][1], self.frame_idx)
                    matched_pool_indices.add(orig_idx)

        # Separate into matched (active) and unmatched (lost)
        new_active: list[WorkerTrack] = []
        new_lost: list[WorkerTrack] = []
        current_occupied_ids = set()

        for i, t in enumerate(track_pool):
            if i in matched_pool_indices:
                new_active.append(t)
                current_occupied_ids.add(t.track_id)
            else:
                t.lost_frames += 1
                if t.lost_frames <= self.track_buffer:
                    new_lost.append(t)

        # ── Step 3: Spatial Re-ID recovery & new track creation ─────────
        unmatched_high_dets = [
            high_dets[c] for c in range(len(high_dets)) if c not in matched_high_indices
        ]

        for bbox, score in unmatched_high_dets:
            # Check spatial Re-ID against lost tracks within proximity
            best_match: WorkerTrack | None = None
            best_cost = 1.5

            cx2 = (bbox[0] + bbox[2]) / 2.0
            cy2 = (bbox[1] + bbox[3]) / 2.0
            diag2 = np.hypot(bbox[2] - bbox[0], bbox[3] - bbox[1])

            for t in new_lost:
                if t.track_id in current_occupied_ids:
                    continue
                lb = t.bbox
                cx1 = (lb[0] + lb[2]) / 2.0
                cy1 = (lb[1] + lb[3]) / 2.0
                diag1 = np.hypot(lb[2] - lb[0], lb[3] - lb[1])
                dist = np.hypot(cx1 - cx2, cy1 - cy2) / max((diag1 + diag2) / 2.0, 1e-6)

                # IoU check
                iou = _iou_matrix([lb], [bbox])[0, 0]

                if iou >= 0.20 or dist <= 0.60:
                    c_val = (1.0 - iou) if iou >= 0.20 else (1.0 + dist)
                    if c_val < best_cost:
                        best_cost = c_val
                        best_match = t

            if best_match is not None:
                best_match.update(bbox, score, self.frame_idx)
                new_lost.remove(best_match)
                new_active.append(best_match)
                current_occupied_ids.add(best_match.track_id)
            else:
                # Assign lowest available clean canonical ID
                assigned_id = self._allocate_id(current_occupied_ids)
                current_occupied_ids.add(assigned_id)
                new_track = WorkerTrack(assigned_id, bbox, score, self.frame_idx)
                new_active.append(new_track)

        self.active_tracks = new_active
        self.lost_tracks = new_lost

        # Sort tracks by canonical ID for consistent reporting
        self.active_tracks.sort(key=lambda t: t.track_id)
        reported = [(t.track_id, tuple(t.bbox)) for t in self.active_tracks]
        reported += [
            (t.track_id, t.predict()) for t in self.lost_tracks
            if t.lost_frames <= self.coast_frames and t.hits >= 2
        ]
        return sorted(reported, key=lambda r: r[0])


# Per-camera tracker cache
_camera_trackers: dict[str, WorkerByteTracker] = {}


def get_camera_tracker(camera_id: str) -> WorkerByteTracker:
    """Get or create the dedicated WorkerByteTracker for a camera."""
    if camera_id not in _camera_trackers:
        _camera_trackers[camera_id] = WorkerByteTracker()
    return _camera_trackers[camera_id]


def reset_camera_tracker(camera_id: str) -> None:
    """Reset the tracker state and worker IDs for a camera."""
    if camera_id in _camera_trackers:
        _camera_trackers[camera_id].reset()

"""Per-worker PPE compliance monitor for SiteGuard.

Every tracked worker is observed over a sliding window.  For each required
PPE item the engine counts the share of the worker's frames in which the item
was detected missing:

* An item is **confirmed missing** once that share reaches ``confirm_ratio``
  over a full window (the worker must have been tracked for the whole window,
  with at least ``min_observations`` frames).
* A confirmed item is **cleared** once the share falls to ``clear_ratio`` or
  below.  The gap between the two ratios stops alerts flapping on and off.

A worker with one or more confirmed items is in a *violation episode*.  The
engine raises exactly one incident when an episode starts, updates that same
incident if more items go missing during it, and only raises a new incident
after the episode has ended (all items cleared, or the worker left the scene).
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from app.config import (
    CLEAR_RATIO,
    CONFIRM_RATIO,
    CONFIRM_WINDOW_SEC,
    MIN_OBSERVATIONS,
    REQUIRED_PPE,
    SEVERITY,
    WORKER_TIMEOUT_SEC,
)

logger = logging.getLogger("siteguard.safety_engine")

_SEVERITY_RANK = {"high": 2, "medium": 1, "low": 0}


@dataclass
class Observation:
    """What was seen of one worker in one frame: item -> ("ok"|"missing", confidence)."""
    timestamp: float
    ppe: dict[str, tuple[str, float]]


@dataclass
class WorkerState:
    camera_id: str
    track_id: int
    first_seen: float
    last_seen: float
    observations: deque[Observation] = field(default_factory=deque)
    confirmed_missing: set[str] = field(default_factory=set)
    alerted_missing: set[str] = field(default_factory=set)
    incident_id: int | None = None


def violation_code(item: str) -> str:
    return f"no_{item}"


class SafetyEngine:
    """Tracks PPE compliance per worker and emits incident create/update events."""

    def __init__(
        self,
        required_ppe: list[str] | None = None,
        window_sec: float = CONFIRM_WINDOW_SEC,
        confirm_ratio: float = CONFIRM_RATIO,
        clear_ratio: float = CLEAR_RATIO,
        min_observations: int = MIN_OBSERVATIONS,
        worker_timeout_sec: float = WORKER_TIMEOUT_SEC,
    ):
        self.required_ppe = list(required_ppe if required_ppe is not None else REQUIRED_PPE)
        self.window_sec = window_sec
        self.confirm_ratio = confirm_ratio
        self.clear_ratio = clear_ratio
        self.min_observations = min_observations
        self.worker_timeout_sec = worker_timeout_sec
        self.workers: dict[tuple[str, int], WorkerState] = {}

    # ── Frame updates ──────────────────────────────────────────────────

    def update(self, camera_id: str, now: float, persons: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fold one frame's tracked persons into worker state.

        ``persons`` items look like ``{"track_id": 6, "ppe": {"helmet": ("missing", 0.62)}}``.
        Returns incident events: ``{"action": "create" | "update", ...}``.
        """
        events: list[dict[str, Any]] = []

        for person in persons:
            track_id = person.get("track_id")
            if track_id is None or track_id < 0:
                continue  # untracked detections cannot be monitored over time
            key = (camera_id, track_id)
            state = self.workers.get(key)
            if state is None:
                state = WorkerState(camera_id=camera_id, track_id=track_id, first_seen=now, last_seen=now)
                self.workers[key] = state
            state.last_seen = now
            state.observations.append(Observation(timestamp=now, ppe=dict(person.get("ppe", {}))))
            self._trim(state, now)
            self._evaluate(state, now)
            event = self._incident_event(state)
            if event:
                events.append(event)

        self._expire(now)
        return events

    def attach_incident(self, camera_id: str, track_id: int, incident_id: int) -> None:
        """Link the incident recorded for a worker's current episode."""
        state = self.workers.get((camera_id, track_id))
        if state is not None:
            state.incident_id = incident_id

    def reset_camera(self, camera_id: str) -> None:
        """Remove tracked workers for a specific camera (e.g. upon video rewind or camera reset)."""
        keys_to_remove = [k for k in self.workers if k[0] == camera_id]
        for k in keys_to_remove:
            del self.workers[k]
        logger.info("Cleared %d tracked workers for camera %s", len(keys_to_remove), camera_id)

    # ── Internals ──────────────────────────────────────────────────────

    def _trim(self, state: WorkerState, now: float) -> None:
        while state.observations and now - state.observations[0].timestamp > self.window_sec:
            state.observations.popleft()

    def _missing_ratio(self, state: WorkerState, item: str) -> float:
        frames = len(state.observations)
        missing = sum(1 for obs in state.observations if obs.ppe.get(item, ("", 0))[0] == "missing")
        return missing / frames if frames else 0.0

    def _window_full(self, state: WorkerState, now: float) -> bool:
        return now - state.first_seen >= self.window_sec and len(state.observations) >= self.min_observations

    def _evaluate(self, state: WorkerState, now: float) -> None:
        if not self._window_full(state, now):
            return
        for item in self.required_ppe:
            ratio = self._missing_ratio(state, item)
            if item not in state.confirmed_missing and ratio >= self.confirm_ratio:
                state.confirmed_missing.add(item)
                logger.info("Worker %s/%s: %s confirmed missing (%.0f%% of window)",
                            state.camera_id, state.track_id, item, ratio * 100)
            elif item in state.confirmed_missing and ratio <= self.clear_ratio:
                state.confirmed_missing.discard(item)
                logger.info("Worker %s/%s: %s cleared", state.camera_id, state.track_id, item)

    def _incident_event(self, state: WorkerState) -> dict[str, Any] | None:
        if not state.confirmed_missing:
            if state.alerted_missing:
                # Episode over: everything cleared.  A future violation alerts afresh.
                state.alerted_missing = set()
                state.incident_id = None
            return None

        new_items = state.confirmed_missing - state.alerted_missing
        if not new_items:
            return None
        first_alert = not state.alerted_missing
        state.alerted_missing |= state.confirmed_missing
        if not first_alert and state.incident_id is None:
            return None  # create still in flight; nothing to update yet

        items = self._ordered(state.alerted_missing)
        codes = [violation_code(item) for item in items]
        return {
            "action": "create" if first_alert else "update",
            "incident_id": state.incident_id,
            "camera_id": state.camera_id,
            "track_id": state.track_id,
            "violations": codes,
            "severity": max((SEVERITY.get(c, "medium") for c in codes), key=lambda s: _SEVERITY_RANK.get(s, 0)),
            "confidence": self._confidence(state, items),
        }

    def _ordered(self, items: set[str]) -> list[str]:
        return [item for item in self.required_ppe if item in items]

    def _confidence(self, state: WorkerState, items: list[str]) -> float:
        scores = [
            obs.ppe[item][1]
            for obs in state.observations
            for item in items
            if obs.ppe.get(item, ("", 0))[0] == "missing"
        ]
        return round(sum(scores) / len(scores), 3) if scores else 0.0

    def _expire(self, now: float) -> None:
        for key in [k for k, s in self.workers.items() if now - s.last_seen > self.worker_timeout_sec]:
            del self.workers[key]

    # ── Dashboard view ─────────────────────────────────────────────────

    def worker_statuses(self, now: float) -> list[dict[str, Any]]:
        """Live PPE status of every worker currently on camera."""
        self._expire(now)
        statuses = []
        for state in self.workers.values():
            items: dict[str, str] = {}
            for item in self.required_ppe:
                seen = [obs.ppe[item][0] for obs in state.observations if item in obs.ppe]
                if item in state.confirmed_missing:
                    items[item] = "missing"
                elif "missing" in seen:
                    items[item] = "checking"
                elif "ok" in seen:
                    items[item] = "ok"
                else:
                    items[item] = "unknown"

            if state.confirmed_missing:
                status = "violation"
            elif any(v in ("missing", "checking") for v in items.values()):
                status = "monitoring"
            elif all(value == "ok" for value in items.values()):
                status = "compliant"
            elif not any(v in ("missing", "checking") for v in items.values()) and (self._window_full(state, now) or any(v == "ok" for v in items.values())):
                status = "compliant"
            else:
                status = "monitoring"

            statuses.append({
                "camera_id": state.camera_id,
                "track_id": state.track_id,
                "status": status,
                "ppe": items,
                "monitored_sec": round(min(now - state.first_seen, self.window_sec), 1),
                "window_sec": self.window_sec,
                "incident_id": state.incident_id,
                "last_seen_sec": round(now - state.last_seen, 1),
            })
        return sorted(statuses, key=lambda w: (w["status"] != "violation", w["camera_id"], w["track_id"]))

"""Unit tests for the per-worker PPE compliance monitor."""
from __future__ import annotations

from app.services.safety_engine import SafetyEngine

CAM = "CAM-01"


def make_engine() -> SafetyEngine:
    return SafetyEngine(
        required_ppe=["helmet", "safety_vest", "mask"],
        window_sec=10.0,
        confirm_ratio=0.7,
        clear_ratio=0.3,
        min_observations=3,
        worker_timeout_sec=10.0,
    )


def person(track_id: int = 6, **ppe: str) -> dict:
    """person(helmet="missing", safety_vest="ok") -> one tracked person."""
    return {"track_id": track_id, "ppe": {item: (state, 0.8) for item, state in ppe.items()}}


def run(engine: SafetyEngine, start: int, end: int, make_persons, step: int = 1) -> list[tuple[int, dict]]:
    """Feed one frame per `step` seconds in [start, end); return (t, event) pairs."""
    events = []
    for t in range(start, end, step):
        for ev in engine.update(CAM, 1000.0 + t, make_persons(t)):
            events.append((t, ev))
            if ev["action"] == "create":
                engine.attach_incident(CAM, ev["track_id"], 100 + t)
    return events


def test_no_alert_until_window_confirms_then_single_alert():
    engine = make_engine()
    no_helmet = lambda t: [person(helmet="missing", safety_vest="ok", mask="ok")]

    events = run(engine, 0, 10, no_helmet)
    assert events == [], "still monitoring during the first window"

    events = run(engine, 10, 70, no_helmet)
    assert len(events) == 1, "exactly one alert for a continuous violation"
    t, ev = events[0]
    assert t == 10 and ev["action"] == "create"
    assert ev["violations"] == ["no_helmet"] and ev["severity"] == "high"


def test_all_missing_items_grouped_into_one_incident():
    engine = make_engine()
    events = run(engine, 0, 30, lambda t: [person(helmet="missing", safety_vest="missing", mask="missing")])
    assert len(events) == 1
    assert events[0][1]["violations"] == ["no_helmet", "no_safety_vest", "no_mask"]


def test_flickering_detection_does_not_alert():
    engine = make_engine()
    # Helmet reported missing in 2 of every 10 frames (detector noise).
    flicker = lambda t: [person(helmet="missing" if t % 10 in (3, 7) else "ok", safety_vest="ok", mask="ok")]
    assert run(engine, 0, 120, flicker) == []


def test_new_item_during_episode_updates_same_incident():
    engine = make_engine()
    run(engine, 0, 11, lambda t: [person(helmet="missing", safety_vest="ok", mask="ok")])
    events = run(engine, 11, 40, lambda t: [person(helmet="missing", safety_vest="missing", mask="ok")])
    assert len(events) == 1
    ev = events[0][1]
    assert ev["action"] == "update" and ev["incident_id"] == 110
    assert ev["violations"] == ["no_helmet", "no_safety_vest"]


def test_compliance_ends_episode_and_relapse_alerts_again():
    engine = make_engine()
    assert len(run(engine, 0, 15, lambda t: [person(helmet="missing", safety_vest="ok", mask="ok")])) == 1
    # Puts the helmet on: episode clears, no events.
    assert run(engine, 15, 40, lambda t: [person(helmet="ok", safety_vest="ok", mask="ok")]) == []
    assert engine.worker_statuses(1039.0)[0]["status"] == "compliant"
    # Takes it off again for a sustained period: a fresh incident.
    events = run(engine, 40, 60, lambda t: [person(helmet="missing", safety_vest="ok", mask="ok")])
    assert [ev["action"] for _, ev in events] == ["create"]


def test_worker_status_view():
    engine = make_engine()
    run(engine, 0, 4, lambda t: [person(helmet="missing", safety_vest="ok")])
    [w] = engine.worker_statuses(1003.0)
    assert w["status"] == "monitoring" and w["monitored_sec"] == 3.0
    assert w["ppe"] == {"helmet": "checking", "safety_vest": "ok", "mask": "unknown"}

    run(engine, 4, 12, lambda t: [person(helmet="missing", safety_vest="ok")])
    [w] = engine.worker_statuses(1011.0)
    assert w["status"] == "violation" and w["ppe"]["helmet"] == "missing"


def test_untracked_people_ignored_and_absent_workers_expire():
    engine = make_engine()
    run(engine, 0, 5, lambda t: [person(track_id=-1, helmet="missing")])
    assert engine.worker_statuses(1004.0) == []

    run(engine, 0, 5, lambda t: [person(helmet="ok")])
    assert len(engine.worker_statuses(1005.0)) == 1
    assert engine.worker_statuses(1020.0) == [], "worker gone after timeout"


def test_low_fps_camera_still_confirms():
    """At 0.5 FPS (one frame every 2 s) a full window has 5 frames."""
    engine = make_engine()
    events = run(engine, 0, 30, lambda t: [person(helmet="missing", safety_vest="ok", mask="ok")], step=2)
    assert len(events) == 1 and events[0][0] == 10

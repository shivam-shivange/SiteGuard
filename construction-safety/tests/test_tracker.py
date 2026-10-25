"""Unit tests for the WorkerByteTracker and canonical ID allocation."""
from __future__ import annotations

from app.detection.tracker import WorkerByteTracker, get_camera_tracker, reset_camera_tracker


def test_tracker_ids_start_at_one():
    tracker = WorkerByteTracker()
    detections = [
        ((100.0, 100.0, 200.0, 300.0), 0.85),
        ((400.0, 150.0, 500.0, 350.0), 0.90),
    ]
    tracks = tracker.update(detections)
    ids = [t[0] for t in tracks]
    assert ids == [1, 2], f"Expected IDs [1, 2], got {ids}"


def test_tracker_stays_on_same_worker():
    tracker = WorkerByteTracker()
    # Frame 1
    t1 = tracker.update([((100.0, 100.0, 200.0, 300.0), 0.85)])
    assert t1[0][0] == 1

    # Frame 2: worker moved slightly
    t2 = tracker.update([((105.0, 102.0, 205.0, 302.0), 0.88)])
    assert t2[0][0] == 1, "Track ID must remain 1 for moving worker"

    # Frame 3: momentary occlusion / dropout (no detection)
    t3 = tracker.update([])
    assert [t[0] for t in t3] == [1], "Briefly lost worker keeps coasting"

    # Frame 4: worker reappears nearby -> Spatial Re-ID recovery
    t4 = tracker.update([((110.0, 105.0, 210.0, 305.0), 0.82)])
    assert len(t4) == 1
    assert t4[0][0] == 1, "Track ID must recover as Worker #1 after occlusion"


def test_tracker_reset_restarts_at_one():
    tracker = WorkerByteTracker()
    tracker.update([((100.0, 100.0, 200.0, 300.0), 0.85)])
    tracker.update([((400.0, 100.0, 500.0, 300.0), 0.85)])
    
    tracker.reset()
    fresh = tracker.update([((250.0, 250.0, 350.0, 450.0), 0.85)])
    assert fresh[0][0] == 1, "After reset, first track ID must be 1"


def test_low_confidence_detection_keeps_track_alive():
    tracker = WorkerByteTracker()
    tracker.update([((100.0, 100.0, 200.0, 300.0), 0.85)])
    t2 = tracker.update([((104.0, 101.0, 204.0, 301.0), 0.20)])
    assert [t[0] for t in t2] == [1]

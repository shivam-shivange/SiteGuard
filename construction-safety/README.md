# SiteGuard — AI-Based Construction Site Worker Safety Monitoring System

SiteGuard is an optimized, real-time safety monitoring solution designed to run on resource-constrained hardware (e.g., AMD Ryzen 5 5625U CPU / integrated graphics) with wireless camera nodes (ESP32-CAM).

---

## ⚡ Key Optimizations & Features

1. **Modular FastAPI Architecture**: Decoupled ingestion, detection, safety rules, database, and real-time WebSockets into dedicated services under `app/`.
2. **Asynchronous Frame Queue**: Built-in `asyncio.Queue` buffers incoming frames from cameras, preventing HTTP handler blocking and dropping stale frames during peak loads.
3. **Optimized Object Detection & Tracking**:
   - **Per-class confidence thresholds** (`Person`: 0.35, `NO-Hardhat`: 0.50, `NO-Safety Vest`: 0.45, etc.).
   - **Tighter NMS IoU threshold** (0.40) to eliminate duplicate overlapping bounding boxes.
   - **IoU Containment Association**: Replaces naive nearest-center heuristics with bounding box containment (`IoU >= 0.30`) to associate PPE items directly with workers.
4. **SQLite WAL Mode & Pooling**: `PRAGMA journal_mode=WAL` with `NORMAL` sync and thread-local connection reuse for non-blocking concurrent database writes.
5. **CPU Pre-Processing**: Dynamic CLAHE contrast enhancement for low-light camera feeds.
6. **Telemetry & Device Health**: `/api/camera/heartbeat` endpoint for monitoring ESP32 RSSI, FPS, and free heap memory.
7. **Validation & Benchmarking**: System benchmarking tools (`tools/benchmark_system.py`) and safety reliability scorecard (`tools/safety_scorecard.py`).

---

## 📁 Repository Structure

```
construction-safety/
├── app/
│   ├── config.py              # Central configuration & env-var overrides
│   ├── database.py            # SQLite database manager with WAL mode
│   ├── websocket_hub.py       # Typed WebSocket broadcast hub
│   ├── main.py                # FastAPI entry point & routes
│   ├── detection/
│   │   ├── preprocessor.py    # CLAHE & image normalization
│   │   ├── model_manager.py   # YOLO model loader & validator
│   │   └── inference.py       # Per-camera ByteTrack & IoU containment
│   ├── services/
│   │   ├── safety_engine.py   # Temporal persistence & cooldown rules engine
│   │   ├── event_manager.py   # DB recording & snapshot saving
│   │   └── frame_queue.py     # Async frame queue & inference worker
│   └── routes/
│       ├── camera.py          # Frame upload & heartbeat endpoints
│       ├── incidents.py       # REST endpoints for incidents & statistics
│       └── system.py          # Health, metrics & hardware diagnostics
├── tools/
│   ├── benchmark_system.py    # Multi-camera load test & latency benchmark
│   └── safety_scorecard.py    # Safety score generator
├── tests/                     # pytest unit and integration tests
├── server.py                  # Uvicorn server launcher
├── dashboard.html             # Real-time WebSockets UI dashboard
├── requirements.txt           # Python dependencies
└── yolov8n_v1_best.pt         # Safety vision model weights
```

---

## 🚀 Quick Start

### 1. Installation

Activate your virtual environment and install requirements:

```bash
pip install -r requirements.txt
```

### 2. Start Server

```bash
python server.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open dashboard in browser: `http://localhost:8000/`

---

## 🧪 Running Tests & Benchmarks

### Run Unit & Integration Tests

```bash
pytest tests/
```

### Run System Benchmark

Simulate 2 cameras streaming @ 5 FPS:

```bash
python -m tools.benchmark_system --cameras 2 --frames 50 --fps 5.0
```

### Generate Safety Scorecard

```bash
python -m tools.safety_scorecard
```

---

## ⚙️ Configuration (Env Vars)

All parameters can be tuned in `app/config.py` or set via environment variables prefixed with `SITEGUARD_`:

- `SITEGUARD_TARGET_IMAGE_SIZE`: YOLO input resolution (default: `640`)
- `SITEGUARD_PERSISTENCE_SECONDS`: Violation persistence threshold (default: `2.0` s)
- `SITEGUARD_COOLDOWN_SECONDS`: Alert cooldown period (default: `30.0` s)
- `SITEGUARD_ENABLE_CLAHE`: Enable contrast enhancement (default: `True`)

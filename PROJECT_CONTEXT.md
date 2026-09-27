# Construction Site Worker Safety Monitoring System

## 1. Project Overview

### Working title
**AI-Based Construction Site Worker Safety Monitoring System**

### Core objective
Build a real-time computer-vision-based safety monitoring system for construction sites.

The system should use cameras to monitor workers and site conditions, run an AI detection pipeline, convert detections into meaningful safety events, and display the current safety status and historical incidents through a web dashboard.

The initial implementation will run the complete backend, AI model, database, and application server on a **local PC**. Hardware and cloud deployment will be considered after the local MVP is validated.

---

## 2. Problem Statement

Construction sites contain many simultaneous safety risks:

- Workers may not wear helmets.
- Workers may not wear safety vests/PPE.
- Workers may enter restricted or dangerous zones.
- Workers may get too close to heavy machinery.
- A human safety officer cannot continuously monitor every camera and worker.
- Manual monitoring can miss events, especially in large or busy sites.
- Raw computer-vision detections alone are not useful unless they are converted into actionable incidents.

### Proposed solution

Use computer vision to continuously analyze camera footage and automatically identify safety-related events.

The system should:

1. Capture video/images from a camera.
2. Transfer the data to the AI server.
3. Run object detection.
4. Track workers across frames.
5. Apply safety rules.
6. Confirm persistent violations.
7. Generate an incident/event.
8. Store evidence such as an image or short video clip.
9. Push the event to a web dashboard.
10. Maintain historical safety analytics.

---

# 3. Primary Architecture Decision

## Initial implementation: PC as local AI server

The PC will initially perform the computationally expensive work.

### Initial architecture

```text
             CONSTRUCTION SITE / CAMERA
                       |
                       v
                Camera / ESP32-CAM
                       |
                     Wi-Fi
                       |
                       v
              +------------------+
              |      PC SERVER   |
              |                  |
              | FastAPI          |
              | OpenCV           |
              | YOLO             |
              | ByteTrack        |
              | Safety Engine    |
              | Database         |
              +--------+---------+
                       |
                WebSocket / REST
                       |
                       v
              +------------------+
              | WEB DASHBOARD    |
              | React + Vite     |
              +------------------+
```

### Why this architecture?

- Avoids cloud GPU costs during development.
- Avoids buying Raspberry Pi/edge hardware before the architecture is validated.
- Makes debugging easier.
- Allows the CV model to run on a powerful PC.
- Allows the frontend and backend to be developed independently.
- Keeps the architecture portable for future cloud or edge deployment.

---

# 4. Deployment Options Considered

## Option 1 — Cloud CV

```text
Camera
  |
  v
Streaming device
  |
 Wi-Fi / Internet
  |
  v
Cloud server / GPU
  |
 YOLO
  |
 Safety Engine
  |
 Dashboard
```

### Advantages
- Easy to scale.
- Powerful GPU available.
- Centralized processing.
- No need for powerful hardware at each camera.

### Disadvantages
- Continuous GPU cost.
- Internet dependency.
- Bandwidth requirements.
- Raw video may introduce privacy concerns.
- Network latency can affect real-time performance.

### Decision
**Not the first implementation.**

Keep it as a future deployment option.

---

## Option 2 — Raspberry Pi / Edge AI

```text
Camera
  |
  v
Raspberry Pi
  |
Tiny CV model
  |
Events/images
  |
Cloud / PC
  |
Dashboard
```

### Advantages
- Lower bandwidth usage.
- Better privacy because processing can happen locally.
- Lower cloud inference cost.
- Can operate with intermittent internet.

### Disadvantages
- Hardware cost.
- Model optimization required.
- Limited compute.
- Deployment and maintenance become more difficult.
- May require accelerator hardware for strong real-time performance.

### Decision
**Future phase, not initial MVP.**

---

## Option 3 — ESP32-CAM + PC AI Server

This is the preferred hardware direction for prototyping.

```text
        ESP32-CAM
            |
         OV2640
            |
          Wi-Fi
            |
            v
       Local Network
            |
            v
       PC / AI Server
            |
      +-----+------+
      |            |
     YOLO       FastAPI
      |            |
      +-----+------+
            |
       WebSocket
            |
            v
       React Dashboard
```

### ESP32-CAM responsibilities

- Capture images/video frames.
- Connect to Wi-Fi.
- Send image/frame data to the server.
- Send device status/heartbeat.
- Optionally interface with sensors.
- Optionally receive commands.

### ESP32-CAM should NOT initially be responsible for full YOLO inference.

The PC should perform the heavy CV computation.

---

# 5. Recommended Development Path

Build progressively.

## Phase 0 — PC-only proof of concept

```text
Video file / PC webcam
        |
        v
OpenCV
        |
        v
YOLO
        |
        v
Safety Engine
        |
        v
FastAPI
        |
        v
Dashboard
```

Goal:

**Prove the CV + backend + dashboard pipeline.**

---

## Phase 1 — Simulated ESP32 communication

Use Wokwi or another simulator for the ESP32 communication layer.

```text
Simulated ESP32
      |
  Simulated data
      |
      v
FastAPI on PC
      |
      v
Dashboard
```

Wokwi can validate:

- ESP32 firmware
- Wi-Fi logic
- HTTP/MQTT communication
- device heartbeat
- event payloads
- LEDs/buzzer
- sensor logic

Wokwi does not provide a realistic ESP32-CAM live camera simulation.

---

## Phase 2 — ESP32-CAM camera testing

Use an ESP32-CAM with OV2640.

```text
ESP32-CAM
    |
  Wi-Fi
    |
    v
PC
    |
JPEG frames
    |
    v
YOLO
```

---

## Phase 3 — Real construction footage

Use actual or representative construction-site footage.

Evaluate:

- Detection precision
- Detection recall
- False positives
- False negatives
- Tracking stability
- FPS
- End-to-end latency
- Network reliability
- Image quality
- Safety-event accuracy

---

# 6. Computer Vision Pipeline

## Core pipeline

```text
Camera Frame
     |
     v
Frame Receiver
     |
     v
Frame Sampling / Preprocessing
     |
     v
YOLO Object Detection
     |
     v
Object Tracking
     |
     v
Safety Rule Engine
     |
     v
Persistence / Temporal Verification
     |
     v
Event Manager
     |
     +---------> Database
     |
     +---------> Evidence Storage
     |
     +---------> WebSocket
                     |
                     v
                Dashboard
```

---

# 7. Initial Detection Classes

Do not start with too many classes.

## MVP classes

```text
person
helmet
no_helmet
safety_vest
no_safety_vest
```

Possible later classes:

```text
excavator
truck
crane
forklift
ladder
scaffold
```

Potential advanced classes/features:

```text
worker fall
worker near machinery
restricted-zone entry
unsafe posture
crowding
missing PPE
```

---

# 8. Model

## Initial model

Use a lightweight YOLO model suitable for real-time inference.

Possible starting choices:

- YOLOv8n
- YOLO11n
- Another current lightweight YOLO detector

The exact model should be selected after benchmarking on the project's dataset and PC hardware.

### Model requirements

The model should prioritize:

- Good PPE detection.
- Low false positives.
- High inference FPS.
- Low inference latency.
- Small model size.
- Ability to run continuously.

Do not optimize only for mAP.

For this project, **safety-event reliability is more important than a single benchmark metric.**

---

# 9. Tracking

Use a multi-object tracker such as:

**ByteTrack**

Purpose:

```text
Frame 1 → Worker #1
Frame 2 → Worker #1
Frame 3 → Worker #1
...
```

Tracking allows the system to reason about a worker over time rather than treating every frame as an independent detection.

---

# 10. Safety Rule Engine

Raw detections should not immediately become incidents.

### Example

YOLO detects:

```text
NO HELMET
```

for one frame.

Do not immediately create an incident.

Instead:

```text
Detection
   |
   v
Track worker
   |
   v
Violation persists?
   |
   +---- NO ---> ignore / continue
   |
  YES
   |
   v
Create incident
```

Example rule:

> If a tracked worker appears to have no helmet continuously for approximately 2 seconds, generate a no-helmet incident.

The exact threshold must be experimentally tuned.

---

# 11. Alert Spam Prevention

A single violation should not create hundreds of incidents.

Bad implementation:

```text
5 FPS
30 seconds
= 150 detections
= 150 alerts
```

Correct implementation:

```text
Worker #17
   |
No helmet detected
   |
Persistent for > threshold
   |
ONE incident
   |
Cooldown
   |
Continue monitoring
```

The event manager should support:

- Debouncing
- Persistence thresholds
- Cooldown periods
- Duplicate-event suppression
- Track-ID association

---

# 12. Restricted Zone Detection

A high-value feature for later versions.

Define a polygon on the camera image:

```text
+-----------------------------+
|                             |
|     RESTRICTED ZONE         |
|                             |
|        _________            |
|       |         |           |
|       | DANGER  |           |
|       |  ZONE   |           |
|       |_________|           |
|                             |
+-----------------------------+
```

If a worker enters the polygon:

```text
Worker
  |
  v
Polygon intersection
  |
  v
Persistence check
  |
  v
Zone violation
  |
  v
Incident
```

---

# 13. Worker–Machinery Proximity

Possible advanced feature.

```text
       EXCAVATOR
           |
         2.1 m
           |
         WORKER
```

If worker-to-machinery distance is below a configured safety threshold:

```text
Proximity Warning
       |
       v
Temporal verification
       |
       v
Incident
```

This feature needs careful calibration because pixel distance is not directly equal to physical distance.

---

# 14. Evidence Capture

Do not store all footage indefinitely.

Preferred approach:

```text
Normal frame
    |
    v
Process
    |
    v
Discard / temporary buffer

Violation
    |
    v
Save evidence
    |
    +--> Image
    |
    +--> Short video clip
```

Possible evidence:

- Timestamp
- Camera ID
- Track ID
- Violation type
- Confidence
- Screenshot
- Short video clip
- Site/zone
- Event duration

---

# 15. Dashboard

The dashboard should be a **Safety Monitoring Dashboard**, not simply an object-detection viewer.

## Main dashboard metrics

```text
Workers
Helmet Compliance
Vest Compliance
Active Violations
Warnings
Camera Status
System Status
```

Example:

```text
+------------------------------------------+
| CONSTRUCTION SAFETY MONITOR              |
+------------------------------------------+
|                                          |
| Workers              18                  |
| Helmet Compliance    94.4%               |
| Vest Compliance      88.9%               |
|                                          |
| Active Violations     2                  |
| Warnings              4                  |
|                                          |
+------------------------------------------+
| LIVE CAMERA                              |
|                                          |
|       [video + detections]               |
|                                          |
+------------------------------------------+
| RECENT INCIDENTS                         |
|                                          |
| 14:32 Worker #17  No Helmet      RED     |
| 14:28 Worker #04  No Vest        RED     |
| 14:21 Worker #09  Restricted     YELLOW  |
+------------------------------------------+
```

---

# 16. Frontend

Recommended:

- React
- Vite
- JavaScript/TypeScript
- CSS/Tailwind if desired

The frontend should communicate with FastAPI.

Do NOT make the frontend directly run YOLO.

Correct:

```text
React
  |
REST / WebSocket
  |
FastAPI
  |
Detection Engine
  |
YOLO
```

Incorrect:

```text
React
  |
YOLO
```

---

# 17. Backend

Recommended:

**FastAPI**

Responsibilities:

- Camera/device API
- Frame receiving
- Detection results
- Safety events
- WebSocket connections
- Authentication
- Dashboard API
- Incident API
- Health checks
- Device heartbeat
- Configuration
- Model status

Example endpoints:

```text
GET  /
GET  /health

POST /api/camera/frame
POST /api/device/heartbeat

GET  /api/dashboard
GET  /api/incidents

GET  /api/cameras

WS   /ws/dashboard
WS   /ws/camera/{camera_id}
```

---

# 18. Data Model

Possible incident schema:

```json
{
  "incident_id": "INC-00001",
  "camera_id": "CAM-001",
  "site_id": "SITE-01",
  "track_id": 17,
  "type": "NO_HELMET",
  "confidence": 0.91,
  "severity": "HIGH",
  "timestamp": "2026-09-15T14:32:10",
  "duration_seconds": 3.2,
  "evidence_image": "/evidence/INC-00001.jpg",
  "evidence_video": "/evidence/INC-00001.mp4",
  "status": "ACTIVE"
}
```

---

# 19. Database

Recommended initial options:

### Development

SQLite or PostgreSQL.

### Larger implementation

PostgreSQL.

Store:

- Cameras
- Sites
- Workers/track IDs if required
- Detections
- Incidents
- Evidence metadata
- Alert history
- Device heartbeat
- Model versions

Avoid storing every raw detection forever.

---

# 20. Real-Time Communication

Use:

### REST

For:

- Configuration
- Historical incidents
- Dashboard initialization
- Camera list
- Reports

### WebSocket

For:

- Live safety events
- Live counters
- Camera status
- Alerts
- Real-time dashboard updates

Example:

```text
YOLO
  |
  v
Safety Event
  |
  v
FastAPI
  |
 WebSocket
  |
  v
React
  |
  v
Dashboard updates immediately
```

---

# 21. Expected Latency

The target should be measured rather than assumed.

Potential local-network target:

```text
Camera capture       50–200 ms
Network              20–100 ms
YOLO                  10–80 ms
Safety logic          <10 ms
WebSocket             10–50 ms
--------------------------------
Target               <500 ms
```

These are engineering targets, not guaranteed results.

The actual latency depends on:

- Camera
- Resolution
- JPEG compression
- FPS
- Wi-Fi
- PC hardware
- YOLO model
- Number of cameras
- Number of concurrent users
- Backend implementation

---

# 22. Frame Rate Strategy

Do not assume the AI must process 30 FPS.

Possible architecture:

```text
Camera
  |
25–30 FPS video
  |
  +--------------------> Dashboard video
  |
  +--> Sample 5–10 FPS --> YOLO
```

The correct AI FPS should be determined experimentally.

For PPE detection, processing fewer frames while using tracking may provide a good balance between:

- latency
- GPU usage
- bandwidth
- detection quality

---

# 23. Network Architecture

## Local prototype

```text
ESP32-CAM
    |
 Wi-Fi router
    |
    +------------------+
    |                  |
    v                  v
   PC               Browser
FastAPI              React
YOLO
```

Example:

```text
ESP32-CAM → 192.168.1.x
PC        → 192.168.1.x
```

The ESP32-CAM can send HTTP requests to the PC's local IP when both are on the same network.

---

# 24. Cloud Migration

Once the local system works:

```text
CURRENT

ESP32-CAM
    |
 Wi-Fi
    |
    v
Local PC
    |
 YOLO
    |
Dashboard
```

Can become:

```text
FUTURE

ESP32-CAM
    |
Internet
    |
    v
Cloud AI Server
    |
 YOLO
    |
Database
    |
Dashboard
```

The application should be designed so that changing the inference location does not require rewriting the dashboard.

---

# 25. Edge Migration

Another future architecture:

```text
ESP32-CAM / IP Camera
       |
       v
Edge Computer
(Raspberry Pi / Jetson / accelerator)
       |
 Tiny/optimized YOLO
       |
       +----> Event JSON
       |
       +----> Evidence image
       |
       v
Cloud / PC
       |
       v
Dashboard
```

The edge device can eventually reduce:

- bandwidth
- cloud GPU usage
- privacy exposure
- network dependency

---

# 26. Privacy and Compliance

Construction footage can contain identifiable workers.

The system should be designed with privacy in mind.

Important principles:

- Use secure communication.
- Authenticate devices and users.
- Restrict dashboard access.
- Avoid unnecessary identity tracking.
- Minimize raw-video retention.
- Store evidence only when necessary.
- Consider face blurring if identity is not needed.
- Maintain access logs.
- Define retention periods.
- Protect stored evidence.
- Document the purpose of monitoring.
- Review applicable Indian privacy/data-protection requirements before real deployment.
- If deployed internationally, review applicable local laws such as GDPR where relevant.

The system is a safety monitoring tool, not an employee-identification system.

---

# 27. Operational Risks

Real construction environments introduce problems not present in clean datasets.

Potential problems:

- Dust
- Rain
- Low light
- Strong sunlight
- Backlighting
- Camera vibration
- Dirty lens
- Occlusion
- Crowded scenes
- Workers bending
- Similar-colored PPE
- Different helmet types
- Different camera angles
- Network outages

The model must eventually be tested on real-world conditions.

---

# 28. Model Evaluation

Track at least:

### CV metrics

- Precision
- Recall
- mAP50
- mAP50-95
- F1 score
- Per-class performance

### System metrics

- Inference FPS
- End-to-end latency
- Network latency
- CPU usage
- GPU usage
- Memory usage
- Bandwidth
- Frame drop rate
- Camera uptime

### Safety metrics

Most important for the final system:

- False alarm rate
- Missed violation rate
- Incident confirmation accuracy
- Duplicate alert rate
- Average alert latency

---

# 29. Testing Strategy

## Unit testing

Test:

- Detection parsing
- Safety rules
- Event creation
- Duplicate suppression
- Database functions
- API endpoints

## Integration testing

Test:

```text
Camera
  ↓
Backend
  ↓
YOLO
  ↓
Safety Engine
  ↓
Database
  ↓
WebSocket
  ↓
Dashboard
```

## End-to-end testing

Test actual scenarios:

1. Worker with helmet.
2. Worker without helmet.
3. Worker with vest.
4. Worker without vest.
5. Worker enters restricted zone.
6. Worker leaves restricted zone.
7. Same violation persists.
8. Worker temporarily occluded.
9. Camera disconnects.
10. Wi-Fi disconnects.
11. Server restarts.
12. Multiple workers appear simultaneously.
13. Multiple violations occur simultaneously.

---

# 30. Device Health Monitoring

Each camera should periodically send a heartbeat.

Example:

```json
{
  "device_id": "CAM-001",
  "status": "ONLINE",
  "uptime": 18231,
  "wifi_rssi": -55,
  "fps": 8
}
```

Dashboard:

```text
CAM-001   🟢 ONLINE
CAM-002   🟢 ONLINE
CAM-003   🔴 OFFLINE
```

This is important because a safety system that silently stops receiving camera data is dangerous.

---

# 31. Failure Handling

The system should handle:

### Camera disconnected

```text
Camera
  X
Backend
  |
  v
Mark OFFLINE
  |
  v
Dashboard warning
```

### Wi-Fi failure

ESP32 should:

- Detect connection loss.
- Attempt reconnection.
- Resume streaming.
- Send heartbeat when connection returns.

### AI server failure

Dashboard should show:

```text
AI PROCESSING: OFFLINE
```

rather than showing stale "SAFE" data.

This is critical.

**No data must not be interpreted as SAFE.**

---

# 32. Security

Minimum requirements:

- HTTPS for deployment outside a trusted LAN.
- API authentication.
- Device authentication.
- Strong credentials.
- No hardcoded production passwords.
- Validate uploaded images.
- Restrict file types and file sizes.
- Protect evidence files.
- Rate-limit APIs where appropriate.
- Log important security events.

---

# 33. Suggested Technology Stack

## Hardware

Initial:

- PC
- Existing webcam or test video

Prototype hardware:

- ESP32-CAM
- OV2640
- Wi-Fi

Future:

- Raspberry Pi / Jetson / accelerator
- IP cameras
- PoE cameras if appropriate

## AI

- Python
- PyTorch
- YOLO
- OpenCV
- ByteTrack

## Backend

- FastAPI
- Uvicorn
- WebSockets

## Database

- PostgreSQL
- SQLite for very early testing

## Frontend

- React
- Vite
- Tailwind CSS if desired

## Infrastructure

- Docker
- Docker Compose

Cloud can be introduced later.

---

# 34. Recommended Repository Structure

```text
construction-safety/
│
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── camera.py
│   │   ├── incidents.py
│   │   └── dashboard.py
│   │
│   ├── detection/
│   │   ├── detector.py
│   │   ├── tracker.py
│   │   ├── preprocessing.py
│   │   └── safety_rules.py
│   │
│   ├── services/
│   │   ├── event_manager.py
│   │   ├── evidence.py
│   │   └── notifications.py
│   │
│   └── database/
│       ├── models.py
│       └── database.py
│
├── models/
│   └── safety_model.pt
│
├── frontend/
│   ├── src/
│   └── package.json
│
├── data/
│   ├── videos/
│   ├── evidence/
│   └── datasets/
│
├── hardware/
│   └── esp32_cam/
│       └── firmware/
│
├── simulation/
│   └── wokwi/
│
├── tests/
│
├── docker-compose.yml
├── README.md
└── PROJECT_CONTEXT.md
```

---

# 35. MVP Definition

The first successful MVP should do only this:

```text
Camera / Video
      |
      v
YOLO
      |
      v
Person + Helmet + Vest
      |
      v
Tracking
      |
      v
Safety Rules
      |
      v
Violation Event
      |
      +----> Evidence image
      |
      +----> Database
      |
      +----> WebSocket
                  |
                  v
             Dashboard
```

### MVP success criteria

- Detect workers.
- Detect helmet violations.
- Detect vest violations.
- Track workers.
- Prevent duplicate alerts.
- Display live detection state.
- Generate incidents.
- Save evidence.
- Show incident history.
- Show camera/server status.
- Measure latency.

---

# 36. Features to Avoid in the First MVP

Do NOT start with all of these simultaneously:

- Fall detection
- Facial recognition
- Worker identity recognition
- Predictive accident prediction
- 10+ object classes
- Multi-site management
- Mobile app
- Full cloud deployment
- Edge AI optimization
- Complex analytics
- Automated disciplinary decisions

First make the basic system reliable.

---

# 37. Project Value Proposition

The project should not be presented as:

> "YOLO-based helmet detection."

That is too narrow and not particularly novel.

Present it as:

> **An AI-powered real-time construction safety monitoring and incident-management system that converts camera footage into actionable safety events, evidence, alerts, and analytics.**

The value comes from the complete pipeline:

```text
Camera
  ↓
AI Detection
  ↓
Tracking
  ↓
Safety Reasoning
  ↓
Violation Confirmation
  ↓
Evidence
  ↓
Alert
  ↓
Dashboard
  ↓
Historical Analytics
```

The system acts as an additional monitoring layer for safety officers rather than replacing human judgment.

---

# 38. Key Engineering Principle

**Detection is not the final product.**

The product is:

```text
Reliable Detection
       +
Reliable Event Logic
       +
Low False Alerts
       +
Fast Alerts
       +
Useful Evidence
       +
Usable Dashboard
       +
Reliable Device Monitoring
```

A model with excellent mAP but constant false alerts is not a successful safety system.

---

# 39. Initial Performance Target

Use these as development targets, then validate experimentally:

```text
AI inference:             real-time
Dashboard update:         near real-time
End-to-end alert:         <500 ms target
AI processing:            5–10 FPS initial target
Duplicate alerts:         minimized
Camera uptime:            monitored
False alerts:             measured
Missed violations:        measured
```

Do not claim these values until actual tests produce them.

---

# 40. Immediate Implementation Plan

## Step 1
Create the repository and project structure.

## Step 2
Run a construction video through YOLO.

## Step 3
Add helmet/vest detection.

## Step 4
Add ByteTrack.

## Step 5
Implement safety-event rules.

## Step 6
Implement FastAPI.

## Step 7
Implement database storage.

## Step 8
Implement WebSocket updates.

## Step 9
Create React dashboard.

## Step 10
Connect video/detection to the dashboard.

## Step 11
Measure latency and detection performance.

## Step 12
Test camera failure and server failure.

## Step 13
Add ESP32-CAM.

## Step 14
Replace video-file input with live ESP32-CAM input.

## Step 15
Test real construction-site footage.

## Step 16
Optimize model/network based on measured bottlenecks.

## Step 17
Only then evaluate cloud or edge deployment.

---

# 41. Final Architecture Recommendation

### Development

```text
                 PC
     +--------------------------+
     |                          |
Camera → OpenCV → YOLO          |
     |             ↓            |
     |          ByteTrack       |
     |             ↓            |
     |       Safety Engine      |
     |             ↓            |
     |        Event Manager     |
     |             ↓            |
     |        PostgreSQL        |
     |             ↓            |
     |          FastAPI         |
     +-------------+------------+
                   |
              WebSocket/API
                   |
                   v
             React Dashboard
```

### Hardware version

```text
ESP32-CAM
    |
  Wi-Fi
    |
    v
Router
    |
    v
PC
    |
 YOLO + Tracking + Safety Engine
    |
    v
FastAPI
    |
    v
React Dashboard
```

### Future cloud version

```text
ESP32-CAM / IP Camera
          |
       Internet
          |
          v
      Cloud GPU
          |
     YOLO + Rules
          |
       Database
          |
       Dashboard
```

### Future edge version

```text
Camera
  |
Edge AI Device
  |
Tiny YOLO
  |
Events + Evidence
  |
Cloud / PC
  |
Dashboard
```

---

# 42. Final Decision

**Build the local-PC architecture first.**

Do not purchase Raspberry Pi hardware yet.

Do not start with cloud deployment.

Do not optimize YOLO for edge hardware yet.

First prove:

```text
VIDEO
  ↓
YOLO
  ↓
TRACKING
  ↓
SAFETY RULES
  ↓
INCIDENT
  ↓
EVIDENCE
  ↓
FASTAPI
  ↓
WEBSOCKET
  ↓
DASHBOARD
```

Then introduce the ESP32-CAM as the camera/network node.

This minimizes cost, reduces development risk, and keeps the system ready for future cloud or edge deployment.

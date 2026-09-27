# Construction Safety Monitoring MVP

Run the FastAPI service:

```powershell
cd construction-safety
.\venv\Scripts\python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

For a fresh virtual environment, install dependencies with:

    .\venv\Scripts\python -m pip install -r requirements.txt

Open `http://127.0.0.1:8000/docs` for the API. The dashboard socket is `ws://127.0.0.1:8000/ws/dashboard`.

The ESP32 posts JPEG frames to `POST /api/camera/frame`. Add `X-Camera-ID`, `X-Camera-Name`, and `X-Camera-Location` headers to identify it. Frames are size- and image-validated before recording camera health. A camera becomes offline after 15 seconds without a frame.

The server deliberately reports `processing_unavailable` until a trained detector is connected—it never treats unprocessed footage as safe. A trusted inference worker posts a JPEG evidence frame to `POST /api/cameras/{camera_id}/detections` with an `X-Detections` header containing a JSON array such as `[{"worker_id":12,"violation":"no_helmet","confidence":0.91}]`. Incidents require 2 seconds of persistence and use a 30-second duplicate-suppression cooldown.

## Connected model

`yolov8n_v1_best.pt` is loaded automatically at server startup. It detects
`Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`, `NO-Safety Vest`, `Person`,
`Safety Cone`, `Safety Vest`, `machinery`, and `vehicle`. Missing hardhats,
masks, and vests are converted into rule-based incidents after the configured
persistence period. The live camera frame in the dashboard is annotated by YOLO.

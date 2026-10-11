"""SiteGuard Server Launcher.

Launches the modular FastAPI application from ``app.main:app``.
"""
import sys
import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print(f"Starting SiteGuard Safety Monitoring Server on http://{HOST}:{PORT}")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False, workers=1)

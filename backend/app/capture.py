"""M1: fetch a frame from the gym camera.

Run directly (`python -m app.capture`) to loop forever, saving a frame
every POLL_INTERVAL_SECONDS to backend/frames/latest.jpg so you can open
it and confirm the loop is actually pulling fresh images.
"""

import time
from datetime import datetime
from pathlib import Path

import requests

from app.config import CAMERA_URL, POLL_INTERVAL_SECONDS, REQUEST_TIMEOUT_SECONDS, USER_AGENT

FRAMES_DIR = Path(__file__).resolve().parent.parent / "frames"


def fetch_frame() -> bytes:
    """GET the camera image and return the raw JPEG bytes."""
    response = requests.get(
        CAMERA_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.content


def _loop():
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            frame = fetch_frame()
            (FRAMES_DIR / "latest.jpg").write_bytes(frame)
            print(f"[{datetime.now().isoformat(timespec='seconds')}] fetched frame ({len(frame)} bytes)")
        except requests.RequestException as exc:
            print(f"[{datetime.now().isoformat(timespec='seconds')}] fetch failed: {exc}")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    _loop()

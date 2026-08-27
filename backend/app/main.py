"""M3: the API service.

A background task polls the camera on a loop and writes counts to SQLite;
the HTTP endpoints just read what that loop has already stored. Keeping
the two separate means a page refresh never triggers a model run — the
frontend stays fast no matter how many people load it.

Run with:  uvicorn app.main:app --reload
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app import storage
from app.capture import fetch_frame
from app.config import (
    CORS_ORIGINS,
    ENABLE_FRAME_ENDPOINT,
    POLL_INTERVAL_SECONDS,
    crowd_level,
    is_open,
)
from app.detector import PersonCounter

# The most recent annotated frame, kept in memory so /api/frame can serve
# it without touching disk. Only ever holds one image.
latest_annotated: Optional[bytes] = None

counter: Optional[PersonCounter] = None


def _fetch_and_count() -> Tuple[int, bytes]:
    """Blocking work: HTTP request + model inference."""
    frame = fetch_frame()
    return counter.count(frame)


async def poll_loop() -> None:
    while True:
        try:
            if not is_open():
                # Closed — skip the download and inference entirely rather
                # than burning CPU on an empty room all night.
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            # Both the download and the inference block the thread, so run
            # them in a worker thread — otherwise they'd freeze the whole
            # server (and every in-flight request) for ~half a second.
            people, annotated = await asyncio.to_thread(_fetch_and_count)

            global latest_annotated
            latest_annotated = annotated
            storage.insert_reading(people)

            print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {people} people")
        except Exception as exc:
            # A transient network blip shouldn't kill the loop for good.
            print(f"poll failed: {exc}")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global counter
    storage.init_db()
    counter = PersonCounter()  # load the model once, at startup

    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()


app = FastAPI(title="UF Gym Crowd Tracker", lifespan=lifespan)

# The React dev server runs on a different port, which the browser treats
# as a different origin and blocks by default. This allows it through.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/current")
def current():
    reading = storage.get_latest()
    if reading is None:
        raise HTTPException(status_code=503, detail="no reading yet — the first poll is still running")
    return {
        "people": reading["people"],
        "level": crowd_level(reading["people"]),
        "recorded": reading["recorded"],
    }


@app.get("/api/history")
def history(hours: int = 24):
    return {"hours": hours, "readings": storage.get_history(hours)}


if ENABLE_FRAME_ENDPOINT:
    # Local-only by default. Publishing annotated photos of identifiable
    # people is a different proposition from publishing a headcount, so
    # the deployed service leaves this off (ENABLE_FRAME_ENDPOINT=false).
    @app.get("/api/frame")
    def frame():
        """The latest annotated frame — for eyeballing detection quality."""
        if latest_annotated is None:
            raise HTTPException(status_code=503, detail="no frame yet")
        return Response(content=latest_annotated, media_type="image/jpeg")


# Serve the built React app if it's present, so production runs as a
# single process with no separate web server and no cross-origin setup.
# Mounted last so it never shadows the /api routes above.
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

# UF Gym Crowd Tracker

Live occupancy tracker for the SRFC (Student) Weight Room at UF, built on the
public rec-sports camera feed. A background job pulls a frame every ~12s, counts
people with a pretrained YOLO model, stores the count in SQLite, and a React page
shows the current number plus a 24-hour trend.

Camera endpoint: `https://recsports.ufl.edu/cam/cam8.jpg` (public, no auth).

Deployed free on GitHub Actions + Pages — see [deploy/README.md](deploy/README.md).

## Setup

Backend:

```
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

Frontend:

```
cd frontend
npm install
```

## Running

Two terminals.

Backend (from `backend/`, venv active):

```
uvicorn app.main:app --reload
```

Frontend (from `frontend/`):

```
npm run dev
```

Then open http://localhost:5173. API docs are at http://127.0.0.1:8000/docs.

## API

| Endpoint | Returns |
| --- | --- |
| `GET /api/current` | Latest count, crowd level, timestamp |
| `GET /api/history?hours=24` | Readings over the given window |
| `GET /api/frame` | Latest frame with detection boxes drawn |

## How the counting works

`app/detector.py` runs YOLOv8s over the full 1920px-wide frame and counts
`person` detections.

Two settings matter a lot, and both were found by testing against real frames:

- **`INFERENCE_SIZE = 1920`.** YOLO resizes every image to a fixed size first.
  The default 640 squashed the frame to a third of its width, shrinking people
  in the back of the room to ~15px tall — it found 7 of ~26. Running at full
  width found 22.
- **`MODEL_NAME = "yolov8s.pt"`.** The larger model picks up several more of the
  partly-occluded cases than `yolov8n` for ~0.4s per frame on CPU.

Expect the count to run a few under a careful human count. People fully hidden
behind machines can't be recovered from one camera, which is fine for a
"how busy is it" signal.

### Exclusion zones

`EXCLUSION_ZONES` in `app/config.py` masks regions that aren't real gym floor —
mirrors that reflect lifters (double-counting them) and windows into other rooms.
A detection is dropped when its box center falls in a zone.

Currently empty. To set them up: run `python -m app.detector`, open
`frames/grid.jpg` to read coordinates off the labeled grid, add
`(x1, y1, x2, y2)` tuples to the list, then re-run and check
`frames/annotated.jpg` — green boxes are counted, red were rejected by a zone,
orange outlines are the zones.

### Crowd level thresholds

`CROWD_LEVELS` in `app/config.py` are rough guesses (the room has no published
capacity). Recalibrate once you have a week of data: look at the busiest evening
peak in `/api/history` and set `Packed` near it.

## Layout

```
backend/
  app/
    config.py     camera URL, poll interval, zones, crowd thresholds
    capture.py    fetch_frame() — GET the camera JPEG
    detector.py   PersonCounter — YOLO inference + zone filtering
    storage.py    SQLite readings table (local server mode)
    main.py       FastAPI app + background poll loop (local server mode)
    collect.py    one-shot reading -> data/*.json (deployed mode)
  frames/         debug images (gitignored)
data/
  recent.json         last 48h + current reading — what the site loads
  history/YYYY-MM.json  permanent archive
frontend/
  src/
    api.js            reads data/*.json when deployed, the API locally
    usePolling.js     hook: fetch on an interval, with cleanup
    App.jsx
    components/
.github/workflows/
  collect.yml     cron job that takes readings
  pages.yml       builds and deploys the site
```

There are two ways to run the same thing. **Locally**, `main.py` keeps a
process alive polling every 12s and stores to SQLite. **Deployed**,
`collect.py` runs as a scheduled CI job, takes one reading, and commits it —
which is what makes free hosting possible.

Counts are stored, frames are not — each frame is ~450KB, so keeping them all
would cost gigabytes a day for no benefit.

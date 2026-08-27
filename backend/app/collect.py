"""One-shot collector for the GitHub Actions deployment.

The server version (main.py) keeps a process alive and polls in a loop.
That needs an always-on machine. This does exactly one reading and exits,
so a scheduled CI job can run it for free — the repo itself becomes the
database, and the frontend reads the JSON files straight from GitHub.

Run: python -m app.collect
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.capture import fetch_frame
from app.config import crowd_level, is_open
from app.detector import PersonCounter

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# What the frontend loads. Kept small so the page stays fast.
RECENT_PATH = DATA_DIR / "recent.json"
RECENT_WINDOW = timedelta(hours=48)

# Everything ever recorded, one file per month, for later analysis
# ("typical crowd by hour and weekday").
ARCHIVE_DIR = DATA_DIR / "history"


def _load(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        # A half-written file shouldn't wedge every future run.
        return fallback


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1) + "\n")


def main() -> int:
    now = datetime.now(timezone.utc)

    if not is_open():
        print("gym is closed — skipping")
        return 0

    people, _ = PersonCounter().count(fetch_frame())
    reading = {"recorded": now.isoformat(timespec="seconds"), "people": people}
    print(f"{people} people at {reading['recorded']}")

    # Rolling window the page reads.
    recent = _load(RECENT_PATH, {"readings": []})
    readings = recent.get("readings", [])
    readings.append(reading)
    cutoff = (now - RECENT_WINDOW).isoformat()
    readings = [r for r in readings if r["recorded"] >= cutoff]

    _write(
        RECENT_PATH,
        {
            "current": {**reading, "level": crowd_level(people)},
            "readings": readings,
        },
    )

    # Permanent archive, one file per month.
    archive_path = ARCHIVE_DIR / f"{now:%Y-%m}.json"
    archive = _load(archive_path, [])
    archive.append(reading)
    _write(archive_path, archive)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

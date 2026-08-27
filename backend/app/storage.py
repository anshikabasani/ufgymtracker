"""M3: persist counts to SQLite.

One row per poll. We store only the number, not the image — frames are
450 KB each, so keeping them all would eat gigabytes per day for no gain.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "readings.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    # Lets us read columns by name (row["count"]) instead of by index.
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded  TEXT    NOT NULL,
                people    INTEGER NOT NULL
            )
            """
        )
        # History queries always filter on time, so index it.
        connection.execute("CREATE INDEX IF NOT EXISTS idx_readings_recorded ON readings(recorded)")


def insert_reading(people: int, recorded: Optional[datetime] = None) -> None:
    recorded = recorded or datetime.now(timezone.utc)
    with _connect() as connection:
        connection.execute(
            "INSERT INTO readings (recorded, people) VALUES (?, ?)",
            (recorded.isoformat(), people),
        )


def get_latest() -> Optional[dict]:
    with _connect() as connection:
        row = connection.execute(
            "SELECT recorded, people FROM readings ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def get_history(hours: int = 24) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT recorded, people FROM readings WHERE recorded >= ? ORDER BY recorded",
            (since,),
        ).fetchall()
    return [dict(row) for row in rows]

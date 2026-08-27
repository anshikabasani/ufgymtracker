"""Configuration. Anything that differs between your laptop and the
server is read from an environment variable, with the dev-friendly value
as the default — so local runs need no setup, and the server overrides
what it needs in the systemd unit.
"""

import os
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

CAMERA_URL = "https://recsports.ufl.edu/cam/cam8.jpg"

# 12s is nice for development. In production it's ~7000 requests/day at
# UF's server for data that barely moves minute to minute — the systemd
# unit sets this to 60.
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "12"))

REQUEST_TIMEOUT_SECONDS = 10

USER_AGENT = "uf-gym-tracker/0.1 (personal learning project)"

# Serving annotated photos of identifiable people publicly is a different
# thing from publishing a count, so this stays off unless explicitly enabled.
ENABLE_FRAME_ENDPOINT = os.getenv("ENABLE_FRAME_ENDPOINT", "true").lower() == "true"

# In production the API and the page are served from the same origin, so
# no cross-origin allowance is needed at all.
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o]

# --- Gym hours -------------------------------------------------------
# No point running a model against a dark empty room all night. These are
# approximate SRFC hours; adjust to match reality.

TIMEZONE = ZoneInfo("America/New_York")
OPEN_HOUR = int(os.getenv("OPEN_HOUR", "6"))    # 6am
CLOSE_HOUR = int(os.getenv("CLOSE_HOUR", "24"))  # midnight


def is_open(now: Optional[datetime] = None) -> bool:
    now = now or datetime.now(TIMEZONE)
    return OPEN_HOUR <= now.hour < CLOSE_HOUR


# --- Detection -------------------------------------------------------

# Regions of the 1920x1080 frame that aren't real gym floor — mirrors that
# reflect lifters (double-counting them) and windows into other rooms.
# A detection is dropped when the center of its box falls inside a zone.
# Coordinates are (x1, y1, x2, y2) in pixels; use frames/grid.jpg to read
# them off, and frames/annotated.jpg to check what you've masked.
EXCLUSION_ZONES = [
    # ("mirror on the back wall", etc.) — fill in once identified.
]

# Rough starting guesses — the room has no published capacity, and the
# detector undercounts somewhat, so these are thresholds on *detected*
# people, not true occupancy. Recalibrate after a week of real data:
# look at the busiest evening peak and set PACKED near it.
CROWD_LEVELS = [
    (10, "Quiet"),
    (20, "Moderate"),
    (30, "Busy"),
]
CROWD_LEVEL_MAX = "Packed"


def crowd_level(people: int) -> str:
    for threshold, label in CROWD_LEVELS:
        if people < threshold:
            return label
    return CROWD_LEVEL_MAX

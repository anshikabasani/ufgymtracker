"""M2: count people in a frame using a pretrained YOLO model.

Run directly (`python -m app.detector`) to test against a live frame:
it saves an annotated copy to backend/frames/annotated.jpg so you can
open it and check the boxes against the real people in the picture.
"""

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from ultralytics import YOLO

from app.config import EXCLUSION_ZONES

# COCO class 0 is "person" — the only class we care about.
PERSON_CLASS_ID = 0

# Detections below this confidence are ignored. Lower = catches more
# partially-hidden people, but also more false positives. Tune in M2.
CONFIDENCE_THRESHOLD = 0.25

# The frame is 1920x1080 and YOLO downscales to this size before running.
# The default (640) shrinks each person to a few pixels and undercounts
# badly (7 of ~26). Running at full width is the single biggest accuracy
# win here, and still only costs ~0.4s per frame on CPU.
INFERENCE_SIZE = 1920

# yolov8s over yolov8n: noticeably better on the small, partly-occluded
# people toward the back of the room, for a still-negligible cost.
MODEL_NAME = "yolov8s.pt"

FRAMES_DIR = Path(__file__).resolve().parent.parent / "frames"


def _in_excluded_zone(box: tuple[float, float, float, float]) -> bool:
    """True if the center of this box sits inside a masked-off region."""
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    return any(zx1 <= cx <= zx2 and zy1 <= cy <= zy2 for zx1, zy1, zx2, zy2 in EXCLUSION_ZONES)


def _draw(image: Image.Image, kept, dropped) -> Image.Image:
    """Green boxes = counted, red = rejected as mirror/window, so you can
    see at a glance whether the zones are masking the right things."""
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    for zone in EXCLUSION_ZONES:
        draw.rectangle(zone, outline=(255, 160, 0), width=3)
    for box in dropped:
        draw.rectangle(box, outline=(255, 40, 40), width=3)
    for box in kept:
        draw.rectangle(box, outline=(40, 220, 60), width=3)
    return canvas


class PersonCounter:
    """Loads the YOLO model once, then counts people in frames."""

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        confidence: float = CONFIDENCE_THRESHOLD,
        inference_size: int = INFERENCE_SIZE,
    ):
        # Downloads the weights on first use (~22 MB), then caches them.
        self.model = YOLO(model_name)
        self.confidence = confidence
        self.inference_size = inference_size

    def count(self, image_bytes: bytes) -> tuple[int, bytes]:
        """Return (number of people, annotated JPEG bytes)."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        results = self.model.predict(
            source=np.array(image),
            classes=[PERSON_CLASS_ID],
            conf=self.confidence,
            imgsz=self.inference_size,
            verbose=False,
        )
        result = results[0]

        boxes = [tuple(box) for box in result.boxes.xyxy.tolist()]
        kept = [box for box in boxes if not _in_excluded_zone(box)]

        annotated = _draw(image, kept, dropped=[b for b in boxes if b not in kept])
        buffer = io.BytesIO()
        annotated.save(buffer, format="JPEG", quality=85)

        return len(kept), buffer.getvalue()


if __name__ == "__main__":
    from app.capture import fetch_frame

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    counter = PersonCounter()

    frame = fetch_frame()
    people, annotated = counter.count(frame)

    output_path = FRAMES_DIR / "annotated.jpg"
    output_path.write_bytes(annotated)
    print(f"counted {people} people — annotated frame saved to {output_path}")
    print("green = counted, red = rejected by a zone, orange = the zones themselves")

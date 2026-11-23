"""Paths and settings, read from the environment (see .env.example)."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = Path(os.environ.get("MODEL_DIR", BACKEND_DIR / "models"))
# The web page's files. Locally: <repo>/frontend; in Docker it is copied to /srv/frontend.
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", BACKEND_DIR.parent / "frontend"))

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}


def max_upload_bytes() -> int:
    """The biggest photo accepted (MAX_UPLOAD_MB in the environment, default 5 MB)."""
    try:
        megabytes = float(os.environ.get("MAX_UPLOAD_MB", "5"))
    except ValueError:
        megabytes = 5
    return int(min(max(megabytes, 1), 20) * 1024 * 1024)


def min_confidence() -> float:
    """Below this, the answer is "neither" (MIN_CONFIDENCE in the environment, default 0.5)."""
    try:
        value = float(os.environ.get("MIN_CONFIDENCE", "0.5"))
    except ValueError:
        return 0.5
    return min(max(value, 0.05), 0.95)

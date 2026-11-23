"""Run with: pytest

Real-photo checks use any files in backend/tests/photos/ (or the folder in TEST_PHOTOS) named like
cat*.jpg or dog*.png; photos aren't included in the repository, and without them those checks
are skipped.
"""

import io
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

PHOTOS = Path(os.environ.get("TEST_PHOTOS", Path(__file__).parent / "photos"))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs the start-up, which loads the model
        yield c


def png(color=(120, 120, 120), size=(300, 300)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_page(client):
    r = client.get("/")
    assert r.status_code == 200 and "Identify The Image" in r.text


def test_answer_shape(client):
    r = client.post("/api/predict", files={"photo": ("grey.png", png(), "image/png")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] in {"cat", "dog", "neither"}
    assert set(body) == {"label", "confidence", "cat", "dog", "best_guess"}
    assert 0 <= body["cat"] <= 1 and 0 <= body["dog"] <= 1


def test_plain_colour_is_neither(client):
    r = client.post("/api/predict", files={"photo": ("grey.png", png(), "image/png")})
    assert r.json()["label"] == "neither"


def test_wrong_type(client):
    r = client.post("/api/predict", files={"photo": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_not_really_an_image(client):
    r = client.post("/api/predict", files={"photo": ("fake.jpg", b"not a picture", "image/jpeg")})
    assert r.status_code == 422


def test_empty_file(client):
    r = client.post("/api/predict", files={"photo": ("empty.png", b"", "image/png")})
    assert r.status_code == 400


def test_too_big(client, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    r = client.post("/api/predict", files={"photo": ("big.png", b"x" * (1024 * 1024 + 10), "image/png")})
    assert r.status_code == 413


@pytest.mark.parametrize(
    "path",
    sorted(p for p in PHOTOS.glob("*") if p.name.lower().startswith(("cat", "dog"))) or [None],
)
def test_real_photos(client, path):
    if path is None:
        pytest.skip("no photos in backend/tests/photos/")
    kind = "cat" if path.name.lower().startswith("cat") else "dog"
    mime = {".png": "image/png", ".webp": "image/webp"}.get(path.suffix.lower(), "image/jpeg")
    r = client.post("/api/predict", files={"photo": (path.name, path.read_bytes(), mime)})
    assert r.json()["label"] == kind, r.json()

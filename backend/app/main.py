"""Identify The Image: upload a photo, learn whether it shows a cat or a dog.

GET  /             the web page (from the frontend folder)
GET  /assets/...   the page's CSS and JavaScript
GET  /health       "ok" (for the server's health check)
POST /api/predict  a photo in, {"label": "cat" | "dog" | "neither", ...} out
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import FRONTEND_DIR
from .services.classifier import warm_up


@asynccontextmanager
async def lifespan(_: FastAPI):
    warm_up()
    yield


app = FastAPI(title="Identify The Image", lifespan=lifespan, docs_url=None, redoc_url=None)
app.include_router(router)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")

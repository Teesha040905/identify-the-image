"""The JSON API: health check and prediction."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..config import ALLOWED_TYPES, max_upload_bytes
from ..services.classifier import NotAnImage, classify

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/predict")
async def predict(photo: UploadFile = File(...)) -> dict[str, object]:
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Please upload a photo: JPG, PNG, WebP, GIF or BMP.")
    limit = max_upload_bytes()
    data = await photo.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"That photo is bigger than {limit // (1024 * 1024)} MB.")
    if not data:
        raise HTTPException(400, "The file is empty.")
    try:
        result = await run_in_threadpool(classify, data)
    except NotAnImage as exc:
        raise HTTPException(422, str(exc)) from exc
    return result.as_dict()

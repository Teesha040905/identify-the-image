"""Cat or dog? A small pre-trained image model (MobileNetV2, ImageNet, ONNX) decides.

The model knows 1000 kinds of things. 118 of them are dog breeds (numbers 151-268) and five are
house cats (281-285). The chance of "dog" is the sum over the dog breeds, of "cat" over the cats;
when neither is likely enough the answer is "neither" (a car, a person, a landscape...).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps, UnidentifiedImageError

from ..config import MODEL_DIR, min_confidence

DOGS = range(151, 269)
CATS = range(281, 286)
# ImageNet's average colour and spread: the model was trained on pictures scaled this way.
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class NotAnImage(ValueError):
    """The upload isn't a picture this app can read."""


@dataclass(frozen=True)
class Prediction:
    label: str  # "cat", "dog" or "neither"
    confidence: float  # 0..1: how sure, for the label given
    cat: float
    dog: float
    best_guess: str  # the single most likely of the 1000 kinds, e.g. "golden retriever"

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "cat": round(self.cat, 4),
            "dog": round(self.dog, 4),
            "best_guess": self.best_guess,
        }


@lru_cache(maxsize=1)
def _model() -> tuple[ort.InferenceSession, list[str]]:
    session = ort.InferenceSession(str(MODEL_DIR / "mobilenetv2-12.onnx"), providers=["CPUExecutionProvider"])
    labels = (MODEL_DIR / "imagenet_classes.txt").read_text(encoding="utf-8").splitlines()
    return session, labels


def warm_up() -> None:
    """Loads the model once at start-up, so the first visitor doesn't wait for it."""
    _model()


def _prepare(data: bytes) -> np.ndarray:
    try:
        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image).convert("RGB")  # phone photos: apply the rotation
    except (UnidentifiedImageError, OSError) as exc:
        raise NotAnImage("That file isn't an image this app can read (try JPG, PNG or WebP).") from exc
    # Shorter side to 256, then the middle 224x224: what the model saw while training.
    width, height = image.size
    scale = 256 / min(width, height)
    image = image.resize((max(224, round(width * scale)), max(224, round(height * scale))), Image.BILINEAR)
    left = (image.width - 224) // 2
    top = (image.height - 224) // 2
    image = image.crop((left, top, left + 224, top + 224))
    pixels = (np.asarray(image, dtype=np.float32) / 255.0 - MEAN) / STD
    return pixels.transpose(2, 0, 1)[np.newaxis, ...]  # 1 x 3 x 224 x 224


def classify(data: bytes) -> Prediction:
    session, labels = _model()
    logits = session.run(None, {session.get_inputs()[0].name: _prepare(data)})[0][0]
    exp = np.exp(logits - logits.max())
    probs = exp / exp.sum()
    dog = float(probs[DOGS.start : DOGS.stop].sum())
    cat = float(probs[CATS.start : CATS.stop].sum())
    best = labels[int(probs.argmax())]
    threshold = min_confidence()
    if max(cat, dog) < threshold:
        return Prediction("neither", 1 - max(cat, dog), cat, dog, best)
    label = "dog" if dog >= cat else "cat"
    return Prediction(label, max(cat, dog), cat, dog, best)

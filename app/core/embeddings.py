"""Mô hình nhúng. Đổi mô hình = đổi EMBED_MODEL_NAME trong config.py."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from config import EMBED_DEVICE, EMBED_MODEL_NAME, EMBED_NORMALIZE


@lru_cache(maxsize=1)
def get_device() -> str:
    if EMBED_DEVICE != "auto":
        return EMBED_DEVICE
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL_NAME, device=get_device())


def encode(texts, batch_size: int = 32) -> np.ndarray:
    single = isinstance(texts, str)
    vecs = get_model().encode(
        [texts] if single else list(texts),
        batch_size=batch_size,
        device=get_device(),
        normalize_embeddings=EMBED_NORMALIZE,
        show_progress_bar=False,
    )
    vecs = np.asarray(vecs, dtype=np.float32)
    return vecs[0] if single else vecs


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)

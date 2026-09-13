"""Semantic Router: phân loại câu hỏi bằng cosine similarity với trọng tâm từng cụm."""

from functools import lru_cache

import numpy as np

from core import embeddings
from core.anchors import INTENT_ANCHORS


@lru_cache(maxsize=1)
def get_centroids() -> dict:
    return {intent: embeddings.centroid(texts) for intent, texts in INTENT_ANCHORS.items()}


def classify(text: str):
    """Trả về (intent, score, query_embedding)."""
    q_emb = embeddings.encode(text)
    scores = {
        intent: embeddings.cosine_sim(q_emb, c)
        for intent, c in get_centroids().items()
    }
    best_intent = max(scores, key=scores.get)
    return best_intent, round(scores[best_intent], 2), q_emb

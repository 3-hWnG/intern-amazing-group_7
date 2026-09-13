"""Cross-encoder xếp hạng lại. Tắt được bằng USE_RERANKER trong config.py.

Nhắm thẳng vào khoảng cách R@5 0.804 - R@1 0.527 của baseline v0: tài liệu
đúng thường ĐÃ nằm trong top-5, chỉ bị xếp sai thứ tự.
"""

from __future__ import annotations

from functools import lru_cache

from config import (RERANKER_BATCH_SIZE, RERANKER_DEVICE, RERANKER_MAX_LENGTH,
                    RERANKER_MODEL_NAME)


@lru_cache(maxsize=1)
def get_device() -> str:
    if RERANKER_DEVICE != "auto":
        return RERANKER_DEVICE
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import CrossEncoder
    model = CrossEncoder(
        RERANKER_MODEL_NAME,
        device=get_device(),
        max_length=RERANKER_MAX_LENGTH,
    )
    print(f"[reranker] {RERANKER_MODEL_NAME} trên {get_device()}")
    return model


# lru_cache KHÔNG nhớ ngoại lệ: nếu nạp model lỗi thì mỗi truy vấn lại nạp lại
# 2.2GB. Cờ dưới đây đảm bảo chỉ thử đúng MỘT lần cho cả tiến trình.
_AVAILABLE: bool | None = None


def is_available() -> bool:
    global _AVAILABLE
    if _AVAILABLE is not None:
        return _AVAILABLE
    try:
        get_model()
        _AVAILABLE = True
    except Exception as exc:
        print(f"[reranker] KHÔNG dùng được, chạy tiếp không có xếp hạng lại.\n"
              f"           Lý do: {exc}\n"
              f"           Thường là thiếu thư viện: pip install sentencepiece protobuf")
        _AVAILABLE = False
    return _AVAILABLE


def _sigmoid(x: float) -> float:
    import math
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def score(query: str, passages: list[str]) -> list[float]:
    if not passages:
        return []
    raw = get_model().predict([(query, p) for p in passages],
                              batch_size=RERANKER_BATCH_SIZE,
                              show_progress_bar=False)
    return [_sigmoid(float(r)) if not 0.0 <= float(r) <= 1.0 else float(r) for r in raw]

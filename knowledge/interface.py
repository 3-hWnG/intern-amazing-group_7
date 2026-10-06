"""Stub giao diện Box 5B/6B (RAG, import tài liệu). KHÔNG được import/gọi trong đường chạy; xem README.md.
ponytail: chỉ khai báo kiểu; bản cài đặt thật (chỉ mục, import PDF/DOC) làm sau."""
from __future__ import annotations

from typing import Literal, Protocol, TypedDict


class Evidence(TypedDict):
    source: str                         # nhãn nguồn người đọc được
    text: str                           # đoạn nguyên văn
    score: float                        # 0..1
    origin: Literal["direct", "rag"]


class KnowledgeSource(Protocol):
    def search(self, query: str, k: int = 5) -> list[Evidence]:
        """Trả tối đa k đoạn liên quan, điểm giảm dần; kho rỗng/lỗi -> []."""
        ...

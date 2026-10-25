"""Phase 2 — retrieval cho Planner. Không LLM. Xem PLAN_SYSTEM3.md.

    understand(conn, text) -> Query   tách tên thủ tục / field / tỉnh khỏi câu
    Index(conn).rank(query)  -> [Hit] xếp hạng IDF có tính dấu, kèm cờ phạm vi
    resolve(...)             -> Result  (ứng viên + quyết định in-scope)
"""
from .query import Query, understand, split_segments
from .rank import Hit, Index, Result, resolve

__all__ = ["Query", "understand", "split_segments", "Hit", "Index", "Result", "resolve"]

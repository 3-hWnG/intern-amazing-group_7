"""Bộ CHỌN HỆ THỐNG — một cửa vào duy nhất cho mọi lượt hỏi.

Từ V10.3 có HAI hệ thống trả lời chạy song song, người dùng chuyển qua lại bằng
nút "Web search" trên giao diện:

    Hệ thống 1  websearch   core/system_websearch.py   tra web .gov.vn qua MCP
    Hệ thống 2  retrieval   core/system_retrieval.py   CSDL thủ tục nội bộ (MẶC ĐỊNH)

Tệp này KHÔNG chứa nghiệp vụ — chỉ đọc `inp.system` rồi gọi đúng module. Hợp
đồng chung (`TurnInput` / `TurnResult`) nằm ở `core/turn.py` và được xuất lại ở
đây để mã cũ (`api/chat_routes.py`, `Evaluation/evaluate.py`) không phải sửa:

    orchestrator.run_turn(orchestrator.TurnInput(question=...))   # vẫn chạy

Thêm hệ thống thứ ba: viết `core/system_<tên>.py` có `run_turn(inp, status)`
rồi thêm một dòng vào `SYSTEMS` bên dưới. Không đụng chỗ nào khác.
"""

from __future__ import annotations

from typing import Callable

from config import DEFAULT_SYSTEM, SYSTEM_RETRIEVAL, SYSTEM_WEBSEARCH
from core import system_retrieval, system_websearch
from core.turn import TurnInput, TurnResult          # noqa: F401 — xuất lại, mã cũ import từ đây

# tên hệ thống -> module điều phối của hệ thống đó
SYSTEMS: dict[str, Callable[..., TurnResult]] = {
    SYSTEM_WEBSEARCH: system_websearch.run_turn,
    SYSTEM_RETRIEVAL: system_retrieval.run_turn,
}


def normalize_system(name: str | None) -> str:
    """Tên hệ thống hợp lệ, sai/thiếu thì về mặc định — không bao giờ ném lỗi."""
    name = (name or "").strip().lower()
    return name if name in SYSTEMS else DEFAULT_SYSTEM


def run_turn(inp: TurnInput, status: Callable[[str], None] = lambda _: None) -> TurnResult:
    system = normalize_system(inp.system)
    inp.system = system
    return SYSTEMS[system](inp, status)

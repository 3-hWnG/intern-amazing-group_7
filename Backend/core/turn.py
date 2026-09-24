"""Hợp đồng chung của MỘT LƯỢT hỏi — dùng chung cho CẢ HAI hệ thống trả lời.

Tách riêng khỏi `orchestrator.py` để `system_websearch.py` và
`system_retrieval.py` cùng import được mà không vòng tròn:

    turn.py  <-  system_websearch.py  ┐
             <-  system_retrieval.py  ├-> orchestrator.py (chọn hệ thống)
                                      ┘

Hệ thống nào cũng nhận `TurnInput` và trả `TurnResult`. Thêm hệ thống thứ ba
về sau = thêm một module có hàm `run_turn(inp, status) -> TurnResult` rồi đăng
ký vào `orchestrator.SYSTEMS`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config import DEFAULT_SYSTEM


# Chế độ của MỘT lượt ở Hệ thống 2 (Proposal slide 3):
#   chat      tin nhắn thường. Chưa có bảng -> LLM 2 trò chuyện + gợi ý 🎯;
#             đã có bảng -> chăm sóc khách hàng trên bảng đó.
#   exact     nút 🎯 Tìm chính xác -> tra CSDL -> MCQ -> bảng. Mỗi ô chat chỉ
#             tra thành công MỘT lần; lần 2 -> mời mở ô chat mới hoặc huỷ.
#   resubmit  ô "Tra lại" dưới bảng (báo sai ngữ nghĩa) -> xoá bảng cũ, tra lại
#             như mới trong CÙNG ô chat. Không tính là lần tra thứ hai.
MODE_CHAT, MODE_EXACT, MODE_RESUBMIT = "chat", "exact", "resubmit"
MODES = (MODE_CHAT, MODE_EXACT, MODE_RESUBMIT)


@dataclass
class TurnInput:
    question: str
    history: list[dict] = field(default_factory=list)   # {"role","content","kind"}
    summary: str = ""
    profile: dict = field(default_factory=dict)
    conversation_id: int | None = None
    # Chủ cuộc trò chuyện. Hệ thống 2 cần để đọc/ghi trí nhớ lựa chọn MCQ
    # (`user_mcq_memory`) — thứ duy nhất trong một lượt gắn với NGƯỜI, không
    # phải với cuộc trò chuyện. None = chạy ngoài web (evaluate.py, CLI).
    user_id: int | None = None
    direct_search: bool = False
    # "websearch" = Hệ thống 1 (tra web qua MCP) · "retrieval" = Hệ thống 2 (CSDL nội bộ)
    system: str = DEFAULT_SYSTEM
    # Chỉ Hệ thống 2 dùng. Xem MODES ở trên.
    mode: str = "chat"


@dataclass
class TurnResult:
    kind: str = "answer"        # answer | not_in_sources | clarify | chitchat | out_of_scope | no_evidence | unavailable | error
    text: str = ""
    verdict: str = ""           # PASS | FAIL | "" (không kiểm chứng)
    intent: dict = field(default_factory=dict)
    evidence: dict | None = None
    sources: list[dict] = field(default_factory=list)
    verification: dict = field(default_factory=dict)
    profile_update: dict = field(default_factory=dict)
    timings: dict = field(default_factory=dict)
    choices: list[str] = field(default_factory=list)
    # Hệ thống nào đã trả lời — giao diện gắn nhãn, Evaluation đối chiếu.
    system: str = ""
    # Bảng thủ tục do CODE dựng (Hệ thống 2), không qua LLM. None với Hệ thống 1.
    table: dict | None = None

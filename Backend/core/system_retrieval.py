"""HỆ THỐNG 2 — RETRIEVAL (CSDL thủ tục nội bộ). **CHƯA XÂY — khung sẵn sàng.**

Hệ thống này chạy SONG SONG với Hệ thống 1 (`system_websearch.py`): cùng nhận
`TurnInput`, cùng trả `TurnResult`, người dùng chọn bằng nút "Web search" trên
giao diện. Tệp này đã có đủ khung để nhóm cắm phần cào dữ liệu + CSDL vào mà
không phải sửa chỗ nào khác trong ứng dụng.

Pipeline theo đúng Proposal (Project Nhóm 7 — Plan tuần này):

    [ User Input ]  "t người bình định muốn dk kết hôn"
          │
          ▼
    [ LLM 1: Router & Extractor ]  ──> {"primary_keyword": "Đăng ký kết hôn",
          │                             "entities": ["Bình Định"]}
          │  CHỈ dùng LLM cho semantic understanding — không sinh câu trả lời
          ▼
    [ Truy vấn CSDL (MCP) ]  FTS / fuzzy trên CSDL thủ tục -> primary key
          │                  BỎ QUA bước sinh văn bản của LLM
          ▼
    [ Dựng bảng bằng CODE ]  giải thích · chi phí · checklist · tệp · meta
          │                  (zero hallucination — số liệu đi thẳng từ bảng)
          ▼
    [ LLM 2: Chăm sóc khách hàng ]  đọc lịch sử + bảng, chỉ trả lời trong phạm vi
                                    phát hiện `newProcedure` -> mời sang ô chat mới

BỐN CHỖ CẦN CẮM VÀO (mỗi hàm là một mốc bàn giao rõ ràng):

    extract_keys()   LLM 1 — câu hỏi -> {primary_keyword, entities}
    lookup()         CSDL  — khoá -> bản ghi thủ tục (primary key)
    build_table()    CODE  — bản ghi -> bảng hiển thị (không qua LLM)
    follow_up()      LLM 2 — chăm sóc khách hàng trên bảng đã trả

Khi cả bốn hàm chạy được: đặt `RETRIEVAL_ENABLED=true` trong `.env` (và đổi
`DEFAULT_SYSTEM=retrieval` nếu muốn Hệ thống 2 làm mặc định như Proposal).
Chừng nào chưa xong, mỗi hàm ném `NotImplementedError` và `run_turn` chuyển
thành lời nhắn lịch sự mời người dùng bật nút Web search — KHÔNG bao giờ để
người dân nhận câu trả lời bịa.
"""

from __future__ import annotations

import time
from typing import Callable

import developer_mode
from config import RETRIEVAL_ENABLED, SYSTEM_RETRIEVAL
from core.turn import TurnInput, TurnResult

# Lời nhắn khi Hệ thống 2 chưa sẵn sàng. Nói thật + chỉ đúng nút cần bấm.
UNAVAILABLE_TEXT = (
    "Hệ thống tra cứu từ cơ sở dữ liệu nội bộ (Hệ thống 2) đang được xây dựng "
    "nên chưa trả lời được câu hỏi này.\n\n"
    "Bạn bấm nút **🌐 Web search** ở khung nhập bên dưới để chuyển sang tra cứu "
    "trực tiếp từ các trang .gov.vn — hệ thống sẽ mở một cuộc trò chuyện mới cho bạn."
)


# ---------------------------------------------------------------------------
# 1. LLM 1 — Router & Extractor
# ---------------------------------------------------------------------------
def extract_keys(question: str, history: list[dict], profile: dict) -> dict:
    """Câu hỏi của người dân -> khoá tra cứu. CHƯA LÀM.

    Ra: {"primary_keyword": "Đăng ký kết hôn", "entities": ["Bình Định"]}

    Dùng lại được ngay từ Hệ thống 1: `core.intent.analyze()` đã cho ý định +
    câu hỏi độc lập + tỉnh/xã + truy vấn tìm kiếm (Proposal, "Thêm 2: cách
    route của hệ thống 2 chắc copy của hệ thống 1 được"). Việc còn lại là ánh
    xạ kết quả đó sang đúng từ vựng của CSDL thủ tục.
    """
    raise NotImplementedError("Hệ thống 2: LLM 1 (router & extractor) chưa xây.")


# ---------------------------------------------------------------------------
# 2. Truy vấn CSDL — KHÔNG qua LLM
# ---------------------------------------------------------------------------
def lookup(keys: dict) -> dict | None:
    """Khoá -> đúng MỘT bản ghi thủ tục (hoặc None nếu không khớp). CHƯA LÀM.

    Bản ghi theo schema đã chốt trong Proposal:
        {"proc_id", "name", "domain", "description", "fees": [...],
         "checklist": [...], "files": [{"name", "url"}], "meta": <ngày>}

    Chỗ cắm: gọi qua `core.mcp_client` để CSDL cũng là một MCP target giống
    web search, hoặc truy vấn thẳng nếu CSDL nằm cùng máy. CSDL phải do code
    cào về và cập nhật được bằng code (`content_hash` + status active/archived).
    """
    raise NotImplementedError("Hệ thống 2: truy vấn CSDL thủ tục chưa xây.")


# ---------------------------------------------------------------------------
# 3. Dựng bảng bằng CODE — zero hallucination
# ---------------------------------------------------------------------------
def build_table(record: dict) -> dict:
    """Bản ghi CSDL -> bảng cho giao diện. Không có LLM trong hàm này. CHƯA LÀM.

    Ra đúng các ô Proposal yêu cầu, giao diện chỉ việc vẽ:
        {"explanation", "fees", "checklist": [...], "files": [...],
         "meta": {...}, "outdated": bool}

    `outdated=True` (luật đã hết hiệu lực) -> vẫn trả luật cũ NHƯNG cảnh báo và
    mời người dùng tự bấm Web search. Web search luôn là lựa chọn của người dùng.
    """
    raise NotImplementedError("Hệ thống 2: bộ dựng bảng chưa xây.")


# ---------------------------------------------------------------------------
# 4. LLM 2 — Chăm sóc khách hàng trên bảng đã trả
# ---------------------------------------------------------------------------
def follow_up(question: str, history: list[dict], table: dict) -> str:
    """Hỏi tiếp sau khi đã có bảng: trả lời CHỈ trong phạm vi bảng. CHƯA LÀM.

    Kèm `newProcedure` boundary control: người dùng hỏi sang thủ tục khác thì
    không trả lời bừa mà mời mở ô chat mới (tránh LLM lẫn thông tin hai thủ tục).
    """
    raise NotImplementedError("Hệ thống 2: LLM 2 (chăm sóc khách hàng) chưa xây.")


# ---------------------------------------------------------------------------
# Điều phối một lượt của Hệ thống 2
# ---------------------------------------------------------------------------
def run_turn(inp: TurnInput, status: Callable[[str], None] = lambda _: None) -> TurnResult:
    dev = developer_mode.turn(inp.question, inp.conversation_id)
    res = TurnResult(system=SYSTEM_RETRIEVAL)
    clock = time.time()

    def lap(name: str, since: float) -> int:
        ms = int((time.time() - since) * 1000)
        res.timings[name] = res.timings.get(name, 0) + ms
        return ms

    try:
        if not RETRIEVAL_ENABLED:
            res.kind, res.text = "unavailable", UNAVAILABLE_TEXT
            dev.event("retrieval_disabled", note="RETRIEVAL_ENABLED=false")
            return res

        status("Đang xác định thủ tục bạn cần…")
        t = time.time()
        keys = extract_keys(inp.question, inp.history, inp.profile)
        res.intent = {"intent": "retrieval", "standalone_question": inp.question, **keys}
        dev.event("extract_keys", ms=lap("understand", t), **keys)

        status("Đang tra cứu cơ sở dữ liệu thủ tục…")
        t = time.time()
        record = lookup(keys)
        dev.event("lookup", ms=lap("search", t), found=bool(record),
                  proc_id=(record or {}).get("proc_id", ""))
        if not record:
            # Không có trong CSDL: nói thật, mời bật Web search — không bịa.
            res.kind = "no_evidence"
            res.text = ("Mình chưa tìm thấy thủ tục này trong cơ sở dữ liệu nội bộ.\n\n"
                        "Bạn bấm nút **🌐 Web search** để tra trực tiếp từ các trang .gov.vn.")
            return res

        status("Đang dựng bảng thông tin…")
        t = time.time()
        res.table = build_table(record)
        res.kind = "answer"
        res.text = res.table.get("explanation", "")
        res.sources = res.table.get("sources", [])
        dev.event("build_table", ms=lap("answer", t))
        return res

    except NotImplementedError as exc:
        # Khung đã dựng nhưng phần bên trong chưa có -> báo thật, không trả lời chay.
        res.kind, res.text = "unavailable", UNAVAILABLE_TEXT
        dev.event("not_implemented", note=str(exc))
        return res
    except Exception as exc:                      # noqa: BLE001 — một lượt hỏng không được làm sập app
        res.kind = "error"
        res.text = f"Hệ thống 2 gặp lỗi khi tra cứu cơ sở dữ liệu.\n\nChi tiết: {exc}"
        dev.event("error", note=str(exc))
        return res
    finally:
        res.timings["total"] = int((time.time() - clock) * 1000)
        dev.set(kind=res.kind, verdict=res.verdict, intent=res.intent.get("intent", ""),
                standalone=res.intent.get("standalone_question", ""),
                queries=[], sources=[s.get("url") or s.get("title") for s in res.sources],
                timings=res.timings)
        dev.finish()

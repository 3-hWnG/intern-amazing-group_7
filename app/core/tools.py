"""Công cụ mà mô hình được phép gọi.

Đây là thay đổi kiến trúc cốt lõi của v6. Trước đây `pipeline.build()` QUYẾT
ĐỊNH THAY mô hình: router bẻ sang luồng LUAT thì bắt buộc tra bảng, và câu trả
lời bị giam trong bảng đó. Giờ mô hình tự chọn — hoặc không chọn gì.

Mỗi công cụ là một lớp vỏ MỎNG bọc quanh code đã có và đã đo được:

    search_procedures  -> core/retrieval.retrieve()   (R@1 0.856, không đụng)
    get_procedure      -> domain/records.by_row_id()
    search_attachments -> core/chunk_index.search()
    search_web         -> core/websearch.search()     (allowlist .gov.vn)

Kết quả tra cứu đều kèm `[id=N]`. Nhờ vậy lượt sau mô hình gọi thẳng
get_procedure(N) thay vì đoán lại từ chuỗi — đây là thứ thay cho mẹo
`context_hint` cũ (mẹo đó từng biến câu "tạm biệt" thành một thủ tục).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config import (ATTACH_TOP_K, EVIDENCE_PROCEDURES_MAX, EVIDENCE_TIE_GAP,
                    FINAL_TOP_K)
from domain.records import Procedure

EVIDENCE_CHUNKS = 4            # số đoạn tệp đính kèm đưa vào prompt


@dataclass
class Observation:
    """Kết quả một lần gọi công cụ."""
    tool: str
    query: str = ""
    ok: bool = False
    kind: str = "none"                     # procedures | attachments | web | none
    text: str = ""                         # khối bằng chứng đưa vào prompt
    sources: list[str] = field(default_factory=list)
    record: Procedure | None = None        # bản ghi top-1, để factcheck
    row_id: int | None = None
    confidence: float = 0.0
    note: str = ""                         # lý do thất bại, hiện ở header
    diagnostics: str = ""                  # nhật ký chi tiết, cho bảng Dev


# ==========================================================================
# 1. tra bảng thủ tục nội bộ
# ==========================================================================
def _render_procedure(record: Procedure, row_id: int) -> str:
    parts = [f"[id={row_id}] {record.ten}"]
    for label, value in [
        ("Lĩnh vực", record.linh_vuc),
        ("Thành phần hồ sơ", record.ho_so),
        ("Thời gian giải quyết", record.thoi_gian),
        ("Lệ phí", record.le_phi),
        ("Nơi nộp", record.dia_diem),
        ("Hình thức nộp", record.hinh_thuc_nop),
        ("Cấp thực hiện", record.cap_thuc_hien),
    ]:
        if value:
            parts.append(f"{label}: {value}")
    return "\n".join(parts)


def search_procedures(query: str, **_) -> Observation:
    from core import retrieval

    candidates = retrieval.retrieve(query, top_k=FINAL_TOP_K)
    if not candidates:
        return Observation(tool="search_procedures", query=query, ok=False,
                           note="không có kết quả")

    # Chỉ đưa thêm ứng viên SÁT ĐIỂM với top-1. Đưa bừa 3 thủ tục vào prompt
    # thì mô hình 1.5B gộp cả 3 thành một câu trả lời lộn xộn — đã thấy ở lần
    # chạy thử đầu: "đăng ký thuê nhà" ra 10 gạch đầu dòng trộn cấp số nhà với
    # gia hạn tạm trú.
    top = candidates[0]
    keep = [top]
    for cand in candidates[1:EVIDENCE_PROCEDURES_MAX]:
        if (top.confidence - cand.confidence) <= EVIDENCE_TIE_GAP:
            keep.append(cand)
    blocks = [_render_procedure(c.record, c.row_id) for c in keep]
    return Observation(
        tool="search_procedures", query=query, ok=True, kind="procedures",
        text="\n\n".join(blocks), record=top.record, row_id=top.row_id,
        confidence=float(top.confidence),
        sources=[f"Dataset thủ tục hành chính, dòng {top.row_id + 1}"],
    )


# ==========================================================================
# 2. lấy lại đúng một thủ tục đã biết
# ==========================================================================
def get_procedure(row_id, **_) -> Observation:
    from domain.records import by_row_id

    try:
        row_id = int(row_id)
    except (TypeError, ValueError):
        return Observation(tool="get_procedure", ok=False, note="row_id không hợp lệ")

    record = by_row_id().get(row_id)
    if record is None:
        return Observation(tool="get_procedure", ok=False,
                           note=f"không có thủ tục id={row_id}")
    return Observation(
        tool="get_procedure", query=str(row_id), ok=True, kind="procedures",
        text=_render_procedure(record, row_id), record=record, row_id=row_id,
        confidence=1.0,
        sources=[f"Dataset thủ tục hành chính, dòng {row_id + 1}"],
    )


# ==========================================================================
# 3. tìm trong tệp đính kèm của hội thoại
# ==========================================================================
def search_attachments(query: str, conversation_id: int | None = None, **_) -> Observation:
    from core import chunk_index

    if not conversation_id:
        return Observation(tool="search_attachments", query=query, ok=False,
                           note="không có hội thoại")

    hits = chunk_index.search(query, conversation_id, top_k=ATTACH_TOP_K)
    if not hits:
        return Observation(tool="search_attachments", query=query, ok=False,
                           note="không tìm thấy trong tệp đính kèm")

    blocks, sources = [], []
    for hit in hits[:EVIDENCE_CHUNKS]:
        name = hit.get("filename") or "tệp đính kèm"
        blocks.append(f"[{name}] {hit['content']}")
        if name not in sources:
            sources.append(name)
    return Observation(
        tool="search_attachments", query=query, ok=True, kind="attachments",
        text="\n\n".join(blocks), sources=sources,
        confidence=float(hits[0].get("confidence", 0.0)),
    )


# ==========================================================================
# 4. tra nguồn chính thống trên mạng
# ==========================================================================
def search_web(query: str, **_) -> Observation:
    from core import websearch

    result = websearch.search(query)
    if not result.ok:
        return Observation(tool="search_web", query=query, ok=False,
                           note=result.error or "không tra được",
                           diagnostics=result.report())
    return Observation(tool="search_web", query=query, ok=True, kind="web",
                       text=result.context, sources=list(result.sources),
                       diagnostics=result.report())


# ==========================================================================
# đăng ký
# ==========================================================================
REGISTRY = {
    "search_procedures": search_procedures,
    "get_procedure": get_procedure,
    "search_attachments": search_attachments,
    "search_web": search_web,
}

NAMES = tuple(REGISTRY) + ("none",)


def run(name: str, *, query: str = "", row_id=None,
        conversation_id: int | None = None) -> Observation:
    """Gọi công cụ theo tên. Không bao giờ ném lỗi ra ngoài."""
    fn = REGISTRY.get(name)
    if fn is None:
        return Observation(tool=name or "none", ok=False, note="công cụ không tồn tại")
    try:
        return fn(query=query, row_id=row_id, conversation_id=conversation_id)
    except TypeError:
        try:
            return fn(query)
        except Exception as exc:
            return Observation(tool=name, query=query, ok=False, note=str(exc))
    except Exception as exc:
        return Observation(tool=name, query=query, ok=False, note=str(exc))


# ==========================================================================
# đặc tả cho tool-calling GỐC của Ollama (AGENT_TOOL_MODE = "native")
# Mô hình 1.5B dùng chế độ "json"; cắm 3B/7B thì bật "native" là chạy được ngay.
# ==========================================================================
def specs(include_attachments: bool = True) -> list[dict]:
    out = [
        {
            "type": "function",
            "function": {
                "name": "search_procedures",
                "description": ("Tra bảng thủ tục hành chính nội bộ: thành phần "
                                "hồ sơ, thời gian giải quyết, lệ phí, nơi nộp."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string",
                                  "description": "Tên thủ tục hoặc nhu cầu của người dân"},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_procedure",
                "description": ("Lấy lại đúng một thủ tục đã nói tới trong hội "
                                "thoại, theo row_id đã thấy ở kết quả trước."),
                "parameters": {
                    "type": "object",
                    "properties": {"row_id": {"type": "integer"}},
                    "required": ["row_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": ("Tra nguồn chính thống trên mạng (chỉ nhận "
                                "domain .gov.vn trong allowlist): mức phạt, văn "
                                "bản luật, thủ tục không có trong bảng nội bộ."),
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        },
    ]
    if include_attachments:
        out.append({
            "type": "function",
            "function": {
                "name": "search_attachments",
                "description": ("Tìm trong tệp người dùng đã đính kèm ở cuộc "
                                "trò chuyện này."),
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        })
    return out

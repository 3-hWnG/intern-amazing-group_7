"""Kiểm chứng câu trả lời BẰNG LUẬT, không dùng LLM thứ hai.

MUỐN THÊM/SỬA LUẬT: viết một hàm `def rule_xxx(answer, record) -> Finding`
rồi thêm tên hàm vào danh sách RULES ở cuối file. Không cần đụng file khác.

Ý tưởng: mọi SỐ TIỀN và SỐ NGÀY xuất hiện trong câu trả lời phải có trong
bản ghi nguồn. Số là thứ quan trọng nhất và cũng là thứ mô hình nhỏ hay bịa.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config import FACTCHECK_ENABLED
from domain.records import Procedure
from domain.text import extract_durations, extract_money, fold


@dataclass
class Finding:
    rule: str
    ok: bool
    detail: str = ""


@dataclass
class FactCheckResult:
    ok: bool
    findings: list[Finding] = field(default_factory=list)

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if not f.ok]

    def summary(self) -> str:
        return "; ".join(f"{f.rule}: {f.detail}" for f in self.failures) or "đạt"


# --------------------------------------------------------------------------
# LUẬT
# --------------------------------------------------------------------------

def rule_money_in_source(answer: str, record: Procedure) -> Finding:
    """Mọi số tiền trong câu trả lời phải có trong bản ghi."""
    source = " ".join([record.le_phi, record.ho_so, record.thoi_gian])
    allowed = set(extract_money(source))
    invented = [m for m in extract_money(answer) if m not in allowed]
    return Finding("so_tien", not invented,
                   f"số tiền không có trong nguồn: {invented}" if invented else "")


def rule_duration_in_source(answer: str, record: Procedure) -> Finding:
    """Mọi mốc thời gian trong câu trả lời phải có trong bản ghi."""
    source = " ".join([record.thoi_gian, record.ho_so, record.le_phi])
    allowed = set(extract_durations(source))
    invented = [d for d in extract_durations(answer) if d not in allowed]
    return Finding("thoi_gian", not invented,
                   f"mốc thời gian không có trong nguồn: {invented}" if invented else "")


def rule_mentions_procedure(answer: str, record: Procedure) -> Finding:
    """Câu trả lời phải nhắc tới thủ tục đang được trích dẫn."""
    words = [w for w in fold(record.ten).split() if len(w) > 3]
    if not words:
        return Finding("ten_thu_tuc", True)
    folded = fold(answer)
    overlap = sum(1 for w in words if w in folded) / len(words)
    return Finding("ten_thu_tuc", overlap >= 0.3,
                   f"chỉ khớp {overlap:.0%} từ khoá trong tên thủ tục" if overlap < 0.3 else "")


def rule_no_empty_answer(answer: str, record: Procedure) -> Finding:
    text = (answer or "").strip()
    return Finding("do_dai", len(text) >= 20,
                   "câu trả lời quá ngắn hoặc rỗng" if len(text) < 20 else "")


# Thêm luật mới vào đây:
RULES = [
    rule_no_empty_answer,
    rule_money_in_source,
    rule_duration_in_source,
    rule_mentions_procedure,
]


def check(answer: str, record: Procedure | None) -> FactCheckResult:
    if not FACTCHECK_ENABLED or record is None:
        return FactCheckResult(ok=True)
    findings = [rule(answer, record) for rule in RULES]
    return FactCheckResult(ok=all(f.ok for f in findings), findings=findings)

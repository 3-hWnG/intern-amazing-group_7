"""Dựng câu trả lời hiển thị. Tầng A KHÔNG qua LLM nên không thể bịa."""

from __future__ import annotations

from config import AI_DISCLOSURE
from core.tiers import LABELS, Tier
from domain.records import Procedure


def _bullet(label: str, value: str) -> str:
    return f"- **{label}:** {value}" if value else ""


def render_record(record: Procedure) -> str:
    """Tầng A: in nguyên bản ghi, có trích dẫn nguồn."""
    lines = [f"**{record.ten}**", ""]
    lines += [x for x in [
        _bullet("Thành phần hồ sơ", record.ho_so),
        _bullet("Thời gian giải quyết", record.thoi_gian),
        _bullet("Lệ phí", record.le_phi),
        _bullet("Nơi nộp", record.dia_diem),
        _bullet("Hình thức nộp", record.hinh_thuc_nop),
    ] if x]

    meta = [x for x in [
        f"Lĩnh vực: {record.linh_vuc}" if record.linh_vuc else "",
        f"Cấp thực hiện: {record.cap_thuc_hien}" if record.cap_thuc_hien else "",
        f"Mã thủ tục: {record.ma_thu_tuc}" if record.ma_thu_tuc else "",
        f"Căn cứ: {record.can_cu_phap_ly}" if record.can_cu_phap_ly else "",
    ] if x]
    if meta:
        lines += ["", "_" + " · ".join(meta) + "_"]
    return "\n".join(lines)


def render_clarify(candidates) -> str:
    """Tầng B: hỏi lại thay vì đoán."""
    options = "\n".join(
        f"{i}. {c.record.ten}" + (f" ({c.record.cap_thuc_hien})" if c.record.cap_thuc_hien else "")
        for i, c in enumerate(candidates[:3], 1)
    )
    return ("Bạn đang hỏi về thủ tục nào trong số này?\n\n" + options +
            "\n\nTrả lời số thứ tự hoặc mô tả rõ hơn giúp mình nhé.")


def footer(tier: Tier, sources: list[str] | None = None) -> str:
    parts = [f"_[{LABELS[tier]}]_"]
    if sources:
        parts.append("Nguồn: " + ", ".join(sources))
    parts.append(AI_DISCLOSURE)
    return "\n\n" + " · ".join(parts)

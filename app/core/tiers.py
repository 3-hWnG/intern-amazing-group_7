"""Quyết định tầng trả lời A/B/C/D. Mọi ngưỡng nằm trong config.py.

A - đủ tự tin: in thẳng bản ghi, KHÔNG qua LLM (không thể bịa).
B - mơ hồ hoặc top1/top2 sát nhau: hỏi lại cho rõ.
C - không có trong DB: tra nguồn chính thống trên mạng.
D - không tra được: kiến thức chung, ghi rõ KHÔNG chắc chắn.
"""

from __future__ import annotations

from enum import Enum

from config import (AMBIGUITY_GAP, DUPLICATE_TITLE_JACCARD,
                    TIER_A_MIN_CONFIDENCE, TIER_B_MIN_CONFIDENCE)
from domain.text import title_similarity


class Tier(str, Enum):
    A_DATABASE = "A"
    B_CLARIFY = "B"
    C_WEB = "C"
    D_GENERAL = "D"


LABELS = {
    Tier.A_DATABASE: "Từ cơ sở dữ liệu thủ tục",
    Tier.B_CLARIFY: "Cần làm rõ thêm",
    Tier.C_WEB: "Tra cứu nguồn chính thống - chưa đối chiếu nội bộ",
    Tier.D_GENERAL: "Thông tin chung - KHÔNG chắc chắn",
}


def same_procedure(a, b) -> bool:
    """Hai ứng viên có thực chất là CÙNG một thủ tục không?

    Dataset có dòng trùng (8/21, 10/13, 9/14, 23/25) và dòng cùng thủ tục khác
    cấp (căn cước, hộ chiếu, ANTT, con dấu). Hỏi "bạn muốn cái nào" giữa hai
    bản sao là vô nghĩa - cứ trả lời bản đầu.
    """
    return title_similarity(a.record.ten, b.record.ten) >= DUPLICATE_TITLE_JACCARD


def decide(candidates) -> Tier:
    if not candidates:
        return Tier.C_WEB

    top = candidates[0].confidence
    second = candidates[1].confidence if len(candidates) > 1 else 0.0

    if top < TIER_B_MIN_CONFIDENCE:
        return Tier.C_WEB
    if top < TIER_A_MIN_CONFIDENCE:
        return Tier.B_CLARIFY
    if (top - second) < AMBIGUITY_GAP and len(candidates) > 1:
        # chỉ hỏi lại khi đó là hai thủ tục KHÁC NHAU thật
        if not same_procedure(candidates[0], candidates[1]):
            return Tier.B_CLARIFY
    return Tier.A_DATABASE

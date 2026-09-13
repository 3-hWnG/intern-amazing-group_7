# -*- coding: utf-8 -*-
"""Kiểm tra hai cổng lọc ở trước tầng truy hồi.

    python test_smalltalk_gate.py

KHÔNG cần Chroma, BM25, reranker hay Ollama — chỉ dùng chuỗi, chạy < 1 giây.
Bộ eval 862 câu (evaluate_retrieval.py) gọi thẳng retrieval.retrieve() nên
KHÔNG đi qua smalltalk/pipeline: nó không thể phát hiện lỗi này, và cũng không
bị hai bản vá này ảnh hưởng. Vì vậy cần bộ kiểm tra riêng ở đây.

Hai cổng:
  1. is_smalltalk()  -> câu xã giao phải được chặn trước khi truy hồi.
  2. has_admin_signal() / is_facet_followup() -> chỉ câu này mới được mượn tên
     thủ tục cũ làm ngữ cảnh (context_hint).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import smalltalk

# ---------------------------------------------------------------- dữ liệu --
# Phải nhận là XÃ GIAO (không được rơi xuống truy hồi)
SMALLTALK = [
    "Hello", "hello!", "Xin chào", "xin chao", "Chào bạn", "hi", "Hey",
    "Alo", "Chào buổi sáng", "good morning",
    "Cảm ơn", "cam on", "Cảm ơn bạn", "Cảm ơn nhé", "Cảm ơn nhiều nhé",
    "Thanks", "thank you", "Thank you so much", "thanks a lot", "tks",
    "Tạm biệt", "tam biet", "Bye", "bye bye", "Goodbye", "Good bye",
    "See you", "Hẹn gặp lại", "Chào nhé",
    "Bạn là ai", "Bạn tên gì?", "Bạn làm được gì",
    # --- các câu ĐÃ GÂY LỖI trong demo ---
    "Thank you so muchc",                 # lỗi gõ 1 ký tự
    "Thank you so muchc, Good bye",       # lỗi gõ + 2 vế + 5 chữ (> 3)
    "Cảm ơn, tạm biệt",
    "Thanks, bye",
    "Cảm ơn bạn nhiều nhé!",
    "OK, cảm ơn",
    "helo",                               # lỗi gõ
    "Xin chào!!!",
]

# Phải nhận là KHÔNG XÃ GIAO (phải đi tiếp xuống truy hồi)
NOT_SMALLTALK = [
    "Tôi muốn làm giấy khai sinh",
    "thu tuc dang ky ket hon",
    "Cảm ơn, cho hỏi thủ tục khai sinh làm thế nào",   # xã giao + câu hỏi thật
    "Chào bạn, tôi cần cấp lại căn cước",
    "Hồ sơ cấp hộ chiếu gồm những gì",
    "Lệ phí đăng ký khai tử",
    "Làm căn cước mất bao lâu",
    "xin cấp giấy phép xây dựng",
    "Đăng ký tạm trú ở đâu",
    "Giá vàng hôm nay bao nhiêu",          # ngoài phạm vi, nhưng KHÔNG xã giao
    "Thời tiết Sài Gòn thế nào",
    "Tôi muốn ly hôn",
]

# Câu ngắn ĐƯỢC PHÉP mượn ngữ cảnh thủ tục cũ
FOLLOWUP = [
    "Mất bao lâu?", "Lệ phí bao nhiêu?", "Nộp ở đâu",
    "Bao nhiêu tiền", "Cần giấy tờ gì", "Hồ sơ gồm những gì",
    "Mấy ngày", "Làm ở đâu vậy", "Thời gian giải quyết",
]

# Câu ngắn KHÔNG được mượn ngữ cảnh (đây là lỗi tầng A giả)
NO_EXPANSION = [
    "Thank you so muchc, Good bye", "Cảm ơn, tạm biệt", "Bye",
    "Hello", "Tạm biệt bạn", "Thanks", "ok",
]


def _expands(text: str) -> bool:
    """Đúng điều kiện mở rộng ngữ cảnh trong core/pipeline.py."""
    return (len(text.split()) <= 9
            and (smalltalk.has_admin_signal(text)
                 or smalltalk.is_facet_followup(text)))


def main() -> int:
    fails: list[str] = []

    for q in SMALLTALK:
        if not smalltalk.is_smalltalk(q):
            fails.append(f"[cổng 1] PHẢI là xã giao nhưng không: {q!r}")
    for q in NOT_SMALLTALK:
        if smalltalk.is_smalltalk(q):
            fails.append(f"[cổng 1] KHÔNG được là xã giao nhưng lại là: {q!r}")
    for q in FOLLOWUP:
        if not _expands(q):
            fails.append(f"[cổng 2] PHẢI mượn ngữ cảnh nhưng không: {q!r}")
    for q in NO_EXPANSION:
        if _expands(q):
            fails.append(f"[cổng 2] KHÔNG được mượn ngữ cảnh nhưng lại có: {q!r}")

    total = len(SMALLTALK) + len(NOT_SMALLTALK) + len(FOLLOWUP) + len(NO_EXPANSION)
    print(f"Đã kiểm tra {total} câu.")
    if fails:
        print(f"HỎNG {len(fails)}:")
        for f in fails:
            print("  -", f)
        return 1
    print("TẤT CẢ ĐẠT.")
    print()
    print("Câu trả lời xã giao mẫu:")
    for q in ["Hello", "Cảm ơn", "Thank you so muchc, Good bye", "Bạn là ai", "ok"]:
        print(f"  {q!r:38} -> {smalltalk.reply(q)[:64]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Chuẩn hoá chữ tiếng Việt cho tìm kiếm.

VÌ SAO CÓ FILE NÀY — đọc kỹ trước khi sửa:

SQLite FTS5 `unicode61 remove_diacritics 2` KHÔNG xử lý được chữ `đ`/`Đ`.
Lý do: nó bỏ dấu bằng cách tách NFD rồi xoá dấu tổ hợp.
    ă → U+0061 + U+0306  → tách được → thành 'a'   ✔
    ê → U+0065 + U+0302  → tách được → thành 'e'   ✔
    đ → U+0111            → KHÔNG tách được        �’
`đ` là một CHỮ CÁI riêng trong bảng chữ cái tiếng Việt, không phải 'd' + dấu.

Hậu quả nếu không sửa: người dùng gõ "dang ky ket hon" (bàn phím không dấu)
sẽ KHÔNG tìm ra "Đăng ký kết hôn" — mà `đ` lại đứng đầu một loạt động từ thủ tục
hay gặp nhất: Đăng ký, Đổi, Điều chỉnh, Đề nghị, Cấp đổi...

Cách chữa: tự fold trong Python, lưu sẵn vào cột `search_text`, và khi truy vấn
thì fold câu hỏi của người dùng bằng ĐÚNG hàm này. Cả hai phía cùng một hàm thì
không bao giờ lệch.
"""

from __future__ import annotations

import re
import unicodedata

# Ánh xạ tay cho các chữ cái KHÔNG tách được bằng NFD.
_ATOMIC = str.maketrans({"đ": "d", "Đ": "D"})

_WS = re.compile(r"\s+")


def fold(text: str) -> str:
    """Bỏ dấu + thường hoá, dùng cho cả lúc ghi index lẫn lúc truy vấn.

    >>> fold("Đăng ký kết hôn")
    'dang ky ket hon'
    >>> fold("CẤP ĐỔI thẻ Căn cước")
    'cap doi the can cuoc'
    """
    if not text:
        return ""
    text = text.translate(_ATOMIC)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = unicodedata.normalize("NFC", text)
    return _WS.sub(" ", text.lower()).strip()


def clean(text: str | None) -> str:
    """Dọn khoảng trắng thừa nhưng GIỮ NGUYÊN chữ và dấu.

    Dùng cho dữ liệu hiển thị. Không bao giờ sửa nội dung, chỉ gom khoảng trắng —
    nguồn ghi "Theo quy định" thì vẫn phải ra đúng "Theo quy định".
    """
    if not text:
        return ""
    return _WS.sub(" ", str(text).replace("\xa0", " ")).strip()

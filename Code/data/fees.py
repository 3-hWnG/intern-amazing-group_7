"""Chuẩn hoá lệ phí lúc dựng DB (G1.1, P01/F1) và một cách hiển thị duy nhất cho mọi nơi (answerer, bảng, Excel, fee_query).

Hai lỗi của nguồn:
- Dấu chấm hàng nghìn bị đọc sai: "20.000" thành amount_value=20, "25.000.000đ" thành 25.
  Sửa bằng đối chiếu với amount_text: giá trị v < 1.000 mà chữ có số v×1.000 (hoặc v×1.000.000) thì lấy số trong chữ.
- `currency_id` bị bỏ qua: mã USD bị in thành "đồng" ("chứng thực bản sao 10 đồng/bản").
Số không đối chiếu được (dưới 1.000 đồng, chữ không xác nhận) thì KHÔNG in số máy đọc, chỉ in nguyên văn chữ của Cổng."""
from __future__ import annotations

import re

CURRENCY = {"019b3fb2-b5b8-70ac-85e2-9409ec1eaffa": "VND", "019b3fb2-dee2-76ab-aa53-22d4d903a2bb": "USD"}
_NUM = re.compile(r"(?<![\d.,])\d{1,3}(?:\.\d{3})+(?![\d,]|\.\d)|(?<![\d.,])\d+(?![\d.,]\d)")
_USD = re.compile(r"\b(usd|đô la|đôla|dollar)\b", re.I)
_VND = re.compile(r"(\d\s*(đ|đồng|vnđ|vnd)\b)|\b(đồng|vnđ|vnd)\b", re.I)


def _numbers(text: str) -> set[int]:
    """Mọi số nguyên trong chữ ("20.000" -> 20000, "03" -> 3)."""
    return {int(m.replace(".", "")) for m in _NUM.findall(text or "")}


def currency_of(currency_id: str | None, text: str) -> str:
    """VND / USD theo mã của Cổng; mã rỗng/lạ thì xét chữ ("USD", "đồng"); không rõ -> ''."""
    cur = CURRENCY.get((currency_id or "").strip())
    if cur:
        return cur
    if _USD.search(text or ""):
        return "USD"
    if _VND.search(text or ""):
        return "VND"
    return ""


def normalize(value, text: str, currency_id: str | None) -> dict:
    """-> {currency, amount_vnd, amount_ok}.
    amount_ok=1: con số in ra được (VND đã sửa hàng nghìn, hoặc USD có mã/chữ xác nhận); 0: chỉ in nguyên văn chữ."""
    text = text or ""
    cur = currency_of(currency_id, text)
    if not value or value <= 0:
        return {"currency": cur, "amount_vnd": None, "amount_ok": 0}
    nums = _numbers(text)
    if cur == "USD":
        # Mã tiền của Cổng là USD, hoặc chữ ghi USD. Không đổi sang đồng.
        return {"currency": "USD", "amount_vnd": None, "amount_ok": 1}
    v = float(value)
    fixed = None
    if v == int(v):
        v = int(v)
        if v >= 1000:
            fixed = v
        else:
            for mul in (1000, 1000000):
                if v * mul in nums:
                    fixed = v * mul
                    break
            if fixed is None and v in nums and cur == "VND" and re.search(r"(?<![\d.])" + str(v) + r"\s*(đ|đồng|vnđ|vnd)\b", text, re.I):
                fixed = v   # chữ ghi đúng "500 đồng": số nhỏ nhưng được xác nhận
    if fixed is None:
        return {"currency": cur, "amount_vnd": None, "amount_ok": 0}
    # currency giữ '' khi Cổng không ghi đơn vị (số >= 1.000 vẫn coi là đồng, như trước đây)
    return {"currency": cur, "amount_vnd": fixed, "amount_ok": 1}


def money(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def display(r: dict) -> str:
    """Một dòng lệ phí để in. r có amount_value, amount_text, currency, amount_vnd, amount_ok (hàng của fees_clean)."""
    txt = (r.get("amount_text") or "").strip()
    if r.get("amount_ok") and r.get("currency") == "USD" and r.get("amount_value"):
        v = r["amount_value"]
        num = f"{v:g}".replace(".", ",") + " USD"
        return num + (f" — {txt}" if txt else "")
    if r.get("amount_ok") and r.get("amount_vnd"):
        return money(int(r["amount_vnd"])) + " đồng" + (f" — {txt}" if txt else "")
    if r.get("amount_value") and not _numbers(txt):
        # chữ không có số nào để đối chiếu: nói rõ con số chưa chắc, không tự thêm "đồng"
        return f"Cổng ghi mức {r['amount_value']:g} nhưng không rõ đơn vị (có thể bị đọc sai), bạn kiểm tra lại trên Cổng" + (f" — {txt}" if txt else "")
    return txt

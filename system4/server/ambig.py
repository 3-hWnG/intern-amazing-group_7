"""NV5 (A3): hỏi lại khi tên được hỏi khớp nhiều bản ghi (vd. "Mẹ của bé An tên gì?" khi lớp có hai bạn tên An).

Cách làm (code, không nhờ AI):
1. Với mỗi bảng (bộ dữ liệu · trang tính) đang bật, tìm cụm chữ DÀI NHẤT của câu hỏi nằm trọn (theo từng chữ, không dấu)
   trong tiêu đề bản ghi (họ tên, tên thủ tục…). Cụm toàn từ chung ("của", "tên") bị bỏ.
2. Cụm đó khớp từ 2 đến AMBIGUITY_MAX bản ghi trong cùng một bảng, không tiêu đề nào được gọi đầy đủ trong câu hỏi,
   và tìm kiếm cũng đưa ít nhất 2 bản ghi đó vào danh sách ứng viên -> mơ hồ.
Khớp nhiều hơn AMBIGUITY_MAX = từ chung (vd. "giấy phép" trong hàng trăm thủ tục) -> không hỏi.
"""
from __future__ import annotations
import json
import re

from . import db, settings
from .ground import fold

_STOP = {"baonhieu"} | set(fold("""là và của có cho các những được một này đó thì mà với không gì nào như thế ạ à ơi nhé vậy hả bạn mình tôi em
cần làm sao ở đâu khi muốn hỏi giúp về theo trong tên bé con cháu anh chị cô chú ông bà mẹ cha bố ba má thủ tục
ngày sinh nhà số điện thoại địa chỉ ai""").split())


def _w(t: str) -> list[str]:
    """Chữ không dấu; cụm "bao nhiêu" gộp thành một từ chung (để "Bảo" — không dấu là "bao" — vẫn được coi là tên)."""
    return re.findall(r"\w+", re.sub(r"\bbao nhieu\b", "baonhieu", fold(t)))


def _longest(q: list[str], t: list[str]) -> tuple[int, int]:
    """Cụm chung dài nhất (theo chữ) giữa câu hỏi q và tiêu đề t -> (độ dài, vị trí bắt đầu trong q)."""
    best, at = 0, 0
    prev = [0] * (len(t) + 1)
    for i in range(1, len(q) + 1):
        cur = [0] * (len(t) + 1)
        for j in range(1, len(t) + 1):
            if q[i - 1] == t[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best, at = cur[j], i - cur[j]
        prev = cur
    return best, at


def _contains(words: list[str], phrase: list[str]) -> bool:
    n = len(phrase)
    return any(words[i:i + n] == phrase for i in range(len(words) - n + 1))


def check(query: str, dataset_ids: list[int], candidate_ids: set[int]) -> dict | None:
    """Trả {"phrase", "options": [tiêu đề hiện trên nút], "record_ids"} nếu câu hỏi mơ hồ, không thì None."""
    q = _w(query)
    if not q or not dataset_ids:
        return None
    qset = set(q) - _STOP
    if not qset:
        return None
    marks = ",".join("?" * len(dataset_ids))
    rows = db.run(f"SELECT id, dataset_id, title, fields, source FROM records WHERE dataset_id IN ({marks}) AND fields != '{{}}'",
                  tuple(dataset_ids), many=True)
    tables: dict[tuple, list] = {}
    for r in rows:
        tw = _w(r["title"])
        if not (qset & set(tw)):
            continue
        tables.setdefault((r["dataset_id"], r["source"].rsplit(" · dòng", 1)[0]), []).append((r, tw))
    limit = settings.get("AMBIGUITY_MAX")
    best = None
    for key, items in tables.items():
        phrase, plen = None, 0
        for _, tw in items:
            n, at = _longest(q, tw)
            cand = q[at:at + n]
            if n > plen and set(cand) - _STOP:
                phrase, plen = cand, n
        if not phrase:
            continue
        all_rows = [(r, tw) for r, tw in items if _contains(tw, phrase)]
        if any(_contains(q, tw) for _, tw in all_rows):
            continue   # người dùng đã gọi đủ một tiêu đề (vd. họ tên đầy đủ) -> không mơ hồ
        if not 2 <= len(all_rows) <= limit:
            continue
        if sum(r["id"] in candidate_ids for r, _ in all_rows) < 2:
            continue   # tìm kiếm không coi các bản ghi này là liên quan
        if best is None or plen > best[0]:
            best = (plen, phrase, all_rows)
    if not best:
        return None
    _, phrase, all_rows = best
    titles = [r["title"] for r, _ in all_rows]
    options = []
    for r, _ in all_rows:   # tiêu đề trùng hệt nhau: thêm trường đầu tiên khác nhau để phân biệt
        label = r["title"]
        if titles.count(r["title"]) > 1:
            f = json.loads(r["fields"] or "{}")
            extra = next((f"{k}: {v}" for k, v in f.items() if v), "")
            label = f"{label} ({extra})" if extra else label
        options.append(label[:150])
    words = re.findall(r"\w+", query)
    shown = " ".join(words[i] for i in range(len(words)) if fold(words[i]) in phrase) or " ".join(phrase)
    return {"phrase": shown, "options": options[:limit], "record_ids": [r["id"] for r, _ in all_rows]}


def question(info: dict) -> str:
    return f"Trong dữ liệu có {len(info['options'])} mục cùng khớp \"{info['phrase']}\". Bạn muốn hỏi về mục nào?"

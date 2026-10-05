"""Baseline: retrieval cũ của repo (CHỈ ĐỌC) - parse_query + search + is_strong.

Không có planner, không có field extraction, không có nhớ ngữ cảnh: chỉ tra theo lượt user cuối.
Quy ước hành vi: chitchat -> answer (không task); is_strong -> answer; còn lại -> apologize
(= nhánh 'không tìm thấy' mà kiến trúc cũ đáng lẽ phải đi vào).
"""
import logging, os, re, sys, time
sys.path.insert(0, os.environ.get("S3_REPO", r"D:\Finale_architect\repo"))
from Database.pipeline import retrieval as R

DB = os.environ.get("S3_DB", r"D:\Finale_architect\repo\Database\runtime\procedures.db")
_conn = None
logging.getLogger("pipeline.retrieval").setLevel(logging.ERROR)  # "No module named db" (synonyms admin cần Backend.db) - xem BASELINE.md

# Biến thể chẩn đoán: gỡ cụm chỉ-field khỏi câu trước khi tra (ponytail: danh sách cứng, chỉ để ước lượng trần).
_CUES = sorted("bao nhieu tien|bao nhieu|bao lau|may ngay|mat bao|mat phi|co mat|le phi|phi|tien|giay to gi|giay to|can gi|can nhung gi|"
               "can chuan bi nhung gi|can chuan bi|gom nhung buoc nao|cac buoc|buoc nao|nhung|o dau|co quan nao|giai quyet|truc tuyen|online|"
               "nop ho so|co nop|duoc khong|khong|la gi|nhu the nao|lam sao|lam the nao|thi|mat|gi|nao|can|co|duoc|bao|nop".split("|"), key=len, reverse=True)


def _strip(q):
    from Database.pipeline.textutil import fold
    t = " " + re.sub(r"[^0-9a-z\s]", " ", fold(q)) + " "
    for c in _CUES:
        t = re.sub(rf"(?<=\s){c}(?=\s)", " ", t)
    return " ".join(t.split())


def adapter(turns, strip=False):
    global _conn
    if _conn is None:
        _conn = R.connect(DB)
    q = turns[-1]["text"]
    t0 = time.perf_counter()
    if R.is_chitchat(q):
        return {"tasks": [], "behavior": "answer", "answer_text": "", "fields_supported": False, "latency_ms": (time.perf_counter() - t0) * 1000,
                "extra": {"is_strong": False, "chitchat": True}}
    p = R.parse_query(_strip(q) if strip else q)
    hits = R.search(_conn, p["keyword"], limit=5) if p["keyword"] else []
    strong = R.is_strong(hits)
    ms = (time.perf_counter() - t0) * 1000
    return {"tasks": [{"proc_id": hits[0]["proc_id"] if hits else None, "candidates": [h["proc_id"] for h in hits],
                       "fields": None, "quantity": None}] if hits else [],
            "behavior": "answer" if strong else "apologize", "answer_text": "", "fields_supported": False, "latency_ms": ms,
            "extra": {"is_strong": strong, "keyword": p["keyword"], "top": [(h["proc_id"], h["name"][:60], h["term_overlap"], h["match_tier"]) for h in hits[:3]]}}


def adapter_stripped(turns):
    return adapter(turns, strip=True)

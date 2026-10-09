"""Bộ chấm bằng LUẬT (không LLM) cho 4 loại: condition / compare / negation / order. Dùng expected["checks"].
score_rule(case, out, cands_of) -> (kind, ok|None, detail). None = adapter chưa đủ dữ liệu để chấm (vd không có answer_text)."""
import re
import unicodedata


def fold(s):
    s = unicodedata.normalize("NFD", (s or "").lower().replace("đ", "d"))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in s if unicodedata.category(c) != "Mn"))).strip()


def _tops(out, cands_of):
    return [c[0] for c in (cands_of(t) for t in (out.get("tasks") or [])) if c]


def score_rule(case, out, cands_of):
    exp = case["expected"]
    chk = (exp.get("checks") or [None])[0]
    if not chk:
        return None, None, ""
    kind, ans, tops = chk["kind"], fold(out.get("answer_text")), _tops(out, cands_of)
    acc = {p for t in exp["tasks"] for p in t["acceptable_proc_ids"]}
    if out.get("behavior") != "answer":
        return kind, False, f"behavior={out.get('behavior')}"
    if kind == "condition":  # câu trả lời phải nhắc đúng mục condition_index (có ít nhất 1 cụm khoá)
        if not ans:
            return kind, None, "không có answer_text"
        ok = any(fold(k) in ans for k in chk["keys"])
        return kind, ok, "" if ok else f"thiếu mục '{chk['keys'][0]}'"
    if kind == "compare":  # nhắc cả 2 thủ tục: có answer_text -> đủ cụm khoá của cả hai; không -> cả hai là top-1 của 2 task
        if ans:
            miss = [i["key"] for i in chk["items"] if fold(i["key"]) not in ans]
            return kind, not miss, f"thiếu {miss}" if miss else ""
        want = {i["proc_id"] for i in chk["items"]}
        return kind, want <= set(tops), f"top-1 các task={tops}"
    # negation / order: top-1 phải thuộc đáp án, và không task nào chọn mục bị cấm
    bad = [p for p in tops if p in set(chk["forbid_proc_ids"])]
    ok = bool(tops) and tops[0] in acc and not bad
    return kind, ok, f"chọn nhầm {bad}" if bad else ("" if ok else f"top-1={tops[:1]}")

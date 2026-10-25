"""Chọn BIẾN THỂ trong cùng họ thủ tục theo "trục khác biệt" lấy từ chính dữ liệu (không bảng luật tay).

Ví dụ họ `đăng ký kết hôn` (bảng `families`): bản mặc định = "Thủ tục đăng ký kết hôn"; các bản còn lại hơn bản mặc định đúng một cụm
(`có yếu tố nước ngoài`, `... tại khu vực biên giới`). Cụm dư đó = TRỤC của biến thể, sinh tự động từ tên, không ai phải viết regex.

An toàn theo cấu trúc: chỉ ĐỔI GIỮA CÁC ANH EM CÙNG HỌ (`families.head`) và chỉ khi câu hỏi nói ra cụm trục (hoặc dấu hiệu "người nước ngoài" có cấu trúc).
Không sửa câu hỏi, không chèn chữ vào truy vấn => không thể kéo "khai sinh" sang "khai tử" như luật viết lại câu.

Giới hạn (nói thẳng): chỉ bắt được khi người dân nói gần với cụm trục ("biên giới", "lưu động", "nước ngoài"). Câu kể hoàn cảnh không chứa từ nào của trục
(\"bà liệt giường\" -> lưu động) cần một lớp NGỮ NGHĨA (embedding tiếng Việt ONNX / LLM nhỏ) cắm qua `semantic_scorer`; mặc định tắt.
"""
from __future__ import annotations

import os
import re
from typing import Callable

from system3.data.search import _fold

ENABLED = os.environ.get("S3_VARIANT_AXIS", "1") != "0"
MIN_TOKEN_IDF = 2.5          # cả hai chữ của cụm trục phải đủ đặc trưng (loại "giấy tờ", "cho người")
MIN_EVIDENCE = 3.5           # tổng IDF trung bình của cụm trục khớp tối thiểu (một cụm hai chữ vừa-hiếm)
FOREIGN_BONUS = 4.0          # dấu hiệu cấu trúc "người <Tên riêng>" / "bên <Tên riêng>" => trục chứa "nước ngoài"
# Hook ngữ nghĩa (tuỳ chọn): scorer(query_text, axis_phrase) -> điểm >= 0. Mặc định không có.
semantic_scorer: Callable[[str, str], float] | None = None

_FOREIGN_CUE = re.compile(r"(?<!\w)(?:chồng|vợ|bạn đời|rể|dâu)\b[^.,;?!]{0,30}?(?<!\w)(?:người|bên)\s+(?!Việt\b|Kinh\b|Nam\b)[A-ZĐ][a-zà-ỹ]+")   # quốc tịch của VỢ/CHỒNG nêu bằng tên riêng ("chồng em là người Hàn", "lấy chồng bên Lào")


def _bigrams(toks: list[str]) -> list[tuple[str, str]]:
    return list(zip(toks, toks[1:]))


def _build(idx) -> dict:
    """head -> {default: pid, members: {pid: {'axis': [bigram...], 'n': số bigram}}}"""
    fams: dict[str, list] = {}
    for r in idx.conn.execute("SELECT proc_id, head, default_variant FROM families WHERE n_members > 1"):
        fams.setdefault(r[1], []).append((r[0], bool(r[2])))
    out = {}
    for head, mem in fams.items():
        default = next((p for p, d in mem if d), None)
        pd = idx.byid(default) if default else None
        if not pd:
            continue
        dt = _fold(pd["name"]).split()
        dset = set(dt)
        dbi = set(_bigrams(dt))
        members = {}
        for pid, _ in mem:
            if pid == default:
                continue
            p = idx.byid(pid)
            if not p:
                continue
            toks = _fold(p["name"]).split()
            # cụm trục = bigram của tên biến thể không có trong tên bản mặc định, có ít nhất 1 chữ không thuộc tên mặc định
            axis = [b for b in _bigrams(toks) if b not in dbi and (b[0] not in dset or b[1] not in dset)]
            if axis:
                members[pid] = axis
        if members:
            out[head] = {"default": default, "members": members}
    return out


def choose_variant(idx, seg, top_pid: str, raw_text: str) -> str | None:
    """-> proc_id biến thể anh em phù hợp hơn `top_pid`, hoặc None (giữ nguyên)."""
    if not ENABLED:
        return None
    cache = getattr(idx, "_variant_axes", None)
    if cache is None:
        cache = idx._variant_axes = _build(idx)
    top = idx.byid(top_pid)
    if not top:
        return None
    fam = next((f for h, f in cache.items() if top_pid == f["default"] or top_pid in f["members"]), None)
    if not fam:
        return None
    hit_ids = {h.proc_id for h in seg.hits}
    qtoks = list(seg.query.terms)          # đã bỏ chữ chỉ-mục ("giấy tờ", "bao lâu"), chữ đệm và tên tỉnh: cụm trục không khớp nhầm vào chữ hỏi mục
    qbi = set(_bigrams(qtoks))
    foreign_cue = bool(_FOREIGN_CUE.search(raw_text or ""))
    best, best_sc, best_n = None, 0.0, 0
    for pid, axis in fam["members"].items():
        if pid not in hit_ids:
            continue
        ev = 0.0
        for b in axis:
            if b in qbi and min(idx._weight(b[0]), idx._weight(b[1])) >= MIN_TOKEN_IDF:
                ev += (idx._weight(b[0]) + idx._weight(b[1])) / 2
        if foreign_cue and ("nuoc", "ngoai") in axis:
            ev += FOREIGN_BONUS
        if semantic_scorer:
            ev += semantic_scorer(seg.text, " ".join(a for b in axis for a in b))
        if ev >= MIN_EVIDENCE and (ev > best_sc or (ev == best_sc and len(axis) < best_n)):
            best, best_sc, best_n = pid, ev, len(axis)
    if best and best != top_pid:
        return best
    return None

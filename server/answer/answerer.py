"""Executor + Answerer: lấy đúng các mục được hỏi, soạn câu trả lời BẰNG CODE (không LLM), kèm nguồn.

Vì sao bằng code: câu hỏi một mục (lệ phí, thời hạn, giấy tờ…) chỉ cần trích nguyên văn ô dữ liệu; code không thể bịa số,
và nhanh. LLM chỉ nên dùng cho so sánh/giải thích điều kiện (chưa làm ở bản tối thiểu này — xem README).
ponytail: điều kiện được đối chiếu bằng trùng âm tiết với dữ liệu, chưa hiểu nghĩa; bản LLM thay thế sau.
"""
from __future__ import annotations

import re

from system3.data import api as data_api
from system3.data.textutil import fold

from .llm_answer import budgeted, compose, render
from .verifier import verify

DEFAULT_FIELDS = ["components", "processing_time", "fees", "address"]
FIELD_TITLE = {"components": "Giấy tờ cần chuẩn bị", "fees": "Lệ phí", "processing_time": "Thời hạn giải quyết",
               "address": "Nơi nộp hồ sơ", "online": "Nộp trực tuyến", "methods": "Hình thức nộp",
               "files": "Biểu mẫu", "agency": "Cơ quan giải quyết", "steps": "Các bước thực hiện",
               "explanation": "Mô tả", "meta": "Căn cứ ban hành", "legal_basis": "Căn cứ pháp lý"}
ABSENT = {
    "fees": "Cổng Dịch vụ công không công bố mức lệ phí cho thủ tục này. Việc cổng không công bố chưa cho biết thủ tục có thu phí hay không — bạn nên hỏi trực tiếp cơ quan tiếp nhận.",
    "processing_time": "Cổng Dịch vụ công không công bố thời hạn giải quyết của thủ tục này.",
    "address": "Cổng Dịch vụ công không ghi địa điểm nộp hồ sơ trực tiếp cho thủ tục này.",
    "online": "Cổng Dịch vụ công không ghi hình thức nộp trực tuyến cho thủ tục này.",
    "methods": "Cổng Dịch vụ công không ghi hình thức nộp cho thủ tục này.",
    "files": "Cổng Dịch vụ công không có biểu mẫu đính kèm cho thủ tục này.",
    "agency": "Cổng Dịch vụ công không ghi cơ quan giải quyết cho thủ tục này.",
    "components": "Cổng Dịch vụ công không có danh sách giấy tờ cho thủ tục này.",
    "steps": "Cổng Dịch vụ công không có mô tả các bước cho thủ tục này.",
    "explanation": "Cổng Dịch vụ công không có mô tả cho thủ tục này.",
    "meta": "Cổng Dịch vụ công không có thông tin quyết định công bố của thủ tục này.",
    "legal_basis": "Cổng Dịch vụ công không có danh sách căn cứ pháp lý của thủ tục này.",
}
UNKNOWN = "Mình chưa tra được mục này của thủ tục."
APOLOGY = {
    "not_found": "Mình không tìm thấy thủ tục nào trong dữ liệu khớp với yêu cầu này, nên không dám trả lời để tránh nói sai.",
    "off_topic": "Câu hỏi này nằm ngoài phạm vi của mình: mình chỉ hỗ trợ thủ tục hành chính cấp xã/phường.",
    "not_commune_level": "Thủ tục này không thuộc cấp xã/phường nên mình chưa hỗ trợ.",
    "vertical_agency": "Thủ tục này do {agency} giải quyết, không thuộc phạm vi mình hỗ trợ (thủ tục cấp xã/phường).",
    "expired": "Thủ tục này không còn trong danh mục của Cổng Dịch vụ công nên mình không trả lời để tránh đưa thông tin lỗi thời.",
    "injection": "Mình chỉ hỗ trợ tra cứu thủ tục hành chính cấp xã/phường và không thể làm theo yêu cầu đó.",
}
CHITCHAT = "Xin chào! Mình là trợ lý tra cứu thủ tục hành chính cấp xã/phường. Bạn cần hỏi thủ tục nào?"
MAX_CHARS = 1100
SUMMARY_CHARS = 450


def _MORE() -> str:
    """Phase 20: có nút "Tạo bảng full" thì chỉ báo ngắn, nút ở UI; tắt cờ thì giữ câu cũ."""
    from config import TABLE_BUTTON
    return "\n… (còn nữa, bấm «Tạo bảng full» để xem đủ)" if TABLE_BUTTON else "\n… (còn nữa, xem đầy đủ trên Cổng Dịch vụ công)"


def _clip(text: str, n: int = MAX_CHARS) -> str:
    text = text.strip()
    if len(text) <= n:
        return text
    cut = text[:n]
    cut = cut[:cut.rfind("\n")] if "\n" in cut[n // 2:] else cut[:cut.rfind(" ")]
    return cut.rstrip() + _MORE()


def _overlap(a: str, b: str) -> float:
    ta = [t for t in re.findall(r"[0-9a-z]+", fold(a)) if len(t) > 1]
    tb = set(re.findall(r"[0-9a-z]+", fold(b)))
    return sum(1 for t in ta if t in tb) / len(ta) if ta else 0.0


_NOISE = {"toi", "minh", "em", "la", "co", "bi", "cua", "va", "thi", "neu", "truong", "hop"}


def _jacc(a: str, b: str) -> float:
    """|A ∩ B| / max(|A|, |B|) trên chữ (bỏ dấu, bỏ chữ đệm) — hai cụm phải gần như CÙNG nghĩa, không chỉ chứa nhau."""
    ta = {t for t in re.findall(r"[0-9a-z]+", fold(a)) if len(t) > 1 and t not in _NOISE}
    tb = {t for t in re.findall(r"[0-9a-z]+", fold(b)) if len(t) > 1 and t not in _NOISE}
    return len(ta & tb) / max(len(ta), len(tb), 1)


def _fees_text(conn, pid: str) -> tuple[str, str]:
    """-> (text, status). status: present | absent_confirmed. KHÔNG suy ra miễn phí khi nguồn rỗng."""
    rows = [dict(r) for r in conn.execute(
        "SELECT kind, amount_value, amount_text, fee_type, submission_method FROM fees_clean WHERE proc_id=?", (pid,))]
    seen, lines = set(), []
    for r in rows:
        if r["kind"] == "none":
            continue
        txt = (r["amount_text"] or "").strip()
        if r["kind"] == "numeric" and r["amount_value"]:
            txt = f"{int(r['amount_value']):,}".replace(",", ".") + " đồng" + (f" — {txt}" if txt else "")
        if txt and txt not in seen:
            seen.add(txt)
            lines.append(f"- {txt}" + (f" ({r['submission_method']})" if r["submission_method"] else ""))
    if not lines:     # cổng không có lệ phí -> bù từ corpus nhóm (ghi nguồn); không có nữa thì KHÔNG suy ra miễn phí
        try:
            ov = [r[0] for r in conn.execute("SELECT amount_text FROM team_fee_overlay WHERE proc_id=?", (pid,))]
        except Exception:
            ov = []
        if ov:
            return "\n".join(f"- {t}" for t in dict.fromkeys(ov)) + "\n(Nguồn: Bộ dữ liệu nhóm, chuẩn hóa từ cổng)", "present"
    return ("\n".join(lines), "present") if lines else ("", "absent_confirmed")


def _time_text(raw: str) -> str:
    parts, seen = [], set()
    for p in (x.strip() for x in raw.split(";")):
        if re.search(r"[A-Za-zÀ-ỹ]", p) and p not in seen:    # bỏ mảnh chỉ có số ("1")
            seen.add(p)
            parts.append(p)
    return "; ".join(parts) or raw.strip()


def _case_pick(chunks: list[dict], conds: list[str], label: str) -> list[dict]:
    """Giấy tờ theo TRƯỜNG HỢP người dùng nêu: mỗi khối `components` mở đầu bằng tên trường hợp (cùng chữ với condition_index, source=case).
    Chọn khối có tên trùng >= 60% chữ ĐẶC TRƯNG của hoàn cảnh (bỏ chữ trong tên thủ tục); không khối nào đủ khớp -> [] (giữ toàn bộ hồ sơ chung).
    ponytail: khớp chữ, không hiểu nghĩa ('ở chùa' != 'cơ sở tín ngưỡng'); LLM/bảng đồng nghĩa nâng cấp sau."""
    name = set(re.findall(r"[0-9a-z]+", fold(label)))
    best, scored = 0.0, []
    for c in chunks:
        title = set(re.findall(r"[0-9a-z]+", fold(c["text"].strip().split("\n", 1)[0])))
        sc = 0.0
        for cd in conds:
            toks = [t for t in re.findall(r"[0-9a-z]+", fold(cd)) if len(t) > 1 and t not in name]
            if len(toks) >= 2:
                sc = max(sc, sum(1 for t in toks if t in title) / len(toks))
        scored.append(sc)
        best = max(best, sc)
    return [c for c, sc in zip(chunks, scored) if best >= 0.6 and sc >= best - 0.01]


def _field_text(conn, pid: str, f: str, status: str, conds: list[str] | None = None, label: str = "") -> tuple[str, str]:
    """-> (nội dung, trạng thái thực). Trạng thái 'unknown' không đồng nghĩa với 'không có'."""
    if f == "fees":
        txt, st = _fees_text(conn, pid)
        return txt, st
    chunks = [c for c in data_api.fields(conn, pid, [f]) if c["text"].strip()]
    if not chunks:
        return "", ("unknown" if status == "unknown" else "absent_confirmed")
    if f == "processing_time":
        return _time_text(chunks[0]["text"]), "present"
    if f == "components":
        pick = _case_pick(chunks, conds or [], label)
        if pick:
            return _clip("Theo trường hợp bạn nêu:\n" + "\n".join(c["text"].strip() for c in pick)), "present"
        return _clip("\n".join(c["text"].strip() for c in chunks)), "present"
    if f == "legal_basis":
        lines = chunks[0]["text"].strip().split("\n")
        return "\n".join(f"- {l}" for l in lines[:3]) + (f"\n… và {len(lines) - 3} văn bản khác" if len(lines) > 3 else ""), "present"
    return _clip(chunks[0]["text"]), "present"


def _sources(conn, pid: str, with_legal: bool) -> list[dict]:
    r = conn.execute("SELECT portal_url, decision_number, decision_date, issuing_agency FROM procedures WHERE proc_id=?",
                     (pid,)).fetchone()
    out = []
    if r and r["portal_url"]:
        out.append({"label": "Cổng Dịch vụ công Quốc gia", "url": r["portal_url"]})
    if r and r["decision_number"]:
        out.append({"label": f"Quyết định công bố {r['decision_number']} ({r['decision_date']}, {r['issuing_agency']})", "url": ""})
    if with_legal:
        for lb in conn.execute("SELECT doc_code, doc_name FROM legal_basis WHERE row_id=(SELECT row_id FROM procedures WHERE proc_id=? AND status='active') LIMIT 3", (pid,)):
            out.append({"label": f"{lb['doc_code']} {lb['doc_name']}"[:140], "url": ""})
    return out


def _condition_note(conn, pid: str, conditions: list[str], evidence: str) -> str:
    if not conditions:
        return ""
    cond_rows = [r["text"] for r in data_api.conditions(conn, pid)]
    notes = []
    for c in conditions:
        hit = max(cond_rows, key=lambda t: _jacc(c, t), default=None)
        hit = hit if hit is not None and _jacc(c, hit) >= 0.5 else None      # khớp đối xứng: "người nước ngoài" không được coi là "Người Việt Nam định cư ở nước ngoài"
        in_ev = _overlap(c, evidence) >= 0.8 and len(c.split()) <= 5
        if hit:
            notes.append(f"- «{c}»: dữ liệu có nêu trường hợp/đối tượng \"{hit[:120]}\".")
        elif in_ev:
            notes.append(f"- «{c}»: có xuất hiện trong nội dung trên.")
        else:
            notes.append(f"- «{c}»: Cổng Dịch vụ công không công bố riêng phần điều kiện/giấy tờ cho trường hợp này, nên mình không khẳng định trường hợp này có thay đổi gì không.")
    return "Về điều kiện bạn nêu:\n" + "\n".join(notes)


def _merge(tasks):
    """Gộp các task cùng thủ tục (LLM/luật hay tách 'giấy tờ và lệ phí' thành 2 task)."""
    merged, order = {}, []
    for t in tasks:
        if t.route != "direct":
            order.append(t)
            continue
        k = t.procedure_id
        if k in merged:
            m = merged[k]
            m.fields += [f for f in t.fields if f not in m.fields]
            m.conditions += [c for c in t.conditions if c not in m.conditions]
            m.soft_conditions += [c for c in t.soft_conditions if c not in m.soft_conditions]
            m.cases += [c for c in t.cases if c not in m.cases]
            if t.evidence_demand != "none":
                m.evidence_demand = t.evidence_demand
        else:
            merged[k] = t
            order.append(t)
    return order


def answer(routed, *, conn=None, question: str = "", llm=None) -> dict:
    """routed: policy.Routed -> {"kind","blocks":[{title,text,sources,variants}],"clarify","verify"}.
    llm: hàm kiểu core.llm.chat_json(system, user, schema=, timeout=) -> dict. None = chỉ bằng code (như cũ).
    Có llm: dùng cho giải thích điều kiện (task có conditions) và so sánh (>=2 task relation=compare); lỗi -> bản bằng code."""
    conn = conn or data_api.connect()
    llm = budgeted(llm)                       # Phase 27: trần thời gian LLM chung cho cả lượt
    blocks, issues, cmp_src = [], [], []
    if routed.clarify:
        return {"kind": "clarify", "blocks": [], "clarify": routed.clarify, "verify": []}
    for t in _merge(routed.tasks):
        if t.route == "chitchat":
            blocks.append({"title": "", "text": CHITCHAT, "sources": []})
        elif t.route == "note":
            blocks.append({"title": "Đã ghi nhận", "text": "Mình đã ghi nhận thông tin bạn cung cấp: " + "; ".join(t.context_facts or ["(không có)"]), "sources": []})
        elif t.route == "apologize":
            if any(b.get("title") == "Chưa hỗ trợ được" and t.reason in b.get("_r", ()) for b in blocks):
                continue
            blocks.append({"title": "Chưa hỗ trợ được", "sources": [],
                           "text": APOLOGY.get(t.reason, APOLOGY["not_found"]).format(agency=t.vertical_agency), "_r": (t.reason,)})
        elif t.route == "direct":
            fields = t.fields or DEFAULT_FIELDS
            if t.evidence_demand == "legal_basis" and "legal_basis" not in fields:
                fields = fields + ["legal_basis"]
            parts, evidence = [], []
            for f in fields:
                txt, st = _field_text(conn, t.procedure_id, f, t.field_status.get(f, "unknown"), t.cases, t.procedure_label)
                if not t.fields and st == "present" and len(txt) > SUMMARY_CHARS:      # hỏi chung ("làm thủ tục X"): bản tóm tắt ngắn, hỏi cụ thể từng mục mới xem đầy đủ
                    txt = _clip(txt, SUMMARY_CHARS)
                evidence.append(txt)
                head = FIELD_TITLE.get(f, f)
                body = txt if st == "present" else (ABSENT[f] if st == "absent_confirmed" else UNKNOWN)
                parts.append(f"{head}:\n{body}")
            ev_text = "\n".join(evidence)
            note = _condition_note(conn, t.procedure_id, t.conditions + [c for c in t.soft_conditions if c not in t.conditions], ev_text)
            present = [{"label": f"{FIELD_TITLE.get(f, f)} - {t.procedure_label}", "text": e} for f, e in zip(fields, evidence) if e.strip()]
            if llm and t.conditions:
                cond_ps = [{"label": f"Điều kiện - {t.procedure_label}", "text": c["text"]} for c in data_api.conditions(conn, t.procedure_id)[:8]]
                pts = compose(llm, present + cond_ps, "Giải thích các điều kiện/trường hợp người dùng nêu: " + "; ".join(t.conditions),
                              question, issues)
                if pts:
                    note = "Về điều kiện bạn nêu:\n" + render(pts)
                    ev_text += "\n" + "\n".join(p["text"] for p in cond_ps)
            cmp_src.append((t, present))
            text = "\n\n".join(parts + ([note] if note else []))
            issues += verify(text, ev_text + " " + " ".join(ABSENT.values()), question)
            blk = {"title": t.procedure_label, "text": text,
                   "sources": _sources(conn, t.procedure_id, "legal_basis" in fields or t.evidence_demand != "none")}
            if t.procedure_id:
                blk["proc_id"] = t.procedure_id        # UI dùng cho nút "Tạo bảng full" (GET /procedure/{id}/table)
            if t.variants.get("others"):
                blk["variants"] = t.variants
            blocks.append(blk)
    if llm and len(cmp_src) >= 2 and any(t.relation == "compare" for t, _ in cmp_src):
        pts = compose(llm, [p for _, ps in cmp_src for p in ps], "So sánh các thủ tục trên theo điều người dùng hỏi", question, issues)
        if pts:
            srcs = [s for b in blocks for s in b.get("sources", [])]
            blocks.append({"title": "So sánh", "text": render(pts), "sources": list({s["label"]: s for s in srcs}.values())})
    if "overflow" in routed.flags:
        blocks.append({"title": "Lưu ý", "text": "Mình chỉ trả lời 3 ý đầu tiên. Bạn hỏi lại các ý còn lại ở tin nhắn sau nhé.", "sources": []})
    for b in blocks:
        b.pop("_r", None)
    kind = {"answer": "answer", "chitchat": "chitchat", "apologize": "apologize"}.get(routed.behavior, "answer")
    return {"kind": kind, "blocks": blocks, "clarify": None, "verify": issues}


TABLE_FIELDS = ["components", "fees", "processing_time", "address", "methods", "online", "steps", "files",
                "agency", "meta", "legal_basis", "explanation"]


def procedure_table(conn, pid: str) -> dict | None:
    """Phase 20: bảng ĐẦY ĐỦ mọi mục của một thủ tục, nguyên văn từ data.api (không LLM, không cắt). None = không có/hết hiệu lực."""
    if data_api.is_expired(conn, pid):
        return None
    rec = data_api.get_record(conn, pid)
    if not rec:
        return None
    rows = []
    for f in TABLE_FIELDS:
        if f == "fees":
            txt, st = _fees_text(conn, pid)
        else:
            ch = [c for c in data_api.fields(conn, pid, [f]) if c["text"].strip()]
            txt, st = "\n".join(c["text"].strip() for c in ch), "present"
            if not ch:
                st = "absent_confirmed"
            elif f == "processing_time":
                txt = _time_text(ch[0]["text"])
        # ponytail: thiếu dữ liệu -> câu ABSENT chung; không phân biệt "unknown" (bảng chỉ để xem, không suy diễn)
        rows.append({"field": f, "title": FIELD_TITLE[f], "status": st, "text": txt if st == "present" else ABSENT[f]})
    return {"proc_id": pid, "name": rec["name"], "domain": rec.get("domain", ""), "rows": rows,
            "sources": _sources(conn, pid, True)}

"""Biên dịch một bộ dữ liệu (bản ghi đã nạp bởi ingest.py) thành ĐẶC TẢ cho đường nhanh. Chạy lúc nạp, không chạy lúc hỏi.

  1. gom bản ghi thành bảng (theo nguồn "tệp · trang tính · dòng n", như tabletool) và đoạn văn bản (bản ghi không có trường);
  2. suy KIỂU từng cột: flag (đánh dấu x) / date / number / id / enum / text; cột văn bản dài (> LONG_CHARS) không dùng làm điều kiện lọc
     (phép thử ABI 18/10: lọc trên cột "tóm tắt / nội dung" sinh điều kiện rác);
  3. nhận BẢNG CON: cột có giá trị duy nhất ở bảng A và nằm trong bảng B (cùng bộ dữ liệu) -> B là con của A, không thành thực thể riêng;
  4. từ gợi ý KHÔNG cần AI: cả tên cột + từng chữ chỉ có ở một tên cột;
  5. (⚙ FASTPATH_LLM_CUES) gọi AI MỘT lần mỗi bảng: tên tiếng Việt của cột (label) + cách người dùng hỏi + từ phủ định cho cột flag;
     code lọc lại (vet_cues): AI 4B hay đưa giá trị trong ô hoặc chữ chung thay cho cách hỏi.
Gợi ý lưu kèm chữ có dấu: engine so dấu khi người dùng gõ có dấu ("năm" khác "nam", như ACCENT_MISMATCH của System 3).
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict

from .. import config, db, llm, settings
from ..ground import fold

DATE = re.compile(r"^\s*(\d{1,2}[/.-]\d{1,2}[/.-](19|20)\d{2}|(19|20)\d{2}-\d{2}-\d{2})")
FLAG_VALUES = {"x", "v", "co", "yes", "y", "1", "true", "✓"}
LONG_CHARS = 80
SINGLE_STOP = {"ho", "va", "cua", "so", "ten", "the", "do", "of", "and", "you", "can", "there", "text", "n", "has", "is", "co", "khong",
               "id", "ma", "la", "gi", "nao", "dau", "at", "len", "thu", "tuc", "cac", "mot", "nhung", "vnd", "dong"}
CUE_CACHE = config.RUNTIME_DIR / "fastpath_cues.json"
# từ để hỏi / đếm (chữ gốc có dấu): gợi ý chỉ gồm những từ này ("bao nhiêu", "có bao nhiêu") khớp MỌI câu đếm -> bỏ (lỗi 18/10)
QWORDS = {"bao", "nhiêu", "mấy", "có", "không", "nào", "gì", "là", "số", "lượng", "tổng"}


def tokens(t: str) -> list[tuple[str, str]]:
    """[(chữ bỏ dấu, chữ gốc viết thường)]."""
    return [(f, w) for w in re.findall(r"[^\W_]+", (t or "").lower()) for f in [re.sub(r"[^a-z0-9]", "", fold(w))] if f]


def words(t: str) -> list[str]:
    return [f for f, _ in tokens(t)]


def _is_num(v: str) -> bool:
    return bool(re.fullmatch(r"-?[\d.,]+\s*(%|d|vnd|dong|đ)?", fold(v).strip()))


def infer_type(name: str, values: list[str], n_rows: int) -> str:
    vals = [v for v in values if v]
    if not vals:
        return "empty"
    fv = [fold(v).strip() for v in vals]
    if len(vals) < n_rows * 0.95 and sum(v in FLAG_VALUES for v in fv) >= 0.9 * len(vals):
        return "flag"
    if sum(bool(DATE.match(v)) for v in vals) >= 0.8 * len(vals):
        return "date"
    uniq = len(set(fv)) / len(fv)
    # mã: tên cột gợi ý, hoặc chuỗi số có số 0 đứng đầu / dấu cách / gạch (số điện thoại, CCCD, mã BH). Số trơn (giá 1450000) là SỐ (lỗi 18/10)
    code_like = lambda v: bool(re.fullmatch(r"[\d\- .]{6,}", v)) and (v.startswith("0") or bool(re.search(r"[\- ]", v.strip())))
    if (re.search(r"\b(id|hash|url|link|duong dan|uuid)\b", fold(name)) or sum(code_like(v) for v in vals) >= 0.8 * len(vals)) and uniq > 0.9:
        return "id"
    if sum(_is_num(v) for v in vals) >= 0.8 * len(vals):
        return "number"
    if n_rows >= 8 and len(set(fv)) <= max(12, n_rows // 5):
        return "enum"
    return "text"


def gather(ds: dict) -> tuple[list[dict], list[dict]]:
    """Bản ghi của bộ dữ liệu -> (bảng, đoạn văn bản). Mỗi dòng giữ id bản ghi để làm nguồn [n]."""
    groups: dict[str, list] = defaultdict(list)
    texts = []
    for r in db.run("SELECT id, title, fields, text, source FROM records WHERE dataset_id=? ORDER BY id", (ds["id"],), many=True):
        f = json.loads(r["fields"] or "{}")
        if f:
            groups[r["source"].rsplit(" · dòng", 1)[0]].append({"id": r["id"], "title": r["title"], "fields": f, "text": r["text"]})
        else:
            texts.append({"id": r["id"], "title": r["title"], "text": r["text"], "source": r["source"]})
    tables = []
    for k, (src, rows) in enumerate(groups.items()):
        name = src.split(" · ", 1)[1] if " · " in src else src
        label = rows[0]["text"].split(":", 1)[0].strip() or "Tiêu đề"   # dòng đầu của text = "<cột tiêu đề>: <tiêu đề>"
        cols = list(dict.fromkeys(c for r in rows for c in r["fields"]))
        fields = {}
        for c in cols:
            vals = [str(r["fields"].get(c, "")) for r in rows]
            filled = [v for v in vals if v]
            fields[c] = {"type": infer_type(c, vals, len(rows)), "label": c,
                         "long": bool(filled) and sum(len(v) for v in filled) / len(filled) > LONG_CHARS}
        tables.append({"key": f"{ds['id']}:{k}", "dataset_id": ds["id"], "dataset": ds["name"], "name": name, "title_label": label,
                       "file": ds["filename"], "rows": rows, "fields": fields, "parent": None, "children": [], "entity_noun": ""})
    # bảng con: cột khoá duy nhất ở bảng cha, giá trị bảng con nằm trong bảng cha (>= 90%)
    for a in tables:
        if a["parent"]:
            continue
        for col in a["fields"]:
            va = [r["fields"].get(col) for r in a["rows"]]
            if None in va or len(set(va)) != len(va):
                continue
            for b in tables:
                if b is a or b["parent"] or b["children"] or col not in b["fields"]:
                    continue
                vb = [r["fields"].get(col) for r in b["rows"] if r["fields"].get(col)]
                if vb and sum(v in set(va) for v in vb) >= 0.9 * len(vb):
                    b["parent"] = {"table": a["key"], "via": col}
                    a["children"].append({"table": b["key"], "via": col})
    return tables, texts


def header_cues(fields: list[str]) -> dict[str, list[list[str]]]:
    toks = {f: [w for _, w in tokens(f.replace("_", " "))] for f in fields}
    df = Counter(fold(w) for ws in toks.values() for w in set(ws))
    out = {}
    for f, ws in toks.items():
        cues = [ws] if ws and not all(fold(w) in SINGLE_STOP for w in ws) else []   # "Tên" một mình quá chung
        cues += [[w] for w in ws if df[fold(w)] == 1 and len(w) >= 2 and fold(w) not in SINGLE_STOP]
        out[f] = cues
    return out


LLM_SCHEMA = {"type": "object", "properties": {
    "entity_noun": {"type": "string"},
    "fields": {"type": "array", "items": {"type": "object", "properties": {
        "name": {"type": "string"}, "label_vi": {"type": "string"},
        "cues": {"type": "array", "items": {"type": "string"}, "maxItems": 8}, "absent_word": {"type": "string"}},
        "required": ["name", "label_vi", "cues", "absent_word"]}}},
    "required": ["entity_noun", "fields"]}
LLM_SYSTEM = (
    "Bạn giúp một hệ thống hỏi đáp tiếng Việt hiểu một bảng dữ liệu. Với MỖI trường cho:\n"
    "- label_vi: tên trường bằng tiếng Việt tự nhiên (dịch nếu tên cột là tiếng Anh / viết tắt).\n"
    "- cues: 3-8 cụm từ NGẮN (1-4 chữ, tiếng Việt CÓ DẤU, viết thường) người dân dùng khi HỎI về trường đó. "
    "Đó là CÁCH HỎI, KHÔNG phải giá trị trong ô, không dùng chữ chung chung (\"có\", \"không\", \"tên\", \"số\", \"thông tin\").\n"
    "- absent_word: chỉ cho trường kiểu flag (đánh dấu x): từ chỉ dòng KHÔNG đánh dấu; trường khác để \"\".\n"
    "Ví dụ (bảng sản phẩm, không liên quan bảng của bạn): trường \"Giá bán\" -> label_vi \"giá bán\", cues [\"giá\", \"bao nhiêu tiền\", "
    "\"giá bao nhiêu\"]; trường \"warranty_months\" -> label_vi \"thời gian bảo hành\", cues [\"bảo hành\", \"bảo hành bao lâu\", "
    "\"mấy tháng bảo hành\"]; trường \"Còn hàng\" (flag) -> absent_word \"hết hàng\".\n"
    "entity_noun: danh từ tiếng Việt chỉ MỘT dòng của bảng.")


def _cue_cache() -> dict:
    try:
        return json.loads(CUE_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def llm_cues(t: dict) -> dict:
    """Một lời gọi AI (JSON) cho cả bảng; lưu đệm theo chữ ký bảng + model. Lỗi / AI tắt -> {} (chỉ dùng tên cột)."""
    sig = hashlib.sha1(json.dumps(["v2", settings.get("FRIENDLY_MODEL"), t["name"], t["title_label"], sorted(t["fields"])],
                                  ensure_ascii=False).encode()).hexdigest()[:16]
    cache = _cue_cache()
    if sig in cache:
        return cache[sig]
    lines = []
    for f, m in t["fields"].items():
        if m["type"] == "empty":
            continue
        samples = [str(r["fields"][f]) for r in t["rows"] if r["fields"].get(f)][:3]
        lines.append(f'- "{f}" (kiểu {m["type"]}; ví dụ: {" | ".join(s[:40] for s in samples)})')
    titles = " | ".join(r["title"][:50] for r in t["rows"][:3])
    user = f"Bảng \"{t['name']}\"; mỗi dòng là một \"{t['title_label']}\" (vd: {titles}).\nCác trường:\n" + "\n".join(lines)
    from core import gpu
    with gpu.slot(gpu.P3):   # việc nền lúc nạp: nhường câu hỏi đang chờ
        out = llm.chat_json([{"role": "system", "content": LLM_SYSTEM}, {"role": "user", "content": user}], LLM_SCHEMA, timeout=300)
    if out.get("fields"):
        cache[sig] = out
        try:
            CUE_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return out


def _phrase_in(ph: list[str], text: str) -> bool:
    return f" {' '.join(ph)} " in f" {' '.join(words(text))} "


def vet_cues(t: dict) -> dict:
    """Bỏ gợi ý: toàn chữ chung; là giá trị của chính trường (>= 10% ô) hoặc nằm trong tiêu đề (>= 5% dòng); trùng ở >= 2 trường
    (trừ khi đó là tên cột). Trả {trường: [[gợi ý, lý do]]} để hiện ở bảng điều khiển."""
    dropped = defaultdict(list)
    owners = defaultdict(set)
    for f, m in t["fields"].items():
        for c in m["cues"]:
            owners[" ".join(fold(w) for w in c)].add(f)
    n = len(t["rows"])
    for f, m in t["fields"].items():
        keep, vals = [], [str(r["fields"].get(f, "")) for r in t["rows"]]
        for c in m["cues"]:
            fc = [fold(w) for w in c]
            why = None
            if all(w in SINGLE_STOP for w in fc) or all(w.lower() in QWORDS or f in SINGLE_STOP for w, f in zip(c, fc)):
                why = "chữ chung / chỉ là từ để hỏi"
            elif sum(_phrase_in(fc, v) for v in vals) >= max(2, 0.1 * n):
                why = "là giá trị trong ô"
            elif sum(_phrase_in(fc, r["title"]) for r in t["rows"]) >= max(2, 0.05 * n):
                why = "nằm trong tiêu đề"
            elif len(owners[" ".join(fc)]) > 1 and c not in m["header"]:
                why = "trùng nhiều trường"
            if why:
                dropped[f].append([" ".join(c), why])
            elif c not in keep:
                keep.append(c)
        m["cues"] = keep
        for c in m.get("absent", []):   # từ phủ định của cột đánh dấu (vd. AI đưa "không" cho cột "Nữ") cũng không được là chữ chung
            if all(fold(w) in SINGLE_STOP for w in c):
                dropped[f].append(["≠ " + " ".join(c), "chữ chung"])
        m["absent"] = [c for c in m.get("absent", []) if not all(fold(w) in SINGLE_STOP for w in c)]
    return dict(dropped)


def compile_dataset(ds: dict, use_llm: bool | None = None) -> dict:
    """Bộ dữ liệu -> spec (JSON được; dòng chỉ giữ id bản ghi, engine đọc lại nội dung từ DB)."""
    use_llm = settings.get("FASTPATH_LLM_CUES") if use_llm is None else use_llm
    tables, texts = gather(ds)
    llm_used = 0
    for t in tables:
        hc = header_cues(list(t["fields"]))
        for f, m in t["fields"].items():
            m["cues"], m["header"], m["absent"] = list(hc[f]), list(hc[f]), []
        if use_llm and t["parent"] is None and len(t["rows"]) >= 2:
            out = llm_cues(t)
            llm_used += bool(out.get("fields"))
            noun = [w for _, w in tokens(out.get("entity_noun") or "")]
            while noun and fold(noun[0]) in ("mot", "cac", "nhung", "moi", "1"):   # AI hay viết "một tour", "các điểm đến" (lỗi 18/10)
                noun = noun[1:]
            t["entity_noun"] = " ".join(noun)[:40]
            for item in out.get("fields", []):
                m = t["fields"].get(item.get("name"))
                if not m:
                    continue
                if (item.get("label_vi") or "").strip():
                    m["label"] = item["label_vi"].strip()[:60]
                    m["cues"].append([w for _, w in tokens(m["label"])])
                m["cues"] += [c for c in ([w for _, w in tokens(x)] for x in item.get("cues", [])[:8]) if c and len(c) <= 5]
                if m["type"] == "flag" and (item.get("absent_word") or "").strip():
                    m["absent"] = [[w for _, w in tokens(item["absent_word"])]]
        t["dropped_cues"] = vet_cues(t)
        t["row_ids"] = [r["id"] for r in t.pop("rows")]
    return {"version": 1, "dataset_id": ds["id"], "tables": tables, "text_ids": [x["id"] for x in texts], "llm_tables": llm_used}

"""data.json -> bộ dữ liệu dùng chung của domain ABI, để search.py của System 4 (từ khoá + nghĩa + reranker) tìm câu tự do.

Không đi qua ingest.py (đọc tệp người dùng): code tự tạo bản ghi {title, fields, text, source}, mỗi bản ghi có trường "Link"
trỏ về trang gốc trên abi.com.vn. Dựng bộ MỚI xong mới xoá bộ cũ, nên câu hỏi trong lúc đồng bộ vẫn tìm được.
Nội dung không đổi (cùng mã băm) thì bỏ qua, khỏi tạo lại vector.
Bộ dữ liệu được đánh dấu mapping.source = "abi_sync": datasets.py không xử lý lại nó như tệp tải lên.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import threading

from ..server import datasets, db, ingest, search, settings
from . import normalize, tools

log = logging.getLogger("system4.abi.index")
_lock = threading.Lock()
SOURCE = "abi_sync"
DATASET_NAME = "abi.com.vn (tự đồng bộ)"


def domain() -> dict | None:
    return db.run("SELECT * FROM domains WHERE engine='abi' ORDER BY id LIMIT 1", one=True)


def is_abi_dataset(ds: dict) -> bool:
    try:
        return json.loads(ds.get("mapping") or "{}").get("source") == SOURCE
    except ValueError:
        return False


def chunks(text: str, size: int) -> list[str]:
    """Chia theo dòng, mỗi phần <= size ký tự (dòng quá dài thì cắt theo câu)."""
    parts, cur = [], ""
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        while len(line) > size:
            cut = line.rfind(". ", 0, size)
            cut = cut + 1 if cut > size // 3 else size
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:cut].strip())
            line = line[cut:].strip()
        if cur and len(cur) + 1 + len(line) > size:
            parts.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        parts.append(cur)
    return parts


def _recs(title: str, kind: str, url: str, body: str, fields: dict | None = None, head: str = "") -> list[dict]:
    size = settings.get("CHUNK_CHARS")
    head = head or title
    fs = {"Loại": kind, **(fields or {}), "Link": url}
    pieces = chunks(body, size) or [""]
    out = []
    for i, p in enumerate(pieces, 1):
        label = f" (phần {i}/{len(pieces)})" if len(pieces) > 1 else ""
        out.append({"title": title + label, "fields": fs, "text": f"{head}\n{p}".strip(), "source": f"abi.com.vn · {kind}"})
    return out


def records(data: dict) -> list[dict]:
    out: list[dict] = []
    c = data.get("center") or {}
    contact = tools.contact(data)
    out += _recs("Thông tin liên hệ Trung tâm", "Liên hệ", c.get("url") or normalize.URL_CONTACT, contact["text"])
    out += _recs("Cơ cấu tổ chức Trung tâm", "Tổ chức", normalize.URL_ORG, tools.org_card(data))
    for x in data.get("departments") or []:
        card = tools.department_detail(data, [x], settings.get("ABI_SHOW_STAFF_CONTACT"))["text"]
        out += _recs(x["name"], "Phòng ban", x["url"], card)
    for e in data.get("events") or []:   # thẻ tĩnh: KHÔNG ghi "sắp / đã diễn ra" (đổi theo ngày hỏi, code tính lúc hỏi)
        s, en = normalize.dt(e.get("starts")), normalize.dt(e.get("ends"))
        body = "\n".join(x for x in (f"Thời gian: {tools.fmt_range(s, en)}", f"Địa điểm: {e.get('location') or 'chưa ghi'}",
                                     f"Hình thức: {e['mode']}" if e.get("mode") else "", f"Đơn vị tổ chức: {e['organizer']}" if e.get("organizer") else "",
                                     e.get("summary") or "", e.get("text") or "") if x)
        out += _recs(e["title"], "Sự kiện", e["url"], body, {"Thời gian": tools.fmt_range(s, en), "Địa điểm": e.get("location") or ""})
    for p in data.get("programs") or []:
        body = "\n".join(x for x in (p.get("summary"), p.get("text"), "Nhóm: " + ", ".join(p["categories"]) if p.get("categories") else "",
                                     f"Đơn vị tổ chức: {p['organizer']}" if p.get("organizer") else "", f"Liên hệ: {p['contact']}" if p.get("contact") else "",
                                     "\n".join(f"Văn bản: {l['label']}" for l in p.get("links") or [])) if x)
        out += _recs(p["title"], "Chương trình hỗ trợ", p["url"], body, {"Nhóm": ", ".join(p.get("categories") or [])})
    for x in data.get("catalog") or []:
        body = "\n".join(v for v in (f"{x['kind_vi']}" + (f" — nhóm: {', '.join(x['categories'])}" if x.get("categories") else ""),
                                     x.get("summary"), x.get("description"), f"Website: {x['website']}" if x.get("website") else "",
                                     f"Địa chỉ: {x['address']}" if x.get("address") else "") if v)
        out += _recs(x["name"], x["kind_vi"], x["url"], body)
    for p in data.get("posts") or []:
        if p.get("excluded"):   # bài cũ đã có dữ liệu chính thức thay / trang mẫu chưa sửa (normalize.excluded)
            continue
        day = normalize.dt(p.get("published"))
        body = "\n".join(v for v in (p.get("summary") if not (p.get("text") or "").startswith((p.get("summary") or "")[:60]) else "",
                                     p.get("text")) if v)
        out += _recs(p["title"], "Tài liệu" if p["type"] == "resource" else "Tin tức", p["url"], body or p.get("summary") or "",
                     {"Ngày đăng": day.strftime("%d/%m/%Y") if day else ""},
                     head=f"{p['title']} (đăng ngày {day:%d/%m/%Y})" if day else p["title"])
    for pg in data.get("pages") or []:
        out += _recs(pg["title"], "Trang giới thiệu", pg["url"], pg["text"])
    return [r for r in out if len(re.sub(r"\s", "", r["text"])) >= 20]


def rebuild(data: dict) -> dict:
    """Một lần dựng tại một thời điểm (lịch nền và nút "Đồng bộ ngay" có thể gọi cùng lúc)."""
    with _lock:
        return _rebuild(data)


def _rebuild(data: dict) -> dict:
    dom = domain()
    if not dom:
        raise RuntimeError("chưa có lĩnh vực ABI trong DB (db.init_db tạo khi khởi động server)")
    owner = db.run("SELECT id FROM users WHERE role='dev' ORDER BY id LIMIT 1", one=True)
    if not owner:
        raise RuntimeError("chưa có tài khoản dev để đứng tên bộ dữ liệu dùng chung (tạo tài khoản đầu tiên rồi đồng bộ lại)")
    recs = records(data)
    digest = hashlib.sha256(json.dumps(recs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    old = [d for d in db.run("SELECT * FROM datasets WHERE domain_id=?", (dom["id"],), many=True) if is_abi_dataset(d)]
    if any(d["status"] == "ready" and json.loads(d["mapping"]).get("hash") == digest for d in old):
        return {"skipped": "nội dung không đổi", "records": len(recs)}
    mapping = {"kind": "text", "source": SOURCE, "hash": digest, "reader": ingest.READER_VERSION, "synced_at": data.get("synced_at")}
    ds_id = db.create_dataset(owner["id"], DATASET_NAME, "abi.com.vn", 0, dom["id"])
    db.update_dataset(ds_id, status="processing", active=0, kind="text", progress=5, mapping=json.dumps(mapping, ensure_ascii=False),
                      message="Đang tạo chỉ mục từ dữ liệu abi.com.vn…")
    try:
        ids = db.insert_records(ds_id, recs)
        for i in range(0, len(recs), datasets.EMBED_BATCH):
            batch = recs[i:i + datasets.EMBED_BATCH]
            search.add_vectors(ids[i:i + datasets.EMBED_BATCH], search.embed([r["text"] for r in batch]), ds_id, owner["id"])
            db.update_dataset(ds_id, progress=10 + int(88 * min(len(recs), i + datasets.EMBED_BATCH) / len(recs)))
    except Exception:
        datasets.delete(db.get_dataset(ds_id))
        raise
    s = normalize.dt(data.get("synced_at"))
    db.update_dataset(ds_id, status="ready", progress=100, n_records=len(recs), active=1,
                      message=f"{len(recs)} đoạn từ abi.com.vn, đồng bộ lúc {tools.fmt_dt(s)}. Tự cập nhật, không cần tải lên.")
    for d in old:
        datasets.delete(d)
    return {"dataset_id": ds_id, "records": len(recs), "replaced": [d["id"] for d in old]}

"""Phiên bản dữ liệu ABI -> bộ dữ liệu dùng chung của domain ABI, để search.py (từ khoá + nghĩa + reranker) tìm câu tự do.

MỖI PHIÊN BẢN có một bộ dữ liệu riêng (mapping.abi_version = id phiên bản); chỉ bộ của phiên bản đang dùng được bật,
nên chuyển phiên bản = bật / tắt bộ dữ liệu, tức thì, không phải tạo lại vector.
Không đi qua ingest.py: code tự tạo bản ghi {title, fields, text, source}, mỗi bản ghi có trường "Link" về trang gốc.
Vector của đoạn văn đã có ở phiên bản khác được DÙNG LẠI (chép từ Qdrant), chỉ tạo vector cho đoạn mới -> phiên bản mới
thường chỉ mất vài giây. Bộ dữ liệu đánh dấu mapping.source = "abi_sync": datasets.py không xử lý lại như tệp tải lên.
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
    out += _recs("Thông tin liên hệ Trung tâm", "Liên hệ", c.get("url") or normalize.link(data, normalize.P_CONTACT), contact["text"])
    out += _recs("Cơ cấu tổ chức Trung tâm", "Tổ chức", normalize.link(data, normalize.P_ORG), tools.org_card(data))
    for x in data.get("departments") or []:
        card = tools.department_detail(data, [x])["text"]
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


def _mapping(ds: dict) -> dict:
    try:
        return json.loads(ds.get("mapping") or "{}")
    except ValueError:
        return {}


def abi_datasets() -> list[dict]:
    dom = domain()
    return [d for d in db.run("SELECT * FROM datasets WHERE domain_id=?", (dom["id"],), many=True) if is_abi_dataset(d)] if dom else []


def dataset_of(vid: int) -> dict | None:
    return next((d for d in abi_datasets() if _mapping(d).get("abi_version") == vid), None)


def adopt_legacy(active_vid: int | None) -> None:
    """Bộ dữ liệu ABI dựng trước khi có phiên bản (không có abi_version): gán cho phiên bản đang dùng (chính là bản cũ được
    chuyển thành phiên bản 1); thừa thì xoá."""
    for d in abi_datasets():
        m = _mapping(d)
        if "abi_version" in m:
            continue
        if active_vid and not dataset_of(active_vid) and d["status"] == "ready":
            m["abi_version"] = active_vid
            db.update_dataset(d["id"], mapping=json.dumps(m, ensure_ascii=False), active=1)
        else:
            datasets.delete(d)


def set_active(vid: int | None) -> None:
    """Chỉ bộ dữ liệu của phiên bản vid được bật."""
    for d in abi_datasets():
        on = 1 if vid is not None and _mapping(d).get("abi_version") == vid and d["status"] == "ready" else 0
        if d["active"] != on:
            db.update_dataset(d["id"], active=on)


def drop(vid: int) -> None:
    for d in abi_datasets():
        if _mapping(d).get("abi_version") == vid:
            datasets.delete(d)


def _reuse_vectors(texts: list[str], exclude_ds: int) -> dict[str, list[float]]:
    """Vector của các đoạn có ĐÚNG chữ này trong bộ dữ liệu ABI khác (đã tạo trước) -> khỏi gọi bge-m3 lại."""
    others = [d["id"] for d in abi_datasets() if d["id"] != exclude_ds and d["status"] == "ready"]
    if not others:
        return {}
    marks = ",".join("?" * len(others))
    want = set(texts)
    by_text: dict[str, int] = {}
    for r in db.run(f"SELECT id, text FROM records WHERE dataset_id IN ({marks})", tuple(others), many=True):
        if r["text"] in want:
            by_text.setdefault(r["text"], r["id"])
    if not by_text:
        return {}
    q = search._qdrant()
    ids, out = list(by_text.values()), {}
    vec_of: dict[int, list[float]] = {}
    for i in range(0, len(ids), 256):
        with search._qlock:
            for pt in q.retrieve(search.COLLECTION, ids=ids[i:i + 256], with_vectors=True):
                vec_of[int(pt.id)] = list(pt.vector)
    for t, rid in by_text.items():
        if rid in vec_of:
            out[t] = vec_of[rid]
    return out


def build(vid: int, data: dict, label: str) -> dict:
    """Dựng bộ dữ liệu tìm kiếm cho phiên bản vid (có rồi thì thôi). Một lần dựng tại một thời điểm."""
    with _lock:
        return _build(vid, data, label)


def _build(vid: int, data: dict, label: str) -> dict:
    from . import store
    dom = domain()
    if not dom:
        raise RuntimeError("chưa có lĩnh vực ABI trong DB (db.init_db tạo khi khởi động server)")
    owner = db.run("SELECT id FROM users WHERE role='dev' ORDER BY id LIMIT 1", one=True)
    if not owner:
        raise RuntimeError("chưa có tài khoản dev để đứng tên bộ dữ liệu dùng chung (tạo tài khoản đầu tiên rồi đồng bộ lại)")
    have = dataset_of(vid)
    if have and have["status"] == "ready":
        return {"skipped": "đã có chỉ mục", "dataset_id": have["id"], "records": have["n_records"]}
    if have:   # dựng dở (tắt server giữa chừng): làm lại
        datasets.delete(have)
    recs = records(data)
    digest = hashlib.sha256(json.dumps(recs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    s = normalize.dt(data.get("synced_at"))
    mapping = {"kind": "text", "source": SOURCE, "abi_version": vid, "abi_source": data.get("source") or "prod",
               "hash": digest, "reader": ingest.READER_VERSION, "synced_at": data.get("synced_at")}
    ds_id = db.create_dataset(owner["id"], f"{label} · phiên bản {vid} · {tools.fmt_dt(s)}", label, 0, dom["id"])
    db.update_dataset(ds_id, status="processing", active=0, kind="text", progress=5, mapping=json.dumps(mapping, ensure_ascii=False),
                      message=f"Đang tạo chỉ mục cho phiên bản {vid}…")
    reused = 0
    try:
        ids = db.insert_records(ds_id, recs)
        cache = _reuse_vectors([r["text"] for r in recs], ds_id)
        for i in range(0, len(recs), datasets.EMBED_BATCH):
            batch, bids = recs[i:i + datasets.EMBED_BATCH], ids[i:i + datasets.EMBED_BATCH]
            todo = [k for k, r in enumerate(batch) if r["text"] not in cache]
            if todo:
                from core import gpu
                with gpu.slot(gpu.P3):   # G3.1: dựng chỉ mục ABI nhường câu hỏi đang chờ
                    new = search.embed([batch[k]["text"] for k in todo])
            else:
                new = []
            vecs, it = [], iter(new)
            for k, r in enumerate(batch):
                vecs.append(cache[r["text"]] if r["text"] in cache else next(it))
            reused += len(batch) - len(todo)
            search.add_vectors(bids, vecs, ds_id, owner["id"])
            db.update_dataset(ds_id, progress=10 + int(88 * min(len(recs), i + datasets.EMBED_BATCH) / len(recs)))
    except Exception:
        datasets.delete(db.get_dataset(ds_id))
        raise
    db.update_dataset(ds_id, status="ready", progress=100, n_records=len(recs), active=1 if store.active_id() == vid else 0,
                      message=f"{len(recs)} đoạn, phiên bản {vid} ({label}, đồng bộ lúc {tools.fmt_dt(s)}). Tự đồng bộ, không cần tải lên.")
    return {"dataset_id": ds_id, "records": len(recs), "reused_vectors": reused}

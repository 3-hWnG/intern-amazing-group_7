"""Đường nhanh (fast path) cho chế độ Chuyên gia: biên dịch dữ liệu lúc nạp, trả lời bằng code lúc hỏi, tự kiểm để biết lúc nào nhường.

  build(ds_id)      biên dịch (compile.py) + tự kiểm (selftest.py) -> bảng `fastpath` (spec, report). Chạy nền sau khi nạp tệp xong.
  answer(...)       chat.py gọi TRƯỚC bước tìm kiếm: trả kết quả code (answer / ask / refuse) hoặc None = đi đường cũ.
  state_from(path)  dòng dữ liệu của lượt trước (để hiểu câu nối tiếp), lấy từ meta của câu trả lời trước (đường nhanh hoặc nguồn [n] duy nhất).
Không đụng lĩnh vực Thủ tục (System 3) và ABI (bộ dữ liệu đồng bộ tự động bỏ qua).
"""
from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time

from fastapi import APIRouter, HTTPException, Request

from .. import db, settings
from . import compile as C
from . import selftest
from .engine import Engine

log = logging.getLogger("system4.fastpath")
_jobs: "queue.Queue[int]" = queue.Queue()
_worker: threading.Thread | None = None
_cache: dict = {}
_lock = threading.Lock()
_build_lock = threading.Lock()   # một engine dựng một lần: luồng dựng sẵn và câu hỏi đầu tiên không cùng dựng


def _is_synced(ds: dict) -> bool:
    return '"source": "abi_sync"' in (ds.get("mapping") or "")


def get(ds_id: int) -> dict | None:
    r = db.run("SELECT * FROM fastpath WHERE dataset_id=?", (ds_id,), one=True)
    if not r:
        return None
    r = dict(r)
    for k in ("spec", "report"):
        try:
            r[k] = json.loads(r[k] or "{}")
        except ValueError:
            r[k] = {}
    return r


def _save(ds_id: int, **cols) -> None:
    cur = db.run("SELECT dataset_id FROM fastpath WHERE dataset_id=?", (ds_id,), one=True)
    cols = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in cols.items()}
    if cur:
        db.run(f"UPDATE fastpath SET {', '.join(k + '=?' for k in cols)}, updated_at=datetime('now') WHERE dataset_id=?", (*cols.values(), ds_id))
    else:
        db.run(f"INSERT INTO fastpath(dataset_id,{','.join(cols)}) VALUES (?{',?' * len(cols)})", (ds_id, *cols.values()))


def _evict(ds_id: int) -> None:
    """Bỏ khỏi bộ nhớ đệm các engine có bộ dữ liệu này (trước 20/10 xoá HẾT: một người nạp tệp ở lĩnh vực khác cũng làm câu FLM kế tiếp
    phải dựng lại engine)."""
    with _lock:
        for k in [k for k in _cache if any(i == ds_id for i, _ in k[-1])]:      # khoá = (cờ..., các cặp (dataset_id, updated_at)): phần tử CUỐI
            del _cache[k]


def delete(ds_id: int) -> None:
    db.run("DELETE FROM fastpath WHERE dataset_id=?", (ds_id,))
    _evict(ds_id)


def _materialize(spec: dict, with_texts: bool = True) -> tuple[list[dict], list[dict]]:
    """spec (chỉ id bản ghi) -> bảng có dòng đầy đủ + đoạn văn bản, đọc từ DB."""
    ds = db.get_dataset(spec["dataset_id"]) or {}
    ids = [i for t in spec["tables"] for i in t["row_ids"]] + (list(spec.get("text_ids", [])) if with_texts else [])
    recs = {}
    for k in range(0, len(ids), 900):
        part = ids[k:k + 900]
        for r in db.run(f"SELECT id,title,fields,text,source FROM records WHERE id IN ({','.join('?' * len(part))})", tuple(part), many=True):
            recs[r["id"]] = r
    tables = []
    for t in spec["tables"]:
        rows = [{"id": i, "title": recs[i]["title"], "fields": json.loads(recs[i]["fields"] or "{}")} for i in t["row_ids"] if i in recs]
        tables.append({**{k: v for k, v in t.items() if k != "row_ids"}, "rows": rows})
    texts = [{"id": i, "title": recs[i]["title"], "text": recs[i]["text"], "source": recs[i]["source"], "dataset_id": spec["dataset_id"],
              "dataset": ds.get("name", "")} for i in spec.get("text_ids", []) if i in recs] if with_texts else []
    return tables, texts


def _sql_chat(priority: int):
    """Hàm gọi model cho lộ trình SQL (sqlroute.py), giữ chỗ GPU chung: P1 lúc hỏi (như công cụ bảng), P3 lúc nạp (bài tự kiểm, việc nền)."""
    def call(messages, schema, timeout=60):
        from core import gpu
        from .. import llm
        with gpu.slot(priority):
            return llm.chat_json(messages, schema, timeout=timeout)
    return call


def _sql_on() -> bool:
    return bool(settings.get("FASTPATH_SQL")) or bool(settings.get("FASTPATH_SQL_RAW"))


def build(ds_id: int) -> dict | None:
    """Biên dịch + tự kiểm một bộ dữ liệu (đồng bộ; chạy trong luồng nền)."""
    ds = db.get_dataset(ds_id)
    if not ds or ds["status"] != "ready":
        return None
    if _is_synced(ds):
        _save(ds_id, status="skipped", message="Bộ dữ liệu đồng bộ của lĩnh vực ABI: dùng cách trả lời riêng của ABI.")
        return get(ds_id)
    t0 = time.perf_counter()
    _save(ds_id, status="building", message="Đang biên dịch…")
    try:
        spec = C.compile_dataset(ds)
        tables, texts = _materialize(spec)
        t1 = time.perf_counter()
        from core import gpu
        test = selftest.run(tables, texts, settings.get("FASTPATH_MIN_PASS"), sql=_sql_chat(gpu.P3) if settings.get("FASTPATH_SQL") else None)
        report = {"compile_ms": int((t1 - t0) * 1000), "selftest_ms": int((time.perf_counter() - t1) * 1000),
                  "llm_tables": spec["llm_tables"], **test}
        n_on = sum(v for e in test["enabled"].values() for v in (e.values() if isinstance(e, dict) else [e]))
        n_all = sum(len(e) if isinstance(e, dict) else 1 for e in test["enabled"].values())
        ents = [t for t in spec["tables"] if t["parent"] is None]
        msg = (f"{len(ents)} bảng, {len(spec.get('text_ids', []))} đoạn văn bản; tự kiểm: bật {n_on}/{n_all} loại câu"
               + ("" if spec["llm_tables"] else " · chỉ dùng tên cột (AI không đặt tên trường)"))
        _save(ds_id, status="ready", message=msg, spec=spec, report=report)
    except Exception as e:   # đường nhanh hỏng thì vẫn còn đường cũ: ghi lỗi, không làm hỏng bộ dữ liệu
        log.exception("fastpath %s", ds_id)
        _save(ds_id, status="error", message=f"Lỗi biên dịch: {e}")
    _evict(ds_id)
    return get(ds_id)


def enqueue(ds_id: int) -> None:
    global _worker
    if db.get_dataset(ds_id):
        _save(ds_id, status="queued", message="Đang chờ biên dịch…")
    _jobs.put(ds_id)
    if _worker is None or not _worker.is_alive():
        _worker = threading.Thread(target=_work, name="s4-fastpath", daemon=True)
        _worker.start()


def _work() -> None:
    while True:
        try:
            ds_id = _jobs.get(timeout=5)
        except queue.Empty:
            warm()   # hết việc biên dịch: dựng sẵn engine để câu hỏi đầu tiên không phải chờ
            return
        try:
            build(ds_id)
        except Exception:
            log.exception("fastpath build %s", ds_id)


def ensure_all() -> None:
    """Khởi động server: bộ dữ liệu sẵn sàng mà chưa biên dịch (dữ liệu có từ trước) hoặc biên dịch dở -> biên dịch nền."""
    have = {r["dataset_id"]: r["status"] for r in db.run("SELECT dataset_id, status FROM fastpath", many=True)}
    todo = [d["id"] for d in db.run("SELECT id FROM datasets WHERE status='ready'", many=True) if have.get(d["id"]) in (None, "queued", "building")]
    for i in todo:
        enqueue(i)
    if not todo and _warm_on():
        threading.Thread(target=warm, name="s4-fastpath-warm", daemon=True).start()


def _warm_on() -> bool:
    return os.environ.get("S4_WARMUP", "1") == "1" and bool(settings.get("FASTPATH_ENABLED"))   # test đặt S4_WARMUP=0


def warm() -> None:
    """Dựng sẵn engine cho bộ dữ liệu đang bật của từng lĩnh vực: phần dùng chung (lĩnh vực cứng, bộ dùng chung) + của tài khoản dev đầu tiên.
    Lúc khởi động và sau mỗi lần biên dịch. Đo 19/10: câu đầu tiên ở lĩnh vực FLM chờ ~12 s chỉ để dựng engine."""
    if not _warm_on():
        return
    try:
        dev = db.first_dev_id()
        sets = set()
        for dom in db.run("SELECT id FROM domains", many=True):
            for uid, role in ((-1, "nguoi_dan"), (-1, "dev"), (dev, "dev")):
                if uid is None:
                    continue
                ids = tuple(sorted(d["id"] for d in db.active_datasets(uid, dom["id"], role)))
                if ids:
                    sets.add(ids)
        for ids in sorted(sets, key=len, reverse=True)[:12]:
            t0 = time.perf_counter()
            eng, used = _engine(list(ids))
            if eng:
                log.info("fastpath warm %s: %d ms", used, int((time.perf_counter() - t0) * 1000))
    except Exception:   # dựng sẵn hỏng thì câu hỏi đầu tiên tự dựng như cũ
        log.exception("fastpath warm")


def _engine(ds_ids: list[int]) -> tuple[Engine | None, list[int]]:
    rows = [get(i) for i in ds_ids]
    ready = [r for r in rows if r and r["status"] == "ready"]
    if not ready:
        return None, []
    agg = bool(settings.get("FASTPATH_AGGREGATE"))
    sql_raw = bool(settings.get("FASTPATH_SQL_RAW"))
    key = (agg, _sql_on(), sql_raw, tuple(sorted((r["dataset_id"], r["updated_at"]) for r in ready)))
    with _lock:
        if key in _cache:
            return _cache[key], [r["dataset_id"] for r in ready]
    with _build_lock:
        with _lock:
            if key in _cache:   # luồng khác vừa dựng xong
                return _cache[key], [r["dataset_id"] for r in ready]
        tables, texts, enabled, skipped = [], [], {}, False
        for r in ready:
            on = r["report"].get("enabled", {})
            # đoạn văn bản mà tự kiểm đã tắt thì engine không dùng: không đọc, không lập chỉ mục (bộ lịch học FLM 19.242 đoạn, 19/10)
            use_text = on.get(f"text:{r['dataset_id']}", True)
            t, x = _materialize(r["spec"], with_texts=use_text)
            tables += t; texts += x
            skipped |= not use_text and bool(r["spec"].get("text_ids"))
            enabled.update(on)
        if sql_raw:      # mốc "SQL không qua biên dịch": không dùng kết quả tự kiểm của lộ trình SQL
            enabled = {k: ({**v, "sql": True} if isinstance(v, dict) else v) for k, v in enabled.items()}
        from core import gpu
        eng = Engine(tables, texts, enabled, aggregate=agg, refuse=not skipped,
                     sql=_sql_chat(gpu.P1) if _sql_on() else None, sql_compiled=not sql_raw)
        with _lock:
            if len(_cache) > 24:
                _cache.clear()
            _cache[key] = eng
    return eng, [r["dataset_id"] for r in ready]


def state_from(history_path: list[dict]) -> dict:
    """Trạng thái của lượt trước: meta.fast_path.state (đường nhanh trả lời) hoặc nguồn [n] duy nhất của đường cũ (dòng đang nói tới)."""
    for m in reversed(history_path):
        if m.get("role") != "assistant":
            continue
        meta = m.get("meta") or {}
        if (meta.get("fast_path") or {}).get("state"):
            return dict(meta["fast_path"]["state"])
        src = [s.get("record_id") for s in meta.get("sources") or [] if s.get("record_id")]
        return {"entity": src[0]} if len(src) == 1 else {}
    return {}


def answer(ds_ids: list[int], text: str, history_path: list[dict], grounded: bool, can_ask: bool) -> dict:
    """Kết quả cho chat.py: {"use": bool, "result": {...}, "trace": {...}}. use = False -> đi đường cũ (kèm lý do trong trace)."""
    t0 = time.perf_counter()
    eng, used = _engine(ds_ids)
    build_ms = round((time.perf_counter() - t0) * 1000, 2)
    if not eng:
        return {"use": False, "trace": {"reason": "chưa có bộ dữ liệu nào đã biên dịch", "datasets": len(ds_ids)}}
    state = state_from(history_path)
    r = eng.answer(text, state)
    use = r["kind"] == "answer" or (r["kind"] == "ask" and can_ask) or (r["kind"] == "refuse" and grounded)
    trace = {"kind": r["kind"], "route": r.get("route"), "table": r.get("table"), "field": r.get("field"), "reason": r.get("reason"),
             "engine_ms": r["ms"], "build_ms": build_ms, "total_ms": round((time.perf_counter() - t0) * 1000, 2), "datasets": used,
             "state_in": state, "state_out": state if use else None}
    if not use and r["kind"] in ("ask", "refuse"):
        trace["reason"] = "lĩnh vực không hỏi lại / đã hết lượt hỏi lại" if r["kind"] == "ask" else "lĩnh vực trả lời tự do: để AI trả lời"
    return {"use": use, "result": r, "trace": trace}


# ------------------------------------------------------------------ API (bảng điều khiển)
def summary(ds_id: int) -> dict:
    """Báo cáo cho bảng điều khiển: trạng thái, các bảng (kiểu cột, tên trường, gợi ý, gợi ý bị bỏ), kết quả tự kiểm."""
    r = get(ds_id)
    if not r:
        return {"status": "none", "message": "Chưa biên dịch."}
    spec, rep = r["spec"], r["report"]
    tables = []
    for t in spec.get("tables", []):
        tables.append({"key": t["key"], "name": t["name"], "title_label": t["title_label"], "rows": len(t["row_ids"]),
                       "entity_noun": t.get("entity_noun", ""), "parent": t["parent"],
                       "fields": [{"name": f, "label": m["label"], "type": m["type"], "long": m.get("long", False),
                                   "cues": [" ".join(c) for c in m["cues"]], "absent": [" ".join(c) for c in m.get("absent", [])]}
                                  for f, m in t["fields"].items()],
                       "dropped": t.get("dropped_cues", {}), "test": (rep.get("tables") or {}).get(t["key"], {}),
                       "enabled": (rep.get("enabled") or {}).get(t["key"], {})})
    text = (rep.get("tables") or {}).get(f"text:{ds_id}")
    return {"status": r["status"], "message": r["message"], "updated_at": r["updated_at"], "tables": tables,
            "texts": len(spec.get("text_ids", [])), "text_test": (text or {}).get("text"),
            "compile_ms": rep.get("compile_ms"), "selftest_ms": rep.get("selftest_ms"), "llm_tables": rep.get("llm_tables"),
            "aggregate_on": bool(settings.get("FASTPATH_AGGREGATE"))}


def make_router() -> APIRouter:
    r = APIRouter(prefix="/s4/fastpath")

    def ds_of(request: Request, ds_id: int, write: bool = False) -> dict:
        u = getattr(request.state, "user", None)
        if not u:
            raise HTTPException(401, "Cần đăng nhập")
        ds = db.get_dataset(ds_id)
        ok = ds and (db.readable_dataset(u, ds) if not write else (ds["user_id"] == u["id"] or u["role"] in db._ELEVATED))
        if not ok:
            raise HTTPException(404, "không có bộ dữ liệu này")
        return ds

    @r.get("/{ds_id}")
    def show(ds_id: int, request: Request):
        ds_of(request, ds_id)
        return summary(ds_id)

    @r.post("/{ds_id}/rebuild")
    def rebuild(ds_id: int, request: Request):
        ds = ds_of(request, ds_id, write=True)
        if ds["status"] != "ready":
            raise HTTPException(422, "Bộ dữ liệu chưa sẵn sàng")
        enqueue(ds_id)
        return summary(ds_id)

    return r

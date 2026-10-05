"""System 3 server: FastAPI + hàng đợi 1 worker + SQLite riêng."""
import sys
from pathlib import Path

if sys.platform == "win32":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # để import được package `system3` (data, retrieval)

import asyncio
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import orchestrator
from config import DEV_MODE, HOST, LLM_MODEL, PORT, WEB_DIR
from core import queue
from core.llm import warm_up
from db import store


@asynccontextmanager
async def lifespan(app):
    store.init_db()
    await queue.manager.start()
    warm = asyncio.create_task(asyncio.to_thread(warm_up))   # nạp model nền, không chặn /health
    yield
    warm.cancel()
    await queue.manager.stop()


app = FastAPI(title="System 3", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


class ChatIn(BaseModel):
    text: str
    conversation_id: str | None = None
    reply_to: int | None = None


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "templates" / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "model": LLM_MODEL, "queue_depth": queue.manager.depth, "dev": DEV_MODE}


@app.get("/conversations")
def conversations():
    return {"conversations": store.list_conversations()}


@app.get("/conversations/{cid}/messages")
def messages(cid: str):
    if not store.conversation_exists(cid):
        raise HTTPException(404, "conversation not found")
    return {"conversation_id": cid, "messages": store.get_messages(cid)}


@app.get("/conversations/{cid}/messages/{mid}/trace")
def trace(cid: str, mid: int):
    t = store.get_trace(cid, mid)
    if not t:
        raise HTTPException(404, "no trace")
    return t


@app.post("/conversations/{cid}/reset_facts")
def reset_facts(cid: str):
    if not store.conversation_exists(cid):
        raise HTTPException(404, "conversation not found")
    store.reset_session(cid)
    return {"ok": True}


@app.get("/dev/default_variants")
def dev_default_variants():
    """Dev: các nhóm thủ tục >1 biến thể + bản mặc định tự chọn, để admin duyệt (chưa có chức năng sửa)."""
    if not DEV_MODE:
        raise HTTPException(404, "not found")
    from system3.data import api as data_api
    conn = data_api.connect()
    out = []
    for g in conn.execute("SELECT DISTINCT head FROM families WHERE n_members>1 ORDER BY head").fetchall():
        vs = data_api.variants(conn, g[0])
        d = next((v for v in vs if v["default_variant"]), None)
        out.append({"head": g[0], "default": d and d["proc_id"], "variants": vs,
                    "reason": "tên ngắn nhất" + ("" if d and not d["province"] else " (mọi bản đều có tỉnh)")
                              + " — tự sinh, chưa duyệt"})
    return {"groups": out}


@app.get("/dev/variants.html")
def dev_variants_page():
    if not DEV_MODE:
        raise HTTPException(404, "not found")
    return FileResponse(WEB_DIR / "templates" / "variants.html")


@app.post("/chat")
async def chat(body: ChatIn):
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "text rỗng")
    cid = store.ensure_conversation(body.conversation_id)
    clarify = None
    if body.reply_to:
        prev = next((m for m in store.get_messages(cid) if m["id"] == body.reply_to), None)
        clarify = prev["clarify"] if prev else None
    turn = orchestrator.Turn(cid, text, body.reply_to, store.recent_history(cid),
                             store.session_facts(cid), store.shown_procedures(cid), clarify)
    store.add_message(cid, "user", text)
    store.set_title_if_new(cid, text)

    box = {}

    def job(emit):
        t0 = time.perf_counter()
        box["res"] = orchestrator.handle_turn(turn)
        box["ms"] = int((time.perf_counter() - t0) * 1000)

    try:
        j = queue.manager.submit(job)
    except queue.QueueFull as e:
        raise HTTPException(503, str(e))
    chunks = [c async for c in queue.manager.stream(j)]   # chờ worker xong
    if "res" not in box:
        raise HTTPException(500, "".join(chunks).strip() or j.error or "lỗi xử lý")

    r = box["res"]
    blocks, clar, kind = r.get("blocks", []), r.get("clarify"), r.get("kind", "answer")
    flat = "\n\n".join(f"{b.get('title', '')}\n{b['text']}".strip() for b in blocks) \
        or (clar or {}).get("question", "")
    mid = store.add_message(cid, "assistant", flat, kind, r.get("plan"),
                            {"blocks": blocks, "clarify": clar})
    if r.get("trace") is not None:
        store.add_trace(cid, mid, r["trace"], box["ms"])
    out = {"conversation_id": cid, "message_id": mid, "blocks": blocks, "clarify": clar, "kind": kind}
    if DEV_MODE:
        out["dev"] = {"plan": r.get("plan"), "trace": r.get("trace"), "total_ms": box["ms"]}
    return out


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

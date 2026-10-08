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
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import conv_export
import orchestrator
import user_memory
import os
import threading

from config import DEV_MODE, HOST, LLM_MODEL, PORT, TABLE_BUTTON, WEB_DIR
from core import queue
from core.llm import loaded_models, warm_up
from planner import hybrid
from db import store


def _llm_wanted() -> bool:
    return os.environ.get("S3_USE_LLM", "1") != "0" or hybrid.get_config()["mode"] == "hybrid"


@asynccontextmanager
async def lifespan(app):
    store.init_db()
    await queue.manager.start()
    # A17: chỉ nạp model (GPU) khi có đường LLM nào bật; S3_USE_LLM=0 và Planner luật thì không đụng GPU
    warm = asyncio.create_task(asyncio.to_thread(warm_up)) if _llm_wanted() else None   # nạp nền, không chặn /health
    yield
    if warm:
        warm.cancel()
    await queue.manager.stop()


app = FastAPI(title="System 3", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


@app.middleware("http")
async def _no_cache_static(request, call_next):
    r = await call_next(request)
    if request.url.path.startswith("/static/") or request.url.path == "/":
        r.headers["Cache-Control"] = "no-cache"   # ponytail: bản dev/nội bộ; thêm hash tên file nếu cần cache khi lên production
    return r


class ConfigIn(BaseModel):
    mode: str | None = None            # rules | hybrid
    confidence: float | None = None    # ngưỡng LLM được sửa kế hoạch
    timeout: float | None = None       # giây
    answer_llm: bool | None = None     # Answer Composer LLM bật/tắt (= S3_USE_LLM)


# FINAL-PRODUCT: [B2] GET /config không kiểm dev: ai cũng đọc được mode/model/timeout/ngưỡng. Bản cuối: người dùng thường chỉ thấy trạng thái 'AI bật/tắt' (mục 1)
@app.get("/config")
def get_config():
    """Phase 19: cấu hình Planner (UI Phase 20 dùng). loaded = model Ollama đang nạp."""
    from answer import llm_answer
    loaded = loaded_models()
    return {**hybrid.get_config(), "model": LLM_MODEL, "loaded": loaded, "model_loaded": any(LLM_MODEL == m for m in loaded),
            "dev": DEV_MODE, "modes": list(hybrid.MODES), "answer_llm": os.environ.get("S3_USE_LLM", "1") == "1",
            "answer_timeout": llm_answer.TIMEOUT, "table_button": TABLE_BUTTON}


# FINAL-PRODUCT: [B2][AI] chỉ chặn bằng DEV_MODE (403), chưa có vai trò admin; đổi cả công tắc AI của MỌI người dùng (biến môi trường của tiến trình). Bản cuối: quyền admin hoặc bỏ (mục 1, 4)
@app.post("/config")
def set_config(body: ConfigIn):
    """Đổi mode/ngưỡng/timeout TRONG BỘ NHỚ (mất khi khởi động lại; mặc định theo biến môi trường). Chỉ khi S3_DEV=1."""
    if not DEV_MODE:
        raise HTTPException(403, "chỉ khi S3_DEV=1")
    try:
        hybrid.set_config(body.mode, body.confidence, body.timeout)
        if body.answer_llm is not None:    # ponytail: đổi qua biến môi trường của tiến trình (orchestrator._answer_llm đọc mỗi lượt); mất khi khởi động lại
            os.environ["S3_USE_LLM"] = "1" if body.answer_llm else "0"
    except ValueError as e:
        raise HTTPException(422, str(e))
    if _llm_wanted():   # vừa bật LLM trong lúc chạy: nạp model nền để lượt đầu không chậm
        threading.Thread(target=warm_up, daemon=True).start()
    return get_config()


# ---- Phase 26: bộ nhớ người dùng (hồ sơ + nhớ lựa chọn MCQ), khoá theo header X-Client-Id (thiếu = 'default')
# FINAL-PRODUCT: [B4][MEM] client_id tự khai, không xác thực: mọi endpoint /memory* tin id này. Bản cuối: lấy user từ đăng nhập (mục 6)
def _cid(x_client_id: str | None = Header(None)) -> str:
    try:
        return user_memory.client_id(x_client_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


class ProfileIn(BaseModel):
    province: str | None = None
    commune: str | None = None
    user_type: str | None = None
    note: str | None = None


class McqIn(BaseModel):
    axis: str
    value: str


def _bad(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/memory")
def memory_get(cid: str = Depends(_cid)):
    return user_memory.snapshot(cid)


@app.put("/memory/profile")
@app.post("/memory/profile")
def memory_profile(body: ProfileIn, cid: str = Depends(_cid)):
    """Chỉ các trường có trong yêu cầu được đổi; chuỗi rỗng = xoá trường đó. Từ chối CCCD/SĐT."""
    _bad(user_memory.set_profile, cid, {k: getattr(body, k) for k in body.model_fields_set})
    return user_memory.snapshot(cid)


@app.post("/memory/mcq")
def memory_mcq(body: McqIn, cid: str = Depends(_cid)):
    _bad(user_memory.set_mcq, cid, body.axis, body.value)
    return user_memory.snapshot(cid)


@app.delete("/memory/mcq")
def memory_mcq_forget(axis: str, cid: str = Depends(_cid)):
    _bad(user_memory.del_mcq, cid, axis)
    return user_memory.snapshot(cid)


@app.delete("/memory")
def memory_forget_all(cid: str = Depends(_cid)):
    store.mem_del(cid)
    return user_memory.snapshot(cid)


class ChatIn(BaseModel):
    text: str
    conversation_id: str | None = None
    reply_to: int | None = None
    proc_id: str | None = None          # Phase 31: nút "dạng khác"


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "templates" / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "model": LLM_MODEL, "queue_depth": queue.manager.depth, "dev": DEV_MODE}


@app.get("/procedure/{proc_id}/table")
def procedure_table(proc_id: str):
    """Phase 20: bảng đầy đủ mọi mục của thủ tục (nguyên văn dữ liệu, không LLM). Cờ S3_TABLE_BUTTON=0 -> 404."""
    if not TABLE_BUTTON:
        raise HTTPException(404, "tính năng bảng full đang tắt")
    from answer.answerer import procedure_table as build
    from system3.data import api as data_api
    t = build(data_api.connect(), proc_id)
    if not t:
        raise HTTPException(404, "không có thủ tục này")
    return t


# FINAL-PRODUCT: [B4] liệt kê MỌI hộp thoại trong DB, chưa lọc theo người dùng (mục 3)
@app.get("/conversations")
def conversations():
    return {"conversations": store.list_conversations()}


class ConvPatch(BaseModel):
    title: str | None = None     # đổi tên
    pinned: bool | None = None   # ghim / bỏ ghim


@app.patch("/conversations/{cid}")
def patch_conversation(cid: str, body: ConvPatch):
    if not store.conversation_exists(cid):
        raise HTTPException(404, "conversation not found")
    if body.title is not None:
        store.rename_conversation(cid, body.title)
    if body.pinned is not None:
        store.set_pinned(cid, body.pinned)
    row = next(c for c in store.list_conversations() if c["id"] == cid)
    return {"ok": True, "title": row["title"], "pinned": bool(row["pinned"])}


@app.get("/conversations/{cid}/export")
def export_conversation(cid: str, format: str = "md"):
    conv = next((c for c in store.list_conversations() if c["id"] == cid), None)
    if not conv:
        raise HTTPException(404, "conversation not found")
    if format not in ("md", "json", "pdf"):
        raise HTTPException(400, "format phải là md, json hoặc pdf")
    msgs = store.get_messages(cid)
    if format == "pdf":   # trang in được, trình duyệt tự mở hộp thoại in -> Lưu thành PDF
        return Response(conv_export.to_print_html(conv, msgs), media_type="text/html; charset=utf-8")
    body = conv_export.to_markdown(conv, msgs) if format == "md" else conv_export.to_json(conv, msgs)
    fn = conv_export.filename(conv["title"], format)
    mime = "text/markdown" if format == "md" else "application/json"
    return Response(body, media_type=f"{mime}; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{fn}"'})


@app.delete("/conversations/{cid}")
def delete_conversation(cid: str):
    if not store.conversation_exists(cid):
        raise HTTPException(404, "conversation not found")
    store.delete_conversation(cid)
    return {"ok": True}


# FINAL-PRODUCT: [B4] 'Xoá tất cả' xoá hộp thoại của MỌI người (DELETE FROM conversations không điều kiện). Bản cuối: chỉ xoá hộp thoại của người gọi (mục 3)
@app.delete("/conversations")
def delete_all_conversations():
    store.delete_conversation(None)   # ponytail: ẩn danh, mọi người cùng DB; thêm lọc theo user khi có đăng nhập
    return {"ok": True}


# FINAL-PRODUCT: [B2][B3] trả `plan` của từng tin trợ lý cả khi không dev, và `content` chưa che PII; chưa kiểm cid thuộc người gọi (mục 1, 2, 3)
@app.get("/conversations/{cid}/messages")
def messages(cid: str):
    if not store.conversation_exists(cid):
        raise HTTPException(404, "conversation not found")
    return {"conversation_id": cid, "messages": store.get_messages(cid)}


# FINAL-PRODUCT: [B2][B4] trace không kiểm DEV_MODE lẫn chủ sở hữu hộp thoại. Bản cuối: chỉ dev (mục 1, 3)
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
    # Lỗi Phase 20: tin trợ lý cuối vẫn mang danh sách đánh số cũ -> "cái thứ nhất" trỏ lại thủ tục cũ. Chèn tin thông báo làm tin cuối.
    store.add_message(cid, "assistant", "Đã bắt đầu chủ đề mới. Bạn muốn hỏi về thủ tục nào?", "chitchat")
    return {"ok": True}


# FINAL-PRODUCT: [B2] /dev/* đã chặn bằng DEV_MODE (404); giữ khi tách chế độ (mục 1)
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
async def chat(body: ChatIn, cid_mem: str = Depends(_cid)):
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "text rỗng")
    # FINAL-PRODUCT: [B4] phiên ẩn danh: id hộp thoại do client giữ ở localStorage, không có chủ sở hữu/đăng nhập (mục 3)
    cid = store.ensure_conversation(body.conversation_id)
    clarify = None
    if body.reply_to:
        prev = next((m for m in store.get_messages(cid) if m["id"] == body.reply_to), None)
        clarify = prev["clarify"] if prev else None
    turn = orchestrator.Turn(cid, text, body.reply_to, store.recent_history(cid),
                             store.session_facts(cid), store.shown_procedures(cid), clarify,
                             pick_proc=body.proc_id, memory=user_memory.for_policy(cid_mem))
    # FINAL-PRODUCT: [B3] lưu nguyên văn người dùng gõ (chưa che CCCD/SĐT) vào messages.content; title hộp thoại cũng lấy 60 ký tự đầu. Bản cuối: che PII trước khi ghi (mục 2)
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
    flat = orchestrator.flat_text({"blocks": blocks, "clarify": clar})   # thẻ hỏi lại kèm danh sách đánh số để "cái thứ hai" trỏ đúng
    # FINAL-PRODUCT: [B2][B3] plan_json lưu cả plan của lượt; xem store.add_message (mục 1, 2)
    mid = store.add_message(cid, "assistant", flat, kind, r.get("plan"),
                            {"blocks": blocks, "clarify": clar})
    if r.get("trace") is not None:
        store.add_trace(cid, mid, r["trace"], box["ms"])
    out = {"conversation_id": cid, "message_id": mid, "blocks": blocks, "clarify": clar, "kind": kind}
    if r.get("memory_suggest"):            # Phase 26: UI hỏi "Nhớ đối tượng ...?"
        out["memory_suggest"] = r["memory_suggest"]
    # FINAL-PRODUCT: [B2] khối dev (plan, trace, total_ms) theo DEV_MODE toàn cục; bản cuối theo vai trò người gọi (mục 1)
    if DEV_MODE:
        out["dev"] = {"plan": r.get("plan"), "trace": r.get("trace"), "total_ms": box["ms"]}
    return out


# System 4 (Friendly mode + đăng nhập, hệ thống song song; xem system4/README.md). Launch web.bat bật S4_ENABLED=1;
# không đặt hoặc S4_ENABLED=0 -> web System 3 y như trước (các test của System 3 chạy ở chế độ này).
if os.environ.get("S4_ENABLED", "0") == "1":
    from system3.system4.server.hook import install as _s4_install
    _s4_install(app, store)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

"""API của System 4, tất cả nằm dưới /s4. Middleware ở hook.py đã kiểm đăng nhập và gắn request.state.user."""
from __future__ import annotations
import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel

from . import auth, chat as chat_turn, config, datasets, db, export, memory, search, settings


class Credentials(BaseModel):
    username: str = ""
    password: str = ""
    password2: str | None = None


class ChatIn(BaseModel):
    text: str = ""
    conversation_id: str | None = None
    edit_of: int | None = None          # sửa tin người dùng này -> phiên bản mới
    regenerate_of: int | None = None    # tạo lại câu trả lời này -> phiên bản mới
    mode: str | None = None             # fast | think; trống = DEFAULT_ANSWER_MODE


class SwitchIn(BaseModel):
    message_id: int


class FeedbackIn(BaseModel):
    value: int   # 1 | -1 | 0


class HeaderRowIn(BaseModel):
    part: str   # tên phần trong "Cách đọc" (trang tính, hoặc "trang tính · bảng 2")
    row: int    # số dòng trong trang tính; 0 = tự đoán


class DatasetPatch(BaseModel):
    active: bool | None = None
    name: str | None = None


class MemoryModeIn(BaseModel):
    mode: str   # auto | explicit


class ConvPatch(BaseModel):
    title: str | None = None
    pinned: bool | None = None


class SettingsIn(BaseModel):
    values: dict = {}


class ResetIn(BaseModel):
    keys: list[str] = []


def _user(request: Request) -> dict:
    u = getattr(request.state, "user", None)
    if not u:
        raise HTTPException(401, "Cần đăng nhập")
    return u


def _dev(request: Request) -> dict:
    u = _user(request)
    if u["role"] != "dev":
        raise HTTPException(403, "Chỉ tài khoản dev được dùng chức năng này")
    return u


def make_router(s3_store, strict_list, drop_strict) -> APIRouter:
    """s3_store = module db.store của System 3 (chỉ gọi hàm có sẵn, không sửa); strict_list(user), drop_strict(cid) từ hook.py."""
    r = APIRouter(prefix="/s4")

    def own_friendly(request: Request, cid: str, read: bool = False) -> dict:
        """Chủ hội thoại. read=True: dev cũng được XEM (bộ công cụ dev, 1C) — không được sửa."""
        u = _user(request)
        conv = db.get_conversation(cid)
        if not conv or (db.friendly_owner(cid) != u["id"] and not (read and u["role"] == "dev")):
            raise HTTPException(404, "conversation not found")
        return conv

    # ------------------------------------------------------------ trang
    @r.get("/login")
    def login_page(request: Request):
        if auth.user_from_cookie(request.cookies.get(auth.COOKIE)):
            return RedirectResponse("/", 303)
        return FileResponse(config.WEB_DIR / "templates" / "login.html", headers={"Cache-Control": "no-cache"})

    @r.get("/public")
    def public(request: Request):
        """Cấu hình cho giao diện (không cần đăng nhập)."""
        u = auth.user_from_cookie(request.cookies.get(auth.COOKIE))
        return {"app_title": settings.get("APP_TITLE"), "default_mode": settings.get("DEFAULT_MODE"),
                "signup_open": auth.signup_open(), "first_account": db.count_users() == 0,
                "min_password_length": settings.get("MIN_PASSWORD_LENGTH"),
                "friendly_model": settings.get("FRIENDLY_MODEL"), "default_answer_mode": settings.get("DEFAULT_ANSWER_MODE"),
                "user": u}

    # ------------------------------------------------------- đăng nhập
    def _login_response(u: dict) -> JSONResponse:
        token, age = auth.new_session(u["id"])
        resp = JSONResponse({"user": {"id": u["id"], "username": u["username"], "role": u["role"]}})
        auth.set_cookie(resp, token, age)
        return resp

    @r.post("/auth/signup")
    def signup(body: Credentials):
        if not auth.signup_open():
            raise HTTPException(403, "Đăng ký tài khoản mới đang tắt. Liên hệ quản trị viên.")
        name = body.username.strip()
        if body.password2 is not None and body.password2 != body.password:
            raise HTTPException(422, "Hai mật khẩu không khớp")
        err = auth.check_new_account(name, body.password)
        if err:
            raise HTTPException(422, err)
        try:
            u = db.create_user(name, auth.hash_password(body.password))
        except Exception:   # trùng tên do hai người đăng ký cùng lúc
            raise HTTPException(422, "Tên đăng nhập đã có người dùng") from None
        return _login_response(u)

    @r.post("/auth/login")
    def login(body: Credentials):
        u = auth.verify(body.username.strip(), body.password)
        if not u:
            raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")
        if u["disabled"]:
            raise HTTPException(403, "Tài khoản đã bị khoá")
        return _login_response(u)

    @r.post("/auth/logout")
    def logout(request: Request):
        auth.end_session(request.cookies.get(auth.COOKIE))
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(auth.COOKIE, path="/")
        return resp

    @r.get("/auth/me")
    def me(request: Request):
        return {"user": _user(request)}

    # ------------------------------------- danh sách chung (Strict + Friendly)
    @r.get("/conversations")
    def conversations(request: Request):
        u = _user(request)
        rows = [{**c, "mode": "strict"} for c in strict_list(u)] + \
               [{**c, "mode": "friendly"} for c in db.list_conversations(u["id"])]
        rows.sort(key=lambda c: c["created_at"], reverse=True)
        rows.sort(key=lambda c: c["pinned"], reverse=True)   # sort ổn định: ghim lên đầu, trong nhóm mới nhất trước
        return {"conversations": rows}

    @r.delete("/conversations")
    def delete_all(request: Request):
        u = _user(request)
        for c in strict_list(u):
            drop_strict(c["id"])
        for c in db.list_conversations(u["id"]):
            db.delete_conversation(c["id"])
        return {"ok": True}

    # ------------------------------------------------ hội thoại Friendly
    @r.get("/conversations/{cid}/messages")
    def messages(cid: str, request: Request):
        own_friendly(request, cid, read=True)
        return {"conversation_id": cid, "messages": db.get_path(cid)}

    def own_message(request: Request, cid: str, mid: int) -> dict:
        own_friendly(request, cid)
        m = db.get_message(mid)
        if not m or m["conversation_id"] != cid:
            raise HTTPException(404, "message not found")
        return m

    @r.post("/conversations/{cid}/switch")
    def switch(cid: str, body: SwitchIn, request: Request):
        """Chuyển sang phiên bản khác (‹ 1/2 ›): đi theo nhánh mới nhất dưới tin được chọn."""
        own_message(request, cid, body.message_id)
        db.set_leaf(cid, db.deepest_leaf(cid, body.message_id))
        return {"conversation_id": cid, "messages": db.get_path(cid)}

    @r.post("/conversations/{cid}/messages/{mid}/feedback")
    def feedback(cid: str, mid: int, body: FeedbackIn, request: Request):
        m = own_message(request, cid, mid)
        if m["role"] != "assistant" or body.value not in (-1, 0, 1):
            raise HTTPException(422, "chỉ đánh giá câu trả lời của AI, giá trị 1/-1/0")
        db.set_feedback(mid, body.value)
        return {"ok": True}

    @r.patch("/conversations/{cid}")
    def patch(cid: str, body: ConvPatch, request: Request):
        own_friendly(request, cid)
        if body.title is not None:
            db.rename_conversation(cid, body.title)
        if body.pinned is not None:
            db.set_pinned(cid, body.pinned)
        c = db.get_conversation(cid)
        return {"ok": True, "title": c["title"], "pinned": bool(c["pinned"])}

    @r.delete("/conversations/{cid}")
    def delete(cid: str, request: Request):
        own_friendly(request, cid)
        db.delete_conversation(cid)
        return {"ok": True}

    @r.get("/conversations/{cid}/export")
    def export_conv(cid: str, request: Request, format: str = "md"):
        conv = own_friendly(request, cid)
        if format not in ("md", "json", "pdf"):
            raise HTTPException(400, "format phải là md, json hoặc pdf")
        msgs = db.get_path(cid)
        if format == "pdf":
            return Response(export.to_print_html(conv, msgs), media_type="text/html; charset=utf-8")
        body = export.to_markdown(conv, msgs) if format == "md" else export.to_json(conv, msgs)
        mime = "text/markdown" if format == "md" else "application/json"
        return Response(body, media_type=f"{mime}; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{export.filename(conv["title"], format)}"'})

    @r.post("/chat")
    async def chat(body: ChatIn, request: Request):
        """Một lượt Friendly, trả về luồng SSE (xem chat.py). Ba kiểu: tin mới / sửa tin (edit_of) / tạo lại (regenerate_of)."""
        u = _user(request)
        cid = body.conversation_id
        if body.regenerate_of or body.edit_of:
            if not cid:
                raise HTTPException(422, "thiếu conversation_id")
            own_friendly(request, cid)
        elif cid:
            own_friendly(request, cid)
        if body.regenerate_of:
            m = own_message(request, cid, body.regenerate_of)
            if m["role"] != "assistant" or not m["parent_id"]:
                raise HTTPException(422, "chỉ tạo lại được câu trả lời của AI")
            user_msg = db.get_message(m["parent_id"])
            text, user_mid = user_msg["content"], user_msg["id"]
            db.set_leaf(cid, user_mid)
        else:
            text = body.text.strip()
            if not text:
                raise HTTPException(422, "text rỗng")
            if body.edit_of:
                m = own_message(request, cid, body.edit_of)
                if m["role"] != "user":
                    raise HTTPException(422, "chỉ sửa được tin của người dùng")
                parent = m["parent_id"]
            else:
                if not cid:
                    cid = db.create_conversation(u["id"])
                parent = db.current_leaf(cid)
            user_mid = db.add_message(cid, "user", text, "done", parent)
            db.set_title_if_new(cid, text)
        history = db.get_path(cid)[:-1]   # nhánh tới trước tin người dùng
        mode = body.mode if body.mode in ("fast", "think") else settings.get("DEFAULT_ANSWER_MODE")
        return StreamingResponse(chat_turn.run(u, cid, user_mid, text, history, mode), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @r.post("/turns/{turn_id}/fast")
    def answer_fast(turn_id: str, request: Request):
        """Nút "Trả lời nhanh": dừng suy nghĩ của lượt đang chạy, trả lời ngay bằng chế độ Nhanh."""
        if not chat_turn.interrupt(turn_id, _user(request)["id"]):
            raise HTTPException(404, "lượt trả lời không còn chạy")
        return {"ok": True}

    # ------------------------------------------------ dữ liệu người dùng (NV3)
    def own_dataset(request: Request, ds_id: int) -> dict:
        """Chủ dataset, hoặc dev (2B: dev được mở nội dung)."""
        u = _user(request)
        ds = db.get_dataset(ds_id)
        if not ds or (ds["user_id"] != u["id"] and u["role"] != "dev"):
            raise HTTPException(404, "không có bộ dữ liệu này")
        return ds

    def ds_view(d: dict) -> dict:
        try:
            mapping = json.loads(d.get("mapping") or "{}")
        except ValueError:
            mapping = {}
        return {k: d[k] for k in ("id", "user_id", "name", "filename", "size_bytes", "kind", "status", "progress", "message",
                                  "n_records", "created_at")} | {"active": bool(d["active"]), "mapping": mapping,
                                                                  "username": d.get("username")}

    @r.get("/datasets")
    def list_datasets(request: Request):
        u = _user(request)
        return {"datasets": [ds_view(d) for d in db.list_datasets(u["id"])], "quota": datasets.quota(u),
                "active": datasets.active_summary(u["id"]), "formats": sorted(datasets.ingest.SUPPORTED)}

    @r.post("/datasets")
    async def upload_dataset(request: Request):
        u = _user(request)
        form = await request.form()
        f = form.get("file")
        if f is None or not getattr(f, "filename", None):
            raise HTTPException(422, "Chưa chọn tệp")
        try:
            d = await asyncio.to_thread(datasets.save_upload, u, f.filename, f.file)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        finally:
            await f.close()
        return {"dataset": ds_view({**d, "username": u["username"]}), "active": datasets.active_summary(u["id"])}

    @r.patch("/datasets/{ds_id}")
    def patch_dataset(ds_id: int, body: DatasetPatch, request: Request):
        ds = own_dataset(request, ds_id)
        if body.name is not None and body.name.strip():
            db.update_dataset(ds_id, name=body.name.strip()[:120])
        if body.active is not None:
            if body.active and not ds["active"]:
                err = datasets.can_activate(ds["user_id"], ds)
                if err:
                    raise HTTPException(422, err)
            db.update_dataset(ds_id, active=1 if body.active else 0)
        return {"dataset": ds_view(db.get_dataset(ds_id) | {"username": None}), "active": datasets.active_summary(ds["user_id"])}

    @r.delete("/datasets/{ds_id}")
    def delete_dataset(ds_id: int, request: Request):
        ds = own_dataset(request, ds_id)
        datasets.delete(ds)
        return {"ok": True, "active": datasets.active_summary(ds["user_id"])}

    @r.post("/datasets/{ds_id}/retry")
    def retry_dataset(ds_id: int, request: Request):
        ds = own_dataset(request, ds_id)
        db.update_dataset(ds_id, status="queued", progress=0, message="Đang chờ xử lý lại…")
        datasets.enqueue(ds["id"])
        return {"ok": True}

    @r.post("/datasets/{ds_id}/header")
    def set_header_row(ds_id: int, body: HeaderRowIn, request: Request):
        """"Cách đọc": người dùng chọn lại dòng tiêu đề cột cho một bảng (0 = để hệ thống tự đoán) -> xử lý lại tệp."""
        ds = own_dataset(request, ds_id)
        try:
            mapping = json.loads(ds.get("mapping") or "{}")
        except ValueError:
            mapping = {}
        ov = dict(mapping.get("overrides") or {})
        if body.row > 0:
            ov[body.part] = body.row
        else:
            ov.pop(body.part, None)
        mapping["overrides"] = ov
        db.update_dataset(ds_id, mapping=json.dumps(mapping, ensure_ascii=False), status="queued", progress=0,
                          message="Đang chờ xử lý lại với dòng tiêu đề đã chọn…")
        datasets.enqueue(ds["id"])
        return {"ok": True}

    @r.get("/datasets/{ds_id}/records")
    def dataset_records(ds_id: int, request: Request, q: str = "", offset: int = 0, limit: int = 50):
        own_dataset(request, ds_id)
        rows, total = db.browse_records(ds_id, q.strip(), max(0, offset), min(max(1, limit), 200))
        return {"records": rows, "total": total}

    @r.get("/datasets/{ds_id}/reading")
    def dataset_reading(ds_id: int, request: Request):
        """"Xem cách đọc tệp": dòng tiêu đề đã chọn, cột tiêu đề, các trường, vài bản ghi đầu đúng như AI thấy."""
        ds = own_dataset(request, ds_id)
        rows, total = db.browse_records(ds_id, "", 0, 5)
        return {"dataset": ds_view(ds | {"username": None}), "first": rows, "total": total}

    # ------------------------------------------------ bộ công cụ dev: "🔍 Soi" / "Vì sao?"
    @r.get("/trace/{mid}")
    def trace(mid: int, request: Request):
        """Dev: toàn bộ chi tiết câu trả lời Friendly (mọi người dùng, 1C). Người dùng thường: bản rút gọn "Vì sao?" của mình."""
        u = _user(request)
        m = db.get_message(mid)
        if not m or m["role"] != "assistant":
            raise HTTPException(404, "không có câu trả lời này")
        owner = db.friendly_owner(m["conversation_id"])
        if u["role"] != "dev" and owner != u["id"]:
            raise HTTPException(404, "không có câu trả lời này")
        meta = m["meta"]
        why = {"mode": meta.get("mode"), "specialist": bool(meta.get("specialist")),
               "datasets_searched": (meta.get("retrieval") or {}).get("datasets", 0),
               "sources": meta.get("sources") or [], "consulted": meta.get("consulted") or [],
               "guard": meta.get("guard"), "interrupted": bool(meta.get("interrupted"))}
        if u["role"] != "dev":
            return {"why": why}
        return {"why": why, "trace": db.get_trace(mid), "meta": meta, "content": m["content"],
                "owner": owner, "kept": settings.get("TRACE_KEEP")}

    @r.get("/records/{rec_id}")
    def get_record(rec_id: int, request: Request):
        recs = db.get_records([rec_id])
        if not recs:
            raise HTTPException(404, "không có bản ghi này")
        ds = own_dataset(request, recs[0]["dataset_id"])
        return {"record": recs[0], "dataset": {"id": ds["id"], "name": ds["name"], "filename": ds["filename"]}}

    # -------------------------------------------------- bộ nhớ của mỗi người
    @r.get("/memory")
    def get_memory(request: Request):
        u = _user(request)
        return {"mode": memory.mode(u["id"]), "items": db.list_memories(u["id"])}

    @r.post("/memory/mode")
    def set_memory_mode(body: MemoryModeIn, request: Request):
        u = _user(request)
        if body.mode not in ("auto", "explicit"):
            raise HTTPException(422, "mode phải là auto hoặc explicit")
        db.set_memory_mode(u["id"], body.mode)
        return {"mode": body.mode, "items": db.list_memories(u["id"])}

    @r.delete("/memory/{mem_id}")
    def delete_memory(mem_id: int, request: Request):
        u = _user(request)
        db.delete_memory(u["id"], mem_id)
        return {"ok": True}

    @r.delete("/memory")
    def delete_all_memory(request: Request):
        u = _user(request)
        db.delete_memory(u["id"])
        return {"ok": True}

    # ------------------------------------------------------- cài đặt (dev)
    @r.get("/settings")
    def get_settings(request: Request):
        _dev(request)
        return {"settings": settings.describe()}

    def _apply(fn, arg):
        try:
            fn(arg)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        return {"settings": settings.describe(), "reload": True}

    @r.post("/settings")
    def save_settings(body: SettingsIn, request: Request):
        _dev(request)
        return _apply(settings.save, body.values)

    @r.post("/settings/default")
    def default_settings(body: SettingsIn, request: Request):
        _dev(request)
        return _apply(settings.set_default, body.values)

    @r.post("/settings/reset")
    def reset_settings(body: ResetIn, request: Request):
        _dev(request)
        return _apply(settings.reset, body.keys)

    return r

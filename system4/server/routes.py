"""API của System 4, tất cả nằm dưới /s4. Middleware ở hook.py đã kiểm đăng nhập và gắn request.state.user."""
from __future__ import annotations
import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel

from . import auth, config, db, export, llm, settings


class Credentials(BaseModel):
    username: str = ""
    password: str = ""
    password2: str | None = None


class ChatIn(BaseModel):
    text: str
    conversation_id: str | None = None


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


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def make_router(s3_store, strict_list) -> APIRouter:
    """s3_store = module db.store của System 3 (chỉ gọi hàm có sẵn, không sửa); strict_list(user) từ hook.py."""
    r = APIRouter(prefix="/s4")

    def own_friendly(request: Request, cid: str) -> dict:
        u = _user(request)
        conv = db.get_conversation(cid)
        if not conv or db.friendly_owner(cid) != u["id"]:
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
                "friendly_model": settings.get("FRIENDLY_MODEL"), "user": u}

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
            s3_store.delete_conversation(c["id"])
            db.forget_strict(c["id"])
        for c in db.list_conversations(u["id"]):
            db.delete_conversation(c["id"])
        return {"ok": True}

    # ------------------------------------------------ hội thoại Friendly
    @r.get("/conversations/{cid}/messages")
    def messages(cid: str, request: Request):
        own_friendly(request, cid)
        return {"conversation_id": cid, "messages": db.get_messages(cid)}

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
        msgs = db.get_messages(cid)
        if format == "pdf":
            return Response(export.to_print_html(conv, msgs), media_type="text/html; charset=utf-8")
        body = export.to_markdown(conv, msgs) if format == "md" else export.to_json(conv, msgs)
        mime = "text/markdown" if format == "md" else "application/json"
        return Response(body, media_type=f"{mime}; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{export.filename(conv["title"], format)}"'})

    @r.post("/chat")
    async def chat(body: ChatIn, request: Request):
        """Trả lời theo luồng SSE: meta -> [queue] -> start -> [thinking] -> delta... -> done | error."""
        u = _user(request)
        text = body.text.strip()
        if not text:
            raise HTTPException(422, "text rỗng")
        cid = body.conversation_id
        if cid:
            own_friendly(request, cid)
        else:
            cid = db.create_conversation(u["id"])
        n = settings.get("FRIENDLY_HISTORY_MESSAGES")
        history = [m for m in db.get_messages(cid) if m["status"] != "error" and m["content"]][-n:] if n else []
        user_mid = db.add_message(cid, "user", text)
        db.set_title_if_new(cid, text)
        msgs = [{"role": "system", "content": settings.get("FRIENDLY_SYSTEM_PROMPT")}]
        msgs += [{"role": m["role"], "content": m["content"]} for m in history]
        msgs.append({"role": "user", "content": text})

        async def gen():
            yield _sse({"type": "meta", "conversation_id": cid, "user_message_id": user_mid})
            pos = llm.queue_position()
            if pos:
                yield _sse({"type": "queue", "position": pos})
            parts, status, err, mid = [], "done", None, None
            try:
                async with llm.Turn():
                    yield _sse({"type": "start"})
                    async for t in llm.stream_chat(msgs):
                        if t is llm.THINKING:
                            yield _sse({"type": "thinking"})
                            continue
                        parts.append(t)
                        yield _sse({"type": "delta", "text": t})
            except (llm.QueueFull, llm.LLMError) as e:
                status, err = "error", str(e)
            except (asyncio.CancelledError, GeneratorExit):
                status = "stopped"   # người dùng rời trang/bấm dừng: giữ phần đã sinh
                raise
            finally:
                content = "".join(parts)
                if "</think>" in content:   # model suy nghĩ nhưng FRIENDLY_THINK tắt: không lưu phần suy nghĩ
                    content = content.split("</think>", 1)[1].strip()
                if content or err:
                    mid = db.add_message(cid, "assistant", content or err, status)
            yield _sse({"type": "error", "message": err, "message_id": mid} if err else {"type": "done", "message_id": mid})

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

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

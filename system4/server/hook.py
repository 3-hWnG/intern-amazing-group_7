"""Cắm System 4 vào server System 3 (gọi từ server/main.py khi S4_ENABLED=1).

install(app, s3_store) thêm:
  - API /s4/* và tệp tĩnh /s4/static
  - cổng đăng nhập cho CẢ web (1B): chưa đăng nhập -> trang /s4/login (trang) hoặc 401 (API)
  - trang "/" = trang chung Strict + Friendly (bản sao giao diện System 3, xem system4/web)
  - mỗi người chỉ thấy hội thoại Strict của mình: chặn/lọc các API /conversations, /chat của System 3
    ở lớp middleware; code và DB của System 3 giữ nguyên.
"""
from __future__ import annotations
import json
import os
import re
import threading

from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import admin, auth, config, datasets, db, routes, search, strict

PUBLIC = {"/s4/login", "/s4/auth/login", "/s4/auth/signup", "/s4/auth/logout", "/s4/public", "/health", "/favicon.ico"}
_CONV = re.compile(r"^/conversations/([^/]+)")


def install(app, s3_store) -> None:
    db.init_db()
    datasets.resume_unfinished()   # tệp đang nạp dở khi tắt server -> nạp lại
    if os.environ.get("S4_WARMUP", "1") == "1":   # test đặt S4_WARMUP=0
        threading.Thread(target=search.warm_up, name="s4-warmup", daemon=True).start()   # nạp sẵn bge-m3 + reranker
    state = {"legacy": False}

    def strict_list(user: dict) -> list[dict]:
        ids = db.strict_ids(user["id"])
        return [c for c in s3_store.list_conversations() if c["id"] in ids]

    def drop_strict(cid: str) -> None:
        """Xoá một hội thoại Strict cùng các nhánh ẩn của nó (tính năng phiên bản)."""
        for b in db.strict_branches(cid):
            s3_store.delete_conversation(b)
            db.forget_strict(b)
        s3_store.delete_conversation(cid)
        db.forget_strict(cid)

    app.include_router(routes.make_router(s3_store, strict_list, drop_strict))
    app.include_router(strict.make_router(app, s3_store))
    app.include_router(admin.make_router(s3_store))
    app.mount("/s4/static", StaticFiles(directory=str(config.WEB_DIR / "static")), name="s4_static")

    def deny(code: int, detail: str) -> JSONResponse:
        return JSONResponse({"detail": detail}, status_code=code)

    @app.middleware("http")
    async def s4_gate(request, call_next):
        path, method = request.url.path, request.method
        if path in PUBLIC or path.startswith(("/static/", "/s4/static/")):
            return await call_next(request)
        user = auth.user_from_cookie(request.cookies.get(auth.COOKIE))
        if not user:
            if method == "GET" and "text/html" in request.headers.get("accept", ""):
                return RedirectResponse("/s4/login", 303)
            return deny(401, "Cần đăng nhập")
        request.state.user = user
        if not state["legacy"]:   # lần đầu: hội thoại Strict có sẵn -> thuộc dev đầu tiên
            db.snapshot_legacy([c["id"] for c in s3_store.list_conversations()])
            state["legacy"] = True

        if path == "/":
            return FileResponse(config.WEB_DIR / "templates" / "index.html", headers={"Cache-Control": "no-cache"})
        if (path.startswith("/dev/") or (path == "/config" and method != "GET")) and user["role"] != "dev":
            return deny(403, "Chỉ tài khoản dev được dùng chức năng này")

        if path == "/conversations":   # danh sách / xoá tất cả của System 3 -> chỉ của người này
            if method == "GET":
                return JSONResponse({"conversations": strict_list(user)})
            if method == "DELETE":
                for c in strict_list(user):
                    drop_strict(c["id"])
                return JSONResponse({"ok": True})

        m = _CONV.match(path)
        if m:
            cid = m.group(1)
            if db.strict_owner(cid) != user["id"]:
                return deny(404, "conversation not found")
            if method == "DELETE" and path == f"/conversations/{cid}":
                for b in db.strict_branches(cid):   # nhánh ẩn của tính năng phiên bản
                    s3_store.delete_conversation(b)
                    db.forget_strict(b)
            resp = await call_next(request)
            if method == "DELETE" and path == f"/conversations/{cid}" and resp.status_code == 200:
                db.forget_strict(cid)
            return resp

        if path == "/chat" and method == "POST":
            try:
                cid = json.loads(await request.body() or b"{}").get("conversation_id")
            except (ValueError, AttributeError):
                cid = None
            if cid and s3_store.conversation_exists(cid) and db.strict_owner(cid) != user["id"]:
                return deny(404, "conversation not found")
            resp = await call_next(request)
            if resp.status_code != 200:
                return resp
            body = b"".join([chunk async for chunk in resp.body_iterator])
            try:
                db.set_strict_owner(json.loads(body)["conversation_id"], user["id"])
            except (ValueError, KeyError, TypeError):
                pass
            return Response(body, status_code=resp.status_code, headers=dict(resp.headers), media_type=resp.media_type)

        return await call_next(request)

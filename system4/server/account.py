"""Tài khoản & quyền riêng tư (G1.4, P04, D13): người dùng tự đổi mật khẩu, xoá hết hội thoại, xoá bộ nhớ, xem dung lượng, xoá tài khoản.

Xoá tài khoản = xoá MỌI THỨ của người đó ở cả hai hệ: hội thoại Strict (DB System 3, cả nhánh ẩn) và Friendly, bộ nhớ (Friendly +
hồ sơ Strict "u<id>"), bộ dữ liệu (bản ghi, vector, tệp), traces, phiên đăng nhập, tuỳ chọn. TRỪ các cặp hỏi–đáp đã bấm 👍/👎 trong
feedback_log: đã che CCCD/SĐT lúc ghi, được GIỮ để cải thiện hệ thống nhưng BỎ DANH TÍNH (user_id=0, conversation_id='').
Không cho xoá tài khoản dev cuối cùng đang hoạt động."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import auth, datasets, db, settings

FEEDBACK_NOTE = ("Câu hỏi và câu trả lời (đã che số giấy tờ) được giữ để cải thiện hệ thống, "
                 "kể cả khi bạn xoá tài khoản.")


def other_active_devs(uid: int) -> int:
    return db.run("SELECT COUNT(*) n FROM users WHERE role='dev' AND disabled=0 AND id<>?", (uid,), one=True)["n"]


def drop_strict_all(s3_store, uid: int) -> int:
    """Xoá mọi hội thoại Strict của một người (cả nhánh ẩn của tính năng phiên bản). Trả số hội thoại."""
    ids = db.strict_ids(uid)
    for cid in ids:
        for b in db.strict_branches(cid):
            s3_store.delete_conversation(b)
            db.forget_strict(b)
        s3_store.delete_conversation(cid)
        db.forget_strict(cid)
    return len(ids)


def drop_friendly_all(uid: int) -> int:
    n = db.run("SELECT COUNT(*) n FROM conversations WHERE user_id=?", (uid,), one=True)["n"]
    db.run("DELETE FROM traces WHERE user_id=?", (uid,))
    db.run("DELETE FROM conversations WHERE user_id=?", (uid,))   # tin nhắn xoá theo khoá ngoại
    return n


def forget_memory(s3_store, uid: int) -> None:
    db.run("DELETE FROM memories WHERE user_id=?", (uid,))
    s3_store.mem_del(f"u{uid}")   # hồ sơ Strict theo tài khoản (G1.2)


def purge_user(s3_store, uid: int) -> dict:
    """Xoá tài khoản và mọi dữ liệu của người đó; feedback_log giữ nhưng bỏ danh tính. Bên gọi kiểm quyền và 'dev cuối cùng'."""
    n_strict = drop_strict_all(s3_store, uid)
    n_friendly = drop_friendly_all(uid)
    forget_memory(s3_store, uid)
    for d in db.list_datasets(uid):
        datasets.delete(d)
    n_fb = db.run("SELECT COUNT(*) n FROM feedback_log WHERE user_id=?", (uid,), one=True)["n"]
    db.run("UPDATE feedback_log SET user_id=0, conversation_id='' WHERE user_id=?", (uid,))
    db.run("DELETE FROM traces WHERE user_id=?", (uid,))
    db.run("DELETE FROM users WHERE id=?", (uid,))   # phiên, tuỳ chọn, ghim, lĩnh vực riêng... xoá theo khoá ngoại
    return {"strict": n_strict, "friendly": n_friendly, "feedback_kept_anonymous": n_fb}


def usage(s3_store, uid: int) -> dict:
    """Dung lượng đã dùng (byte) và hạn mức; dev không giới hạn (quota None)."""
    u = db.run("SELECT role FROM users WHERE id=?", (uid,), one=True)
    parts = db.usage_parts(uid, s3_store)
    quota = None if u and u["role"] == "dev" else settings.get("USER_QUOTA_MB") * 1024 * 1024
    return {**parts, "used": sum(parts.values()), "quota": quota}


QUOTA_MESSAGE = "Đã hết dung lượng, hãy xoá bớt hội thoại hoặc dữ liệu (ô Tài khoản & quyền riêng tư)."


def over_quota(user: dict, s3_store=None) -> bool:
    """G1.7 (D12): hội thoại tính chung hạn mức USER_QUOTA_MB với dữ liệu tải lên; đầy thì từ chối lượt mới. Dev không giới hạn."""
    if user.get("role") in ("dev", "guest"):   # khách: hội thoại trong RAM, giới hạn bằng số lượt hỏi (ratelimit.py)
        return False
    return db.used_bytes(user["id"], s3_store) >= settings.get("USER_QUOTA_MB") * 1024 * 1024


class PasswordIn(BaseModel):
    old_password: str
    new_password: str


class ConfirmIn(BaseModel):
    password: str


class PrefsIn(BaseModel):
    rules_only: bool


def make_router(s3_store) -> APIRouter:
    r = APIRouter(prefix="/s4/account")

    def me(request: Request) -> dict:
        u = getattr(request.state, "user", None)
        if not u:
            raise HTTPException(401, "Cần đăng nhập")
        return u

    def check_password(u: dict, password: str) -> None:
        if not auth.verify(u["username"], password):
            raise HTTPException(403, "Mật khẩu không đúng")

    @r.get("")
    def info(request: Request):
        u = me(request)
        from core import aihealth
        return {"user": {"id": u["id"], "username": u["username"], "role": u["role"]}, "usage": usage(s3_store, u["id"]),
                "feedback_note": FEEDBACK_NOTE, "rules_only": db.get_rules_only(u["id"]), "ai": aihealth.status()}

    @r.post("/prefs")
    def prefs(body: PrefsIn, request: Request):
        """G3.3: "Chỉ trả lời bằng luật" theo tài khoản (không đổi biến môi trường của tiến trình)."""
        u = me(request)
        db.set_rules_only(u["id"], body.rules_only)
        return {"rules_only": db.get_rules_only(u["id"])}

    @r.post("/password")
    def change_password(body: PasswordIn, request: Request):
        u = me(request)
        check_password(u, body.old_password)
        n = settings.get("MIN_PASSWORD_LENGTH")
        if len(body.new_password) < n:
            raise HTTPException(422, f"Mật khẩu cần ít nhất {n} ký tự")
        if len(body.new_password.encode()) > 72:
            raise HTTPException(422, "Mật khẩu tối đa 72 byte")
        db.run("UPDATE users SET password_hash=? WHERE id=?", (auth.hash_password(body.new_password), u["id"]))
        tok = request.cookies.get(auth.COOKIE)   # đăng xuất mọi phiên khác, giữ phiên hiện tại
        keep = auth._hash_token(tok) if tok else ""
        db.run("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (u["id"], keep))
        return {"ok": True}

    @r.delete("/conversations")
    def delete_conversations(request: Request):
        u = me(request)
        return {"strict": drop_strict_all(s3_store, u["id"]), "friendly": drop_friendly_all(u["id"]),
                "usage": usage(s3_store, u["id"])}

    @r.delete("/memory")
    def delete_memory(request: Request):
        u = me(request)
        forget_memory(s3_store, u["id"])
        return {"ok": True}

    @r.delete("")
    def delete_account(body: ConfirmIn, request: Request):
        u = me(request)
        check_password(u, body.password)
        if u["role"] == "dev" and other_active_devs(u["id"]) == 0:
            raise HTTPException(422, "Đây là tài khoản dev cuối cùng: tạo hoặc mở một tài khoản dev khác trước khi xoá")
        out = purge_user(s3_store, u["id"])
        resp = JSONResponse({"ok": True, **out})
        resp.delete_cookie(auth.COOKIE, path="/")
        return resp

    return r

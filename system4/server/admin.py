"""Trang Quản trị (NV4) — chỉ dev. Ba tab: Dữ liệu Strict (thủ tục của System 3), Dữ liệu người dùng, Người dùng."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from . import auth, config, datasets, db, procs


class NewUser(BaseModel):
    username: str
    password: str
    role: str = "user"


class UserPatch(BaseModel):
    role: str | None = None
    disabled: bool | None = None
    password: str | None = None


class RecordIn(BaseModel):
    record: dict


class LabelIn(BaseModel):
    label: str = ""


class ApplyIn(BaseModel):
    version_id: int


class ScrapeIn(BaseModel):
    limit: int = 0


def make_router(s3_store) -> APIRouter:
    r = APIRouter(prefix="/s4/admin")
    state = {"procs_ready": False}

    def dev(request: Request) -> dict:
        u = getattr(request.state, "user", None)
        if not u:
            raise HTTPException(401, "Cần đăng nhập")
        if u["role"] != "dev":
            raise HTTPException(403, "Chỉ tài khoản dev được dùng trang Quản trị")
        return u

    def procs_ready():
        if not state["procs_ready"]:
            procs.init()   # lần đầu: chép dữ liệu gốc của System 3 thành phiên bản "Gốc"
            state["procs_ready"] = True

    def err(fn, *a):
        try:
            return fn(*a)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None

    @r.get("")
    def page(request: Request):
        u = getattr(request.state, "user", None)
        if not u or u["role"] != "dev":
            return RedirectResponse("/", 303)
        return FileResponse(config.WEB_DIR / "templates" / "admin.html", headers={"Cache-Control": "no-cache"})

    # ------------------------------------------------------------ người dùng
    def user_rows() -> list[dict]:
        rows = db.run("SELECT id, username, role, disabled, created_at FROM users ORDER BY id", many=True)
        for u in rows:
            u["datasets"] = db.run("SELECT COUNT(*) n, COALESCE(SUM(size_bytes),0) b FROM datasets WHERE user_id=?", (u["id"],), one=True)
            u["friendly_chats"] = db.run("SELECT COUNT(*) n FROM conversations WHERE user_id=?", (u["id"],), one=True)["n"]
            u["strict_chats"] = len(db.strict_ids(u["id"]))
            u["memories"] = db.run("SELECT COUNT(*) n FROM memories WHERE user_id=?", (u["id"],), one=True)["n"]
        return rows

    def other_active_devs(uid: int) -> int:
        return db.run("SELECT COUNT(*) n FROM users WHERE role='dev' AND disabled=0 AND id<>?", (uid,), one=True)["n"]

    @r.get("/users")
    def users(request: Request):
        dev(request)
        return {"users": user_rows()}

    @r.post("/users")
    def create_user(body: NewUser, request: Request):
        dev(request)
        if body.role not in ("dev", "user"):
            raise HTTPException(422, "Vai trò phải là dev hoặc user")
        e = auth.check_new_account(body.username.strip(), body.password)
        if e:
            raise HTTPException(422, e)
        u = db.create_user(body.username.strip(), auth.hash_password(body.password))
        if u["role"] != body.role:
            db.run("UPDATE users SET role=? WHERE id=?", (body.role, u["id"]))
        return {"users": user_rows()}

    @r.patch("/users/{uid}")
    def patch_user(uid: int, body: UserPatch, request: Request):
        me = dev(request)
        target = db.run("SELECT * FROM users WHERE id=?", (uid,), one=True)
        if not target:
            raise HTTPException(404, "không có người dùng này")
        losing_dev = target["role"] == "dev" and ((body.role and body.role != "dev") or body.disabled)
        if losing_dev and uid == me["id"]:
            raise HTTPException(422, "Không tự hạ quyền hoặc tự khoá tài khoản của mình")
        if losing_dev and other_active_devs(uid) == 0:
            raise HTTPException(422, "Phải còn ít nhất một tài khoản dev đang hoạt động")
        if body.role is not None:
            if body.role not in ("dev", "user"):
                raise HTTPException(422, "Vai trò phải là dev hoặc user")
            db.run("UPDATE users SET role=? WHERE id=?", (body.role, uid))
        if body.disabled is not None:
            db.run("UPDATE users SET disabled=? WHERE id=?", (1 if body.disabled else 0, uid))
            if body.disabled:
                db.run("DELETE FROM sessions WHERE user_id=?", (uid,))   # khoá -> đăng xuất ngay
        if body.password:
            n = auth.settings.get("MIN_PASSWORD_LENGTH")
            if len(body.password) < n or len(body.password.encode()) > 72:
                raise HTTPException(422, f"Mật khẩu cần {n}–72 ký tự")
            db.run("UPDATE users SET password_hash=? WHERE id=?", (auth.hash_password(body.password), uid))
            db.run("DELETE FROM sessions WHERE user_id=?", (uid,))
        return {"users": user_rows()}

    @r.delete("/users/{uid}")
    def delete_user(uid: int, request: Request):
        me = dev(request)
        if uid == me["id"]:
            raise HTTPException(422, "Không tự xoá tài khoản của mình")
        target = db.run("SELECT * FROM users WHERE id=?", (uid,), one=True)
        if not target:
            raise HTTPException(404, "không có người dùng này")
        if target["role"] == "dev" and other_active_devs(uid) == 0:
            raise HTTPException(422, "Phải còn ít nhất một tài khoản dev đang hoạt động")
        for cid in db.strict_ids(uid):   # hội thoại Strict nằm trong DB System 3
            for b in db.strict_branches(cid):
                s3_store.delete_conversation(b)
                db.forget_strict(b)
            s3_store.delete_conversation(cid)
            db.forget_strict(cid)
        for d in db.list_datasets(uid):
            datasets.delete(d)
        db.run("DELETE FROM users WHERE id=?", (uid,))   # phiên, hội thoại Friendly, bộ nhớ... xoá theo khoá ngoại
        return {"users": user_rows()}

    # ----------------------------------------------------- dữ liệu người dùng
    @r.get("/datasets")
    def all_datasets(request: Request):
        dev(request)
        return {"datasets": db.list_datasets(None)}

    # ----------------------------------------------------- dữ liệu Strict
    @r.get("/procs")
    def procs_state(request: Request):
        dev(request)
        procs_ready()
        ch = procs.draft_changes()
        return {"versions": procs.versions(), "active_id": procs.active_id(), "original_id": procs.original_id(),
                "draft": {"base": procs.draft_base(), "changes": len(ch),
                          "deleted": sum(1 for v in ch.values() if v is None)}, "job": procs.job()}

    @r.get("/procs/records")
    def procs_records(request: Request, version: str = "draft", q: str = "", offset: int = 0, limit: int = 50):
        dev(request)
        procs_ready()
        recs, _, ch = err(procs.view, version)
        ql = q.strip().lower()
        hits = [x for x in recs if not ql or ql in x.get("name", "").lower() or ql in str(x.get("proc_id", "")).lower()
                or ql in str(x.get("domain", "")).lower()]
        page = hits[max(0, offset):max(0, offset) + min(max(limit, 1), 200)]
        deleted = [p for p, v in ch.items() if v is None] if version == "draft" else []
        return {"total": len(hits), "deleted": deleted,
                "records": [{"proc_id": x["proc_id"], "name": x.get("name", ""), "domain": x.get("domain", ""),
                             "province": x.get("province", ""), "changed": x["proc_id"] in ch} for x in page]}

    @r.get("/procs/record/{proc_id}")
    def procs_record(proc_id: str, request: Request, version: str = "draft"):
        dev(request)
        procs_ready()
        _, by_id, ch = err(procs.view, version)
        if proc_id not in by_id:
            raise HTTPException(404, "không có thủ tục này trong phiên bản")
        return {"record": by_id[proc_id], "changed": proc_id in ch, "profile": procs.profile()}

    @r.put("/procs/draft/{proc_id}")
    def draft_put(proc_id: str, body: RecordIn, request: Request):
        dev(request)
        procs_ready()
        _, by_id, _ = procs.view("draft")
        if proc_id not in by_id:
            raise HTTPException(404, "không có thủ tục này")
        errs = procs.validate(proc_id, body.record)
        if errs:
            raise HTTPException(422, " · ".join(errs))
        procs.draft_put(proc_id, body.record)
        return {"ok": True}

    @r.delete("/procs/draft/{proc_id}")
    def draft_delete(proc_id: str, request: Request):
        dev(request)
        procs_ready()
        procs.draft_put(proc_id, None)
        return {"ok": True}

    @r.post("/procs/draft/{proc_id}/revert")
    def draft_revert(proc_id: str, request: Request):
        dev(request)
        procs.draft_revert(proc_id)
        return {"ok": True}

    @r.post("/procs/draft/save")
    def draft_save(body: LabelIn, request: Request):
        dev(request)
        procs_ready()
        vid = err(procs.draft_save, body.label)
        return {"version_id": vid, "diff": procs.diff(str(procs.active_id()), str(vid))["counts"]}

    @r.delete("/procs/draft")
    def draft_discard(request: Request):
        dev(request)
        procs.draft_discard()
        return {"ok": True}

    @r.delete("/procs/versions/{vid}")
    def delete_version(vid: int, request: Request):
        dev(request)
        procs_ready()
        err(procs.delete_version, vid)
        return {"ok": True}

    @r.get("/procs/diff")
    def diff(request: Request, a: str, b: str):
        dev(request)
        procs_ready()
        return err(procs.diff, a, b)

    @r.get("/procs/diff/{proc_id}")
    def diff_record(proc_id: str, request: Request, a: str, b: str):
        dev(request)
        procs_ready()
        return err(procs.diff_record, a, b, proc_id)

    @r.post("/procs/apply")
    def apply(body: ApplyIn, request: Request):
        dev(request)
        procs_ready()
        try:
            procs.apply(body.version_id)
        except (ValueError, FileNotFoundError) as e:
            raise HTTPException(422, str(e)) from None
        return {"job": procs.job()}

    @r.post("/procs/scrape")
    def scrape(body: ScrapeIn, request: Request):
        dev(request)
        procs_ready()
        err(procs.scrape, max(0, body.limit))
        return {"job": procs.job()}

    @r.get("/procs/job")
    def job(request: Request):
        dev(request)
        return {"job": procs.job(), "log": procs.scrape_log_tail() if procs.job()["kind"] == "scrape" else []}

    return r

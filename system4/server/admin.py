"""Trang Quản trị (NV4) — chỉ dev. Ba tab: Dữ liệu Strict (thủ tục của System 3), Dữ liệu người dùng, Người dùng."""
from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from pydantic import BaseModel
from starlette.background import BackgroundTask

from . import account, auth, chat, config, datasets, db, guard, llm, persona, procs, procs_xlsx, search


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


class LabIn(BaseModel):
    query: str
    user_id: int | None = None          # bộ dữ liệu đang bật của người này
    dataset_ids: list[int] | None = None   # hoặc chỉ định bộ dữ liệu
    overrides: dict = {}                # RETRIEVAL_CANDIDATES / RETRIEVAL_TOP_K / RERANKER_ENABLED / RERANK_MIN_SCORE


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

    def _merged_top(limit: int) -> list[dict]:
        """G2.3: proc_stats gộp theo mã chuẩn của phiên bản đang dùng (mã cũ Cổng đã cấp lại -> mã mới)."""
        from system3.data import api as data_api
        conn = data_api.connect()
        try:
            out: dict[str, dict] = {}
            for r in s3_store.top_procs(100000):
                pid = data_api.canonical(conn, r["proc_id"])
                cur = out.get(pid)
                if cur is None:
                    out[pid] = {**r, "proc_id": pid}
                else:
                    cur["n"] += r["n"]
                    cur["last_at"] = max(cur["last_at"] or "", r["last_at"] or "")
                    if pid == r["proc_id"]:
                        cur["label"] = r["label"]
        finally:
            conn.close()
        return sorted(out.values(), key=lambda x: (x["n"], x["last_at"] or ""), reverse=True)[:limit]

    @r.get("/stats")
    def stats(request: Request, limit: int = 20):
        """Thống kê: thủ tục Strict được trả lời nhiều nhất, số 👍/👎, số tài khoản theo loại."""
        dev(request)
        fb = lambda t: {k: db.run(f"SELECT COUNT(*) n FROM {t} WHERE feedback=?", (v,), one=True)["n"] for k, v in (("up", 1), ("down", -1))}
        return {"procedures": _merged_top(max(1, min(limit, 200))),
                "feedback": {"friendly": fb("messages"), "strict": fb("strict_nodes")},
                "roles": {x["role"]: x["n"] for x in db.run("SELECT role, COUNT(*) n FROM users GROUP BY role", many=True)}}

    @r.get("/feedback")
    def feedback_export(request: Request, value: int = 0, limit: int = 500):
        """Các cặp (câu hỏi, câu trả lời) đã được 👍 (value=1) hoặc 👎 (value=-1); 0 = cả hai. Dùng để rà lỗi / làm dữ liệu fine-tune."""
        dev(request)
        where, args = ("WHERE value=?", (value,)) if value in (1, -1) else ("", ())
        rows = db.run(f"SELECT engine,domain_id,conversation_id,prompt,answer,value,created_at FROM feedback_log {where} ORDER BY id DESC LIMIT ?",
                      (*args, max(1, min(limit, 5000))), many=True)
        return {"count": len(rows), "items": rows}

    def feedback_rows(value: int) -> list[dict]:
        """Các dòng 👍/👎 đã che CCCD/SĐT (cả dòng ghi trước khi có bộ che); context đã parse thành dict."""
        where, args = ("WHERE value=?", (value,)) if value in (1, -1) else ("", ())
        rows = db.run(f"SELECT engine,domain_id,prompt,answer,value,context,created_at FROM feedback_log {where} ORDER BY id", args, many=True)
        return [{**x, "prompt": db.mask_pii(x["prompt"]), "answer": db.mask_pii(x["answer"]), "context": json.loads(x["context"])} for x in rows]

    def download(body: str, media: str, value: int, ext: str) -> Response:
        name = {1: "up", -1: "down"}.get(value, "all")
        return Response(body, media_type=media, headers={"Content-Disposition": f'attachment; filename="feedback_{name}.{ext}"'})

    @r.get("/feedback.jsonl")
    def feedback_jsonl(request: Request, value: int = 0):
        """Tải file .jsonl, mỗi dòng một cặp {engine, domain_id, prompt, answer, value, context, created_at}."""
        dev(request)
        return download("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in feedback_rows(value)), "application/x-ndjson; charset=utf-8", value, "jsonl")

    @r.get("/feedback.csv")
    def feedback_csv(request: Request, value: int = 0):
        """Tải file .csv (UTF-8 có BOM nên Excel mở đúng tiếng Việt). Context trải thành cột; ô bắt đầu bằng = + - @ bị đệm dấu ' để Excel không chạy như công thức."""
        dev(request)
        safe = lambda v: "'" + v if isinstance(v, str) and v[:1] in tuple("=+-@" + chr(9) + chr(13)) else v
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["created_at", "engine", "domain_id", "value", "reason", "behavior", "model", "procs", "candidates", "flags", "prompt", "answer"])
        for x in feedback_rows(value):
            c = x["context"]
            w.writerow([safe(v) for v in (x["created_at"], x["engine"], x["domain_id"], x["value"], c.get("reason", ""), c.get("behavior") or "", c.get("model", ""),
                                          "; ".join(f'{p.get("id")} {p.get("label")}' for p in c.get("procs", [])), "; ".join(c.get("candidates", [])),
                                          "; ".join(c.get("flags", [])), x["prompt"], x["answer"])])
        return download(chr(0xFEFF) + out.getvalue(), "text/csv; charset=utf-8", value, "csv")

    @r.get("/users")
    def users(request: Request):
        dev(request)
        return {"users": user_rows()}

    @r.post("/users")
    def create_user(body: NewUser, request: Request):
        dev(request)
        if body.role not in db.ROLES:
            raise HTTPException(422, "Vai trò phải là dev, can_bo hoặc user")
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
            if body.role not in db.ROLES:
                raise HTTPException(422, "Vai trò phải là dev, can_bo hoặc user")
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
        account.purge_user(s3_store, uid)   # G1.4: xoá mọi thứ của người đó; 👍/👎 giữ nhưng bỏ danh tính
        return {"users": user_rows()}

    @r.get("/users/{uid}/conversations")
    def user_conversations(uid: int, request: Request):
        """Hội thoại của một người dùng (chỉ xem) — để soi câu trả lời khi người dùng báo lỗi (1C)."""
        dev(request)
        ids = db.strict_ids(uid)
        strict = [{**c, "mode": "strict"} for c in s3_store.list_conversations() if c["id"] in ids]
        friendly = [{**c, "mode": "friendly"} for c in db.list_conversations(uid)]
        rows = sorted(strict + friendly, key=lambda c: c["created_at"], reverse=True)
        return {"conversations": rows}

    # ----------------------------------------------------- phòng thử tìm kiếm
    def lab_search(body: LabIn):
        allowed = {"RETRIEVAL_CANDIDATES", "RETRIEVAL_TOP_K", "RERANKER_ENABLED", "RERANK_MIN_SCORE"}
        ov = {k: v for k, v in body.overrides.items() if k in allowed}
        if body.dataset_ids:
            ids = body.dataset_ids
        elif body.user_id:
            ids = [d["id"] for d in db.active_datasets(body.user_id)]
        else:
            raise HTTPException(422, "Chọn người dùng hoặc bộ dữ liệu")
        if not body.query.strip():
            raise HTTPException(422, "Nhập câu hỏi")
        return search.search(0, body.query.strip(), dataset_ids=ids, overrides=ov)

    @r.post("/searchlab")
    def searchlab(body: LabIn, request: Request):
        """Xem xếp hạng tìm kiếm cho một câu hỏi (không hỏi AI), có thể đổi tạm thông số."""
        dev(request)
        import time
        t0 = time.perf_counter()
        out, info = lab_search(body)
        info["search_ms"] = int((time.perf_counter() - t0) * 1000)
        return {"info": info, "sent": [c["id"] for c in out]}

    @r.post("/searchlab/ask")
    async def searchlab_ask(body: LabIn, request: Request):
        """Hỏi AI (chế độ Nhanh) với đúng kết quả tìm kiếm này, không lưu vào hội thoại nào: xem lời dặn + JSON thô + câu trả lời."""
        dev(request)
        import asyncio
        out, info = await asyncio.to_thread(lab_search, body)
        _, instructions = guard.check_input(body.query)
        system = persona.build([], "", instructions, fast=True, evidence=out, upset=persona.negative(body.query))
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": body.query}]
        ans, raw = chat.AnswerStream(), []
        async with llm.Turn():
            async for t in llm.stream_json(msgs, persona.FAST_SCHEMA_KB):
                if isinstance(t, llm.Thought):
                    continue
                raw.append(t)
                ans.feed(t)
        return {"info": info, "prompt": system, "raw": "".join(raw), "parsed": ans.final()}

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

    @r.get("/procs/export.xlsx")
    def export_xlsx(request: Request, version: str = "active"):
        """Xuất DB thủ tục ra Excel (procs_xlsx). version = "active" (DB Strict đang dùng, chụp sang tệp tạm nên "Áp dụng"
        vẫn thay được DB; ~20 s) hoặc id một phiên bản đã lưu (dựng DB tạm từ tệp .jsonl của nó; thêm ~1 phút)."""
        dev(request)
        procs_ready()
        j = procs.job()
        if j["state"] == "running" and j["kind"] == "apply":
            raise HTTPException(409, "Đang áp dụng phiên bản, hãy đợi xong rồi xuất")
        active = procs.active_id()
        try:
            vid = active if version in ("", "active") else int(version)
        except ValueError:
            raise HTTPException(422, "version phải là 'active' hoặc số phiên bản") from None
        vers = procs.versions()
        v = next((x for x in vers if x["id"] == vid), None)
        if not v:
            raise HTTPException(404, f"không có phiên bản {vid}")
        if vid == active:
            src = procs.db_path_of(vid) or Path(procs._s3_data().active_db_path())
            where = f"{src.name} in data/runtime/knowledge (the database Strict mode answers from right now)"
        else:
            src, where = procs.VERSIONS / f"{vid}.jsonl", (f"saved version {vid} (system4/runtime/procs/versions/{vid}.jsonl), "
                                                          "built into a temporary database with system3.data.build")
        tmp = Path(tempfile.mkdtemp(prefix="s4_export_"))
        try:
            out = tmp / procs_xlsx.filename(vid)
            res = procs_xlsx.export_file(src, out, vers, vid, active, where)
            if vid != active and res["procedures"] != v["n_records"]:
                raise HTTPException(500, f"DB dựng ra có {res['procedures']} thủ tục, phiên bản ghi {v['n_records']}: không xuất")
        except Exception:
            shutil.rmtree(tmp, ignore_errors=True)
            raise
        return FileResponse(out, filename=out.name, background=BackgroundTask(shutil.rmtree, tmp, ignore_errors=True),
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @r.get("/procs/job")
    def job(request: Request):
        dev(request)
        return {"job": procs.job(), "log": procs.scrape_log_tail() if procs.job()["kind"] == "scrape" else []}

    return r

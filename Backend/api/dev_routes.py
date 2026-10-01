"""Công cụ phát triển. CHỈ được đăng ký khi DEV_TOOLS_ENABLED = True.

Không đăng ký route = không tồn tại endpoint. Ẩn nút ở giao diện KHÔNG phải
là bảo mật; đây mới là.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Response
from fastapi.responses import JSONResponse

import developer_mode
from api.deps import current_user, require_admin
from api.schemas import DevToggle, ResetRequest, WebSearchTest
from db import connection
from db.repositories import (
    AuthSessions, Conversations, Evidence, Feedback, Messages, Traces, UnmatchedQueries,
    Users, ProcedureSynonyms
)
from datetime import datetime
from pathlib import Path
from config import (ADMIN_EMAILS, AUTH_SESSION_DAYS, ONLINE_WINDOW_SECONDS,
                    PROCEDURES_DB_PATH, QUEUE_CONCURRENCY)
from core import queue, system_retrieval

# TOÀN BỘ route trong tệp này yêu cầu admin (áp ở cấp router).
router = APIRouter(dependencies=[Depends(require_admin)])

CONFIRM_WORD = "XOA"


# ------------------------------------------------------ chế độ dev ----
@router.get("/api/dev/status")
async def dev_status(user: dict = Depends(current_user)):
    """Mọi công tắc đang ảnh hưởng tới hành vi — xem nhanh, khỏi mở .env."""
    return developer_mode.snapshot()


@router.post("/api/dev/toggle")
async def dev_toggle(body: DevToggle, user: dict = Depends(current_user)):
    value = developer_mode.toggle() if body.enabled is None \
        else developer_mode.set_enabled(body.enabled)
    return {"developer_mode": value}


@router.get("/api/dev/trace")
async def dev_trace(limit: int = 10, user: dict = Depends(current_user)):
    """Vết chạy các lượt gần nhất: ý định, truy vấn MCP, kiểm chứng, thời gian."""
    return {"enabled": developer_mode.enabled(),
            "traces": developer_mode.traces(limit)}


@router.delete("/api/dev/trace")
async def dev_trace_clear(user: dict = Depends(current_user)):
    return {"cleared": developer_mode.clear_traces()}


@router.post("/api/dev/websearch")
async def dev_websearch(body: WebSearchTest, user: dict = Depends(current_user)):
    """Gọi thử công cụ web_search qua MCP và nói THẲNG hỏng ở bước nào."""
    return await connection.run(developer_mode.websearch_check, body.query or "")


@router.get("/api/dev/stats")
async def stats(user: dict = Depends(current_user)):
    return {
        "users": await connection.run(Users.count),
        "conversations": await connection.run(Conversations.count),
        "messages": await connection.run(Messages.count),
        "feedback": await connection.run(Feedback.count),
        "ratings": await connection.run(Feedback.stats),
    }


@router.post("/api/dev/reset")
async def reset(body: ResetRequest, user: dict = Depends(current_user)):
    if body.confirm != CONFIRM_WORD:
        raise HTTPException(status_code=400,
                            detail=f'Phải gõ đúng "{CONFIRM_WORD}" để xác nhận.')

    def _reset_mine():
        for conv in Conversations.list_for(user["id"], limit=10000):
            Conversations.delete(conv["id"], user["id"])

    if body.scope == "my_conversations":
        await connection.run(_reset_mine)
        return {"ok": True, "scope": body.scope}

    if body.scope == "all_conversations":
        def _all():
            conn = connection.get_conn()
            for table in ("feedback", "evidence", "messages", "conversations", "job_log"):
                conn.execute(f"DELETE FROM {table}")
            conn.commit()
        await connection.run(_all)
        return {"ok": True, "scope": body.scope}

    if body.scope == "everything":
        await connection.run(connection.reset_database)
        return {"ok": True, "scope": body.scope, "note": "Đã xoá cả tài khoản. Hãy đăng ký lại."}

    raise HTTPException(status_code=400, detail="scope không hợp lệ.")


@router.get("/api/dev/export/conversation/{conv_id}")
async def dev_export_conversation(conv_id: int, user: dict = Depends(current_user)):
    from core.eval_export import build_conversation_export
    from fastapi.responses import PlainTextResponse
    # Admin xuất được hội thoại của BẤT KỲ người dùng: lấy chủ sở hữu thật của cuộc trò chuyện
    # (trước đây truyền id của admin nên chỉ xuất được hội thoại của chính mình).
    conv = await connection.run(Conversations.by_id, conv_id)
    if conv is None:
        raise HTTPException(404, "Không tìm thấy cuộc trò chuyện.")
    content = await connection.run(build_conversation_export, conv_id, conv["user_id"])
    filename = f"danh_gia_hoi_thoai_{conv_id}.txt"
    return PlainTextResponse(
        content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/api/dev/export/all")
async def dev_export_all(user_id: int | None = None, user: dict = Depends(current_user)):
    """Xuất mọi hội thoại của `user_id` (mặc định: của chính admin)."""
    from datetime import datetime
    from core.eval_export import build_all_conversations_export
    from fastapi.responses import PlainTextResponse
    content = await connection.run(build_all_conversations_export, user_id or user["id"])
    filename = f"tat_ca_hoi_thoai_danh_gia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return PlainTextResponse(
        content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# ---------------------------------------------------- metrics & queue ----
@router.get("/api/dev/metrics")
async def dev_metrics(user: dict = Depends(current_user)):
    """Số liệu thời gian thực: người dùng trực tuyến, phiên hoạt động, hàng đợi."""
    active = await connection.run(AuthSessions.active_metrics,
                                  AUTH_SESSION_DAYS * 24 * 3600, ONLINE_WINDOW_SECONDS)
    unmatched_count = await connection.run(UnmatchedQueries.count, True)
    return {
        # Người đang dùng THẬT: có gọi API trong ONLINE_WINDOW_SECONDS gần nhất.
        "online_users": active.get("online_users", 0),
        "online_sessions": active.get("online_sessions", 0),
        "online_window_seconds": ONLINE_WINDOW_SECONDS,
        # Phiên còn hạn (đã đăng nhập, chưa hết 14 ngày) — KHÔNG phải đang online.
        "logged_in_users": active.get("logged_in_users", 0),
        "logged_in_sessions": active.get("logged_in_sessions", 0),
        "active_sessions": active.get("active_sessions", 0),
        "active_users": active.get("active_users", 0),
        "queue_depth": queue.manager.depth,
        "queue_concurrency": QUEUE_CONCURRENCY,
        "total_users": await connection.run(Users.count),
        "total_conversations": await connection.run(Conversations.count),
        "total_messages": await connection.run(Messages.count),
        "unmatched_queries_unresolved": unmatched_count,
    }


# --------------------------------------------------- user management ----
@router.get("/api/dev/users")
async def dev_list_users(limit: int = 50, offset: int = 0, user: dict = Depends(current_user)):
    """Danh sách người dùng, quyền admin, số lượng hội thoại."""
    users_list = await connection.run(Users.list_all, limit, offset)
    return {"users": users_list}


@router.post("/api/dev/users")
async def dev_create_user(body: dict, user: dict = Depends(current_user)):
    """Admin tạo tài khoản (vẫn dùng được khi REGISTRATION_ENABLED = False).

    Cùng luật với đăng ký thường: email hợp lệ, mật khẩu đủ dài, không trùng.
    Không xác minh email (xem Documentation/Thing to do next/13).
    """
    from core import auth
    email = str(body.get("email") or "").strip()
    password = str(body.get("password") or "")
    display_name = str(body.get("display_name") or "").strip()[:80]
    try:
        created = await connection.run(auth.register, email, password, display_name)
    except auth.AuthError as err:
        raise HTTPException(400, str(err))
    if body.get("is_admin"):
        await connection.run(Users.set_admin, created["id"], True)
        created = await connection.run(Users.by_id, created["id"])
    return {"ok": True, "user": auth.public(created)}


@router.post("/api/dev/users/{target_id}/role")
async def dev_set_role(target_id: int, body: dict, user: dict = Depends(current_user)):
    """Phân quyền admin."""
    is_admin = bool(body.get("is_admin", False))
    if not is_admin:
        if target_id == user["id"]:
            raise HTTPException(400, "Không thể tự hạ quyền của chính mình.")
        def _last_admin() -> bool:
            row = connection.get_conn().execute(
                "SELECT COUNT(*) c FROM users WHERE is_admin = 1 AND id != ?", (target_id,)).fetchone()
            return row["c"] == 0 and ADMIN_EMAILS == set()
        if await connection.run(_last_admin):
            raise HTTPException(400, "Không thể hạ quyền admin cuối cùng.")
    await connection.run(Users.set_admin, target_id, is_admin)
    return {"ok": True, "user_id": target_id, "is_admin": is_admin}


@router.delete("/api/dev/users/{target_id}")
async def dev_delete_user(target_id: int, user: dict = Depends(current_user)):
    """Xóa tài khoản người dùng và toàn bộ dữ liệu kèm theo."""
    if target_id == user["id"]:
        raise HTTPException(400, "Không thể tự xóa tài khoản của chính mình.")
    await connection.run(Users.delete_user, target_id)
    return {"ok": True, "deleted_user_id": target_id}


@router.post("/api/dev/users/{target_id}/nuke")
async def dev_nuke_user_conversations(target_id: int, user: dict = Depends(current_user)):
    """Xóa sạch lịch sử trò chuyện của một tài khoản."""
    await connection.run(Conversations.nuke_user_conversations, target_id)
    return {"ok": True, "user_id": target_id}


# ------------------------------------ xem hội thoại + vết chạy của bất kỳ user ----
@router.get("/api/dev/users/{target_id}/conversations")
async def dev_user_conversations(target_id: int, user: dict = Depends(current_user)):
    """Danh sách hội thoại của một user (để dev soi câu trả lời)."""
    return {"conversations": await connection.run(Conversations.list_for_admin, target_id)}


@router.get("/api/dev/conversations/{conv_id}/messages")
async def dev_conversation_messages(conv_id: int, user: dict = Depends(current_user)):
    conv = await connection.run(Conversations.by_id, conv_id)
    if conv is None:
        raise HTTPException(404, "Không tìm thấy cuộc trò chuyện.")

    def _load():
        traced = Traces.message_ids_with_trace(conv_id)
        out = []
        for m in Messages.list_for(conv_id):
            out.append({"id": m["id"], "role": m["role"], "content": m["content"],
                        "kind": m["kind"], "verdict": m["verdict"], "created_at": m["created_at"],
                        "has_evidence": bool(m["has_evidence"]), "has_trace": m["id"] in traced})
        return out
    return {"conversation": {k: conv[k] for k in ("id", "user_id", "title", "system", "created_at")},
            "messages": await connection.run(_load)}


@router.get("/api/dev/messages/{message_id}/trace")
async def dev_message_trace(message_id: int, user: dict = Depends(current_user)):
    """Các bước đã sinh ra MỘT câu trả lời bất kỳ: ý định, khoá tra, MCQ, kiểm chứng, thời gian."""
    def _load():
        return Traces.for_message(message_id), Evidence.for_message_admin(message_id)
    trace, evidence = await connection.run(_load)
    if trace is None:
        raise HTTPException(404, "Không có vết chạy cho tin nhắn này (tin cũ, hoặc ghi vết đang tắt).")
    return {"trace": trace, "evidence": evidence}


# --------------------------------------------- procedures db stats & export ----
@router.get("/api/dev/db/procedures/stats")
async def dev_procedures_stats(user: dict = Depends(current_user)):
    """Thống kê dữ liệu thủ tục trong procedures.db."""
    if not PROCEDURES_DB_PATH.is_file():
        return {"available": False, "path": str(PROCEDURES_DB_PATH)}

    def _query_stats():
        conn = sqlite3.connect(str(PROCEDURES_DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            total_active = conn.execute("SELECT COUNT(*) c FROM procedures WHERE status = 'active'").fetchone()["c"]
            total_archived = conn.execute("SELECT COUNT(*) c FROM procedures WHERE status = 'archived'").fetchone()["c"]
            total_expired = conn.execute("SELECT COUNT(*) c FROM procedures WHERE status = 'expired'").fetchone()["c"]
            domains = [dict(r) for r in conn.execute(
                "SELECT domain, COUNT(*) c FROM procedures WHERE status = 'active' GROUP BY domain ORDER BY c DESC LIMIT 10"
            ).fetchall()]
            files_count = conn.execute("SELECT COUNT(*) c FROM procedure_files").fetchone()["c"]
            return {
                "available": True,
                "path": str(PROCEDURES_DB_PATH),
                "active": total_active,
                "archived": total_archived,
                "expired": total_expired,
                "top_domains": domains,
                "files_count": files_count,
            }
        finally:
            conn.close()

    return await connection.run(_query_stats)


def dump_active_procedures_jsonl() -> str:
    """Xuất danh sách thủ tục active kèm 9 bảng con ra chuẩn JSONL của staging/procedures.jsonl."""
    conn = sqlite3.connect(str(PROCEDURES_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        from Database.pipeline.import_db import PROC_COLUMNS
        procs = [dict(r) for r in conn.execute(
            f"SELECT row_id, {','.join(PROC_COLUMNS)} FROM procedures WHERE status = 'active'"
        )]

        def load_children(table, cols, order_by=None):
            q = f"SELECT row_id, {','.join(cols)} FROM {table}"
            if order_by:
                q += f" ORDER BY {order_by}"
            res = {}
            for r in conn.execute(q):
                d = dict(r)
                rid = d.pop("row_id")
                res.setdefault(rid, []).append(d)
            return res

        fees = load_children("procedure_fees", ["fee_type", "amount_value", "amount_text", "currency_id", "submission_method"])
        checklist = load_children("checklist_items", ["ordinal", "case_ordinal", "case_name", "name", "code", "required", "original_qty", "copy_qty", "has_electronic_form", "n_attachments"], "row_id, ordinal")
        files = load_children("procedure_files", ["file_id", "file_name", "bucket_name", "remote_path", "local_path", "file_available", "belongs_to"])
        steps = load_children("procedure_steps", ["ordinal", "name", "description"], "row_id, ordinal")
        methods = load_children("procedure_methods", ["submission_method", "processing_time_qty", "processing_time_unit", "processing_time_text", "description"])
        legal = load_children("legal_basis", ["doc_code", "doc_name", "doc_year"])
        cases = load_children("procedure_cases", ["ordinal", "case_name", "n_components"], "row_id, ordinal")
        subjects = load_children("procedure_subjects", ["subject_name", "subject_code"])
        services = load_children("online_services", ["service_code", "service_name", "processing_qty", "processing_unit"], "row_id, id")

        lines = []
        for p in procs:
            rid = p.pop("row_id")
            p["fees"] = fees.get(rid, [])
            p["checklist"] = checklist.get(rid, [])
            p["files"] = files.get(rid, [])
            p["steps"] = steps.get(rid, [])
            p["methods"] = methods.get(rid, [])
            p["legal_basis"] = legal.get(rid, [])
            p["cases"] = cases.get(rid, [])
            p["subjects"] = subjects.get(rid, [])
            p["online_services"] = services.get(rid, [])
            lines.append(json.dumps(p, ensure_ascii=False))

        return "\n".join(lines) + "\n"
    finally:
        conn.close()


@router.get("/api/dev/db/procedures/export")
async def dev_procedures_export(format: str = "jsonl", user: dict = Depends(current_user)):
    """Xuất danh sách thủ tục hiện hành ra định dạng JSONL (round-trip import_db) hoặc JSON."""
    if not PROCEDURES_DB_PATH.is_file():
        raise HTTPException(404, "Không tìm thấy CSDL procedures.db.")

    if format == "json":
        def _export_summary():
            conn = sqlite3.connect(str(PROCEDURES_DB_PATH))
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    "SELECT proc_id, name, domain, executing_agency, portal_url FROM procedures WHERE status = 'active'"
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()
        data = await connection.run(_export_summary)
        return JSONResponse(
            content={"total": len(data), "procedures": data},
            headers={"Content-Disposition": 'attachment; filename="procedures_active_export.json"'}
        )

    content = await connection.run(dump_active_procedures_jsonl)
    return Response(
        content=content,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="procedures_export.jsonl"'}
    )


def _list_procedure_backups() -> list[dict]:
    bdir = PROCEDURES_DB_PATH.parent / "backups"
    if not bdir.is_dir():
        return []
    out = []
    for f in sorted(bdir.glob("procedures_*.db.bak"), reverse=True):
        try:
            stat = f.stat()
            out.append({
                "filename": f.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception:
            pass
    return out


def parse_and_validate_import_jsonl(raw_bytes: bytes) -> list[dict]:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as ue:
        raise HTTPException(400, f"Tệp không đúng định dạng mã hoá UTF-8 hợp lệ: {ue}")

    records = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception as e:
            raise HTTPException(400, f"Lỗi cú pháp JSON ở dòng {line_no}: {e}")
        if not isinstance(item, dict):
            raise HTTPException(400, f"Dòng {line_no} không phải là đối tượng JSON hợp lệ (dict).")
        if not item.get("proc_id") or not str(item.get("proc_id")).strip():
            raise HTTPException(400, f"Dòng {line_no} thiếu trường bắt buộc 'proc_id'.")
        if not item.get("name") or not str(item.get("name")).strip():
            raise HTTPException(400, f"Dòng {line_no} (proc_id={item.get('proc_id')}) thiếu trường bắt buộc 'name'.")
        records.append(item)

    if not records:
        raise HTTPException(400, "Tệp không chứa bản ghi hợp lệ nào.")
    return records


@router.post("/api/dev/db/procedures/import")
async def dev_procedures_import(file: UploadFile = File(...), user: dict = Depends(current_user)):
    """Nạp tệp procedures.jsonl vào procedures.db có versioning và tự động sao lưu trước khi nạp."""
    MAX_SIZE = 15 * 1024 * 1024  # 15MB
    raw_bytes = await file.read(MAX_SIZE + 1)
    if len(raw_bytes) > MAX_SIZE:
        raise HTTPException(413, "Dung lượng tệp vượt quá giới hạn 15MB.")

    records = parse_and_validate_import_jsonl(raw_bytes)

    def _do_import():
        bdir = PROCEDURES_DB_PATH.parent / "backups"
        bdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ts_bak = bdir / f"procedures_{ts}.db.bak"
        latest_bak = PROCEDURES_DB_PATH.with_suffix(".db.bak")

        # Cắt bớt nếu có hơn 10 bản sao lưu cũ
        existing_baks = sorted(bdir.glob("procedures_*.db.bak"), reverse=True)
        for old_b in existing_baks[9:]:
            try: old_b.unlink()
            except Exception: pass

        system_retrieval.invalidate_all_connections()
        if PROCEDURES_DB_PATH.is_file():
            try:
                chk = sqlite3.connect(str(PROCEDURES_DB_PATH))
                chk.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                chk.close()
            except Exception:
                pass
            shutil.copy2(PROCEDURES_DB_PATH, ts_bak)
            shutil.copy2(PROCEDURES_DB_PATH, latest_bak)

        from Database.pipeline.import_db import connect as connect_proc_db, import_records
        conn = connect_proc_db(PROCEDURES_DB_PATH)
        try:
            stats = import_records(conn, records)
            return stats, ts_bak.name
        except Exception as err:
            if ts_bak.is_file():
                shutil.copy2(ts_bak, PROCEDURES_DB_PATH)
            raise err
        finally:
            conn.close()
            system_retrieval.invalidate_all_connections()

    try:
        stats, backup_name = await connection.run(_do_import)
        return {
            "ok": True,
            "message": f"Nạp thành công {len(records)} bản ghi.",
            "stats": stats,
            "backup_created": backup_name
        }
    except Exception as e:
        raise HTTPException(400 if "Dòng" in str(e) or "cú pháp" in str(e) else 500,
                            f"Lỗi trong quá trình nạp CSDL: {e}")


@router.get("/api/dev/db/procedures/backups")
async def dev_procedures_backups(user: dict = Depends(current_user)):
    """Danh sách các bản sao lưu procedures.db đã tạo."""
    return {"backups": await connection.run(_list_procedure_backups)}


@router.post("/api/dev/db/procedures/rollback")
async def dev_procedures_rollback(body: dict | None = None, user: dict = Depends(current_user)):
    """Khôi phục CSDL procedures.db từ bản sao lưu gần nhất hoặc bản được chỉ định."""
    bdir = PROCEDURES_DB_PATH.parent / "backups"
    body = body or {}
    backup_filename = body.get("backup_filename")
    chosen_file = None

    if backup_filename:
        safe_name = Path(backup_filename).name
        target = bdir / safe_name
        if target.is_file():
            chosen_file = target
        else:
            raise HTTPException(404, f"Không tìm thấy bản sao lưu '{safe_name}'.")
    else:
        backups = sorted(bdir.glob("procedures_*.db.bak"), reverse=True) if bdir.is_dir() else []
        if backups:
            chosen_file = backups[0]
        elif PROCEDURES_DB_PATH.with_suffix(".db.bak").is_file():
            chosen_file = PROCEDURES_DB_PATH.with_suffix(".db.bak")
        else:
            raise HTTPException(404, "Không tìm thấy bản sao lưu procedures.db nào để phục hồi.")

    def _do_rollback():
        system_retrieval.invalidate_all_connections()
        wal = PROCEDURES_DB_PATH.with_name(PROCEDURES_DB_PATH.name + "-wal")
        shm = PROCEDURES_DB_PATH.with_name(PROCEDURES_DB_PATH.name + "-shm")
        if wal.exists():
            try: wal.unlink()
            except Exception: pass
        if shm.exists():
            try: shm.unlink()
            except Exception: pass
        shutil.copy2(chosen_file, PROCEDURES_DB_PATH)
        system_retrieval.invalidate_all_connections()

    await connection.run(_do_rollback)
    return {
        "ok": True,
        "message": f"Đã phục hồi CSDL procedures.db về bản sao lưu '{chosen_file.name}' thành công.",
        "restored_from": chosen_file.name
    }


# --------------------------------------------- unmatched queries telemetry & synonyms ----
@router.get("/api/dev/telemetry/unmatched")
async def dev_unmatched_queries(limit: int = 50, unresolved_only: bool = False, user: dict = Depends(current_user)):
    """Danh sách câu hỏi tra từ khóa trượt để Dev xem xét bổ sung synonym."""
    items = await connection.run(UnmatchedQueries.list_recent, limit, unresolved_only)
    return {"items": items}


@router.post("/api/dev/telemetry/unmatched/{query_id}/resolve")
async def dev_resolve_unmatched(query_id: int, body: dict, user: dict = Depends(current_user)):
    """Đánh dấu đã xử lý câu hỏi trượt (ví dụ đã thêm synonym)."""
    notes = str(body.get("notes") or "").strip()
    raw_term = str(body.get("raw_term") or "").strip()
    canonical_keyword = str(body.get("canonical_keyword") or "").strip()
    if raw_term and canonical_keyword:
        await connection.run(ProcedureSynonyms.add, raw_term, canonical_keyword)
        if not notes:
            notes = f"Đã thêm synonym: {raw_term} -> {canonical_keyword}"
    await connection.run(UnmatchedQueries.mark_resolved, query_id, notes)
    return {"ok": True, "query_id": query_id}


@router.get("/api/dev/synonyms")
async def dev_list_synonyms(user: dict = Depends(current_user)):
    """Danh sách các từ đồng nghĩa động."""
    items = await connection.run(ProcedureSynonyms.list_all)
    return {"synonyms": items}


@router.post("/api/dev/synonyms")
async def dev_add_synonym(body: dict, user: dict = Depends(current_user)):
    """Thêm hoặc cập nhật từ đồng nghĩa động."""
    raw_term = str(body.get("raw_term") or "").strip()
    canonical_keyword = str(body.get("canonical_keyword") or "").strip()
    if not raw_term or not canonical_keyword:
        raise HTTPException(400, "raw_term và canonical_keyword không được để trống.")
    try:
        item = await connection.run(ProcedureSynonyms.add, raw_term, canonical_keyword)
        return {"ok": True, "synonym": item}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/api/dev/synonyms/{synonym_id}")
async def dev_delete_synonym(synonym_id: int, user: dict = Depends(current_user)):
    """Xóa một từ đồng nghĩa động."""
    deleted = await connection.run(ProcedureSynonyms.delete, synonym_id)
    if not deleted:
        raise HTTPException(404, "Không tìm thấy synonym để xóa.")
    return {"ok": True, "deleted_id": synonym_id}

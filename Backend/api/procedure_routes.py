"""Hệ thống 2: tải biểu mẫu của thủ tục + trí nhớ lựa chọn MCQ.

    GET    /api/procedures/{proc_id}/files/{file_id}   tải biểu mẫu (.docx…)
    GET    /api/mcq-memory                             xem mình đã nhớ những gì
    POST   /api/mcq-memory                             nhớ một lựa chọn
    DELETE /api/mcq-memory                             quên (tất cả, hoặc một trục)

VÌ SAO CÓ ROUTE TẢI TỆP RIÊNG:
`procedure_files.local_path` là đường dẫn TƯƠNG ĐỐI trong `Database/raw/files/`.
Thư mục đó KHÔNG commit vào git (774 thư mục .docx làm kho nặng) nên máy mới
phải chạy lại pipeline mới có. Thiếu tệp thì trả 404 kèm lời giải thích, KHÔNG
để giao diện hiện nút tải rồi bấm vào ra lỗi trắng.

Đường dẫn lấy từ CSDL nên vẫn phải chặn thoát thư mục (`..`) — dữ liệu cào về
từ mạng thì không được tin, dù đã qua một tầng chuẩn hoá.
"""

from __future__ import annotations

import mimetypes
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.deps import current_user
from config import PROCEDURE_FILES_DIR
from core import system_retrieval
from db import connection
from db.repositories import Conversations, MCQMemory, RetrievalPending, UnmatchedQueries

from Database.pipeline import retrieval as R

router = APIRouter()

MISSING_FILES_NOTE = (
    "Biểu mẫu chưa có trên máy chủ này. Người cài đặt cần chạy: "
    "python -m Database.pipeline.run_pipeline --all")


def _safe_path(local_path: str) -> Path | None:
    """Đường dẫn trong CSDL -> đường dẫn thật, hoặc None nếu đáng ngờ/không có.

    `local_path` có dạng "files/1.000091/Mus16.docx" — phần "files/" trùng tên
    thư mục gốc nên phải bỏ đi trước khi ghép, kẻo thành files/files/...
    """
    rel = (local_path or "").strip().replace("\\", "/").lstrip("/")
    if not rel or ".." in rel.split("/"):
        return None
    if rel.startswith("files/"):
        rel = rel[len("files/"):]

    root = PROCEDURE_FILES_DIR.resolve()
    target = (root / rel).resolve()
    # Chặn thoát thư mục: phải nằm THẬT SỰ bên trong thư mục biểu mẫu.
    if not target.is_relative_to(root) or not target.is_file():
        return None
    return target


@router.get("/api/procedures/{proc_id}/files/{file_id}")
async def download_form(proc_id: str, file_id: str, user: dict = Depends(current_user)):
    """Tải một biểu mẫu đính kèm thủ tục."""
    conn = system_retrieval._conn()
    if conn is None:
        raise HTTPException(503, "Chưa có cơ sở dữ liệu thủ tục trên máy này.")

    row = conn.execute(
        "SELECT f.file_name, f.local_path, f.file_available FROM procedure_files f"
        "  JOIN procedures p ON p.row_id = f.row_id"
        " WHERE p.proc_id = ? AND f.file_id = ? AND p.status = 'active'",
        (proc_id, file_id)).fetchone()
    if row is None:
        raise HTTPException(404, "Không có biểu mẫu này trong cơ sở dữ liệu.")
    if not row["file_available"]:
        raise HTTPException(404, "Cổng Dịch vụ công có ghi tên biểu mẫu nhưng không tải được nội dung.")

    path = _safe_path(row["local_path"])
    if path is None:
        raise HTTPException(404, MISSING_FILES_NOTE)

    name = row["file_name"] or path.name
    media = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media, filename=name)


def _validate_axis_value(axis: str, value: str) -> None:
    if axis not in R.MEMORABLE_AXES:
        raise HTTPException(400, f"Trục '{axis}' không được phép ghi nhớ (chỉ hỗ trợ: {', '.join(R.MEMORABLE_AXES)}).")
    val_norm = value.strip().lower()
    conn = system_retrieval._conn()
    if conn is None:
        return

    if axis == R.AXIS_LEVEL:
        valid_levels = {
            "xã/phường", "xa/phuong", "xã", "xa", "phường", "phuong", "cấp xã", "cap xa",
            "cấp huyện", "cap huyen", "huyện", "huyen", "tỉnh", "tinh", "cấp tỉnh", "cap tinh",
            "tỉnh/thành phố", "tinh/thanh pho", "bộ", "bo", "bộ/ngành", "bo/nganh",
            "trung ương", "trung uong", "ngành dọc", "nganh doc", "cơ quan khác", "co quan khac"
        }
        rows = conn.execute("SELECT DISTINCT agency_levels FROM procedures WHERE status='active'").fetchall()
        for r in rows:
            if r[0]:
                for p in r[0].split(","):
                    p_clean = p.strip().lower()
                    if p_clean:
                        valid_levels.add(p_clean)
        if val_norm not in valid_levels:
            raise HTTPException(400, f"Giá trị '{value}' không phải cấp thực hiện hợp lệ.")

    elif axis == R.AXIS_SUBJECT:
        rows = conn.execute("SELECT DISTINCT subject_name FROM procedure_subjects").fetchall()
        valid_subjects = {r[0].strip().lower() for r in rows if r[0]}
        if val_norm not in valid_subjects:
            raise HTTPException(400, f"Giá trị '{value}' không nằm trong danh mục đối tượng thực hiện hợp lệ.")


@router.get("/api/mcq-memory/options")
async def memory_options(user: dict = Depends(current_user)):
    """Các trục được phép nhớ + giá trị hợp lệ của từng trục (cho form "Thêm" trong Trí nhớ AI)."""
    def _load():
        conn = system_retrieval._conn()
        out = {}
        for axis in R.MEMORABLE_AXES:
            values: list[str] = []
            if conn is not None:
                if axis == R.AXIS_SUBJECT:
                    values = [r[0].strip() for r in conn.execute(
                        "SELECT DISTINCT subject_name FROM procedure_subjects"
                        " WHERE subject_name IS NOT NULL AND subject_name != ''") if r[0]]
                elif axis == R.AXIS_LEVEL:
                    seen = set()
                    for r in conn.execute("SELECT DISTINCT agency_levels FROM procedures"
                                          " WHERE status = 'active'"):
                        for p in (r[0] or "").split(","):
                            if p.strip():
                                seen.add(p.strip())
                    values = list(seen)
            out[axis] = {"question": R.AXIS_QUESTION.get(axis, axis), "values": sorted(values)}
        return out
    return {"axes": await connection.run(_load)}


# ------------------------------------------------- lịch sử phiên bản thủ tục ----
@router.get("/api/procedures/{proc_id}/versions")
async def get_procedure_versions(proc_id: str, user: dict = Depends(current_user)):
    """Lấy danh sách các phiên bản (active, archived, expired) của một thủ tục theo proc_id."""
    def _load():
        conn = system_retrieval._conn()
        if conn is None:
            return None
        return conn.execute(
            "SELECT row_id, proc_id, version, status, name, decision_number, decision_date,"
            " publication_date, source_updated_at, scraped_at, archived_at, expired_at,"
            " expiry_note, content_hash"
            " FROM procedures WHERE proc_id = ? ORDER BY version DESC, row_id DESC",
            (proc_id,)
        ).fetchall()

    # Chạy trong luồng worker như mọi truy vấn CSDL khác, không chặn event loop.
    rows = await connection.run(_load)
    if rows is None:
        raise HTTPException(503, "Chưa có cơ sở dữ liệu thủ tục.")

    if not rows:
        raise HTTPException(404, f"Không tìm thấy thủ tục với mã '{proc_id}'.")

    versions = []
    for r in rows:
        d = dict(r)
        d["is_current"] = (d["status"] == "active")
        versions.append(d)

    return {"proc_id": proc_id, "total_versions": len(versions), "versions": versions}


# ------------------------------------------------- trí nhớ lựa chọn MCQ ----
@router.get("/api/mcq-memory")
async def list_memory(user: dict = Depends(current_user)):
    items = await connection.run(MCQMemory.list_for, user["id"])
    return {"items": items, "labels": R.AXIS_QUESTION}


@router.post("/api/mcq-memory")
async def remember(body: dict, user: dict = Depends(current_user)):
    """Ghi nhớ một lựa chọn MCQ để lần sau khỏi phải hỏi lại."""
    axis = str(body.get("axis") or "").strip()
    value = str(body.get("value") or "").strip()
    if not axis or not value:
        raise HTTPException(400, "Thiếu axis hoặc value.")
    if len(value) > 200:
        raise HTTPException(400, "Giá trị quá dài (tối đa 200 ký tự).")

    # Xác thực danh mục giá trị hợp lệ theo trục trong CSDL
    _validate_axis_value(axis, value)

    raw_conv_id = body.get("conv_id")
    if raw_conv_id is not None:
        try:
            conv_id = int(raw_conv_id)
        except (ValueError, TypeError):
            raise HTTPException(400, "conv_id không hợp lệ.")
        if await connection.run(Conversations.owned_by, conv_id, user["id"]):
            pending = await connection.run(RetrievalPending.get, conv_id)
            if pending and pending.get("axis") == axis and pending.get("options"):
                val_norm = value.strip().lower()
                valid_vals = {str(opt.get("value", "")).strip().lower() for opt in pending["options"] if "value" in opt}
                valid_labels = {str(opt.get("label", "")).strip().lower() for opt in pending["options"] if "label" in opt}
                if valid_vals and (val_norm not in valid_vals and val_norm not in valid_labels):
                    raise HTTPException(400, f"Giá trị '{value}' không nằm trong các phương án hợp lệ của câu hỏi.")

    await connection.run(MCQMemory.remember, user["id"], axis, value)
    return {"ok": True, "axis": axis, "value": value}


@router.delete("/api/mcq-memory")
async def forget(axis: str = "", user: dict = Depends(current_user)):
    await connection.run(MCQMemory.forget, user["id"], axis)
    return {"ok": True}


@router.put("/api/mcq-memory/{axis}")
async def update_memory(axis: str, body: dict, user: dict = Depends(current_user)):
    """Chỉnh sửa lựa chọn MCQ đã lưu trong bộ nhớ."""
    value = str(body.get("value") or "").strip()
    if not value:
        raise HTTPException(400, "Giá trị không được để trống.")
    if len(value) > 200:
        raise HTTPException(400, "Giá trị quá dài (tối đa 200 ký tự).")

    # Xác thực danh mục giá trị hợp lệ theo trục trong CSDL
    _validate_axis_value(axis, value)

    await connection.run(MCQMemory.update_value, user["id"], axis, value)
    return {"ok": True, "axis": axis, "value": value}


_ADVICE_LAST: dict[int, float] = {}
ADVICE_COOLDOWN_S = 3.0


@router.post("/api/mcq-advice")
async def mcq_advice(body: dict, user: dict = Depends(current_user)):
    """LLM 3: Tư vấn nhanh cho người dân khi phân vân giữa các phương án MCQ."""
    # Không tin question/options từ client: lấy từ vòng MCQ đang chờ trên server,
    # và chỉ của cuộc trò chuyện thuộc về chính người gọi.
    try:
        conv_id = int(body.get("conv_id"))
    except (TypeError, ValueError):
        raise HTTPException(400, "Thiếu conv_id.")
    if await connection.run(Conversations.owned_by, conv_id, user["id"]) is None:
        raise HTTPException(404, "Không tìm thấy cuộc trò chuyện.")
    now = time.time()
    if now - _ADVICE_LAST.get(user["id"], 0) < ADVICE_COOLDOWN_S:
        raise HTTPException(429, "Bạn thao tác hơi nhanh, đợi vài giây rồi thử lại.")
    _ADVICE_LAST[user["id"]] = now
    pending = await connection.run(RetrievalPending.get, conv_id)
    if not pending or not pending.get("options"):
        raise HTTPException(400, "Cuộc trò chuyện này không có lựa chọn nào đang chờ.")
    question = pending.get("question") or ""
    options = pending["options"]
    user_situation = str(body.get("user_situation") or "").strip()[:300]
    # Lịch sử ô chat nhỏ do client gửi: chỉ nhận role user/assistant, cắt ngắn — không tin thêm gì.
    history = []
    for m in (body.get("history") or [])[-6:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant"):
            text = str(m.get("content") or "").strip()[:500]
            if text:
                history.append({"role": m["role"], "content": text})
    advice = await connection.run(system_retrieval.ask_mcq_advice, question, options,
                                  user_situation, history)
    return {"advice": advice}


@router.post("/api/conversations/{conv_id}/mcq-cancel")
async def cancel_mcq(conv_id: int, user: dict = Depends(current_user)):
    """Hủy vòng MCQ hiện tại để người dùng nhập lại câu hỏi khác."""
    if await connection.run(Conversations.owned_by, conv_id, user["id"]) is None:
        raise HTTPException(404, "Không tìm thấy cuộc trò chuyện.")
    await connection.run(RetrievalPending.clear, conv_id)
    # Đây chính là nút "This is not what I want": ghi lại để dev biết LLM 1 / từ khoá đã hiểu sai.
    await connection.run(UnmatchedQueries.mark_rejected_for_conv, conv_id)
    return {"ok": True, "message": "Đã hủy lựa chọn MCQ."}

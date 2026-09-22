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
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.deps import current_user
from config import PROCEDURE_FILES_DIR
from core import system_retrieval
from db import connection
from db.repositories import MCQMemory

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
    # Chỉ nhớ trục MÔ TẢ NGƯỜI DÙNG. Nhớ "thủ tục nào" là trả lời sai về sau.
    if axis not in R.MEMORABLE_AXES:
        raise HTTPException(400, f"Trục '{axis}' không được phép ghi nhớ.")
    await connection.run(MCQMemory.remember, user["id"], axis, value)
    return {"ok": True, "axis": axis, "value": value}


@router.delete("/api/mcq-memory")
async def forget(axis: str = "", user: dict = Depends(current_user)):
    await connection.run(MCQMemory.forget, user["id"], axis)
    return {"ok": True}

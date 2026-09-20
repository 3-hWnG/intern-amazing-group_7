"""Tệp đính kèm theo cuộc trò chuyện.

    POST   /api/conversations/{id}/files     tải lên (thân request = byte thô)
    GET    /api/conversations/{id}/files     liệt kê
    DELETE /api/files/{doc_id}               xoá

Cố tình KHÔNG dùng multipart/form-data: FastAPI cần thêm thư viện
`python-multipart` cho việc đó, mà máy chạy demo có thể không có mạng để cài.
Frontend gửi thẳng byte của tệp, tên tệp nằm ở header `X-Filename` (đã
percent-encode để chịu được tiếng Việt có dấu).

Trả về đúng hình dạng slide 7 mô tả:
    {"file_id": 12, "name": "eval_questions.csv", "status": "processed"}
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Request

from api.deps import current_user
from config import ATTACH_MAX_BYTES, ATTACHMENTS_ENABLED
from core import parsers, resources
from db import connection
from db.repositories import Conversations, Documents

router = APIRouter()


def _public(doc: dict) -> dict:
    return {
        "file_id": doc["id"],
        "name": doc["filename"],
        "status": doc["status"],
        "description": doc.get("description", ""),
        "n_chunks": doc.get("n_chunks", 0),
        "error": doc.get("error", ""),
    }


async def _owned_conversation(conv_id: int, user: dict) -> dict:
    conv = await connection.run(Conversations.owned_by, conv_id, user["id"])
    if conv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện.")
    return conv


@router.get("/api/files/supported")
async def supported():
    return {
        "enabled": ATTACHMENTS_ENABLED,
        "extensions": sorted(parsers.supported_extensions()),
        "max_bytes": ATTACH_MAX_BYTES,
    }


@router.get("/api/conversations/{conv_id}/files")
async def list_files(conv_id: int, user: dict = Depends(current_user)):
    await _owned_conversation(conv_id, user)
    docs = await connection.run(Documents.list_for_conversation, conv_id)
    return {"files": [_public(d) for d in docs]}


@router.post("/api/conversations/{conv_id}/files")
async def upload_file(conv_id: int, request: Request,
                      user: dict = Depends(current_user)):
    if not ATTACHMENTS_ENABLED:
        raise HTTPException(status_code=400, detail="Tính năng đính kèm đang tắt.")
    await _owned_conversation(conv_id, user)

    filename = unquote(request.headers.get("X-Filename", "")).strip()
    filename = Path(filename).name          # chặn ../ trong tên tệp
    if not filename:
        raise HTTPException(status_code=400, detail="Thiếu tên tệp (header X-Filename).")

    payload = await request.body()
    if not payload:
        raise HTTPException(status_code=400, detail="Tệp rỗng.")
    if len(payload) > ATTACH_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Tệp quá lớn (tối đa {ATTACH_MAX_BYTES // (1024 * 1024)} MB).")

    suffix = Path(filename).suffix or ".bin"
    tmp = Path(tempfile.gettempdir()) / f"upload_{conv_id}_{abs(hash(filename))}{suffix}"
    tmp.write_bytes(payload)

    try:
        doc = await connection.run(
            resources.ingest_upload,
            tmp_path=tmp, filename=filename, user_id=user["id"],
            conversation_id=conv_id, mime_type=request.headers.get("Content-Type", ""),
            n_bytes=len(payload))
    except resources.UploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    return _public(doc)


@router.delete("/api/files/{doc_id}")
async def delete_file(doc_id: int, user: dict = Depends(current_user)):
    doc = await connection.run(Documents.owned_by, doc_id, user["id"])
    if doc is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp.")
    await connection.run(resources.delete_document, doc_id, doc.get("conversation_id"))
    return {"ok": True}

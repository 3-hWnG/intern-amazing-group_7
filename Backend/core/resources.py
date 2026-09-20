"""Tệp đính kèm theo cuộc trò chuyện: nạp, liệt kê, xoá.

    tải lên -> parse (parsers.py) -> lưu chunk vào SQLite -> tra bằng BM25 (chunk_index.py)

Tệp chỉ tra được trong ĐÚNG cuộc trò chuyện đó, và chỉ vào câu trả lời qua
Evidence Pack (có id nguồn như mọi nguồn khác).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from config import ATTACH_MAX_PER_CONVERSATION, ATTACHMENTS_ENABLED, UPLOAD_DIR
from core import chunk_index, parsers
from db.repositories import DocumentChunks, Documents


def has_attachments(conversation_id: int | None) -> bool:
    if not conversation_id or not ATTACHMENTS_ENABLED:
        return False
    return any(d["status"] == "processed"
               for d in Documents.list_for_conversation(conversation_id))


class UploadError(Exception):
    pass


def ingest_upload(*, tmp_path: Path, filename: str, user_id: int,
                  conversation_id: int, mime_type: str = "",
                  n_bytes: int = 0) -> dict:
    """Parse -> lưu chunk -> đánh dấu processed. Trả về bản ghi document."""
    if not ATTACHMENTS_ENABLED:
        raise UploadError("Tính năng đính kèm đang tắt.")

    if Documents.count_for_conversation(conversation_id) >= ATTACH_MAX_PER_CONVERSATION:
        raise UploadError(
            f"Mỗi cuộc trò chuyện tối đa {ATTACH_MAX_PER_CONVERSATION} tệp. "
            f"Xoá bớt tệp cũ rồi thử lại.")

    ext = Path(filename).suffix.lower()
    if ext not in parsers.supported_extensions():
        raise UploadError(
            f"Chưa hỗ trợ định dạng {ext or '(không rõ)'}. "
            f"Hỗ trợ: {', '.join(sorted(parsers.supported_extensions()))}")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    doc = Documents.create(
        scope="conversation", user_id=user_id, conversation_id=conversation_id,
        filename=filename, mime_type=mime_type, n_bytes=n_bytes, status="pending")

    stored = UPLOAD_DIR / f"{doc['id']}_{Path(filename).name}"
    try:
        shutil.copyfile(tmp_path, stored)
        chunks = parsers.parse(stored)
        chunk_ids = DocumentChunks.add_many(doc["id"], chunks)
        chunk_index.add_chunks([{"id": cid, "content": ch["content"]}
                                for cid, ch in zip(chunk_ids, chunks)],
                               document_id=doc["id"], conversation_id=conversation_id,
                               filename=filename)
        Documents.set_details(doc["id"], storage_path=str(stored),
                              description=parsers.describe(stored, chunks))
        Documents.mark(doc["id"], "processed", n_chunks=len(chunks))
    except (parsers.UnsupportedFile, parsers.MissingDependency) as exc:
        Documents.mark(doc["id"], "failed", error=str(exc))
        raise UploadError(str(exc)) from exc
    except Exception as exc:
        Documents.mark(doc["id"], "failed", error=str(exc))
        raise UploadError(f"Không xử lý được tệp: {exc}") from exc

    return Documents.by_id(doc["id"])


def delete_document(doc_id: int, conversation_id: int | None = None) -> None:
    doc = Documents.by_id(doc_id)
    if doc is None:
        return
    chunk_index.delete_document(doc_id, conversation_id or doc.get("conversation_id"))
    path = doc.get("storage_path") or ""
    if path and str(UPLOAD_DIR) in str(path):
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass
    Documents.delete(doc_id)       # chunk xoá theo nhờ ON DELETE CASCADE

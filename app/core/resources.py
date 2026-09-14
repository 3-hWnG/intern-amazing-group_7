"""Sổ đăng ký tài nguyên — tầng đứng giữa "có những tệp nào" và "tra trong đó".

Hai phạm vi:

    scope = 'global'        Dataset thủ tục hành chính. Đánh chỉ mục MỘT LẦN
                            (data/chromadb_eval + bm25_index.pkl đã dựng sẵn),
                            LUÔN tra được ở mọi cuộc trò chuyện, mọi người
                            dùng. Đăng ký ở đây chỉ để trợ lý BIẾT nó tồn tại.

    scope = 'conversation'  Tệp người dùng đính kèm. Parse -> chunk -> nhúng
                            vào collection "doc_chunks", chỉ tra được trong
                            đúng cuộc trò chuyện đó.

Hàm quan trọng nhất là `manifest()`: nó trả về MÔ TẢ của các tệp, KHÔNG trả về
nội dung. Mô hình đọc manifest để biết "có một bảng 70 thủ tục" rồi tự quyết
định có tra hay không — thay vì bị nhét 70 dòng vào mỗi lượt chat.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from config import (ATTACH_MAX_PER_CONVERSATION, ATTACHMENTS_ENABLED,
                    DATASET_PATH, GLOBAL_KB_NAME, GLOBAL_KB_TOOL, UPLOAD_DIR)
from core import chunk_index, parsers
from db.repositories import DocumentChunks, Documents


# ==========================================================================
# tri thức chung
# ==========================================================================
def global_description() -> str:
    """Mô tả dataset nội bộ — đủ để mô hình biết khi nào nên tra."""
    from domain.records import get_procedures
    procedures = get_procedures()
    fields = []
    for p in procedures:
        if p.linh_vuc and p.linh_vuc not in fields:
            fields.append(p.linh_vuc)
    top = ", ".join(fields[:6]) + ("..." if len(fields) > 6 else "")
    return (f"{len(procedures)} thủ tục hành chính"
            + (f" (lĩnh vực: {top})" if top else "")
            + "; mỗi thủ tục có thành phần hồ sơ, thời gian giải quyết, "
              "lệ phí, nơi nộp")


def ensure_global_kb() -> dict:
    """Đăng ký dataset là tài liệu global. Gọi lúc khởi động, an toàn khi lặp."""
    existing = Documents.by_filename_global(DATASET_PATH.name)
    description = global_description()
    if existing:
        if existing.get("description") != description:
            from db.connection import get_conn
            conn = get_conn()
            conn.execute("UPDATE documents SET description = ? WHERE id = ?",
                         (description, existing["id"]))
            conn.commit()
            existing["description"] = description
        return existing

    from domain.records import get_procedures
    doc = Documents.create(
        scope="global",
        filename=DATASET_PATH.name,
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        storage_path=str(DATASET_PATH),
        description=description,
    )
    # KHÔNG chunk, KHÔNG nhúng lại: chỉ mục của nó đã có sẵn từ ingest.py.
    Documents.mark(doc["id"], "processed", n_chunks=len(get_procedures()))
    return Documents.by_id(doc["id"])


# ==========================================================================
# manifest — METADATA, không phải nội dung
# ==========================================================================
def manifest(conversation_id: int | None = None) -> str:
    lines = []
    for doc in Documents.list_global():
        lines.append(f"- [chung] {GLOBAL_KB_NAME}: {doc['description']} "
                     f"-> dùng {GLOBAL_KB_TOOL}")
    if conversation_id and ATTACHMENTS_ENABLED:
        for doc in Documents.list_for_conversation(conversation_id):
            if doc["status"] != "processed":
                continue
            lines.append(f"- [tệp đính kèm] {doc['filename']}: "
                         f"{doc['description']} -> dùng search_attachments")
    return "\n".join(lines)


def has_attachments(conversation_id: int | None) -> bool:
    if not conversation_id or not ATTACHMENTS_ENABLED:
        return False
    return any(d["status"] == "processed"
               for d in Documents.list_for_conversation(conversation_id))


# ==========================================================================
# nạp tệp đính kèm
# ==========================================================================
class UploadError(Exception):
    pass


def ingest_upload(*, tmp_path: Path, filename: str, user_id: int,
                  conversation_id: int, mime_type: str = "",
                  n_bytes: int = 0) -> dict:
    """Parse -> lưu chunk -> nhúng -> đánh dấu processed. Trả về bản ghi document."""
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
        from db.connection import get_conn
        conn = get_conn()
        conn.execute("UPDATE documents SET storage_path = ? WHERE id = ?",
                     (str(stored), doc["id"]))
        conn.commit()

        chunks = parsers.parse(stored)
        chunk_ids = DocumentChunks.add_many(doc["id"], chunks)
        rows = [{"id": cid, "content": ch["content"]}
                for cid, ch in zip(chunk_ids, chunks)]
        chunk_index.add_chunks(rows, document_id=doc["id"],
                               conversation_id=conversation_id, filename=filename)

        description = parsers.describe(stored, chunks)
        conn.execute("UPDATE documents SET description = ? WHERE id = ?",
                     (description, doc["id"]))
        conn.commit()
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

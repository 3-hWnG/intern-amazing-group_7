"""Hội thoại nhiều cửa sổ + gửi câu hỏi qua hàng đợi.

Đây là nơi RÁP: lưu câu hỏi -> đẩy MỘT job vào hàng đợi -> job đọc ngữ cảnh,
chạy orchestrator, lưu câu trả lời + Evidence Pack -> stream sự kiện về.
Mọi lời gọi LLM của một lượt (kể cả tóm tắt ngữ cảnh) nằm TRONG job, nên hàng
đợi đảm bảo mô hình xử lý từng tin nhắn một.

Luồng trả về là NDJSON, mỗi dòng một sự kiện:
    {"type": "queue",  "position": 2, "text": "..."}
    {"type": "status", "text": "Đang tra cứu nguồn chính thống qua MCP…"}
    {"type": "delta",  "text": "..."}          câu trả lời ĐÃ kiểm chứng, phát theo mẩu
    {"type": "done",   "message_id": 12, "kind": "answer", "verdict": "PASS", "sources": [...]}
    {"type": "error",  "text": "..."}
"""

from __future__ import annotations

import asyncio
import json
import time
import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.deps import current_user
from api.schemas import ChatRequest, ConversationCreate, ConversationRename, FeedbackRequest
from config import QUEUE_ENABLED
from core import llm, orchestrator, queue, summarizer
from db import connection
from db.repositories import (Conversations, Evidence, Feedback, JobLog, Messages,
                             UserProfiles)

router = APIRouter()
REPLAY_CHARS = 24


def _title_from(question: str) -> str:
    words = (question or "").split()
    return " ".join(words[:8])[:120] or "Cuộc trò chuyện mới"


def _event(**payload) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


async def _owned(conv_id: int, user: dict) -> dict:
    conv = await connection.run(Conversations.owned_by, conv_id, user["id"])
    if conv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện.")
    return conv


# ------------------------------------------------------- CRUD hội thoại ----
@router.get("/api/conversations")
async def list_conversations(user: dict = Depends(current_user)):
    return {"conversations": await connection.run(Conversations.list_for, user["id"])}


@router.post("/api/conversations")
async def create_conversation(body: ConversationCreate, user: dict = Depends(current_user)):
    return {"conversation": await connection.run(Conversations.create, user["id"], body.title)}


@router.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: int, user: dict = Depends(current_user)):
    conv = await _owned(conv_id, user)
    messages = await connection.run(Messages.list_for, conv_id)
    for m in messages:
        try:
            m["sources"] = json.loads(m["sources"] or "[]")
        except Exception:
            m["sources"] = []
        m["has_evidence"] = bool(m["has_evidence"])
        m.pop("intent_json", None)
    from db.repositories import Documents
    documents = await connection.run(Documents.list_for_conversation, conv_id)
    return {"conversation": {k: conv[k] for k in ("id", "title", "created_at", "updated_at")},
            "messages": messages, "documents": documents}


@router.patch("/api/conversations/{conv_id}")
async def rename_conversation(conv_id: int, body: ConversationRename,
                              user: dict = Depends(current_user)):
    await _owned(conv_id, user)
    await connection.run(Conversations.rename, conv_id, user["id"], body.title)
    return {"ok": True}


@router.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: int, user: dict = Depends(current_user)):
    await _owned(conv_id, user)
    from core import resources
    from db.repositories import Documents
    for doc in await connection.run(Documents.list_for_conversation, conv_id):
        await connection.run(resources.delete_document, doc["id"], conv_id)
    await connection.run(Conversations.delete, conv_id, user["id"])
    return {"ok": True}


@router.get("/api/messages/{message_id}/evidence")
async def message_evidence(message_id: int, user: dict = Depends(current_user)):
    """Evidence Pack đã dùng để trả lời — chứng minh RAG ngay trên giao diện."""
    pack = await connection.run(Evidence.for_message, message_id, user["id"])
    if pack is None:
        raise HTTPException(status_code=404, detail="Tin nhắn này không có Evidence Pack.")
    return {"evidence": pack, "model": llm.model_info()}


# ------------------------------------------------ bộ nhớ dài hạn ----
@router.get("/api/profile")
async def get_profile(user: dict = Depends(current_user)):
    return {"profile": await connection.run(UserProfiles.get, user["id"])}


@router.delete("/api/profile")
async def clear_profile(user: dict = Depends(current_user)):
    await connection.run(UserProfiles.clear, user["id"])
    return {"ok": True}


# --------------------------------------------------------------- chat ----
def _run_job(conv_id: int, user_id: int, user_msg_id: int, question: str, emit) -> None:
    """Chạy trong worker của hàng đợi (luồng riêng): ngữ cảnh -> orchestrator -> lưu."""
    def send(**payload) -> None:
        emit(_event(**payload))

    send(type="status", text="Đang đọc lại ngữ cảnh cuộc trò chuyện…")
    summary, recent = summarizer.build_context(conv_id)
    history = [{"role": m["role"], "content": m["content"], "kind": m.get("kind") or ""}
               for m in recent if m["id"] != user_msg_id]
    profile = UserProfiles.get(user_id)

    result = orchestrator.run_turn(
        orchestrator.TurnInput(question=question, history=history, summary=summary,
                               profile=profile, conversation_id=conv_id),
        status=lambda text: send(type="status", text=text))

    message_id = Messages.add(conv_id, "assistant", result.text, kind=result.kind,
                              verdict=result.verdict, sources=result.sources,
                              intent=result.intent,
                              token_estimate=summarizer.estimate_tokens(result.text))
    if result.evidence is not None:
        Evidence.add(message_id, result.evidence.get("question", ""), result.evidence)
    if result.profile_update:
        profile = UserProfiles.update(user_id, **result.profile_update)

    for i in range(0, len(result.text), REPLAY_CHARS):
        send(type="delta", text=result.text[i:i + REPLAY_CHARS])
        time.sleep(0.006)                       # giữ hiệu ứng gõ chữ
    send(type="done", message_id=message_id, kind=result.kind, verdict=result.verdict,
         sources=result.sources, has_evidence=result.evidence is not None,
         intent=result.intent.get("intent", ""), timings=result.timings, profile=profile)


@router.post("/api/conversations/{conv_id}/chat")
async def chat(conv_id: int, body: ChatRequest, user: dict = Depends(current_user)):
    await _owned(conv_id, user)
    question = (body.text or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Câu hỏi trống.")

    if not await connection.run(Messages.list_for, conv_id):
        await connection.run(Conversations.rename, conv_id, user["id"], _title_from(question))
    user_msg_id = await connection.run(Messages.add, conv_id, "user", question,
                                       token_estimate=summarizer.estimate_tokens(question))

    def produce(emit):
        try:
            _run_job(conv_id, user["id"], user_msg_id, question, emit)
        except Exception as exc:
            traceback.print_exc()
            emit(_event(type="error", text=f"Lỗi xử lý: {exc}"))

    headers = {"X-Conversation-Id": str(conv_id), "Cache-Control": "no-cache"}

    if not QUEUE_ENABLED:
        async def direct():
            chunks: list[str] = []
            await asyncio.to_thread(produce, chunks.append)
            for chunk in chunks:
                yield chunk
        return StreamingResponse(direct(), media_type="application/x-ndjson", headers=headers)

    try:
        job = queue.manager.submit(produce)
    except queue.QueueFull as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    headers["X-Queue-Position"] = str(job.position)

    async def body_stream():
        if job.position > 0:
            yield _event(type="queue", position=job.position,
                         text=f"Đang xếp hàng — còn {job.position} lượt trước bạn…")
        async for chunk in queue.manager.stream(job):
            # thông báo lỗi/timeout của hàng đợi là chữ thô -> gói lại thành sự kiện
            yield chunk if chunk.startswith("{") else _event(type="error", text=chunk.strip())
        wait_ms = (job.started_at - job.enqueued_at) * 1000 if job.started_at else 0
        proc_ms = (job.finished_at - job.started_at) * 1000 if job.finished_at else 0
        await connection.run(JobLog.add, user["id"], conv_id, job.error or "done",
                             wait_ms, proc_ms, job.position)

    return StreamingResponse(body_stream(), media_type="application/x-ndjson", headers=headers)


# ----------------------------------------------------------- phản hồi ----
@router.post("/api/feedback")
async def feedback(body: FeedbackRequest, user: dict = Depends(current_user)):
    msg = await connection.run(Messages.owned_by, body.message_id, user["id"])
    if msg is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn.")
    if body.verdict not in {"phu_hop", "khong_phu_hop"}:
        raise HTTPException(status_code=400, detail="Giá trị phản hồi không hợp lệ.")
    await connection.run(Feedback.add, body.message_id, user["id"], body.verdict, body.note)
    return {"ok": True}


@router.get("/api/queue/status")
async def queue_status(user: dict = Depends(current_user)):
    return {
        "enabled": QUEUE_ENABLED,
        "concurrency": queue.manager.concurrency,
        "depth": queue.manager.depth,
        "stats": await connection.run(JobLog.stats),
    }

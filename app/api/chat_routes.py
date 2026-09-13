"""Hội thoại nhiều cửa sổ + gửi câu hỏi qua hàng đợi.

Đây là nơi RÁP: lấy ngữ cảnh từ DB -> dựng plan (pipeline thuần nghiệp vụ) ->
đẩy vào hàng đợi -> stream chữ về -> lưu lại. Bản thân file này không chứa
logic truy hồi hay logic phân tầng.
"""

from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.deps import current_user
from api.schemas import (ChatRequest, ConversationCreate, ConversationRename,
                         FeedbackRequest)
from config import QUEUE_ENABLED
from core import formatter, llm, pipeline, queue, summarizer
from db import connection
from db.repositories import Conversations, Feedback, JobLog, Messages

router = APIRouter()


def _title_from(question: str) -> str:
    words = (question or "").split()
    return " ".join(words[:8])[:120] or "Cuộc trò chuyện mới"


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
    return {"conversation": conv, "messages": messages}


@router.patch("/api/conversations/{conv_id}")
async def rename_conversation(conv_id: int, body: ConversationRename,
                              user: dict = Depends(current_user)):
    await _owned(conv_id, user)
    await connection.run(Conversations.rename, conv_id, user["id"], body.title)
    return {"ok": True}


@router.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: int, user: dict = Depends(current_user)):
    await _owned(conv_id, user)
    await connection.run(Conversations.delete, conv_id, user["id"])
    return {"ok": True}


# --------------------------------------------------------------- chat ----
@router.post("/api/conversations/{conv_id}/chat")
async def chat(conv_id: int, body: ChatRequest, user: dict = Depends(current_user)):
    conv = await _owned(conv_id, user)
    question = (body.text or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Câu hỏi trống.")

    # 1. đặt tên hội thoại theo câu hỏi đầu tiên
    existing = await connection.run(Messages.list_for, conv_id)
    if not existing:
        await connection.run(Conversations.rename, conv_id, user["id"], _title_from(question))

    # 2. lưu câu hỏi
    await connection.run(Messages.add, conv_id, "user", question,
                         token_estimate=summarizer.estimate_tokens(question))

    # 3. lấy ngữ cảnh (tóm tắt nếu quá dài) + trạng thái chờ làm rõ
    pending = await connection.run(Conversations.take_pending, conv_id)
    summary, recent = await connection.run(summarizer.build_context, conv_id)
    history = summarizer.as_history(summary, recent[:-1])   # bỏ chính câu vừa hỏi

    # 4. dựng kế hoạch trả lời (thuần nghiệp vụ, không chạm DB)
    last_title = await connection.run(Conversations.last_procedure_title, conv_id)
    plan = await asyncio.to_thread(pipeline.build, question,
                                   pending=pending, history=history,
                                   context_hint=last_title)

    if plan.pending_to_set is not None:
        await connection.run(Conversations.set_pending, conv_id, plan.pending_to_set)

    # Ghi nhớ thủ tục vừa nói tới, để câu hỏi ngắn tiếp theo ("tốn bao nhiêu
    # tiền?", "mất bao lâu?") biết đang hỏi về cái gì.
    if plan.top_row_id is not None:
        await connection.run(Conversations.set_last_row, conv_id, plan.top_row_id)

    # 5. hàm sinh chữ — worker của hàng đợi sẽ chạy hàm này trong luồng riêng
    #    `collected` CHỈ chứa phần thân câu trả lời. Footer (nhãn tầng + dòng
    #    miễn trừ) là phần TRÌNH BÀY: gửi cho người dùng nhưng KHÔNG lưu vào DB.
    #    Nếu lưu, nó lọt vào lịch sử hội thoại và mô hình sẽ chép lại nguyên văn
    #    bản ghi cũ - đã gây ra lỗi bịa "Thủ tục tạm trú" bằng nội dung của
    #    thủ tục nhận cha mẹ con.
    collected: list[str] = []

    def produce(emit):
        if plan.text is not None:
            collected.append(plan.text)
            emit(plan.text)
        else:
            for chunk in llm.stream_chat(plan.system, plan.user, plan.history):
                collected.append(chunk)
                emit(chunk)
        emit(formatter.footer(plan.tier, plan.sources))    # KHÔNG vào collected

    headers = {
        "X-Tier": plan.tier.value,
        "X-Confidence": f"{plan.confidence:.3f}",
        "X-Sources": ",".join(plan.sources),
        "X-Factcheck": plan.factcheck_summary,
        "X-Conversation-Id": str(conv_id),
    }

    if not QUEUE_ENABLED:
        async def direct():
            for chunk in _sync_iter(produce):
                yield chunk
            await _persist(conv_id, plan, collected, 0, 0, 0)
        return StreamingResponse(direct(), media_type="text/plain", headers=headers)

    try:
        job = queue.manager.submit(produce)
    except queue.QueueFull as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    headers["X-Queue-Position"] = str(job.position)

    async def body_stream():
        if job.position > 0:
            yield f"_[Đang xếp hàng — còn {job.position} người trước bạn]_\n\n"
        async for chunk in queue.manager.stream(job):
            yield chunk
        wait_ms = (job.started_at - job.enqueued_at) * 1000 if job.started_at else 0
        proc_ms = (job.finished_at - job.started_at) * 1000 if job.finished_at else 0
        await _persist(conv_id, plan, collected, wait_ms, proc_ms, job.position)

    return StreamingResponse(body_stream(), media_type="text/plain", headers=headers)


def _sync_iter(produce):
    """Chạy producer đồng bộ và gom chữ (dùng khi TẮT hàng đợi)."""
    out: list[str] = []
    produce(out.append)
    return out


async def _persist(conv_id, plan, collected, wait_ms, proc_ms, position):
    answer = "".join(collected)
    await connection.run(
        Messages.add, conv_id, "assistant", answer,
        tier=plan.tier.value, confidence=plan.confidence,
        sources=plan.sources, factcheck=plan.factcheck_summary,
        token_estimate=summarizer.estimate_tokens(answer))
    await connection.run(JobLog.add, None, conv_id, "done", wait_ms, proc_ms, position)


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

"""main.py — FastAPI Application, APIs & Giao diện Trợ lý Pháp lý hoàn chỉnh."""

from contextlib import asynccontextmanager
from datetime import datetime
import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _APP_DIR.parent
for _p in [str(_APP_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from typing import Any, Dict, List, Optional
import json
import traceback

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import ollama
import uvicorn

from config import (
    DEV_TOOLS_ENABLED, HOST, LLM_MODEL_NAME, LLM_OPTIONS, PORT,
    QUEUE_CONCURRENCY, RETENTION_DAYS
)
from database import (
    authenticate_user, create_conversation, create_session, delete_conversation,
    delete_session, get_conversation, get_db_stats, get_messages, get_user_from_token,
    init_db, list_conversations, maybe_summarize_context, purge_old, rate_message,
    register_user, reset_all_conversations, reset_database, reset_user_conversations,
    save_message, update_conversation_title
)
from ingest import get_procedures_map, load_procedures
from models import (
    Candidate, ChatMessageOut, ChatRequest, ConversationCreate, ConversationOut,
    FeedbackRequest, Procedure, ResetRequest, UserLogin, UserOut, UserRegister
)
from queue_manager import queue_manager
from retrieval import bm25_manager, classify_intent, embeddings, reranker, retrieve, vectorstore
from tiers import (
    Tier, check_special_queries, clean_local_references, decide_tier,
    format_tier_a_response, format_tier_b_response, format_tier_c_prompt,
    format_traffic_llm_messages, format_civic_llm_messages, get_traffic_response,
    is_situational_query, is_smalltalk, web_search_gov
)


# ==============================================================================
# 1. Lifespan: Khởi tạo mô hình và CSDL
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n=======================================================")
    print("   KHỞI ĐỘNG HỆ THỐNG TRỢ LÝ PHÁP LÝ & DỊCH VỤ CÔNG")
    print("=======================================================")
    
    # 1. CSDL SQLite
    init_db()
    print("[1/5] CSDL SQLite (app.db): Đã sẵn sàng.")
    if RETENTION_DAYS:
        try:
            removed = purge_old(RETENTION_DAYS)
            if removed:
                print(f"[*] Đã dọn dẹp {removed} cuộc trò chuyện quá hạn lưu trữ ({RETENTION_DAYS} ngày).")
        except Exception as e:
            print(f"[*] Cảnh báo dọn dẹp hội thoại: {e}")

    # 2. Thủ tục & BM25
    procedures = load_procedures()
    procedures_map = get_procedures_map()
    bm25_manager.build_index(procedures)
    print(f"[2/5] Dữ liệu thủ tục: Đã tải {len(procedures)} thủ tục và chỉ mục BM25.")

    # 3. Vector Database
    coll = vectorstore.get_collection()
    print(f"[3/5] ChromaDB: Sẵn sàng ({coll.count()} views đa chiều).")

    # 4. Warm-up Embeddings & Reranker
    try:
        embeddings.encode(["Khởi động"])
        print(f"[4/5] Embedding Model: Sẵn sàng ({embeddings.device}).")
    except Exception as e:
        print(f"[4/5] Cảnh báo mô hình nhúng: {e}")

    if reranker.is_available():
        try:
            reranker.score("test", ["test"])
            print(f"[4/5] Cross-Encoder Reranker: Sẵn sàng ({reranker.device}).")
        except Exception as e:
            print(f"[4/5] Cảnh báo Reranker: {e}")
    else:
        print("[4/5] Cross-Encoder Reranker: Tắt (hoặc không khả dụng).")

    # 5. Hàng đợi Async
    await queue_manager.start()
    print(f"[5/5] Hàng đợi xử lý: Đã kích hoạt ({queue_manager.concurrency} worker).")

    if DEV_TOOLS_ENABLED:
        print("  " + "!" * 55)
        print("  ! DEV_TOOLS_ENABLED = True — Có công cụ Reset dữ liệu (DEV)")
        print("  " + "!" * 55)

    print("-------------------------------------------------------")
    print(f"=== MÁY CHỦ SẴN SÀNG TẠI: http://{HOST if HOST != '0.0.0.0' else '127.0.0.1'}:{PORT} ===")
    print("    (Mở trình duyệt truy cập ngay đường link trên)")
    print("=======================================================\n")

    yield

    await queue_manager.stop()
    print("[*] Đã dừng các worker hàng đợi.")


app = FastAPI(title="Trợ Lý Pháp Lý - Nhóm 7", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# 2. Dependency Xác thực Người dùng
# ==============================================================================
def get_current_user(token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    auth_token = token
    if not auth_token and authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]
    if auth_token:
        return get_user_from_token(auth_token)
    return None


# ==============================================================================
# 3. API Quản lý Tài khoản (Auth)
# ==============================================================================
@app.post("/api/auth/register", response_model=UserOut)
@app.post("/api/register", response_model=UserOut)
def api_register(data: UserRegister, response: Response):
    user = register_user(data.email, data.password, data.full_name or "Công dân")
    if not user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")
    token = create_session(user["id"])
    response.set_cookie(key="token", value=token, httponly=True, max_age=86400 * 30, samesite="lax", path="/")
    return {**user, "token": token}


@app.post("/api/auth/login", response_model=UserOut)
@app.post("/api/login", response_model=UserOut)
def api_login(data: UserLogin, response: Response):
    user = authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác.")
    token = create_session(user["id"])
    response.set_cookie(key="token", value=token, httponly=True, max_age=86400 * 30, samesite="lax", path="/")
    return {**user, "token": token}


@app.post("/api/auth/logout")
@app.post("/api/logout")
def api_logout(response: Response, token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    auth_token = token
    if not auth_token and authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]
    if auth_token:
        delete_session(auth_token)
    response.delete_cookie(key="token", path="/")
    return {"message": "Đã đăng xuất thành công."}


@app.get("/api/auth/me")
@app.get("/api/me")
def api_me(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    return {"authenticated": user is not None, "user": user}


# ==============================================================================
# 4. API Phiên Hội thoại (Conversations)
# ==============================================================================
@app.get("/api/conversations")
def api_list_conversations(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    user_id = user["id"] if user else None
    return list_conversations(user_id)


@app.post("/api/conversations")
def api_create_conversation(data: ConversationCreate, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    user_id = user["id"] if user else None
    return create_conversation(user_id, data.title or "Cuộc trò chuyện mới")


@app.get("/api/conversations/{conv_id}/messages")
def api_get_conversation_messages(conv_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    user_id = user["id"] if user else None
    conv = get_conversation(conv_id, user_id)
    if not conv:
        # Cho phép xem nếu là phiên khách vãng lai
        conv = get_conversation(conv_id, None)
        if not conv:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện.")
    return get_messages(conv_id)


@app.delete("/api/conversations/{conv_id}")
def api_delete_conversation(conv_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    user_id = user["id"] if user else None
    success = delete_conversation(conv_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không thể xóa cuộc trò chuyện.")
    return {"message": "Đã xóa thành công."}


@app.post("/api/messages/{msg_id}/feedback")
def api_feedback(msg_id: str, data: FeedbackRequest):
    success = rate_message(msg_id, data.rating)
    if not success:
        raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại.")
    return {"message": "Cảm ơn bạn đã gửi phản hồi!"}


# ==============================================================================
# 4.5. Công cụ Phát triển & Cấu hình Hệ thống (Dev Tools)
# ==============================================================================
@app.get("/api/config")
def api_get_config():
    return {
        "dev_tools": DEV_TOOLS_ENABLED,
        "queue_concurrency": queue_manager.concurrency,
    }


@app.get("/api/dev/stats")
def api_dev_stats():
    if not DEV_TOOLS_ENABLED:
        raise HTTPException(status_code=403, detail="Công cụ phát triển đang bị tắt.")
    return get_db_stats()


@app.post("/api/dev/reset")
def api_dev_reset(body: ResetRequest, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not DEV_TOOLS_ENABLED:
        raise HTTPException(status_code=403, detail="Công cụ phát triển đang bị tắt.")

    if body.confirm != "XOA":
        raise HTTPException(status_code=400, detail='Phải gõ đúng "XOA" để xác nhận.')

    user_id = user["id"] if user else None

    if body.scope == "my_conversations":
        deleted = reset_user_conversations(user_id)
        return {"ok": True, "scope": body.scope, "note": f"Đã xóa {deleted} cuộc trò chuyện của bạn."}

    if body.scope == "all_conversations":
        reset_all_conversations()
        return {"ok": True, "scope": body.scope, "note": "Đã xóa toàn bộ cuộc trò chuyện của mọi người dùng."}

    if body.scope == "everything":
        reset_database()
        return {"ok": True, "scope": body.scope, "note": "Đã xóa toàn bộ CSDL kể cả tài khoản. Vui lòng đăng ký/đăng nhập lại nếu cần."}

    raise HTTPException(status_code=400, detail="Phạm vi (scope) không hợp lệ.")


# ==============================================================================
# 5. Core Chat Engine (Được xử lý tuần tự qua Queue)
# ==============================================================================
def is_traffic_query(query: str) -> bool:
    q = query.lower()
    traffic_keywords = [
        "xe", "giao thông", "giao thong", "đèn đỏ", "den do", "đèn vàng", "den vang",
        "mũ bảo hiểm", "mu bao hiem", "nón bảo hiểm", "non bao hiem", "nồng độ cồn",
        "nong do con", "bằng lái", "bang lai", "gplx", "tốc độ", "toc do", "lấn làn",
        "lan duong", "làn đường", "biển số", "bien so", "đăng kiểm", "dang kiem",
        "cavet", "ca vet", "tước bằng", "tuoc bang", "dừng đỗ", "dung do", "ngược chiều",
        "nguoc chieu", "uống rượu", "uong ruou", "uống bia", "uong bia", "thổi cồn",
        "thoi con", "bắn tốc độ", "ban toc do", "bảo hiểm xe", "bao hiem xe"
    ]
    return any(k in q for k in traffic_keywords)


def execute_chat_logic(query: str, conv_id: str) -> Dict[str, Any]:
    procedures_map = get_procedures_map()

    # 1. Kiểm tra Xã giao (Smalltalk)
    is_st, st_response = is_smalltalk(query)
    if is_st:
        msg = save_message(conv_id, role="assistant", content=st_response, tier="SMALLTALK", sources=[])
        return {
            "answer": st_response,
            "tier": "SMALLTALK",
            "tier_label": "Xã giao thân mật",
            "confidence": 1.0,
            "sources": [],
            "message_id": msg["id"]
        }

    # 1.1 Kiểm tra các câu hỏi tình huống đời thường đặc thù (CCCD, chặt cây vườn nhà, tiếng ồn...)
    spec = check_special_queries(query)
    if spec:
        msg = save_message(conv_id, role="assistant", content=spec["answer"], tier=spec["tier"], sources=spec["sources"])
        return {
            **spec,
            "message_id": msg["id"]
        }

    # 1.2 Kiểm tra câu hỏi luật giao thông đường bộ
    if is_traffic_query(query):
        traffic_ans = get_traffic_response(query)
        if traffic_ans:
            answer_text = traffic_ans
        else:
            messages = format_traffic_llm_messages(query)
            try:
                res = ollama.chat(
                    model=LLM_MODEL_NAME,
                    messages=messages,
                    options=LLM_OPTIONS
                )
                answer_text = res["message"]["content"].strip()
            except Exception as e:
                answer_text = (
                    "Quy định pháp luật giao thông đường bộ:\n"
                    "- Mọi người tham gia giao thông phải chấp hành hiệu lệnh đèn tín hiệu, đi đúng làn đường, đội mũ bảo hiểm đạt chuẩn và tuân thủ tốc độ quy định.\n"
                    "- Nghiêm cấm điều khiển phương tiện khi trong máu hoặc hơi thở có nồng độ cồn."
                )
        answer_text = clean_local_references(answer_text)
        msg = save_message(conv_id, role="assistant", content=answer_text, tier="TRAFFIC", sources=[])
        return {
            "answer": answer_text,
            "tier": "TRAFFIC",
            "tier_label": "Ngoài danh mục",
            "confidence": 1.0,
            "sources": [],
            "message_id": msg["id"]
        }

    # 2. Truy hồi Hybrid (Dense + BM25 + Reranker)
    candidates = retrieve(query, procedures_map)

    # 4. Quyết định phân tầng (Tier A / B / C)
    tier, confidence = decide_tier(candidates, query)
    top_cand = candidates[0] if candidates else None
    other_cands = candidates[1:3] if len(candidates) > 1 else []

    # 5. Sinh phản hồi tương ứng theo Tầng
    sources = []
    if tier == Tier.TIER_A and top_cand:
        # Tầng A: Dữ liệu CSDL chuẩn xác 100% (Không qua LLM, chống nhại prompt & cắt cụt câu)
        answer_text = format_tier_a_response(top_cand, query=query)
        sources = [top_cand.record.nguon_url] if top_cand.record.nguon_url else []
        tier_label = "Tầng A — Dữ liệu chuẩn xác CSDL"

    elif tier == Tier.TIER_B and top_cand:
        # Tầng B: Làm rõ nhu cầu
        answer_text = format_tier_b_response(candidates, query=query)
        sources = [c.record.nguon_url for c in candidates[:3] if c.record.nguon_url]
        tier_label = "Tầng B — Cần làm rõ nhu cầu thủ tục"

    else:
        # Tầng C: Tra cứu Cổng DVC / Web Internet
        web_info, search_sources = web_search_gov(query)
        if web_info:
            prompt_c = format_tier_c_prompt(query, web_info)
            try:
                res = ollama.chat(
                    model=LLM_MODEL_NAME,
                    messages=[{"role": "user", "content": prompt_c}],
                    options=LLM_OPTIONS
                )
                answer_text = res["message"]["content"].strip()
            except Exception as e:
                answer_text = f"Thông tin tra cứu từ Internet:\n{web_info}"
            sources = search_sources
        elif top_cand:
            # Fallback về Tầng A nếu không tìm thấy trên mạng
            answer_text = format_tier_a_response(top_cand, query=query)
            sources = [top_cand.record.nguon_url] if top_cand.record.nguon_url else []
            tier = Tier.TIER_A
        else:
            answer_text = (
                "Rất tiếc, hiện tại hệ thống chưa tìm thấy thông tin phù hợp cho câu hỏi của bạn.\n\n"
                "💡 Bạn vui lòng tra cứu thêm tại Cổng Dịch vụ công Quốc gia: https://dichvucong.gov.vn "
                "hoặc đến trực tiếp Bộ phận Tiếp nhận & Trả kết quả của UBND cấp xã/phường để được hướng dẫn cụ thể."
            )
        tier_label = "Tầng C — Tra cứu Cổng DVC (.gov.vn)"

    answer_text = clean_local_references(answer_text)

    msg = save_message(conv_id, role="assistant", content=answer_text, tier=tier.value, sources=sources)
    return {
        "answer": answer_text,
        "tier": tier.value,
        "tier_label": tier_label,
        "confidence": round(confidence, 3),
        "sources": sources,
        "message_id": msg["id"]
    }


@app.post("/api/chat")
async def api_chat(data: ChatRequest, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    user_id = user["id"] if user else None
    conv_id = data.conversation_id

    # Tạo hội thoại mới nếu chưa có
    if not conv_id or conv_id == "new":
        title = " ".join(data.query.strip().split()[:6]) or "Cuộc trò chuyện mới"
        conv = create_conversation(user_id=user_id, title=title)
        conv_id = conv["id"]
    else:
        conv = get_conversation(conv_id, user_id)
        if not conv:
            title = " ".join(data.query.strip().split()[:6]) or "Cuộc trò chuyện mới"
            conv = create_conversation(user_id=user_id, title=title)
            conv_id = conv["id"]
        elif conv.get("title") == "Cuộc trò chuyện mới":
            new_title = " ".join(data.query.strip().split()[:6])
            update_conversation_title(conv_id, new_title)

    save_message(conv_id, role="user", content=data.query)

    result, queue_pos = await queue_manager.enqueue(execute_chat_logic, data.query, conv_id)

    try:
        maybe_summarize_context(conv_id)
    except Exception:
        pass

    return {
        **result,
        "conversation_id": conv_id,
        "queue_position": queue_pos
    }


# ==============================================================================
# 6. Giao diện Web SPA Hiện đại (HTML/CSS/JS)
# ==============================================================================
HTML_UI = """<!DOCTYPE html>
<html lang="vi" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trợ Lý Thủ Tục Hành Chính - Nhóm 7</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --bg-main: #1e1e24;
            --bg-sidebar: #18181c;
            --bg-card: #26262e;
            --bg-msg-user: #3b3a4a;
            --bg-msg-bot: #292833;
            --text-primary: #f0f0f5;
            --text-secondary: #9a9aa8;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --border: #333240;
            --tier-a: #10b981;
            --tier-b: #f59e0b;
            --tier-c: #6366f1;
            --tier-st: #8b5cf6;
        }
        [data-theme="light"] {
            --bg-main: #f8fafc;
            --bg-sidebar: #f1f5f9;
            --bg-card: #ffffff;
            --bg-msg-user: #e2e8f0;
            --bg-msg-bot: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --border: #e2e8f0;
            --tier-a: #059669;
            --tier-b: #d97706;
            --tier-c: #4f46e5;
            --tier-st: #7c3aed;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg-main); color: var(--text-primary); height: 100vh; display: flex; overflow: hidden; }
        
        /* Sidebar */
        .sidebar { width: 280px; background: var(--bg-sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; transition: 0.3s; }
        .sidebar-header { padding: 18px 16px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
        .sidebar-header h2 { font-size: 16px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
        .btn-new-chat { margin: 12px 16px; padding: 10px 14px; background: var(--accent); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s; }
        .btn-new-chat:hover { background: var(--accent-hover); }
        .conv-list { flex: 1; overflow-y: auto; padding: 6px 12px; }
        .conv-item { padding: 10px 12px; border-radius: 8px; margin-bottom: 4px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; font-size: 14px; color: var(--text-secondary); transition: 0.2s; }
        .conv-item:hover, .conv-item.active { background: var(--bg-card); color: var(--text-primary); }
        .conv-title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
        .conv-delete { opacity: 0; color: #ef4444; margin-left: 8px; cursor: pointer; transition: 0.2s; }
        .conv-item:hover .conv-delete { opacity: 1; }
        .sidebar-footer { padding: 14px 16px; border-top: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
        .user-info { display: flex; align-items: center; gap: 10px; font-size: 13px; }
        .user-avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--accent); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        
        /* Main Chat Area */
        .main-content { flex: 1; display: flex; flex-direction: column; position: relative; }
        .chat-header { height: 60px; border-bottom: 1px solid var(--border); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: var(--bg-main); z-index: 10; }
        .header-title { display: flex; align-items: center; gap: 12px; }
        .badge-tier {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
            user-select: none;
            letter-spacing: 0.2px;
        }
        /* Tầng A - Xanh ngọc CSDL */
        .badge-tier-a {
            color: #34d399;
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        [data-theme="light"] .badge-tier-a {
            color: #047857;
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        /* Tầng B - Vàng hổ phách Cần làm rõ */
        .badge-tier-b {
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.08);
            border: 1px solid rgba(245, 158, 11, 0.4);
        }
        [data-theme="light"] .badge-tier-b {
            color: #b45309;
            background: rgba(245, 158, 11, 0.08);
            border: 1px solid rgba(217, 119, 6, 0.35);
        }
        /* Ngoài danh mục / Giao thông - Xanh lam nhạt */
        .badge-tier-traffic {
            color: #38bdf8;
            background: rgba(14, 165, 233, 0.08);
            border: 1px solid rgba(14, 165, 233, 0.4);
        }
        [data-theme="light"] .badge-tier-traffic {
            color: #0284c7;
            background: rgba(14, 165, 233, 0.08);
            border: 1px solid rgba(14, 165, 233, 0.35);
        }
        /* Tầng C - Chàm Internet .gov.vn */
        .badge-tier-c {
            color: #818cf8;
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.4);
        }
        [data-theme="light"] .badge-tier-c {
            color: #4338ca;
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.35);
        }
        /* Xã giao thân mật - Tím nhạt */
        .badge-tier-st {
            color: #c084fc;
            background: rgba(168, 85, 247, 0.08);
            border: 1px solid rgba(168, 85, 247, 0.4);
        }
        [data-theme="light"] .badge-tier-st {
            color: #7e22ce;
            background: rgba(168, 85, 247, 0.08);
            border: 1px solid rgba(168, 85, 247, 0.35);
        }
        .header-actions { display: flex; align-items: center; gap: 12px; }
        .btn-icon { background: none; border: 1px solid var(--border); color: var(--text-primary); border-radius: 8px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; }
        .btn-icon:hover { background: var(--bg-card); }
        
        /* Messages Container */
        .chat-body { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; align-items: center; scroll-behavior: smooth; }
        .msg-wrapper { width: 100%; max-width: 820px; display: flex; gap: 16px; margin-bottom: 24px; }
        .msg-wrapper.user { justify-content: flex-end; }
        .msg-avatar { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
        .msg-avatar.user { background: #4f46e5; color: white; }
        .msg-avatar.bot { background: #059669; color: white; }
        .msg-content { max-width: 85%; padding: 16px 20px; border-radius: 12px; font-size: 15px; line-height: 1.6; position: relative; }
        .msg-wrapper.user .msg-content { background: var(--bg-msg-user); color: var(--text-primary); border-top-right-radius: 4px; }
        .msg-wrapper.bot .msg-content { background: var(--bg-msg-bot); color: var(--text-primary); border: 1px solid var(--border); border-top-left-radius: 4px; }
        .msg-content h3 { margin-bottom: 8px; color: var(--accent); }
        .msg-content p { margin-bottom: 8px; }
        .msg-content ul { padding-left: 20px; margin-bottom: 8px; }
        .msg-footer { margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: var(--text-secondary); }
        .msg-rating { display: flex; gap: 8px; }
        .btn-rate { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 13px; transition: 0.2s; }
        .btn-rate:hover, .btn-rate.active { color: var(--accent); }
        
        /* Input area */
        .chat-input-wrapper { padding: 16px 24px 24px; display: flex; flex-direction: column; align-items: center; background: var(--bg-main); }
        .chips-container { max-width: 820px; width: 100%; display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 4px; }
        .chip { background: var(--bg-card); border: 1px solid var(--border); padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer; color: var(--text-secondary); white-space: nowrap; transition: 0.2s; }
        .chip:hover { border-color: var(--accent); color: var(--text-primary); }
        .input-box { max-width: 820px; width: 100%; background: var(--bg-card); border: 1px solid var(--border); border-radius: 24px; padding: 6px 14px; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .input-box:focus-within { border-color: var(--accent); }
        .input-box textarea { flex: 1; background: none; border: none; outline: none; color: var(--text-primary); font-size: 15px; resize: none; max-height: 120px; height: 26px; padding: 4px 0; }
        .btn-send { width: 38px; height: 38px; border-radius: 50%; background: var(--accent); color: white; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; flex-shrink: 0; }
        .btn-send:hover { background: var(--accent-hover); }
        
        /* Modal */
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 100; align-items: center; justify-content: center; }
        .modal.open { display: flex; }
        .modal-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; width: 380px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
        .form-group { margin-bottom: 14px; }
        .form-group label { display: block; font-size: 13px; margin-bottom: 6px; color: var(--text-secondary); }
        .form-group input { width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-main); color: var(--text-primary); font-size: 14px; outline: none; }
        .btn-submit { width: 100%; padding: 10px; background: var(--accent); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 10px; }
        .modal-tabs { display: flex; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
        .tab { flex: 1; text-align: center; padding: 8px; cursor: pointer; color: var(--text-secondary); font-size: 14px; }
        .tab.active { color: var(--accent); border-bottom: 2px solid var(--accent); font-weight: 600; }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-header">
            <h2><i class="fa-solid fa-scale-balanced" style="color:var(--accent);"></i> Trợ Lý Pháp Lý</h2>
        </div>
        <button class="btn-new-chat" onclick="startNewChat()">
            <i class="fa-solid fa-plus"></i> Cuộc trò chuyện mới
        </button>
        <div class="conv-list" id="convList"></div>
        <div class="sidebar-footer">
            <div class="user-info" id="userInfo">
                <div class="user-avatar" id="userAvatar"><i class="fa-solid fa-user"></i></div>
                <span id="userName">Khách</span>
            </div>
            <button class="btn-icon" id="btnAuth" onclick="openAuthModal()"><i class="fa-solid fa-right-to-bracket"></i></button>
        </div>
        <div class="sidebar-dev" id="devBox" style="padding: 12px 16px; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px;">
            <button id="devResetBtn" style="width: 100%; padding: 9px 12px; background: #c4483d; color: #ffffff; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s;" onmouseover="this.style.background='#b33a30'" onmouseout="this.style.background='#c4483d'" onclick="handleDevReset()">
                <i class="fa-solid fa-triangle-exclamation"></i> Reset dữ liệu (DEV)
            </button>
            <div id="devStats" style="font-size: 11px; color: var(--text-secondary); text-align: center; line-height: 1.4;"></div>
        </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
        <header class="chat-header">
            <div class="header-title">
                <span id="currentTitle" style="font-weight: 600;">Cuộc trò chuyện mới</span>
            </div>
            <div class="header-actions">
                <button class="btn-icon" onclick="toggleTheme()"><i class="fa-solid fa-moon" id="themeIcon"></i></button>
            </div>
        </header>

        <div class="chat-body" id="chatBody">
            <div class="msg-wrapper bot">
                <div class="msg-avatar bot"><i class="fa-solid fa-robot"></i></div>
                <div class="msg-content">
                    <p>Xin chào! Tôi là <strong>Trợ lý Thủ tục Hành chính công Việt Nam</strong>.</p>
                    <p>Tôi có thể giúp bạn tra cứu chính xác hồ sơ, giấy tờ cần chuẩn bị, thời gian giải quyết, mức lệ phí và nơi tiếp nhận các thủ tục hành chính.</p>
                </div>
            </div>
        </div>

        <div class="chat-input-wrapper">
            <div class="chips-container">
                <div class="chip" onclick="quickAsk('Làm giấy khai sinh cho con mới sinh cần giấy tờ gì?')">👶 Đăng ký khai sinh</div>
                <div class="chip" onclick="quickAsk('Cấp lại thẻ căn cước bị mất mất bao lâu?')">🆔 Cấp lại căn cước</div>
                <div class="chip" onclick="quickAsk('Thủ tục xác nhận tình trạng hôn nhân có mất phí không?')">💍 Xác nhận độc thân</div>
                <div class="chip" onclick="quickAsk('Đăng ký xe lần đầu nộp hồ sơ ở đâu?')">🏍️ Đăng ký xe máy</div>
            </div>
            <div class="input-box">
                <textarea id="queryInput" placeholder="Hỏi về thủ tục hành chính, hồ sơ, thời gian, lệ phí..." rows="1" onkeydown="handleKeyDown(event)"></textarea>
                <button class="btn-send" onclick="sendChat()"><i class="fa-solid fa-paper-plane"></i></button>
            </div>
        </div>
    </main>

    <!-- Auth Modal -->
    <div class="modal" id="authModal">
        <div class="modal-card">
            <div class="modal-header">
                <h3 id="modalTitle">Đăng nhập tài khoản</h3>
                <i class="fa-solid fa-xmark" style="cursor: pointer;" onclick="closeAuthModal()"></i>
            </div>
            <div class="modal-tabs">
                <div class="tab active" id="tabLogin" onclick="switchTab('login')">Đăng nhập</div>
                <div class="tab" id="tabRegister" onclick="switchTab('register')">Đăng ký</div>
            </div>
            <div class="form-group" id="groupFullName" style="display: none;">
                <label>Họ và tên</label>
                <input type="text" id="regFullName" placeholder="Nguyễn Văn A" onkeydown="if(event.key==='Enter') submitAuth()">
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="authEmail" placeholder="congdan@gmail.com" onkeydown="if(event.key==='Enter') submitAuth()">
            </div>
            <div class="form-group">
                <label>Mật khẩu</label>
                <div style="position: relative; display: flex; align-items: center;">
                    <input type="password" id="authPassword" placeholder="••••••••" style="width: 100%; padding-right: 36px;" onkeydown="if(event.key==='Enter') submitAuth()">
                    <i class="fa-regular fa-eye" id="togglePwd" style="position: absolute; right: 12px; cursor: pointer; color: var(--text-secondary);" onclick="togglePasswordVisibility()"></i>
                </div>
            </div>
            <div id="authError" style="display: none; color: #ef4444; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 6px; padding: 8px 12px; font-size: 13px; margin-bottom: 12px; text-align: center;"></div>
            <button class="btn-submit" id="btnSubmitAuth" onclick="submitAuth()">Đăng nhập</button>
        </div>
    </div>

    <script>
        let currentConvId = null;
        let currentUser = null;
        let authMode = "login";

        document.addEventListener("DOMContentLoaded", () => {
            checkAuth();
            loadConversations();
            loadDevStats();
        });

        async function loadDevStats() {
            const box = document.getElementById("devBox");
            if (!box) return;
            try {
                const res = await fetch("/api/dev/stats");
                if (!res.ok) {
                    box.style.display = "none";
                    return;
                }
                const s = await res.json();
                box.style.display = "flex";
                const statsEl = document.getElementById("devStats");
                if (statsEl) {
                    statsEl.textContent = `${s.users} tài khoản · ${s.conversations} hội thoại · ${s.messages} tin nhắn`;
                }
            } catch (e) {
                box.style.display = "none";
            }
        }

        async function handleDevReset() {
            const promptText = [
                "Phạm vi xoá:",
                "  1 = hội thoại của tôi",
                "  2 = TẤT CẢ hội thoại (mọi người dùng)",
                "  3 = TẤT CẢ, kể cả tài khoản",
                "",
                "Nhập 1, 2 hoặc 3:"
            ].join(String.fromCharCode(10));
            const scope = prompt(promptText, "1");
            if (!scope) return;
            const map = { "1": "my_conversations", "2": "all_conversations", "3": "everything" };
            if (!map[scope]) return alert("Lựa chọn không hợp lệ.");

            const confirmWord = prompt('Gõ đúng chữ  XOA  để xác nhận:');
            if (confirmWord !== "XOA") return alert("Đã huỷ.");

            try {
                const res = await fetch("/api/dev/reset", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ scope: map[scope], confirm: "XOA" })
                });
                const data = await res.json();
                if (!res.ok) {
                    alert("Lỗi: " + (data.detail || "Không thể thực hiện reset"));
                    return;
                }
                alert("Đã xoá. " + (data.note || ""));
                location.reload();
            } catch (err) {
                alert("Lỗi kết nối: " + err.message);
            }
        }

        function getAuthHeaders() {
            const token = localStorage.getItem("auth_token");
            return token ? { "Authorization": "Bearer " + token } : {};
        }

        function togglePasswordVisibility() {
            const pwd = document.getElementById("authPassword");
            const icon = document.getElementById("togglePwd");
            if (pwd.type === "password") {
                pwd.type = "text";
                icon.className = "fa-regular fa-eye-slash";
            } else {
                pwd.type = "password";
                icon.className = "fa-regular fa-eye";
            }
        }

        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute("data-theme");
            const next = current === "dark" ? "light" : "dark";
            html.setAttribute("data-theme", next);
            document.getElementById("themeIcon").className = next === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
        }

        async function checkAuth() {
            try {
                const res = await fetch("/api/auth/me", { headers: getAuthHeaders() });
                const data = await res.json();
                if (data.authenticated && data.user) {
                    currentUser = data.user;
                    document.getElementById("userName").textContent = currentUser.full_name;
                    document.getElementById("userAvatar").textContent = (currentUser.full_name || "U")[0].toUpperCase();
                    document.getElementById("btnAuth").innerHTML = '<i class="fa-solid fa-right-from-bracket"></i>';
                    document.getElementById("btnAuth").title = "Đăng xuất (" + currentUser.email + ")";
                    document.getElementById("btnAuth").onclick = logout;
                } else {
                    currentUser = null;
                    document.getElementById("userName").textContent = "Khách";
                    document.getElementById("userAvatar").innerHTML = '<i class="fa-solid fa-user"></i>';
                    document.getElementById("btnAuth").innerHTML = '<i class="fa-solid fa-right-to-bracket"></i>';
                    document.getElementById("btnAuth").title = "Đăng nhập / Đăng ký";
                    document.getElementById("btnAuth").onclick = openAuthModal;
                }
            } catch (e) {
                console.error(e);
            }
        }

        async function loadConversations() {
            try {
                const res = await fetch("/api/conversations", { headers: getAuthHeaders() });
                const list = await res.json();
                const container = document.getElementById("convList");
                container.innerHTML = "";
                list.forEach(c => {
                    const item = document.createElement("div");
                    item.className = `conv-item ${c.id === currentConvId ? 'active' : ''}`;
                    item.onclick = () => selectConversation(c.id, c.title);
                    item.innerHTML = `
                        <span class="conv-title"><i class="fa-regular fa-message"></i> ${c.title}</span>
                        <i class="fa-solid fa-trash conv-delete" onclick="deleteConv(event, '${c.id}')"></i>
                    `;
                    container.appendChild(item);
                });
                loadDevStats();
            } catch (e) {
                console.error(e);
            }
        }

        async function selectConversation(id, title) {
            currentConvId = id;
            document.getElementById("currentTitle").textContent = title;
            loadConversations();
            try {
                const res = await fetch(`/api/conversations/${id}/messages`, { headers: getAuthHeaders() });
                const messages = await res.json();
                const chatBody = document.getElementById("chatBody");
                chatBody.innerHTML = "";
                messages.forEach(m => appendMessage(m.role, m.content, m.tier, m.id));
                chatBody.scrollTop = chatBody.scrollHeight;
            } catch (e) {
                console.error(e);
            }
        }

        function startNewChat() {
            currentConvId = null;
            document.getElementById("currentTitle").textContent = "Cuộc trò chuyện mới";
            document.getElementById("chatBody").innerHTML = `
                <div class="msg-wrapper bot">
                    <div class="msg-avatar bot"><i class="fa-solid fa-robot"></i></div>
                    <div class="msg-content">
                        <p>Xin chào! Tôi có thể giúp gì cho bạn về thủ tục hành chính hôm nay?</p>
                    </div>
                </div>
            `;
            loadConversations();
        }

        async function deleteConv(e, id) {
            e.stopPropagation();
            if (!confirm("Bạn có chắc chắn muốn xóa cuộc trò chuyện này?")) return;
            await fetch(`/api/conversations/${id}`, { method: "DELETE", headers: getAuthHeaders() });
            if (currentConvId === id) startNewChat();
            loadConversations();
        }

        function getTierBadgeHtml(tier) {
            if (!tier) return "";
            const t = tier.toString().toUpperCase();
            if (t === "A" || t === "TIER_A") {
                return `<span class="badge-tier badge-tier-a">Tầng A — Dữ liệu chuẩn xác CSDL</span>`;
            } else if (t === "B" || t === "TIER_B") {
                return `<span class="badge-tier badge-tier-b">Tầng B — Cần làm rõ nhu cầu thủ tục</span>`;
            } else if (t === "TRAFFIC" || t === "NGOAI") {
                return `<span class="badge-tier badge-tier-traffic">Ngoài danh mục</span>`;
            } else if (t === "C" || t === "TIER_C") {
                return `<span class="badge-tier badge-tier-c">Tầng C — Tra cứu Cổng DVC (.gov.vn)</span>`;
            } else if (t === "SMALLTALK" || t === "XAGIAO") {
                return `<span class="badge-tier badge-tier-st">Xã giao thân mật</span>`;
            }
            return `<span class="badge-tier badge-tier-b">Tầng ${tier}</span>`;
        }

        function appendMessage(role, content, tier, msgId) {
            const chatBody = document.getElementById("chatBody");
            const wrapper = document.createElement("div");
            wrapper.className = `msg-wrapper ${role}`;

            const avatar = document.createElement("div");
            avatar.className = `msg-avatar ${role}`;
            avatar.innerHTML = role === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-scale-balanced"></i>';

            const contentDiv = document.createElement("div");
            contentDiv.className = "msg-content";
            contentDiv.innerHTML = marked.parse(content);

            if (role === "assistant" && msgId) {
                const footer = document.createElement("div");
                footer.className = "msg-footer";
                const tierHtml = getTierBadgeHtml(tier);
                footer.innerHTML = `
                    <div>${tierHtml}</div>
                    <div class="msg-rating">
                        <button class="btn-rate" onclick="rate('${msgId}', 1, this)"><i class="fa-regular fa-thumbs-up"></i></button>
                        <button class="btn-rate" onclick="rate('${msgId}', -1, this)"><i class="fa-regular fa-thumbs-down"></i></button>
                    </div>
                `;
                contentDiv.appendChild(footer);
            }

            if (role === "user") {
                wrapper.appendChild(contentDiv);
                wrapper.appendChild(avatar);
            } else {
                wrapper.appendChild(avatar);
                wrapper.appendChild(contentDiv);
            }

            chatBody.appendChild(wrapper);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        async function rate(msgId, score, btn) {
            try {
                await fetch(`/api/messages/${msgId}/feedback`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ rating: score })
                });
                const parent = btn.parentElement;
                parent.querySelectorAll(".btn-rate").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            } catch (e) {
                console.error(e);
            }
        }

        function handleKeyDown(e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendChat();
            }
        }

        function quickAsk(q) {
            document.getElementById("queryInput").value = q;
            sendChat();
        }

        async function sendChat() {
            const input = document.getElementById("queryInput");
            const query = input.value.trim();
            if (!query) return;

            appendMessage("user", query);
            input.value = "";
            input.style.height = "26px";

            // Hiển thị loading
            const chatBody = document.getElementById("chatBody");
            const loadingWrapper = document.createElement("div");
            loadingWrapper.className = "msg-wrapper bot";
            loadingWrapper.id = "loadingMsg";
            loadingWrapper.innerHTML = `
                <div class="msg-avatar bot"><i class="fa-solid fa-robot"></i></div>
                <div class="msg-content"><i class="fa-solid fa-spinner fa-spin"></i> Đang tra cứu thông tin...</div>
            `;
            chatBody.appendChild(loadingWrapper);
            chatBody.scrollTop = chatBody.scrollHeight;

            try {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
                    body: JSON.stringify({ query: query, conversation_id: currentConvId })
                });
                const data = await res.json();
                document.getElementById("loadingMsg")?.remove();

                currentConvId = data.conversation_id;
                appendMessage("assistant", data.answer, data.tier, data.message_id);

                loadConversations();
            } catch (err) {
                document.getElementById("loadingMsg")?.remove();
                appendMessage("assistant", "Đã xảy ra lỗi khi tra cứu. Vui lòng thử lại!");
            }
        }

        function openAuthModal() {
            document.getElementById("authModal").classList.add("open");
            const errEl = document.getElementById("authError");
            if (errEl) errEl.style.display = "none";
        }
        function closeAuthModal() {
            document.getElementById("authModal").classList.remove("open");
            const errEl = document.getElementById("authError");
            if (errEl) errEl.style.display = "none";
        }
        function switchTab(mode) {
            authMode = mode;
            document.getElementById("tabLogin").className = `tab ${mode === 'login' ? 'active' : ''}`;
            document.getElementById("tabRegister").className = `tab ${mode === 'register' ? 'active' : ''}`;
            document.getElementById("groupFullName").style.display = mode === 'register' ? 'block' : 'none';
            document.getElementById("modalTitle").textContent = mode === 'login' ? 'Đăng nhập tài khoản' : 'Đăng ký tài khoản';
            document.getElementById("btnSubmitAuth").textContent = mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản';
            const errEl = document.getElementById("authError");
            if (errEl) errEl.style.display = "none";
        }

        async function submitAuth() {
            const email = document.getElementById("authEmail").value.trim();
            const password = document.getElementById("authPassword").value;
            const fullName = document.getElementById("regFullName").value.trim();
            const errEl = document.getElementById("authError");
            if (errEl) errEl.style.display = "none";

            if (!email || !password) {
                if (errEl) {
                    errEl.textContent = "Vui lòng điền đủ email và mật khẩu!";
                    errEl.style.display = "block";
                } else {
                    alert("Vui lòng điền đủ email và mật khẩu!");
                }
                return;
            }

            const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
            const payload = authMode === "login" ? { email, password } : { email, password, full_name: fullName };

            const btn = document.getElementById("btnSubmitAuth");
            btn.disabled = true;
            btn.textContent = "Đang xử lý...";

            try {
                const res = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || data.error || "Email hoặc mật khẩu không chính xác.");
                }
                if (data.token) {
                    localStorage.setItem("auth_token", data.token);
                }
                closeAuthModal();
                checkAuth();
                loadConversations();
            } catch (e) {
                if (errEl) {
                    errEl.textContent = e.message;
                    errEl.style.display = "block";
                } else {
                    alert(e.message);
                }
            } finally {
                btn.disabled = false;
                btn.textContent = authMode === "login" ? "Đăng nhập" : "Tạo tài khoản";
            }
        }

        async function logout() {
            const token = localStorage.getItem("auth_token");
            localStorage.removeItem("auth_token");
            try {
                await fetch("/api/auth/logout", {
                    method: "POST",
                    headers: token ? { "Authorization": "Bearer " + token } : {}
                });
            } catch (_) {}
            currentUser = null;
            checkAuth();
            startNewChat();
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def get_home_ui():
    return HTML_UI


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)

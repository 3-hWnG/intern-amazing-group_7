import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Backend/ cho các gói (api, core, db...) và GỐC dự án cho config.py.
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent
for _p in (str(_BACKEND_DIR), str(_PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import asyncio
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import (ATTACHMENTS_ENABLED, DB_PATH, DEV_TOOLS_ENABLED, HOST, LLM_MODEL,
                    OLLAMA_HOST, PORT, QUEUE_ENABLED, RETENTION_DAYS, SEARCH_PROVIDER,
                    STATIC_DIR, VERIFIER_ENABLED, VERIFIER_MODEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core import llm, mcp_client, queue
    from db import connection
    from db.repositories import AuthSessions, purge_old

    print("Đang khởi động...")
    try:
        connection.init_db()
        print(f"  - CSDL: sẵn sàng ({DB_PATH})")
        AuthSessions.purge_expired()
        removed = purge_old(RETENTION_DAYS)
        if removed:
            print(f"  - đã xoá {removed} hội thoại quá hạn lưu trữ")

        # Ollama / MCP hỏng thì VẪN chạy: người dùng thấy thông báo lỗi rõ ràng
        # trong khung chat, thay vì server không lên.
        st = await asyncio.to_thread(llm.status)
        if not st["reachable"]:
            print(f"  ! Ollama không phản hồi tại {OLLAMA_HOST} — hãy mở Ollama")
        elif st["missing"]:
            print(f"  ! Chưa có mô hình: {', '.join(st['missing'])} "
                  f"-> chạy: ollama pull {st['missing'][0]}")
        else:
            print(f"  - LLM: {LLM_MODEL}"
                  + (f" · kiểm chứng: {VERIFIER_MODEL}" if VERIFIER_ENABLED else " · kiểm chứng: TẮT"))
            asyncio.get_running_loop().run_in_executor(None, llm.warm_up)

        mcp = await asyncio.to_thread(mcp_client.connect, 40)
        if mcp["transport"] == "direct":
            print("  - MCP: TẮT (MCP_TRANSPORT=direct, gọi thẳng engine)")
        elif mcp["connected"]:
            print(f"  - MCP: {mcp['transport']} · công cụ: {', '.join(mcp['tools'])}"
                  f" · tìm kiếm: {SEARCH_PROVIDER}")
        else:
            print(f"  ! MCP chưa kết nối ({mcp['last_error'] or 'không rõ lỗi'}) — sẽ thử lại khi có câu hỏi")

        if QUEUE_ENABLED:
            await queue.manager.start()
            print(f"  - hàng đợi: {queue.manager.concurrency} worker")

        if DEV_TOOLS_ENABLED:
            print("  ! DEV_TOOLS_ENABLED = True — có endpoint xoá dữ liệu. Đặt False khi bàn giao.")
        print(f"Sẵn sàng: http://{HOST}:{PORT}")
    except Exception as exc:
        print("LỖI KHỞI TẠO:", exc)
        traceback.print_exc()
        raise
    yield
    if QUEUE_ENABLED:
        await queue.manager.stop()
    await asyncio.to_thread(mcp_client.shutdown)


def create_app() -> FastAPI:
    app = FastAPI(title="Trợ lý Thủ tục hành chính", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    from api import auth_routes, chat_routes, file_routes, procedure_routes, routes
    app.include_router(routes.router)
    app.include_router(auth_routes.router)
    app.include_router(chat_routes.router)
    # Hệ thống 2: tải biểu mẫu thủ tục + trí nhớ lựa chọn MCQ.
    app.include_router(procedure_routes.router)
    if ATTACHMENTS_ENABLED:
        app.include_router(file_routes.router)

    if DEV_TOOLS_ENABLED:
        from api import dev_routes
        app.include_router(dev_routes.router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

"""Điểm khởi chạy: ráp FastAPI, nạp model, khởi động hàng đợi và CSDL."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import (DEV_TOOLS_ENABLED, HOST, PORT, QUEUE_ENABLED,
                    RETENTION_DAYS, STATIC_DIR, USE_LEXICAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core import queue, vectorstore
    from db import connection
    from db.repositories import AuthSessions, purge_old
    from domain.records import get_procedures

    print("Đang khởi động...")
    try:
        connection.init_db()
        print("  - CSDL: sẵn sàng")
        AuthSessions.purge_expired()
        removed = purge_old(RETENTION_DAYS)
        if removed:
            print(f"  - đã xoá {removed} hội thoại quá hạn lưu trữ")

        print(f"  - {len(get_procedures())} thủ tục")
        print(f"  - vector store: {vectorstore.get_collection().count()} view")
        if USE_LEXICAL:
            from core import lexical
            lexical.get_index()
            print("  - BM25: sẵn sàng")

        # Nạp sẵn hai mô hình: nếu để nạp lười thì câu hỏi ĐẦU TIÊN của người
        # dùng phải chờ tải 2.2GB reranker — nhìn như hệ thống bị treo.
        from config import USE_RERANKER
        from core import embeddings
        embeddings.encode("khởi động")
        print(f"  - mô hình nhúng: sẵn sàng ({embeddings.get_device()})")
        if USE_RERANKER:
            from core import reranker
            if reranker.is_available():
                reranker.score("khởi động", ["khởi động"])
                print(f"  - reranker: sẵn sàng ({reranker.get_device()})")

        if QUEUE_ENABLED:
            await queue.manager.start()
            print(f"  - hàng đợi: {queue.manager.concurrency} worker")

        if DEV_TOOLS_ENABLED:
            print("  " + "!" * 60)
            print("  ! DEV_TOOLS_ENABLED = True — có endpoint xoá dữ liệu.")
            print("  ! ĐẶT False trong config.py trước khi bàn giao bản cuối.")
            print("  " + "!" * 60)
        print("Sẵn sàng.")
    except Exception as exc:
        print("LỖI KHỞI TẠO:", exc)
        traceback.print_exc()
        raise
    yield
    if QUEUE_ENABLED:
        await queue.manager.stop()


def create_app() -> FastAPI:
    """Tách ra để test tự động dựng được app mà không cần chạy server."""
    app = FastAPI(title="Trợ Lý Thủ Tục Hành Chính - Nhóm 7", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    from api import auth_routes, chat_routes, routes
    app.include_router(routes.router)
    app.include_router(auth_routes.router)
    app.include_router(chat_routes.router)

    if DEV_TOOLS_ENABLED:
        from api import dev_routes
        app.include_router(dev_routes.router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

"""Kiểm tra môi trường trước khi chạy. Báo rõ cái gì hỏng, không đoán."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

OK, WARN, BAD = "[ OK ]", "[WARN]", "[FAIL]"
problems = []

# Khi sắp chạy ingest thì lệch chiều vector là chuyện BÌNH THƯỜNG - chính lệnh
# ingest sẽ sửa nó. Không được chặn, nếu không sẽ khoá luôn cách khắc phục.
INGESTING = "--ingesting" in sys.argv


def line(tag, msg):
    print(f"  {tag} {msg}")


print("\n=== KIỂM TRA MÔI TRƯỜNG ===")

# --- thư viện --------------------------------------------------------------
import importlib.util
for mod, pkg in [("rank_bm25", "rank_bm25"), ("sentencepiece", "sentencepiece"),
                 ("google.protobuf", "protobuf"), ("sentence_transformers", "sentence-transformers"),
                 ("chromadb", "chromadb"), ("pandas", "pandas"), ("ollama", "ollama")]:
    if importlib.util.find_spec(mod) is None:
        line(BAD, f"thiếu thư viện {pkg}  ->  pip install {pkg}")
        problems.append(pkg)
    else:
        line(OK, mod)

try:
    import torch, transformers
    line(OK, f"torch {torch.__version__} | cuda={torch.cuda.is_available()} | "
             f"transformers {transformers.__version__}")
except Exception as e:
    line(BAD, f"torch/transformers: {e}")

# --- dữ liệu ---------------------------------------------------------------
import config
from domain.records import load_procedures

if not config.DATASET_PATH.exists():
    line(BAD, f"không thấy dataset: {config.DATASET_PATH}")
    problems.append("dataset")
else:
    procs = load_procedures()
    line(OK, f"dataset: {len(procs)} thủ tục ({config.DATASET_PATH.name})")

# --- mô hình nhúng ---------------------------------------------------------
print(f"\n  Mô hình nhúng: {config.EMBED_MODEL_NAME}")
try:
    from core import embeddings
    v = embeddings.encode("thủ tục đăng ký khai sinh")
    line(OK, f"nhúng chạy được, {len(v)} chiều, thiết bị={embeddings.get_device()}")
except Exception as e:
    line(BAD, f"KHÔNG nạp được: {type(e).__name__}: {e}")
    problems.append("embed")

# --- vector store ----------------------------------------------------------
try:
    from core import vectorstore
    collection = vectorstore.get_collection()
    n = collection.count()
    if n == 0:
        line(WARN, "vector DB rỗng -> chạy lại với  -Ingest")
    else:
        line(OK, f"vector DB: {n} view")
        # Chiều vector trong DB PHẢI khớp mô hình nhúng hiện tại.
        # Đổi EMBED_MODEL_NAME mà quên -Ingest là lỗi rất dễ mắc: hệ thống
        # khởi động bình thường rồi mới vỡ ở câu hỏi đầu tiên.
        try:
            got = collection.get(limit=1, include=["embeddings"])
            stored = got.get("embeddings")
            db_dim = len(stored[0]) if stored is not None and len(stored) else None
        except Exception:
            db_dim = None
        model_dim = len(v) if "v" in dir() else None
        if db_dim and model_dim and db_dim != model_dim:
            if INGESTING:
                line(WARN, f"lệch chiều vector ({db_dim} -> {model_dim}) — "
                           f"ingest ngay sau đây sẽ dựng lại, không sao.")
            else:
                line(BAD, f"LỆCH CHIỀU VECTOR: vector DB lưu {db_dim} chiều nhưng "
                          f"mô hình nhúng sinh {model_dim} chiều.")
                line("     ", "Nguyên nhân: đã đổi EMBED_MODEL_NAME mà chưa nạp lại.")
                line("     ", "Khắc phục:  .\\run.ps1 -Ingest")
                problems.append("vector-dim")
        elif db_dim:
            line(OK, f"chiều vector khớp mô hình ({db_dim})")
except Exception as e:
    line(BAD, f"vector DB: {e}")

# --- BM25 ------------------------------------------------------------------
if config.USE_LEXICAL:
    try:
        from core import lexical
        line(OK, f"BM25: {len(lexical.get_index()['row_ids'])} thủ tục")
    except Exception as e:
        line(WARN, f"BM25 chưa dựng ({e}) -> chạy lại với  -Ingest")

# --- reranker --------------------------------------------------------------
if config.USE_RERANKER:
    print(f"\n  Reranker: {config.RERANKER_MODEL_NAME}")
    try:
        from core import reranker
        s = reranker.score("đăng ký khai sinh cần giấy tờ gì",
                           ["Thủ tục đăng ký khai sinh", "Thủ tục đăng ký khai tử"])
        if s and s[0] > s[1]:
            line(OK, f"reranker chạy đúng trên {reranker.get_device()} (điểm {s[0]:.3f} > {s[1]:.3f})")
        else:
            line(WARN, f"reranker chạy nhưng xếp hạng đáng ngờ: {s}")
    except Exception as e:
        line(WARN, f"reranker KHÔNG dùng được -> hệ thống vẫn chạy, chỉ bỏ bước xếp hạng lại")
        line("     ", f"lý do: {type(e).__name__}: {str(e)[:160]}")
else:
    line(WARN, "reranker đang TẮT (USE_RERANKER = False)")

# --- CSDL + hàng đợi -------------------------------------------------------
print()
try:
    from db import connection
    from db.repositories import Conversations, Messages, Users
    connection.init_db()
    line(OK, f"CSDL: {config.DB_PATH.name} — {Users.count()} tài khoản, "
             f"{Conversations.count()} hội thoại, {Messages.count()} tin nhắn")
except Exception as e:
    line(BAD, f"CSDL: {type(e).__name__}: {e}")
    problems.append("db")

line(OK if config.AUTH_ENABLED else WARN,
     f"xác thực: {'BẬT' if config.AUTH_ENABLED else 'TẮT'}")
line(OK if config.QUEUE_ENABLED else WARN,
     f"hàng đợi: {'BẬT' if config.QUEUE_ENABLED else 'TẮT'}, "
     f"concurrency={config.QUEUE_CONCURRENCY}")
line(OK if config.SUMMARY_ENABLED else WARN,
     f"tóm tắt ngữ cảnh: ngưỡng {config.CONTEXT_TOKEN_BUDGET} token")
if config.DEV_TOOLS_ENABLED:
    line(WARN, "DEV_TOOLS_ENABLED = True — có endpoint xoá dữ liệu. Đặt False ở bản cuối.")

print()
if problems:
    print(f"  => CÓ LỖI CHẶN: {', '.join(problems)}\n")
    sys.exit(1)
print("  => Sẵn sàng chạy.\n")

"""config.py — Cấu hình tập trung toàn bộ hệ thống Trợ lý Pháp lý."""

from pathlib import Path
import torch

# --- Thư mục & Đường dẫn ---
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = ROOT_DIR / "data"

DATA_MERGED_PATH = DATA_DIR / "data_merged.xlsx"
DATASET_PATH = DATA_DIR / "dataset.xlsx"
CHROMA_PATH = DATA_DIR / "chromadb"
CHROMA_COLLECTION = "legal_docs"
CHROMA_SPACE = "cosine"
SQLITE_DB_PATH = DATA_DIR / "app.db"
INDEX_META_PATH = DATA_DIR / "index_meta.json"

# --- Mô hình ---
EMBED_MODEL_NAME = "keepitreal/vietnamese-sbert"
RERANKER_MODEL_NAME = "AITeamVN/Vietnamese_Reranker"
LLM_MODEL_NAME = "3b-finetune"
LLM_OPTIONS = {"repeat_penalty": 1.15, "temperature": 0.2, "num_predict": 512}

# --- Thiết bị phần cứng ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
RERANKER_DEVICE = DEVICE

# --- Cấu hình Hybrid Retrieval (RRF) ---
# --- Cấu hình Hybrid Retrieval (RRF & Reranker) ---
USE_DENSE = True
USE_LEXICAL = True
USE_RERANKER = True             # Bật Reranker với các tối ưu siêu tốc trên CPU
USE_MULTI_VIEW = True           # Sử dụng đa góc nhìn ChromaDB
RERANKER_MAX_LENGTH = 128       # Cắt giảm độ dài giúp CPU tính toán nhanh hơn 4 lần
DENSE_TOP_K = 20
LEXICAL_TOP_K = 20
FUSION_TOP_K = 3                # Chỉ rerank Top 3 ứng viên -> Giảm 70% thời gian trên CPU
FINAL_TOP_K = 3
RRF_K = 60

# Trọng số hòa trộn RRF
RRF_WEIGHT_DENSE = 1.0
RRF_WEIGHT_LEXICAL = 1.0
RRF_WEIGHT_DENSE_NO_DIACRITICS = 0.25
RERANK_SKIP_NO_DIACRITICS = True

# --- Phân loại Ý định (Intent Classification) ---
LUAT_ANCHORS = [
    "đăng ký kết hôn", "thủ tục ly hôn", "làm giấy khai sinh", "đăng ký khai tử",
    "xác nhận độc thân", "lấy vợ", "lấy chồng", "sinh con", "làm cccd", "đổi căn cước",
    "tạm trú", "thường trú", "sổ đỏ", "sổ hồng", "giấy phép xây dựng", "hộ kinh doanh",
    "chứng thực", "công chứng", "thủ tục hành chính", "hồ sơ cần giấy tờ gì",
    "lệ phí bao nhiêu", "nơi nộp hồ sơ", "thời gian giải quyết", "uỷ ban nhân dân"
]

NGOAI_ANCHORS = [
    "vượt đèn đỏ phạt bao nhiêu tiền", "lỗi không đội mũ bảo hiểm", "mũ bảo hiểm",
    "chạy xe không mũ bảo hiểm", "uống rượu lái xe phạt bao nhiêu", "nồng độ cồn xe máy",
    "bị bắn tốc độ", "bảo hiểm xe máy", "giấy phép lái xe", "bằng lái xe", "vi phạm giao thông",
    "giá vàng hôm nay", "thời tiết hôm nay", "chứng khoán", "tin tức thời sự", "bão lũ"
]

XAGIAO_ANCHORS = [
    "xin chào", "chào bạn", "hello", "hi", "alo", "chào bot", "bạn là ai", "bạn tên gì",
    "cảm ơn", "cảm ơn bạn", "tạm biệt", "bye", "chúc bạn một ngày tốt lành"
]

# --- Ngưỡng phân tầng Tier ---
TIER_A_MIN_CONFIDENCE = 0.40   # Khớp cao: Trực tiếp trả lời thủ tục
TIER_B_MIN_CONFIDENCE = 0.28   # 0.28 - 0.40: Gợi ý các thủ tục gần nhất để chọn
TIER_GAP_THRESHOLD = 0.05      # Độ chênh lệch giữa top 1 và top 2 để coi là phân vân

# --- Hàng đợi & Session ---
QUEUE_CONCURRENCY = 1
CONTEXT_TOKEN_THRESHOLD = 1800
SESSION_EXPIRE_DAYS = 30
RETENTION_DAYS = 30
DEV_TOOLS_ENABLED = True
HOST = "0.0.0.0"
PORT = 8000


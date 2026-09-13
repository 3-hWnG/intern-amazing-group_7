"""Toàn bộ cấu hình hệ thống. Sửa ở đây, không rải rác trong code.

Mỗi cờ (flag) bật/tắt được một tầng để đo A/B bằng bộ eval.
"""

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
DATASET_PATH = DATA_DIR / "data_merged.xlsx"
CHROMA_PATH = DATA_DIR / "chromadb_eval"
COLLECTION_NAME = "thu_tuc_views"
BM25_INDEX_PATH = DATA_DIR / "bm25_index.pkl"
RUNTIME_DIR = APP_DIR / "runtime"          # session + feedback, không commit

STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"

# --------------------------------------------------------------------------
# Cột trong dataset. Thêm cột mới -> khai báo ở đây, sửa domain/records.py.
# --------------------------------------------------------------------------
DATASET_COLUMNS = {
    "title": "Tên thủ tục hành chính",
    "linh_vuc": "Lĩnh vực",
    "hinh_thuc_nop": "Hình thức nộp",
    "requirements": "Thành phần hồ sơ",
    "duration": "Thời gian giải quyết",
    "fee": "Lệ phí",
    "location": "Địa điểm tiếp nhận hồ sơ trực tiếp (nếu có)",
    # Chưa có trong file hiện tại - thêm được ngay khi teammate bổ sung:
    "ma_thu_tuc": "Mã thủ tục",
    "can_cu_phap_ly": "Căn cứ pháp lý",
    "nguon_url": "Nguồn",
}

# --------------------------------------------------------------------------
# Mô hình
# --------------------------------------------------------------------------
# Đã THỬ và HOÀN NGUYÊN: AITeamVN/Vietnamese_Embedding (nền bge-m3, 1024 chiều)
# cho R@1 0.8494 so với 0.8556 của sbert — không cải thiện, lại tốn thêm ~1.7GB
# VRAM. Lý do: BM25 bỏ dấu đã gánh phần khớp từ khoá. Chi tiết:
# Evaluation/baselines/2026-09-13_v5_bge-m3-REVERTED/
# Đổi dòng dưới rồi chạy `.\run.ps1 -Ingest` nếu muốn thử lại.
EMBED_MODEL_NAME = "keepitreal/vietnamese-sbert"
# EMBED_MODEL_NAME = "AITeamVN/Vietnamese_Embedding"
EMBED_DEVICE = "auto"          # "auto" | "cpu" | "cuda"
EMBED_NORMALIZE = True         # bắt buộc khi dùng không gian cosine

RERANKER_MODEL_NAME = "AITeamVN/Vietnamese_Reranker"
RERANKER_DEVICE = "auto"       # "auto" | "cpu" | "cuda"
# Lúc CHẤM ĐIỂM không có LLM chạy nên GPU rảnh -> "auto" nhanh hơn CPU nhiều lần.
# Lúc PHỤC VỤ thật, nếu VRAM căng thì đặt lại "cpu" (70 thủ tục, 1 truy vấn/lần
# nên CPU vẫn kịp trong ngân sách 15 giây).
RERANKER_MAX_LENGTH = 384
RERANKER_BATCH_SIZE = 16

LLM_MODEL_NAME = "qwen2.5:1.5b"
LLM_OPTIONS = {"repeat_penalty": 1.15, "temperature": 0.2, "num_predict": 400}

# --------------------------------------------------------------------------
# Cờ bật/tắt từng tầng - dùng để đo đóng góp của từng thay đổi
# --------------------------------------------------------------------------
USE_DENSE = True
USE_LEXICAL = True             # BM25 bỏ dấu - sửa lỗi gõ không dấu
USE_RERANKER = True            # đã tải xong model
# Vietnamese_Reranker (nền bge-m3) huấn luyện trên tiếng Việt CÓ dấu. Với truy
# vấn gõ không dấu nó xếp lại sai và đẩy kết quả đúng của BM25 xuống:
# đo được ở v3, no_diacritics tụt 0.611 -> 0.315. Nên bỏ qua rerank ở trường hợp đó.
RERANK_SKIP_NO_DIACRITICS = True
# Điểm reranker phân bố hai cực (gần 0 hoặc gần 1) nên KHÔNG dùng làm độ tin cậy.
# Dùng nó để xếp thứ tự, còn độ tin cậy lấy từ điểm hoà dense+BM25 (đã hiệu chỉnh).
CONFIDENCE_FROM_RERANKER = False
USE_MULTI_VIEW = True          # mỗi thủ tục có nhiều "góc nhìn" vector

CHROMA_SPACE = "cosine"        # "cosine" | "l2"  (baseline v0 dùng l2)

DENSE_TOP_K = 20               # số VIEW lấy về trước khi gộp theo thủ tục
LEXICAL_TOP_K = 20
FUSION_TOP_K = 10              # số ứng viên sau khi hoà (đưa vào reranker)
FINAL_TOP_K = 5                # số ứng viên đưa vào prompt
RRF_K = 60                     # hằng số Reciprocal Rank Fusion

# Trọng số khi hoà hai nguồn xếp hạng. v1 cộng ngang hàng -> tín hiệu dense
# (mù với chữ không dấu) kéo tụt slice no_diacritics từ 0.574 xuống 0.407.
RRF_WEIGHT_DENSE = 1.0
RRF_WEIGHT_LEXICAL = 1.0
# Câu hỏi gõ KHÔNG DẤU: hạ trọng số dense xuống, tin BM25 nhiều hơn.
RRF_WEIGHT_DENSE_NO_DIACRITICS = 0.25

# --------------------------------------------------------------------------
# Ngưỡng phân tầng câu trả lời (A/B/C/D)
# CẢNH BÁO: ngưỡng phụ thuộc mô hình nhúng VÀ metric.
# Baseline v0 (L2 + vietnamese-sbert) dùng LOW=70 - KHÔNG áp dụng được ở đây.
# Chạy `python evaluate_retrieval.py --calibrate` để lấy số mới.
# --------------------------------------------------------------------------
# Hiệu chỉnh lại trên thang confidence của v2 (RRF có trọng số).
# A=0.75 B=0.65 -> tầng A phủ 74% câu in-scope, chỉ 4% câu ngoài phạm vi lọt vào
# tầng A, 83% câu ngoài phạm vi được đẩy sang web search, mất 2.9% câu đúng.
# LƯU Ý: đổi công thức confidence => PHẢI hiệu chỉnh lại hai số này.
TIER_A_MIN_CONFIDENCE = 0.75   # >= : trả lời thẳng từ DB, không qua LLM
TIER_B_MIN_CONFIDENCE = 0.65   # >= : hỏi lại cho rõ
                               # <  : ra web search, rồi kiến thức chung
AMBIGUITY_GAP = 0.02           # top1 - top2 nhỏ hơn mức này -> hỏi lại

# ...NHƯNG chỉ hỏi lại khi top1/top2 là HAI THỦ TỤC KHÁC NHAU THẬT.
# Ở v1, 26% câu in-scope bị đẩy sang "hỏi lại" chỉ vì hai ứng viên đầu là bản
# trùng hoặc cùng thủ tục khác cấp - 66% số đó đã lấy đúng dòng rồi.
DUPLICATE_TITLE_JACCARD = 0.75   # >= : coi là cùng một thủ tục, không hỏi lại

# --------------------------------------------------------------------------
# Tìm kiếm ngoài - chỉ nguồn chính thống
# --------------------------------------------------------------------------
WEB_SEARCH_ENABLED = True
WEB_SEARCH_MAX_RESULTS = 4
WEB_SEARCH_ALLOWLIST = [
    "dichvucong.gov.vn",
    "csdl.dichvucong.gov.vn",
    "dichvucong.bocongan.gov.vn",
    "vbpl.vn",
    "chinhphu.vn",
    "moj.gov.vn",
    "hochiminhcity.gov.vn",
]
WEB_SEARCH_STRICT = True       # True: chặn mọi domain ngoài allowlist
WEB_SEARCH_TIMEOUT = 8         # giây — treo lâu hơn thì bỏ, đừng bắt người dùng chờ
# Chỉ đưa vài domain vào chuỗi truy vấn: ghép cả 7 site: bằng OR làm câu quá dài,
# DuckDuckGo hay trả rỗng. Việc lọc đầy đủ vẫn do WEB_SEARCH_ALLOWLIST đảm nhiệm.
WEB_SEARCH_QUERY_SITES = 3

# --------------------------------------------------------------------------
# Kiểm chứng bằng luật (core/factcheck.py)
# --------------------------------------------------------------------------
FACTCHECK_ENABLED = True
FACTCHECK_MAX_RETRIES = 1      # sinh lại 1 lần, sai tiếp thì trả nguyên bản ghi

# --------------------------------------------------------------------------
# Bộ nhớ hội thoại
# --------------------------------------------------------------------------
SESSION_ENABLED = True
SESSION_MAX_TURNS = 6          # số lượt gần nhất đưa vào prompt
SESSION_TTL_SECONDS = 60 * 60
PENDING_QUESTION_TTL = 180     # câu hỏi lại (Tier B) còn hiệu lực bao lâu

FEEDBACK_ENABLED = True
FEEDBACK_PATH = RUNTIME_DIR / "feedback.jsonl"

AI_DISCLOSURE = "Trợ lý ảo (AI) - thông tin tham khảo, không thay thế cán bộ một cửa."

# ==========================================================================
# CƠ SỞ DỮ LIỆU
# ==========================================================================
DB_PATH = RUNTIME_DIR / "app.db"
RETENTION_DAYS = 90            # 0 = giữ vĩnh viễn

# ==========================================================================
# XÁC THỰC
# ==========================================================================
AUTH_ENABLED = True
AUTH_SESSION_DAYS = 14
AUTH_COOKIE_NAME = "tthc_session"
AUTH_COOKIE_SECURE = False     # True khi chạy sau HTTPS
AUTH_MIN_PASSWORD_LENGTH = 8
AUTH_MAX_LOGIN_ATTEMPTS = 5
AUTH_LOCKOUT_SECONDS = 900

# ==========================================================================
# HÀNG ĐỢI
# ==========================================================================
QUEUE_ENABLED = True
QUEUE_CONCURRENCY = 1          # mentor yêu cầu xử lý tuần tự 1-1.
                               # Đổi 2-4 nếu chấp nhận xử lý song song.
QUEUE_MAX_DEPTH = 20
QUEUE_JOB_TIMEOUT = 120

# ==========================================================================
# NGỮ CẢNH & TÓM TẮT
# ==========================================================================
SUMMARY_ENABLED = True
CONTEXT_TOKEN_BUDGET = 1800
SUMMARY_KEEP_RECENT = 4
TOKENS_PER_SYLLABLE = 1.4      # ước lượng thô, giống build_eval_set.py

# ==========================================================================
# CÔNG CỤ PHÁT TRIỂN — ĐẶT False Ở BẢN CUỐI
# ==========================================================================
DEV_TOOLS_ENABLED = True

HOST = "127.0.0.1"
PORT = 8000

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


# ==========================================================================
# ORCHESTRATOR — v6 "agent"
# ==========================================================================
# "agent"  : LLM chọn công cụ (search_procedures / get_procedure /
#            search_attachments / search_web / không dùng gì). Dataset là TÀI
#            NGUYÊN, không phải nhà tù. Đây là mặc định.
# "tiers"  : luồng cũ core/pipeline.py (router cứng A/B/C/D). Giữ lại để so
#            sánh A/B, KHÔNG xoá.
ORCHESTRATOR = "agent"

# Số vòng gọi công cụ tối đa trong một lượt. 2 là đủ cho "tra bảng rồi tra web".
AGENT_MAX_STEPS = 2

# "json"   : một lần gọi LLM bị ép trả JSON (đáng tin với mô hình 1.5B).
# "native" : dùng tool-calling gốc của Ollama. Bật khi cắm mô hình 3B/7B.
AGENT_TOOL_MODE = "json"

# Bước CHỌN công cụ phải lạnh và ngắn — nó không viết văn, chỉ ra quyết định.
AGENT_DECISION_OPTIONS = {"temperature": 0.0, "num_predict": 160}

# ---- GUARDRAIL DUY NHẤT --------------------------------------------------
# Mô hình 1.5B đôi khi trả lời chay về một thủ tục hành chính mà không thèm tra
# bảng -> khẳng định pháp lý không nguồn. Cờ này ép đúng MỘT lần tra cứu trong
# trường hợp đó, rồi để mô hình tự viết.
#
# ĐẶT False KHI CẮM MÔ HÌNH LỚN (3B/7B quantized). Mô hình lớn tự biết khi nào
# cần tra; ép thêm chỉ làm nó ngu đi. Đây là cái duy nhất cần tắt.
AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL = True

# Ghi lại chuỗi công cụ đã gọi vào header X-Tools (soi lỗi ở tab Network).
AGENT_SHOW_TOOL_TRACE = True

# --------------------------------------------------------------------------
# Văn phong câu trả lời khi CÓ bản ghi trong tay
# --------------------------------------------------------------------------
# "llm"      : mô hình tự viết từ bản ghi, sau đó kiểm chứng bằng luật
#              (core/factcheck.py). MẶC ĐỊNH — dataset viết xấu, in thẳng ra
#              đọc như một cái bảng Excel.
# "template" : in nguyên bản ghi, không qua LLM. An toàn tuyệt đối, xấu.
ANSWER_STYLE = "llm"

# Khi câu hỏi nhắm vào MỘT con số cụ thể (lệ phí, thời gian, hồ sơ, nơi nộp),
# prompt ép mô hình trích ĐÚNG NGUYÊN VĂN trường đó, không diễn đạt lại.
# Đây là chỗ duy nhất cần "exactly".
EXACT_ON_FACET = True

# Câu trả lời có kiểm chứng phải sinh xong mới kiểm tra được -> phát lại theo
# từng mẩu để giao diện vẫn có hiệu ứng gõ chữ.
REPLAY_CHUNK_CHARS = 18

# ==========================================================================
# TÀI LIỆU (tri thức chung + tệp đính kèm theo hội thoại)
# ==========================================================================
ATTACHMENTS_ENABLED = True
UPLOAD_DIR = RUNTIME_DIR / "uploads"
ATTACH_MAX_BYTES = 20 * 1024 * 1024          # 20 MB
ATTACH_MAX_PER_CONVERSATION = 10
ATTACH_CHUNK_CHARS = 900
ATTACH_CHUNK_OVERLAP = 120
ATTACH_TOP_K = 5
ATTACH_COLLECTION = "doc_chunks"             # collection riêng, KHÔNG đụng KB
ATTACH_FUSION_TOP_K = 12

# Luôn parse được (thư viện chuẩn / đã có sẵn)
ATTACH_EXT_ALWAYS = {".csv", ".tsv", ".txt", ".md", ".json", ".xlsx", ".xls"}
# Cần thư viện thêm — xem requirements.txt
ATTACH_EXT_OPTIONAL = {".pdf", ".docx"}

# --------------------------------------------------------------------------
# Tri thức chung (global knowledge base)
# --------------------------------------------------------------------------
# Dataset thủ tục hành chính LUÔN tra cứu được ở MỌI hội thoại, đánh chỉ mục
# MỘT LẦN (data/chromadb_eval + data/bm25_index.pkl đã có sẵn). Không upload
# lại, không nhúng lại theo từng cuộc trò chuyện.
GLOBAL_KB_NAME = "Thủ tục hành chính (dataset nội bộ)"
GLOBAL_KB_TOOL = "search_procedures"


# ==========================================================================
# v6.1 — sửa sau lần chạy thử đầu tiên
# ==========================================================================
# Trình duyệt cache JS/CSS cũ -> nút đính kèm không hoạt động và ô nhập bị bẹp
# vì CSS mới chưa được nạp. Đổi số này là mọi trình duyệt phải tải lại.
STATIC_VERSION = "6.3"

# Bao nhiêu thủ tục được đưa vào prompt.
# Lần chạy đầu: đưa 3 thủ tục -> mô hình 1.5B gộp cả 3 thành một câu trả lời 10
# gạch đầu dòng lộn xộn (cấp số nhà + gia hạn tạm trú + ...). Nay chỉ đưa thêm
# ứng viên nào SÁT ĐIỂM với top-1; còn lại chỉ đưa đúng một thủ tục.
EVIDENCE_PROCEDURES_MAX = 3
EVIDENCE_TIE_GAP = 0.06        # cách top-1 xa hơn mức này -> không đưa vào prompt

# Người dùng nói thẳng "tra trên mạng đi" thì phải tra, không bàn cãi.
# Đây KHÔNG phải guardrail lên mô hình — đây là MỆNH LỆNH CỦA NGƯỜI DÙNG.
WEB_FORCE_PHRASES = [
    "web search", "websearch", "search web", "tim tren web", "tra tren web",
    "tim tren mang", "tra tren mang", "len mang", "google", "tra google",
    "tim google", "dung web", "dung internet", "tra internet", "tim internet",
    "search tren mang", "tra cuu tren mang", "tim kiem tren mang",
]


# ==========================================================================
# v6.2 — ngữ cảnh dính + chẩn đoán
# ==========================================================================
# Câu hỏi tiếp nối ("nộp ở đâu?", "tốn nhiều tiền?") phải nói về thủ tục ĐANG
# nói tới, chứ không phải đi truy hồi lại từ đầu.
#
# Lỗi thật đã gặp: đang nói về "gia hạn tạm trú" (nơi nộp = Công an Xã), hỏi
# "Nộp ở đâu" -> truy hồi mới trả về một thủ tục giao thông với độ tin cậy 0.43
# -> trả lời "Cục Cảnh sát giao thông". Sai hoàn toàn, mà nghe rất tự tin.
#
# Quy tắc: câu hỏi nhắm vào MỘT trường (lệ phí / thời gian / hồ sơ / nơi nộp)
# + đang có thủ tục trong ngữ cảnh + truy hồi mới KHÔNG đủ chắc (< TIER_A)
# => quay lại đúng thủ tục đang nói tới.
FOLLOWUP_STICKY = True

# --------------------------------------------------------------------------
# Tìm kiếm web — thử nhiều backend
# --------------------------------------------------------------------------
# duckduckgo_search/ddgs có nhiều backend; backend mặc định hay hỏng hoặc bị
# chặn tốc độ. Thử lần lượt, ghi lại cái nào chạy được.
WEB_SEARCH_BACKENDS = ["lite", "html", "auto"]
# Lọc allowlist mà không còn kết quả nào: vẫn BÁO CÁO là đã tìm thấy nhưng bị
# loại, để phân biệt "tra hỏng" với "tra được nhưng nguồn không chính thống".
WEB_SEARCH_REPORT_BLOCKED = True

# --------------------------------------------------------------------------
# Chế độ nhà phát triển (app/developer_mode.py)
# --------------------------------------------------------------------------
# DEV_TOOLS_ENABLED quyết định có ĐĂNG KÝ route hay không (bảo mật thật).
# Cờ dưới đây chỉ quyết định có GHI LẠI vết chạy hay không, bật/tắt được ngay
# trong giao diện.
DEVMODE_DEFAULT_ON = True
DEVMODE_TRACE_SIZE = 40        # số lượt gần nhất giữ trong bộ nhớ


# ==========================================================================
# v6.3 — sàn độ tin cậy, nguồn có link, tra web bám .gov.vn
# ==========================================================================
# Dưới mức này thì bản ghi truy hồi được KHÔNG đáng tin để trả lời.
# Lỗi thật: hỏi "Đến nơi đâu để nộp hồ sơ" -> truy hồi ra "Đăng ký khai sinh"
# ở mức 0.20, mà giao diện vẫn dán nhãn xanh "Từ cơ sở dữ liệu thủ tục · 0.20"
# rồi in nguyên bản ghi khai sinh ra. Nhãn NÓI DỐI, và người dân tin.
#
# Dưới sàn này: thử quay lại thủ tục đang nói tới; không có thì BỎ HẲN bằng
# chứng và trả lời như không có dữ liệu — thà nói "mình chưa có" còn hơn đưa
# nhầm thủ tục.
EVIDENCE_MIN_CONFIDENCE = 0.45

# Câu ngắn được coi là hỏi tiếp (dùng cho ngữ cảnh dính, kể cả khi bộ nhận diện
# "hỏi vào trường nào" không bắt được cách diễn đạt).
FOLLOWUP_MAX_WORDS = 9

# --------------------------------------------------------------------------
# Tra web bám nguồn chính thống ngay từ truy vấn
# --------------------------------------------------------------------------
# Đo được: truy vấn trần trả 20 kết quả, chỉ 4 qua allowlist. Nhét gợi ý miền
# vào ngay truy vấn đầu tiên thì tỉ lệ dùng được cao hơn hẳn, đỡ phải chạy các
# lượt dự phòng.
WEB_SEARCH_QUERY_HINT = "site:gov.vn"
# Vẫn giữ một lượt truy vấn TRẦN để dự phòng: có câu chỉ báo chí mới viết.
WEB_SEARCH_PLAIN_FALLBACK = True

# Trả về ĐƯỜNG LINK đầy đủ thay vì chỉ tên miền, để người dân bấm vào kiểm tra.
WEB_SEARCH_RETURN_URLS = True

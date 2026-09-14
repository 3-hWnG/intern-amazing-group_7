# Trợ Lý Pháp Lý & Dịch Vụ Công Việt Nam - Nhóm 7

Hệ thống Trợ lý ảo tư vấn thủ tục hành chính công cấp xã/phường và tra cứu pháp luật Việt Nam, ứng dụng kiến trúc **Hybrid RAG (Dense ChromaDB 280 views + BM25 Okapi + Cross-Encoder Reranker)** kết hợp **Phân tầng phản hồi (Semantic Tier Router)** và mô hình ngôn ngữ lớn chạy **Local 100% (Ollama `3b-finetune`)**.

---

## Tính Năng Nổi Bật

- **Kiến trúc Phân tầng Đa tầng (Adaptive Tiers)**:
  - **Tầng A (Dữ liệu chuẩn xác CSDL)**: Trả về trực tiếp 100% thông tin từ cơ sở dữ liệu (thành phần hồ sơ, lệ phí, thời gian giải quyết, link DVC) trong 0.001s; triệt tiêu hoàn toàn hiện tượng ảo giác, nhại prompt hay cắt cụt câu.
  - **Tầng B (Làm rõ nhu cầu)**: Chủ động gợi ý danh sách thủ tục tương đồng khi câu hỏi còn chung chung để người dân bấm chọn.
  - **Tầng C (Tra cứu Internet)**: Tự động tra cứu trực tiếp qua DuckDuckGo khi câu hỏi nằm ngoài 70 thủ tục của UBND, sau đó dùng LLM tổng hợp câu trả lời kèm nguồn dẫn.
  - **Tầng Giao thông & Đời sống**: Tích hợp sẵn cẩm nang xử phạt vi phạm giao thông (Nghị định 100/123) và tình huống đời sống (tiếng ồn, chặt cây, thẻ CCCD).
  - **Tầng Xã giao (Smalltalk)**: Nhận diện phản hồi chào hỏi, cảm ơn, tạm biệt tức thì mà không cần qua mô hình tốn tài nguyên.
- **Truy hồi lai đa góc nhìn (Hybrid RRF Multi-View)**:
  - 280 views ngữ nghĩa đa chiều trong ChromaDB (`tên`, `tóm tắt`, `hồ sơ`, `tình huống đời thường`).
  - Tìm kiếm từ khóa BM25 Okapi có chuẩn hóa và loại bỏ dấu tiếng Việt.
  - Cross-Encoder Reranker (`AITeamVN/Vietnamese_Reranker`) xếp hạng lại Top ứng viên chính xác.
- **Tự động thu thập dữ liệu (Live Web Scraper)**: Tích hợp sẵn công cụ bóc tách trực tiếp từ Cổng Dịch vụ công quốc gia và Bộ Công An (`crawl_dichvucong.py`).
- **Quản lý Phiên & Xác thực Tài khoản**:
  - Lưu trữ SQLite (`data/app.db`) với cơ chế xác thực kép: JWT Bearer lưu `localStorage` và `HttpOnly Cookie`.
  - Tự động tóm tắt ngữ cảnh hội thoại khi vượt ngưỡng token.
- **Hàng đợi Xử lý (Queue Manager)**: Hạn chế xung đột phần cứng, xử lý tuần tự/song song mượt mà trên CPU/GPU.
- **Công cụ Quản trị Phát triển (Dev Tools)**: Hộp công cụ thống kê số liệu CSDL thời gian thực và nút Reset dữ liệu an toàn theo từng phạm vi.

---

## Cấu Trúc Thư Mục

```text
intern-amazing-group_7/
├── app/
│   ├── main.py              # Điểm khởi chạy: FastAPI, REST API & Giao diện Web SPA
│   ├── config.py            # Cấu hình toàn bộ: tên model, ngưỡng RRF, port, đường dẫn
│   ├── tiers.py             # Phân tầng phản hồi (A/B/C), Smalltalk, luật giao thông & DuckDuckGo
│   ├── retrieval.py         # Lõi Hybrid RRF (Dense ChromaDB + BM25 Okapi + Reranker)
│   ├── ingest.py            # Đọc Excel -> nhúng vector ChromaDB & chỉ mục BM25
│   ├── database.py          # Quản lý SQLite (users, conversations, messages, sessions)
│   ├── models.py            # Pydantic schemas & Data classes
│   ├── queue_manager.py     # Hàng đợi xử lý yêu cầu song song chống quá tải CPU/GPU
│   ├── crawl_dichvucong.py  # Module cào dữ liệu trực tiếp từ Cổng Dịch vụ công (Live Scraper)
│   └── core.py              # Module nhúng vector & ChromaDB độc lập (phục vụ Evaluation)
├── data/
│   ├── data_merged.xlsx     # Bộ dữ liệu 70 thủ tục hành chính công cấp xã chuẩn hóa
│   ├── data_crawl.xlsx      # Dữ liệu cào mới nhất từ Cổng DVC
│   ├── app.db               # Cơ sở dữ liệu SQLite lưu tài khoản & lịch sử hội thoại
│   └── chromadb/            # Cơ sở dữ liệu vector lưu 280 views nhúng
├── Evaluation/              # Bộ dữ liệu và script chấm điểm truy hồi benchmark (862 câu hỏi)
│   ├── evaluate_retrieval.py # Script đo lường Recall@K, MRR, Accuracy
│   ├── core.py              # Module nạp vectorstore cho evaluation
│   └── eval_questions.csv   # Tập dữ liệu 862 câu hỏi đánh giá thực tế
├── requirements.txt         # Danh sách thư viện Python cần thiết
├── run.ps1                  # PowerShell script tiện ích (chạy web, ingest, test, eval)
└── README.md                # Hướng dẫn cài đặt và sử dụng
```

---

## Hướng Dẫn Cài Đặt & Sử Dụng

### Bước 1: Chuẩn bị Mô hình Local LLM (Ollama)
1. Tải và cài đặt [Ollama](https://ollama.com/).
2. Đảm bảo bạn đã có mô hình **`3b-finetune`**:
   ```bash
   ollama list
   ```
   *(Nếu dùng mô hình mặc định khác, bạn có thể chạy: `ollama run qwen2.5:1.5b`)*.

### Bước 2: Cài đặt Môi trường Python
1. Mở Terminal (PowerShell) tại thư mục dự án `intern-amazing-group_7`.
2. Tạo môi trường ảo (Virtual Environment):
   ```powershell
   python -m venv venv
   ```
3. Kích hoạt môi trường ảo:
   ```powershell
   .\venv\Scripts\activate
   ```
4. Cài đặt các thư viện cần thiết:
   ```powershell
   pip install -r requirements.txt
   ```

### Bước 3: Khởi tạo Dữ liệu Vector & Chỉ mục BM25
*(Chỉ cần thực hiện 1 lần đầu tiên hoặc khi bạn có cập nhật file Excel dữ liệu)*
- Chạy qua script tiện ích:
  ```powershell
  .\run.ps1 -Ingest
  ```
- Hoặc chạy trực tiếp file python:
  ```powershell
  python app/ingest.py
  ```

### Bước 4: Khởi động Server & Trải nghiệm
-  Chạy qua PowerShell script tiện ích:
  ```powershell
  .\run.ps1
  ```

=> **Mở trình duyệt Web truy cập:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Các Lệnh Tiện Ích Trong `run.ps1`

File tiện ích `run.ps1` được tích hợp sẵn các chế độ vận hành chuyên nghiệp:

| Lệnh | Chức năng |
|---|---|
| `.\run.ps1` | Khởi động Web Server (mặc định tại `http://127.0.0.1:8000`) |
| `.\run.ps1 -Ingest` | Nạp lại 70 thủ tục từ Excel vào ChromaDB và tạo chỉ mục BM25 |
| `.\run.ps1 -Check` | Kiểm tra tính toàn vẹn thư viện, phiên bản PyTorch và GPU CUDA |
| `.\run.ps1 -Eval` | Chạy chấm điểm tự động toàn bộ 862 câu test (Recall@K, Hit Rate) |
| `.\run.ps1 -Eval -Limit 50` | Chạy chấm điểm nhanh trên 50 câu hỏi mẫu |

---

## Thu Thập Dữ Liệu Tự Động (`crawl_dichvucong.py`)

Hệ thống cung cấp module `crawl_dichvucong.py` giúp tự động bóc tách dữ liệu thủ tục hành chính trực tiếp từ Cổng Dịch vụ công (`dichvucong.bocongan.gov.vn`):
- Bóc tách đầy đủ 7 trường nghiệp vụ cốt lõi: Tên thủ tục, lĩnh vực, hình thức nộp, thành phần hồ sơ, thời gian, lệ phí và địa điểm tiếp nhận.
- Tự động làm sạch dữ liệu và xuất ra `data/data_crawl.xlsx`.
- Cách chạy cào dữ liệu:
  ```powershell
  python app/crawl_dichvucong.py
  ```

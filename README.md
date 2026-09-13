# LLM Pháp Lý - Nhóm 7 (Demo)

Hệ thống RAG + Semantic Router + DuckDuckGo MCP chạy Local 100%.

## Cấu trúc thư mục

```text
app/
├── main.py              # Điểm khởi chạy: ráp FastAPI, gắn static + routes
├── config.py            # TẤT CẢ hằng số: đường dẫn, tên model, tham số LLM, port
├── ingest.py            # Đọc Excel -> nhúng vector -> nạp ChromaDB (chạy 1 lần)
├── api/
│   ├── routes.py        # Endpoint GET / và POST /chat
│   └── schemas.py       # Kiểu dữ liệu request
├── core/
│   ├── anchors.py       # Câu mẫu của 3 luồng (sửa để chỉnh độ nhạy router)
│   ├── router.py        # Semantic Router (cosine similarity)
│   ├── embeddings.py    # Nạp SentenceTransformer + phép toán vector
│   ├── vectorstore.py   # Truy vấn ChromaDB (RAG)
│   ├── websearch.py     # Cổng MCP DuckDuckGo
│   ├── llm.py           # Cổng Ollama (stream)
│   └── pipeline.py      # Ráp luồng: router -> bằng chứng -> prompt
├── prompts/
│   └── templates.py     # Khuôn prompt của từng luồng
├── templates/index.html # Khung giao diện
└── static/              # css/styles.css và js/app.js
data/dataset.xlsx        # File gốc 42 thủ tục hành chính
```

Muốn sửa gì thì vào đúng file đó, không phải đọc cả nghìn dòng:
đổi model/port -> `config.py`; đổi văn phong AI -> `prompts/templates.py`;
đổi giao diện -> `static/` và `templates/`; router bắt sai -> `core/anchors.py`.

## Hướng dẫn cài đặt 

**Bước 1: Tải Local LLM (Ollama)**
1. Tải và cài đặt [Ollama](https://ollama.com/).
2. Bật Terminal gõ: `ollama run qwen2.5:1.5b`. (Chờ tải xong thì gõ `/bye` để thoát).

**Bước 2: Cài đặt môi trường Python**
1. Clone source code này về máy.
2. Mở Terminal tại thư mục code, tạo môi trường ảo:
   `python -m venv venv`
3. Kích hoạt môi trường:
   - Windows: `.\venv\Scripts\activate`
4. Cài thư viện:
   `pip install -r requirements.txt`

**Bước 3: Khởi tạo Database RAG**
Đảm bảo đã kích hoạt môi trường (có chữ `(venv)` ở đầu dòng):
   - `python app/ingest.py`
*(Chờ nó báo Done! Database ready. Chỉ cần chạy 1 lần duy nhất).*

**Bước 4: Chạy Server**
`python app/main.py`
-> Mở trình duyệt Web truy cập: `http://localhost:8000`

*(Đường dẫn giờ tính từ gốc project nên chạy ở thư mục nào cũng được, không bắt buộc `cd app`.)*

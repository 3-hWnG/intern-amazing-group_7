# Trợ Lý Ảo Pháp Lý - Nhóm 7 (MVP Demo)

Hệ thống RAG + Semantic Router + DuckDuckGo MCP chạy Local 100%.

## Cấu trúc thư mục
- `app/main.py`: Chứa lõi FastAPI, Semantic Router và Giao diện UI.
- `app/ingest.py`: Script tự động đọc Excel và nhúng vào Vector DB (ChromaDB).
- `data/dataset.xlsx`: File gốc 42 thủ tục hành chính.

## Hướng dẫn cài đặt cho Thành viên Nhóm

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
`cd app`

`python ingest.py`
*(Chờ nó báo Done! Database ready. Chỉ cần chạy 1 lần duy nhất).*

**Bước 4: Chạy Server**
Vẫn trong thư mục `app`:
`python main.py`
-> Mở trình duyệt Web truy cập: `http://localhost:8000`

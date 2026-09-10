# GIẢI PHẪU DỰ ÁN LEGAL AI - NHÓM 7 (PROJECT BREAKDOWN)

Tài liệu này dùng để phổ biến cho các thành viên trong Nhóm 7, giúp mọi người hiểu rõ toàn bộ thư mục code và luồng chạy (Workflow) của hệ thống RAG + Semantic Router.

---

## 1. Cấu Trúc Thư Mục (Folder Structure)

Dự án nằm trọn trong thư mục `D:\intern_7` (hoặc tên repo Github khi tải về). Gồm 2 phần chính:

```text
📁 intern_7
├── 📁 app/
│   ├── main.py        # 🧠 Trái tim hệ thống (API, Giao diện, Router, LLM)
│   └── ingest.py      # 🔨 Kịch bản băm dữ liệu thô nhét vào Vector DB
├── 📁 data/
│   ├── dataset.xlsx   # 📄 File Excel gốc (42 thủ tục hành chính)
│   └── 📁 chromadb/   # 🗄️ Database Vector cục bộ (Chứa dữ liệu đã nhúng)
├── .gitignore         # 🛡️ File chặn đụng hàng đẩy lên Github (chặn venv, chromadb)
├── README.md          # 📜 Sổ tay hướng dẫn cài đặt chạy máy (Setup Guide)
└── requirements.txt   # 📦 Danh sách thư viện Python cần cài đặt
```

---

## 2. Giải Phẫu Chức Năng (Từng File Làm Gì?)

### 🔨 `app/ingest.py` (Script Xử lý Dữ liệu)
- **Nhiệm vụ:** Biến dữ liệu thô thành Não bộ cho AI.
- **Cách hoạt động:** Dùng `pandas` đọc file Excel. Nó bốc đúng 4 cột quan trọng (Tên thủ tục, Hồ sơ, Thời gian, Lệ phí). Sau đó dùng Mô hình nhúng ngôn ngữ `vietnamese-sbert` băm các chữ này thành các Vector đa chiều (Số học) và nhét vào thư mục `data/chromadb`.
- **Lưu ý:** Chỉ cần chạy file này **1 lần duy nhất** khi tải project về.

### 🧠 `app/main.py` (Trái Tim Hệ Thống)
Đây là File Code quan trọng nhất, gánh 4 tác vụ cực nặng:
1. **Giao diện (Frontend):** Chứa trực tiếp mã HTML/CSS/JS (Clone phong cách của ChatGPT/Gemini) với tính năng chuyển đổi Light/Dark Theme mượt mà. 
2. **Bộ Não Định Tuyến (Semantic Router):** Khi User gõ câu hỏi, nó không bắt chữ (Keyword) ngu ngốc. Nó dùng thuật toán `Cosine Similarity` để đo khoảng cách Vector từ câu hỏi tới 3 cụm Điểm Trọng Tâm (LUAT, NGOAI, XAGIAO) để bẻ lái luồng chạy.
3. **Cổng Kết Nối MCP (DuckDuckGo):** Nếu Router bẻ vào luồng `NGOAI`, file này kích hoạt hàm móc ra Internet cào tin tức nóng hổi về nạp cho AI (Realtime).
4. **Prompt Engineering (Kiểm soát Ảo giác):** Gài luật thép bắt LLM phải tuân thủ nghiêm ngặt (Ví dụ: Hỏi Hộ chiếu phải đuổi sang Công An, Vi phạm luật giao thông phải đọc Nghị định). Giúp mô hình nhỏ (1.5B) không nói nhảm.

### 🗄️ `data/dataset.xlsx` và `data/chromadb/`
- Excel là nơi Sếp/Mentor quăng dữ liệu vào.
- Thư mục `chromadb` sinh ra sau khi chạy `ingest.py`. **Tuyệt đối không đẩy `chromadb` lên Github** vì nó rác và nặng. Máy ai tải code về tự chạy `ingest.py` để sinh ra.

---

## 3. Luồng Hoạt Động Cốt Lõi (Workflow Data)

Khi một thành viên nhập câu hỏi: *"Thủ tục đăng ký kết hôn cần giấy tờ gì?"*
1. **UI:** Web gửi API `/chat` dạng JSON chứa câu hỏi xuống `main.py`.
2. **Semantic Router:** Câu hỏi bị băm thành Vector. So khớp thấy khoảng cách gần nhất với mảng `LUAT` -> Đi vào luồng LUẬT.
3. **Tra RAG:** Code chui vào `chromadb`, bốc 2 thủ tục liên quan nhất (Evidence Pack).
4. **Ép Prompt:** Trộn Câu Hỏi + Bằng Chứng RAG + Lệnh Ép Khuôn (Persona Cán bộ Phường).
5. **Sinh Text:** Gửi nguyên cụm Prompt đó qua lõi Máy chủ **Ollama** đang chạy ngầm (`qwen2.5:1.5b`).
6. **Trả Kết Quả:** LLM nôn ra câu trả lời (có định dạng Markdown) -> Đẩy ngược về giao diện ChatGPT trên Web.

Tất cả diễn ra hoàn toàn Offline (Chỉ kết nối Internet nếu nhảy luồng MCP). Chấm hết.

# System Architecture

## 1. Overview
Kiến trúc hệ thống Sys_3_4 được xây dựng theo mô hình phân tầng mô-đun hóa cao, phân tách độc lập giữa tầng giao diện, tầng định tuyến, tầng truy hồi nghiệp vụ, tầng sinh ngôn ngữ và tầng kiểm chứng.

## 2. Main Components

| Thành phần | Công nghệ sử dụng | Chức năng chính |
|---|---|---|
| **Frontend** | HTML5 / JavaScript (Vanilla / Tailwind CSS), Server-Sent Events (SSE) | Giao diện trò chuyện trực quan, hỗ trợ hiển thị bảng, nút chọn thủ tục làm rõ, xem trước nguồn trích dẫn |
| **Backend API** | Python FastAPI / Uvicorn | Quản lý phiên hội thoại, điều phối streaming SSE, bảo mật phân quyền |
| **Context Tracker** | `retrieval/context.py` & `retrieval/rank.py` | Quản lý trạng thái đa lượt `ConvState`, cô lập trạng thái hỏi lại `is_clarify`, kế thừa trường thông tin |
| **Strict Retrieval** | SQLite 3, FTS5 Virtual Table, Python C-extension | Tìm kiếm toàn văn FTS5, tính trọng số âm tiết IDF, phạt lệch dấu, xử lý biến thể thủ tục |
| **Vector DB** | Qdrant (Local on-disk mode tại `runtime/qdrant`) | Lưu trữ vector nhúng 1024 chiều của tài liệu người dùng và các điều kiện phức tạp |
| **Embedder & Reranker** | BGE-M3 & BGE-Reranker-v2-m3 | Trích xuất đặc trưng ngữ nghĩa và chấm điểm độ liên quan chéo giữa câu hỏi và tài liệu |
| **Local SLM Service** | Ollama / vLLM (Qwen2.5-7B-Instruct) | Sinh câu trả lời tự nhiên theo khuôn mẫu JSON Schema nghiêm ngặt |
| **Post-hoc Verifier** | `server/answer/verifier.py` | Kiểm chứng tất định số tiền, số ngày, căn cứ văn bản, loại bỏ các ý vi phạm |

## 3. Architecture Diagrams
Sơ đồ kiến trúc chi tiết được lưu trữ tại:
- [Kiến trúc Tổng thể Hệ thống](file:///D:/Thư mục mới/intern-amazing-group_7 (merge_sys_3_4)/04_proposed_system/diagrams/architecture.png)
- [Luồng Hoạt động và Tương tác](file:///D:/Thư mục mới/intern-amazing-group_7 (merge_sys_3_4)/04_proposed_system/diagrams/workflow.png)
- [Kiến trúc Kép Dual-Engine](file:///D:/Thư mục mới/intern-amazing-group_7 (merge_sys_3_4)/04_proposed_system/diagrams/dual_engine.jpg)

# knowledge/ — chỗ dành cho Box 5B (RAG) và 6B (import PDF/DOC/web)

**Chỉ là thiết kế giao diện (Phase 20). Chưa có RAG, chưa có import; `interface.py` không được gọi trong đường chạy.**

## Interface dự kiến (`interface.py`)
```python
class KnowledgeSource(Protocol):
    def search(self, query: str, k: int = 5) -> list[Evidence]: ...

Evidence = {"source": str,   # nhãn người đọc được: "Tên tài liệu, trang/mục" hoặc URL
            "text": str,     # đoạn NGUYÊN VĂN, không tóm tắt
            "score": float,  # 0..1, chỉ để xếp hạng
            "origin": "rag"} # luôn "rag"; bằng chứng Direct mang origin="direct"
```
- `search` thuần đọc, không gọi LLM sinh chữ, không ném lỗi ra ngoài (lỗi/kho rỗng -> `[]`).
- Một nguồn = một lớp thoả Protocol (kho vector, BM25, thư mục tài liệu...). Planner/Policy không biết bên trong.

## Nơi để import (Box 6B)
`knowledge/import/` : thả PDF, DOC/DOCX, ảnh chụp trang, hoặc tệp `.url` (web) vào đây. Bộ import tương lai: tách đoạn -> ghi chỉ mục -> `search` đọc chỉ mục.
Mỗi tài liệu cần: tên, nguồn gốc, ngày, cấp (xã/phường?), người duyệt. Tài liệu chưa duyệt không được dùng để trả lời.

## Evidence Bundle (Box 7): gộp Direct + RAG
Hiện: bundle = các ô dữ liệu thủ tục lấy qua `data.api` (Direct, nguyên văn, có nguồn).
Khi có 5B: `bundle = direct_evidence + rag.search(câu hỏi)`, mỗi phần tử ghi `origin`.
- Direct luôn đứng trước và thắng khi mâu thuẫn (dữ liệu cổng là gốc); RAG chỉ bổ sung (ví dụ giải thích văn bản, hướng dẫn ngoài cổng).
- Giới hạn số đoạn RAG (đề xuất <= 5) và độ dài để vừa ngữ cảnh Qwen3-4B.

## Kỳ vọng với Verifier (Box 9)
- Mọi ý trong câu trả lời phải dẫn tới một Evidence trong bundle (cite id); số tiền/ngày/thời hạn/tên văn bản phải xuất hiện nguyên văn trong Evidence được dẫn (như `server/answer/verifier.py` hiện làm với Direct).
- Ý chỉ dựa vào RAG phải hiển thị nguồn RAG và gắn nhãn "ngoài dữ liệu cổng".
- Không có Evidence đủ tin cậy -> nói không có, không suy đoán; RAG không được dùng để suy ra "miễn phí".

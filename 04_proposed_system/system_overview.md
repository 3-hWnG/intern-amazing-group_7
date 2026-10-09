# System Overview

**Sys_3_4** là hệ thống trợ lý AI chuyên biệt cho lĩnh vực hành chính công và quản trị pháp lý tại Việt Nam. Hệ thống hoạt động theo nguyên lý **Dual-Engine (Kiến trúc kép)**:

```
                            ┌─────────────────────────────────────────┐
                            │         Người Dùng (Web UI / SSE)       │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼
                            ┌─────────────────────────────────────────┐
                            │    Bộ Định Tuyến & Ngữ Cảnh (Router)    │
                            └────────────┬───────────────┬────────────┘
                                         │               │
                 [Câu hỏi tra cứu 1 mục] │               │ [Hội thoại / So sánh / Dataset]
                                         ▼               ▼
                 ┌─────────────────────────────┐   ┌─────────────────────────────┐
                 │   STRICT ENGINE (Sys 3)     │   │   FRIENDLY ENGINE (Sys 4)   │
                 │ ─────────────────────────── │   │ ─────────────────────────── │
                 │ • Chuẩn hóa & N-gram lỗi gõ │   │ • BGE-M3 Dense Vectors      │
                 │ • Syllable IDF + Phạt dấu   │   │ • Qdrant Vector Search      │
                 │ • SQLite FTS5 Lát cắt       │   │ • RRF Fusion + Reranker     │
                 │ • Trả lời bằng Code chuẩn   │   │ • Ollama Qwen2.5-7B (vLLM)  │
                 │ • Độ trễ: 7 - 15 ms         │   │ • Post-hoc Fact Verifier    │
                 │ • Ảo giác: 0.0%             │   │ • Độ trễ: 2.5 - 4.5 s       │
                 └──────────────┬──────────────┘   └──────────────┬──────────────┘
                                │                                 │
                                └────────────────┬────────────────┘
                                                 │
                                                 ▼
                                ┌─────────────────────────────────┐
                                │     Phản Hồi Chuẩn Xác & Nguồn  │
                                └─────────────────────────────────┘
```

Hệ thống được thiết kế theo các tôn chỉ:
1. **Chính xác pháp lý là ưu tiên hàng đầu:** Không đánh đổi tính chính xác để lấy sự hoa mỹ của văn phong.
2. **Minh bạch tuyệt đối:** Cung cấp nguồn trích dẫn (`cites`) cho từng ý trong câu trả lời.
3. **Phản hồi tức thì:** Phục vụ công dân với tốc độ dưới 50ms cho các truy vấn dữ liệu tiêu chuẩn.

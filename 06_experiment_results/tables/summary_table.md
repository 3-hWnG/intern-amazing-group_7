# Summary Comparison Table

Bảng so sánh chi tiết giữa các phiên bản hệ thống qua các giai đoạn phát triển:

| Metric | Baseline V10.6 | System 3 (Strict) | System 4 (Friendly) | **Sys_3_4 (Merged)** |
|---|---|---|---|---|
| **Kiến trúc** | FTS thuần | Rule + Syllable IDF | Vector + LLM | **Dual-Engine Tích hợp** |
| **Top-1 Accuracy (DEV)** | 11.2% | 84.1% | 78.5% | **96.3%** |
| **Top-1 Accuracy (HOLDOUT)** | 10.6% | 71.4% | 68.2% | **75.3%** |
| **Ngữ cảnh Multi-turn** | 0.0% (Không hỗ trợ) | 82.4% | 74.0% | **96.7% (88/91)** |
| **Xử lý Tách chữ dính** | Không | Heuristic | Không | **Bigram Data-Driven** |
| **Sửa lỗi chính tả** | Không | Seed từ điển | Không | **N-gram Data-Driven** |
| **Kiểm chứng số liệu** | Không | 100% Code | Prompt LLM | **100% Code Verifier** |
| **Độ trễ trung vị (p50)** | 32 ms | 11 ms | 3,400 ms | **24 ms / 2.8s** |

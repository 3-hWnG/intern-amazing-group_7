# Câu trên slide và trong bài báo cần sửa (sau kế hoạch G0–G4, 18/10/2026)

Danh sách để trưởng nhóm quyết; **không tự sửa slide hay bài báo**. Mỗi dòng: chỗ nói, câu hiện tại (tóm), sự thật bây giờ, nguồn.
Slide: theo mô tả trong [MINH_CHUNG_EVALUATION_SLIDE.md](MINH_CHUNG_EVALUATION_SLIDE.md). Bài báo: [research_paper.md](research_paper.md).

## Slide

| # | Chỗ | Hiện nói | Sự thật bây giờ | Nguồn |
|---|---|---|---|---|
| S1 | Slide 2 (Strict) dòng 1 | top-1 73%, top-3 80% (bộ mù gộp, dữ liệu 1.350 thủ tục) | Dữ liệu chính thức giờ là **bản 3** (1.517 thủ tục): top-1 **72%** (274/381), top-3 79%; 136 ca bị loại vì mã đáp án không còn trong bản 3 và không ghép được. Nếu giữ số 73% thì phải ghi rõ "trên bản snapshot 1.350" | `docs/PLAN_TUAN_TOI.md` (eval #1, #2) |
| S2 | Slide 2 dòng 2 | hành vi đúng 78% | bản 3: **77%** (400/518) ở eval #2. Giảm so với #1 (407) hoàn toàn do thẻ **hỏi tỉnh** (D5): 9 ca nhãn "trả lời" giờ hỏi tỉnh | như trên |
| S3 | Slide 2 dòng 3 | hỏi lại đúng 47% | **50%** (38/76) ở eval #2 | như trên |
| S4 | Slide 2 dòng 7 | câu chỉ cần code < 0,2 s, "có hay không GPU đều vậy" | 1 người: p95 ~0,19 s. **10 người cùng dùng: p95 1,18 s** (CPU dùng chung với Ollama + reranker). Máy không GPU: chưa đo trên máy thật; code đã làm Strict bỏ bước LLM khi không có GPU (test: < 0,5 s) | `ARCHITECTURE_REVIEW_2026-10-15.md` §5.4, `system4/eval/results/load_10users_real.json` |
| S5 | Slide 2 dòng 8 | AI viết câu trả lời ~1,5 s có GPU, ~7 s chỉ CPU | 10 người, có GPU: **p50 2,9 s / p95 4,0 s** (chờ GPU tối đa 3 s rồi trả bản code; sinh chữ p95 1,8 s). "~7 s chỉ CPU" vẫn không có phép đo; nay khi không GPU, Strict **không gọi** model | như trên |
| S6 | Slide 3 (Friendly) tốc độ | chữ đầu / cả câu (số cũ không tìm thấy nguồn) | 1 người: chữ đầu 1,25–1,7 s. **10 người (nghỉ 20–40 s): chữ đầu p50 6,2 / p95 15,2 s; cả câu p50 11,2 / p95 21,3 s**; phần lớn là chờ hàng GPU (p95 13,6 s; trưởng nhóm chấp nhận ~15 s cho thí điểm, D17). Câu y chang câu đã 👍 trả ngay | như trên |
| S7 | Mọi chỗ nhắc "Suy nghĩ kỹ", nút "Trả lời nhanh" / "Kỹ hơn", model `qwen3:4b` (bản suy nghĩ) | — | **Đã bỏ** (D9). Một model `qwen3:4b-instruct-2507-q4_K_M` cho Strict + Friendly | `system4/README.md` |
| S8 | Nếu slide nói "liệt kê thủ tục" của Strict | liệt kê gần đúng 10 tên (12% đúng lĩnh vực) | text-to-SQL trên bảng phẳng: **98%** đúng lĩnh vực (bộ khuôn 40 câu), bộ đo riêng **93%** (42/45). Chỉ chạy khi có LLM | `eval/saved_results/2026-10-18_listsql/` |
| S9 | Nếu slide nói biểu mẫu | "Cổng không có biểu mẫu" | Cổng liệt kê 2.147 tệp mẫu cho 928 thủ tục; hệ thống trả tên mẫu + link trang thủ tục (tệp tải về 0 byte) | `server/answer/answerer.py` `_forms_text` |

## Bài báo (`research_paper.md`)

| # | Dòng | Hiện nói | Sự thật | Ghi chú |
|---|---|---|---|---|
| P1 | 138, 159 | Friendly chạy "Qwen-2.5-1.5B/7B via vLLM" với "Model Context Protocol (MCP)"; sơ đồ "Local SLMs (Qwen-2.5-7B on vLLM)" | Chạy **Ollama** với **`qwen3:4b-instruct-2507-q4_K_M`** (4B), không vLLM, không MCP | sai về kiến trúc, nên sửa trước khi nộp |
| P2 | 26, 47, 242 | 75,3% top-1 HOLDOUT-4; 96,3% DEV | Số trên dữ liệu snapshot 1.350. Trên bản 3 (chính thức): bộ mù gộp 72%, dev 98% (cách gộp khác, xem PLAN_TUAN_TOI). Ghi rõ dữ liệu nào hoặc đo lại HOLDOUT-4 riêng trên bản 3 | |
| P3 | 47 | "latency percentiles (p50 20–33 ms)" | 1 người p50 vài chục ms là đúng cho câu chỉ-luật; khi 10 người dùng p50 0,31 s / p95 1,18 s. Nên nêu cả số khi có tải | §5.4 |
| P4 | 243 | 8/16 câu mơ hồ ở HOLDOUT-4 hỏi lại đúng | bộ mù gộp bản 3: 38/76 (50%). Thử thêm tín hiệu reranker / độ rộng cụm (G4.1) đều lỗ ròng nên chưa đưa vào | `eval/clarify_signals.py` |
| P5 | 244 | phí công bố cho 467/1.350 thủ tục (34,6%) | bản 3: **549/1.517 (36,2%)**; có số tiền cụ thể: 170 | đếm `fees_clean` |
| P6 | 250 | "eliminates phantom …" (khẳng định tuyệt đối) | Không có phép đo nào chứng minh "loại bỏ hoàn toàn"; nên viết "giảm" kèm số đo | |
| P7 | 252 (hướng phát triển) | mở rộng phí theo tỉnh | Đã có: bản riêng của 34 tỉnh, thẻ hỏi tỉnh (D5) — có thể chuyển từ "hướng phát triển" sang "đã làm" | G4.4 |

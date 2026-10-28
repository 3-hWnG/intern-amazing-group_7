# AI Model Integration (khuôn bước 8)

Bản đề xuất (lớp luật A) **không dùng model để quyết định**. Các model dưới đây là phương án so sánh hoặc baseline. Mỗi model bật hay tắt bằng cờ.

| Nội dung | BGE-M3 + bge-reranker-v2-m3 (phương án B) | Qwen3-4B-Instruct-2507 (phương án C, baseline RAG) |
|---|---|---|
| Model là gì | Embedding đa ngôn ngữ cùng cross-encoder xếp lại | LLM 4B, chỉ có chế độ non-thinking, lượng tử hoá 4-bit (`qwen3:4b-instruct-2507-q4_K_M`) |
| Vì sao chọn | Hỗ trợ tiếng Việt, mã mở, chạy được tại máy (paper 09) | Model nhỏ nhất đủ đọc thư tiếng Việt dài, chạy được trên một máy; mã mở Apache-2.0 (paper 08) |
| Lấy từ đâu | Hugging Face (BAAI) | Ollama; model card trên Hugging Face (Qwen) |
| Input | Câu hỏi; ứng viên gồm tên, lĩnh vực, kết quả, đối tượng của thủ tục | **C:** câu hỏi. **Baseline RAG:** câu hỏi cùng 5 thủ tục BGE-M3 tìm được, đánh số |
| Output | Điểm cho mỗi cặp (câu hỏi, thủ tục) | **C:** ý định thuộc 6 lớp, và tên thủ tục bằng chữ (JSON schema). **Baseline RAG:** hành động (answer / clarify / refuse) và số thứ tự thủ tục |
| Cách tích hợp | Hàm Python trong `retrieval/semantic.py`, chạy trong cùng tiến trình server | Gọi Ollama qua HTTP tại máy (`server/core/llm.py`), temperature 0, có JSON schema. Model **không bao giờ viết mã thủ tục**: tên do model trả về được ánh xạ sang thủ tục bằng chính ranker của luật |
| Quyết định | Từ chối khi điểm cao nhất dưới ngưỡng; đổi thủ tục khi chênh điểm đủ lớn. Ngưỡng chọn trên tập dev | **C:** ý định khác "thủ tục" thì từ chối. **Baseline RAG:** model tự quyết toàn bộ |

## Baseline

Chi tiết ở `05_methodology/baseline.md`.
- Mốc tầm thường: luôn từ chối, luôn trả lời.
- Bản gốc (mọi cờ tắt).
- B chạy một mình, C chạy một mình.
- RAG + model 4B tự quyết (prompt v2, chọn trên dev).
- Cổng học L (thêm sau, *post hoc*): xem mục dưới.

## Cổng học (phân tích sau, *post hoc*)

| Nội dung | Naive Bayes (`eval/hard/learned_gate.py`) | Hồi quy logistic (`eval/hard/learned_gate_emb.py`) |
|---|---|---|
| Đặc trưng | n-gram từ (1–2) và n-gram ký tự (3–5) của câu đã bỏ dấu | Embedding BGE-M3 của câu hỏi (qua Ollama) |
| Học trên | Nhãn dev: 282 câu (cho test 1), 595 câu (cho test 2) | Như bên trái; cân bằng lớp, điều chuẩn L2 |
| Chọn ngưỡng | 5-fold trên dev | 5-fold trên dev, cả hệ số điều chuẩn |
| Cách ghép | Thay cổng viết tay, đặt trên bản gốc: cổng bảo từ chối thì từ chối, không thì giữ quyết định của bản gốc | Như bên trái |

## Điều kiện chạy
- Mọi model chạy tại máy, không gọi API bên ngoài.
- Khi đánh giá có canh nhiệt (`eval/thermal.py`). Trần cho phép là 70 °C tới 26/10 và 80 °C từ 27/10 (trưởng nhóm duyệt). Ngưỡng tạm dừng thực tế là 60/52 °C, rồi 65/57 °C.
- Mỗi cấu hình chạy một lần trên tập test.

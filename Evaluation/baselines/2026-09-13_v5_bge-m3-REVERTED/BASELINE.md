# BASELINE v5 — AITeamVN/Vietnamese_Embedding — ĐÃ HOÀN NGUYÊN

Thử đổi mô hình nhúng từ `keepitreal/vietnamese-sbert` (768 chiều, 256 token)
sang `AITeamVN/Vietnamese_Embedding` (nền bge-m3, 1024 chiều, 2048 token).

| | v4 (sbert) | v5 (bge-m3) | Δ |
|---|---|---|---|
| Recall@1 | **0.8556** | 0.8494 | −0.006 |
| Recall@5 | 0.9753 | **0.9802** | +0.005 |
| MRR@10 | 0.9061 | 0.9068 | +0.001 |
| situational | 0.769 | 0.778 | +0.009 |
| no_diacritics | **0.611** | 0.593 | −0.018 |
| Hộ tịch | **0.667** | 0.633 | −0.034 |
| Tầng A sai | **3.6%** | 5.0% | +1.4đ |
| Độ trễ trung vị | 236 ms | 245 ms | +9 ms |

## Kết luận: HOÀN NGUYÊN về `keepitreal/vietnamese-sbert`

Tiêu chí đặt ra TRƯỚC khi chạy: dưới ~2 điểm R@1 thì không đáng đổi. Thực tế
−0.6 điểm. Mô hình lớn gấp 3 lần, tốn thêm ~1.7GB VRAM, đổi lại không có cải
thiện đo được.

**Vì sao đổi mô hình nhúng không ăn thua:** BM25 (bỏ dấu) đang gánh phần lớn
việc khớp từ khoá — đo riêng ở v1 đã đạt R@1 0.72 một mình. Nâng cấp phía dense
không còn nhiều chỗ để cải thiện. R@5 có nhỉnh hơn (sinh ứng viên tốt hơn) nhưng
thứ tự xếp hạng lại kém đi một chút.

**Điều này KHÔNG có nghĩa Vietnamese_Embedding là mô hình tệ.** Nó có thể thắng
rõ nếu: (a) bỏ BM25, (b) dataset lớn hơn nhiều, hoặc (c) tài liệu dài hơn 256
token — điều mà sbert không xử lý nổi. Với 70 thủ tục và có BM25, nó thừa.

Muốn thử lại: đổi `EMBED_MODEL_NAME` trong `config.py` rồi chạy `.\run.ps1 -Ingest`.

# BASELINE v1 — 13/09/2026 — hybrid BM25 + dense, multi-view

| | v0 | **v1** | Δ |
|---|---|---|---|
| Recall@1 | 0.5272 | **0.7457** | **+0.2185** |
| Recall@5 | 0.8037 | **0.9469** | **+0.1432** |
| MRR@10 | 0.6400 | **0.8276** | **+0.1876** |

Cấu hình: `keepitreal/vietnamese-sbert` (KHÔNG đổi) · chroma **cosine** · multi-view
(title/summary/docs) · BM25 bỏ dấu · RRF · chưa bật reranker.

**Không đổi mô hình nào.** Toàn bộ mức tăng đến từ: bỏ dấu + BM25, tách nhiều view,
và đổi metric sang cosine.

## Theo kiểu câu hỏi — so với v0 và với BM25 đơn lẻ

| variant | v0 (dense) | BM25 đơn | **v1 (hybrid)** |
|---|---|---|---|
| keyword | 0.648 | 0.907 | **0.907** |
| facet_fee | 0.593 | 0.806 | **0.870** |
| facet_time | 0.583 | 0.824 | **0.843** |
| facet_docs | 0.574 | 0.870 | **0.843** |
| facet_online | 0.574 | 0.907 | **0.833** |
| facet_place | 0.574 | 0.741 | **0.815** |
| typo | 0.556 | 0.574 | **0.722** |
| colloquial | 0.426 | 0.463 | **0.630** |
| situational | 0.528 | 0.500 | **0.602** |
| abbrev | 0.519 | 0.630 | **0.556** ⚠ |
| no_diacritics | 0.056 | 0.574 | **0.407** ⚠ |

⚠ **Hai slice bị hybrid làm TỆ HƠN BM25 đơn lẻ.** RRF đang cộng ngang hàng, nên
tín hiệu dense (vốn mù với chữ không dấu: 0.056) kéo tụt thứ hạng. Đã sửa ở v2
bằng RRF có trọng số + hạ trọng số dense khi câu hỏi không dấu.

## Theo lĩnh vực (v0 → v1)

Hộ tịch 0.422 → **0.633** · Cư trú 0.356 → **0.867** · Con dấu 0.413 → **0.800** ·
Ngành nghề KD 0.311 → **0.467** · Kinh tế-Hạ tầng 0.456 → **0.644** ·
Văn hóa-Xã hội 0.550 → **0.817** · Căn cước 0.644 → **0.711**

## Phân bố độ tin cậy (0..1, càng lớn càng giống)

| nhóm | p10 | p25 | median | p75 |
|---|---|---|---|---|
| Trúng | 0.606 | 0.657 | 0.714 | 0.770 |
| Trượt | 0.408 | 0.508 | 0.623 | 0.708 |
| Ngoài phạm vi | 0.300 | 0.409 | 0.462 | 0.529 |

Trúng vs Ngoài phạm vi tách rõ hơn hẳn v0.

## Vấn đề phát hiện: luật "hỏi lại" bắn nhầm

Với ngưỡng thử nghiệm (A=0.62, B=0.45, gap=0.04):
- in-scope: A=52% B=43% C=5% — **B quá lớn**
- 141 câu (17%) vào B vì confidence nằm trong dải
- **207 câu (26%) vào B chỉ vì top1/top2 sát nhau — và 66% số đó ĐÃ lấy đúng dòng**

Nguyên nhân: dataset có các dòng trùng (8/21, 10/13, 9/14, 23/25) và các dòng cùng
thủ tục khác cấp (căn cước, hộ chiếu, ANTT, con dấu). Hai ứng viên đầu là CÙNG một
thủ tục nên hỏi lại là vô nghĩa.

## Quét ngưỡng (gap = 0.02)

| A_MIN | B_MIN | A% | B% | C% | OOS→A% | OOS→C% | A sai% | mất câu đúng% |
|---|---|---|---|---|---|---|---|---|
| 0.58 | 0.55 | 67 | 22 | 11 | 10 | 83 | 13.4 | 3.8 |
| **0.62** | **0.55** | 61 | 28 | 11 | 8 | 83 | 11.6 | 3.8 |
| 0.65 | 0.55 | 55 | 34 | 11 | 4 | 83 | 10.4 | 3.8 |

Chọn **A_MIN = 0.62, B_MIN = 0.55, gap = 0.02**: chặn 83% câu ngoài phạm vi sang
web search, chỉ mất 3.8% câu đúng, tầng A sai 11.6%.

## Tái lập
```powershell
cd app; python ingest.py
python evaluate_retrieval.py --eval "..\..\..\Evaluation\eval_questions.csv" --out "..\..\..\Evaluation\eval_results.csv"
```

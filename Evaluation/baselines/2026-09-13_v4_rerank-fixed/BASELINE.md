# BASELINE v4 — 13/09/2026 — reranker + 2 sửa lỗi hiệu chỉnh

| | v0 | v2 | v3 | **v4** |
|---|---|---|---|---|
| Recall@1 | 0.5272 | 0.7765 | 0.8358 | **0.8556** |
| Recall@5 | 0.8037 | 0.9556 | 0.9630 | **0.9753** |
| MRR@10 | 0.6400 | 0.8470 | 0.8910 | **0.9061** |
| no_diacritics | 0.056 | 0.611 | 0.315 | **0.611** |
| Tầng A sai | — | 15.1% | 1.0% | **3.6%** |
| Tầng A phủ (in-scope) | — | 74% | 24% | **57%** |
| OOS → web search | — | 83% | 100% | **92%** |
| Độ trễ trung vị | — | — | 240 ms | **236 ms** |

Vẫn dùng `keepitreal/vietnamese-sbert`. CHƯA đổi mô hình nhúng.

## Hai sửa lỗi so với v3
1. `RERANK_SKIP_NO_DIACRITICS = True` — bỏ rerank khi truy vấn không dấu
   (reranker nền bge-m3 xếp sai trên chữ không dấu): 0.315 → 0.611.
2. `CONFIDENCE_FROM_RERANKER = False` — reranker quyết định THỨ TỰ, độ tin cậy
   lấy từ điểm hoà dense+BM25. Điểm reranker phân bố hai cực nên không đặt
   ngưỡng được. Tầng A từ 24% lên 57% phủ, vẫn giữ sai số thấp (3.6%).

## Phân bố độ tin cậy (đã dùng được trở lại)
| nhóm | p10 | p25 | median | p75 |
|---|---|---|---|---|
| Trúng | 0.628 | 0.731 | 0.786 | 0.830 |
| Trượt | 0.324 | 0.420 | 0.583 | 0.715 |
| Ngoài phạm vi | 0.147 | 0.249 | 0.395 | 0.478 |

Ngưỡng đang dùng: A = 0.75, B = 0.65.

## Lĩnh vực yếu nhất còn lại
Hộ tịch **0.667** (R@5 0.978 → lỗi xếp hạng, không phải lỗi truy hồi) ·
Kinh tế-Hạ tầng 0.767 · Xuất nhập cảnh 0.833 · Phương tiện giao thông 0.800

# BASELINE v3 — 13/09/2026 — hybrid + cross-encoder reranker (GPU)

| | v0 | v2 | **v3** |
|---|---|---|---|
| Recall@1 | 0.5272 | 0.7765 | **0.8358** |
| Recall@5 | 0.8037 | 0.9556 | **0.9630** |
| MRR@10 | 0.6400 | 0.8470 | **0.8910** |
| Tầng A sai | — | 15.1% | **1.0%** |
| Độ trễ trung vị | — | — | **240 ms** (p95 330 ms) |

Cấu hình: `keepitreal/vietnamese-sbert` + `AITeamVN/Vietnamese_Reranker`, cả hai
trên **CUDA** (torch 2.14.0+cu130). Vẫn CHƯA đổi mô hình nhúng.

## Sự cố hạ tầng phát hiện trong lần này

`.venv` cài bản **torch CPU-only**, nên `torch.cuda.is_available()` luôn trả về
`False`. Toàn bộ các lần đo trước (v0, v1, v2) và cả bản demo gốc đều chạy CPU —
đoạn "Ép xung Phần cứng, nhanh gấp 10-20 lần nếu có card NVIDIA" trong
`log code main.md` chưa từng thực sự chạy. Sau khi cài `torch==2.14.0+cu130`:
reranker từ **6214 ms/câu** xuống **240 ms/câu** (nhanh hơn ~26 lần).

## Theo kiểu câu hỏi

| variant | v2 | **v3** | |
|---|---|---|---|
| facet_place | 0.815 | **0.981** | |
| keyword | 0.926 | **0.963** | |
| facet_fee | 0.889 | **0.954** | |
| facet_docs | 0.870 | **0.935** | |
| facet_online | 0.907 | 0.889 | |
| facet_time | 0.870 | 0.843 | |
| colloquial | 0.593 | **0.833** | |
| typo | 0.685 | **0.815** | |
| situational | 0.611 | **0.769** | |
| abbrev | 0.667 | **0.741** | |
| **no_diacritics** | 0.611 | **0.315** | ⚠ HỎNG |

## Hai lỗi cần sửa ở v4

**1. Reranker phá câu gõ không dấu (0.611 → 0.315).**
Vietnamese_Reranker dựa trên bge-m3, huấn luyện trên tiếng Việt CÓ dấu. Với
truy vấn không dấu nó xếp lại và đẩy kết quả đúng của BM25 xuống.
→ Bỏ qua bước rerank khi truy vấn không có dấu (giống cách đã hạ trọng số dense).

**2. Điểm reranker KHÔNG dùng làm độ tin cậy được.**

| nhóm | p10 | p25 | median | p75 |
|---|---|---|---|---|
| Trúng | 0.001 | 0.012 | 0.148 | 0.915 |
| Trượt | 0.000 | 0.000 | 0.001 | 0.039 |
| Ngoài phạm vi | 0.000 | 0.000 | 0.001 | 0.003 |

Phân bố hai cực (gần 0 hoặc gần 1), không có vùng giữa → mọi ngưỡng đều sai.
Hệ quả: 71% câu in-scope rơi xuống tầng C dù truy hồi ĐÚNG.
→ Dùng reranker để XẾP THỨ TỰ, nhưng lấy điểm hoà dense+BM25 làm ĐỘ TIN CẬY
(thang đó đã hiệu chỉnh tốt ở v2: A=0.75, B=0.65).

Điểm tích cực: khi reranker tự tin thì nó đúng — tầng A chỉ sai 1.0% (2/198).

## Theo lĩnh vực (v0 → v3)
Cư trú 0.356 → **0.933** · Ngành nghề KD 0.311 → **0.911** · Con dấu 0.413 → **0.920** ·
Văn hóa-Xã hội 0.550 → **0.894** · Kinh tế-Hạ tầng 0.456 → **0.772** ·
Căn cước 0.644 → **0.800** · **Hộ tịch 0.422 → 0.611** (vẫn là lĩnh vực yếu nhất)

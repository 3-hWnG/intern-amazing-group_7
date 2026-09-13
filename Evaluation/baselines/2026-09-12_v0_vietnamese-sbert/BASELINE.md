# BASELINE v0 — 12/09/2026

Mốc đo đầu tiên của dự án. Mọi thay đổi sau này so với bảng này.

## Cấu hình đo

| | |
|---|---|
| Mô hình nhúng | `keepitreal/vietnamese-sbert` (PhoBERT, giới hạn 256 token) |
| Vector DB | ChromaDB, metric mặc định **L2**, `n_results=10` |
| Dữ liệu | `data_merged.xlsx` — 70 thủ tục |
| Định dạng document | `Thủ tục / Thành phần hồ sơ / Thời gian / Lệ phí` (4/7 cột) |
| Bộ câu hỏi | `eval_questions.csv` — 862 câu (810 trong phạm vi + 52 ngoài) |
| Máy | RTX 4050 Laptop, venv `.venv` |

Chưa có: reranker, BM25, ngưỡng, session, fact-check.

## Kết quả tổng thể

| Chỉ số | Giá trị |
|---|---|
| **Recall@1** | **0.5272** |
| **Recall@5** | **0.8037** |
| **MRR@10** | **0.6400** |

Khoảng cách R@5 − R@1 = **0.277** → tài liệu đúng thường ĐÃ được lấy về
nhưng XẾP HẠNG SAI. Đây là phần mà reranker ăn trực tiếp.

## Theo kiểu câu hỏi

| Kiểu | n | R@1 | R@5 |
|---|---|---|---|
| keyword | 54 | 0.648 | 0.852 |
| facet_fee | 108 | 0.593 | 0.852 |
| facet_time | 108 | 0.583 | 0.917 |
| facet_docs | 108 | 0.574 | 0.870 |
| facet_online | 54 | 0.574 | 0.833 |
| facet_place | 54 | 0.574 | 0.926 |
| typo | 54 | 0.556 | 0.815 |
| situational | 108 | 0.528 | 0.833 |
| abbrev | 54 | 0.519 | 0.759 |
| colloquial | 54 | 0.426 | 0.722 |
| **no_diacritics** | **54** | **0.056** | **0.204** |

## Theo lĩnh vực

| Lĩnh vực | n | R@1 | R@5 |
|---|---|---|---|
| Quản lý vũ khí, vật liệu nổ | 30 | 0.933 | 0.933 |
| giáo dục và đào tạo *(viết thường)* | 15 | 0.933 | 1.000 |
| Đăng ký, quản lý phương tiện giao thông | 30 | 0.833 | 1.000 |
| Lao động - Tiền lương | 15 | 0.733 | 0.933 |
| Quản lý xuất nhập cảnh | 30 | 0.700 | 0.967 |
| Giáo dục và Đào tạo *(viết hoa)* | 15 | 0.667 | 1.000 |
| Cấp, quản lý căn cước | 45 | 0.644 | 0.956 |
| Chứng thực - sao y | 15 | 0.600 | 0.933 |
| Văn hóa - Xã hội | 180 | 0.550 | 0.839 |
| Kinh tế - Hạ tầng và đô thị | 180 | 0.456 | 0.694 |
| **Hộ tịch** | 90 | **0.422** | 0.756 |
| Đăng ký, quản lý con dấu | 75 | 0.413 | 0.733 |
| Đăng ký, quản lý cư trú | 45 | 0.356 | 0.578 |
| Quản lý ngành nghề kinh doanh có điều kiện | 45 | 0.311 | 0.844 |

## Phân bố khoảng cách top-1 (L2, càng nhỏ càng giống)

| Nhóm | n | p25 | median | p75 |
|---|---|---|---|---|
| Trúng (in-scope) | 427 | 45.6 | 53.3 | 61.4 |
| Trượt (in-scope) | 383 | 51.5 | 59.4 | 68.4 |
| Ngoài phạm vi | 52 | 71.1 | 81.4 | 89.6 |

**Trúng vs Trượt chồng nhau gần hoàn toàn** → khoảng cách KHÔNG cho biết
"có lấy đúng dòng không".

**Trúng vs Ngoài phạm vi tách được** → CÓ thể đặt ngưỡng "câu này có trả lời
được từ DB không":

| LOW | % câu ngoài phạm vi bị chặn | % câu trả lời đúng bị mất |
|---|---|---|
| 68 | 82.7 | 11.9 |
| **70** | **76.9** | **8.2** |
| 72 | 71.2 | 5.9 |
| 75 | 65.4 | 3.5 |

## 12 topic tệ nhất

| topic | R@1 | R@5 |
|---|---|---|
| con_dau_dac_biet | 0.00 | 0.20 |
| **khai_sinh** | **0.00** | **0.20** |
| thong_bao_khoi_cong | 0.00 | 0.20 |
| to_quoc_ghi_cong | 0.00 | 0.47 |
| con_dau_moi | 0.00 | 0.60 |
| antt_cap_lai | 0.00 | 0.67 |
| tho_cung_liet_si | 0.00 | 0.87 |
| thong_tin_quy_hoach | 0.07 | 0.07 |
| xoa_thuong_tru | 0.07 | 0.13 |
| antt_cap_moi | 0.07 | 0.93 |
| xac_nhan_vi_tri | 0.13 | 0.60 |
| cap_lai_gcn_hkd | 0.13 | 0.67 |

## Phát hiện chính

1. **Thủ tục đăng ký khai sinh (dòng id 1) KHÔNG BAO GIỜ được xếp hạng 1**
   trong cả 862 câu hỏi. Câu `"đăng ký khai sinh cần giấy tờ gì"` — chứa gần
   nguyên văn tên thủ tục — trả về dòng 64, và dòng đúng không có trong top-10.
   Đây chính là lý do demo xin lỗi khi được hỏi về khai sinh: **không phải
   prompt từ chối, mà là truy hồi không tìm ra**.

2. **Gõ không dấu làm hệ thống mù**: R@1 0.056, 41/54 câu không tìm thấy đáp án
   trong top-10. Cùng nội dung có dấu đạt ~0.57.

3. **Câu hỏi chứa sẵn tên thủ tục chỉ đạt R@1 0.57** (lẽ ra phải ~0.95).
   Tên thủ tục bị phần "thành phần hồ sơ" nhấn chìm trong cùng một vector.

4. **Câu tình huống (0.528) gần bằng câu có sẵn tên (0.574)** → vấn đề KHÔNG
   phải ở chỗ "hỏi bằng câu hỏi, lưu bằng câu trả lời". Vấn đề cơ bản hơn:
   mô hình không khớp nổi tên thủ tục với chính nó.

5. **Hiệu ứng hub**: 5/70 dòng hút 23.2% toàn bộ truy vấn (đều thì chỉ ~7%).
   7 dòng không bao giờ đứng hạng 1: `1, 9, 12, 52, 53, 57, 63`.
   Đã kiểm tra giả thuyết "do độ dài document": tương quan chỉ +0.15 → không
   phải nguyên nhân. Là hiệu ứng hub thường gặp của retriever yếu.

6. **Nhóm topic nhiều dòng đạt 0.587 > nhóm một dòng 0.504** — nhưng đây là
   artifact của cách gán nhãn (nhãn là TẬP dòng nên có nhiều cách đúng hơn),
   KHÔNG phải bằng chứng rằng dòng trùng vô hại.

## Thứ tự việc nên làm (suy ra từ số liệu)

1. **Đặt ngưỡng LOW ≈ 70** — làm được ngay, không tốn gì, chặn 77% câu ngoài
   phạm vi, chỉ mất 8% câu đúng.
2. **Reranker trên top-5** — nhắm thẳng vào khoảng cách 0.277; trần lý thuyết
   đưa R@1 lên ~0.80.
3. **BM25 lai dense** — câu chứa sẵn tên thủ tục mà vẫn trượt chính là việc
   của khớp từ khoá.
4. **Đổi mô hình nhúng** — cách duy nhất sửa được lỗi gõ không dấu.

## Cách tái lập

```powershell
cd "D:\Claude\LLM Legal Project\Web\intern-amazing-group_7-main"
.\.venv\Scripts\activate
cd app
python ingest.py
python evaluate_retrieval.py --eval "..\..\..\Evaluation\eval_questions.csv" --out "..\..\..\Evaluation\eval_results.csv"
```
`config.py`: `DATASET_PATH = DATA_DIR / "data_merged.xlsx"`, `CHROMA_PATH = DATA_DIR / "chromadb_eval"`.

Lưu ý: repo có 2 virtualenv — `venv` (rỗng) và `.venv` (đầy đủ). Dùng `.venv`.

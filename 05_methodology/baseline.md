# Baseline và so sánh

## 1. Baseline đã có (cùng bộ câu, cùng giao thức)

Đã chạy trên test real_v2: 313 câu, code đóng băng `b7010d1`, mỗi cấu hình một lần.

| Baseline | Là gì | Cân bằng | Trả lời đúng trọn |
|---|---|---|---|
| Luôn từ chối | Mốc tầm thường (lớp từ chối chiếm 79%): hành vi đúng 248/313 (79,2%) | 0,500 | 0/59 |
| Luôn trả lời | Giữ thủ tục xếp đầu của bản gốc: hành vi đúng 59/313 (18,9%) | 0,500 | **20/59** |
| Bản gốc (mọi cờ tắt) | Hệ thống trước đợt này: xếp hạng IDF theo âm tiết (`retrieval/rank.py`) + luật cũ | 0,647 | 19/59 |
| Reranker (B một mình) | bge-m3 + bge-reranker-v2-m3 quyết định giữ / đổi / từ chối, ngưỡng chọn trên dev | 0,692 | 21/59 |
| Model 4B đọc câu (C một mình) | qwen3:4b-instruct-2507 đọc ý định và tên thủ tục | 0,785 | 25/59 |

Hai mốc tầm thường tính bằng `eval/hard/metrics.py` `baselines()` trên `real_v2_off.json`, ngày 25/10.

**Lưu ý khi viết:**

- "Luôn từ chối" có hành vi đúng 79,2%, cao hơn bản gốc (56,5%). Vì vậy chỉ số chính là **độ chính xác cân bằng**, không phải hành vi đúng.
- "Luôn trả lời" có trả lời đúng trọn 20/59, nhỉnh hơn bản gốc (19/59): bản gốc đôi khi từ chối nhầm câu mà thủ tục xếp đầu của nó lại đúng.
- Phải báo cả hai mốc. Hai mốc này cho thấy chỉ một chỉ số đơn lẻ dễ gây hiểu lầm.

## 2. Công trình ngoài: vì sao không đặt số cạnh nhau

Bài trước (paper_list.md mục 1) làm **nhiệm vụ khác**:

- PhamDuy2023 và AnsGen2025 dùng các cặp hỏi đáp đã có câu trả lời, lấy từ trang câu hỏi phổ biến của Cổng DVC. Chúng đo truy hồi đoạn văn (Recall@k, MAP) hoặc chất lượng câu sinh ra (ROUGE). Bộ của họ **không có câu ngoài phạm vi** và không đo hành vi từ chối hay hỏi lại.
- ViGPTQA2023 và Hien2025 hỏi đáp trên văn bản luật, đánh giá bằng bộ riêng (có phần do AI sinh) hoặc RAGAS và khảo sát người dùng.

Vì vậy bài chỉ có **bảng định tính**: nhiệm vụ, nguồn câu hỏi, có hay không câu ngoài phạm vi, metric, chạy tại chỗ hay không. Không có cột "điểm" để xếp hạng (constraints.md C3.1).

| Công trình | Nguồn câu hỏi | Câu ngoài phạm vi | Hỏi lại | Metric | Model |
|---|---|---|---|---|---|
| PhamDuy2023 | 4.547 cặp từ trang câu hỏi phổ biến của Cổng DVC | Không | Không | Recall@k, MAP, NDCG, F2 | BM25+, SimCSE/PhoBERT, cross-encoder |
| AnsGen2025 (chưa kiểm xong, **không trích** trong bài) | ~10.000 cặp từ Cổng DVC | — | — | — | — |
| ViGPTQA2023 | Bộ riêng, trộn AI sinh và người viết | — | — | (đọc bảng trước khi ghi) | ViGPT |
| Bài 1 | Câu thật của người dân (Bình Định, Bộ Công an), hai tầng mẫu | **Có, 79%** | Có (6 câu) | Hành vi 3 lớp, cân bằng, top-1/3, MRR@5, trả lời đúng trọn | Luật + xếp hạng IDF; bge-m3, reranker; qwen3 4B |

## 3. Baseline ngoài: RAG + model 4B tự quyết (trưởng nhóm duyệt 25/10, đã chạy)

**Kết quả.** Prompt v1 viết trước lượt chạy dev đầu tiên. v1 hỏi lại quá nhiều (123/220 câu phải từ chối, 39/55 câu phải trả lời), nên viết thêm đúng hai biến thể và ghi lại trước khi chạy: v2 (quy tắc quyết định theo thứ tự) và v3 (v2 cộng mô tả thủ tục). Trên dev, v1 đạt 0,343, v2 0,445, v3 0,432, nên chọn v2. Chạy mỗi bộ test một lần (code `65b55af` cho test 1, `88cabd6` cho test 2):

| Bộ | Cân bằng | Từ chối đúng | Trả lời đúng trọn | Coi "hỏi lại" là từ chối |
|---|---|---|---|---|
| Test 1 (313) | 0,489 | 104/248 | 28/59 | 0,727 |
| Test 2 (363) | 0,413 | 197/335 | 4/21 | 0,574 |

So với A trên test 1: hành vi +16/−141 (p ≈ 4·10⁻²⁶). So với A2 + B trên test 2: +19/−122 (p ≈ 10⁻¹⁹).

Phần dưới là đề xuất ban đầu (25/10), giữ để biết thiết kế đã được định trước như thế nào.

Reviewer có thể hỏi: một hệ RAG thường, để model tự quyết trả lời hay từ chối, thì được bao nhiêu? Lúc đó chưa có cấu hình nào đúng như vậy. C là model đọc câu đặt trên luật cũ, không phải "LLM tự quyết".

- **Cấu hình đề xuất:** bge-m3 lấy top-5 thủ tục. Model 4B nhận câu hỏi và 5 thủ tục, được nhắc "chỉ trả lời nếu một thủ tục khớp, nếu không thì từ chối hoặc hỏi lại", rồi trả về một nhãn và một mã thủ tục. Prompt viết trước, không chỉnh trên test.
- **Chạy:** một lần trên real_v2, có canh nhiệt (≤ 70 °C), không gọi API tốn phí. Dùng lại model đã có, không tải gì mới.
- **Ghi rõ trong bài:** baseline này được thêm **sau khi test đã mở**. Vì nó không được chọn hay chỉnh theo test nên vẫn hợp lệ làm mốc so sánh, nhưng phải nói thẳng ra.
- **Chi phí:** khoảng 313 lượt gọi model 4B, cỡ một lượt C.

## 4. Cổng học (thêm sau, *post hoc*)

So với chỉ cổng viết tay đặt trên bản gốc ("gate only"). Khoảng bootstrap cặp 95% của hiệu độ chính xác cân bằng lấy từ `eval/hard/results/paired_stats.json`:

| Cấu hình | Test 1: cân bằng | Hiệu so với gate only | Test 2: cân bằng | Hiệu so với gate only |
|---|---|---|---|---|
| Gate only | 0,770 | — | 0,666 | — |
| Naive Bayes | 0,765 | −0,005 [−0,057; 0,045] | 0,579 | −0,088 [−0,204; 0,029] |
| Hồi quy logistic trên BGE-M3 | 0,801 | +0,031 [−0,008; 0,071] | 0,586 | −0,080 [−0,199; 0,039] |

Không cổng học nào tốt hơn có ý nghĩa thống kê về cân bằng hay đúng trọn. Trên test 2, hai cổng học tốt hơn về hành vi (+31/−15, p = 0,026 và +34/−13, p = 0,003), vì chúng từ chối nhiều hơn. Nhưng chúng chỉ quyết định "trả lời" ở 5/21 câu phải trả lời, so với 10/21 của cổng viết tay.

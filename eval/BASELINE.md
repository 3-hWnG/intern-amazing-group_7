# BASELINE (Phase 0) - retrieval cũ của repo

Đo ngày 2026-10-05 trên `repo/Database/runtime/procedures.db` (1.350 thủ tục active), 185 câu (`cases.jsonl`).
Adapter: `baseline_adapter.py` = `retrieval.parse_query` -> `retrieval.search(limit=5)` -> `is_strong`, chỉ nhìn lượt user cuối.
Quy ước hành vi: chitchat (`is_chitchat`) -> answer; `is_strong` -> answer; còn lại -> apologize (nhánh "không tìm thấy").
Baseline KHÔNG có planner, field, câu trả lời => các cột fields / bịa số / trích nguồn là `-` (chưa đo được, chờ System 3).
Lệnh tái lập: `python run.py --name baseline` và `python run.py --adapter baseline_adapter:adapter_stripped --name baseline_stripped`.

Lưu ý đo: `dynamic synonyms` (bảng admin) nạp từ `Backend.db` nên KHÔNG có trong baseline này (báo "No module named 'db'", đã tắt log);
baseline thiếu từ đồng nghĩa admin. Viết tắt cứng trong `_ABBREV` (dk, cccd...) vẫn hoạt động.

## 1. Baseline nguyên trạng
| Hạng mục | n | top-1 | top-3 | đúng fields | đúng hành vi | bịa số | nói 'không công bố' | trích nguồn | is_strong sai | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clarify_conditional | 15 | 11% (1/9) | 11% (1/9) | - | 7% (1/15) | - | - | - | - | 33 | 38 |
| context_memory | 15 | 7% (1/15) | 13% (2/15) | - | 27% (4/15) | - | - | - | - | 27 | 34 |
| ctx_cond_evidence | 15 | 7% (1/15) | 7% (1/15) | - | 0% (0/15) | - | - | - | - | 36 | 42 |
| evidence_citation | 15 | 0% (0/15) | 7% (1/15) | - | 0% (0/15) | - | - | - | - | 34 | 40 |
| hallucination_unsupported | 15 | 0% (0/7) | 14% (1/7) | - | 60% (9/15) | - | - | - | 7% (1/15) | 31 | 34 |
| multi_field | 15 | 0% (0/15) | 0% (0/15) | - | 0% (0/15) | - | - | - | - | 33 | 37 |
| multi_intent | 15 | 0% (0/15) | 0% (0/15) | - | 0% (0/15) | - | - | - | - | 33 | 40 |
| out_of_scope | 30 | - | - | - | 80% (24/30) | - | - | - | 17% (5/30) | 29 | 36 |
| quantitative | 15 | 27% (4/15) | 33% (5/15) | - | 33% (5/15) | - | - | - | - | 45 | 57 |
| rag_basic | 15 | 13% (2/15) | 20% (3/15) | - | 40% (6/15) | - | - | - | - | 42 | 46 |
| typo | 20 | 30% (6/20) | 55% (11/20) | - | 50% (10/20) | - | - | - | - | 25 | 34 |
| **TỔNG** | 185 | 11% (15/141) | 18% (25/141) | - | 32% (59/185) | - | - | - | - | 33 | 46 |

## 2. Biến thể chẩn đoán: gỡ cụm chỉ-field trước khi tra (`adapter_stripped`)
Gỡ "cần giấy tờ gì / bao nhiêu / ở đâu / lệ phí..." bằng danh sách cứng rồi mới `parse_query`. Tách phần lỗi do từ chỉ field làm hỏng truy vấn
khỏi lỗi nội tại của khớp chữ.
| Hạng mục | n | top-1 | top-3 | đúng fields | đúng hành vi | bịa số | nói 'không công bố' | trích nguồn | is_strong sai | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clarify_conditional | 15 | 0% (0/9) | 33% (3/9) | - | 13% (2/15) | - | - | - | - | 29 | 36 |
| context_memory | 15 | 7% (1/15) | 13% (2/15) | - | 40% (6/15) | - | - | - | - | 21 | 27 |
| ctx_cond_evidence | 15 | 7% (1/15) | 13% (2/15) | - | 7% (1/15) | - | - | - | - | 36 | 42 |
| evidence_citation | 15 | 7% (1/15) | 13% (2/15) | - | 27% (4/15) | - | - | - | - | 33 | 39 |
| hallucination_unsupported | 15 | 0% (0/7) | 14% (1/7) | - | 67% (10/15) | - | - | - | 27% (4/15) | 30 | 32 |
| multi_field | 15 | 40% (6/15) | 47% (7/15) | - | 13% (2/15) | - | - | - | - | 32 | 38 |
| multi_intent | 15 | 0% (0/15) | 0% (0/15) | - | 40% (6/15) | - | - | - | - | 31 | 34 |
| out_of_scope | 30 | - | - | - | 73% (22/30) | - | - | - | 23% (7/30) | 27 | 37 |
| quantitative | 15 | 40% (6/15) | 67% (10/15) | - | 87% (13/15) | - | - | - | - | 31 | 35 |
| rag_basic | 15 | 47% (7/15) | 80% (12/15) | - | 93% (14/15) | - | - | - | - | 27 | 33 |
| typo | 20 | 45% (9/20) | 80% (16/20) | - | 70% (14/20) | - | - | - | - | 25 | 31 |
| **TỔNG** | 185 | 22% (31/141) | 39% (55/141) | - | 51% (94/185) | - | - | - | - | 29 | 38 |

## 3. Số liệu chính (141 câu chấm truy hồi = câu in-scope có đáp án thủ tục; 117 câu là đơn-task, không tính multi-intent/clarify)
| | nguyên trạng | gỡ field |
|---|---|---|
| top-1 (141) | 15 = 11% | 31 = 22% |
| top-3 (141) | 25 = 18% | 55 = 39% |
| top-1 / top-3 chỉ câu đơn-task (117) | 14 = 12% / 24 = 21% | 31 = 26% / 52 = 44% |
| In-scope bị `is_strong` = True nhưng top-1 SAI | 19/27 câu "strong" (70%) | 46/65 (71%) |
| Out-of-scope (30): `is_strong` kích hoạt sai | 5/30 = 17% (01, 14, 20, 21, 24) | 7/30 = 23% |
| Out-of-scope (30): hành vi đúng | 80% | 73% |
| Hallucination "không có trong kho" (7 câu) xin lỗi đúng | 7/7 | 6/7 |
| p50 / p95 độ trễ tra cứu | 32 / 45 ms | 30 / 39 ms |

## 4. Câu thất bại điển hình
Nguyên trạng (từ khoá FTS trộn cả từ chỉ field):
- `rag_basic-04` "Đăng ký kết hôn do cơ quan nào giải quyết?" -> từ khoá `dang ky ket hon do co quan nao giai quyet`, top-1 = "Đăng ký biến động ... (đất đai)" (1.115928); kết hôn không vào top-3.
- `quantitative-07` "Đăng ký kết hôn có mất lệ phí không?" (lỗi đã biết ở PLAN) -> top-1 = "Đăng ký biến động..." (đất đai); đáp án đúng 1.000894 có nguồn ghi "Miễn lệ phí".
- `quantitative-01` "Đăng ký tạm trú mất bao nhiêu tiền?" -> `dang ky tam tru mat tien` -> top-1 = đất đai/hải quan, đáp án 1.004194 không vào top-3.
- `rag_basic-03` "Xóa đăng ký thường trú gồm những bước nào?" và `rag_basic-11` "Thủ tục tách hộ gồm những bước nào?" -> kết quả RỖNG (AND toàn bộ "gom nhung buoc nao").
- `rag_basic-07` "Khai báo tạm vắng cần chuẩn bị những gì?" -> rỗng.
- `rag_basic-01` "Đăng ký khai tử cần giấy tờ gì?" -> top-1 = khai tử *có yếu tố nước ngoài* (1.001766), không phải bản chuẩn 1.000656 (overlap 0,71, không strong).
- `context_memory-01` "Còn lệ phí thì sao?" -> keyword `con sao`, rỗng: không có bộ nhớ hội thoại (đúng thiết kế baseline; cần Phase 6).
- `multi_intent-01` "Khai sinh cần giấy tờ gì, còn kết hôn thì mất bao nhiêu tiền?" -> 1 truy vấn trộn 2 ý, không task nào đúng.

Out-of-scope bị `is_strong` bắt nhầm (hiện ra như thủ tục thật):
- `out_of_scope-01` "Làm hộ chiếu mới ở đâu?" -> strong (0,75) vào "Hỗ trợ gạo cho các **hộ** gia đình..." (bỏ dấu: hộ ~ hỗ ~ hồ). Khớp lỗi PLAN đã nêu.
- `out_of_scope-20` "Thủ tục thành lập công ty TNHH một thành viên?" -> strong (0,86) "Khai thuế thu nhập doanh nghiệp..." (kho không có thủ tục thành lập công ty).
- `out_of_scope-21` "Đăng ký bảo hộ nhãn hiệu cho sản phẩm của tôi ở đâu?" -> strong (kết quả có overlap 0,8 là "Đăng ký biến động ... đất"; top-1 là "bán hàng miễn thuế").
- `out_of_scope-14` "Tối qua đội tuyển Việt Nam đá thế nào?" -> strong vào trợ cấp quân nhân/đất đai (khớp "việt nam", "đội").
- `out_of_scope-24` "Cấp Giấy phép thành lập Hiệp hội doanh nghiệp nước ngoài tại TP.HCM" -> strong 0,92 đúng chữ nhưng là thủ tục **cấp tỉnh** (`agency_levels='Tỉnh'`); `is_strong` không có khái niệm cấp xã/tỉnh.
- Chitchat `out_of_scope-30` "Xin chào, cảm ơn bạn nhiều nhé!" không được `is_chitchat` nhận (câu ghép chào + cảm ơn + "nhiều nhé"), rơi vào tra cứu.
- Biến thể gỡ field thêm: `out_of_scope-03` "Gia hạn hộ chiếu cần giấy tờ gì?" (strong 0,75 vào "Hỗ trợ gạo cho các hộ gia đình...", cùng lỗi hộ/hỗ như câu 01), `out_of_scope-18` thuế TNCN (ngành dọc, strong 0,78: đúng chữ nhưng phải xin lỗi vì ngành dọc).
- Các câu thuế/hải quan nguyên trạng "apologize" đúng chỉ vì overlap thấp, không vì phát hiện ngành dọc.

Điểm lệch khác:
- Chọn biến thể: `quantitative-05` "Đăng ký khai sinh lệ phí bao nhiêu?" (gỡ field) top-1 = "khai sinh kết hợp nhận cha mẹ con" thay vì bản chuẩn 1.001193. Có 24 câu "đúng trong top-3, sai top-1" (biến thể lưu động / có yếu tố nước ngoài / kết hợp xếp trước bản chuẩn); chưa có `default_variant`.
- Bỏ dấu va chạm: "khai tử" ~ "khai tư/từ", nên "đăng ký khai tử" (gỡ field) bị trộn với thủ tục thuế/hải quan (`rag_basic-01`: top-1 = "khai báo giá tạm tính" hải quan).

## 5. Kết luận cho Phase 2
1. Từ chỉ field PHẢI tách khỏi truy vấn trước khi FTS (chỉ gỡ bằng danh sách cứng thô đã nâng top-3 từ 18% lên 39%; vẫn chưa đủ).
2. Xếp lại có dấu + ưu tiên bản chuẩn/`default_variant`: 24 câu đúng-top-3-sai-top-1 là lỗi biến thể.
3. `is_strong` không dùng làm cổng out-of-scope: sai 17-23% ở OOS, và ~70% câu "strong" ở in-scope không đúng top-1.
4. Cần cờ cấp (`agency_levels`) và ngành dọc (Thuế/Hải quan) cho quyết định phạm vi.
5. Mục tiêu đề xuất: top-3 >= 90% in-scope, OOS loại >= 90%.

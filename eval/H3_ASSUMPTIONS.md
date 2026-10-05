# HOLDOUT-3: các đáp án là GIẢ ĐỊNH / không chắc

Bộ `cases_h3.jsonl` (88 câu, id `h3-*`, split `holdout3`). Soạn mù: không đọc code/kết quả hệ thống. proc_id và condition_index đã assert với `system3.db`.

## Quy tắc người dùng áp dụng
- Kho có thủ tục thì đáp án là trả lời theo kho. Vì vậy KHÔNG đưa thuế / hải quan vào out_of_scope (kho có 95 thủ tục thuế, 104 hải quan, một số ở cấp xã).
- clarify: >=3 thủ tục gần nhau mà câu không phân biệt => hỏi lại; 2 biến thể => bản mặc định + nút.

## Đáp án giả định (nên xem lại)
| id | Giả định |
|---|---|
| out_of_scope-01..03 | Chào / cảm ơn / hỏi danh tính: behavior=answer (đáp lịch sự, không tra thủ tục). Chưa có quy tắc chốt cho chitchat. |
| out_of_scope-04, 05 | Chèn lệnh: apologize/từ chối. Câu 05 đòi bịa "mọi thủ tục miễn phí": coi là injection. |
| out_of_scope-06..09 | Bóng đá, thời tiết, đầu tư vàng/bitcoin, đau bụng: apologize (không phải thủ tục). Riêng "đầu tư" và "y khoa" có thể hệ thống từ chối kiểu khác (cảnh báo), chấp nhận nếu không bịa. |
| out_of_scope-10 | Giờ mở cửa UBND: kho không có dữ liệu giờ làm việc => apologize. Nếu hệ thống có nguồn khác thì đáp án đổi. |
| out_of_scope-11 | "Công bố vùng nước neo đậu" chỉ có bản cấp Tỉnh (1.014825/1.014826) => province_level. Nếu hệ thống coi bản cấp tỉnh vẫn trả lời theo kho (quy tắc "kho có thì trả lời") thì câu này sai kỳ vọng. Rủi ro cao nhất nhóm OOS. |
| clarify_conditional-01..06 | Danh sách acceptable_proc_ids chỉ để kiểm "không chọn bừa"; hành vi đúng = clarify. Câu 03 (sổ đỏ) đất đai có nhiều bản theo tỉnh nên cực mơ hồ. |
| clarify_conditional-07 | Hỏi "giấy xác nhận khuyết tật" chung: coi là 2 biến thể (xác định 1.001699 / đổi-cấp lại 1.001653) => trả bản mặc định xác định + nút. Có thể bị coi là 3 biến thể nếu tính cả "xác định lại". |
| hallucination-01..04 | Chỉ kiểm theo TÊN thủ tục (absent). Kho có thể có mô tả/chi tiết nhắc tới (ví dụ BHTN) nhưng không có thủ tục riêng. |
| multi_intent-04 | Ý 2 (giấy chứng sinh) không có trong kho => xin lỗi riêng. |
| rag_basic-08, rule_condition-05, context_memory-06 | Đất đai có nhiều bản cùng tên theo tỉnh; chấp nhận mọi proc_id trùng TÊN (`same()`); riêng context_memory-06 chấp nhận cả 1.012812 và 1.013967 (tranh chấp đất cấp xã). Câu hỏi phí (fees) đất đai text_only. |
| quantitative-03/05/06 | Dữ liệu không có số phí (fees none / text_only không miễn) => đáp án đúng là nói cổng không công bố, không bịa số. `must_say_not_published` tính tự động từ DB. |
| ctx_cond_evidence-03 | Chọn 1.012537 (ốm đau, tai nạn, bị thương, chưa BHYT) chứ không phải 1.012538 (chết). |
| rule_compare-02 | Key "tổ dân phố" cho 6.006759 nằm trong tên "Thôn, tổ dân phố văn hóa". |

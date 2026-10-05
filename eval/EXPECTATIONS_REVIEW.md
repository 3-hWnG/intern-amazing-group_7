# Đáp án mong đợi cần người dùng duyệt (đợt 3 / Phase 8)

Các câu dưới đây có đáp án (nhất là `behavior`) là GIẢ ĐỊNH, không suy ra được từ DB. Mỗi mục: id, câu, đáp án đang ghi, lý do. Gạch "OK" hoặc sửa trong `build_cases.py` / `cases_new.py` rồi chạy lại `python build_cases.py`. Chưa sửa đáp án nào theo kết quả chạy.

## A. Nhóm clarify (expected.behavior = clarify; chỉ chấm hành vi, không chấm truy hồi)
| id | câu | đáp án đang ghi | lý do giả định |
|---|---|---|---|
| clarify_conditional-10 (DEV) | Cho tôi hỏi về hỗ trợ chi phí mai táng | clarify | có 2 thủ tục sát nhau (bảo trợ xã hội 1.001731 / hưu trí xã hội 1.014028); giả định hỏi lại tốt hơn đoán bản đầu |
| clarify_conditional-11 (DEV) | Tôi muốn xin trợ cấp hàng tháng | clarify | 1.001776 / 1.014027 / 2.001396 đều "trợ cấp"; giả định không đủ để chọn |
| clarify_conditional-12 (DEV) | Cho tôi hỏi về giám hộ | clarify | đăng ký / chấm dứt / giám sát giám hộ khác nội dung. Mâu thuẫn nhẹ: typo-15 "cong nhan ho ngheo the nao" (3 bản gần nhau) lại ghi là answer, chưa thống nhất tiêu chí "đủ mơ hồ" |
| clarify_conditional-13 (DEV) | Tôi muốn làm giấy tờ cho con | clarify | khai sinh / căn cước / khuyết tật... chưa biết việc gì |
| clarify_conditional-14 (DEV) | Xin cấp lại giấy | clarify | thiếu tên giấy |
| clarify_conditional-15 (DEV) | Tôi muốn đăng ký | clarify | thiếu đối tượng đăng ký |
| hold-clarify_conditional-03 | Người nhà vừa mất rồi, giờ tôi phải làm những thủ tục gì? | clarify | khai tử / mai táng / liên thông khai tử-xóa thường trú; có thể người dùng muốn trợ lý liệt kê luôn (multi-task) thay vì hỏi lại |
| hold-clarify_conditional-04 | làm lại giấy tờ bị mất | clarify | không nói giấy gì |
| hold-clarify_conditional-05 | cho hỏi về trợ cấp cho người già | clarify | 1.014027 hưu trí xã hội / 1.014589 hỗ trợ NCT 70-75 / 1.001776; có thể chấp nhận trả lời thủ tục phổ biến nhất kèm gợi ý |

Câu hỏi chung cho người duyệt: khi 2-3 thủ tục gần nhau, chọn "hỏi lại" hay "trả lời bản mặc định kèm danh sách dạng khác"? Hiện DEV chọn hỏi lại cho mai táng/trợ cấp/giám hộ nhưng trả lời cho hộ nghèo.

**Người dùng đã duyệt (2026-10-05):** giữ nguyên toàn bộ đáp án ở A, B, C, D. Quy tắc chốt: có từ 3 bản gần nhau mà câu hỏi không phân biệt được -> hỏi lại để xác định ý định, rồi chọn bản gần nhất. Hệ quả: typo-15 ("cong nhan ho ngheo the nao") đổi từ answer sang clarify (sẽ sửa trong `build_cases.py` sau khi Phase 10 xong). 2 bản gần nhau vẫn trả bản mặc định kèm nút "dạng khác".

## B. Nhóm chitchat (expected.behavior = answer, tasks rỗng)
| id | câu | lý do giả định |
|---|---|---|
| out_of_scope-29 (DEV) | Chào bạn, bạn là ai vậy? | giả định là xã giao => answer (không phải apologize) |
| out_of_scope-30 (DEV) | Xin chào, cảm ơn bạn nhiều nhé! | như trên |
| hold-out_of_scope-05 | alo ad oi | chào kiểu nhắn tin; giả định answer |
| hold-out_of_scope-06 | ok cảm ơn nha, hôm nay hỏi vậy thôi | kết thúc hội thoại; giả định answer (lời chào tạm biệt), không hỏi thêm |
Ngoài ra: các câu chèn lệnh (out_of_scope-27/28, hold-out_of_scope-02) giả định là apologize, không chitchat.

## C. Nhóm multi-intent > 3 ý và ý không có trong kho
| id | câu | đáp án đang ghi | lý do giả định |
|---|---|---|---|
| multi_intent-11 (DEV) | 4 ý khai sinh/kết hôn/khai tử/tạm trú | answer 3 ý đầu + nói rõ còn ý 4; chỉ chấm 3 task | giới hạn 3 task là quyết định thiết kế, không phải đặc tả; có thể muốn trả đủ 4 |
| hold-multi_intent-03 | 4 ý khai sinh/khai tử/kết hôn/tạm vắng | như trên | như trên (ý bị cắt là tạm vắng) |
| multi_intent-10 (DEV), hold-multi_intent-04 | 1 ý có trong kho + "sổ hộ khẩu giấy" | answer ý 1 + xin lỗi riêng ý 2 (`partial_apology`) | giả định hành vi tổng là answer thay vì apologize |

## D. Giả định khác phát sinh khi soạn bộ mới
- hold-rule_order-*, rule_order-*: danh sách đánh số do trợ lý hiển thị dùng đúng TÊN thủ tục trong DB; giả định hệ thống phải trả lời thủ tục được chỉ, không hỏi lại (behavior=answer).
- rule_negation: "không phải X" ở lượt đầu (chưa có thủ tục trước đó) giả định chọn thủ tục còn lại/bản mặc định; chấm: top-1 thuộc đáp án và KHÔNG chọn mục bị cấm.
- rule_compare: đáp án đúng khi câu trả lời nhắc đủ cụm khoá tên của cả hai thủ tục (tên có trong DB); không chấm chất lượng so sánh.
- hold-clarify_conditional-01/02 (nhà thuê trọ; khuyết tật nhẹ): ghi answer thủ tục chính; điều kiện "khuyết tật nhẹ" không có trong condition_index nên chỉ chấm truy hồi/hành vi.

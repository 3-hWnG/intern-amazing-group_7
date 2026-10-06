# Giả định bộ câu hỏi pseudo-real

- Đáp án gán từ DB system3.db (bản active); mọi proc_id đã assert tồn tại.
- `fields`: nhãn tự đặt (documents, fee, time, place, steps, conditions, province, period, case, beneficiary_type); với clarify là thông tin còn thiếu cần hỏi lại.
- Không có FORMAT_SAMPLE.md; dùng format theo yêu cầu.
- Mọi bản trùng tên theo tỉnh (vd 'Đắk Lắk - ...') bị loại khỏi danh sách chấp nhận, trừ pr-10 chỉ liệt kê bản toàn quốc.

## Câu đơn

- pr-01 | con em sinh tuần trước giờ làm giấy khai sinh cho bé thì cần mang theo gì ạ | answer ['1.001193'] | khai sinh thường, trường hợp phổ biến nhất
- pr-02 | dang ky tam tru het bao nhieu tien vay | answer ['1.004194'] | không dấu, hỏi phí
- pr-03 | mất giấy khai sinh của con rồi, làm lại sao | clarify ['1.004884', '2.000635'] | mơ hồ: đăng ký lại khai sinh vs cấp bản sao trích lục
- pr-04 | Bố em mất hôm qua ở quê, cần đi đâu làm giấy báo tử, mất bao lâu? | answer ['1.000656', '2.002913'] | kể hoàn cảnh; khai tử hoặc liên thông khai tử
- pr-05 | chung thuc di chuc phi bn ạ | answer ['2.001019'] | viết tắt, thiếu dấu
- pr-06 | photo công chứng cmnd ở ubnd xã đc ko, mấy bản | answer ['2.000815'] | nói 'công chứng' nhưng là chứng thực bản sao từ bản chính
- pr-07 | xin giấy xác nhận độc thân để đk kết hôn nộp ở đâu | answer ['1.004873'] | giấy xác nhận tình trạng hôn nhân
- pr-08 | thủ tục mở hộ kinh doanh bán tạp hóa tại nhà cần giấy tờ gì | answer ['1.001612'] | đăng ký thành lập hộ kinh doanh
- pr-09 | bà ngoại em 80 tuổi muốn nhận trợ cấp hàng tháng thì làm sao | answer ['1.014027', '1.001776'] | trợ cấp hưu trí xã hội (>=75t); chấp nhận bản trợ cấp xã hội hàng tháng
- pr-10 | cho hỏi cấp sổ đỏ lần đầu cho hộ gia đình cần những giấy gì | clarify 11 ids | nhiều bản trùng tên theo tỉnh, không phân biệt được từ câu hỏi
- pr-11 | con cháu bị khuyết tật nặng làm giấy xác nhận khuyết tật ở đâu, mấy ngày có | answer ['1.001699'] | xác định mức độ khuyết tật
- pr-12 | con mình sắp vào lớp 6, tuyển sinh thcs nộp hồ sơ ở đâu | answer ['3.000182'] | giáo dục
- pr-13 | nha toi o xa nay nhung ho khau o xa khac, muon chuyen ve day thi lam sao | answer ['1.004222'] | không dấu, đăng ký thường trú
- pr-14 | thẻ bhyt của con bị sai ngày sinh sửa ở đâu | answer ['1.002759'] | y tế/BHYT; thủ tục có cấp xã nhưng cơ quan thực hiện BHXH huyện
- pr-15 | nhà em thu nhập thấp muốn được công nhận hộ nghèo thì sao | clarify ['1.011606', '1.011607', '1.116214', '1.116215'] | nhiều bản (định kỳ/thường xuyên/trong năm; chuẩn cũ/mới)
- pr-16 | xin giay phep xay nha 2 tang tren dat nha o nong thon | answer ['1.013225', '1.009122'] | giấy phép xây dựng nhà ở riêng lẻ
- pr-17 | me em mat, lo mai tang phi dc ho tro ko | clarify ['1.001731', '1.014028', '3.000731', '2.002307', '1.010456'] | nhiều chế độ mai táng phí, thiếu đối tượng
- pr-18 | cho con 14 tuổi làm thẻ căn cước thì đi đâu | answer ['1.116410'] | cấp thẻ căn cước
- pr-19 | cháu trai 17 tuổi đăng ký nghĩa vụ quân sự lần đầu nộp ở đâu | answer ['1.013133'] | NVQS
- pr-20 | làm thủ tục nhận con nuôi trong nước tốn bao nhiêu | answer ['2.001263'] | nuôi con nuôi
- pr-21 | tranh chấp ranh giới đất với nhà hàng xóm, xã có hòa giải ko | answer ['1.012812', '1.013967'] | hòa giải tranh chấp đất đai
- pr-22 | nhà văn hóa thôn tổ chức lễ hội thì thông báo trước bao nhiêu ngày | answer ['1.003622', '1.013791'] | lễ hội cấp xã
- pr-23 | cho mình hỏi làm khai tử với xóa thường trú cho ông nội thì mất bao lâu, có tốn phí ko | answer ['1.000656', '1.003197', '2.002913'] | hai việc một tin nhắn
- pr-24 | gia hạn tạm trú phí bao nhiêu, với khách ở nhà vài hôm thì báo lưu trú sao | answer ['1.002755', '2.001159'] | hai việc một tin nhắn
- pr-25 | xin cấp hộ chiếu mới cho con thì nộp hồ sơ ở xã đc ko | apologize [] | cấp hộ chiếu không có trong kho (chỉ có trình báo mất hộ chiếu)
- pr-26 | em muốn ly hôn đơn phương, nộp đơn ở đâu, tốn bao nhiêu | apologize [] | ly hôn là việc của Tòa án, ngoài thẩm quyền xã
- pr-27 | thi bằng lái xe máy a1 đăng ký ở đâu vậy cán bộ | apologize [] | sát hạch GPLX không có trong kho/ngoài thẩm quyền xã
- pr-28 | cho em xin phiếu lý lịch tư pháp số 2 đi xin visa | apologize [] | LLTP thuộc Sở Tư pháp, kho không có bản phù hợp
- pr-29 | hôm nay giá vàng bao nhiêu vậy ad | apologize [] | không phải thủ tục
- pr-30 | thành lập công ty tnhh vốn 2 tỷ phải làm sao | apologize [] | đăng ký doanh nghiệp cấp tỉnh, không có trong kho

## Hội thoại
- prc-02 t1: 'chứng thực chữ ký' coi là 2.000884 (mặc định, không phải chữ ký người dịch).
- prc-03: t1 clarify vì chưa rõ chia di sản/từ chối/đăng ký biến động; t2 'không nhận' => văn bản từ chối nhận di sản 2.001016.
- prc-04 t2 'cái thứ hai' giả định hệ thống liệt kê thứ tự [đăng ký lại khai sinh, cấp bản sao]; nếu thứ tự khác, câu đã kèm 'bản sao' để vẫn xác định được.
- prc-01 t3 'gia hạn' hiểu là gia hạn tạm trú (ngữ cảnh).

## Giả định chung
- pr-09: 80 tuổi => trợ cấp hưu trí xã hội 1.014027 (nhận thêm 1.001776).
- pr-14: 1.002759 có cấp xã trong agency_levels dù cơ quan thực hiện là BHXH huyện.
- pr-25..30 apologize: không có thủ tục tương ứng trong DB hoặc thuộc tỉnh/tòa án; pr-29 không phải thủ tục. DB có 'Đăng ký xe', 'căn cước' nên không dùng chúng làm câu ngoài kho.
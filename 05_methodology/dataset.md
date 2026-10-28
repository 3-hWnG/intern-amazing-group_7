# Dataset (khuôn bước 9)

## 1. Dữ liệu thủ tục (nguồn tri thức)

- **Nguồn:** Cổng Dịch vụ công Quốc gia, thu một lần ngày 13/10/2026.
- **Quy mô:** 1.517 thủ tục, kể cả các bản riêng theo tỉnh của 34 tỉnh.
- **Phạm vi:** 542 thủ tục cấp xã không phân theo tỉnh. Thủ tục do cấp tỉnh hay bộ giải quyết nằm ngoài phạm vi.
- **Mỗi bản ghi gồm:** tên, lĩnh vực, cơ quan thực hiện, giấy tờ, lệ phí, thời hạn, các bước, căn cứ pháp lý.
- **Cách thu:**
  - dùng các JSON endpoint công khai, không cần đăng nhập, mà chính trang web của cổng dùng;
  - tốc độ 2 yêu cầu/giây, chạy một luồng;
  - cổng không có API chính thức.
- Bản ghi không chứa dữ liệu cá nhân.

## 2. Câu hỏi thật của người dân

- **Nguồn:** hai bộ dữ liệu công khai trên Hugging Face.
  - `hieunguyen1053/dichvucong_faqs`: hỏi đáp của Cổng DVC tỉnh Bình Định.
  - `doanhieung/vn-mps-public-service-qa`: hỏi đáp của Cổng DVC Bộ Công an.
  - Cả hai bộ **không ghi giấy phép** (kiểm ngày 25/10/2026). Vì vậy repo công khai không chép lại văn bản câu hỏi (D9).
- **Xử lý trước khi gán nhãn:**
  - che dữ liệu cá nhân (tên, số điện thoại, số giấy tờ, email);
  - bỏ câu trùng, câu dưới 4 chữ, câu chỉ có lời chào;
  - bỏ 266 câu đã dùng trước đó để thiết kế luật hỏi lại.
  - Còn lại kho 1.490 câu.
- **Hai tầng mẫu, hạt giống cố định:**
  - `random`: theo đúng phân bố thật;
  - `topical`: câu có từ khoá của các lĩnh vực cấp xã, để có thêm câu trả lời được. Danh sách từ khoá viết trước khi xem bất kỳ đầu ra nào của hệ thống.

| Bộ | Vai trò | Số câu | Nhãn |
|---|---|---|---|
| real_v1 | Dev: viết luật, chọn ngưỡng | 282 (120 random + 180 topical, đã bỏ câu không phải câu hỏi) | 55 answer, 7 clarify, 220 refuse |
| real_v2 | Test 1, khoá trước khi sửa code (`7e78438`) | Rút 348 câu (120 random + 228 topical); bỏ 35 skip, còn 313 (102 random + 211 topical). 11 câu gần trùng với dev | 59 answer, 6 clarify, 248 refuse |
| real_v4 | Test 2: 814 câu còn lại của kho (đã bỏ 25 câu gần trùng), chỉ tầng random, đã xáo; thứ tự khoá `5499d0f`. Gán 400 câu đầu (Gemini 4 Argon đề xuất, trưởng nhóm duyệt), nhãn khoá `a79ec5f` | Bỏ 37 skip, còn 363 | 21 answer, 7 clarify, 335 refuse |

Từ vòng cải thiện thứ hai, real_v1 và real_v2 gộp lại làm dev (595 câu, `eval/hard/dev595/`). Số "sau cải thiện" chỉ được báo trên real_v4 (D12).

## 3. Nhãn và độ đồng thuận

- **Lượt A:** AI assistant gán nhãn theo hướng dẫn viết sẵn. Đây cũng là bên viết luật.
- **Lượt B:** lấy ngẫu nhiên 100 câu test. Gemini 4 Argon (mức "High") đề xuất nhãn, rồi trưởng nhóm kiểm từng câu mà không xem nhãn A.
- **Kết quả:**
  - Lượt B đánh dấu 9 câu kiến nghị là "không phải câu hỏi".
  - Trên 91 câu còn lại, hai lượt khớp 79 câu (86,8%).
  - κ = 0,685 (bootstrap 95%: 0,55–0,82), tức mức "substantial".
  - Chấm lại bằng nhãn B thì kết luận không đổi (`eval/real_v2/relabel/`).
- **Hướng dẫn gán nhãn của real_v4:** dùng hướng dẫn của dev, thêm hai điều làm rõ. (1) Kiến nghị và phản ánh thì từ chối, không đánh skip. Điều này có vì lượt B đã để riêng 9 câu kiến nghị. (2) Hai thủ tục gần tương đương tính là một câu answer. Nhãn skip chỉ dành cho câu cụt hoặc không hiểu được (`eval/real_v4/make_label_sheet.py`).
- **Không được viết** "two human annotators" (D11).

## 4. Bộ câu nhóm tự viết (để so sánh)

- Phần blind của bộ hồi quy: 518 câu, nhóm viết qua nhiều đợt.
- 102 câu trong số đó viết theo lối người dân.
- Nhãn: 384 answer (381 câu có thủ tục còn trong dữ liệu hiện tại), 76 clarify, 58 refuse.
- Chỉ 11% câu nằm ngoài phạm vi.

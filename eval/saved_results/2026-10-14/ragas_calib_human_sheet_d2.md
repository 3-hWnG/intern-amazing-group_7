# Phiếu chấm tay: 15 ca giám khảo và LLM bất đồng (Đợt 2, chế độ ít chấm tay)

Việc cần làm (~30 phút): với mỗi ca, điền hai ô. Không cần xem điểm của máy; phiếu cố ý không hiển thị.

- **faithful** (1 hoặc 0): 1 nếu MỌI thông tin về nội dung thủ tục trong câu trả lời (bước, giấy tờ, phí, thời hạn, nơi nộp, căn cứ) đều có trong NGỮ CẢNH. Bỏ qua tên thủ tục, đường link, số quyết định công bố ở cuối. 0 nếu có ý nào ngữ cảnh không nói.
- **rel** (0, 1 hoặc 2): 2 = trả lời đúng và đủ điều được hỏi; 1 = đúng thủ tục nhưng chỉ trả lời một phần (vd so sánh A với B mà chỉ nói về A); 0 = lạc đề hoặc sai thủ tục.

Điền xong, lưu thành `eval/results/ragas_calib_human_d2.json` dạng `{"id": {"faithful": 1, "rel": 2}, ...}`, rồi chạy:
`python eval/ragas_calib.py kappa --name d2 --ratings eval/results/ragas_calib_llm_d2.json --human eval/results/ragas_calib_human_d2.json`

Ngữ cảnh bị cắt ở 1.500 ký tự cho dễ đọc; nếu thấy câu trả lời nhắc thứ nằm sau chỗ cắt, mở `ragas_calib_d2.json` xem đủ (3.500 ký tự).

## 1. `h4-001`

**Câu hỏi:** giay to xin cap lai giay xac nhan khuyet tat can nhung gi

**Câu trả lời của hệ thống:**

```
Đổi, cấp lại Giấy xác nhận khuyết tật
Giấy tờ cần chuẩn bị:
- Đơn đề nghị cấp đổi, cấp lại Giấy xác nhận khuyết tật theo Mẫu số 01 ban hành kèm theo Thông tư số 01/2019/TT-BLĐTBXH (được sửa đổi, bổ sung tại Thông tư số 08/2023/TT-BLĐTBXH) (bản chính 1, bản sao 0)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.001653
Quyết định công bố 970/QĐ-BYT (2025-03-21, Bộ Y tế) 
```

**Ngữ cảnh:**

```
- Đơn đề nghị cấp đổi, cấp lại Giấy xác nhận khuyết tật theo Mẫu số 01 ban hành kèm theo Thông tư số 01/2019/TT-BLĐTBXH (được sửa đổi, bổ sung tại Thông tư số 08/2023/TT-BLĐTBXH) (bản chính 1, bản sao 0)
```

faithful: ___    rel: ___

---

## 2. `h4c-05.3`

**Câu hỏi:** còn khi chuyển đi nơi khác thì xóa tạm trú ra sao

**Câu trả lời của hệ thống:**

```
Xóa đăng ký tạm trú
Giấy tờ cần chuẩn bị:
- Thông tin chứng minh thuộc trường hợp xóa đăng ký tạm trú của công dân trong Cơ sở dữ liệu quốc gia, cơ sở dữ liệu chuyên ngành và cơ sở dữ liệu khác được kết nối, chia sẻ với cơ quan đăng ký cư trú. Trường hợp thông tin chưa được kết nối, chia sẻ thì công dân xuất trình giấy tờ, tài liệu chứng minh thuộc một trong các trường hợp xóa đăng ký tạm trú quy định tại Điều 29 Luật Cư trú. (bản chính 1, bản sao 0)
- Tờ khai thay đổi thông tin cư trú (Mẫu CT01 ban hành kèm theo Thông tư số 53/2025/TT-BCA). (bản chính 1, bản sao 0)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.010028
Quyết định công bố 1523/QĐ-BCA-C06 (2026-03-25, Bộ Công an) 
```

**Ngữ cảnh:**

```
- Thông tin chứng minh thuộc trường hợp xóa đăng ký tạm trú của công dân trong Cơ sở dữ liệu quốc gia, cơ sở dữ liệu chuyên ngành và cơ sở dữ liệu khác được kết nối, chia sẻ với cơ quan đăng ký cư trú. Trường hợp thông tin chưa được kết nối, chia sẻ thì công dân xuất trình giấy tờ, tài liệu chứng minh thuộc một trong các trường hợp xóa đăng ký tạm trú quy định tại Điều 29 Luật Cư trú. (bản chính 1, bản sao 0)
- Tờ khai thay đổi thông tin cư trú (Mẫu CT01 ban hành kèm theo Thông tư số 53/2025/TT-BCA). (bản chính 1, bản sao 0)
```

faithful: ___    rel: ___

---

## 3. `h5-057`

**Câu hỏi:** sinh con ma cha me chua dang ky ket hon thi khai sinh kieu gi

**Câu trả lời của hệ thống:**

```
Thủ tục đăng ký khai sinh
Giấy tờ cần chuẩn bị:
* Giấy tờ phải nộp:
- Trường hợp trẻ em bị bỏ rơi thì phải có biên bản về việc trẻ bị bỏ rơi do cơ quan có thẩm quyền lập. (bản chính 1, bản sao 0)
- Văn bản ủy quyền (được chứng thực) theo quy định của pháp luật trong trường hợp ủy quyền thực hiện việc đăng ký khai sinh. Trường hợp người được ủy quyền là ông, bà, cha, mẹ, con, vợ, chồng, anh, chị, em ruột của người ủy quyền thì văn bản ủy quyền không phải chứng thực. (bản chính 1, bản sao 0)
- Trường hợp người yêu cầu đã nộp bản điện tử Giấy chứng sinh hoặc cơ quan đăng ký hộ tịch đã khai thác được dữ liệu điện tử có ký số của Giấy chứng sinh thì không phải nộp bản giấy.
- Trường hợp khai sinh cho trẻ em sinh ra do mang thai hộ phải có văn bản xác nhận của cơ sở y tế đã thực hiện kỹ thuật hỗ trợ sinh sản cho việc mang thai hộ. (bản chính 1, bản sao 0)
- Giấy chứng sinh; trường hợp không có Giấy chứng sinh thì nộp văn bản của người làm chứng xác nhận về việc sinh; nếu không có người làm chứng thì phải có giấy cam đoan về việc sinh. (bản chính 1, bản sao 0)
* Giấy tờ phải xuất trình:
… (còn nữa, bấm «Tạo bảng full» để xem đủ)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc
```

**Ngữ cảnh:**

```
* Giấy tờ phải nộp:
- Trường hợp trẻ em bị bỏ rơi thì phải có biên bản về việc trẻ bị bỏ rơi do cơ quan có thẩm quyền lập. (bản chính 1, bản sao 0)
- Văn bản ủy quyền (được chứng thực) theo quy định của pháp luật trong trường hợp ủy quyền thực hiện việc đăng ký khai sinh. Trường hợp người được ủy quyền là ông, bà, cha, mẹ, con, vợ, chồng, anh, chị, em ruột của người ủy quyền thì văn bản ủy quyền không phải chứng thực. (bản chính 1, bản sao 0)
- Trường hợp người yêu cầu đã nộp bản điện tử Giấy chứng sinh hoặc cơ quan đăng ký hộ tịch đã khai thác được dữ liệu điện tử có ký số của Giấy chứng sinh thì không phải nộp bản giấy.
- Trường hợp khai sinh cho trẻ em sinh ra do mang thai hộ phải có văn bản xác nhận của cơ sở y tế đã thực hiện kỹ thuật hỗ trợ sinh sản cho việc mang thai hộ. (bản chính 1, bản sao 0)
- Giấy chứng sinh; trường hợp không có Giấy chứng sinh thì nộp văn bản của người làm chứng xác nhận về việc sinh; nếu không có người làm chứng thì phải có giấy cam đoan về việc sinh. (bản chính 1, bản sao 0)
---
* Giấy tờ phải xuất trình:
- Trường hợp không khai thác được thông tin hoặc thông tin khai thác được không đầy đủ, không chính xác thì cơ quan đăng ký hộ tịch yêu cầu người đi đăng ký hộ tịch xuất trình bản chính giấy tờ để chứng minh, đồng thời đề nghị người đi đăng ký hộ tịch cập nhật, điều chỉnh thông tin trong các cơ sở dữ liệu theo quy định của pháp luật.
- Giấy tờ có giá trị chứng minh thông tin về cư trú trong trường hợp cơ quan đăng ký hộ tịch không thể khai thá
```

faithful: ___    rel: ___

---

## 4. `h6-026`

**Câu hỏi:** muon lap cau lac bo the thao o thon thi can nhung gi

**Câu trả lời của hệ thống:**

```
Thủ tục công nhận câu lạc bộ thể dục thể thao cơ sở
Giấy tờ cần chuẩn bị:
- Tờ trình đề nghị công nhận câu lạc bộ thể dục thể thao cơ sở (theo mẫu số 01 tại Phụ lục kèm theo Thông tư số 16/2025/TT-BVHTTDL ngày 01/12/2025) (bản chính 1, bản sao 0)
- Quy chế hoạt động của câu lạc bộ thể dục thể thao cơ sở (theo mẫu số 02 tại Phụ lục kèm theo Thông tư số 16/2025/TT-BVHTTDL ngày 01/12/2025) (bản chính 1, bản sao 0)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/2.000794
Quyết định công bố 109/QĐ-BVHTTDL (2026-01-19, Bộ Văn hóa, Thể thao và Du lịch) 
```

**Ngữ cảnh:**

```
- Tờ trình đề nghị công nhận câu lạc bộ thể dục thể thao cơ sở (theo mẫu số 01 tại Phụ lục kèm theo Thông tư số 16/2025/TT-BVHTTDL ngày 01/12/2025) (bản chính 1, bản sao 0)
- Quy chế hoạt động của câu lạc bộ thể dục thể thao cơ sở (theo mẫu số 02 tại Phụ lục kèm theo Thông tư số 16/2025/TT-BVHTTDL ngày 01/12/2025) (bản chính 1, bản sao 0)
```

faithful: ___    rel: ___

---

## 5. `h6-057`

**Câu hỏi:** dang ky thuong tru vao nha thue nha muon nha o nho can giay to gi

**Câu trả lời của hệ thống:**

```
Xác nhận về điều kiện diện tích bình quân nhà ở để đăng ký thường trú vào chỗ ở do thuê, mượn, ở nhờ; nhà ở, đất ở không có tranh chấp quyền sở hữu nhà ở, quyền sử dụng đất ở, không thuộc địa điểm không được đăng ký thường trú mới
Giấy tờ cần chuẩn bị:
- Tờ khai xác nhận tình trạng chỗ ở hợp pháp, diện tích nhà ở tối thiểu để đăng ký thường trú, đăng ký tạm trú (Mẫu số 02 ban hành kèm theo Nghị định số 154/2024/NĐ-CP). (bản chính 1, bản sao 0)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.013314
Quyết định công bố 1523/QĐ-BCA-C06 (2026-03-25, Bộ Công an) 
```

**Ngữ cảnh:**

```
- Tờ khai xác nhận tình trạng chỗ ở hợp pháp, diện tích nhà ở tối thiểu để đăng ký thường trú, đăng ký tạm trú (Mẫu số 02 ban hành kèm theo Nghị định số 154/2024/NĐ-CP). (bản chính 1, bản sao 0)
```

faithful: ___    rel: ___

---

## 6. `own-p07`

**Câu hỏi:** Thủ tục đăng ký hộ kinh doanh so với thông báo tạm ngừng kinh doanh hộ kinh doanh khác nhau chỗ nào?

**Câu trả lời của hệ thống:**

```
Đăng ký thành lập hộ kinh doanh
Mô tả:
- Chủ hộ kinh doanh hoặc người được ủy quyền thực hiện thủ tục đăng ký hộ kinh doanh gửi hồ sơ đăng ký thành lập hộ kinh doanh đến Cơ quan đăng ký kinh doanh cấp xã. - Sau khi tiếp nhận hồ sơ đăng ký hộ kinh doanh, Cơ quan đăng ký kinh doanh cấp xã trao giấy tiếp nhận hồ sơ và hẹn trả kết quả, kiểm tra điều kiện cấp Giấy chứng nhận đăng ký hộ kinh doanh theo quy định tại khoản 2 Điều 85 Nghị định số 168/2025/NĐ-CP. Trường hợp hồ sơ đủ điều kiện cấp, Cơ quan đăng ký kinh doanh cấp xã cấp Giấy chứng nhận đăng ký hộ kinh doanh và gửi thông báo về Cơ quan thuế quản lý trực tiếp hộ kinh doanh cho hộ kinh doanh trong thời hạn 03 ngày làm việc kể từ ngày nhận hồ sơ. Trường hợp hồ sơ không đủ điều kiện cấp, Cơ quan đăng ký kinh doanh cấp xã thông báo bằng văn bản cho người nộp hồ sơ trong thời hạn 03 ngày làm việc kể từ ngày nhận hồ sơ. Thông báo phải nêu rõ lý do và các yêu cầu sửa đổi, bổ sung hồ sơ.
… (còn nữa, bấm «Tạo bảng full» để xem đủ)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.001612
Quyết định công bố 1995/QĐ-BTC (2026-07-23, Bộ Tài chính) 

Thông báo tạm ngừng kinh doanh/ tiếp tục kinh doanh trở lại đối với t
```

**Ngữ cảnh:**

```
- Chủ hộ kinh doanh hoặc người được ủy quyền thực hiện thủ tục đăng ký hộ kinh doanh gửi hồ sơ đăng ký thành lập hộ kinh doanh đến Cơ quan đăng ký kinh doanh cấp xã. - Sau khi tiếp nhận hồ sơ đăng ký hộ kinh doanh, Cơ quan đăng ký kinh doanh cấp xã trao giấy tiếp nhận hồ sơ và hẹn trả kết quả, kiểm tra điều kiện cấp Giấy chứng nhận đăng ký hộ kinh doanh theo quy định tại khoản 2 Điều 85 Nghị định số 168/2025/NĐ-CP. Trường hợp hồ sơ đủ điều kiện cấp, Cơ quan đăng ký kinh doanh cấp xã cấp Giấy chứng nhận đăng ký hộ kinh doanh và gửi thông báo về Cơ quan thuế quản lý trực tiếp hộ kinh doanh cho hộ kinh doanh trong thời hạn 03 ngày làm việc kể từ ngày nhận hồ sơ. Trường hợp hồ sơ không đủ điều kiện cấp, Cơ quan đăng ký kinh doanh cấp xã thông báo bằng văn bản cho người nộp hồ sơ trong thời hạn 03 ngày làm việc kể từ ngày nhận hồ sơ. Thông báo phải nêu rõ lý do và các yêu cầu sửa đổi, bổ sung hồ sơ.

Người nộp hồ sơ đăng nhập Cổng dịch vụ công quốc gia hoặc Ứng dụng định danh quốc gia bằng tài khoản định danh điện tử để truy cập Hệ thống thông tin về đăng ký hộ kinh doanh. Người nộp hồ sơ thực hiện thủ tục đăng ký hộ kinh doanh theo quy trình trên Hệ thống thông tin về đăng ký hộ kinh doanh như sau: - Trường hợp người nộp hồ sơ là người có thẩm quyền ký văn bản đề nghị đăng ký hộ kinh doanh Người nộp hồ sơ kê khai thông tin trên Hệ thống thông tin về đăng ký hộ kinh doanh. Đối với các giấy đề nghị hoặc thông báo có nội dung được kê khai trên Hệ thống thông tin về đăng ký hộ kinh d
```

faithful: ___    rel: ___

---

## 7. `own-p09`

**Câu hỏi:** So sánh đăng ký khai sinh với đăng ký khai sinh lưu động.

**Câu trả lời của hệ thống:**

```
Thủ tục đăng ký khai sinh
Mô tả:
- Nếu lựa chọn hình thức nộp hồ sơ trực tiếp, người yêu cầu đăng ký khai sinh nộp hồ sơ đăng ký khai tâm Phục vụ hành chính công có thẩm quyền; nộp lệ phí nếu thuộc trường hợp phải nộp lệ phí đăng ký khai sinh; nộp phí cấp bản sao Giấy khai sinh nếu có yêu cầu cấp bản sao Giấy khai sinh. - Nếu lựa chọn hình thức nộp hồ sơ trực tuyến, người yêu cầu đăng ký khai sinh truy cập Cổng dịch vụ công quốc gia hoặc Ứng dụng định danh quốc gia. Người yêu cầu đăng ký khai sinh trực tuyến cung cấp thông tin theo mẫu hộ tịch điện tử tương tác đăng ký khai sinh, đính kèm bản chụp hoặc bản sao điện tử các giấy tờ, tài liệu theo quy định; nộp phí, lệ phí thông qua chức năng thanh toán trực tuyến hoặc bằng cách thức khác theo quy định pháp luật, hoàn tất việc sinh tại Trung nộp hồ sơ. - Cán bộ tiếp nhận hồ sơ tại Trung tâm Phục vụ hành chính công có trách nhiệm kiểm tra tính chính xác, đầy đủ, thống nhất, hợp lệ của hồ sơ. (i) Trường hợp hồ sơ đầy đủ, hợp lệ thì tiếp nhận hồ sơ; nếu tiếp nhận hồ sơ sau 15 giờ thì có Phiếu hẹn, trả kết quả cho người yêu cầu trong ngày làm việc tiếp theo (nếu
… (còn nữa, bấm «Tạo bảng full» để xem đủ)
Cổng Dịch vụ công Quốc gia ht
```

**Ngữ cảnh:**

```
- Nếu lựa chọn hình thức nộp hồ sơ trực tiếp, người yêu cầu đăng ký khai sinh nộp hồ sơ đăng ký khai tâm Phục vụ hành chính công có thẩm quyền; nộp lệ phí nếu thuộc trường hợp phải nộp lệ phí đăng ký khai sinh; nộp phí cấp bản sao Giấy khai sinh nếu có yêu cầu cấp bản sao Giấy khai sinh. - Nếu lựa chọn hình thức nộp hồ sơ trực tuyến, người yêu cầu đăng ký khai sinh truy cập Cổng dịch vụ công quốc gia hoặc Ứng dụng định danh quốc gia. Người yêu cầu đăng ký khai sinh trực tuyến cung cấp thông tin theo mẫu hộ tịch điện tử tương tác đăng ký khai sinh, đính kèm bản chụp hoặc bản sao điện tử các giấy tờ, tài liệu theo quy định; nộp phí, lệ phí thông qua chức năng thanh toán trực tuyến hoặc bằng cách thức khác theo quy định pháp luật, hoàn tất việc sinh tại Trung nộp hồ sơ. - Cán bộ tiếp nhận hồ sơ tại Trung tâm Phục vụ hành chính công có trách nhiệm kiểm tra tính chính xác, đầy đủ, thống nhất, hợp lệ của hồ sơ. (i) Trường hợp hồ sơ đầy đủ, hợp lệ thì tiếp nhận hồ sơ; nếu tiếp nhận hồ sơ sau 15 giờ thì có Phiếu hẹn, trả kết quả cho người yêu cầu trong ngày làm việc tiếp theo (nếu người yêu cầu nộp hồ sơ trực tiếp) hoặc gửi ngay Phiếu hẹn, trả kết quả qua thư điện tử hoặc gửi tin nhắn hẹn trả kết quả qua điện thoại di động cho người yêu cầu (nếu người yêu cầu nộp hồ sơ trực tuyến); chuyển hồ sơ để công chức tư pháp - hộ tịch xử lý; trường hợp tiếp nhận hồ sơ tại Trung tâm Phục vụ hành chính công cấp tỉnh, cán bộ tiếp nhận hồ sơ chuyển hồ sơ đến Ủy ban nhân dân cấp xã có thẩm quy
```

faithful: ___    rel: ___

---

## 8. `p18-p18_B_single-12`

**Câu hỏi:** Tôi đang ở nhờ nhà bạn, gia hạn tạm trú thì phí bao nhiêu?

**Câu trả lời của hệ thống:**

```
Gia hạn tạm trú
Lệ phí:
- 5.000 đồng — - Gia hạn tạm trú (cá nhân, hộ gia đình): + Trường hợp công dân nộp hồ sơ qua cổng dịch vụ công trực tuyến thu 7.000 đồng/lần đăng ký. (Trực tuyến)
- 7.000 đồng (Trực tuyến)
- 10.000 đồng — - Gia hạn tạm trú theo danh sách: + Trường hợp công dân nộp hồ sơ trực tiếp thu 10.000 đồng/người/lần đăng ký; (Trực tiếp)
- 15.000 đồng (Trực tiếp)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.002755
Quyết định công bố 5548/QĐ-BCA-C06 (2021-07-05, Bộ Công an) 
```

**Ngữ cảnh:**

```
FEE - 5.000 đồng - - Gia hạn tạm trú (cá nhân, hộ gia đình): + Trường hợp công dân nộp hồ sơ qua cổng dịch vụ công trực tuyến thu 7.000 đồng/lần đăng ký. - Trực tuyến
FEE - 7.000 đồng - Trực tuyến
FEE - 10.000 đồng - - Gia hạn tạm trú theo danh sách: + Trường hợp công dân nộp hồ sơ trực tiếp thu 10.000 đồng/người/lần đăng ký; - Trực tiếp
FEE - 15.000 đồng - Trực tiếp
```

faithful: ___    rel: ___

---

## 9. `p18-p18_F_multi-08`

**Câu hỏi:** nhầm rồi, ý mình là thường trú

**Câu trả lời của hệ thống:**

```
Đăng ký thường trú
Giấy tờ cần chuẩn bị:
Đăng ký thường trú vào chỗ ở hợp pháp thuộc quyền sở hữu của mình
- Văn bản xác nhận của Ủy ban nhân dân cấp xã về địa điểm phương tiện đăng ký đậu, đỗ thường xuyên trong trường hợp phương tiện không phải đăng ký hoặc nơi đăng ký phương tiện không trùng với nơi thường xuyên đậu, đỗ (nội dung xác nhận tại mục 1 của Ủy ban nhân dân cấp xã tại Tờ khai đề nghị xác nhận nơi thường xuyên đậu, đỗ; sử dụng phương tiện vào mục đích để ở theo Mẫu số 01 ban hành kèm theo Nghị định số 154/2024/NĐ-CP). (bản chính 1, bản sao 0)
- Giấy chứng nhận đăng ký phương tiện và giấy chứng nhận an toàn kỹ thuật và bảo vệ môi trường của phương tiện hoặc văn bản xác nhận của Ủy ban nhân dân cấp xã về việc sử dụng phương tiện đó vào mục đích để ở đối với phương tiện không thuộc đối tượng phải đăng ký, đăng kiểm (nội dung xác nhận tại mục 2 của Ủy ban nhân dân cấp xã tại Tờ khai đề nghị xác nhận nơi thường xuyên đậu, đỗ; sử dụng phương tiện vào mục đích để ở theo Mẫu số 01 ban hành kèm theo Nghị định số 154/2024/NĐ-CP). (bản chính 1, bản sao 0)
… (còn nữa, bấm «Tạo bảng full» để xem đủ)
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.004222
Quy
```

**Ngữ cảnh:**

```
Đăng ký thường trú vào chỗ ở hợp pháp thuộc quyền sở hữu của mình
- Văn bản xác nhận của Ủy ban nhân dân cấp xã về địa điểm phương tiện đăng ký đậu, đỗ thường xuyên trong trường hợp phương tiện không phải đăng ký hoặc nơi đăng ký phương tiện không trùng với nơi thường xuyên đậu, đỗ (nội dung xác nhận tại mục 1 của Ủy ban nhân dân cấp xã tại Tờ khai đề nghị xác nhận nơi thường xuyên đậu, đỗ; sử dụng phương tiện vào mục đích để ở theo Mẫu số 01 ban hành kèm theo Nghị định số 154/2024/NĐ-CP). (bản chính 1, bản sao 0)
- Giấy chứng nhận đăng ký phương tiện và giấy chứng nhận an toàn kỹ thuật và bảo vệ môi trường của phương tiện hoặc văn bản xác nhận của Ủy ban nhân dân cấp xã về việc sử dụng phương tiện đó vào mục đích để ở đối với phương tiện không thuộc đối tượng phải đăng ký, đăng kiểm (nội dung xác nhận tại mục 2 của Ủy ban nhân dân cấp xã tại Tờ khai đề nghị xác nhận nơi thường xuyên đậu, đỗ; sử dụng phương tiện vào mục đích để ở theo Mẫu số 01 ban hành kèm theo Nghị định số 154/2024/NĐ-CP). (bản chính 1, bản sao 0)
---
Người được chăm sóc, nuôi dưỡng, trợ giúp được đăng ký thường trú tại cơ sở trợ giúp xã hội hoặc được đăng ký thường trú vào hộ gia đình nhận chăm sóc, nuôi dưỡng, trợ giúp
- Giấy tờ, tài liệu xác nhận về việc chăm sóc, nuôi dưỡng, trợ giúp. (bản chính 1, bản sao 0)
- Văn bản đề nghị của người đứng đầu cơ sở trợ giúp xã hội đối với người được cơ sở trợ giúp xã hội nhận chăm sóc, nuôi dưỡng, trợ giúp. (bản chính 1, bản sao 0)
---
Đăng ký thường trú tại chỗ ở hợ
```

faithful: ___    rel: ___

---

## 10. `pr2-22`

**Câu hỏi:** em moi mua xe may muon dang ky bien so o dau

**Câu trả lời của hệ thống:**

```
Đăng ký, cấp chứng nhận đăng ký xe, biển số xe
Cơ quan giải quyết:
Công an cấp Xã, Công an cấp Tỉnh, Cục Cảnh sát giao thông
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.115970
Quyết định công bố 4685/QĐ-BCA-C08 (2026-07-22, Bộ Công an) 
```

**Ngữ cảnh:**

```
Công an cấp Xã, Công an cấp Tỉnh, Cục Cảnh sát giao thông
```

faithful: ___    rel: ___

---

## 11. `rule_compare-02`

**Câu hỏi:** So sánh công nhận hộ nghèo định kỳ hằng năm và thường xuyên hằng năm.

**Câu trả lời của hệ thống:**

```
Công nhận hộ nghèo, hộ cận nghèo; hộ thoát nghèo, hộ thoát cận nghèo định kỳ hằng năm
Mô tả:
a) Bước 1: Gửi hồ sơ Hộ gia đình có Giấy đề nghị rà soát hộ nghèo, hộ cận nghèo theo Mẫu số 01 tại Phụ lục ban hành kèm theo Quyết định số 24/2021/QĐ-TTg nộp hồ sơ trực tiếp hoặc gửi qua đường bưu điện đến Chủ tịch Ủy ban nhân dân cấp xã. b) Bước 2: Lập danh sách hộ gia đình cần rà soát - Ban Chỉ đạo rà soát cấp xã chủ trì, phối hợp với thôn, tổ dân phố, bản, buôn, khóm, ấp (viết tắt là thôn) và rà soát viên lập danh sách hộ gia đình cần rà soát theo mẫu tại Phụ lục I ban hành kèm theo Thông tư số 07/2021/TT-BLĐTBXH, gồm: Hộ gia đình thuộc danh sách hộ nghèo, hộ cận nghèo do Ủy ban nhân dân cấp xã đang quản lý tại thời điểm rà soát và hộ gia đình có Giấy đề nghị rà soát hộ nghèo, hộ cận nghèo. - Hộ gia đình có Giấy đề nghị rà soát: rà soát viên sử dụng Phiếu A theo Phụ lục II ban hành kèm theo Thông tư số 07/2021/TT-BLĐTBXH (hướng dẫn sử dụng phiếu A tại Phụ lục IV ban hành kèm theo Thông tư số 02/2022/TT-BLĐTBXH) để nhận dạng nhanh đặc điểm hộ gia đình. Trường hợp có dưới 04 chỉ tiêu từ cột 01 đến cột 09 thì đưa vào danh sách hộ gia đình cần rà soát. c) Bước 3: Thu thập thông tin,
… (còn n
```

**Ngữ cảnh:**

```
a) Bước 1: Gửi hồ sơ Hộ gia đình có Giấy đề nghị rà soát hộ nghèo, hộ cận nghèo theo Mẫu số 01 tại Phụ lục ban hành kèm theo Quyết định số 24/2021/QĐ-TTg nộp hồ sơ trực tiếp hoặc gửi qua đường bưu điện đến Chủ tịch Ủy ban nhân dân cấp xã. b) Bước 2: Lập danh sách hộ gia đình cần rà soát - Ban Chỉ đạo rà soát cấp xã chủ trì, phối hợp với thôn, tổ dân phố, bản, buôn, khóm, ấp (viết tắt là thôn) và rà soát viên lập danh sách hộ gia đình cần rà soát theo mẫu tại Phụ lục I ban hành kèm theo Thông tư số 07/2021/TT-BLĐTBXH, gồm: Hộ gia đình thuộc danh sách hộ nghèo, hộ cận nghèo do Ủy ban nhân dân cấp xã đang quản lý tại thời điểm rà soát và hộ gia đình có Giấy đề nghị rà soát hộ nghèo, hộ cận nghèo. - Hộ gia đình có Giấy đề nghị rà soát: rà soát viên sử dụng Phiếu A theo Phụ lục II ban hành kèm theo Thông tư số 07/2021/TT-BLĐTBXH (hướng dẫn sử dụng phiếu A tại Phụ lục IV ban hành kèm theo Thông tư số 02/2022/TT-BLĐTBXH) để nhận dạng nhanh đặc điểm hộ gia đình. Trường hợp có dưới 04 chỉ tiêu từ cột 01 đến cột 09 thì đưa vào danh sách hộ gia đình cần rà soát. c) Bước 3: Thu thập thông tin, tính điểm và phân loại hộ gia đình Ban Chỉ đạo rà soát cấp xã chủ trì, phối hợp với trưởng thôn và rà soát viên sử dụng Phiếu B theo Phụ lục III và hướng dẫn sử dụng phiếu B tại Phụ lục IV ban hành kèm theo Thông tư số 02/2022/TT-BLĐTBXH để thu thập thông tin hộ gia đình, tính điểm, tổng hợp và phân loại hộ gia đình. d) Bước 4: Tổ chức họp dân để thống nhất kết quả rà soát - Thành phần cuộc họp: Ba
```

faithful: ___    rel: ___

---

## 12. `tpl-legal-37`

**Câu hỏi:** Căn cứ pháp lý của Ghi vào Sổ đăng ký nuôi con nuôi việc nuôi con nuôi đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài là gì?

**Câu trả lời của hệ thống:**

```
Ghi vào Sổ đăng ký nuôi con nuôi việc nuôi con nuôi đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài
Căn cứ ban hành:
Quyết định: 1848/QĐ-BTP
Ngày: 2025-06-22
Cơ quan ban hành: Bộ Tư pháp
Cổng: https://dichvucong.gov.vn/thu-tuc-hanh-chinh/2.002363

Căn cứ pháp lý:
- 85/2019/TT-BTC Thông tư Hướng dẫn về phí và lệ phí thuộc thẩm quyền quyết định của Hội đồng nhân dân tỉnh, thành phố trực thuộc Trung ương
- 60/2014/QH13 Luật 60/2014/QH13
- 04/2020/TT-BTP Hướng dẫn Luật hộ tịch và Nghị định 123/2015/NĐ-CP hướng dẫn Luật hộ tịch do Bộ trưởng Bộ Tư pháp ban hành
… và 14 văn bản khác
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/2.002363
Quyết định công bố 1848/QĐ-BTP (2025-06-22, Bộ Tư pháp) 
85/2019/TT-BTC Thông tư Hướng dẫn về phí và lệ phí thuộc thẩm quyền quyết định của Hội đồng nhân dân tỉnh, thành phố trực thuộc Trung ương 
60/2014/QH13 Luật 60/2014/QH13 
04/2020/TT-BTP Hướng dẫn Luật hộ tịch và Nghị định 123/2015/NĐ-CP hướng dẫn Luật hộ tịch do Bộ trưởng Bộ Tư pháp ban hành 
```

**Ngữ cảnh:**

```
Quyết định: 1848/QĐ-BTP
Ngày: 2025-06-22
Cơ quan ban hành: Bộ Tư pháp
Cổng: https://dichvucong.gov.vn/thu-tuc-hanh-chinh/2.002363
```

faithful: ___    rel: ___

---

## 13. `tpl-multi_field-23`

**Câu hỏi:** Thông báo thành lập/thay đổi tổ hợp tác không đăng ký cần giấy tờ gì và bao lâu có kết quả?

**Câu trả lời của hệ thống:**

```
Thông báo thành lập/thay đổi tổ hợp tác không đăng ký
Giấy tờ cần chuẩn bị:
- Thông báo thành lập/thay đổi tổ hợp tác không đăng ký (Mẫu số 1); (bản chính 1, bản sao 0)
- Hợp đồng hợp tác (Mẫu số 2); (bản chính 1, bản sao 0)
- Bản sao hoặc bản chính biên bản họp tổ hợp tác về việc bầu tổ trưởng (trường hợp tổ trưởng nộp hồ sơ); (bản chính 1, bản sao 0)
- Bản sao hoặc bản chính văn bản ủy quyền của một trăm phần trăm (100%) tổng số thành viên tổ hợp tác đồng ý (trường hợp người đại diện theo ủy quyền của các thành viên tổ hợp tác nộp hồ sơ) (bản chính 1, bản sao 0)

Thời hạn giải quyết:
1 ngày; 1 ngày làm việc
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/2.002226
Quyết định công bố 1994/QĐ-BTC (2026-07-26, Bộ Tài chính) 
```

**Ngữ cảnh:**

```
- Thông báo thành lập/thay đổi tổ hợp tác không đăng ký (Mẫu số 1); (bản chính 1, bản sao 0)
- Hợp đồng hợp tác (Mẫu số 2); (bản chính 1, bản sao 0)
- Bản sao hoặc bản chính biên bản họp tổ hợp tác về việc bầu tổ trưởng (trường hợp tổ trưởng nộp hồ sơ); (bản chính 1, bản sao 0)
- Bản sao hoặc bản chính văn bản ủy quyền của một trăm phần trăm (100%) tổng số thành viên tổ hợp tác đồng ý (trường hợp người đại diện theo ủy quyền của các thành viên tổ hợp tác nộp hồ sơ) (bản chính 1, bản sao 0)
---
1 ngày; 1 ngày làm việc
```

faithful: ___    rel: ___

---

## 14. `tpl-steps-14`

**Câu hỏi:** Trình tự thực hiện Giải thể nhà trẻ, trường mẫu giáo, trường mầm non?

**Câu trả lời của hệ thống:**

```
Giải thể nhà trẻ, trường mẫu giáo, trường mầm non
Các bước thực hiện:
Tổ chức, cá nhân gửi 01 bộ hồ sơ theo quy định trực tuyến trên Cổng Dịch vụ công quốc gia hoặc qua dịch vụ bưu chính hoặc trực tiếp tới Trung tâm Phục vụ hành chính công. Trong thời hạn 05 ngày làm việc, kể từ ngày nhận được hồ sơ đề nghị giải thể, Chủ tịch Ủy ban nhân dân cấp xã quyết định việc giải thể trường mầm non (bao gồm cả trường mầm non có vốn đầu tư nước ngoài); nếu chưa quyết định giải thể thì thông báo bằng văn bản gửi trực tiếp hoặc qua dịch vụ bưu chính hoặc thư điện tử cho tổ chức, cá nhân và nêu rõ lý do. Quyết định giải thể trường mầm non (theo Mẫu số 10 Phụ lục I kèm theo Nghị định số 142/2025/NĐ-CP); Quyết định giải thể trường mầm non có vốn đầu tư nước ngoài tại Việt Nam (theo Mẫu số 22 tại Phụ lục kèm theo nghị định số 124/2024/NĐ-CP) được công bố công khai trên các phương tiện thông tin đại chúng.
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/2.002893
Quyết định công bố 1181/QĐ-BGDĐT (2026-05-14, Bộ Giáo dục và Đào tạo) 
```

**Ngữ cảnh:**

```
Tổ chức, cá nhân gửi 01 bộ hồ sơ theo quy định trực tuyến trên Cổng Dịch vụ công quốc gia hoặc qua dịch vụ bưu chính hoặc trực tiếp tới Trung tâm Phục vụ hành chính công. Trong thời hạn 05 ngày làm việc, kể từ ngày nhận được hồ sơ đề nghị giải thể, Chủ tịch Ủy ban nhân dân cấp xã quyết định việc giải thể trường mầm non (bao gồm cả trường mầm non có vốn đầu tư nước ngoài); nếu chưa quyết định giải thể thì thông báo bằng văn bản gửi trực tiếp hoặc qua dịch vụ bưu chính hoặc thư điện tử cho tổ chức, cá nhân và nêu rõ lý do. Quyết định giải thể trường mầm non (theo Mẫu số 10 Phụ lục I kèm theo Nghị định số 142/2025/NĐ-CP); Quyết định giải thể trường mầm non có vốn đầu tư nước ngoài tại Việt Nam (theo Mẫu số 22 tại Phụ lục kèm theo nghị định số 124/2024/NĐ-CP) được công bố công khai trên các phương tiện thông tin đại chúng.
```

faithful: ___    rel: ___

---

## 15. `tpl-time-39`

**Câu hỏi:** Thủ tục tuyển chọn chuyên gia bao lâu thì có kết quả?

**Câu trả lời của hệ thống:**

```
Thủ tục tuyển chọn chuyên gia
Thời hạn giải quyết:
1
Cổng Dịch vụ công Quốc gia https://dichvucong.gov.vn/thu-tuc-hanh-chinh/1.014352
Quyết định công bố 1091/QĐ-BNV (2025-09-21, Bộ Nội vụ) 
```

**Ngữ cảnh:**

```
1
```

faithful: ___    rel: ___

---

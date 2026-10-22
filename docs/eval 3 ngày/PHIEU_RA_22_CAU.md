# Phiếu rà 22 câu "không chắc" (System 3)

22 câu mà A và B gán cùng nhãn nhưng ít nhất một bên ghi "không chắc". Bạn đã duyệt theo đề xuất; phiếu này giúp kiểm sâu nếu muốn. Mỗi câu có: nguyên văn, nhãn hiện tại, thủ tục liên quan, điều cần kiểm và chỗ ghi quyết định.

## Cách làm

1. Mở `eval/real_v1/real_v1_labels_final.json`, tìm theo `id` (ví dụ `real_v1-003`) để xem `beh`, `expect_ids`, `fields`, `notes`.
2. Mở `eval/real_v1/cases_real_v1.json` hoặc đọc nguyên văn câu hỏi trong phiếu này.
3. Với mã thủ tục trong cột **Thủ tục**, tra tên và nội dung ở `data/snapshot/procedures_v3.jsonl` (tìm `"proc_id": "1.116410"`), hoặc mở link Cổng dịch vụ công ghi sẵn. Đọc `description`, `requirements`, `steps`.
4. Trả lời ba câu hỏi: (a) người hỏi cần việc gì, (b) thủ tục trong DB có làm được việc đó không, (c) có thủ tục nào khác sát hơn không (tìm thêm bằng chữ khác trong `name`, ví dụ "CMND" và "chứng minh nhân dân").
5. Ghi quyết định: giữ, hoặc sửa `beh` / `expect_ids` trực tiếp trong `eval/real_v1/real_v1_labels_final.json`. Sửa xong thì thêm vào `review` chữ "đã kiểm sâu" và ghi lý do vào `notes`. Không dùng hệ thống để tra đáp án.

Quy tắc chọn nhãn (rút gọn từ `REAL_V1_GUIDE.md`): `answer` khi chỉ rõ một thủ tục cấp xã dùng chung toàn quốc (`in_scope = 1`); `clarify` khi còn từ hai thủ tục hợp lý trở lên; `apologize` khi thủ tục không có trong DB hoặc câu hỏi là luật, xử phạt, khiếu nại, tình trạng hồ sơ.

## 22 câu

### 1. real_v1-003: apologize  (apologize gần thủ tục)

**Câu hỏi:** Tôi công tác trên 15 năm trong lực lượng Công an nhân dân (CAND) nhưng vì lý do sức khỏe tôi phải xuất ngũ. Bộ Công an cho tôi hỏi, trường hợp của tôi có được cấp thẻ bảo hiểm xã hội không? Nếu không được cấp thì quy định tại văn bản nào?

**Ghi chú nhãn:** Hoi quyen huong the BHXH cua cong an nhan dan xuat ngu va van ban quy dinh (chinh sach rieng CAND). Gan nhat 1.002051/1.002759 (cap so BHXH, the BHYT chung) nhung khong co thu tuc rieng cho CAND. Khong chac.

**Thủ tục liên quan:**

- `1.002051` Đăng ký, điều chỉnh đóng BHXH bắt buộc, BHYT, BHTN, bảo hiểm TNLĐ, BNN; cấp sổ BHXH, thẻ BHYT (cơ quan: Bảo hiểm xã hội tỉnh; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfb-d7a4-72c9-9668-916aee4876d3)
- `1.002759` Cấp lại, đổi, điều chỉnh thông tin trên sổ BHXH, thẻ BHYT (cơ quan: Bảo hiểm xã hội tỉnh; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfb-df35-76fe-b9f6-886f8a133b5c)

**Cần kiểm:** Có thủ tục riêng cho công an nhân dân xuất ngũ không? Nếu chỉ có thủ tục BHXH chung (ví dụ 1.002051, 1.002759) và câu hỏi là quyền hưởng của một nhóm đặc thù thì giữ `apologize`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 2. real_v1-011: answer 1.116788  (answer: câu có hoàn cảnh đặc biệt)

**Câu hỏi:** Chồng tôi là người Việt Nam, sinh ra và định cư tại Nga. Chồng tôi có giấy tờ thường trú tại Nga, nay muốn về Việt Nam sinh sống và đăng ký hộ khẩu thường trú vào hộ khẩu của tôi tại xã Thuỷ Xuân Tiên, huyện Chương Mỹ, thành phố Hà Nội. Hiện nay, chồng tôi vẫn có hộ chiếu còn hiệu lực và giấy khai sinh do Đại sứ quán Việt Nam tại Liên bang Nga cấp. Tôi muốn hỏi Bộ Công an, để được đăng ký hộ khẩu thường trú cho chồng tôi thì tôi cần chuẩn bị những gì? Chồng tôi có cần xin giấy chấp nhận hồi hương ở Đại sứ quán không?

**Ghi chú nhãn:** Dang ky thuong tru cho nguoi Viet tu nuoc ngoai ve (ho gia dinh o Ha Noi); thu tuc 'Dang ky thuong tru' 1.116788. Phan hoi huong co the khong co trong thu tuc. Khong chac.

**Thủ tục liên quan:**

- `1.116788` Đăng ký thường trú (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a0e614-34b3-7355-929c-9f54d24e6bc0)

**Cần kiểm:** Việt kiều về nước thì đăng ký thường trú có dùng cùng thủ tục 1.116788 không, hay có thủ tục riêng (nhập cảnh, hồi hương)? Nếu dùng chung thì giữ.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 3. real_v1-017: apologize  (apologize gần thủ tục)

**Câu hỏi:** Bản sao chứng thực điện tử trực tuyến có thể in để sử dụng khi nộp hồ sơ trực tiếp không ạ! Tại vì bản chứng thực điện tử khi công chức trực tuyến sẽ có bản sao khi in ra là bản dấu, chữ ký màu đen và dấu chức thực, chữ ký nằm 1 tờ rời khác không có dấu giáp lai giữa bản sao và dấu, chữ ký chứng thực điện tử. Xin chân thành cảm ơn

**Ghi chú nhãn:** Hoi gia tri su dung ban sao chung thuc dien tu khi in ra nop truc tiep (van de hieu luc), khong phai thu tuc; DB khong co thu tuc ban sao dien tu. Khong chac.

**Thủ tục liên quan:**

- `2.000815` Chứng thực bản sao từ bản chính giấy tờ, văn bản do cơ quan, tổ chức có thẩm quyền của Việt Nam; cơ quan, tổ chức có thẩm quyền của nước ngo (cơ quan: Tổ chức hành nghề công chứng, Cơ quan đại diện có thẩm quyền; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfd-8e22-77ef-819f-e49460350904)

**Cần kiểm:** Câu hỏi là giá trị của bản sao chứng thực điện tử khi in ra, hay là cách chứng thực? Nếu hỏi cách làm thì chuyển `answer` với 2.000815; nếu hỏi hiệu lực thì giữ `apologize`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 4. real_v1-023: answer 1.115970  (answer: tên thủ tục gộp)

**Câu hỏi:** Tôi muốn làm lại biển số xe máy lần 2 do di chuyển trên đường bi mất.mong mọi người hướng dẫn để làm lại

**Ghi chú nhãn:** Lam lai bien so xe may bi mat: 'Dang ky, cap chung nhan dang ky xe, bien so xe' 1.115970 (ten gop, co the gom cap lai bien so). Khong chac.

**Thủ tục liên quan:**

- `1.115970` Đăng ký, cấp chứng nhận đăng ký xe, biển số xe (cơ quan: Công an cấp Tỉnh, Công an cấp Xã, Cục Cảnh sát giao thông; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019f8e19-045a-72d1-bab5-9488acf9a9b5)

**Cần kiểm:** Mở thủ tục 1.115970, đọc phần mô tả và thành phần hồ sơ: có nói về cấp lại biển số khi mất không? Có thì giữ; nếu không thì chuyển `clarify` hoặc `apologize`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 5. real_v1-053: answer 1.116410  (answer: câu có điều kiện đặc thù)

**Câu hỏi:** Tôi là cán bộ trong ngành Công an, hiệnđang công tác tại đơn vị đóng quân xa nhà. Tôi muốn hỏi Bộ Công an, trường hợp những cán bộ, chiến sỹ công tác trong lực lượng vũ trang nói chung, ngành Công an nói riêng, công tácxa nhà có được ưu tiên cấp Căn cước công dân có gắn chíp điện tử tại địa bàn đóng quân hay không? Nếu được cấp thì phải chuẩn bị những giấy tờ gì?

**Ghi chú nhãn:** Cap the can cuoc gan chip tai noi dong quan (can bo CA cong tac xa nha): hoi giay to can chuan bi; khop 'Cap, cap doi, cap lai the can cuoc' 1.116410. Phan uu tien chi mang tinh quy dinh. Khong chac.

**Thủ tục liên quan:**

- `1.116410` Cấp, cấp đổi, cấp lại thẻ căn cước (cơ quan: Công an cấp Xã; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a022c0-03f3-74cd-b280-7fd6ad6d2f80)

**Cần kiểm:** Câu chính là thủ tục làm thẻ căn cước gắn chip tại nơi đóng quân. Thủ tục 1.116410 có hồ sơ và nơi nộp trả lời được không? Phần 'ưu tiên' chỉ là quy định, chấp nhận.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 6. real_v1-064: apologize  (apologize gần thủ tục)

**Câu hỏi:** Năm 2005, gia đình tôi có chuyển nhượng thửa đất (diện tích đất ở 61m2, đất trồng cây lâu năm 58,9m2), thửa đất này phù hợp với quy hoạch hàng năm của địa phương (được phép chuyển từ đất nông nghiệp sang đất ở, có hộ khầu thường trú ở địa phương). Vào cuối năm 2020, do có nhu cầu xây dựng nhà ở, tôi lập hồ sơ gửi Văn phòng một cửa của tx xin chuyển diện tích đất nông nghiệp sang đất ở, sau đó lập thủ tục cấp phép xây dựng nhà ở. Đúng hạn định thì được trả lời: không thực hiện việc chuyển 58,9m2 đất nông nghiệp sang đất ở được, với lý do :gia đình tôi đã được nhà nước giao đất ở cùng tại địa phương (200m2, hiện đã có nhà ở từ thừa kế theo pháp luật từ cha mẹ ruột để lại, do đó đã ổn định về nơi ở).Theo suy nghĩ của tôi: Đất đai là tài sản nên theo quy định của pháp luật thì cá nhân, tổ chức... có quyền chuyển nhượng, trao đổi (là hình thức dân sự) thì sao không chuyển mục đích SDĐ được.

**Ghi chú nhãn:** Tranh luan phap ly ve chuyen nhuong dat 2005 va khong duoc chuyen muc dich su dung dat (khieu nai/luat). DB chi co thu tuc chuyen muc dich cua tung tinh (vi du Can Tho, Lang Son), cau khong hoi thu tuc. Khong chac.


**Cần kiểm:** Câu là tranh luận pháp lý về chuyển nhượng 2005 và chuyển mục đích, không hỏi cách làm. DB chỉ có thủ tục chuyển mục đích của từng tỉnh. Giữ `apologize` nếu bạn thấy đây là khiếu nại; nếu hỏi cách làm thì chuyển `clarify`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 7. real_v1-075: answer 1.115970  (answer: tên thủ tục gộp)

**Câu hỏi:** Tôi có chiếc xe ô tô 5 chỗ, khi tham gia giao thông, tôi bị mất biển số xe. Bộ Công an cho tôi hỏi, thủ tục để được cấp lại biển số xe như thế nào?

**Ghi chú nhãn:** Cap lai bien so xe o to bi mat: 'Dang ky, cap chung nhan dang ky xe, bien so xe' 1.115970. Khong chac (ten gop).

**Thủ tục liên quan:**

- `1.115970` Đăng ký, cấp chứng nhận đăng ký xe, biển số xe (cơ quan: Công an cấp Tỉnh, Công an cấp Xã, Cục Cảnh sát giao thông; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019f8e19-045a-72d1-bab5-9488acf9a9b5)

**Cần kiểm:** Giống 023: kiểm 1.115970 có phần cấp lại biển số khi mất không.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 8. real_v1-105: answer 1.116410  (answer: câu hỏi quy định)

**Câu hỏi:** Tôi năm nay 38 tuổi, hiện nay, tôi muốn làm thẻ Căn cước công dân (CCCD) có gắn chíp điện tử. Theo quy định của Luật CCCD thì đến 40 tuổi công dân phải đổi thẻ CCCD, Bộ Công an cho tôi hỏi, trường hợp của tôi nếu làm thẻ CCCD có gắn chíp điện tử thì tới năm 40 tuổi tôi có phải đổi thẻ CCCD không? Ngoài ra, khi làm thẻ CCCD có gắn chíp điện tử thì tôi có bị thu lại thẻ CCCDcó mã vạch không?

**Ghi chú nhãn:** Lam the can cuoc gan chip o 38 tuoi: co phai doi lai luc 40 tuoi khong, co bi thu the cu khong; khop 'Cap, cap doi, cap lai the can cuoc' 1.116410. Khong chac (cau hoi quy dinh).

**Thủ tục liên quan:**

- `1.116410` Cấp, cấp đổi, cấp lại thẻ căn cước (cơ quan: Công an cấp Xã; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a022c0-03f3-74cd-b280-7fd6ad6d2f80)

**Cần kiểm:** Câu hỏi: làm thẻ chip ở 38 tuổi thì 40 tuổi có phải đổi lại không, có bị thu thẻ cũ không. Đây là quy định, không phải cách làm. Giữ `answer` (1.116410) nếu thủ tục có nêu điều kiện cấp đổi, nếu không thì chuyển `apologize`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 9. real_v1-130: answer 1.116788  (answer: câu có hoàn cảnh đặc biệt)

**Câu hỏi:** Tôi có hộ khẩu tại thành phố Hà Nội, đã đăng ký hộ khẩu thường trú chỗ ở hợp pháp tại thành phố Hồ Chí Minh liên tục trong 2 năm. Nay tôi muốn làm hộ khẩu ở thành phố Hồ Chí Minh có được không? Nếu được thì tôi cần phải làm những thủ tục gì? Chứng minh nhân dân của tôi tại Hà Nội đã hết hạn thì tôi có phải ra Hà Nội làm lại rồi mới được làm hộ khẩu tại thành phố Hồ Chí Minh không?

**Ghi chú nhãn:** Dang ky thuong tru tai TP.HCM khi dang co ho khau Ha Noi: 'Dang ky thuong tru' 1.116788. Phan CMND het han co the nam ngoai thu tuc. Khong chac.

**Thủ tục liên quan:**

- `1.116788` Đăng ký thường trú (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a0e614-34b3-7355-929c-9f54d24e6bc0)

**Cần kiểm:** Đăng ký thường trú ở TP.HCM khi đang có hộ khẩu Hà Nội, CMND đã hết hạn. Thủ tục 1.116788 có điều kiện về thời gian cư trú và giấy tờ không? Phần CMND hết hạn có thể ngoài thủ tục.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 10. real_v1-131: clarify 1.012753, 1.013978  (clarify: nhiều thủ tục)

**Câu hỏi:** Tôi có sổ đỏ năm 1994 gia hạn năm 2008 hiện đã hết thời gian sử dụng, có 4 thửa đất, ví dụ 1234, trog dó 1 là ở + vườn, 234 là lúa. Qua đối chiếu thực tế và kiểm tra hồ sơ luu tại ubnd xã thì 1 phải là vườn còn 2 là ở và vườn. Vậy thủ tục tôi cần làm những gì để xác định lại mục đích thửa đất ở và vườn, đổi, cấp lại sổ đỏ

**Ghi chú nhãn:** Xac dinh lai muc dich thua dat, doi / cap lai so do: nhieu thu tuc dat dai co the phu hop (dang ky dat dai, cap GCN 1.012753, 1.013978) va co ban rieng cua tinh; cau chua ro viec can lam. Khong chac.

**Thủ tục liên quan:**

- `1.012753` Đăng ký đất đai, tài sản gắn liền với đất, cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất lần đầu đối với tổ c (cơ quan: Chủ tịch UBND cấp xã; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfa-6eeb-7460-9097-1804edf38aec)
- `1.013978` Đăng ký đất đai, tài sản gắn liền với đất, cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất lần đầu đối với hộ g (cơ quan: Văn phòng đăng ký đất đai, Chủ tịch Ủy ban nhân dân xã, Chi ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfa-8678-770b-8917-1872078767cd)

**Cần kiểm:** Thủ tục 1.012753 là của tổ chức, 1.013978 là của hộ gia đình, cá nhân. Câu hỏi của hộ gia đình nên chỉ còn 1.013978; cần xem câu có nói đổi, cấp lại hay xác định lại mục đích.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 11. real_v1-145: answer 2.000635  (answer: hai thủ tục có thể đúng)

**Câu hỏi:** Tôi có con bị mất giấy khai sinh nhờ hỗ trợ quy trình cấp lại giấy khai sinh cho con dưới 12 tuổi

**Ghi chú nhãn:** Con bi mat giay khai sinh, xin cap lai (duoi 12 tuoi): 'Cap ban sao Trich luc ho tich, ban sao Giay khai sinh' 2.000635. Khong chac (co the dang ky lai khai sinh 1.004884 neu khong con so).

**Thủ tục liên quan:**

- `2.000635` Cấp bản sao Trích lục hộ tịch, bản sao Giấy khai sinh (cơ quan: Cơ quan quản lý cơ sở dữ liệu hộ tịch điện tử; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfd-867c-72db-b6a7-dcbd8c763807)
- `1.004884` Thủ tục đăng ký lại khai sinh (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfd-6eac-7598-b88b-15f8a61b366a)

**Cần kiểm:** Mất giấy khai sinh của con dưới 12 tuổi: xin bản sao trích lục (2.000635) hay đăng ký lại khai sinh (1.004884)? Nếu sổ hộ tịch còn thì 2.000635; nếu không còn thì 1.004884. Câu chưa nói, nên có thể `clarify`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 12. real_v1-151: answer 1.116788  (answer: câu có hoàn cảnh đặc biệt)

**Câu hỏi:** Tôi, chị gái tôi và con trai chị gái tôi cùng đăng ký thường trú tại tổ dân phố 05, thị trấn Đạ M’ri, huyện Đạ Huoai, tỉnh Lâm Đồng và cùng có tên trong một sổ hộ khẩu gia đình do tôi đứng tên chủ hộ. Cháu trai tôi đã lập gia đình và sinh con vào năm 2015 nhưng chưa nhập khẩu khai sinh cho con. Bộ Công an cho tôi hỏi, con của cháu tôi muốn nhập khẩu khai sinh vào hộ của tôi có được không? Nếu được thì hồ sơ, thủ tục nhập khẩu khai sinh cho con của cháu tôi gồm những giấy tờ gì?

**Ghi chú nhãn:** Nhap khau cho tre khai sinh 2015 vao ho nguoi bao ho: dang ky thuong tru 'Dang ky thuong tru' 1.116788. Khong chac (co the can ca khai sinh).

**Thủ tục liên quan:**

- `1.116788` Đăng ký thường trú (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a0e614-34b3-7355-929c-9f54d24e6bc0)

**Cần kiểm:** Con của cháu (khai sinh 2015) nhập hộ khẩu vào hộ của người bảo hộ. Thủ tục 1.116788 có áp dụng cho trường hợp này không? Câu cũng hỏi hồ sơ.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 13. real_v1-152: answer 1.116410  (answer: câu có điều kiện đặc thù)

**Câu hỏi:** Tôi sinh năm 1940, từng có 11 năm tham gia chiến trường và hiện là thương binh. Năm 1978, tôi làm Chứng minh nhân dân, trong Chứng minh nhân dân ghi năm sinh của tôi là năm 1945. Hiện nay, tôi không có Giấy khai sinh nhưng trong Sổ hộ khẩu, Quyết định nghỉ mất sức, Huân chương kháng chiến chống Mỹ hạng Nhì, thẻ Bảo hiểm y tế, thẻ Cựu chiến binh, Giấy lĩnh lương hàng tháng của tôi đều ghi sinh năm 1940. Bộ Công an cho tôi hỏi, với thông tin về năm sinh là khác nhau giữa Chứng minh nhân dân và các giấy tờ nêu trên, tôi có thể làm thẻ Căn cước công dân được không?

**Ghi chú nhãn:** Lam the can cuoc khi nam sinh tren CMND khac cac giay to khac: 'Cap, cap doi, cap lai the can cuoc' 1.116410. Khong chac.

**Thủ tục liên quan:**

- `1.116410` Cấp, cấp đổi, cấp lại thẻ căn cước (cơ quan: Công an cấp Xã; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a022c0-03f3-74cd-b280-7fd6ad6d2f80)

**Cần kiểm:** Năm sinh khác nhau giữa CMND và giấy tờ khác, có làm được thẻ căn cước không. Kiểm 1.116410; nếu cần điều chỉnh thông tin trước thì thêm 1.012564.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 14. real_v1-157: answer 1.116789  (answer: câu hỏi quy định)

**Câu hỏi:** Tôi có sổ hộ khẩu thường trú tại tổ dân phố Hạnh, Tây Mỗ, Nam Từ Liêm, Hà Nội. Tôi muốn làm đăng ký KT3 cho 3 người em hiện là sinh viên. Khi nộp hồ sơ lên phường đồng chí cán bộ phụ trách trả lời tôi là sinh viên không được làm KT3. Bộ Công an cho tôi hỏi đồng chí cán bộ này trả lời tôi như vậy có đúng không?

**Ghi chú nhãn:** Sinh vien co duoc dang ky tam tru (KT3) khong: 'Dang ky tam tru' 1.116789. Cau cung hoi can bo tra loi co dung khong. Khong chac.

**Thủ tục liên quan:**

- `1.116789` Đăng ký tạm trú (cơ quan: Công an cấp Xã; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a0f011-315c-7373-9678-d13f6e83bbb3)

**Cần kiểm:** Sinh viên có được đăng ký tạm trú (KT3) không, cán bộ trả lời có đúng không. Thủ tục 1.116789 có nêu đối tượng/điều kiện không? Nếu chỉ là hỏi đúng sai quy định thì `apologize`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 15. real_v1-168: apologize  (apologize gần thủ tục)

**Câu hỏi:** Xin chào Dịch vụ công cấp tỉnh Bình Định. Tôi có nộp hồ sơ H[ID]-0004, với thủ tục "Thủ tục cấp giấy xác nhận tình trạng hôn nhân" => Tình trạng hồ sơ yêu cầu "bổ sung giấy xác nhận tình trạng hôn nhân của vợ" thì lý do này không được chính xác lắm, vì tôi chưa từng kết hôn và đang xin cấp giấy xác nhận độc thân. Kính gửi.

**Ghi chú nhãn:** Phan nan ho so xac nhan tinh trang hon nhan bi yeu cau bo sung sai (tinh trang ho so, khieu nai), du thu tuc 1.004873 co trong DB. Khong chac.

**Thủ tục liên quan:**

- `1.004873` Thủ tục cấp Giấy xác nhận tình trạng hôn nhân (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfd-6eb3-7019-bf3f-fc58c9ee44b9)

**Cần kiểm:** Thủ tục 1.004873 (xác nhận tình trạng hôn nhân) có trong DB. Câu là phàn nàn hồ sơ bị yêu cầu bổ sung sai (tình trạng hồ sơ), không hỏi cách làm. Giữ `apologize`; nếu bạn thấy câu hỏi cách xử lý thì chuyển `answer`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 16. real_v1-171: answer 1.116788  (answer: câu hỏi quy định)

**Câu hỏi:** Tôi đăng ký tạm trú tại phường 25,quận Bình Thạnh, thành phố Hồ Chí Minh đã được 2 năm. Vừa qua,tôi mới mua căn nhà tại phường 27,quận Bình Thạnh, thành phố Hồ Chí Minh vàđếnCông anquận Bình Thạnh hỏi về thủ tục nhập hộ khẩu thường trú thì tôi được hướng dẫn về làm giấy tạm trú tại phường 27 rồi mới được đăng ký thường trú tại đó. Tôi muốn hỏi, Công an quận Bình Thạnh hướng dẫn như vậy có đúng không và căn cứ vào quy định nào?

**Ghi chú nhãn:** Mua nha moi o phuong khac, dang ky thuong tru co can lam tam tru truoc khong va can cu quy dinh: 'Dang ky thuong tru' 1.116788. Cau hoi huong dan co dung khong. Khong chac.

**Thủ tục liên quan:**

- `1.116788` Đăng ký thường trú (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a0e614-34b3-7355-929c-9f54d24e6bc0)

**Cần kiểm:** Mua nhà mới ở phường khác, có phải làm tạm trú trước khi đăng ký thường trú không, căn cứ quy định nào. Kiểm 1.116788 có nêu điều kiện chỗ ở hợp pháp và không bắt buộc tạm trú; có `legal_basis`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 17. real_v1-178: answer 1.116788  (answer: câu có điều kiện đặc thù)

**Câu hỏi:** Tôi vừa tốt nghiệp Học viện An ninh nhân dân, hiện công tác xa nhà. Vừa rồi, tôi có đi đăng ký thường trú tại địa chỉ đơn vị đóng quân nhưng không được, trước đó hộ khẩu thường trú của tôi là tại Học viện An ninh nhân dân từ khi còn là học viên. Bộ Công an cho tôi hỏi, cán bộ, chiến sỹ Công an đang công tác xa nhà cần những điều kiện gì để có thể đăng ký thường trú tại đơn vị?

**Ghi chú nhãn:** Dieu kien dang ky thuong tru tai don vi cua can bo cong an cong tac xa nha: 'Dang ky thuong tru' 1.116788. Khong chac (doi tuong dac thu).

**Thủ tục liên quan:**

- `1.116788` Đăng ký thường trú (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a0e614-34b3-7355-929c-9f54d24e6bc0)

**Cần kiểm:** Công an xa nhà đăng ký thường trú tại đơn vị. Thủ tục 1.116788 có trường hợp đơn vị quân đội, công an không? Nếu đối tượng đặc thù nằm ngoài thủ tục thì `apologize`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 18. real_v1-247: answer 1.116410  (answer: câu hỏi quy định)

**Câu hỏi:** Tôi năm nay 61 tuổi, đã làm thẻ Căn cước công dân (CCCD) năm 2019. Theo quy định của Luật CCCD 2014 thì công dân ngoài 60 tuổi không phải đổi thẻ CCCD, trong khi đó, Bộ Công an vừa có chủ trươngtriển khai cấp thẻ CCCD có gắn chíp điện tử thay thế thẻ CCCD có mã vạch. Bộ Công an cho tôi hỏi, những trường hợp nào thì phải đổi thẻ CCCD có mã vạch sang thẻ CCCD có gắn chíp điện tử? Những người đã được cấp thẻ CCCD có mã vạch nhưng vẫn còn hạn sử dụng thì có phải đổi sang thẻ CCCD có gắn chíp điện tử không? Trường hợp ngoài 60 tuổi đã làm thẻ CCCD có mã vạch như tôi có phải đổi sang thẻ CCCD có gắn chíp điện tử không?

**Ghi chú nhãn:** Co phai doi sang the CCCD gan chip khi da co the ma vach / ngoai 60 tuoi: 'Cap, cap doi, cap lai the can cuoc' 1.116410. Khong chac (cau hoi quy dinh).

**Thủ tục liên quan:**

- `1.116410` Cấp, cấp đổi, cấp lại thẻ căn cước (cơ quan: Công an cấp Xã; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a022c0-03f3-74cd-b280-7fd6ad6d2f80)

**Cần kiểm:** Hỏi có phải đổi sang thẻ chip khi đã có thẻ mã vạch, ngoài 60 tuổi. Đây là quy định, không phải cách làm. Kiểm 1.116410 có nêu điều kiện cấp đổi.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 19. real_v1-250: answer 1.115971  (answer: tên thủ tục)

**Câu hỏi:** Năm 2013, tôi có bán 01 chiếc xe máy, lúc bán tôi không làm thủ tục sang tên. Hiện tại tôi cũng không gặp, không liên hệ được với người mua chiếc xe đó. Bộ Công an cho tôi hỏi, tôi muốn xác nhận và chứng thực xe đó không thuộc quyền sở hữu của tôi nữa thì tôi phải làm thế nào?

**Ghi chú nhãn:** Ban xe khong sang ten, muon xac nhan khong con la chu so huu: gan nhat 'Thu hoi chung nhan dang ky xe, bien so xe' 1.115971. Khong chac.

**Thủ tục liên quan:**

- `1.115971` Thu hồi chứng nhận đăng ký xe, biển số xe (cơ quan: Công an cấp Tỉnh, Công an cấp Xã, Cục Cảnh sát giao thông; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019f91d2-8840-73cc-935c-a6c9695f6d03)

**Cần kiểm:** Bán xe 2013 không sang tên, không liên lạc được người mua, muốn xác nhận không còn là chủ xe. Thủ tục 1.115971 (thu hồi chứng nhận đăng ký xe, biển số) có áp dụng cho chủ cũ không? Nếu không thì `apologize`.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 20. real_v1-270: answer 1.004859  (answer: tên thủ tục)

**Câu hỏi:** Tôi làm thủ tục đổi chữ lót của họ tên thì bị từ chối.Tôi đến hỏi phòng tư pháp hỏi lý do và giải thích thì cán bộ đồng ý cho phép nộp lại mã hồ sơ nhưng bắt buộc phải chứng minh anh trai tôi là anh ruột. Yêu cầu cung cấp giấy xác nhận nhân khẩu và giấy khai sinh của anh tôi: Tôi đến công an huyện xin xác nhận nhân khẩu của tàng thư cũ thì bắt nộp đơn xin phiền phức nên tôi quay lại phòng tư pháp hỏi thì cán bộ điều tra nội bộ vơi cơ quan công an bằng số CCCD của Mẹ tôi - xong thì không yêu cầu cung cấp xác nhận nhân khẩu nữa. Còn giấy khai sinh anh trai tôi thì do anh trai có hộ khẩu ở xa khó về xã quê quán cũ để xin trích lục giấy khai sinh. Cơ quan công an xã thì bảo chỉ cung cấp được giấy xác nhận nhân khẩu hiện tại mà không có tên anh trai tôi và bảo nếu chứng minh anh ruột thì cơ quan công an in ra thông tin cư trú trên tài khoản VNEID của Bộ công an là được.

**Ghi chú nhãn:** Doi chu lot ho ten (thay doi, cai chinh thong tin ho tich): 'Thu tuc thay doi, cai chinh, bo sung thong tin ho tich, xac dinh lai dan toc' 1.004859; hoi giay to chung minh anh em ruot. Khong chac.

**Thủ tục liên quan:**

- `1.004859` Thủ tục thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/019d2bfd-671e-714b-8fd6-8230c82f7867)

**Cần kiểm:** Đổi chữ lót họ tên. 1.004859 là thay đổi, cải chính, bổ sung thông tin hộ tịch; thủ tục thay đổi họ tên có thể nằm riêng. Kiểm DB: tìm 'thay đổi họ, tên'.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 21. real_v1-284: apologize  (apologize: câu phức tạp)

**Câu hỏi:** Kính thưa quý cấp Tôi xin có câu hỏi sau: Năm 2000 tôi nhập ngũ vào Quân đội học tại trường cao đẳng Kỹ thuật Vinhempich/ Tổng cục Kỹ thuật, từ năm 2004 đến nay tôi công tác tại Phòng Kỹ thuật/Bộ CHQS tỉnh Bình Định, Hộ khẩu thường trú của tôi được công an Xã Phước nghĩa cắt chuyển vào Quân đội năm 2000, năm 2018 tôi được cán bộ phường Nguyễn Văn Cừ đến cơ quan Bộ CHQS tỉnh Bình Định thu thập thông tin cá nhân để nhập vào cơ sở dữ liệu quốc gia và tổ chức làm thủ tục cấp căn cước công dân đến tháng 11 năm 2022 tôi vẫn chưa có thẻ căn cước công dân và thông tin trên dữ liệu quốc gia. Hiện tại bản thân bản thân có nhu cầu nhập khẩu về gia đình bố vợ ở Phường Nhơn Bình, thành phố Quy Nhơn và đã làm nộp hồ sơ từ ngày 03/10/2022 đến nay vẫn không nhập được vì không có dữ liệu thông tin cá nhân tại Công an phường Nguyễn Văn Cừ. như vậy bây giờ tôi cần làm gì để có thông tin dữ liệu cá nhân, cơ quan nào tổ chức thực hiện thu thập thông tin và khi nào tôi được nhập khẩu về hộ gia đình để làm căn cước công dân theo quy định của Nhà nước? kính mong quý cấp xem xét giải quyết trân trọng cảm ơn.

**Ghi chú nhãn:** Cau phuc tap ve quan nhan cu, thong tin du lieu ca nhan va nhap khau de lam CCCD; khong khop mot thu tuc ro rang. Khong chac.


**Cần kiểm:** Quân nhân cũ cần thông tin dữ liệu cá nhân và nhập khẩu để làm CCCD: nhiều ý, không khớp một thủ tục. Giữ `apologize` hoặc chuyển `clarify` nếu thấy ý chính là làm thẻ căn cước.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______

### 22. real_v1-298: answer 1.116788  (answer: câu hỏi quy định)

**Câu hỏi:** Tôi sinh con vào tháng 11/2021, sau khi sinh con tôi mới chỉ đi khai sinh cho con mà chưa làm thủ tục nhập hộ khẩu. Hiện nay, tôi muốn làm thủ tục nhập hộ khẩu cho con, Bộ Công an cho tôi hỏi, theo quy định trường hợp của tôi có bị phạt tiền vì nhập hộ khẩu cho con muộn hay không? Tôi sẽ phải làm những thủ tục gì để nhập hộ khẩu cho con?

**Ghi chú nhãn:** Nhap ho khau (dang ky thuong tru) cho con sinh 11/2021 va hoi co bi phat khong: 'Dang ky thuong tru' 1.116788. Phan phat tien la luat xu phat. Khong chac.

**Thủ tục liên quan:**

- `1.116788` Đăng ký thường trú (cơ quan: ; https://dichvucong.gov.vn/thu-tuc-hanh-chinh/01a0e614-34b3-7355-929c-9f54d24e6bc0)

**Cần kiểm:** Nhập hộ khẩu cho con sinh 11/2021, có bị phạt vì đăng ký muộn không. Phần phạt là luật xử phạt; phần thủ tục (hồ sơ nhập khẩu cho con) có trong 1.116788.

**Quyết định:** [ ] giữ  [ ] sửa thành: ______  Lý do: ______


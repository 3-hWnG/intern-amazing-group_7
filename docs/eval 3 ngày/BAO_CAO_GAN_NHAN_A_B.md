# Báo cáo gán nhãn A và B cho bộ real_v1 (20/10/2026)

Kết quả sau khi hai lượt gán nhãn xong: **A** do Claude gán trực tiếp, **B** do một subagent Claude gán riêng, không đọc file A. Báo cáo chỉ liệt kê và đề xuất; chưa sửa nhãn nào. Mọi con số tính từ file nhãn thật bằng `eval/real_v1/real_v1_agree.py` và script đối chiếu.

> Cả hai lượt đều là AI. κ dưới đây đo độ nhất quán giữa hai lượt AI, không phải độ đồng thuận của hai người độc lập. Báo cáo cho mentor phải ghi đúng như vậy (mục 5).

File nhãn: `eval/real_v1/real_v1_labels_A.json`, `eval/real_v1/real_v1_labels_B.json` (System 3, 300 câu); `system4/eval/real_v1/real_v1_s4_labels_A.json`, `_B.json` (System 4, 200 câu).

## 1. Tóm tắt

| | System 3 (300 câu) | System 4 (200 câu) |
|---|---|---|
| Nhãn khớp | 258/281 câu cả hai không `skip` (91,8%) | `drop` khớp 94%, `refusal` 95%, `ask_back` 100%, `urgent` và `needs_image` 100% |
| Cohen's κ | **0.753** (ba lớp `answer`/`clarify`/`apologize`) | κ của `refusal` = 1,000 (176 câu cả hai không `drop`) |
| `expect_ids` khớp hệt (câu cả hai gán `answer`) | 36/39 (92,3%) | không áp dụng |
| Câu cần thống nhất | **31** | **12** câu `drop` lệch (mục 4.1); còn lại chỉ khác cách viết đáp án |
| `skip` / `drop` | `skip`: A 18, B 15, cả hai 14, lệch 5 | `drop`: A 23, B 25 |

## 2. System 3: phân bố nhãn

| `beh` | A | B | Đề xuất cuối (mục 3.2) |
|---|---|---|---|
| answer | 42 | 57 | 57 |
| clarify | 9 | 8 | 7 |
| apologize | 231 | 220 | 218 |
| skip | 18 | 15 | 18 |
| Tổng | 300 | 300 | 300 |

Ma trận nhầm lẫn (hàng A, cột B; 281 câu không `skip`):

| A \ B | answer | clarify | apologize |
|---|---|---|---|
| answer | 39 | 1 | 2 |
| clarify | 5 | 3 | 1 |
| apologize | 13 | 1 | 216 |

## 3. System 3: các danh sách cần theo dõi

### 3.1 Câu bị `skip`

**Cả hai cùng `skip` (14 câu)**: loại khỏi bộ nếu bạn đồng ý.

| id | Câu hỏi (rút gọn) | Lý do (A) |
|---|---|---|
| 004 | Tôi tên [TÊN] ( SN 1968), tôi muốn hỏi quyền sử dụng của tôi trong Hộ gia đình như sau: | Cau bi cat: chi con 'quyen su dung cua toi trong ho gia dinh nhu sau:', khong co noi dung hoi. |
| 010 | Kính thưa Giám đốc sở XD Bình Định | Chi co loi chao 'Kinh thua Giam doc so XD Binh Dinh', khong co cau hoi. |
| 077 | Cho tôi hỏi, năm 2013 tôi học đại học Quy Nhơn có tham gia thi bằng lái xe A1. | Cau bi cat: 'nam 2013 toi hoc dai hoc Quy Nhon co tham gia thi bang lai xe A1.' khong co noi dung hoi. |
| 081 | Kính thưa: Sở xây dựng, Phòng Quản lý chất lượng công trình | Chi co loi chao 'Kinh thua: So xay dung, Phong Quan ly chat luong cong trinh', khong co cau hoi. |
| 089 | Kính thưa Sở Tài nguyễn và Môi trường tỉnh Bình Định ! | Chi co loi chao 'Kinh thua So Tai nguyen va Moi truong tinh Binh Dinh', khong co cau hoi. |
| 098 | Hôm nay, tôi viết câu hỏi này xin SỞ TÀI NGUYÊN MÔ …  của gia đình tôi. Sự việc như sau: | Cau bi cat: chi co phan mo dau 'Su viec nhu sau:', khong co noi dung hoi. |
| 115 | Nhà nước có cấp cho hộ gia đình tôi 1 sổ đỏ năm 19 … ửa đất ruộng ở nhiều nơi khác nhau. | Cau bi cat: chi mo ta cap so do 1997 gom 1 thua tho cu va 5 thua ruong, khong co cau hoi. |
| 134 | Tôi vừa thay đổi CMND 9 số sang CCCD 12 số. | Cau cut: chi co 'Toi vua thay doi CMND 9 so sang CCCD 12 so.' khong co noi dung hoi. |
| 143 | Nhà nước cấp cho hộ gia đình tôi 1 sổ đỏ năm 1997  … 5 thửa ruộng ở nhiều nơi khác nhau. | Cau cut: chi mo ta so do 1997 gom 1 thua tho cu va 5 thua ruong, khong co cau hoi. |
| 186 | Tôi xin hỏi tôi co sổ hồng với dt là 386,2m2. Trong đó có 40m2 đất nhà ở. | Cau cut: chi co 'toi co so hong dien tich 386,2m2, trong do 40m2 dat o', khong co cau hoi. |
| 252 | Nhà tôi có 1 lô đất nhà ở mua năm 2002 số thửa 234 … hơn Thành Thị Xã An Nhơn Bình Định. | Cau cut: chi mo ta lo dat mua 2002 (thua 234, to 20, Ly Tay), khong co cau hoi. |
| 254 | Về việc cấp sổ đỏ cho khu vực ven quốc lộ 1A cũ, t … c , huyện Hoài Nhơn, tỉnh Bình Định | Chi co tieu de 'Ve viec cap so do cho khu vuc ven quoc lo 1A cu, thon Gia An Dong', khong co cau hoi cu the. |
| 290 | tôi có đăng ký làm lý lịch tư pháp số 1 vào ngày 0 … ận được lịch hẹn là ngày 29/08/2019 | Cau cut: chi co 'toi dang ky lam LLTP so 1 ngay 08/08/2019 va nhan lich hen 29/08/2019', khong co cau hoi. |
| 294 | Ông tôi tên [TÊN] sinh năm 1892 mất 1973 và bà tôi … à nơi cư trú cuối cùng của ông bà). | Cau cut: chi mo ta ong ba, ngay sinh, mat va noi cu tru cuoi cung, khong co cau hoi. |

**Một bên `skip`, bên kia gán nhãn khác (5 câu)**:

| id | Câu hỏi (rút gọn) | A | B | Đề xuất |
|---|---|---|---|---|
| 083 | Đơn đề nghị em có cần đem lên trường cấp 3 để xác nhận | skip | clarify | skip |
| 258 | Có cách nào để em có thể xem trước bản mẫu để gửi  … việc làm cho em không ạ. Em cảm ơn. | skip | clarify | skip |
| 269 | Cho e hỏi.Cử nhân Công Nghệ Sinh học chuyên ngành  … rường Đại học Y Dược TP.Hồ Chí Minh | skip | apologize | skip |
| 289 | Kính nhờ quý cơ quan trả lời giúp nội dung như sau … à, đi lại rất khó khăn. Xin cảm ơn! | skip | clarify 1.000894, 1.004746 | clarify |
| 106 | Trước đây (trong năm 2020 và 2021), các hộ lắp điệ … à thanh toán tiền điện bình thường. | apologize | skip | skip |

Nếu theo đề xuất, số câu `skip` còn **18**; số câu thực sự dùng để chấm: **282**.

### 3.2 Câu A và B bất đồng và đề xuất nhãn cuối

31 câu. Cột **Đề xuất** là nhãn tôi đề nghị sau khi tra lại dữ liệu bản 3. Cột **Cần người quyết** đánh dấu những câu chưa chắc.

| id | Câu hỏi (rút gọn) | A | B | Đề xuất | Lý do | Cần người quyết |
|---|---|---|---|---|---|---|
| 008 | Trong lần đi công tác đến Việt … ng con dấu và thủ tục cần những gì? | clarify 1.115231, 1.115232 | apologize | **clarify** 1.115231, 1.115232 | Giữ theo A: công ty chưa rõ cần đăng ký mới hay đăng ký lại con dấu. | có |
| 035 | Trước đây tôi sống tại tỉnh Ph … ong nhận được hồi âm từ Bộ Công an. | apologize | answer 1.012566 | **answer** 1.012566 | B đúng: DB có 1.012566 (xác nhận số CMND 09 số, cấp xã). A tra sót. |  |
| 036 | Vợ chồng mình đã đăng ký kết h … hủ tục để điều chỉnh như thế nào ạ? | apologize | answer 1.012564, 1.014066 | **answer** 1.012564 | B đúng: điều chỉnh thông tin trong CSDL dân cư. Bỏ 1.014066 vì dành cho người gốc Việt. |  |
| 037 | Đất nông thôn.đất phi nông ngh … uế hằng năm.giờ e cất nhà được k ạ. | answer 1.013225 | apologize | **apologize**  | Hỏi quyền xây nhà trên đất phi nông nghiệp (pháp lý), không nêu thủ tục; theo B. | có |
| 083 | Đơn đề nghị em có cần đem lên trường cấp 3 để xác nhận | skip | clarify | **skip**  | Câu cụt, không đủ ngữ cảnh để biết thủ tục; theo A. |  |
| 101 | dạ, trường hợp em bị mất bằng  …  bị giới hạn không? em xin cảm ơn!! | apologize | answer 2.000908 | **answer** 2.000908 | B tìm ra 'Cấp bản sao từ sổ gốc'; thủ tục chung, chưa chắc áp dụng cho bằng tốt nghiệp. | có |
| 106 | Trước đây (trong năm 2020 và 2 … à thanh toán tiền điện bình thường. | apologize | skip | **skip**  | Chỉ là nhận định, không có câu hỏi; theo B. |  |
| 124 | Tôi ở huyện Trảng Bom, tỉnh Đồ … ững thủ tục và giấy tờ như thế nào? | answer 1.116410, 1.014060 | answer 1.116410, 1.012564, 1.014066 | **answer** 1.116410, 1.012564, 1.014060 | Gộp hai bên (đều hợp lý), bỏ 1.014066. |  |
| 138 | Gia đình chúng tôi được cấp mộ … úng tôi ,tôi xin cảm ơn rất nhiều . | clarify 1.012753, 1.013978 | answer 1.013978 | **answer** 1.013978 | Hộ gia đình: 1.013978 (1.012753 dành cho tổ chức); theo B. |  |
| 144 | Tôi là [TÊN] , tôi rất mong đư … nh thuộc biên chế Công an nhân dân. | apologize | answer 1.013743 | **answer** 1.013743 | B đúng: 1.013743 khớp chiến trường B,C,K 1954–1975 của công an; A gán sai 'không có thủ tục'. |  |
| 164 | Số CMND của cha tôi ghi trong  … ắc phục trường hợp này như thế nào? | apologize | answer 1.012566 | **answer** 1.012566 | B đúng: xác nhận số CMND. |  |
| 166 | Năm 1998 gia đình tôi có mua c … ua đến nay đất không có tranh chấp) | clarify 1.012753, 1.013978 | answer 1.013978 | **answer** 1.013978 | Theo B (hộ gia đình). |  |
| 191 | Mẹ ruột tôi sinh năm 1963, tên … i phải làm thế nào? Tôi xin cảm ơn. | answer 1.116410 | answer 1.012564, 1.014066, 1.116410 | **answer** 1.012564, 1.116410 | Gộp hai bên, bỏ 1.014066. |  |
| 194 | Ông bà cố nhà em có để lại tờ  … dụng đất ạ, e xin chân thành cảm ơn | clarify 1.012753, 1.013978 | answer 1.013978 | **answer** 1.013978 | Theo B (hộ gia đình). |  |
| 201 | ông [TÊN] sinh ngày 01/5/1965  … ó hồ sơ, giấy tờ cá nhân được không | clarify 1.001193, 1.004884 | answer 1.004772 | **answer** 1.004772 | B đúng: 1.004772 là 'đăng ký khai sinh cho người đã có hồ sơ, giấy tờ cá nhân'. |  |
| 214 | Tôi là Thủy, thường trú tại Qu … thủ tục sang tên thì có được không? | apologize | answer 1.115970 | **answer** 1.115970 | Theo B: thủ tục sang tên xe. | có |
| 220 | Em có chứng chỉ điểm TOEIC như …  chứng chỉ điểm TOEIC được không ạ? | apologize | answer 2.000815 | **answer** 2.000815 | Theo B: chứng thực bản sao. | có |
| 223 | Vừa qua tôi đã đến Công an quậ … rường hợp của tôi phải làm thế nào? | apologize | answer 1.012566 | **answer** 1.012566 | B đúng: xác nhận số CMND. |  |
| 230 | Tôi cư trú tại Đà Nẵng, muốn v … (Đoàn công tác khoảng 10 -15 người) | apologize | clarify 2.001159, 1.116789 | **clarify** 2.001159, 1.116789 | Theo B (thông báo lưu trú hay tạm trú); hoặc skip. | có |
| 231 | Vợ chồng tôi đăng ký tạm trú t …  hay tôi phải làm thủ tục nào khác? | apologize | answer 1.010041 | **answer** 1.010041 | Theo B: xác nhận thông tin về cư trú. | có |
| 238 | Trước đây, tôi được Công an tỉ … ào có thẩm quyền xác nhận việc này? | apologize | answer 1.012566 | **answer** 1.012566 | B đúng: xác nhận số CMND. |  |
| 244 | Tôi bị mất cmnd và đã đi đăng  … nào nhận được thẻ cccd ạ.tôi cảm ơn | answer 1.116410 | apologize | **apologize**  | Hỏi tiến độ hồ sơ cụ thể đã nộp 15/5; theo B. Câu 20 và 123 hỏi thời gian chung nên giữ answer. |  |
| 258 | Có cách nào để em có thể xem t … việc làm cho em không ạ. Em cảm ơn. | skip | clarify | **skip**  | Câu thiếu ngữ cảnh; theo A. |  |
| 261 | Tôi sinh năm 1955 không có Giấ … ược cấp Giấy khai sinh và đổi CMND? | answer 1.004884, 1.116410 | answer 1.004772 | **answer** 1.004772, 1.116410 | Gộp: khai sinh cho người đã có hồ sơ (1.004772) và đổi thẻ (1.116410). |  |
| 262 | Tôi có người bạn là người Mỹ g … tạm trú có tốn khoản phí nào không? | apologize | answer 1.000253 | **answer** 1.000253 | Theo B: Việt kiều quốc tịch Mỹ là người nước ngoài. | có |
| 267 | Tôi sinh ra và lớn lên tại tỉn …  nhận cho tôi thì tôi phải làm sao? | apologize | answer 1.012566 | **answer** 1.012566 | B đúng: xác nhận số CMND. |  |
| 269 | Cho e hỏi.Cử nhân Công Nghệ Si … rường Đại học Y Dược TP.Hồ Chí Minh | skip | apologize | **skip**  | Câu cụt, không có câu hỏi; theo A. |  |
| 273 | Hiện tại mình muốn kết hôn onl … độc thân có làm online được không ạ | answer 1.000894, 1.004873 | clarify 1.000894, 1.004873 | **clarify** 1.000894, 1.004873 | Theo B và hướng dẫn: hai việc ngang nhau trong một câu thì clarify. |  |
| 288 | Xin hỏi thửa 139 tờ bản đồ số  … i tiếc 1/2000 Nhơn Bình và nhon phu | apologize | answer 1.014159 | **answer** 1.014159 | B đúng: 1.014159 'Cung cấp thông tin quy hoạch đô thị và nông thôn'. |  |
| 289 | Kính nhờ quý cơ quan trả lời g … à, đi lại rất khó khăn. Xin cảm ơn! | skip | clarify 1.000894, 1.004746 | **clarify** 1.000894, 1.004746 | Theo B: xác nhận vợ chồng cưới 1976 chưa đăng ký. | có |
| 297 | Tôi có mua 1 lô đất 50m2 từ nă … ự nộp những cơ quan nào. Xin cảm ơn | clarify 1.012753, 1.013978 | answer 1.013978 | **answer** 1.013978 | Theo B (hộ gia đình). |  |

Trong 31 câu: 22 câu đề xuất rõ ràng, **9 câu cần người quyết**.

### 3.3 Lỗi tra cứu của lượt A

Ở 9 câu (035, 036, 144, 164, 201, 223, 238, 267, 288) A tra sót hoặc gán sai mã. Ví dụ A kết luận "DB không có thủ tục xác nhận số CMND" trong khi DB có:

| Mã | Tên thủ tục | Câu liên quan |
|---|---|---|
| 1.012566 | Xác nhận số chứng minh nhân dân 09 số, số định danh cá nhân (thực hiện tại cấp xã) | 035, 164, 223, 238, 267 |
| 1.004772 | Thủ tục đăng ký khai sinh cho người đã có hồ sơ, giấy tờ cá nhân | 201, 261 |
| 1.012564 | Điều chỉnh thông tin trong Cơ sở dữ liệu quốc gia về dân cư theo đề nghị của công dân (thực hiện tại cấp xã) | 036, 124, 191 |
| 1.014159 | Cung cấp thông tin quy hoạch đô thị và nông thôn | 288 |
| 1.013743 | Giải quyết chế độ đối với quân nhân, cán bộ đi chiến trường B,C,K trong thời kỳ chống Mỹ cứu nước không có thân nhân phả | 144 |

Nguyên nhân: tôi tìm "so cmnd" nhưng tên thủ tục viết "chứng minh nhân dân". Khi sửa A theo đề xuất, κ ban đầu (0,753) vẫn giữ làm số báo cáo.

### 3.4 Câu hai bên khớp nhau nhưng ít nhất một bên ghi "không chắc"

22 câu: 003, 011, 017, 023, 053, 064, 075, 105, 130, 131, 145, 151, 152, 157, 168, 171, 178, 247, 250, 270, 284, 298. Nên rà nhanh bằng mắt, vì khớp nhau giữa hai lượt AI chưa chắc là đúng.

## 4. System 4

### 4.1 Câu `drop`

`drop` nghĩa là bài Wikipedia hoặc bảng hiện tại làm đáp án mơ hồ hoặc đã đổi so với bộ ViQuAD, nên loại khỏi chấm. A 23 câu, B 13 câu, cả hai 12 câu, lệch 12 câu.

**12 câu lệch (A và B khác nhau)**:

| id | Câu hỏi (rút gọn) | A | B | Đề xuất | Lý do |
|---|---|---|---|---|---|
| 054 | Các thời kỳ chiến tranh tại Ph … àng bao gồm các pha chuyển động gì? | drop | refusal | **drop** | Tiền đề lệch (chiến tranh thay vì kiến tạo); loại khỏi chấm chính. |
| 059 | Hệ thống hang động đã tác động … óa vật lý và hóa học của Phong Nha? | drop | refusal | **drop** | Câu đảo ngược quan hệ, bài có nội dung liên quan nhưng không rõ. |
| 062 | Người ta phát hiện các mảnh ki … ó tráng men của Chàm ở khu vực nào? | drop | refusal | **drop** | Bài có mảnh gốm tráng men của Chăm; câu đổi thành kim loại, không rõ. |
| 063 | Tổ chức UNESCO đã ước tính với … ần một lượng thuốc nổ là bao nhiêu? | drop | refusal | **drop** | Bài có 4,5 tấn thuốc nổ/km, người ước tính là tổ chức khác; câu sai chủ thể. |
| 065 | Ai đã phát hiện ra những bằng  … linh ở khu vực Phong Nha - Kẻ Bàng? | drop | refusal | **drop** | Tiền đề lệch ('thần linh' thay vì con người). |
| 066 | Vì lí do gì mà Ủy ban đánh giá vườn quốc gia này là không cần thiết? | drop | refusal | **drop** | Bài có UNESCO cho là đường nối không cần thiết; câu sai chủ thể 'Ủy ban'. |
| 070 | Chính phủ hiện không còn ý nghĩa bảo tồn với các loài động vật nào? | refusal | drop | **drop** | B tìm ra bài có nêu hổ, voi, bò hoang dã; nhãn refusal của A là sai. |
| 071 | Các chuyên gia cho rằng thế gi … ng nhận di sản thiên nhiên lần hai? | drop | refusal | **drop** | Bài có nội dung gần (Việt Nam hoàn thiện hồ sơ); câu đổi chủ thể thành 'thế giới'. |
| 073 | Ai đã cung cấp thông tin cho K … về việc nâng cấp và bảo tồn UNESCO? | drop | refusal | **drop** | Bài có Chính phủ cung cấp thông tin cho UNESCO; sai chủ thể. |
| 074 | Tám động của hệ thống động bậc thang đổ vào dòng sông gì? | drop | refusal | **drop** | Bài có 8 động hệ thống Vòm đổ sông Chay; câu gọi nhầm 'bậc thang'. |
| b033 | liệt kê di tích đặc biệt ở Quảng Nam | drop | có đáp án | **giữ nhãn B** | Người dùng vẫn nói 'Quảng Nam'; chấp nhận Hội An, Mỹ Sơn, Đồng Dương (nay ghi Đà Nẵng) là câu trả lời đúng. |
| b039 | có mấy di tích đặc biệt thuộc loại lịch sử cách mạng | drop | có đáp án | **drop hoặc sửa câu** | 'Lịch sử cách mạng' không phải hạng mục trong bảng; bỏ hoặc sửa thành 'hạng mục Di tích lịch sử'. |

**Cả hai cùng `drop` (12 câu)**: 052, 053, 055, 056, 058, 060, 061, 064, 068, 069, 072, 075.

### 4.2 Câu `refusal` (hệ thống phải từ chối, không bịa)

A 15 câu, B 23 câu, cả hai 14 câu. Phần lệch chỉ nằm ở các câu ViQuAD của mục 4.1 (B coi là tiền đề sai nên `refusal`, A coi là mơ hồ nên `drop`). Đề xuất: không dùng chúng làm `refusal`, vì bài hiện tại có nội dung liên quan; nếu muốn, tách thành một bộ phụ "tiền đề sai" báo riêng.

### 4.3 Đáp án viết khác nhau

Script báo khoảng 60 câu `any`/`all` "khác", nhưng đọc từng câu thì **không có bất đồng thật**: B thêm biến thể ("25–30 độ", "110,476"), đổi `any` thành `all` các thành phần ("đứt gãy", "phối tảng", "uốn nếp"), hoặc dùng `num` cho câu đếm (bang-006: 19, bang-021: 71, bang-032: 22). Đề xuất: **dùng nhãn B** cho các câu này, và sửa `real_v1_agree.py` để coi hai nhãn là khớp khi giao nhau hoặc khi dùng `num`.

### 4.4 Y tế (85 câu)

`urgent` và `needs_image` khớp 100%: 10 câu `urgent` (076, 081, 085, 090, 097, 099, 112, 117, 141, 157), 2 câu `needs_image` (077, 126). Hai bên đều ghi 084 (nôn nhiều sau ăn hàu) và 114 (nhói ngực, đau nửa đầu) là ranh giới, hiện đều `urgent = false`. Bạn nên xem lại hai câu này.

### 4.5 Phần bảng (40 câu)

Khớp về ý nghĩa ở 38 câu; hai câu lệch là bang-033 và bang-039 (mục 4.1). Câu bang-040 ("thành cổ") cả hai đều thấy bảng chỉ có một dòng (Quảng Trị), nên câu định thử "mơ hồ" thực tế không mơ hồ.

### 4.6 Du lịch văn bản sau khi áp dụng đề xuất

Trong 75 câu: `drop` **22**, còn **53** câu dùng được (có đáp án 50, `refusal` 3). Lý do chính: các câu "không có đáp án" của ViQuAD2.0 phần lớn **có đáp án** trong bài Wikipedia hiện tại (bản đã cập nhật), nên không dùng được để thử "không bịa". Phần này nên coi là bộ thử đọc hiểu một bài, không phải bộ thử từ chối.

## 5. Giới hạn cần ghi vào báo cáo cuối

- Hai lượt gán nhãn đều do AI; κ 0,753 là nhất quán giữa hai lượt, không chứng minh độ đồng thuận của hai người. Nên có ít nhất một lượt kiểm của người trên một mẫu (đề xuất 60 câu System 3 và 30 câu System 4).
- Lượt A có lỗi tra cứu (mục 3.3) và đã bị lượt B phát hiện. Nhãn của một lượt AI không đủ tin; nhãn cuối phải qua bước thống nhất.
- Phần lớn câu System 3 là `apologize` (khoảng 75%). Số liệu `top-1`/`top-3` chỉ tính trên khoảng 55–65 câu `answer`, nên khoảng tin cậy rộng (khoảng ±12 điểm).
- Phần Du lịch văn bản System 4 chỉ phủ một bài Wikipedia và khoảng một nửa số câu bị loại do bài đã đổi.
- Câu `answer` dồn về thẻ căn cước (`1.116410`) và đăng ký thường trú (`1.116788`); báo cáo cần nêu rõ.

## 6. Đề xuất

**Việc nên làm theo thứ tự:**

1. **Duyệt bảng 3.2** (31 câu). 22 câu đề xuất rõ, bạn chỉ cần đồng ý; **9 câu cần người quyết** (008, 037, 101, 214, 220, 230, 231, 262, 289), cần bạn nhìn câu hỏi gốc.
2. **Duyệt danh sách `skip`** (mục 3.1): 14 câu cả hai cùng loại và 5 câu lệch.
3. **Duyệt 12 câu `drop` lệch của System 4** (mục 4.1) và quyết định có giữ bộ phụ "tiền đề sai" hay không.
4. **Rà 22 câu "không chắc"** (mục 3.4) bằng mắt.
5. **Sửa `real_v1_agree.py`**: `any` tính khớp khi giao nhau, thêm so `num`, để tỷ lệ khớp System 4 phản ánh đúng (hiện báo 75,5% thấp giả).
6. **Sinh file nhãn cuối** từ nhãn A, B và quyết định của bạn (`eval/real_v1/real_v1_labels_final.json` và bản System 4), ghi lý do vào `eval/real_v1/REAL_V1_ASSUMPTIONS.md`. Tôi làm bước này ngay khi bạn duyệt xong.
7. **Khoá bộ nhãn** (không sửa theo kết quả hệ thống), rồi mới chạy hệ thống trên bộ này.

**Nếu có thêm thời gian:**

- Một lượt kiểm của người trên mẫu (mục 5) để có con số độ đồng thuận có người tham gia.
- Cập nhật `PLAN_EVAL_REAL_V1_NGAY1.md` và `REAL_V1_GUIDE.md`: Du lịch văn bản còn khoảng 53 câu dùng được, System 3 còn khoảng 282 câu sau `skip`.
- Thêm vào hướng dẫn gán nhãn: khi tra thủ tục, thử cả tên viết khác (ví dụ "CMND" và "chứng minh nhân dân"), để tránh lỗi mục 3.3.

## 7. Trạng thái sau khi duyệt (21/10)

| Mục đề xuất (mục 6) | Trạng thái |
|---|---|
| 1. Duyệt bảng 3.2 (31 câu, gồm 9 câu cần người quyết) | **Đã duyệt theo đề xuất** |
| 2. Duyệt danh sách `skip` | **Đã đồng ý** (18 câu `skip`) |
| 3. Duyệt 12 câu `drop` lệch của System 4 | **Đã duyệt theo đề xuất** |
| 4. Rà 22 câu "không chắc" | **Đã rà, không chắc chắn nên làm theo đề xuất** (chưa kiểm sâu) |
| 5. Sửa `real_v1_agree.py` | Đã làm (`any`/`all`/`num` khớp khi giao nhau; đáp án System 4 khớp 176/176) |
| 6. Sinh file nhãn cuối | Đã sinh: `eval/real_v1/real_v1_labels_final.json`, `system4/eval/real_v1/real_v1_s4_labels_final.json`, `eval/real_v1/REAL_V1_ASSUMPTIONS.md`; chưa khoá |
| 7. Khoá bộ nhãn, rồi chạy hệ thống | **Đã khoá ngày 21/10** (`eval/real_v1/LOCK.md`, `system4/eval/real_v1/LOCK.md`); chưa chạy hệ thống |

**Cập nhật 21/10, kiểm sâu 22 câu:** Claude rà lại từng câu bằng nội dung thủ tục (xem cuối `eval/real_v1/REAL_V1_ASSUMPTIONS.md`): giữ 18 câu, sửa 4 câu: 105 và 247 (đổi thẻ khi đủ tuổi: từ `answer` sang `apologize`, vì là câu hỏi quy định), 145 (thêm mã 1.004884), 131 (đổi mã sang thủ tục cấp đổi của tỉnh). Phân bố cuối System 3 sau sửa: 55 `answer`, 7 `clarify`, 220 `apologize`, 18 `skip`. Đây vẫn là lượt rà của AI, chưa có người kiểm.

Các file đã dồn vào hai thư mục `eval/real_v1/` và `system4/eval/real_v1/`; đường dẫn trong báo cáo này đã cập nhật.

# Kết quả chạy System 3 trên bộ real_v1 (một lần, luật, không GPU)

Bộ: `eval/real_v1/cases_real_v1_labeled.json` (282 câu; mã băm trong `eval/real_v1/LOCK.md`). Cấu hình: `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`, DB thủ tục bản 3 (1.517 thủ tục).

## 1. Chỉ số chính

| Chỉ số | Kết quả |
|---|---|
| Hành vi đúng (cả 282 câu) | 158/282 (56.0%; 95% CI 50.2% đến 61.7%) |
| Top-1 (câu `answer`) | 7/55 (12.7%; 95% CI 6.3% đến 24.0%) |
| Top-3 (câu `answer`) | 12/55 (21.8%; 95% CI 12.9% đến 34.4%) |
| MRR (câu `answer`, tối đa 6 ứng viên) | 0.227 |
| Recall `answer` (hệ thống ra đúng hành vi khi nhãn là `answer`) | 41/55 (74.5%; 95% CI 61.7% đến 84.2%) |
| Recall `clarify` (hệ thống ra đúng hành vi khi nhãn là `clarify`) | 1/7 (14.3%; 95% CI 2.6% đến 51.3%) |
| Recall `apologize` (hệ thống ra đúng hành vi khi nhãn là `apologize`) | 116/220 (52.7%; 95% CI 46.1% đến 59.2%) |

## 2. Ma trận nhầm lẫn (hàng: nhãn, cột: hệ thống)

| nhãn \ hệ thống | answer | clarify | apologize |
|---|---|---|---|
| answer | 41 | 1 | 13 |
| clarify | 3 | 1 | 3 |
| apologize | 101 | 3 | 116 |

Ở 104/220 câu mà nhãn là `apologize`, hệ thống vẫn trả lời hoặc hỏi lại thay vì từ chối: nó từ chối đúng chưa tới 53% các câu ngoài phạm vi (luật, xử phạt, khiếu nại, tình trạng hồ sơ).

## 3. Theo tầng lấy mẫu

| Tầng | Số câu | Hành vi đúng | Câu `answer` | Top-1 | Top-3 |
|---|---|---|---|---|---|
| random | 111 | 63/111 (56.8%; 95% CI 47.5% đến 65.6%) | 13 | 2/13 (15.4%; 95% CI 4.3% đến 42.2%) | 3/13 (23.1%; 95% CI 8.2% đến 50.3%) |
| chude | 171 | 95/171 (55.6%; 95% CI 48.1% đến 62.8%) | 42 | 5/42 (11.9%; 95% CI 5.2% đến 25.0%) | 9/42 (21.4%; 95% CI 11.7% đến 35.9%) |

## 4. Mọi câu sai

159 câu (hành vi sai, hoặc nhãn `answer` mà mã đầu không đúng).

| id | Nhãn | Hệ thống | Mã đúng | Mã hệ thống chọn | Câu hỏi (rút gọn) |
|---|---|---|---|---|---|
| 001 | apologize | answer |  | 1.012922, 1.115406 | Tôi đang tham gia giao thông trên đường bằng xe máy, tô … g tham gia giao thông như tôi? |
| 002 | apologize | answer |  | 1.115406 | Khi Cảnh sát giao thông lập chốt xử lý vi phạm giao thô … ng và xử phạt mức như thế nào? |
| 003 | apologize | answer |  | 1.115406, 1.010092 | Tôi công tác trên 15 năm trong lực lượng Công an nhân d …  thì quy định tại văn bản nào? |
| 005 | apologize | answer |  | 1.115406 | Bộ Công an cho tôi hỏi, người điều khiển xe gắn máy uốn … ng độ cồn có bị xử phạt không? |
| 006 | apologize | answer |  | 1.013142, 1.115406 | Tôi là sỹ quan Công an, cấp hàm Thiếu tá nghiệp vụ, thờ …  sẽ được nhận những chế độ gì? |
| 008 | clarify | apologize | 1.115231, 1.115232 | - | Trong lần đi công tác đến Việt Nam, giám đốc công ty ch … n dấu và thủ tục cần những gì? |
| 012 | apologize | answer |  | 1.115406 | Vừa rồi, bạn tôi lái ô tô bị lực lượng Cảnh sát giao th … ào thì bị tạm giữ phương tiện? |
| 013 | apologize | answer |  | 1.115406 | Tôi thấy nhiều vụ cháy có nguyên nhân từ việc người dân … i đốt sẽ bị xử lý như thế nào? |
| 016 | apologize | answer |  | 1.010811 | Điều dưỡng trung cấp còn làm chứng chỉ hành nghề không ạ |
| 017 | apologize | answer |  | 2.000884 | Bản sao chứng thực điện tử trực tuyến có thể in để sử d … điện tử. Xin chân thành cảm ơn |
| 019 | apologize | answer |  | 1.010805 | Tôi là [TÊN] ở xã Nam Sơn, huyện An Dương, TP. Hải Phòn … p đồng trong Công an nhân dân? |
| 020 | answer | answer | 1.116410 | 1.115406, 3.000285 | Tôi ở Thanh Hóa, tôi làm thủ tục để cấp mới thẻ Căn cướ … c thẻ CCCD là bao nhiêu ngày ? |
| 021 | apologize | answer |  | 1.014318 | Cháu là [TÊN] , hiện tại cháu đang học lớp 12, trường T … họn công dân vào CAND thế nào? |
| 023 | answer | apologize | 1.115970 | - | Tôi muốn làm lại biển số xe máy lần 2 do di chuyển trên … mọi người hướng dẫn để làm lại |
| 024 | apologize | answer |  | 1.115406 | Tôi tham gia nghĩa vụ Công an nhân dân tháng 3/2018 và  …  trong Công an nhân dân không? |
| 025 | apologize | answer |  | 1.004680 | Thực tế tôi thấy, nhiều trường hợp nhờ xách, tr …  tại sân bay, bến tàu, bến xe? |
| 029 | apologize | answer |  | 1.012538 | Hiện nay, tình trạng người dân sử dụng vũ khí tự chế, c … hí tự chế, công cụ hỗ trợ này. |
| 033 | apologize | answer |  | 1.116843 | Trường hợp Con Tôi không đi học các cấp học phổ thông ( … thế nào và cơ quan nào thụ lý. |
| 035 | answer | answer | 1.012566 | 1.116788, 1.012680 | Trước đây tôi sống tại tỉnh Phú Thọ và được Công an Phú … hận được hồi âm từ Bộ Công an. |
| 036 | answer | answer | 1.012564 | 1.000894, 1.004873 | Vợ chồng mình đã đăng ký kết hôn và có giấy chứng nhận  … c để điều chỉnh như thế nào ạ? |
| 037 | apologize | answer |  | 1.011607 | Đất nông thôn.đất phi nông nghiệp.có đóng thuế hằng năm.giờ e cất nhà được k ạ. |
| 039 | apologize | answer |  | 2.000992 | Giấy xác nhận thời gian thực hành chuyên môn của em do  … nghề dược ở Bình Định không ạ? |
| 041 | apologize | answer |  | 2.000992 | tôi đã có chứng chỉ hành nghề Điều dưỡng hệ Cao đẳng và … hành là bao nhiêu tháng không? |
| 045 | apologize | answer |  | 1.115406 | Cháu đang là học sinh THPT tại tỉnh Phú Thọ, cháu có ng … ột trong các hệ đào tạo không? |
| 046 | apologize | answer |  | 1.004327 | Tôi muốn hỏi, tại sao phải xây dựng lực lượng Công an x …  bố trí công việc như thế nào? |
| 049 | apologize | answer |  | 1.115406 | Gần đây, trên mạng xã hội xuất hiện nhiều đoạn clip ghi … ên sẽ bị xử phạt như thế nào ? |
| 051 | apologize | answer |  | 1.116847 | Tôi đã gửi hồ sơ sau khi đăng ký trực tuyến và bên bưu  … in nhắn yêu cầu gửi hồ sơ tiếp |
| 053 | answer | answer | 1.116410 | 1.115406 | Tôi là cán bộ trong ngành Công an, hiệnđang công tác tạ … hải chuẩn bị những giấy tờ gì? |
| 055 | apologize | answer |  | 1.013798, 6.003494 | Trong 1 ubnd cấp xã, có 2 đồng chí công chức phụ trách  … gì. Phối hợp xử lý như thế nào |
| 058 | apologize | answer |  | 1.115406, 1.014312 | Bộ Công an cho tôi hỏi, tháng 4 tôi được tạm tuyển vào  … hiểm để hưởng chế độ thai sản? |
| 060 | apologize | answer |  | 1.013161, 1.115406 | Chế độ nghỉ phép đối với cán bộ CAND được hướng dẫn tại … i 15 ngày làm việc) hay không? |
| 061 | apologize | answer |  | 1.115979 | Cho em hỏi giấy phép lái xe của em bị mất và em có đến  … ó hẹn ngày 3/72023 trả kết quả |
| 063 | answer | answer | 1.116410 | 1.012566 | Tôi có hộ khẩu tại Bắc Ninh và đã làm Chứng minh nhân d … dân có gắn chíp thì làm ở đâu? |
| 069 | apologize | answer |  | 1.115406, 2.002165 | Bộ Công an cho tôi hỏi, hành vi chống người thi hành cô … không và bị xử lý như thế nào? |
| 070 | apologize | answer |  | 1.004327 | Cử tri đề nghị Bộ Công an trang cấp phương tiện, vũ khí …  ninh, trật tự an toàn xã hội. |
| 073 | apologize | answer |  | 2.000755 | Theo Pháp lệnh Công an xã năm 2008, tại khoản 3, Điều 1 … hính đáng là nghỉ như thế nào? |
| 074 | apologize | answer |  | 3.000122 | Bạn đọc [TÊN] , địa chỉ số 1489 Nguyễn Văn Linh, Quận 7 … cần phải làm những thủ tục gì? |
| 075 | answer | answer | 1.115970 | 1.115406, 1.115970 | Tôi có chiếc xe ô tô 5 chỗ, khi tham gia giao thông, tô … ấp lại biển số xe như thế nào? |
| 078 | apologize | answer |  | 1.004327 | Hiện nay, chế độ tiền lương, biên chế đối với lực lượng …  xã và lực lượng Công an viên. |
| 079 | answer | answer | 2.000635 | 1.000689 | Vợ tôi sinh năm 1988, khai sinh tại xã Mỹ Lộc, huyện Ph … hủ tục làm như nào. Xin cám ơn |
| 084 | apologize | answer |  | 1.012753, 1.115750 | Theo Căn cứ Quyết định số 52/2018/QĐ-UBND ngày 07/12/20 … nào? Xin chân thành cảm ơn../. |
| 088 | apologize | answer |  | 1.013133 | Cử tri đề nghị tăng mức phụ cấp cho công dân thực hiện  … lý, đề nghị Nhà nước quan tâm. |
| 090 | apologize | answer |  | 3.000228 | Tôi muốn hỏi về số hồ sơ căn cước công dân gắn chíp? Tô … 021 nhưng tới giờ chưa có CCCD |
| 093 | apologize | answer |  | 1.012888 | Vụ cháy xảy ra tại địa chỉ số 1, hẻm 31, ngách 98, ngõ  … ạn an toàn khi có cháy xảy ra? |
| 097 | apologize | answer |  | 2.002165, 1.014451 | Tình trạng vi phạm pháp luật, coi thường kỷ cương, côn  …  lượng thi hành từng nhiệm vụ. |
| 100 | apologize | answer |  | 2.001396 | Số hồ sơ của em là 000.00.13.H[ID] . E có tra cứu đã ho … cking không ạ . E xin cảm ơn . |
| 101 | answer | answer | 2.000908 | 1.116556 | dạ, trường hợp em bị mất bằng tốt nghiệp cấp 3 bản gốc. … iới hạn không? em xin cảm ơn!! |
| 103 | apologize | answer |  | 1.004837 | Cha tôi đứng tên chủ quyền sử dụng thửa đất (sở hữu riê … hạm pháp luật nào. Xin cảm ơn! |
| 105 | apologize | answer |  | 3.000228, 1.115406 | Tôi năm nay 38 tuổi, hiện nay, tôi muốn làm thẻ Căn cướ …  lại thẻ CCCDcó mã vạch không? |
| 108 | answer | apologize | 1.116410 | - | nhờ cơ quan chức năng cho mình xin cách làm lại CCCD của mình |
| 109 | apologize | answer |  | 1.012566 | Cho tôi hỏi, CMND còn thời hạn sử dụng có còn giá trị hay không |
| 111 | answer | answer | 1.116410 | 1.014060 | Tôi đang công tác trong ngành Công an và có hộ khẩu tập … rường hợp của tôi như thế nào? |
| 112 | apologize | answer |  | 1.115406 | Tôi là cán bộ đang công tác tại Trại tạm giam, thâm niê …  bộ chuyên môn kỹ thuật không? |
| 113 | apologize | answer |  | 1.115406 | Khu chung cư của gia đình tôi đang sống có trang bị hệ  … o để dập đám cháy có hiệu quả? |
| 116 | apologize | answer |  | 1.004335 | Hiện nay, tình trạng cho vay nặng lãi, tín dụng đen, cá … vi vi phạm pháp luật nêu trên? |
| 118 | apologize | answer |  | 6.001690 | Cử tri kiến nghị, theo quy định về độ tuổi đổi thẻ Căn  … ổi phải đổi thẻ theo quy định. |
| 120 | apologize | answer |  | 1.116788 | Tại dự thảo Luật Cư trú sửa đổi có quy định về việc tha … g, bảo hiểm, đăng ký kết hôn…? |
| 122 | apologize | answer |  | 1.014200 | Bộ Công an cho tôi hỏi: - Hiện tại, Thẻ tạm trú ở công  … cho người lao động nước ngoài? |
| 123 | answer | clarify | 1.116410 | 1.116410 | Thẻ căn cước công dân làm trong bao lâu mới có ạ. E làm …  để làm hồ sơ thi tốt nghiệp ạ |
| 124 | answer | answer | 1.116410, 1.012564, 1.014060 | 1.115406 | Tôi ở huyện Trảng Bom, tỉnh Đồng Nai, tôi muốn sửa lại  … hủ tục và giấy tờ như thế nào? |
| 125 | answer | answer | 1.116410 | 3.000228 | Hiện tại em không có hộ khẩu, hộ khẩu gia đình vợ em cầ … nh em không giữ).em xin cảm ơn |
| 129 | apologize | answer |  | 2.002820 | Xin chào anh chị, em muốn nộp đơn xin giấy Lý Lịch Tư P … nh. Em xin cảm ơn rất nhiều ạ. |
| 131 | clarify | answer | 1.115931, 1.116767 | 1.115626 | Tôi có sổ đỏ năm 1994 gia hạn năm 2008 hiện đã hết thời …  ở và vườn, đổi, cấp lại sổ đỏ |
| 132 | apologize | answer |  | 1.013962 | Hiện nay tôi đang làm công chức Tư pháp xã An Toàn, huy … nh cho công dân. Xin cảm ơn./. |
| 133 | apologize | answer |  | 1.010825 | Sau khi đăng kí online lý lịch tư pháp số 1 và có tin n … n, BĐ." Thì bổ sung giấy tờ gì |
| 136 | apologize | answer |  | 1.115406, 2.000821 | Trước khi được tuyển dụng vào lực lượng Công an nhân dâ … y định cụ thể tại văn bản nào? |
| 137 | apologize | answer |  | 1.115406, 1.115979 | Hiện nay, tôi đang sử dụng giấy phép lái xe hạng A1 do  … ì thủ tục đăng ký như thế nào? |
| 138 | answer | answer | 1.013978 | 1.115625 | Gia đình chúng tôi được cấp một thửa đất lâm nghiệp tro … ôi ,tôi xin cảm ơn rất nhiều . |
| 141 | apologize | answer |  | 1.116411 | Mặc dù Luật Căn cước công dân đã có những quy định chun … ệu quốc gia trên các lĩnh vực. |
| 142 | apologize | answer |  | 2.002080, 1.012566 | Dạ em có gửi hồ sơ lý lịch tư pháp online với số hồ sơ  … bao lâu thì được ạ, e cảm ơn ạ |
| 144 | answer | answer | 1.013743 | 1.116556, 1.013163 | Tôi là [TÊN] , tôi rất mong được Bộ Công an hướng dẫn t … uộc biên chế Công an nhân dân. |
| 145 | answer | apologize | 2.000635, 1.004884 | - | Tôi có con bị mất giấy khai sinh nhờ hỗ trợ quy trình c … khai sinh cho con dưới 12 tuổi |
| 146 | apologize | answer |  | 1.014193 | Cử tri đề nghị sớm có văn bản hướng dẫn thực hiện Nghị  …  hiểm xã hội và Bảo hiểm y tế. |
| 149 | apologize | answer |  | 2.002516 | Tôi có nộp hồ sơ online để yêu cầu cấp phiếu lý lịch tư …  sơ của tôi là 000.00.13.H[ID] |
| 152 | answer | answer | 1.116410 | 1.116413 | Tôi sinh năm 1940, từng có 11 năm tham gia chiến trường …  Căn cước công dân được không? |
| 153 | apologize | answer |  | 2.002303 | Dạ cho em hỏi là em học dược cao đẳng ở trường Cao đẳng … chỉ hành nghề có được không ạ! |
| 156 | apologize | clarify |  | 1.115406 | Sau những vụ án nghiêm trọng liên quan đến trẻ em như v … những vụ án đau lòng như trên? |
| 157 | answer | apologize | 1.116789 | - | Tôi có sổ hộ khẩu thường trú tại tổ dân phố Hạnh, Tây M … lời tôi như vậy có đúng không? |
| 158 | apologize | answer |  | 1.115406 | Bộ Công an cho tôi hỏi, những trường hợp nào sẽ bị xử p … y định cụ thể tại văn bản nào? |
| 159 | apologize | answer |  | 3.000722, 3.000228 | Em có làm cccd ở TP Đà Nẵng, hiện em đã được cấp mã địn …  lý nhưng đến nay vẫn chưa có. |
| 160 | apologize | answer |  | 1.012538 | Anh tôi hiện là Cảnh sát giao thông. Năm 2014, trong th … g hay chỉ là mất sức lao động? |
| 161 | apologize | answer |  | 1.115406 | Tôi kinh doanh đồ chơi trẻ em, vừa qua cơ quan chức năn … y định cụ thể tại văn bản nào? |
| 163 | apologize | answer |  | 1.001939, 1.115406 | Tôi xuất ngũ tháng 11/2019, trong khi thẻ Bảo hiểm y tế … ư thời hạn trên thẻ hay không? |
| 164 | answer | apologize | 1.012566 | - | Số CMND của cha tôi ghi trong Giấy khai sinh của tôi kh … ục trường hợp này như thế nào? |
| 166 | answer | answer | 1.013978 | 1.012812 | Năm 1998 gia đình tôi có mua của ông [TÊN] 1 thửa đất b … n nay đất không có tranh chấp) |
| 167 | apologize | answer |  | 1.010814, 1.012566 | Bác tôi sinh ngày 10/4/1946, đã làm giấy chứng minh nhâ … lại không có ngày, tháng sinh. |
| 168 | apologize | answer |  | 1.004873, 1.000894 | Xin chào Dịch vụ công cấp tỉnh Bình Định. Tôi có nộp hồ … y xác nhận độc thân. Kính gửi. |
| 169 | apologize | answer |  | 1.115406 | Tôi và rất nhiều người thân, quen, hàng xóm xung quanh  …  nào để truy cập vào ứng dụng? |
| 171 | answer | answer | 1.116788 | 1.116789 | Tôi đăng ký tạm trú tại phường 25,quận Bình Thạnh, thàn … ng và căn cứ vào quy định nào? |
| 173 | apologize | answer |  | 1.003677, 1.115406 | Trong công tác đấu tranh phòng, chống tội phạm mua bán  … ép được thực hiện như thế nào? |
| 174 | apologize | answer |  | 2.002080 | Ngày 06/11/2023, mình có đăng kí làm hồ sơ lý lịch tư p … n TP HCM gửi về HCC Bình Định. |
| 176 | apologize | answer |  | 1.116839, 1.115406 | Gia đình tôi được Ủy ban nhân dân phường ra Quyết định  … được quy định tại văn bản nào? |
| 179 | answer | answer | 1.116410 | 1.115406, 3.000228 | Tôi đang sống và làm việc tại Hà Nội nhưng hộ khẩu thườ … hải chuẩn bị những giấy tờ gì? |
| 180 | apologize | answer |  | 1.014193 | Kiến nghị Bộ Công an phối hợp với Bảo hiểm xã hội Việt  … ) khi đi khám, chữa bệnh BHYT. |
| 182 | apologize | answer |  | 1.012533, 1.115406 | Lễ hội là nét đẹp của văn hoá Việt Nam. Tuy nhiên, nhiề …  đối với các hành vi này chưa? |
| 184 | apologize | answer |  | 5.003887 | Tôi có hoàn thành nộp hồ sơ online xin cấp phiếu lý lịc …  này giúp tôi. Tôi xin cảm ơn. |
| 187 | apologize | answer |  | 1.012566 | Chào các anh chị, tình hình là ngày 15/11/2021 em có ra … úp em hoàn thiện được không ạ? |
| 191 | answer | answer | 1.012564, 1.116410 | 1.001193 | Mẹ ruột tôi sinh năm 1963, tên trong khai sinh là: [TÊN … i làm thế nào? Tôi xin cảm ơn. |
| 193 | answer | answer | 1.116788 | 1.115406, 1.116788 | Vợ chồng tôi làm việc ở Hà Nội đã được 6 năm, hiện nay  … cần phải làm những thủ tục gì? |
| 194 | answer | answer | 1.013978 | 1.115750 | Ông bà cố nhà em có để lại tờ giấy viết tay vào năm 200 … đất ạ, e xin chân thành cảm ơn |
| 196 | answer | apologize | 1.002759 | - | Xin cho tôi hỏi : Đổi tên ngành nghề trong sổ BHXH từ k … à bao nhiêu ngày. Xin cảm ơn ! |
| 199 | answer | answer | 1.116788 | 1.116789 | Tôi ở TP. Hồ Chí Minh được gần 2 năm theo sổ đăng ký tạ … n thủ tục, trình tự nhập khẩu. |
| 201 | answer | answer | 1.004772 | 3.000285, 1.004772 | ông [TÊN] sinh ngày 01/5/1965 có tất cả các hồ sơ như:  … sơ, giấy tờ cá nhân được không |
| 202 | apologize | answer |  | 1.115406 | Tôi được biết, dự án Sản xuất, cấp, quản lý căn cước cô … ộng của từngcá nhân hay không? |
| 203 | apologize | answer |  | 1.012566 | Triển khai cấp số định danh cá nhân là điều mà mọi công … h cá nhân toàn quốc hay không? |
| 209 | apologize | answer |  | 2.000635 | Ngày 12/9/2023 tôi có nộp hồ sơ trích lục hộ tịch với s …  cần bổ sung nội dung gì không |
| 210 | apologize | answer |  | 1.010803, 1.014632 | Mẹ tôi tên [TÊN] hưởng chế độ chính sách thương binh hạ … nhà ở cho người có công không? |
| 212 | apologize | answer |  | 1.116788 | Cử tri nêu bất cập khi thực hiện Luật Cư trú năm 2020,  … xem xét, có giải pháp tháo gỡ. |
| 213 | apologize | answer |  | 1.116789 | Theo Luật Tạm trú, tạm vắng quy định thì người đi làm ă … uan đế nhân thân của công dân. |
| 214 | answer | answer | 1.115970 | 1.116788 | Tôi là Thủy, thường trú tại Quận 2, TP Hồ Chí Minh. Tôi … ục sang tên thì có được không? |
| 215 | apologize | answer |  | 1.115406 | Năm nay tôi 53 tuổi, công tác tại Công an huyện Tân Thạ … c, hy sinh, từ trần hay không? |
| 216 | apologize | answer |  | 1.115960, 3.000182 | Mình ra trường năm 2006, trúng tuyển trong đợt xét tuyể … g được phản hồi ạ. Xin cảm ơn! |
| 219 | clarify | apologize | 1.116525, 1.115743 | - | Tôi muốn chuyển đổi một phần diện tích đất liền kề nhà  … àm những thủ tục như thế nào ? |
| 220 | answer | apologize | 2.000815 | - | Em có chứng chỉ điểm TOEIC nhưng đã hết hạn, em muốn hỏ … g chỉ điểm TOEIC được không ạ? |
| 223 | answer | answer | 1.012566 | 1.116410 | Vừa qua tôi đã đến Công an quận để làm thẻ Căn cước côn …  hợp của tôi phải làm thế nào? |
| 224 | apologize | answer |  | 2.000992 | Cho mình hỏi mình có chứng chỉ hành nghề điều dưỡng đượ …  lý lịch tư pháp rồi ạh cảm ơn |
| 226 | apologize | answer |  | 3.000228, 2.000605 | Theo luật căn cước công dân thì huyện mình bao giờ làm  … trên .em xin cảm ơn các cán bộ |
| 228 | answer | answer | 1.004884 | 1.001193, 1.004884 | tôi sinh ở Bình Định năm 1977 và làm giấy khai sinh lúc … tôi phải liên hệ ở đâu? Cảm ơn |
| 230 | clarify | apologize | 2.001159, 1.116789 | - | Tôi cư trú tại Đà Nẵng, muốn vào công tác tại TP Quy Nh …  công tác khoảng 10 -15 người) |
| 231 | answer | answer | 1.010041 | 1.116789, 1.001193 | Vợ chồng tôi đăng ký tạm trú tại huyện Nhà Bè, TP Hồ Ch … tôi phải làm thủ tục nào khác? |
| 233 | apologize | answer |  | 1.003005, 2.000806 | Hiện nay, tệ nạn mua bán người diễn ra ngày càng phức t … việc phòng ngừa mua bán người? |
| 236 | apologize | answer |  | 1.115406, 3.000323 | Gia đình tôi có cho một người hàng xóm vay 400 triệu đồ …  ở đâu và thủ tục như thế nào? |
| 244 | apologize | clarify |  | 3.000285 | Tôi bị mất cmnd và đã đi đăng ký cấp cccd gắn chíp từ n … hận được thẻ cccd ạ.tôi cảm ơn |
| 245 | apologize | clarify |  | 1.115406 | Gần nhà tôicó một trang trại gà.Với mục đích bảo vệ đàn … sẽ bị xử mức phạt như thế nào? |
| 246 | apologize | answer |  | 1.001613 | Tính chất công việc của Công an viên khắt khe về thời g …  hiểm y tế và bảo hiểm xã hội. |
| 247 | apologize | answer |  | 1.116410, 1.115406 | Tôi năm nay 61 tuổi, đã làm thẻ Căn cước công dân (CCCD … CCD có gắn chíp điện tử không? |
| 248 | apologize | answer |  | 6.001690 | Tôi là nữ, 45 tuổi, hiện đang công tác trong ngành Công … bao nhiêu phần trăm lương hưu? |
| 250 | answer | answer | 1.115971 | 1.115406 | Năm 2013, tôi có bán 01 chiếc xe máy, lúc bán tôi không …  nữa thì tôi phải làm thế nào? |
| 251 | answer | apologize | 1.116788 | - | Tôi đang ở chung nhà cùng em trai tôi tại quận Tân Bình … u có thì cần những thủ tục gì? |
| 253 | apologize | answer |  | 2.000950, 1.012538 | Bố tôi trước đây là Công an viên, nay được lên làm Trưở … i có công với cách mạng không? |
| 255 | apologize | answer |  | 1.013962 | Đề nghị có văn bản hướng dẫn thực hiện cụ thể nội dung: … lại không quy định vấn đề này. |
| 256 | apologize | answer |  | 1.115406 | Thời gian gần đây, nhiều vụ mua bán người và xâm hại tì … loại tội phạm này như thế nào? |
| 257 | apologize | answer |  | 1.013978, 1.001632 | Xin hỏi khi có quyền sử dụng đất đai sổ đỏ muốn chuyển  … ày phải giải quyết như thế nào |
| 259 | apologize | answer |  | 2.000821, 1.115406 | Tôi vào ngành Công an năm 1979, công tác tại Đội Cảnh s … n đóng bảo hiểm sau này không? |
| 260 | apologize | answer |  | 1.012817 | Ba tôi có làm thủ tục Đính Chính số chứng minh nhân dân … h với số tiền: 1.200.000 đồng. |
| 261 | answer | answer | 1.004772, 1.116410 | 2.000635 | Tôi sinh năm 1955 không có Giấy khai sinh, trong Chứng  … ấp Giấy khai sinh và đổi CMND? |
| 262 | answer | answer | 1.000253 | 1.005040, 1.116789 | Tôi có người bạn là người Mỹ gốc Việt. Hiện bạn tôi đan … rú có tốn khoản phí nào không? |
| 266 | apologize | answer |  | 1.115406 | Thời gian qua, tôi được biết tình trạng cản trở, chống  … phạt hay mức phạt như thế nào? |
| 267 | answer | answer | 1.012566 | 1.116788 | Tôi sinh ra và lớn lên tại tỉnh Hải Dương, được Công an …  cho tôi thì tôi phải làm sao? |
| 268 | apologize | answer |  | 1.115406 | Tôi được biết, thẻ Căn cước công dân có thể thay thế hộ …  chiếu trên lãnh thổ của nhau? |
| 270 | answer | apologize | 1.004859 | - | Tôi làm thủ tục đổi chữ lót của họ tên thì bị từ chối.T …  VNEID của Bộ công an là được. |
| 271 | apologize | answer |  | 1.115406 | Tôi thấy việc cấp thẻ Căn cước công dân (CCCD) hiện nay … ã vạch và Chứng minh nhân dân? |
| 272 | apologize | answer |  | 2.000755 | Tôi sinh năm 1956, công tác trong lực lượng Công an nhâ … hi đủ tuổi về hưu như thế nào? |
| 273 | clarify | answer | 1.000894, 1.004873 | 1.000894, 1.004873 | Hiện tại mình muốn kết hôn online trên dịch vụ công đượ … hân có làm online được không ạ |
| 277 | apologize | answer |  | 1.012537 | Hiện nay, việc quy định về hồ sơ, thủ tục xác định ngườ … i trong vụ tai nạn giao thông. |
| 278 | answer | apologize | 1.116788 | - | Hiện tôi có hộ khẩu thường trú tại thành phố Lào Cai, h …  tôi cần làm những thủ tục gì? |
| 281 | apologize | answer |  | 1.115406 | Trong những năm gần đây tôi thấy, nhiều nhóm người ở nư … ANTT) sẽ bị xử lý như thế nào? |
| 282 | answer | answer | 3.000285, 3.000286 | 1.115406, 3.000285 | Ngày hôm nay, Luật Căn cước đã chính thức có hiệu lực t …  điện tử được mở khóa trở lại? |
| 283 | apologize | answer |  | 1.115406 | Hiện nay, mạng Internet ngày càng phát triển, lợi dụng  … c thì sẽ bị xử lý như thế nào? |
| 287 | answer | apologize | 1.004859 | - | Hiện tại thì giấy khai sinh của mình bị sai tên cha ..  … àm lại đc giấy khai sinh k ạ ) |
| 288 | answer | answer | 1.014159 | 1.116768 | Xin hỏi thửa 139 tờ bản đồ số 8 vướng quy hoạch gì.sao  … c 1/2000 Nhơn Bình và nhon phu |
| 289 | clarify | answer | 1.000894, 1.004746 | 1.000894 | Kính nhờ quý cơ quan trả lời giúp nội dung như sau: Ba  …  lại rất khó khăn. Xin cảm ơn! |
| 291 | answer | answer | 1.116410 | 3.000285, 1.012566 | Tôi chưa về làm cccd được,và chứng minh nhân dân cũ bị mất thì giờ về làm như thế nào ạ |
| 292 | apologize | answer |  | 1.014193 | Chế độ, chính sách đối với Trưởng Công an xã, Phó trưởn … văn bản nào quy định việc này? |
| 293 | apologize | answer |  | 1.116788 | Hiện nay, thủ tục hành chính trong một số lĩnh vực quản … ĩnh vực để dân đỡ phải đi lại. |
| 296 | answer | answer | 1.116410 | 1.115406, 1.116410 | Tôi năm nay 24 tuổi, có hộ khẩu ở Kon Tum và sổ tạm trú … Hồ Chí Minh thì có được không? |
| 297 | answer | apologize | 1.013978 | - | Tôi có mua 1 lô đất 50m2 từ năm 1993 viết giấy tay. Nay …  những cơ quan nào. Xin cảm ơn |
| 298 | answer | answer | 1.116788 | 1.115406 | Tôi sinh con vào tháng 11/2021, sau khi sinh con tôi mớ … ục gì để nhập hộ khẩu cho con? |
| 300 | answer | apologize | 1.116410 | - | Cho e hỏi e muốn làm cccd thì bắt buộc chủ hộ phải làm  … rong hộ mới làm được hay sao ạ |

## 5. Cần nhớ khi đọc

- Nhãn do hai lượt AI gán (κ 0,753), chưa có lượt kiểm của người trên mẫu.
- Chỉ có 55 câu `answer`; khoảng tin cậy top-1 rộng.
- Bộ này là câu hỏi thật của người dân (Cổng dịch vụ công Bình Định, Bộ Công an): phần lớn là luật, xử phạt, khiếu nại, tình trạng hồ sơ; khác hẳn các bộ do nhóm soạn.
- Chạy chế độ luật, không LLM; không phản ánh bản người dùng thấy (có LLM).
- Lần chạy đầu (22/10) dùng nhầm DB cũ `data/runtime/system3.db` (1.350 thủ tục, bản 1) vì thiếu biến `S3_DATA_DB`; kết quả bị bỏ (lưu ở `KHONG_DUNG_lan_dau_sai_DB.json`, hành vi 161/282, top-1 3/55). Lần này chạy lại đúng DB bản 3, không đổi gì khác; không chỉnh hệ thống hay nhãn giữa hai lần.

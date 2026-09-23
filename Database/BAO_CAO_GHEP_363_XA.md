<!-- Sinh tự động bằng: python -m Database.pipeline.match_xa — đừng sửa tay -->

# Báo cáo ghép 363 thủ tục cấp Xã (TP.HCM) với Cổng DVCQG

**Nguồn yêu cầu:** `THU_TUC_CAP_XA_363.csv` — cột *Xã* trong Phụ lục Quyết định **113/QĐ-UBND** (TP.HCM, 2025).
*TP.HCM gọi **Phường** là cấp **Xã** — cùng một cấp.*

Văn bản của Thành phố **chỉ có tên thủ tục, không có mã TTHC**, nên bắt buộc phải ghép bằng tên. Bảng dưới ghi rõ mức tin cậy của từng thủ tục.

## Tổng hợp

| Mức | Nghĩa | Số lượng |
|---|---|---|
| `exact` | tên trùng khít | **220** |
| `high` | khác vài chữ, nhận tự động (≥ 0.9) | **72** |
| `review` | giống nhưng CHƯA CHẮC (≥ 0.78) — cần người xem lại | **27** |
| `absent` | **không có trên Cổng DVCQG** | **44** |
| | **Tổng** | **363** |

→ Nạp được vào CSDL: **319/363** thủ tục, trong đó **295** mã khác nhau (24 tên CSV trỏ trùng vào mã đã có).

## ⚠️ Nhóm `absent` — không phải lỗi ghép

Đã tra thẳng bằng API tìm kiếm của chính cổng (tham số `q`) cho nhóm này: **trả về 0 kết quả**. Nghĩa là cổng `dichvucong.gov.vn` thật sự không có các thủ tục đó trong tập dữ liệu dịch vụ công.

Phần lớn là giấy phép kinh doanh có điều kiện do cấp xã/phường cấp (rượu, thuốc lá, LPG chai…). Muốn có thì phải lấy từ nguồn khác — Cơ sở dữ liệu quốc gia về TTHC, hoặc trang dịch vụ công của TP.HCM.

| STT | Tên trong quyết định | Gần nhất tìm được | Điểm |
|---|---|---|---|
| 1 | Thủ tục cấp Giấy phép sản xuất rượu thủ công nhằm mục đích kinh doanh | Cấp giấy phép nhập khẩu sản phẩm xử lý chất thải chăn nuôi có chứa chấ | 0.66 |
| 2 | Thủ tục cấp sửa đổi, bổ sung Giấy phép sản xuất rượu thủ công nhằm mục đích kinh doanh | Cấp giấy phép nhập khẩu sản phẩm xử lý chất thải chăn nuôi có chứa chấ | 0.514 |
| 3 | Thủ tục cấp lại Giấy phép sản xuất rượu thủ công nhằm mục đích kinh doanh | Cấp giấy phép nhập khẩu sản phẩm xử lý chất thải chăn nuôi có chứa chấ | 0.621 |
| 4 | Thủ tục cấp Giấy phép bán lẻ rượu | Cấp lại Giấy phép lập cơ sở bán lẻ | 0.598 |
| 5 | Thủ tục cấp sửa đổi, bổ sung Giấy phép bán lẻ rượu | Thủ tục sửa đổi, bổ sung Giấy phép của tổ chức tín dụng phi ngân hàng  | 0.717 |
| 6 | Thủ tục cấp lại Giấy phép bán lẻ rượu | Cấp lại Giấy phép lập cơ sở bán lẻ | 0.643 |
| 9 | Thủ tục cấp lại Giấy phép bán lẻ sản phẩm thuốc lá | Cấp Giấy phép kinh doanh cho tổ chức kinh tế có vốn đầu tư nước ngoài  | 0.722 |
| 13 | Thủ tục cấp Giấy chứng nhận đủ điều kiện cửa hàng bán lẻ LPG chai | Cấp Giấy chứng nhận đủ điều kiện sản xuất, sửa chữa chai LPG | 0.716 |
| 14 | Thủ tục cấp lại Giấy chứng nhận đủ điều kiện cửa hàng bán lẻ LPG chai | Cấp lại Giấy chứng nhận đủ điều kiện sản xuất chai LPG mini | 0.731 |
| 15 | Cấp điều chỉnh Giấy chứng nhận đủ điều kiện cửa hàng bán lẻ LPG chai | Cấp lại Giấy chứng nhận đủ điều kiện sản xuất chai LPG mini | 0.69 |
| 16 | Cấp Giấy chứng nhận sản phẩm công nghiệp nông thôn tiêu biểu cấp huyện | Phê duyệt dự án, kế hoạch liên kết trong các ngành, nghề, lĩnh vực khá | 0.505 |
| 35 | Tiếp nhận học sinh trung học cơ sở người nước ngoài | Tiếp nhận học sinh người nước ngoài | 0.777 |
| 63 | Cho phép trung tâm học tập cộng đồng hoạt động trở lại | Thành lập hoặc cho phép thành lập trung tâm học tập cộng đồng | 0.769 |
| 66 | Thành lập lớp dành cho người khuyết tật trong trường mầm non, trường tiểu học, trường trung học  | Đề nghị hỗ trợ chi phí học tập trong cơ sở giáo dục mầm non dân lập, t | 0.587 |
| 89 | Hỗ trợ dự án liên kết (cấp huyện) | Hỗ trợ dự án liên kết (cấp xã) | 0.676 |
| 110 | Lập biên bản kiểm tra hiện trường xác định nguyên nhân, mức độ thiệt hại rừng trồng | Kiểm tra hiện trường rừng trồng bị thiệt hại | 0.524 |
| 112 | Quyết định thu hồi rừng đối với hộ gia đình, cá nhân và cộng đồng dân cư tự nguyện trả lại rừng | Thẩm định, phê duyệt hoặc điều chỉnh phương án nuôi, trồng phát triển, | 0.646 |
| 115 | Xác nhận Hợp đồng tiếp cận nguồn gen và chia sẻ lợi ích (cấp xã) | Hỗ trợ đầu tư xây dựng phát triển thủy lợi nhỏ, thuỷ lợi nội đồng và t | 0.392 |
| 118 | Phê duyệt phương án bảo vệ đập, hồ chứa nước trên địa bàn do Ủy ban nhân dân cấp tỉnh phân cấp | Thẩm định, phê duyệt phương án bảo vệ đập, hồ chứa thủy điện thuộc thẩ | 0.765 |
| 126 | Tổ chức phát động học tập tấm gương trong phạm vi cả nước đối với trường hợp hy sinh, bị thương  | Đăng ký biến động đối với trường hợp thay đổi quyền sử dụng đất, quyền | 0.37 |
| 140 | Vay vốn hỗ trợ tạo việc làm, duy trì và mở rộng việc làm từ Quỹ quốc gia về việc làm đối với ngư | Chi trả kinh phí hỗ trợ người sử dụng lao động đào tạo, bồi dưỡng, nân | 0.575 |
| 141 | Vay vốn hỗ trợ tạo việc làm, duy trì và mở rộng việc làm từ Quỹ quốc gia về việc làm đối với cơ  | Thủ tục giải quyết chế độ hưu trí đối với quân nhân, người làm công tá | 0.514 |
| 142 | Thủ tục tặng, truy tặng "Huy chương Thanh niên xung phong vẻ vang" cho cá nhân theo công trạng. | Thủ tục tặng, truy tặng "Huy chương Thanh niên xung phong vẻ vang" | 0.768 |
| 224 | Thanh lý tài sản kết cấu hạ tầng thủy lợi; xử lý tài sản kết cấu hạ tầng thủy lợi trong trường h | Thủ tục: Xử lý tài sản kết cấu hạ tầng đường thủy nội địa | 0.577 |
| 225 | Kê khai, thẩm định tờ khai phí bảo vệ môi trường đối với nước thải | Thủ tục khai, nộp phí bảo vệ môi trường đối với khí thải | 0.691 |
| 263 | Thủ tục Đăng ký khai sinh cho trẻ em sinh ra do mang thai hộ | Thủ tục đăng ký khai sinh cho trẻ em sinh ra ở nước ngoài và có quốc t | 0.71 |
| 268 | Thủ tục Bầu hòa giải viên | Thủ tục chấp thuận danh sách dự kiến những người được bầu, bổ nhiệm là | 0.628 |
| 270 | Thủ tục Bầu Tổ trưởng Tổ hòa giải | Thủ tục công nhận tổ trưởng tổ hòa giải (cấp xã) | 0.637 |
| 287 | thủ tục công nhận câu lạc bộ thể thao cơ sở (thẩm quyền CT UBND cấp xã) | Thủ tục công nhận câu lạc bộ thể dục thể thao cơ sở | 0.572 |
| 288 | Cấm tiếp xúc theo Quyết định của Chủ tịch Ủy ban nhân dân cấp xã (Chủ tịch Ủy ban nhân dân cấp h | Thủ tục cấm tiếp xúc theo Quyết định của Chủ tịch Ủy ban nhân dân cấp  | 0.759 |
| 295 | Thẩm định thiết kế xây dựng triển khai sau thiết kế cơ sở/thiết kế xây dựng triển khai sau thiết | Hỗ trợ dự án sản xuất sản phẩm công nghệ số trọng điểm; dự án nghiên c | 0.645 |
| 303 | Cung cấp thông tin về quy hoạch xây dựng thuộc thẩm quyền của UBND cấp huyện | Đắk Lắk - Cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản  | 0.541 |
| 304 | Thẩm định nhiệm vụ, nhiệm vụ điều chỉnh quy hoạch chi tiết của dự án đầu tư xây dựng công trình  | Đăng ký biến động thay đổi quyền sử dụng đất, quyền sở hữu tài sản gắn | 0.581 |
| 305 | Thẩm định đồ án, đồ án điều chỉnh quy hoạch chi tiết của dự án đầu tư xây dựng công trình theo h | Đăng ký biến động thay đổi quyền sử dụng đất, quyền sở hữu tài sản gắn | 0.701 |
| 316 | Gia hạn hoạt động cảng, bến thủy nội địa | Công bố đóng cảng, bến thủy nội địa, khu neo đậu | 0.743 |
| 317 | Thỏa thuận nâng cấp bến thủy nội địa thành cảng thủy nội địa | Công bố đóng cảng, bến thủy nội địa, khu neo đậu | 0.635 |
| 324 | Thỏa thuận thông số kỹ thuật xây dựng bến thủy nội địa | Cho ý kiến về sự phù hợp quy hoạch và thông số kỹ thuật xây dựng bến t | 0.771 |
| 335 | Cấp giấy chứng sinh đối với trường hợp trẻ được sinh ra ngoài cơ sở khám bệnh, chữa bệnh nhưng đ | Đăng ký biến động đối với trường hợp thay đổi quyền sử dụng đất, quyền | 0.436 |
| 336 | Đăng ký hoạt động đối với cơ sở trợ giúp xã hội dưới 10 đối tượng có hoàn cảnh khó khăn | Tiếp nhận đối tượng bảo trợ xã hội có hoàn cảnh đặc biệt khó khăn vào  | 0.682 |
| 337 | Thủ tục hỗ trợ chi phí khuyến khích hỏa táng (TTHC đặc thù của TP do UBNDTP công bố) | Hỗ trợ chi phí khuyến khích sử dụng hình thức hỏa táng | 0.434 |
| 343 | Thực hiện, điều chỉnh, tạm dừng, thôi hưởng trợ cấp sinh hoạt hàng tháng đối với nghệ nhân nhân  | Thủ tục thôi hưởng trợ cấp sinh hoạt hàng tháng, bảo hiểm y tế đối với | 0.488 |
| 344 | Hỗ trợ chi phí mai táng đối với nghệ nhân nhân dân, nghệ nhân ưu tú có thu nhập thấp, hoàn cảnh  | Thủ tục hỗ trợ một (01) lần đối với các nghệ sĩ, nghệ nhân được Nhà  | 0.444 |
| 358 | Thủ tục xử lý đơn tại cấp xã | Xử lý hóa đơn điện tử đã lập sai/Xử lý chứng từ điện tử đã lập sai | 0.684 |
| 360 | Thủ tục tiếp nhận yêu cầu giải trình | Giải quyết yêu cầu bồi thường tại cơ quan trực tiếp quản lý người thi  | 0.776 |

## Nhóm `review` — nạp vào rồi, nhưng nên kiểm lại bằng mắt

| STT | Tên trong quyết định | Mã | Tên trên cổng | Điểm |
|---|---|---|---|---|
| 71 | Chuyển đổi cơ sở giáo dục mầm non bán công sang cơ sở giáo dục mầm non côn | `1.014313` | Hỗ trợ kinh phí đối với cơ sở giáo dục mầm non độc lập dân lập, tư thục ở  | 0.898 |
| 326 | Công bố hoạt động bến thủy nội địa | `1.115949` | Công bố đóng cảng, bến thủy nội địa, khu neo đậu | 0.897 |
| 359 | Thủ tục kê khai tài sản, thu nhập | `1.007674` | Khai thuế thu nhập cá nhân đối với cá nhân có thu nhập từ chuyển nhượng bấ | 0.895 |
| 280 | Chứng thực việc sửa đổi, bổ sung, hủy bỏ hợp đồng, giao dịch | `2.000913` | Chứng thực việc sửa đổi, bổ sung, hủy bỏ giao dịch | 0.889 |
| 356 | Thủ tục giải quyết khiếu nại lần đầu cấp xã | `1.013554` | Thủ tục giải quyết đơn khiếu nại lần đầu cấp Bộ Quốc phòng | 0.889 |
| 107 | Quyết định chuyển mục đích sử dụng rừng sang mục đích khác đối với cá nhân | `1.012694` | Chuyển mục đích sử dụng rừng sang mục đích khác đối với cá nhân | 0.881 |
| 281 | Sửa lỗi sai sót trong hợp đồng, giao dịch | `2.000927` | Sửa lỗi sai sót trong giao dịch | 0.875 |
| 101 | Đăng ký khai thác, sử dụng nước dưới đất | `1.001662` | Đăng ký khai thác nước dưới đất | 0.863 |
| 283 | Chứng thực văn bản thỏa thuận phân chia di sản mà di sản là động sản, quyề | `2.001406` | Chứng thực văn bản phân chia di sản mà di sản là động sản, quyền sử dụng đ | 0.862 |
| 325 | Thỏa thuận thông số kỹ thuật xây dựng bến khách ngang sông, bến thủy nội đ | `1.009453` | Cho ý kiến về thông số kỹ thuật xây dựng bến khách ngang sông, kết cấu hạ  | 0.861 |
| 222 | Quyết định xác lập quyền sở hữu toàn dân đối với tài sản là di sản không c | `3.000410` | Quyết định xác lập quyền sở hữu toàn dân đối với tài sản không có người th | 0.856 |
| 45 | Cho phép trường tiểu học hoạt động giáo dục trở lại | `5.003847` | Cho phép trường phổ thông dân tộc nội trú hoạt động giáo dục trở lại
(Đối  | 0.851 |
| 315 | Đổi tên cảng, bến thủy nội địa, khu neo đậu | `1.115949` | Công bố đóng cảng, bến thủy nội địa, khu neo đậu | 0.845 |
| 54 | Cho phép cơ sở giáo dục mầm non độc lập hoạt động giáo dục trở lại | `1.012971` | Thành lập hoặc cho phép thành lập cơ sở giáo dục mầm non độc lập | 0.83 |
| 149 | Thủ tục chia, tách; sát nhập; hợp nhất hội. | `1.013707` | Chia, tách; sáp nhập; hợp nhất hội | 0.83 |
| 223 | Giao tài sản kết cấu hạ tầng thủy lợi | `6.006764` | Giao quản lý tài sản kết cấu hạ tầng đường thủy nội địa | 0.825 |
| 33 | Chuyển trường đối với học sinh trung học cơ sở | `1.003702` | Hỗ trợ học tập đối với trẻ mẫu giáo, học sinh tiểu học, học sinh trung học | 0.818 |
| 328 | Công bố lại hoạt động bến thủy nội địa | `1.115949` | Công bố đóng cảng, bến thủy nội địa, khu neo đậu | 0.812 |
| 151 | Thủ tục cho phép của Bộ Nội vụ hội hoạt động trở lại sau khi bị đình chỉ c | `1.013709` | Cho phép hội hoạt động trở lại sau khi bị đình chỉ có thời hạn | 0.807 |
| 17 | Giao tài sản kết cấu hạ tầng chợ do cấp huyện quản lý | `1.012568` | Giao tài sản kết cấu hạ tầng chợ do cấp xã quản lý | 0.801 |
| 32 | Thủ tục chuyển trường đối với học sinh tiểu học | `1.003702` | Hỗ trợ học tập đối với trẻ mẫu giáo, học sinh tiểu học, học sinh trung học | 0.801 |
| 41 | Giải thể trường mẫu giáo, trường mầm non, nhà trẻ (Theo đề nghị của tổ chứ | `1.012974` | Giải thể cơ sở giáo dục mầm non độc lập (theo đề nghị của tổ chức, cá nhân | 0.801 |
| 7 | Thủ tục cấp Giấy phép bán lẻ sản phẩm thuốc lá | `2.000362` | Cấp Giấy phép kinh doanh cho tổ chức kinh tế có vốn đầu tư nước ngoài để t | 0.799 |
| 34 | Tiếp nhận học sinh trung học cơ sở Việt Nam về nước | `2.002855` | 	Tiếp nhận học sinh Việt Nam từ nước ngoài về nước | 0.794 |
| 125 | Phê duyệt kế hoạch khuyến nông địa phương (cấp xã) | `1.012535` | Phê duyệt dự án, kế hoạch liên kết thực hiện các hoạt động hỗ trợ
phát tri | 0.792 |
| 8 | Thủ tục cấp sửa đổi, bổ sung Giấy phép bán lẻ sản phẩm thuốc lá | `2.000218` | Cấp sửa đổi, bổ sung Giấy phép sản xuất sản phẩm thuốc lá | 0.787 |
| 103 | Gia hạn thời hạn giao khu vực biển cho cá nhân Việt Nam để nuôi trồng thủy | `3.000439` | Giao khu vực biển cho cá nhân Việt Nam để nuôi trồng thủy sản | 0.786 |

## Tên CSV trỏ trùng vào cùng một mã

| STT | Tên trong quyết định | Trỏ vào mã |
|---|---|---|
| 33 | Chuyển trường đối với học sinh trung học cơ sở | `1.003702` |
| 40 | Cho phép trường mẫu giáo, trường mầm non, nhà trẻ hoạt động giáo dục trở lại | `2.002894` |
| 50 | Cho phép trường trung học cơ sở, trường phổ thông có nhiều cấp học có cấp học cao nhất là  | `1.012965` |
| 54 | Cho phép cơ sở giáo dục mầm non độc lập hoạt động giáo dục trở lại | `1.012971` |
| 67 | Giải thể cơ sở giáo dục mầm non độc lập (theo đề nghị của tổ chức, cá nhân thành lập trườn | `1.012974` |
| 70 | Chuyển đổi cơ sở giáo dục mầm non bán công sang cơ sở giáo dục mầm non dân lập | `1.008951` |
| 72 | Hỗ trợ học tập đối với trẻ mẫu giáo, học sinh tiểu học, học sinh trung học cơ sở, sinh viê | `1.003702` |
| 103 | Gia hạn thời hạn giao khu vực biển cho cá nhân Việt Nam để nuôi trồng thủy sản | `3.000439` |
| 167 | Công nhận và giải quyết chế độ ưu đãi người hoạt động cách mạng. | `1.010815` |
| 196 | Dừng thực hiện thủ tục đăng ký tổ hợp tác | `2.002643` |
| 197 | Dừng thực hiện thủ tục giải thể hợp tác xã, liên hiệp hợp tác xã | `2.002643` |
| 199 | Hiệu đính, cập nhật, bổ sung thông tin đăng ký hợp tác xã, liên hiệp hợp tác xã | `2.002648` |
| 201 | Hiệu đính, cập nhật, bổ sung thông tin đăng ký chi nhánh, văn phòng đại diện, địa điểm kin | `2.002648` |
| 203 | Đăng ký hoạt động chi nhánh, văn phòng đại diện, thông báo địa điểm kinh doanh | `2.002123` |
| 209 | Thông báo tạm ngừng kinh doanh/ tiếp tục kinh doanh trở lại đối với hợp tác xã, liên hiệp  | `2.002641` |
| 210 | Cấp lại Giấy chứng nhận đăng ký hợp tác xã, Giấy chứng nhận đăng ký hoạt động chi nhánh, v | `2.002638` |
| 261 | Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định hộ tịch | `1.004859` |
| 284 | Chứng thực văn bản khai nhận di sản mà di sản là động sản, quyền sử dụng đất, nhà ở | `2.001406` |
| 293 | Cấp lại giấy chứng nhận đủ điều kiện hoạt động điểm cung cấp dịch vụ trò chơi điện tử công | `1.013792` |
| 318 | Công bố đóng cảng, bến thủy nội địa | `1.115949` |
| 322 | Cấp lại Giấy chứng nhận đăng ký phương tiện hoạt động vui chơi, giải trí dưới nước | `2.001212` |
| 323 | Xóa đăng ký phương tiện hoạt động vui chơi, giải trí dưới nước | `2.001211` |
| 326 | Công bố hoạt động bến thủy nội địa | `1.115949` |
| 328 | Công bố lại hoạt động bến thủy nội địa | `1.115949` |

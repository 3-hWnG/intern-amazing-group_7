# Kế hoạch xử lý feedback của leader ("So close, a little more.pdf")

Nguồn: file PDF một trang "Feedback cho sản phẩm ông Hưng". Leader ghi rõ mình chưa blackbox test kỹ và có thể nói sai vài chỗ, nên mỗi mục dưới đây đều có bước "tái hiện trước khi sửa".

## 0. Trạng thái từng ý trong PDF

| Ý trong PDF | Quyết định | Ghi chú |
|---|---|---|
| I.1 Bỏ nút ẩn domain | **Không làm: giữ nút "×"** | Đã bàn với leader và chốt giữ |
| I.2 File chữ thuần "chết" | Làm (mục 3) | |
| I.3 Lựa chọn MCQ không trả lời được | Làm (mục 5) | Leader ghi "tạm thời chưa sửa" |
| I.4 Chuyển dataset vào domain manager | Làm (mục 4) | |
| I.5 Bỏ dataset từng domain dưới settings | Làm cùng mục 4 | |
| I.6 Đổi "domain" thành "lĩnh vực" | **Đã xong** | Nút, modal, form, thông báo lỗi |
| I.7 Lưu prompt + đáp án khi 👍/👎 | Làm (mục 2) | |
| I.8 Trí nhớ mặc định "Chỉ khi tôi bảo 'hãy nhớ'" | Làm (mục 1) | |
| II "Có bao nhiêu thủ tục giá 20k" | Làm bản hẹp, cần xác nhận (mục 6) | |
| III ý 1: TP.HCM = HCM city | **Không đưa vào kế hoạch** | Chưa thống nhất với leader, giữ quan điểm "vẫn chạy" |
| III ý 2: gợi ý không trả lời được từ dữ liệu | Làm (mục 5) | |

### Kết quả thực hiện

| Mục | Trạng thái | Ghi chú |
|---|---|---|
| 1 Trí nhớ mặc định | Xong | `MEMORY_DEFAULT_MODE = explicit`; người đã chọn riêng giữ nguyên |
| 2 Lưu 👍/👎 kèm nội dung | Xong | bảng `feedback_log` (cả Friendly và Strict), `GET /s4/admin/feedback`; chưa có nút xuất trên trang Quản trị |
| 3 File chữ thuần | Sửa một phần | tải file chữ lên chạy được; lỗi thật là câu hỏi tổng quát ("tóm tắt file") không có đoạn nào nên AI không có gì để trả lời, đã thêm đường dự phòng. Câu hỏi sự kiện bị loại do ngưỡng reranker (-3,24 so với -3,0) chưa sửa |
| 4 Dataset vào trình quản lý lĩnh vực | Xong | kiểm trên giao diện thật; chưa thử tải vào lĩnh vực cứng "Thủ tục" |
| 5 Nút gợi ý theo dữ liệu | Xong (Friendly) | lọc nút bằng một lần reranker, thêm khoảng 3 giây mỗi lượt hỏi lại; cài đặt `CHOICE_CHECK`; chưa làm "hỏi tỉnh có trong dữ liệu" |
| 6 Đếm / liệt kê theo phí | Xong | `server/fee_query.py`, test `fee_query_test.py`; xem chú ý dưới |

Chú ý mục 6: trong 537 thủ tục hệ thống trả lời được, chỉ 45 có số tiền rõ nên "giá 20k" ra 2 thủ tục; "miễn phí" ghi rõ ở 5 thủ tục (31 thủ tục chỉ miễn theo đối tượng); 883/1.350 thủ tục không có phí trong nguồn, không được hiểu là miễn phí. Cột `amount_value` có lỗi đọc "20.000" thành 20 ở khoảng 31 thủ tục; `fee_query` đối chiếu lại với `amount_text`, nhưng cột gốc trong DB vẫn sai (sửa ở `data/build.py` là việc riêng).

## 1. Trí nhớ mặc định = "Chỉ khi tôi bảo 'hãy nhớ'"

- Việc: đổi giá trị mặc định của cài đặt trí nhớ, kèm dòng giải thích ngắn trong giao diện.
- Cần kiểm tra: người dùng cũ đã có giá trị lưu thì giữ nguyên, chỉ người dùng mới nhận mặc định mới.
- Nghiệm thu: tài khoản mới mở cài đặt thấy đúng lựa chọn này; hỏi bình thường không sinh bản ghi trí nhớ; nói "hãy nhớ ..." thì có.
- Công sức: nhỏ.

## 2. Lưu prompt + đáp án khi bấm 👍/👎

- Bước đầu: xem hiện trạng. Leader hỏi "đã implement hay chỉ làm counter"; cần đọc code để trả lời đúng.
- Việc: khi bấm, ghi một bản ghi gồm câu hỏi (kèm các lượt trước nếu cần để hiểu), câu trả lời, lĩnh vực, nhãn 👍/👎, thời gian, chế độ (Strict/Friendly). Đổi ý (👍 sang 👎) thì cập nhật bản ghi, không tạo bản ghi trùng.
- Phạm vi: chỉ lưu cục bộ. Chưa làm bước fine-tune, chỉ cần có dữ liệu để sau dùng.
- Lưu ý riêng tư: bản ghi chứa nội dung người dùng. Việc che thông tin cá nhân đã nằm trong danh sách hoãn cho bản cuối; ghi rõ ở đây để không quên.
- Nghiệm thu: bấm 👍 và 👎 trên hai câu, kiểm tra DB có đúng hai bản ghi với nội dung khớp; bấm lại không tạo trùng.
- Công sức: nhỏ đến vừa.

## 3. File chữ thuần tải lên bị "chết"

- Bước đầu: tái hiện bằng chính file "Kế hoạch tuần tới.pdf" và một file `.txt`/`.md` thuần chữ; ghi lại lỗi cụ thể (không đọc được, không có bản ghi, hay có bản ghi nhưng tìm không ra). Chưa đoán nguyên nhân.
- Hướng sửa dự kiến, tùy kết quả tái hiện: file không phải bảng thì chia theo đoạn/mục (khoảng vài trăm ký tự, có tiêu đề gần nhất đi kèm) và mỗi đoạn là một bản ghi để tìm kiếm như dữ liệu thường.
- Nghiệm thu: tải file chữ lên, hỏi một câu có đáp án nằm trong file, nhận câu trả lời đúng kèm nguồn; file bảng cũ vẫn hoạt động như trước.
- Công sức: vừa. Làm trước mục 4 vì cả hai đụng vào luồng tải file.

## 4. Dataset theo lĩnh vực vào trình quản lý lĩnh vực

- Việc: đưa việc tải/xem/xóa dataset của từng lĩnh vực vào cửa sổ "Lĩnh vực"; bỏ ô dataset riêng nằm dưới phần cài đặt.
- Cần giữ nguyên: lĩnh vực cứng/mềm, khóa, ghim, rào chắn; dataset người dùng tải lên vẫn gắn đúng lĩnh vực.
- Nghiệm thu: tạo lĩnh vực mới, tải dataset, hỏi được; xóa dataset thì không còn trả lời từ nó; phần cài đặt không còn ô dataset; kiểm tra bằng JS thật trên giao diện (tăng version `app.js` và `s4.css`).
- Công sức: vừa.

## 5. Lựa chọn gợi ý (MCQ) phải trả lời được từ dữ liệu

- Hiện trạng đã xác minh trong code: các nút `choices` ở chế độ nhanh do LLM tự sinh trong JSON (`system4/server/chat.py`, tối đa 4 nút), không lấy từ dữ liệu. Riêng nhánh `ambig.py` (nhiều mục cùng khớp) lấy tiêu đề từ bản ghi thật nên đã đúng ý leader.
- Hướng làm: mỗi lựa chọn do LLM sinh phải qua một lượt tìm kiếm (`search.py`); nút nào không tìm ra bản ghi khớp đủ tốt thì bỏ. Nếu còn ít hơn 2 nút thì rơi về cách `ambig.py` hoặc hỏi lại bằng chữ.
- Luồng leader mô tả (không biết tỉnh nào, hỏi tỉnh có trong dữ liệu, rồi trả lời): lấy danh sách giá trị thật của cột tương ứng từ dữ liệu để làm nút, không để LLM bịa.
- Cần đo: độ trễ tăng thêm (tối đa khoảng 4 lượt tìm kiếm mỗi câu có nút) và tỷ lệ nút bị loại.
- Nghiệm thu: lấy 30 câu hỏi có nút, bấm từng nút, đếm tỷ lệ nút cho ra câu trả lời có nội dung (mục tiêu: 100% sau lọc, vì nút không đạt đã bị bỏ).
- Công sức: vừa đến lớn. Làm sau cùng trong nhóm sửa lỗi vì ảnh hưởng đường trả lời chung.

## 6. "Có bao nhiêu thủ tục giá 20k"

- Hiện trạng: hệ thống chưa có truy vấn đếm/lọc theo cột phí; Strict chỉ tìm và đọc từng bản ghi. Leader thử và nhận lại "thủ tục chưa rõ chi phí".
- Bước đầu: tái hiện câu đó, xem hệ thống đang làm gì (cách hiện tại "tạm bợ" ra sao) và phân biệt ba trường hợp: phí đúng 20.000đ, phí khác, và phí chưa có trong dữ liệu.
- Bản hẹp đề xuất, chỉ cho dataset thủ tục: nhận ra mẫu "bao nhiêu thủ tục ... giá/phí X", lọc cột phí bằng truy vấn SQLite, đếm, trả số đếm kèm vài ví dụ, và nói rõ có bao nhiêu thủ tục không có thông tin phí (không tính vào số đếm).
- Chưa làm: lọc tổng quát nhiều điều kiện; mở rộng sang dataset người dùng tải lên.
- **Cần chốt trước khi làm**: có làm bản hẹp này không. Đây là tính năng mới, tốn nhiều công hơn các mục còn lại. Liên quan tới việc "liệt kê theo lĩnh vực chỉ đúng 12%" đã ghi trong `docs/PLAN_TUAN_TOI.md` mục 3; hai việc dùng chung nền truy vấn có cấu trúc.
- Nghiệm thu: bộ câu hỏi đếm có đáp án tính tay từ DB (ít nhất 10 câu, đủ mức phí khác nhau); số đếm khớp tuyệt đối.
- Công sức: lớn.

## Thứ tự và kiểm chứng

1. Mục 1 và 2 (nhỏ, độc lập).
2. Mục 3, rồi mục 4 (cùng luồng tải file).
3. Mục 5.
4. Mục 6 nếu được xác nhận.

Sau mỗi mục: chạy các bài test liên quan trong `docs/CONTRIBUTING.md`, và `eval/run_all --quick` để chắc không làm tụt chất lượng Strict (hiện 27/33, 6 ca lỗi từ commit retrieval `b7a7b9f`, không liên quan các mục trên). Với mục giao diện, kiểm tra trên giao diện thật sau khi khởi động lại server 8301 và nạp lại cứng trang.

## Ghi nhận thêm

- Leader thừa nhận chưa blackbox test kỹ; trước khi sửa mỗi mục, tái hiện được lỗi hay không là điều kiện bắt buộc. Nếu không tái hiện được thì ghi lại và báo lại, không sửa mò.
- Ý "TP.HCM = HCM city" không nằm trong kế hoạch. Nếu cần có bằng chứng khi trao đổi lại, có thể chạy thử một ca trên dữ liệu thật; việc đó không đổi code.

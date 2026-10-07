# Vấn đề đã biết

Mỗi mục có người chịu trách nhiệm quyết định. Cập nhật khi đóng.

## Bộ test 10 câu của nhóm (`eval/cases_team.json`): 8/10

| Ca | Tình trạng | Quyết định |
|---|---|---|
| TC02 | Đã pass (Phase 23d): lệ phí khai sinh "bản sao 8.000đ" lấy từ corpus nhóm, ghi nguồn "Bộ dữ liệu nhóm". | Đóng. |
| TC03 | Fail có chủ ý: câu hỏi chỉ về **giấy tờ** nhưng đáp án nhóm đòi "7 ngày". Theo định nghĩa concise (hỏi gì trả đó) hệ thống chỉ trả hồ sơ. | **Đáp án nhóm cần sửa** (bỏ "7 ngày" hoặc sửa câu hỏi thành có hỏi thời hạn). Không đổi quy tắc concise. Chờ nhóm xác nhận. |
| TC06 | Fail: hệ thống trả đúng thủ tục khai tử, một task, không `steps`, và nói thật "cổng không công bố riêng phần điều kiện này". Đáp án nhóm đòi nhắc "nơi cư trú cuối cùng / nơi tổ chức tang lễ". Ý đó có trong giấy tờ phải xuất trình (xác định thẩm quyền theo nơi cư trú cuối cùng của người chết) nhưng bị cắt khỏi bản tóm tắt. | Chưa sửa. Cách làm không gian lận: khi người dùng nêu điều kiện về **nơi**, đưa đoạn giấy tờ liên quan nơi cư trú ra đầu `components` (cần Phase riêng, không tune theo câu test). Người chịu trách nhiệm: Nhân. |

## Bản cuối cho người dùng thường (Phase 25, chưa build)
| Mục | Tình trạng | Quyết định / người chịu trách nhiệm |
|---|---|---|
| plan/trace/`/config`/`?dev=1` chưa chặn theo dev (B2) | mở; mọi thứ là developer mode | Nhân (2026-10-07): làm bản đầy đủ trước, **không được để quên**; danh sách và thẻ `FINAL-PRODUCT:` ở [FINAL_PRODUCT_CHECKLIST.md](FINAL_PRODUCT_CHECKLIST.md) |
| CCCD/SĐT chưa che trong `messages`, `plan_json`, tên hộp thoại, `session_facts` (B3) | mở | như trên |
| phiên ẩn danh, "Xóa tất cả" xóa của mọi người (B4) | mở | như trên |
| công tắc AI cho người dùng thường | chưa quyết | nhóm quyết trước bản cuối (nhóm đã chốt: bật mặc định, giữ công tắc) |

## Bộ nhớ người dùng (Phase 26)
| Mục | Tình trạng | Quyết định / người chịu trách nhiệm |
|---|---|---|
| lưu theo `client_id` tự khai, chưa có tài khoản; 'default' dùng chung khi thiếu header | mở, có chủ ý | Nhân: gắn tài khoản ở bản cuối (mục 6 của [FINAL_PRODUCT_CHECKLIST.md](FINAL_PRODUCT_CHECKLIST.md)) |
| mơ hồ theo đối tượng hiếm trong dữ liệu thật; hồ sơ "người dân" gần như không bớt hỏi lại (hầu hết thủ tục khai "Công dân Việt Nam") | giới hạn của dữ liệu, không sửa được bằng code | ghi rõ ở README; không hứa hơn |
| `procedure_subjects` có chỗ lệch với tên thủ tục: thu hẹp thẻ theo đối tượng có thể ẩn đúng thủ tục (vd đăng ký đất đai lần đầu cho hộ gia đình chỉ khai doanh nghiệp/Việt kiều) | mở; giảm nhẹ bằng luật "câu nêu rõ thì hồ sơ không can thiệp" và thẻ ghi "không thấy thì gõ tên thủ tục" | nhóm rà dữ liệu đối tượng nếu muốn bật mạnh hơn |
| `pick` (bỏ hỏi, chọn ứng viên hợp đối tượng) có thể đổi đáp án so với ứng viên đứng đầu của truy hồi; câu trả lời luôn nói "Theo hồ sơ của bạn ... nếu chưa đúng, bạn nói lại nhé" | chấp nhận theo thiết kế; chưa đo trên câu thật | Nhân duyệt sau khi có câu hỏi thật |
| danh sách tỉnh = 63 đơn vị trước sáp nhập 07/2025; tỉnh/xã chỉ hiển thị | chờ danh mục 34 tỉnh | mục 6 checklist |
| đường `context_facts`/`session_facts` vẫn không được Planner luật tạo | không đổi ở Phase 26 (hồ sơ đi vào Policy) | — |

## Bước sinh chữ (Answer Composer)
Bật mặc định (nhóm quyết); đã đo ở Phase 27 (`eval/P27_REPORT.md`). Không làm tụt chỉ số hồi quy nào; 0/64 lượt gọi chạm timeout 7 s sau khi rút gọn prompt (trước đó 3–8/64, phụ thuộc GPU bận). Còn lại:
- **Giá trị cho người dùng chưa chứng minh được bằng luật**: bộ chấm luật cho thấy bật = bản code về đủ ý/đúng số/không đảo nghĩa/không bịa, chỉ hơn ở độ ngắn gọn (94% so với 71% đạt cả 5 tiêu chí, phần lớn do tiêu chí độ dài; bản code chép nguyên văn mục điều kiện nên dài). Chờ người chấm 20 ca (`eval/results/composer_sample20.md`).
- Bước này chỉ kích hoạt khi Planner gán `conditions` hoặc quan hệ `compare`: ~9% câu DEV, ~3% câu ctx; trong các ca kích hoạt, ~60% là điều kiện Planner tự gán (mục `condition_index` trùng chữ với tên thủ tục) chứ người dùng không nêu, nên LLM trả lời câu hỏi gốc chứ không "giải thích điều kiện".
- So sánh: LLM chủ yếu liệt kê dữ kiện từng thủ tục kèm trích dẫn, ít khi nêu điểm khác nhau rõ ràng; có thể nói chung chung ("cả hai đều yêu cầu...").
- Ô nhiễm số đo: GPU dùng chung với ứng dụng khác nên p50/p95 dao động 2 lần giữa các lượt đo (cùng cấu hình). Model nguội (sau `ollama stop`/hết `LLM_KEEP_ALIVE`) cần > 14 s để nạp: nay lượt đó trả bản code ngay (không đợi hết 7 s) và nạp nền cho lượt sau.
- Verifier chỉ kiểm số/tên văn bản/"miễn phí", không kiểm nghĩa; bộ chấm luật có kiểm đảo có/không nhưng chỉ bắt các cặp từ cố định.

## Môi trường và tài liệu
- Các script `eval/*.py` và `server/tests/*.py` cần `import system3`: trong thư mục tên khác `system3` hãy chạy qua `python run_server.py <script>` hoặc `-m <module>` (server, `smoke_test.py` và `memory_test.py` tự dùng launcher). `data/DATA_NOTES.md` và `data/snapshot/SOURCE.md` còn ghi đường dẫn máy tác giả (thư mục `data/` không sửa ở đợt này).
- Phase 28: `eval/run_all.py` dựng lại và chạy mọi gate không GPU từ một bản Git sạch (xem `eval/REPRODUCE.md`). Hạn chế: (a) baseline V10.6 chạy lại ra 10,7% / 31,4% (cũ 11% / 32%): retrieval giống từng ca, lệch do đáp án 1 ca (`typo-15`) đã đổi sau baseline; (b) `run_all.py` không chạy bộ mù/team (chỉ `--with-blind` cho người điều phối) nên số bộ mù trong README không được kiểm lại; (c) `retrieval.py` V10.6 vẫn không có bảng từ đồng nghĩa admin (`Backend/`), giống lúc đo baseline; (d) bộ ca bộ mù (`cases_h*`, `cases_pseudo_real*`) là file ca có sẵn, không dựng lại được bằng script ở đây.
- `eval/check_docs.py` kiểm số bộ không-mù với `eval/results/`; số bộ mù và bộ team không đọc từ file (quy tắc bộ mù) nên chỉ kiểm nhất quán giữa các tài liệu, không kiểm với kết quả chạy.

## Dữ liệu
- Corpus nhóm chỉ bù **lệ phí** (15 thủ tục cổng không có lệ phí, khớp tên chính xác). Thời hạn và giấy tờ vẫn lấy từ cổng.
- Phần lớn thủ tục (883 thủ tục) vẫn không có lệ phí; hệ thống nói "cổng không công bố", không suy ra miễn phí.

## Khả năng chịu nhiễu đầu vào (`eval/perturb.py`, 99,4%)
- Còn lỗi khi: dính chữ 4-5 ký tự không có cặp trong tên thủ tục ("tờgì"), dính qua chữ số ("số3"), lời chào đứng trước nhãn ("Chào bạn, câu hỏi 2:"), bỏ dấu làm đổi nghĩa ("sổ đỏ" thành "so do").

## Điểm yếu số một
- Hỏi lại khi câu mơ hồ: 8/16 (HOLDOUT-4), 0/3 (pseudo_real 2). Chưa xử lý trong đợt 5.

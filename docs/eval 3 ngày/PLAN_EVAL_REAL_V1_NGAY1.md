# Kế hoạch Ngày 1: thu thập câu hỏi thật cho bộ `real_v1`

Thuộc việc: `VIEC_EVAL_3_NGAY_2026-10-21.md` (cùng thư mục này). Các file khác của việc này: `REAL_V1_GUIDE.md` (hướng dẫn gán nhãn Ngày 2, có bảng tổng hợp thành phần câu hỏi), `REAL_V1_S4_BANG_FORM.md` (phiếu 40 câu phần bảng System 4). Ngày 1 chỉ thu câu hỏi, chưa gán nhãn, chưa chạy hệ thống.
Hai bộ: System 3 = 300 câu thủ tục (`eval/real_v1/cases_real_v1.json`), System 4 = 200 câu (`system4/eval/real_v1/cases_real_v1_s4.json` 160 câu + `system4/eval/real_v1/cases_real_v1_s4_bang.json` 40 câu).
Nguồn của bộ System 3: các tập câu hỏi thật của người dân trên Hugging Face (không dùng Google Form). Bỏ tập Zalo (truy hồi văn bản luật; trong 80 câu đã gán nhãn trước đó chỉ 1 câu là thủ tục cấp xã), dùng Bình Định (1.074 dòng thô) và Bộ Công an (809 dòng thô). Nguồn của bộ System 4: xem mục 7.

**Trạng thái 20/10:** bước 1–6 của bộ System 3 xong; bộ System 4 đủ 200 câu (mục 7). Script `eval/real_v1/collect_real_v1.py` (chạy bằng `python run_server.py eval/real_v1/collect_real_v1.py`, `SEED=20261021`) sinh `eval/real_v1/cases_real_v1.json`: 300 câu = 120 `random` + 180 `chude` (160 Bình Định, 140 Bộ Công an). Pool sạch 1.490 câu (loại 176 câu đã dùng, 65 trùng, 60 quá ngắn, 92 lời chào). Kiểm: không trùng, không rỗng, 0 trùng 266 câu cũ, regex CCCD/SĐT/email 0 kết quả, chạy lại cùng `seed` ra tệp giống hệt. Che tên người: quy tắc "ông/bà/anh/chị/cô/chú + Tên" cộng quy tắc "Tôi là / tên là / tên / Bạn đọc + Tên" và 17 tên còn sót sau khi đọc quét tay 300 câu (`MANUAL_NAMES` trong script). Chưa commit.

## 1. Mục tiêu và điều kiện xong

- `eval/real_v1/cases_real_v1.json`: 300 câu (đổi từ 150 ngày 20/10; tối thiểu 100), chỉ có câu hỏi, chưa có nhãn. Bộ System 4: 200 câu (mục 7).
- Mỗi câu có `id`, `text` (nguyên văn, giữ lỗi chính tả và thiếu dấu), `source`, `collected_on`, `collector`, `stratum`, `seed`.
- Không còn CCCD, SĐT, email, tên người trong file (quét bằng regex).
- Không câu nào trùng với 266 câu đã dùng để chọn luật M1/M2.
- Commit riêng chỉ chứa file này. Ghi hash commit vào báo cáo.

## 2. Việc chặn (cần trả lời trước khi chạy)

| # | Việc | Ai | Ghi chú |
|---|---|---|---|
| B1 | ~~Xin DB bản 3 từ Nhân~~ **Xong 20/10:** Nhân đã đưa bản 3 vào git (`data/snapshot/procedures_v3.jsonl`, 1.517 thủ tục). Máy này đã nạp và áp dụng; `content_sha256 70c42af1…36bd` khớp số eval của Nhân. Trên máy này bản 3 mang số phiên bản 2 (số phiên bản là cục bộ) | xong | Ghi `content_sha256` vào báo cáo, không ghi số phiên bản |
| B2 | Xin trưởng nhóm cho push đúng một commit (câu hỏi chưa nhãn) | bạn | GitHub đóng dấu giờ. Commit local sửa được ngày giờ nên không đủ làm bằng chứng |
| B3 | Tên `collector` | xong | Phần Hugging Face ghi tên script (`collect_real_v1.py` / `collect_real_v1_s4.py`); 40 câu phần bảng ghi `hwng` |

B2 cần xong trước bước 7.

## 3. Các bước

| Bước | Việc | Ai | Kết quả |
|---|---|---|---|
| 1 | Tải lại dữ liệu thô từ Hugging Face: Bình Định 1.074 dòng, Bộ Công an 809 dòng (không dùng FAQ 17 dòng và Zalo) | tôi | `research/clarify/raw/` (không vào git) |
| 2 | Loại 266 câu đã dùng (`research/clarify/real_questions_labeled.jsonl`) và các câu trùng | tôi | Pool sạch 1.490 câu, ghi ở `research/clarify/pool_real_v1.jsonl` |
| 3 | Loại cơ học các dòng không phải câu hỏi: dưới 4 chữ, dòng chỉ là lời chào (bắt đầu bằng "kính gửi", "xin chào", "chào", dài ≤ 70 ký tự) | tôi | Quy tắc viết vào đầu script, không chọn theo nội dung |
| 4 | Lấy mẫu **tầng 1 (ngẫu nhiên)**: 120 câu từ Bình Định và Bộ Công an, `seed` cố định, bỏ Zalo vì toàn câu pháp luật | tôi | Đo khả năng từ chối ngoài phạm vi đúng như ngoài đời |
| 5 | Lấy mẫu **tầng 2 (chủ đề cấp xã)**: lọc bằng danh sách từ khoá viết **trước** (hộ tịch, khai sinh, kết hôn, cư trú, chứng thực, đất đai…), lấy từ danh mục nhóm thủ tục trong DB, rồi chọn ngẫu nhiên 180 câu bằng `seed` | tôi | Đo `top-1` / `top-3` khi có đủ câu trả lời được |
| 6 | Che PII bằng `mask_pii` (`server/policy`), giữ nguyên chữ của người hỏi, quét regex lần cuối | tôi | `eval/real_v1/cases_real_v1.json` |
| 7 | Bạn xem qua file, rồi commit và push (khi B2 xong). Ghi hash vào báo cáo | bạn | Hash "câu hỏi tồn tại trước kết quả" |

Danh sách từ khoá ở bước 5 phải được viết xong và commit cùng script **trước khi** xem bất kỳ kết quả nào của hệ thống.

## 4. Kiểm tra trước khi commit

- Đếm câu theo `stratum` và theo nguồn: 300 câu (System 3), 200 câu (System 4); mỗi bộ trên mức tối thiểu 100.
- Không có `text` rỗng, không trùng nhau, không trùng 266 câu cũ.
- Regex CCCD / SĐT / email trả 0 kết quả.
- Chạy lại script với cùng `seed` cho ra file giống hệt.

## 5. Điều cần biết (ghi vào báo cáo cuối)

- Câu thật ngoài đời phần lớn ngoài phạm vi: trong 266 câu đã gán nhãn chỉ 24 câu (9%) hệ thống trả lời được. Vì vậy tách hai tầng và báo riêng, không gộp.
- Cỡ mẫu 300 (tầng `chude` 180) cho khoảng tin cậy khoảng ±6–7 điểm trên toàn bộ, rộng hơn khi tách theo tầng; chỉ khẳng định "cùng cỡ với bộ nội bộ", không khẳng định "tốt hơn".
- Giấy phép tập Bình Định và Bộ Công an trên Hugging Face ghi "không rõ": chỉ dùng đánh giá nội bộ, không phát hành lại bộ câu hỏi.
- Đây là câu hỏi công khai đã được cổng ghi nhận, không phải mọi câu của mọi người dân.

## 6. Việc để sang ngày sau

- Ngày 2: hai người gán nhãn độc lập theo `REAL_V1_GUIDE.md`; κ ba lớp (`answer` / `clarify` / `apologize`) và độ khớp `expect_ids` bằng `eval/real_v1/real_v1_agree.py` (System 4: thêm `--s4`); thống nhất bất đồng, ghi lý do vào `eval/real_v1/REAL_V1_ASSUMPTIONS.md`. Gán nhãn `proc_id` phải tra bằng Cổng dịch vụ công hoặc `data/snapshot/procedures_v3.jsonl` thô, không dùng công cụ tìm của hệ thống.
- Ngày 3: chạy một lần bằng `run_pseudo.py` (ghi vào `eval/results/`, phải chép sang `eval/saved_results/2026-10-23_real_v1/`), báo cáo, diễn tập demo, xoá bộ `du_lich_gia` khỏi tài khoản dev trước khi demo.

## 7. Phần System 4 (200 câu, thêm 20/10)

Quyết định: bộ System 3 = 300 câu thủ tục; bộ System 4 = 200 câu. Script `system4/eval/real_v1/collect_real_v1_s4.py` sinh `system4/eval/real_v1/cases_real_v1_s4.json` (`SEED=20261021`):

| Phần | Số câu | Nguồn | Chấm |
|---|---|---|---|
| `du_lich_vqd` | 75 (50 có đáp án + 25 không có đáp án trong bài) | UIT-ViQuAD2.0, câu người viết trên bài Wikipedia | Có đáp án gốc (`source_gold`); câu không có đáp án thử "không bịa" |
| `y_te_real` | 85 | hungnm/vietnamese-medical-qa, loại 300 câu hệ thống đã nạp | Chỉ chấm hành vi (không chẩn đoán bừa), không có đáp án |
| `bang_human` | 40 (14 Y tế, 13 Giáo dục, 13 Du lịch) | Soạn khi chỉ nhìn tên cột, `hwng` duyệt từng câu (`REAL_V1_S4_BANG_FORM.md`) | Đáp án trong bảng, gán nhãn Ngày 2 |

Đủ 200 câu (160 từ Hugging Face + 40 phần bảng, `system4/eval/real_v1/cases_real_v1_s4_bang.json`). Giới hạn: trong 6 bài Du lịch của hệ thống, ViQuAD chỉ có bài Phong Nha (190 câu có đáp án + 137 không), nên phần Du lịch văn bản chỉ phủ một bài, và bản Wikipedia trong ViQuAD (khoảng 2020) có thể khác bản hệ thống nạp (10/2026). Câu Y tế hỏi về thông tin ngoài dữ liệu của hệ thống nên đo hành vi, không đo độ đúng.

## 8. Trạng thái 21/10 (cập nhật)

- Ngày 2 xong: gán nhãn hai lượt (A: Claude, B: subagent), κ System 3 = 0,753, thống nhất 31 câu, duyệt và kiểm sâu 22 câu "không chắc". Báo cáo: `BAO_CAO_GAN_NHAN_A_B.md`.
- File đã dồn vào hai thư mục riêng: `eval/real_v1/` (System 3) và `system4/eval/real_v1/` (System 4), mỗi thư mục có `README.md` và `LOCK.md`.
- **Bộ để chạy:** System 3 = 282 câu (55 `answer`, 7 `clarify`, 220 `apologize`; bỏ 18 `skip`); System 4 = 177 câu (Du lịch văn bản 53, Y tế 85, bảng 39; bỏ 23 `drop`).
- **Đã khoá** (mã băm sha256 trong `LOCK.md`): không sửa nhãn theo kết quả hệ thống. Chưa chạy hệ thống.
- Còn lại (Ngày 3): chạy System 3 một lần, báo cáo, `EVAL_THAT_V1.md`, demo, cập nhật slide. System 4 cần hỏi trưởng nhóm trước khi chạy GPU/LLM.

## 9. Trạng thái 22/10 (Ngày 3)

- B1 xong: System 3 chạy một lần (luật, không GPU, DB bản 3). Lần chạy đầu dùng nhầm DB bản 1 nên bỏ, ghi rõ trong báo cáo.
- B2 xong: `eval/saved_results/2026-10-22_real_v1/report.md` (hành vi 56,0%, top-1 12,7%).
- B3 xong: System 4 chạy một lần (177 câu, 58 phút); báo cáo `system4/eval/saved_results/2026-10-22_real_v1/report.md`.
- B4 xong: `docs/EVAL_THAT_V1.md`.
- Còn lại: B5 (demo: công cụ tra `eval/real_v1/tra_thu_tuc.py` đã có; còn xoá bộ `du_lich_gia` khỏi tài khoản dev, tập câu của mentor, video dự phòng), B6 (cập nhật slide và `MINH_CHUNG_EVALUATION_SLIDE.md`), commit theo thứ tự câu hỏi, nhãn, kết quả.
- B6 xong (22/10): `MINH_CHUNG_EVALUATION_SLIDE.md` mục 0b (số real_v1 cho slide 2 và 3, bảng số cũ lệch và số nên dùng), `SUA_SLIDE_VA_BAI_BAO.md` (S10–S13, P8), `TOM_TAT_EVAL_CHO_MENTOR.md`. File slide `.pptx` không nằm trong repo nên chưa sửa; có sẵn bảng để dán.

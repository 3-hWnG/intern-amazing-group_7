# Đánh giá trên câu hỏi thật, bộ real_v1 (22/10/2026)

Một trang trả lời ba phản đối của mentor: dữ liệu đo có phải tự sinh không, có chạy lại được trước mặt không, và có chứng minh được là đo thật không. Mọi số ở đây tính từ file kết quả thô trong `eval/saved_results/2026-10-22_real_v1/` (System 3) và `system4/eval/saved_results/2026-10-22_real_v1/` (System 4).

## 1. Dữ liệu: câu hỏi từ đâu ra

Không câu nào do nhóm hoặc AI viết lại. Câu hỏi giữ nguyên chữ người viết (kể cả lỗi chính tả); chỉ gộp khoảng trắng và che CCCD, SĐT, email, tên người. Mã nguồn lấy mẫu: `eval/real_v1/collect_real_v1.py`, `system4/eval/real_v1/collect_real_v1_s4.py`, cùng `SEED` cho tệp giống hệt.

| Bộ | Số câu gốc | Nguồn | Ghi chú |
|---|---|---|---|
| System 3 | 300 | Hỏi đáp Cổng dịch vụ công Bình Định (160 câu), hỏi đáp Cổng dịch vụ công Bộ Công an (140 câu), Hugging Face | Hai tầng: 120 ngẫu nhiên, 180 lọc theo chủ đề cấp xã. Loại 266 câu nhóm từng dùng để chọn luật. |
| System 4, Du lịch văn bản | 75 | UIT-ViQuAD2.0, bài Wikipedia "Vườn quốc gia Phong Nha - Kẻ Bàng" | Câu do người viết trên bài Wikipedia, không phải câu người dùng thật. Chỉ phủ một bài trong sáu bài của hệ thống. |
| System 4, Y tế | 85 | hungnm/vietnamese-medical-qa (câu của người dân gửi bác sĩ) | Loại 300 câu mà hệ thống đã nạp. Không có đáp án đúng trong dữ liệu, chỉ đo hành vi. |
| System 4, phần bảng | 40 | Soạn khi chỉ nhìn tên cột của ba bảng Wikipedia; `hwng` duyệt từng câu | Không phải câu người dùng thật. |

Giấy phép hai tập Bình Định và Bộ Công an trên Hugging Face ghi "không rõ": chỉ dùng đánh giá nội bộ, không phát hành lại.

## 2. Gán nhãn

- Hướng dẫn: `docs/eval 3 ngày/REAL_V1_GUIDE.md`. Dữ liệu tra: thủ tục bản 3 (1.517 thủ tục, `content_sha256` `70c42af1…36bd`).
- Hai lượt gán nhãn độc lập: A (Claude) và B (một subagent Claude không đọc file A). **Cả hai đều là AI; chưa có lượt kiểm của người trên mẫu.**
- System 3: κ ba lớp (`answer`/`clarify`/`apologize`) = **0,753**, khớp 258/281 câu cả hai không bỏ qua; 31 câu bất đồng. System 4: khớp 94% ở `drop`, 95% ở `refusal`, 100% ở `urgent` và `needs_image`; đáp án khớp 176/176 sau khi sửa script để coi các cách viết khác nhau là một.
- Lượt A tra sót thủ tục ở 9 câu (ví dụ "xác nhận số CMND"); lượt B tìm ra. Nhãn cuối do thống nhất và được chủ dự án duyệt ngày 21/10; lý do từng câu: `eval/real_v1/REAL_V1_ASSUMPTIONS.md`; báo cáo: `docs/eval 3 ngày/BAO_CAO_GAN_NHAN_A_B.md`.
- Loại khỏi chấm: System 3 bỏ 18 câu cụt hoặc chỉ có lời chào; System 4 bỏ 23 câu mà bài Wikipedia hiện tại có đáp án khác bản ViQuAD hoặc mơ hồ. Bộ để chạy: System 3 = 282 câu, System 4 = 177 câu.

## 3. Bằng chứng về thứ tự (câu hỏi, rồi nhãn, rồi kết quả)

Mã băm sha256 của câu hỏi, nhãn và bộ chạy được ghi lúc khoá ngày 21/10 trong `eval/real_v1/LOCK.md` và `system4/eval/real_v1/LOCK.md`; hệ thống chạy ngày 22/10 sau khoá. **Chưa có commit git nào cho bộ này**, nên ba mã commit (câu hỏi, nhãn, kết quả) chưa có; ngày giờ file trên đĩa chưa phải bằng chứng độc lập. Muốn có bằng chứng cần commit và push theo đúng thứ tự.

## 4. Kết quả

### System 3 (Strict), chế độ luật, không GPU, DB bản 3, 282 câu

| Chỉ số | Kết quả (khoảng tin cậy Wilson 95%) |
|---|---|
| Hành vi đúng | 158/282 = **56,0%** (50,2% đến 61,7%) |
| Top-1, 55 câu `answer` | 7/55 = **12,7%** (6,3% đến 24,0%) |
| Top-3 | 12/55 = 21,8% (12,9% đến 34,4%) |
| MRR | 0,227 |
| Recall `answer` / `clarify` / `apologize` | 41/55 (74,5%) / 1/7 (14,3%) / 116/220 (52,7%) |

Hai tầng cho kết quả gần nhau (ngẫu nhiên 56,8%, theo chủ đề 55,6% hành vi đúng).

### System 4 (Friendly), `inst02`, GTX 1660 SUPER 6 GB, 177 câu

| Nhóm | Kết quả |
|---|---|
| Du lịch văn bản, có đáp án (50 câu) | nghiêm 46/50 = **92,0%** (81,2% đến 96,8%); nới 47/50 = 94,0% |
| Phần bảng, có đáp án (26 câu) | 17/26 = **65,4%** (46,2% đến 80,6%) |
| Phải từ chối (14 câu) | 10/14 = 71,4% (45,4% đến 88,3%) |
| Phải hỏi lại (2 câu) | 0/2 |
| Y tế (85 câu): khuyên khám | 80/85 = 94,1% |
| Y tế, câu `urgent` (10 câu): khuyên cấp cứu / đi ngay | **4/10** = 40,0% |
| Y tế: có liều thuốc cụ thể / khẳng định chẩn đoán | 2/85 / 1/85 |
| Thời gian | câu đầu median 13,0 s; cả câu median 19,4 s, p90 32,4 s, lớn nhất 51,7 s; 0 lỗi |

Cách chấm viết trước khi chạy (đầu `system4/eval/real_v1/run_real_v1_s4.py`): luật chữ của `bench.py`; Y tế chỉ đo hành vi bằng luật chữ.

## 5. Chỗ hệ thống sai

**System 3** (danh sách 159 câu sai trong `report.md`):
- **Từ chối kém:** trả lời thay vì từ chối ở 101/220 câu ngoài phạm vi (luật, xử phạt, khiếu nại, tình trạng hồ sơ).
- **Chọn nhầm một thủ tục hàng loạt:** `1.115406` (xét hưởng chế độ trợ cấp đối tượng Công an nhân dân) được chọn ở 26 câu ngoài phạm vi và 10 câu `answer` sai, do khớp chữ "Công an nhân dân" trong các câu gửi Bộ Công an.
- **Hỏi lại gần như không có:** 1/7.

**System 4:**
- **Hỏi lại thừa:** 6 câu đáp "Trong dữ liệu có 2 mục cùng khớp…" ở câu không mơ hồ hoặc lẽ ra phải từ chối vì bảng không có cột.
- **Câu Y tế nguy hiểm:** chỉ 4/10 câu `urgent` được khuyên cấp cứu; câu người già hôn mê do ngộ độc khí CO (081) không có lời khuyên đi khám.
- **Câu liệt kê** (thành viên đại học, di tích UNESCO, di tích năm 2012): trả bảng thiếu một phần dòng.

## 6. Điều đánh giá này KHÔNG chứng minh

- Nhãn do hai lượt AI gán, κ 0,753 chỉ là nhất quán giữa hai lượt, chưa có lượt kiểm của người.
- System 3 chỉ có 55 câu `answer`; top-1 có khoảng tin cậy rộng (6% đến 24%). 78% câu của bộ là `apologize`.
- System 3 chạy chế độ luật, không LLM, không phản ánh bản người dùng thấy (có LLM). System 4 chạy trên GPU 6 GB; thời gian chậm hơn máy RTX 4050 của Nhân.
- Câu System 3 là câu hỏi công khai đã được cổng ghi nhận, không đại diện mọi người dân. Câu System 4 không phải câu người dùng thật (ViQuAD do người viết trên Wikipedia; phần bảng soạn khi chỉ nhìn tên cột).
- Du lịch văn bản chỉ phủ một bài Wikipedia; các câu "không có đáp án" của ViQuAD bị loại vì bài hiện tại có đáp án.
- Phần bảng nhỏ (26 câu có đáp án); chấm bằng luật chữ có thể đánh trượt câu đúng ý (ví dụ câu bang-005 trượt vì yêu cầu nguồn trong nhãn).
- **Sự cố khi chạy:** lần chạy đầu System 3 (22/10) dùng nhầm DB cũ (bản 1) vì thiếu biến `S3_DATA_DB`; kết quả bị bỏ và lưu riêng (`KHONG_DUNG_lan_dau_sai_DB.json`), lần chạy lại dùng đúng DB bản 3, không đổi gì khác.
- Không so sánh với hệ thống khác; bản V10.6 cũ không được tính làm baseline.

## 7. Chạy lại

```bash
# System 3: hơn một phút, không cần GPU
S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 S3_DATA_DB=<DB bản 3> python run_server.py eval/run_pseudo.py real_v1/cases_real_v1_labeled.json real_v1
S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 S3_DATA_DB=<DB bản 3> python run_server.py eval/real_v1/score_real_v1.py <thư mục báo cáo>
# System 4: cần Ollama; khoảng một giờ trên GTX 1660 SUPER
python system4/eval/real_v1/run_real_v1_s4.py prepare && python system4/eval/real_v1/run_real_v1_s4.py run && python system4/eval/real_v1/run_real_v1_s4.py score <thư mục>
```

# Kế hoạch điền mục III (Metrics) trong bài thuyết trình Gamma, và kiểm tra ảnh hưởng của commit mới lên eval

Nguồn việc: tin nhắn của trưởng nhóm (22/10, 15:52) và file `Thuyet-trinh (3).pdf` (trang 1 là "Template cho Hưng": hai bảng cần điền; trang 6 là chỗ "III/ Metrics nằm đây"). Hạn: **1h30 trưa mai (23/10)**; chưa xong thì đưa các số quan trọng.

## 1. Commit 3318436 (chế độ khách, giới hạn lượt hỏi) có ảnh hưởng eval không?

Đã kéo về và kiểm tra ngày 22/10. **Kết luận: số đo không đổi; chỉ cần nhớ tắt giới hạn khi đo.**

| Kiểm tra | Kết quả |
|---|---|
| Strict (System 3) chạy lại bộ real_v1 sau commit | **Giống hệt từng dòng** (`cmp` hai file kết quả): 158/282, top-1 7/55. Commit không đụng `server/`, `eval/`, `data/`, `retrieval/` |
| Friendly (System 4) chạy thử 10 câu sau commit | Chạy bình thường qua middleware mới; 10/10 câu đạt (trước 9/10, lệch do nhiệt độ 0,2, không do code). Thời gian trung vị 16,7 s so với 34,6 s ở lần đầu: mười câu đầu của lần chạy chính chậm vì GPU nóng máy, không phải do code |
| Giới hạn lượt hỏi (`ratelimit.py`) | **Bật mặc định**: dev 60 câu/phút, 5 câu cùng lúc. Chỉ ảnh hưởng đo bằng HTTP. `bench.py` và `load_test.py` đã được Nhân thêm `S4_RATE_LIMIT=0`; tôi thêm vào `system4/eval/real_v1/run_real_v1_s4.py`. Script đo qua adapter (`run_golden.py`, `run_pseudo.py`) không qua HTTP nên không bị ảnh hưởng |
| Phần Stream (`chat.py`, `app.js`: chỉ hiện lần viết đầu, bản viết lại lưu phiên bản 2) | **Chưa có trong commit** (theo tin nhắn, đang ở working tree của Nhân). Khi đẩy lên cần kiểm lại: bộ đo đọc câu trả lời cuối của hội thoại; nếu có bản viết lại thì phải lấy bản nào, và thời gian chữ đầu có đổi nghĩa không. Nhân nói `abi/golden.py` và `bench.py` đã được sửa theo; tôi sẽ chạy lại 10 câu thử khi commit đó lên |

Trả lời gửi trưởng nhóm: "Commit khách + giới hạn lượt không đổi số eval (Strict giống hệt, Friendly chạy bình thường); bench đã tắt giới hạn. Chờ commit Stream để kiểm lại cách đọc câu trả lời cuối."

## 2. Cách điền mục III

Template có hai bảng (3. Strict, 4. Friendly + đường nhanh) với các cột **Câu hỏi | Tuần trước | Tuần này | Đánh giá**. Ghi chú trong template: "thấy khác thì đổi luôn cột Tuần trước". Đề xuất:

1. **Điền đủ hai bảng** theo mục 3 (số lấy từ các file đã có, nguồn ghi ở cột phải).
2. **Thêm một khung "Câu hỏi thật của người dân (real_v1)"** ngay dưới (mục 3b), vì đây là điều mentor phản đối ("dữ liệu tự sinh"): hai bảng nhỏ + một biểu đồ cột "bộ nhóm soạn so với câu thật".
3. **Không dài**: mỗi ô một câu; chi tiết cách đo để ở file `docs/EVAL_THAT_V1.md`, trên slide chỉ có số và một dòng đánh giá.
4. Biểu đồ: tôi có thể dựng ảnh PNG (hành vi đúng, top-1, từ chối đúng: nhóm soạn so với câu thật) để dán vào Gamma.

Thứ tự làm (theo hạn 13:30 mai): (a) bạn đọc bản nháp ở mục 3 và chọn các ô cần đổi lời; (b) tôi sửa theo ý bạn và dựng biểu đồ; (c) bạn dán vào Gamma. Tôi không mở được Gamma, nên bản nháp để dán tay.

## 3. Bản nháp để dán (cột Tuần trước giữ nguyên chữ của template trừ khi ghi "ĐỔI")

### 3. Evaluation Metrics (Strict)

Chữ mở đầu của template (tuần này: dữ liệu bản 3, 518 câu, eval đầy đủ #2 và #3) giữ nguyên.

| Câu hỏi | Tuần trước | Tuần này | Đánh giá |
|---|---|---|---|
| Có tìm đúng thủ tục người dùng cần không? | 73% top-1, 80% top-3, MRR 0,759 | **72% top-1** (274/381), 79% top-3, MRR 0,752 | Ổn định (khoảng tin cậy chồng nhau); bộ do nhóm soạn. Trên câu thật: 12,7% (mục 3b) |
| Có phản ứng đúng kiểu không (trả lời, hỏi lại, từ chối)? | 78% | **77%** (400/518) | Giảm 1 điểm do thẻ hỏi tỉnh (9 ca nhãn "trả lời" nay hỏi tỉnh), cố ý. Trên câu thật: 56,0% |
| Gặp câu mơ hồ thì có hỏi lại không? | 47% | **50%** (38/76) | Nhích lên nhờ luật bỏ chữ đệm và hỏi lại khi không nêu thủ tục; vẫn là điểm yếu nhất. Trên câu thật: 1/7 |
| Gặp câu ngoài phạm vi thì có từ chối không? | 90% | **90%** (52/58) | Giữ. Trên câu thật: 52,7% (116/220), hệ thống hay trả lời thay vì từ chối |
| Liệt kê / đếm thủ tục có đúng lĩnh vực không? | 12% | **98%** (bộ khuôn 40 câu); 93% (42/45, bộ đo riêng) | Tăng lớn nhờ truy vấn bảng phẳng; chỉ chạy khi có LLM |
| Lệ phí có đọc đúng không? | ~31 thủ tục đọc "20.000" thành 20 | **Đã sửa** khi dựng DB: 4/150 câu mẫu đổi đúng ý (10 đồng thành 10 USD) | Xong; có test hồi quy |
| Có hỏi tỉnh khi thủ tục có bản riêng của tỉnh không? | Chưa có | **Có**: mẫu 20 câu bản 3 đúng 20/20 | Mới; nhãn bộ mù viết trước nên 9 ca bị tính sai (đã giải thích kèm số) |
| Có chặn câu cố ý lừa hệ thống không? | Strict 11/11 | Strict 11/11; **Friendly 11/11 (trước 4/11)** | Friendly được lớp chính sách chung chặn chèn lệnh |
| Có che CCCD/SĐT không? | 12/12 phép thử (khi hiển thị, trong log) | 12/12 + **che ngay lúc ghi vào cả 2 DB** (tin nhắn, tiêu đề, tóm tắt, bộ nhớ, trace, 👍/👎); test quét mọi bảng sau một lượt Strict + Friendly có số giả: không còn số nguyên văn | Xong; không che cả câu trả lời (dữ liệu Cổng có 1.852 mã dịch vụ) |
| Câu cần AI viết mất bao lâu khi 10 người dùng cùng lúc? | Chưa đo khi đông người (p95 15,4 s ở lần chạy thử đầu) | **p50 2,9 s / p95 4,0 s** (10 người giả, nghỉ 20–40 s) | Đạt mục tiêu (≤ 8 s) nhờ bộ lập lịch GPU chung |
| Câu chỉ dùng luật mất bao lâu khi 10 người dùng cùng lúc? | Dưới 0,2 s (một người) | **p95 1,18 s** (10 người); một người vẫn dưới 0,2 s | Chưa đạt mục tiêu 0,5 s (CPU dùng chung với Ollama + reranker) |

Nguồn: `docs/KET_QUA_THUC_THI_2026-10-23.md` (§2–§4), `docs/SUA_SLIDE_VA_BAI_BAO.md` (S4, S5), `docs/PLAN_TUAN_TOI.md`.

### 4. Evaluation Metrics (Friendly + đường nhanh)

| Câu hỏi | Tuần trước | Tuần này | Đánh giá |
|---|---|---|---|
| Có trả lời đúng không (NV5)? | 96% (75/78) | Bài thi cũ không đo lại. **Câu thật/Wikipedia: Du lịch văn bản 92,0% (46/50), bảng 65,4% (17/26)** | Bài thi nhóm soạn 96%; trên câu thật thấp hơn, nhất là bảng |
| Chào hỏi / cư xử đúng trong 22 tình huống | 100% / 17/22 | Không đo lại tuần này | Giữ số cũ; 5 ca trượt (xưng hô, trí nhớ) chưa điều tra |
| Tra cứu một dòng trên dữ liệu lạ (bộ mù cửa hàng) | — | **14/14 đúng**, 0,09 s (không gọi AI); đường cũ 3–7 s | Hơn đường cũ cả đúng lẫn nhanh |
| Đếm / liệt kê bằng đường nhanh trên dữ liệu lạ | — | 1/6, nên **tắt mặc định** (đi đường cũ) | Chưa dùng được; chờ sửa lỗi còn sót và đo trên bộ mù thứ ba |
| Tổng trên bộ mù, đường cũ so với mới | — | 27/32 so với 25/32 (ước tính 29/32 nếu tắt đếm: suy ra, chưa đo) | Chưa hơn trên tổng; hơn ở tra cứu và tốc độ |
| Tốc độ cả câu (trung vị, có GPU) | 3,3–11,4 s tuỳ loại câu | Câu thật/Wikipedia (GTX 1660 SUPER 6 GB): câu đầu 13,0 s, cả câu **19,4 s** (p90 32,4 s); đường nhanh 0,09 s | Chậm trên máy 6 GB (GPU chia cho reranker); bộ câu dài hơn bài thi cũ |
| Chờ hàng GPU khi 10 người dùng cùng lúc | Chưa đo | Chữ đầu p50 6,2 / p95 15,2 s; cả câu p50 11,2 / p95 21,3 s; chờ hàng p95 13,6 s | Trên mục tiêu 10 s; trưởng nhóm chấp nhận khoảng 15 s cho thí điểm |
| Gặp câu cố ý lừa (chèn lệnh) | 4/11 bị chặn | **11/11 bị chặn** | Xong (lớp chính sách chung) |
| Lĩnh vực FLM (dữ liệu thật, câu tự đặt, không phải bộ mù) | — | Nạp thật 19/10: 65 ngành, 1.305 môn; dựng engine 12 s xuống 1,5 s | Chưa có bộ câu đo; không có số chính xác |

Nguồn: `docs/SYSTEM4_DUONG_NHANH.md` (mục E–H), `docs/KET_QUA_THUC_THI_2026-10-23.md` §3, `system4/eval/saved_results/`, `system4/eval/real_v1/`.

### 3b. Câu hỏi thật của người dân (real_v1): điều mentor hỏi

Một lần chạy, nhãn khoá trước khi chạy (mã băm trong `LOCK.md`). Báo cáo một trang: `docs/EVAL_THAT_V1.md`.

| | Strict (282 câu, chế độ luật) | Friendly (177 câu) |
|---|---|---|
| Hành vi đúng | **56,0%** (158/282) | Du lịch văn bản 92,0% (46/50); bảng 65,4% (17/26) |
| Top-1 / top-3 | **12,7%** (7/55) / 21,8% | |
| Từ chối đúng | 52,7% (116/220) | 71,4% (10/14) |
| Hỏi lại đúng | 1/7 | 0/2 |
| Y tế | | khuyên khám 94,1%; câu nguy hiểm khuyên cấp cứu **4/10** |

Điều nói kèm (một dòng mỗi ý): nhãn do hai lượt AI gán (κ 0,753), chưa có lượt kiểm của người; Strict chọn nhầm một thủ tục công an ở 26 câu và trả lời thay vì từ chối ở 101/220 câu ngoài phạm vi; Friendly hay hỏi lại thừa ("2 mục cùng khớp").

**Biểu đồ đề xuất:** ba cặp cột (hành vi đúng 77% so với 56%, top-1 72% so với 12,7%, từ chối đúng 90% so với 52,7%): "bộ nhóm soạn so với câu thật".

## 4. Cần bạn quyết

1. Có đưa **số thấp của real_v1 (mục 3b)** lên slide không? Tôi khuyên có, vì giấu thì mentor thấy ở báo cáo.
2. Với các ô chưa đo tuần này (22 tình huống, FLM): ghi "không đo lại" như bản nháp, hay bỏ hàng.
3. Muốn tôi dựng ảnh biểu đồ không.

## 5. Đã quyết và đã làm (22/10)

1. Đưa số thấp của real_v1 lên slide: **có**.
2. Hai hàng không đo lại tuần này (22 tình huống, FLM): **bỏ hàng** (đã bỏ khỏi bảng Friendly).
3. Biểu đồ: **đã dựng** (`bieu_do_nhom_soan_vs_cau_that.png`).
4. Đã điền thử vào bản sao PDF: `D:\merged_sys3_4\Thuyet-trinh (3)_da_dien.pdf` (11 trang): bỏ trang template và trang "III/ Metrics nằm đây", thay bằng trang "III/ Metrics" và ba trang đã điền (Strict, Friendly, câu hỏi thật). Các trang khác giữ nguyên; bản gốc không đổi.


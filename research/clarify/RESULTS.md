# Hỏi lại khi câu hỏi mơ hồ — thử nghiệm 18/10/2026

Yêu cầu của trưởng nhóm: đề ra vài cách, thử xem cách nào hợp lý rồi sửa. Được duyệt web và tải dataset (≤ 100 MB). Thư mục này chứa toàn bộ thử nghiệm.
Quy tắc giữ nguyên: **không chọn ngưỡng trên bộ mù**; bộ mù chỉ đo **một lần** ở cuối, sau khi đã chốt cách.

## 1. Dữ liệu

### 1a. Câu hỏi thật của người dân (tải 18/10, tổng 3,8 MB; tệp gốc ở `raw/`, không đưa vào git)
| Mã | Nguồn (Hugging Face) | Nội dung | Số câu | Giấy phép |
|---|---|---|---|---|
| dvc | `hieunguyen1053/dichvucong_faqs` (cấu hình `hoi-dap`) | hỏi đáp trên Cổng dịch vụ công Bình Định | 979 (sau bỏ trùng) | không ghi |
| mps | `doanhieung/vn-mps-public-service-qa`, `-faq` | hỏi đáp Cổng dịch vụ công Bộ Công an | 822 | không ghi |
| zalo | `GreenNode/zalo-ai-legal-text-retrieval-vn` (chỉ `queries.jsonl`) | câu hỏi pháp luật của người dân | 3.196 | MIT |

Đã xem nhưng không dùng: `thailevann/VietAdminQA` (bị khoá truy cập, câu theo khuôn), `DANGDOCAO/GeneratingQuestions` (tệp 117 MB > giới hạn; câu sinh tự động),
`DatNguyenAIML/ViLegalExperts` (tư vấn luật dài). Chỉ giữ câu hỏi: bỏ tên người hỏi, câu trả lời, người trả lời; che CCCD/SĐT; bản lưu git
(`real_questions_labeled.jsonl`) còn thay tên người và email bằng `[TÊN]` / `[EMAIL]`.

### 1b. Gán nhãn (390 câu: 250 câu ngắn Bình Định, 80 Zalo, 60 Bộ Công an; chia 60% tune / 40% test)
Gán tay theo định nghĩa viết trước, nhìn câu hỏi + tên 3 thủ tục gần nhất (KHÔNG nhìn hành vi của hệ thống); tra dữ liệu bản 3 bằng `find.py` khi chưa chắc:
- **A** câu chỉ rõ một thủ tục cấp xã có trong dữ liệu (hoặc bản mặc định của họ rõ ràng là cái người hỏi cần);
- **C** nói về việc thuộc thủ tục cấp xã nhưng còn ≥ 2 thủ tục khác nhau đều hợp lý, hoặc thủ tục chỉ có bản riêng của tỉnh mà chưa nêu tỉnh;
- **O** hỏi luật / xử phạt / tình trạng hồ sơ / thủ tục cấp tỉnh hoặc trung ương / lỗi cổng…;
- **X** không phải câu hỏi (dòng chào "Kính gửi…" bị cắt từ tiêu đề) — loại.

Kết quả: **A 24 · C 4 · O 238 · X 124.** Câu thật cần hỏi lại rất hiếm; đa số là câu rõ ràng hoặc ngoài phạm vi cấp xã.

### 1c. Bộ dùng để chọn cách
dev (golden, một lượt, 453 câu), `eval/cases_p30.jsonl` (228), câu thật đã gán nhãn (266, bỏ X).

## 2. Hiện trạng (trước khi sửa, dữ liệu bản 3, chỉ luật)
| Bộ | C → hỏi lại | A → trả lời | O → từ chối |
|---|---|---|---|
| dev | 23/26 | 355/387 | 38/40 |
| p30 | 101/115 | 106/113 | — |
| câu thật | 2/4 | 15/24 | **176/238** (trả lời nhầm 53, hỏi lại 9) |

Hai lỗi thấy ngay trên câu thật: "Thủ tục bao gồm những giấy tờ nào" (không nêu thủ tục nào) bị **trả lời bừa** một thủ tục; câu dùng từ đời thường
("làm lại giấy chứng minh thư", "mất cà vẹt", "đất vườn sang đất ở") bị **xin lỗi "không tìm thấy"**.

## 3. Các cách đã thử

| Cách | Ý tưởng | Kết quả trên bộ chọn | Quyết định |
|---|---|---|---|
| A (trước, G4.1) | reranker câu hỏi × tên: điểm đầu thấp, chênh hạng 1–2 nhỏ | tốt nhất +1 C / −13 A (dev+p30-tune) | loại |
| B (trước, G4.1) | độ rộng cụm: cụm nằm trong tên nhiều họ | tốt nhất +2 C / −17 A | loại |
| **M1** | bỏ chữ đệm hội thoại trên chữ có dấu: "đang tìm hiểu/muốn/cần…", "bao gồm [giấy tờ/hồ sơ/gì]", "liên quan đến/tới", "về" sau hỏi/biết/hiểu/thắc mắc/tư vấn/thông tin | p30 C +5, không làm sai ca nào | **dùng** (`S3_CLARIFY_FILLER`) |
| **M2** | câu hỏi về thủ tục (thủ tục, giấy tờ, hồ sơ, lệ phí, bao lâu, ở đâu, tìm hiểu…) mà không nêu thủ tục nào, đầu hội thoại → "Bạn muốn hỏi về thủ tục nào?" | dev C +1, câu thật C +1, không làm sai ca nào | **dùng** (`S3_CLARIFY_NOPROC`) |
| M3 | cụm chính chung cho ≥ 3 họ, không có thủ tục "chính danh" mang đúng cụm | 0 ca đổi; nới điều kiện thì thành cách B (lỗ) | loại, gỡ code |
| M4a | model 4B phán "đã đủ rõ chưa" (câu ≤ 15 chữ mà luật đã trả lời) | bắt 11/11 C nhưng hỏi lại thừa 199/249 A (dev), 37/91 (p30) | loại |
| M4b | model 4B chọn số thủ tục, 0 = không quyết được | bắt 0/11 C, vẫn hỏi lại thừa 9 A | loại |
| M5 | thủ tục chỉ có bản riêng của tỉnh → hỏi tỉnh | các ca thật loại này không tới được bước đó (bộ luật không tìm ra thủ tục: thiếu từ đồng nghĩa "đổi sổ hồng" ~ "cấp đổi giấy chứng nhận") | chưa làm, cần bảng từ đồng nghĩa trước |
| M6 | luật định xin lỗi nhưng tìm theo nghĩa (bge-m3) thấy ứng viên → "Có phải bạn muốn hỏi…?" | ngưỡng 0,58: gợi ý 16/17 nhưng gợi ý nhầm 88/212 câu O; thêm điều kiện ý định: 13/17 vs 58/212; thêm reranker ≥ 0: 3/17 vs 5/212; ứng viên thường sai | loại |

M1 + M2 cùng bật (mặc định từ 18/10): dev C 24/26, p30 C 106/115, câu thật C 3/4; A, O **không đổi ca nào**; mẫu so khớp 150 ca không đổi;
test `server/tests/clarify_vague_test.py`.

## 4. Đo bộ mù một lần (eval #4, `eval/saved_results/2026-10-18_eval4_clarify/`)
Bộ mù: hỏi lại đúng **38/76 — không đổi**; top-1 không đổi; chỉ 2 ca đổi (nhãn "trả lời", từ xin lỗi sang hỏi lại — vẫn tính sai). Dev hỏi lại đúng 22 → 23/25.
Đếm tổng (không đọc câu): 38 ca bỏ lỡ thì hệ thống **trả lời** 32 ca, xin lỗi 6; gần hết là câu một lượt 5–19 chữ, nhiều nhất ở bộ h6 (15).
Đồng thời bộ mù có **31 ca hỏi lại thừa** (nhãn "trả lời"). Tức là luật hỏi lại **hỏi sai câu** so với cách người viết bộ mù hiểu "mơ hồ" (thiếu 38, thừa 31),
không phải hỏi quá ít.

## 5. Kết luận
1. M1 + M2 sửa đúng lỗi có thật (câu không nêu thủ tục bị trả lời bừa; chữ đệm lọt vào tên thủ tục), không gây hại ở đâu, nên giữ — nhưng **không làm tăng số trên bộ mù**.
2. Câu hỏi thật ngoài đời rất ít khi cần hỏi lại; lỗi lớn hơn trên câu thật là **trả lời nhầm câu ngoài phạm vi** (53/238) và **thiếu từ đồng nghĩa đời thường** (A bị xin lỗi).
3. Model 4B không phán được độ mơ hồ; tìm theo nghĩa không phân biệt được "có trong dữ liệu" với "gần giống".
4. Muốn tăng số hỏi lại trên bộ mù thì phải hiểu cách bộ mù định nghĩa "mơ hồ" — điều không làm được nếu không nhìn vào nó.

## 6. Hướng tiếp (cần trưởng nhóm chọn)
- (a) Tách bộ mù: lấy một nửa số ca hỏi lại (và một số ca trả lời tương tự) làm bộ chọn mới, nửa còn lại giữ mù để đo. Mất một nửa độ tin cậy của bộ mù cho mục này.
- (b) Rà lại nhãn hỏi lại của bộ mù theo một định nghĩa viết ra trước (như mục 1b) — có thể chính nhãn chưa nhất quán (dev cũng có: "thường trú cần những gì" = trả lời nhưng "hỏi về giám hộ" = hỏi lại).
- (c) Làm bảng từ đồng nghĩa đời thường (G4.10) và chặn trả lời nhầm câu ngoài phạm vi — có lợi rõ trên câu thật, dù không phải "hỏi lại".

## 7. Chạy lại
```
python run_server.py research/clarify/build_pool.py          # cần raw/ (tải lại theo mục 1a)
S3_DATA_DB=<db bản 3> python run_server.py research/clarify/run_pool.py
python research/clarify/make_sample.py ; python research/clarify/show.py 0 50 ; python research/clarify/label.py "0:X 1:O ..."
S3_DATA_DB=<db bản 3> python run_server.py research/clarify/features.py      # dùng real_questions_labeled.jsonl, cần Ollama (bge-m3)
S3_DATA_DB=<db bản 3> python run_server.py research/clarify/experiment.py    # bảng mục 3
S3_DATA_DB=<db bản 3> S3_CLARIFY_FILLER=1 S3_CLARIFY_NOPROC=1 python run_server.py research/clarify/llm_judge.py   # M4, cần Ollama
```

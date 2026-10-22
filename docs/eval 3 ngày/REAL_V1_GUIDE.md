# Hướng dẫn gán nhãn bộ `real_v1` (Ngày 2)

Bộ này dùng để chứng minh hệ thống chạy tốt trên câu hỏi **không do nhóm viết để thử hệ thống**: câu thật của người dân (System 3, Y tế), câu do người viết trên Wikipedia (Du lịch văn bản). Riêng 40 câu phần bảng của System 4 soạn khi chỉ nhìn tên cột, `hwng` duyệt từng câu. Nhãn do hai người gán độc lập; bằng chứng nằm ở thứ tự: câu hỏi, rồi nhãn, rồi kết quả. Mọi quy tắc dưới đây có một mục tiêu: nhãn không được chịu ảnh hưởng của hệ thống.

## 1. Có những gì (bảng tổng hợp thành phần câu hỏi)

Tất cả nằm trong `D:\merged_sys3_4\Nhân sys 3_4`, dồn vào hai thư mục: `eval/real_v1/` (System 3) và `system4/eval/real_v1/` (System 4), mỗi thư mục có `README.md` và `LOCK.md`. Cả hai bộ đã đủ câu hỏi (System 3: 300, System 4: 200), chưa có nhãn nào.

| System | Phần | Số câu | Nguồn | File câu hỏi | Script sinh | Cách chấm |
|---|---|---|---|---|---|---|
| 3 (Strict) | `random` | 120 | Bình Định + Bộ Công an (Hugging Face), ngẫu nhiên | `eval/real_v1/cases_real_v1.json` | `eval/real_v1/collect_real_v1.py` | Hành vi (`answer` / `clarify` / `apologize`) + `proc_id` |
| 3 (Strict) | `chude` | 180 | Như trên, lọc theo từ khoá chủ đề cấp xã | cùng file | cùng script | Như trên, đo `top-1` / `top-3` |
| 4 (Friendly) | `du_lich_vqd` | 75 (50 có đáp án, 25 không có trong bài) | UIT-ViQuAD2.0, bài "Vườn quốc gia Phong Nha - Kẻ Bàng" | `system4/eval/real_v1/cases_real_v1_s4.json` | `system4/eval/real_v1/collect_real_v1_s4.py` | Đáp án gốc (`source_gold`); câu không có đáp án thử "không bịa" |
| 4 (Friendly) | `y_te_real` | 85 | `hungnm/vietnamese-medical-qa`, loại 300 câu hệ thống đã nạp | cùng file | cùng script | Chỉ hành vi, không có đáp án |
| 4 (Friendly) | `bang_human` | 40 (Y tế 14, Giáo dục 13, Du lịch 13) | Soạn khi chỉ nhìn tên cột; `hwng` duyệt từng câu (20/10) | `system4/eval/real_v1/cases_real_v1_s4_bang.json` (đủ 40 câu) | Theo `docs/eval 3 ngày/REAL_V1_S4_BANG_FORM.md`; mỗi câu có trường `table` (file Excel nhắm tới) | Đáp án trong bảng |

Tổng: System 3 có 300/300 câu, System 4 có 200/200 câu (160 câu từ Hugging Face + 40 câu phần bảng).
Dữ liệu trung gian: kho thô System 3 ở `research/clarify/raw/`, pool sạch ở `research/clarify/pool_real_v1.jsonl` (1.490 câu), kho thô System 4 ở `research/s4_raw/`.
Đã loại khỏi bộ 266 câu mà nhóm dùng để chọn luật M1/M2 (`research/clarify/real_questions_labeled.jsonl`).

## 2. Quy tắc chung (không phá)

1. Hai người gán nhãn (A và B) làm **riêng**, không hỏi nhau, không xem file của nhau. Mỗi người lưu một file nhãn (mục 3).
2. **Không chạy hệ thống** trên bộ này, không dùng công cụ tìm của hệ thống (web Strict / Friendly) để tìm đáp án. Nhìn kết quả hệ thống thì nhãn bị lệch theo nó. Tra bằng Cổng dịch vụ công, hoặc đọc dữ liệu thô như mục 4.
3. Nhãn dựa trên **câu hỏi như người dùng viết** và **dữ liệu thủ tục bản 3** (1.517 thủ tục, `content_sha256 70c42af1…36bd`). Không đoán theo hệ thống "sẽ trả lời gì".
4. Không sửa chữ trong câu hỏi (kể cả lỗi chính tả, thiếu dấu). Câu hỏi nhờ AI viết lại thì mất giá trị.
5. Mỗi câu một dòng giải thích ngắn (`notes`), cùng kiểu với `eval/H4_ASSUMPTIONS.md`: "vì sao nhãn như vậy".
6. Gán xong không sửa nhãn theo kết quả của hệ thống. Cần chỉnh luật thì làm bộ mới.
7. Không đưa tên thật, SĐT, CCCD vào `notes`. Câu hỏi đã được che (`[TÊN]`, `[ID]`, `[SĐT]`), gặp chỗ sót thì báo, đừng chép lại.

## 3. File nhãn và định dạng

| Người | System 3 | System 4 |
|---|---|---|
| A | `eval/real_v1/real_v1_labels_A.json` | `system4/eval/real_v1/real_v1_s4_labels_A.json` |
| B | `eval/real_v1/real_v1_labels_B.json` | `system4/eval/real_v1/real_v1_s4_labels_B.json` |

### System 3: cùng định dạng `eval/cases_h4.json` (để dùng `eval/run_pseudo.py` và `run_golden.py` không sửa)

```json
{"id": "real_v1-007", "beh": "answer", "expect_ids": ["1.002345"], "fields": ["time"], "notes": "ly lich tu phap: khong co; ..."}
```

- `id`: đúng `id` trong `eval/real_v1/cases_real_v1.json`. Mỗi người gán đủ 300 câu, không bỏ sót.
- `beh`: `answer`, `clarify`, `apologize`, hoặc `skip` (mục 5.4).
- `expect_ids`: danh sách `proc_id` đúng (mục 4 và 5). Rỗng với `apologize` và `skip`.
- `fields`: các mục người hỏi cần: `documents`, `conditions`, `fee`, `time`, `place`, `legal_basis`. Để `[]` nếu câu hỏi chung chung hoặc `beh` không phải `answer`.
- `notes`: một dòng lý do.

Bước gộp (sau khi thống nhất) đổi trường `text` của câu hỏi thành `q`, ghép với nhãn, rồi lưu thành bộ cuối ở `eval/real_v1/cases_real_v1.json`.

## 4. Tìm `proc_id` mà không dùng công cụ của hệ thống

Dữ liệu thô: `data/snapshot/procedures_v3.jsonl` (mỗi dòng một thủ tục, có `proc_id`, `name`, `domain`, `executing_agency`, `province`, `fees`, `processing_time_text`, `checklist`, `steps`, `legal_basis`). Có ba cách tra:

1. **Cổng Dịch vụ công**: trang `https://dichvucong.gov.vn`. Dùng khi cần xem thủ tục thật và đối chiếu mã.
2. **Tìm chữ trong tên thủ tục** bằng một dòng Python:
   ```bash
   python -c "import json,sys; [print(r['proc_id'], r['name'][:110], '|', r.get('province')) for r in map(json.loads, open('data/snapshot/procedures_v3.jsonl', encoding='utf-8')) if 'tạm trú' in r['name'].lower()]"
   ```
3. **Cột `in_scope` trong DB**: bảng `proc_flat` của DB bản 3 (`data/runtime/knowledge/*.db`, bản có 1.517 thủ tục) có cột `in_scope`. `in_scope = 1` là 542 thủ tục cấp xã dùng chung toàn quốc; đây là các thủ tục **trả lời được**. Câu hỏi dùng đọc thông thường của SQLite, không qua truy hồi của hệ thống:
   ```sql
   SELECT proc_id, name, domain, province, in_scope FROM proc_flat WHERE name_fold LIKE '%tam tru%';
   ```

Không dùng `server/` (Strict) hay `system4/` (Friendly) để tra: chúng chính là thứ ta đang đo.

**Mẹo tra:** thử nhiều cách viết cho cùng một từ. Tên thủ tục thường viết đầy đủ ("chứng minh nhân dân", không phải "CMND"; "căn cước", không phải "CCCD"). Khi kết luận "DB không có thủ tục nào", tìm lại ít nhất ba cách viết khác. Lượt A từng gán sai 9 câu vì tra sót kiểu này (xem `BAO_CAO_GAN_NHAN_A_B.md` mục 3.3).

## 5. Chọn `beh` (hành vi mong đợi) cho System 3

Hỏi theo thứ tự:

### 5.1 `answer`: trả lời thẳng
- Câu chỉ **một thủ tục** (hoặc một cặp thủ tục thật sự tương đương) có `in_scope = 1`, và bản mặc định của nó rõ là cái người hỏi cần.
- Câu nêu rõ tỉnh/thành mà thủ tục có bản riêng cho tỉnh đó: `expect_ids` là mã bản của tỉnh nêu.
- Nhiều `proc_id` đều đúng thì ghi hết vào `expect_ids` (như `h4-007`, `h4-012`); lý do viết ở `notes`.
- Câu nhiều ý nhưng cùng một thủ tục ("hồ sơ gì, phí bao nhiêu, bao lâu") vẫn là `answer`; ghi đủ vào `fields`.

### 5.2 `clarify`: phải hỏi lại
- Còn **từ hai thủ tục khác nhau trở lên** đều hợp lý với câu hỏi, và câu hỏi không đủ thông tin để chọn (xin giấy phép xây nhà: cấp mới / điều chỉnh / gia hạn; trợ cấp: nhiều loại). `expect_ids` liệt kê các thủ tục hợp lý.
- Thủ tục chỉ có bản riêng của từng tỉnh mà câu hỏi **chưa nêu tỉnh**.
- Câu hỏi về thủ tục nhưng **không nêu thủ tục nào** ("thủ tục cần giấy tờ gì", "xin giấy tờ nhà"). `expect_ids` rỗng.
- Phép thử: một cán bộ một cửa có trả lời ngay được không, hay phải hỏi lại một câu? Phải hỏi lại là `clarify`.
- Hiếm trên câu thật (4/266 ở lần gán trước), đừng ép câu vào `clarify` khi một thủ tục mặc định vẫn rõ ràng.

### 5.3 `apologize`: từ chối, nói không có
Một trong các điều sau:
- Thủ tục **không có trong dữ liệu** bản 3 (hộ chiếu, lý lịch tư pháp nếu không có, bảo hiểm thất nghiệp, đăng ký công ty).
- Thủ tục có trong dữ liệu nhưng **ngoài phạm vi cấp xã** (`in_scope = 0` và không có bản của tỉnh/xã khớp): cấp tỉnh, trung ương, ngành dọc.
- Câu hỏi **luật / xử phạt / tình trạng hồ sơ cá nhân / lỗi cổng / chuyện cá nhân** (mức phạt vi phạm giao thông, "hồ sơ của tôi đã xong chưa", trò chuyện).
- Không phải câu hỏi về thủ tục hành chính.
Ghi `expect_ids: []`. `notes` nói rõ thuộc nhóm nào, kèm `proc_id` gần nhất nếu có (như `h4-071`).

### 5.4 `skip`: loại khỏi bộ
Chỉ dùng khi câu **không phải câu hỏi** (cụt, chỉ có lời chào, mất nghĩa vì cắt) hoặc **không thể hiểu** nếu không đọc ngữ cảnh gốc. Phải có lý do ở `notes`. Số câu `skip` sẽ được báo cáo, nên đừng dùng cho câu "khó". Hai người cùng `skip` thì bỏ; một `skip` một nhãn khác thì xét ở bước thống nhất.

### 5.5 Trường hợp hay gặp
| Tình huống | Nhãn |
|---|---|
| Câu tiếng Việt không dấu, viết tắt, lỗi chính tả mà vẫn rõ thủ tục | `answer`, nhãn theo thủ tục, ghi `~không dấu` ở `notes` |
| Người dân kể hoàn cảnh dài, câu hỏi chính rõ | `answer` theo câu hỏi chính |
| Hỏi hai việc khác nhau trong một câu (làm CCCD và khai sinh) | Chọn theo việc **chính** (câu hỏi cuối hoặc ý chính); nếu không phân biệt được thì `clarify`, ghi rõ ở `notes` |
| Thủ tục đúng nhưng người hỏi muốn thông tin dữ liệu không có (ví dụ tiến độ hồ sơ) | `apologize` |
| Thủ tục cấp xã nhưng dữ liệu chỉ có bản của tỉnh khác tỉnh người hỏi | `clarify` hoặc `apologize` theo mô tả ở `notes`; chọn `apologize` nếu tỉnh đó không có thủ tục |
| Có hai thủ tục trùng tên (một cấp xã, một cấp tỉnh) | Chọn theo cấp người hỏi nói tới; không rõ thì `clarify` |

## 6. System 4: nhãn

Không dùng `run_pseudo`. Bộ System 4 chấm bằng `system4/eval/bench.py` với luật `check` giống `system4/eval/bench_cases.py` (`any`, `all`, `none`, `refusal`, `ask_back`, `source`). Mỗi người ghi cho mỗi câu:

```json
{"id": "real_v1_s4-001", "check": {"any": ["đường Hồ Chí Minh và đường 20"]}, "notes": "gold khop bai hien tai (du_lich_diem_den.md muc ...)"}
```

### 6.1 `du_lich_vqd` (75 câu)
- Có `source_gold`: tìm trong `system4/eval/real_domains/data/du_lich_diem_den.md` (bài Phong Nha). Nếu bài hiện tại còn chứa đáp án: `check.any` = đáp án gốc cộng cách viết khác bạn thấy trong bài (số, tên gọi). Nếu bài đã đổi hoặc không còn đáp án: `{"drop": true}` và ghi lý do (số câu drop sẽ báo cáo).
- Câu **không có đáp án** (`source_gold` rỗng): đọc bài hiện tại, nếu quả thật không có thì `check.refusal = true` (hệ thống phải nói không có thông tin, không bịa). Nếu bài hiện tại có đáp án thì `drop`.

### 6.2 `y_te_real` (85 câu)
Hệ thống không có đáp án (chỉ nạp 300 hỏi đáp khác). Mỗi câu gán hai nhãn:
- `urgent`: `true` nếu mô tả triệu chứng nguy hiểm cần đi cấp cứu / khám ngay (khó thở, đau ngực, hôn mê, chảy máu nhiều, trẻ sơ sinh sốt cao...), còn lại `false`.
- `needs_image`: `true` nếu câu tham chiếu ảnh, kết quả xét nghiệm, đơn thuốc mà hệ thống không thấy được.
Kỳ vọng khi chấm (ghi ở bước chạy, không cần ghi từng câu): không khẳng định chẩn đoán hay liều thuốc như sự thật, có khuyên đi khám; câu `urgent` phải khuyên khám / cấp cứu ngay; câu `needs_image` phải nói không xem được ảnh. Không có đáp án đúng/sai về nội dung.

### 6.3 `bang_human` (40 câu)
Nguồn: soạn khi chỉ nhìn tên cột, `hwng` duyệt từng câu. Người gán nhãn **được mở** file `.xlsx` ghi ở trường `table` của câu (lúc viết câu thì không được mở). Mỗi câu có thêm `kind_hint` (`lookup`, `filter`, `count`, `compare`, `verify`, `refusal`, `ambiguous`) để rà nhanh; đừng coi nó là nhãn. Với mỗi câu:
- Tìm dòng và cột trả lời được trong bảng; ghi `check.all` / `check.any` bằng giá trị trong bảng, viết theo cách người dùng có thể thấy (có dấu phân cách hàng nghìn thì ghi cả hai dạng).
- Câu đếm hoặc liệt kê: `check.all` = đủ các giá trị cần có; ghi cách đếm ở `notes`.
- Câu mà bảng **không có cột nào chứa** thông tin: `check.refusal = true`.
- Câu mơ hồ (nhiều dòng cùng tên): `check.ask_back = true` và `choices_all` = các dòng trùng.
- Ghi `source` là giá trị cột tên (tên bệnh viện / trường / di tích) của dòng đúng.

## 7. Độ đồng thuận và thống nhất

Sau khi A và B nộp file, chạy `python eval/real_v1/real_v1_agree.py` (System 3) và `python eval/real_v1/real_v1_agree.py --s4` (System 4); thêm `--write` để ghi sườn `REAL_V1_ASSUMPTIONS.md`. Script cho ra:
1. **Cohen's κ** trên `beh`, ba lớp (`answer` / `clarify` / `apologize`; câu `skip` tính riêng).
2. **% khớp `expect_ids`**: hai tập `proc_id` giống hệt nhau, trên các câu cả hai gán `answer`. Báo cả tỷ lệ tập con (một người nhiều hơn).
3. Báo cáo **cả hai con số, kể cả khi thấp**. `eval/ragas_calib.py kappa` không dùng nguyên được vì nó so điểm nhị phân của giám khảo LLM, không phải nhãn ba lớp.

Rồi A và B ngồi cùng nhau xử từng câu bất đồng. Mỗi câu một dòng lý do trong `eval/real_v1/REAL_V1_ASSUMPTIONS.md`, cùng định dạng `H4_ASSUMPTIONS.md`:

```
- real_v1-017 | <câu hỏi> | <nhãn cuối> | A: answer(1.004222), B: clarify | ly do thong nhat
```

Nhãn cuối ghi vào bộ `eval/real_v1/cases_real_v1.json` (S3) và `system4/eval/real_v1/cases_real_v1_s4.json` (S4). Chạy hệ thống **sau** khi bộ nhãn đã khoá.

## 8. Danh sách việc Ngày 2

- [ ] A và B mỗi người đọc hướng dẫn này, kiểm tra tra được `proc_id` bằng một câu thử (câu thử không nằm trong bộ).
- [ ] A gán 300 câu System 3, B gán 300 câu System 3, riêng.
- [ ] A và B gán 200 câu System 4 (160 từ Hugging Face + 40 phần bảng).
- [ ] Chạy `eval/real_v1/real_v1_agree.py` (System 3) và `--s4` (System 4), ghi κ và % khớp.
- [ ] A và B xử các câu bất đồng, ghi lý do vào `eval/real_v1/REAL_V1_ASSUMPTIONS.md`.
- [ ] Gộp nhãn vào bộ cuối, kiểm lại số lượng (S3 300, S4 200, trừ số `skip` / `drop`).
- [ ] Khoá bộ nhãn, rồi mới chạy hệ thống (Ngày 3).

## 9. Kết quả (cập nhật 21/10)

Hai lượt gán nhãn đã xong và đã khoá. Bộ để chạy: System 3 = 282 câu, System 4 = 177 câu (bảng tổng hợp ở mục 1 ghi số câu gốc 300 và 200). Báo cáo: `BAO_CAO_GAN_NHAN_A_B.md`; nhãn cuối và lý do: `eval/real_v1/real_v1_labels_final.json`, `eval/real_v1/REAL_V1_ASSUMPTIONS.md`.

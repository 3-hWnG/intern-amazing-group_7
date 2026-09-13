# Bộ câu hỏi đánh giá — Nhóm 7 / LLM Pháp lý

Sinh ngày 12/09/2026 từ `data_merged.xlsx` (70 thủ tục).
**862 câu hỏi**, mỗi câu đã có nhãn sẵn — không ai phải gán nhãn thủ công.

| | |
|---|---|
| Trong phạm vi | 810 câu (54 topic × 15) |
| Ngoài phạm vi | 52 câu (nhãn = rỗng) |
| Độ phủ | 70/70 dòng của xlsx |
| Tái lập | `SEED = 7` cố định, chạy lại ra kết quả y hệt |

## File

| File | Nội dung |
|---|---|
| `eval_questions.csv` | Bộ dữ liệu, mở được bằng Excel (UTF-8 BOM) |
| `eval_questions.jsonl` | Cùng nội dung, dạng dòng-JSON cho script |
| `report.json` | Thống kê: độ phủ, phân bố biến thể, topic đa nhãn |
| `../build_eval_set.py` | Script sinh — sửa `TOPICS` rồi chạy lại khi thêm dòng mới |
| `../evaluate_retrieval.py` | Script chấm điểm — đặt cạnh `app/`, cho ra con số đầu tiên |

## Cột

| Cột | Ý nghĩa |
|---|---|
| `qid` | Mã câu hỏi, `Q0001`… |
| `question` | Câu hỏi |
| `topic_key` | Mã nhu cầu người dân (`khai_sinh`, `cccd_cap_lai`…), `none` nếu ngoài phạm vi |
| `topic` | Tên nhu cầu, dạng người dân hay nói |
| `gold_row_no` | Dòng đúng trong xlsx, **đếm từ 1**. Nhiều dòng ngăn bằng `;` |
| `gold_chroma_id` | Cùng dòng đó nhưng **đếm từ 0** — khớp id do `ingest.py` sinh ra |
| `gold_title` | Tên thủ tục đúng, để kiểm tra bằng mắt |
| `linh_vuc` | Lĩnh vực, lấy từ xlsx |
| `variant` | Kiểu câu hỏi (xem dưới) |
| `difficulty` | `easy` / `medium` / `hard` |
| `in_scope` | 1 = có đáp án trong dataset, 0 = không |
| `oos_kind` | Với câu ngoài phạm vi: loại nào (`phap_ly`, `muc_phat`, `thoi_su`, `xa_giao`, `mo_ho`, `ngoai_dataset`) |

## Các kiểu câu hỏi

| Kiểu | Số câu | Mục đích |
|---|---|---|
| `situational` | 108 | Câu tình huống viết tay — *"Con tôi mới sinh được 3 ngày, giờ tôi phải làm gì"*. Không chứa tên thủ tục, buộc hệ thống phải **hiểu**, không chỉ khớp từ. Đây là phép thử thật. |
| `facet_docs/time/fee/place/online` | 432 | Hỏi thẳng vào từng trường: giấy tờ, thời gian, lệ phí, nơi nộp, làm online. Dễ nhất — nếu vẫn sai thì lỗi nằm ở tầng nhúng. |
| `no_diacritics` | 54 | Gõ không dấu — *"lam giay khai sinh can gi"* |
| `abbrev` | 54 | Viết tắt — *"đk khai sinh cần gt j"* |
| `typo` | 54 | Lỗi gõ: dính chữ, gõ đúp, nuốt ký tự |
| `keyword` | 54 | Cụt lủn — *"cấp lại thẻ căn cước"* |
| `colloquial` | 54 | Khẩu ngữ — *"ad ơi … vs ạ"* |
| `out_of_scope` | 52 | Không có đáp án đúng |

## Nhãn nhiều dòng — đọc kỹ chỗ này

15 topic ứng với **nhiều hơn một dòng** trong xlsx, vì dataset đang tách theo cấp
thực hiện hoặc bị trùng:

```
cccd_cap_lai        -> dòng 54, 57   (cấp tỉnh / cấp trung ương)
cccd_cap_doi        -> dòng 60, 63
cccd_cap_moi        -> dòng 67, 70
ho_chieu            -> dòng 44, 45
dang_ky_xe_lan_dau  -> dòng 42, 43, 62
antt_cap_moi        -> dòng 46, 47
antt_cap_doi        -> dòng 52, 55
antt_cap_lai        -> dòng 58, 64
thi_thuc_dien_tu    -> dòng 48, 49
giay_phep_xay_dung  -> dòng 23, 25   (trùng nội dung)
khuyet_tat          -> dòng 8, 21    (trùng)
tho_cung_liet_si    -> dòng 10, 13   (trùng)
hoa_tang            -> dòng 9, 14    (trùng)
mai_tang            -> dòng 15, 19
vay_von_viec_lam    -> dòng 26, 30
```

Trả về **bất kỳ dòng nào trong nhóm** đều tính là đúng. Nếu ép một nhãn duy nhất,
hệ thống trả lời đúng vẫn bị chấm sai và con số sẽ nói dối.

Riêng 4 nhóm ghi *(trùng)* là **lỗi dữ liệu, không phải phân cấp** — cần gộp lại
khi dọn dataset. Các nhóm còn lại là do thiếu cột `cấp thực hiện`; khi thêm cột
đó thì tách nhãn lại được.

## Dùng như thế nào

**1. Lấy mốc (làm trước tiên)**
```bash
cd app
python ../evaluate_retrieval.py --eval ../eval/eval_questions.csv
```
Ra `Recall@1`, `Recall@5`, `MRR@10`. Con số này là mốc so sánh cho mọi thay đổi sau.

**2. Chọn ngưỡng HIGH / LOW**
Script in phân bố khoảng cách top-1 của câu trúng, câu trượt và câu ngoài phạm vi.
Đặt `LOW` vào khe giữa nhóm "trúng" và nhóm "ngoài phạm vi".
Nếu hai phân bố chồng lên nhau thì **không ngưỡng nào cứu được** — phải đổi mô
hình nhúng trước, đừng chỉnh số.

**3. Soi lỗi**
Mở `eval_results.csv`, lọc `hit@1 = 0`, nhóm theo `variant`.
- Sai nhiều ở `situational` → hiểu ngữ nghĩa yếu
- Sai nhiều ở `no_diacritics` → mô hình nhúng không chịu được gõ không dấu
- Sai nhiều ở `facet_*` → lỗi ở cách dựng document lúc ingest, không phải ở câu hỏi

**4. Dữ liệu fine-tune**
Ghép `question` với câu trả lời dựng từ dòng gold → cặp in/out đúng định dạng
mentor yêu cầu. Chia train/test theo `topic_key` (không chia ngẫu nhiên theo câu,
nếu không các biến thể của cùng một topic sẽ rơi vào cả hai bên và điểm sẽ ảo).

## Giới hạn cần biết

- Câu hỏi do người viết/sinh ra, **không phải người dân thật**. Điểm ở đây là giới
  hạn trên, thực tế sẽ thấp hơn. Thay bằng log thật ngay khi có.
- Bộ này chấm **truy hồi đúng dòng nào**, không chấm chất lượng câu trả lời sinh ra.
  Việc đó cần rule-based fact check hoặc người chấm.
- 52 câu ngoài phạm vi mới đo được *"có biết từ chối không"*, chưa đo được
  *"fallback có trả lời tử tế không"*.
- Dataset vẫn chưa có `mã thủ tục` và `cấp thực hiện`. Khi bổ sung, sửa `TOPICS`
  trong `build_eval_set.py` rồi chạy lại — nhãn sẽ chính xác hơn.

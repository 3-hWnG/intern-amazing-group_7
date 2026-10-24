# Bộ TEST real_v2 cho System 3 (Strict), 24/10/2026

Từ 24/10, real_v1 (282 câu) đã chạy một lần và đã xem từng câu sai, nên **real_v1 chỉ còn là bộ DEV** để sửa luật. Số báo cáo cuối (và số cho bài báo) lấy trên real_v2.

| File | Là gì |
|---|---|
| `collect_real_v2.py` | Rút 348 câu từ pool sạch của real_v1 (`research/clarify/pool_real_v1.jsonl`), SEED 20261024: 120 `random` + toàn bộ 228 câu `chude` còn lại. Loại 300 câu của real_v1 và 4 dòng đầu pool (đã thấy khi xem định dạng). Commit `a82d970`, trước khi gán nhãn. |
| `find.py` | Công cụ tra `proc_id` khi gán nhãn: đọc thẳng bảng `proc_flat` của DB bản 3, không qua truy hồi của hệ thống. |
| `_work/b01..b08.jsonl` | Nhãn gán tay theo từng lô (nhật ký gán nhãn gốc). |
| `build_labeled.py` | Gộp và kiểm nhãn (đủ id, mã có trong DB, `answer` phải có mã). |
| `real_v2_labels.json` | Nhãn cuối, 348 câu. |
| `cases_real_v2_labeled.json` | **Bộ để chạy**: 313 câu (bỏ 35 `skip`), cùng định dạng `eval/real_v1/cases_real_v1_labeled.json`. |
| `LOCK.md` | Mã băm sha256 lúc khoá. |

## Nhãn

Gán theo `docs/eval 3 ngày/REAL_V1_GUIDE.md` (cùng quy tắc, cùng quy ước với nhãn cuối của real_v1: hỏi tình trạng hồ sơ cụ thể thì `apologize`, hỏi thời gian giải quyết chung thì `answer`; hỏi luật/quy định mà dữ liệu thủ tục không ghi thì `apologize`; thủ tục chỉ có bản theo tỉnh mà câu chưa nêu tỉnh thì `clarify`).

| | answer | clarify | apologize | skip | Tổng |
|---|---|---|---|---|---|
| random | 11 | 1 | 90 | 18 | 120 |
| chude | 48 | 5 | 158 | 17 | 228 |
| **Bộ chạy** | **59** | **6** | **248** | (35 bỏ) | **313** |

19/59 câu `answer` chấp nhận hơn một mã (ví dụ mất giấy khai sinh: bản sao trích lục hoặc đăng ký lại), như real_v1.

## Giới hạn (nói thẳng trong báo cáo)

1. **Một người gán nhãn, và đó cũng là người sửa hệ thống** (Claude, theo quyết định của trưởng nhóm ngày 24/10). Người gán đã đọc 348 câu. Biện pháp: nhãn gán và khoá (sha256 + commit) **trước mọi thay đổi code**; trong lúc sửa không mở lại câu hỏi của real_v2; mọi luật mới chỉ được viết từ real_v1 (dev) và từ dữ liệu thủ tục. Chưa có lượt gán nhãn thứ hai hay lượt kiểm của người.
2. **11 câu gần trùng với real_v1** (tập chữ trùng Jaccard ≥ 0,6; cùng người gửi nhiều lần): `real_v2-013, 133, 152, 154, 164, 188, 212, 263, 268, 288, 297` (10 `apologize`, 1 `answer`). Báo cáo cả bộ 313 câu và bộ "sạch" 302 câu.
3. Câu `clarify` chỉ có 6: không kết luận gì riêng về hỏi lại trên bộ này.

## Kế hoạch đo (ghi TRƯỚC khi sửa code, không đổi sau khi thấy kết quả)

- Cấu hình so sánh: `base` (code lúc khoá) và từng phương án sửa, cộng bản cuối kết hợp. Mỗi cấu hình chạy **đúng một lần** trên real_v2, sau khi code đã đóng băng (ghi mã commit vào kết quả).
- Chế độ chạy như real_v1: `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`, DB bản 3 (`S3_DATA_DB=data/runtime/knowledge/3-423eff02f8.db`). Phương án dùng model 4B (nếu có) chạy Ollama cục bộ, canh nhiệt `eval/thermal.py`.
- Chỉ số, khoảng tin cậy Wilson 95%:
  1. Hành vi đúng (accuracy 3 lớp), như real_v1.
  2. Recall từng lớp; **độ chính xác cân bằng** = trung bình recall `answer` và `apologize` (chỉ số chính; bộ lệch lớp: 79% là `apologize`, luôn từ chối đã được 79%), kèm trung bình 3 lớp.
  3. Top-1 / top-3 / MRR trên 59 câu `answer`; và **trả lời đúng trọn** = hệ thống trả lời VÀ thủ tục đầu tiên đúng.
  4. Hai mốc ngây thơ để so: luôn từ chối; luôn trả lời bằng thủ tục xếp đầu.
- Báo cáo cả 313 câu và 302 câu (bỏ 11 câu gần trùng), cả hai tầng `random` / `chude`.

Chạy (sau khi đóng băng):

```bash
S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 S3_DATA_DB=data/runtime/knowledge/3-423eff02f8.db \
  python run_server.py eval/run_pseudo.py real_v2/cases_real_v2_labeled.json real_v2_<cấu hình>
```

# Code — System 3 (bài 1: *When Rules Should Decide*)

Thư mục này chứa code và kết quả đi kèm bài báo về trợ lý **thủ tục hành chính cấp xã/phường**. Trợ lý chỉ phục vụ thủ tục do cấp xã/phường giải quyết, không phải mọi thủ tục hành chính.

Bản xuất được dựng bằng `tools/make_public_code.py` từ commit ghi ở `EXPORT.txt` của repo phát triển.

## Những gì không có ở đây

- **Văn bản câu hỏi.** Câu hỏi lấy từ hai dataset công khai trên Hugging Face, nhưng cả hai không ghi giấy phép, nên không phát hành lại:
  - `hieunguyen1053/dichvucong_faqs` (config `hoi-dap`);
  - `doanhieung/vn-mps-public-service-qa`.

  Mỗi câu chỉ còn mã câu và vị trí dòng (`labels/*.jsonl`). Để dựng lại văn bản, chạy `python run_server.py eval/rebuild_questions.py`.
- **Dữ liệu thủ tục đã thu.** Dữ liệu từ Cổng Dịch vụ công Quốc gia, thu ngày 13/10/2026, gồm 1.517 thủ tục, không có trong bản này. Cổng không có API chính thức; dữ liệu được lấy qua các JSON endpoint công khai, không cần đăng nhập, mà chính trang web của cổng dùng, với tốc độ 2 yêu cầu/giây. Lược đồ ở `data/snapshot/schema_procedures.sql`; cách dựng DB ở `data/build.py`.
- **Cache đầu ra của model, tệp Excel gán nhãn và log chạy.** Các tệp này có chứa văn bản câu hỏi.
- **Danh sách 17 họ tên** tìm được khi đọc tay. Danh sách này đã bị xoá khỏi `eval/real_v1/collect_real_v1.py`.

## Ánh xạ với bài báo

| Trong bài | Ở đây |
|---|---|
| Base, lớp luật A (§4), cổng ngoài phạm vi | `server/policy/scope.py`, `retrieval/query.py`, `retrieval/rank.py`. Các cờ `S3_*` ghi trong từng tệp |
| Vòng 2 (A2) | Cờ `S3_R2=1` trong `retrieval/` và `server/policy/` |
| Reranker (B) | `retrieval/semantic.py` (`S3_SEMANTIC=1`) |
| LLM reader (C) | `server/planner/reader.py` (`S3_READER=1`) |
| Baseline RAG (R) | `eval/hard/rag4b.py` (prompt `v2`) |
| Chỉ số, McNemar, Wilson | `eval/hard/metrics.py` |
| Giao thức, chạy một lần | `eval/hard/final_runs.sh` (test 1), `eval/hard/final_runs_v4.sh` (test 2), `eval/real_v4/RUN_PLAN.md` |
| Bảng 1–3 | `eval/hard/results/regress/`, `results/test/`, `results/test_v4/` (kết quả từng câu, không có văn bản câu hỏi) |
| Lượt nhãn thứ hai, κ | `eval/real_v2/relabel/` |
| Nhiệt độ máy | `eval/thermal.py`, `results/test_v4/thermal.csv` |

## Khoá và đóng băng

| Bộ | Khoá câu hỏi và nhãn | Code đóng băng |
|---|---|---|
| Test 1 | `7e78438` | `b7010d1` (A/B/C); `65b55af` (R) |
| Test 2 | thứ tự `5499d0f`, nhãn `a79ec5f` | `88cabd6` |

Message của năm commit đã được sửa sau khi chạy; nội dung (tree) không đổi. Bảng đối chiếu ở `eval/hard/results/test_v4/COMMIT_MAP.md`. Trong `stamp.txt`, hash `9c6051a` tương ứng với `88cabd6`.

## Chạy

1. Cài thư viện: `pip install -r requirements.txt`.
2. Dựng DB thủ tục, xem `data/`.
3. Dựng lại câu hỏi: `python run_server.py eval/rebuild_questions.py`.
4. Chạy đánh giá trên dev: `python run_server.py eval/hard/dev.py`. Script dựng lại ở bước 3 ghi câu hỏi vào đúng chỗ mà `dev.py` và `--final real_v2|real_v4` đọc.

Các model chạy tại máy qua Ollama: `qwen3:4b-instruct-2507-q4_K_M` và `bge-m3`. Reranker `BAAI/bge-reranker-v2-m3` chạy bằng transformers.

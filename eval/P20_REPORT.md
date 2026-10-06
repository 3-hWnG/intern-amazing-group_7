# Báo cáo Phase 20 — tính năng chất lượng sống (2026-10-06)

Không đọc/chạy `cases_h3`, `cases_h2`, `cases_team`, `cases_pseudo_real`, `PSEUDO_REAL_ASSUMPTIONS.md`.

## Đã làm
1. **Tạo bảng full.** `GET /procedure/{proc_id}/table` (`server/main.py` -> `answer/answerer.py::procedure_table`): 12 mục (giấy tờ, lệ phí, thời hạn, nơi nộp, hình thức nộp, trực tuyến, các bước, biểu mẫu, cơ quan, căn cứ ban hành, căn cứ pháp lý, mô tả) nguyên văn từ `data.api` + nguồn; không LLM, không cắt; mục thiếu dữ liệu hiện câu "cổng không công bố" (xám). Block direct mang `proc_id` -> UI hiện nút; mục dài >220 ký tự thu gọn trong `<details>`. Dòng cũ "xem đầy đủ trên Cổng Dịch vụ công" thành "… (còn nữa, bấm «Tạo bảng full» để xem đủ)". Cờ `S3_TABLE_BUTTON` (mặc định 1; 0 -> endpoint 404, dòng cũ trở lại, nút ẩn).
2. **Chỉ báo + panel cấu hình.** Nút "AI: bật" (xanh) / "AI: tắt" (xám) ở đầu khung chat; bấm mở panel: Answer Composer (công tắc), Planner rules/hybrid (select), model + đã nạp/chưa nạp, timeout Planner/trả lời, ngưỡng confidence, dev mode. Không dev: panel chỉ xem, một dòng ghi chú ngắn. `/config` thêm `answer_llm`, `answer_timeout`, `model_loaded`, `table_button`; `POST /config` nhận `answer_llm` (đặt `os.environ["S3_USE_LLM"]` của tiến trình; `# ponytail`: mất khi khởi động lại).
3. **Reset chủ đề** (kiểm bằng trình duyệt, xem dưới): tìm thấy và sửa 2 lỗi.
4. **`knowledge/`**: `README.md` (Protocol `search(query,k)->list[Evidence{source,text,score,origin}]`, thư mục `knowledge/import/`, gộp Direct + RAG ở Evidence Bundle, kỳ vọng Verifier) + `interface.py` (chỉ kiểu, không ai import). ARCHITECTURE có bảng map G7 theo hiện trạng.
5. Tài liệu: README, docs/SETUP.md (biến + endpoint + test), docs/ARCHITECTURE.md, PLAN_DOT4.
6. Test mới: `server/tests/p20_api_test.py` (TestClient): bảng đủ 12 mục/404/proc_id có trong block và không có trong chào hỏi, `/config` answer_llm đọc/đổi/403 khi không dev, cờ tắt nút, reset + "cái thứ nhất".

## Kiểm trình duyệt (server tạm S3_USE_LLM=0 S3_DEV=1, đã dừng; Browser pane, đọc DOM + ảnh chụp)
- Chat bình thường: trả lời khai sinh có nguồn, nút "Tạo bảng full" + các nút "dạng khác"; bấm "dạng khác" trả đúng biến thể (lưu động, có yếu tố nước ngoài).
- Tạo bảng full: bảng hiện đủ 12 hàng + "Nguồn", 4 mục dài thu gọn, nút đổi thành "Ẩn bảng".
- Panel cấu hình: "AI: tắt" -> bật công tắc -> badge "AI: bật" xanh, `/config` answer_llm=true; tắt lại -> false. Model hiện "qwen3:4b · đã nạp".
- Thẻ hỏi lại ("trợ cấp hàng tháng"): 4 nút, bấm nút 1 trả đúng thủ tục, thẻ cũ bị khoá.
- Console: không lỗi (trước đó có 1 lỗi 404 `favicon.ico`, đã thêm `<link rel="icon" href="data:,">`).
- Điện thoại 375 px: không cuộn ngang (scrollWidth 375), bảng vừa khung, chip AI và panel hiển thị được.
## Lỗi tìm thấy / đã sửa
- **Reset: "cái thứ nhất" vẫn trỏ thẻ hỏi lại cũ.** Sau "Bắt đầu chủ đề mới" tin trợ lý cuối vẫn chứa danh sách đánh số; `rank.py` đọc lại -> trả thủ tục trong thẻ cũ. Sửa: `reset_facts` chèn tin trợ lý "Đã bắt đầu chủ đề mới" làm tin cuối. Sau sửa: "cái thứ nhất" và "còn lệ phí thì sao" sau reset đều trả "ngoài phạm vi/chưa rõ", không mang thủ tục cũ.
- **Nút cũ vẫn bấm được sau reset.** Sửa ở UI: danh sách nút/thẻ cũ làm mờ, khoá, nhãn "Đã hết hiệu lực (chủ đề mới)".
- **Bố cục điện thoại hỏng sẵn từ trước:** thanh bên 270 px chiếm gần hết màn 375 px (khung chat còn ~100 px). Sửa: ≤760 px thanh bên là lớp phủ, mặc định ẩn.
- Danh sách đã hiển thị sau reset: đã xoá (xác nhận ở lượt trước và qua `shown_procedures` rỗng; test `memory_test`).

## Gate (S3_USE_LLM=0)
`test_data`, `memory_test`, `context_test`, `answer_llm_test`, `planner_hybrid_test`, `p20_api_test`, `smoke_test`, `selftest` xanh. `run.py --name p20 --split all`: DEV cũ 209 top-1 96,3% (>=95), hành vi 97,6% (>=96), bịa số 0,0% (<=3), y hệt P19; DEV 449 top-1 97,4%, HOLDOUT cũ 98,2%. `run_ctx.py`: 89/91.

## Chưa làm / giới hạn
- Chưa kiểm với S3_USE_LLM=1 trên UI (Ollama đang chạy, nhưng chỉ kiểm công tắc, không đo câu LLM).
- Sau khi tải lại trang, nút cũ trong lịch sử không còn bị làm mờ (trạng thái "hết hiệu lực" chỉ ở phiên hiện tại); tin "Đã bắt đầu chủ đề mới" thì có lưu.
- Bảng full theo từng thủ tục/biến thể đang hiện, không gộp họ biến thể.
- `POST /config answer_llm` là trạng thái tiến trình, không bền; nhiều worker uvicorn sẽ không đồng bộ.
- Không có RAG/import (đúng phạm vi); `knowledge/interface.py` chỉ là stub.

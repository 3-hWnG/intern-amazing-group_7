# Đóng góp cho System 3

## Quy ước
- Python, code theo phong cách file xung quanh; comment ngắn. Chỗ đơn giản hoá có trần ghi `# ponytail: <trần> ; <cách nâng cấp>` (tìm bằng `grep -rn "ponytail:"`).
- Chỉ dùng `system3.data.api` để đọc dữ liệu; không truy vấn thẳng bảng gốc từ module khác.
- Mọi quyết định trong Planner/Policy/Answerer phải là luật + dữ liệu để test được. LLM chỉ sinh chữ có trích dẫn và phải qua verifier.
- Không sửa dữ liệu nguồn `data/snapshot/*`. Cập nhật dữ liệu: chép đè hai tệp rồi `python -m system3.data.build` (xem `data/snapshot/SOURCE.md`).
- Không commit `data/runtime/*.db`, `.env`, kết quả đo lớn (xem `.gitignore`).

## Trước khi mở PR
1. `python -m system3.data.tests.test_data`
2. `cd server && python tests/memory_test.py && python tests/context_test.py && python tests/answer_llm_test.py && python tests/planner_hybrid_test.py` (tuỳ chọn: `python smoke_test.py`)
3. `cd eval && S3_USE_LLM=0 python selftest.py` và `python run.py --adapter answer_adapter:adapter --name pr --split all`
4. Không để tụt các cổng hồi quy hiện tại trên DEV cũ (209 ca, id không bắt đầu `p16`/`p18`/`p19`): top-1 ≥ 95%, đúng hành vi ≥ 96%, bịa số ≤ 3%, ngoài phạm vi 30/30; ctx ≥ 89/91; synth TEST-seed ≥ 94%. Chạy thêm `python run_concise.py --name pr` (DEV focus ≥ 90%, task thừa ≤ 2%).
5. Nếu thay đổi hành vi truy hồi/context: chạy `synth_retrieval.py` và so TRAIN-seed với TEST-seed (chênh ≤ 5 điểm), báo cáo số HOLDOUT-3 chỉ khi nghiệm thu.
6. Ghi vào PR: thay đổi gì, nhóm lỗi chung nào được sửa, số trước/sau.

## Việc đang mở (ưu tiên)
Xem "Giới hạn đã biết" và "Việc nên làm tiếp" trong [../README.md](../README.md). Nổi bật:
- hỏi lại khi mơ hồ (HOLDOUT-4 đúng 8/16, pseudo_real 2 đúng 0/3); chọn nhầm bản anh em;
- bộ câu hỏi thật từ người dân (chưa có);
- bộ chấm cho bước LLM sinh chữ; bảng sự kiện đời sống dựng từ `condition_index`;
- RAG/import tài liệu theo `knowledge/README.md`.

Gate hồi quy hiện tại (chế độ luật): DEV cũ 209 top-1 ≥ 95%, hành vi ≥ 96%, bịa số ≤ 3%, ngoài phạm vi 30/30, ctx ≥ 89/91, synth TEST ≥ 94%, DEV focus (`run_concise.py`) ≥ 95%.
Chạy test thêm: `server/tests/planner_hybrid_test.py`, `server/tests/p20_api_test.py`, `server/smoke_test.py` (cần `PYTHONIOENCODING=utf-8` trên Windows).

## Lưu ý về dữ liệu
Dữ liệu thủ tục lấy từ Cổng Dịch vụ công thông qua repo V10.6 của nhóm. Câu trả lời luôn kèm nguồn; không đưa dữ liệu cá nhân thật vào bộ test hay log (Policy che CCCD/SĐT trước khi ghi log).

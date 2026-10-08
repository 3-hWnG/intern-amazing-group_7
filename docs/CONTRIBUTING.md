# Đóng góp cho System 3

## Quy ước
- Python, code theo phong cách file xung quanh; comment ngắn. Chỗ đơn giản hoá có trần ghi `# ponytail: <trần> ; <cách nâng cấp>` (tìm bằng `grep -rn "ponytail:"`).
- Chỉ dùng `system3.data.api` để đọc dữ liệu; không truy vấn thẳng bảng gốc từ module khác.
- Mọi quyết định trong Planner/Policy/Answerer phải là luật + dữ liệu để test được. LLM chỉ sinh chữ có trích dẫn và phải qua verifier.
- Không sửa dữ liệu nguồn `data/snapshot/*`. Cập nhật dữ liệu: chép đè hai tệp rồi `python -m system3.data.build` (xem `data/snapshot/SOURCE.md`).
- Không commit `data/runtime/*.db`, `.env`, kết quả đo lớn (xem `.gitignore`).

## Trước khi mở PR
Tắt nhanh: `python run_server.py eval/run_all.py` chạy mọi gate dưới đây (trừ nhắc bằng tay) và in bảng kèm ngưỡng; `--quick` bỏ synth + perturb. Xem [../eval/REPRODUCE.md](../eval/REPRODUCE.md).
Đặt `PYTHONIOENCODING=utf-8 S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1` (không cần GPU/Ollama). Nếu thư mục clone không tên `system3`, chạy các lệnh Python qua `python run_server.py <script.py>` / `python run_server.py -m <module>` (xem SETUP).
1. `python -m system3.data.tests.test_data`
2. `cd server && python tests/memory_test.py && python tests/context_test.py && python tests/answer_llm_test.py && python tests/planner_hybrid_test.py && python tests/p20_api_test.py && python tests/p23_input_test.py && python tests/p26_memory_test.py && python tests/p30_clarify_test.py && python tests/p31_variants_test.py` và `python smoke_test.py`
3. `cd eval && S3_USE_LLM=0 python selftest.py` và `python run.py --adapter answer_adapter:adapter --name pr --split all`; `python run_ctx.py` (ctx 91 ca) và `python run_ctx.py --name ctx_p23 --split ctx-p23`
3b. **`python eval/check_docs.py` phải sạch** (số trong README khớp `eval/results/`, đường dẫn/lệnh trong tài liệu tồn tại, test nào cũng có trong SETUP/CONTRIBUTING). Sửa tài liệu cùng lúc với số đo; chạy lại bộ đo thì cập nhật README rồi chạy lại script.
4. Không để tụt các cổng hồi quy hiện tại trên DEV cũ (209 ca, id không bắt đầu `p16`/`p18`/`p19`/`p23`): top-1 ≥ 95%, đúng hành vi ≥ 96%, bịa số ≤ 3%, ngoài phạm vi 30/30; ctx ≥ 89/91; synth TEST-seed ≥ 94%. Chạy thêm `python run_concise.py --name pr` (DEV focus ≥ 95%, task thừa ≤ 2%) và `python perturb.py --name pr` (bất biến ≥ 98%).
5. Nếu thay đổi hành vi truy hồi/context: chạy `synth_retrieval.py` và so TRAIN-seed với TEST-seed (chênh ≤ 5 điểm), báo cáo số HOLDOUT-3 chỉ khi nghiệm thu.
6. Ghi vào PR: thay đổi gì, nhóm lỗi chung nào được sửa, số trước/sau.

## Việc đang mở (ưu tiên)
Xem "Giới hạn đã biết" và "Việc nên làm tiếp" trong [../README.md](../README.md), và [KNOWN_ISSUES.md](KNOWN_ISSUES.md). Nổi bật:
- hỏi lại khi mơ hồ (HOLDOUT-4 đúng 8/16, pseudo_real 2 đúng 0/3); chọn nhầm bản anh em;
- bộ câu hỏi thật từ người dân (chưa có);
- người chấm 20 ca của bước LLM sinh chữ (`eval/results/composer_sample20.md`; bộ chấm luật đã có: `eval/score_composer.py`, Phase 27); bảng sự kiện đời sống dựng từ `condition_index`;
- RAG/import tài liệu theo `knowledge/README.md`.

Phase 26 (bộ nhớ người dùng) thêm: `python eval/run_p26.py` (bộ ca `cases_p26.jsonl`, dựng bằng `build_p26.py`): bất biến tắt-hồ-sơ = như cũ phải 100% (nhóm d), hồ sơ sai đối tượng không đổi thủ tục khi câu nêu rõ (nhóm c), số lần hỏi lại giảm so với không hồ sơ (nhóm a, b).

Gate hồi quy hiện tại (chế độ luật; bảng đầy đủ kèm số hiện tại ở [EVAL.md](EVAL.md#cổng-hồi-quy-chế-độ-luật-s3_use_llm0)): DEV cũ 209 top-1 ≥ 95%, hành vi ≥ 96%, bịa số ≤ 3%, ngoài phạm vi 30/30, ctx ≥ 89/91, synth TEST ≥ 94% (`glued` ≥ 90%), **DEV focus (`run_concise.py`) ≥ 95%** (mốc 90% của đợt 4 đã bỏ; B1), task thừa ≤ 2%, `perturb.py` bất biến ≥ 98%, `check_docs.py` sạch.
Test server: `memory_test`, `context_test`, `answer_llm_test`, `planner_hybrid_test`, `p20_api_test`, `p23_input_test` (nhãn lượt, chữ dính, điều kiện), `p26_memory_test` (bộ nhớ người dùng), `p31_variants_test` (Phase 31: tên chung họ nhiều dạng thật -> hỏi lại, nút "dạng khác"), `p30_clarify_test` (hỏi lại khi mơ hồ + điều kiện phải thêm thông tin) và `smoke_test.py` (cần `PYTHONIOENCODING=utf-8` trên Windows). Bản cuối cho người dùng thường: làm hết [FINAL_PRODUCT_CHECKLIST.md](FINAL_PRODUCT_CHECKLIST.md).

## Lưu ý về dữ liệu
Dữ liệu thủ tục lấy từ Cổng Dịch vụ công thông qua repo V10.6 của nhóm. Câu trả lời luôn kèm nguồn; không đưa dữ liệu cá nhân thật vào bộ test hay log (Policy che CCCD/SĐT trước khi ghi log).

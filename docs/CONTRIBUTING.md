# Đóng góp cho System 3

## Quy ước
- Python, code theo phong cách file xung quanh; comment ngắn. Chỗ đơn giản hoá có trần ghi `# ponytail: <trần> ; <cách nâng cấp>` (tìm bằng `grep -rn "ponytail:"`).
- Chỉ dùng `system3.data.api` để đọc dữ liệu; không truy vấn thẳng bảng gốc từ module khác.
- Mọi quyết định trong Planner/Policy/Answerer phải là luật + dữ liệu để test được. LLM chỉ sinh chữ có trích dẫn và phải qua verifier.
- Không sửa dữ liệu nguồn `data/snapshot/*`. Cập nhật dữ liệu: chép đè hai tệp rồi `python -m system3.data.build` (xem `data/snapshot/SOURCE.md`).
- Không commit `data/runtime/*.db`, `.env`, kết quả đo lớn (xem `.gitignore`).

## Trước khi mở PR
1. `python -m system3.data.tests.test_data`
2. `cd server && python tests/memory_test.py && python tests/context_test.py && python tests/answer_llm_test.py`
3. `cd eval && S3_USE_LLM=0 python selftest.py` và `python run.py --adapter answer_adapter:adapter --name pr --split all`
4. Không để tụt các cổng hồi quy hiện tại trên DEV: top-1 ≥ 87%, bịa số ≤ 3%, ngoài phạm vi 30/30.
5. Nếu thay đổi hành vi truy hồi/context: chạy `synth_retrieval.py` và so TRAIN-seed với TEST-seed (chênh ≤ 5 điểm), báo cáo số HOLDOUT-3 chỉ khi nghiệm thu.
6. Ghi vào PR: thay đổi gì, nhóm lỗi chung nào được sửa, số trước/sau.

## Việc đang mở (ưu tiên)
Xem mục "Giới hạn đã biết" và "Việc nên làm tiếp" trong [../README.md](../README.md). Nổi bật:
- hỏi lại khi mơ hồ (HOLDOUT-3 đúng 2/8), chọn theo thứ tự, câu không có trong kho;
- bảng sự kiện đời sống (`_EVENTS` trong `retrieval/context.py`) mới 5 sự kiện, nên dựng từ `condition_index`;
- sửa `server/smoke_test.py`;
- bộ chấm cho bước LLM sinh chữ.

## Lưu ý về dữ liệu
Dữ liệu thủ tục lấy từ Cổng Dịch vụ công thông qua repo V10.6 của nhóm. Câu trả lời luôn kèm nguồn; không đưa dữ liệu cá nhân thật vào bộ test hay log (Policy che CCCD/SĐT trước khi ghi log).

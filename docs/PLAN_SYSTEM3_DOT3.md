# Plan đợt 3 — System 3 (tiếp sau đợt 1–2)

Mục tiêu: đóng các khoản nợ trong checklist, đưa System 3 từ "chạy được" lên "đo được, dùng thử được".
Nguyên tắc: mỗi phase có cổng nghiệm thu bằng số đo trên `eval/`. Không qua cổng thì không sang phase sau.

## Phase 7 — Xác nhận nền (0,5 ngày)
- Chạy lại `server/e2e_test.py` (kiểm tra dạng mặc định + chống trùng xin lỗi).
- Mở UI trên trình duyệt: gửi 5 lượt, bấm nút thẻ hỏi lại, bấm nút "dạng khác", nhập free-text.
- Ghim `requirements.txt` (`pip freeze` các gói thật sự dùng). Kiểm tra gói agent 3 đã cài thêm.
- **Cổng:** e2e chạy sạch, UI không lỗi console, `pip install -r` trên venv mới chạy được.

## Phase 8 — Bộ test tin cậy hơn (1 ngày)
Làm trước các phase sửa lỗi để số đo không còn là "tune trên chính bộ test".
- Tách `cases.jsonl` thành DEV (tune) và HOLDOUT (chỉ chạy khi nghiệm thu). Thêm ~60 câu holdout mới, viết khác văn phong.
- Thêm bộ chấm cho phần LLM: điều kiện, so sánh, phủ định, thứ tự. Chấm bằng luật (có/không nhắc đúng mục dữ liệu).
- Bạn duyệt lại đáp án mong đợi của nhóm clarify, chitchat, multi-intent >3 (đang là giả định của tôi).
- **Cổng:** `run.py` in riêng số DEV và HOLDOUT; HOLDOUT lệch DEV không quá 5 điểm top-1.

## Phase 9 — Độ trễ Planner (1 ngày)
- Đo tỉ lệ gọi LLM hiện tại và lý do gọi (uncertain / ambiguous / conditional / multi-sentence).
- Thu hẹp gate: chỉ gọi LLM khi câu có điều kiện hoặc so sánh, hoặc khi luật không chọn được. Mặc định luật.
- Đặt timeout cứng (vd 2,5 s) rồi fallback luật. Thử `num_predict` nhỏ và prompt ngắn hơn.
- Máy dev: GTX 1660 Super 6 GB. Đặt `keep_alive` 30 phút và nạp trước model khi server khởi động; kiểm `ollama ps` ra 100% GPU.
- **Cổng (đã nới, bạn duyệt):** Planner p95 ≤ 4 s, tổng p95 ≤ 8 s; lần gọi đầu (nạp model) tính riêng, ≤ 10 s; top-3 và fields không thấp hơn luật-thuần.

## Phase 10 — Ngoài phạm vi và phủ định (2 ngày)
- Ngoài phạm vi: thêm cổng "từ khớp tình cờ" (đội tuyển, ly hôn tòa án, nhãn hiệu): yêu cầu khớp từ-đặc-trưng của tên thủ tục, không chỉ từ chung. Thêm danh sách chủ đề ngoài hệ thống (thể thao, giải trí, tư pháp tòa án, sở hữu trí tuệ).
- Phủ định: nhận "không phải X", "không có X" → loại biến thể chứa X, chọn biến thể còn lại.
- Thứ tự: "cái thứ nhất/hai/ba" trỏ vào danh sách đã hiển thị (dùng `shown_procedures`).
- **Cổng:** ngoài phạm vi ≥ 27/30; fabrication ≤ 3%; không giảm top-1 trên HOLDOUT.

## Phase 11 — LLM trả lời có kiểm soát (2–3 ngày)
Chỉ cho: so sánh 2 thủ tục, giải thích điều kiện áp dụng. Câu hỏi một mục vẫn bằng code.
- LLM nhận *đúng* các đoạn dữ liệu đã trích, trả JSON `{ý, trích_dẫn_id}`; code ghép lại và gắn nguồn.
- Verifier mở rộng: số và tên văn bản phải nằm trong dữ liệu đưa vào; cấm "miễn phí" khi không có dữ liệu; sai thì fallback câu trả lời bằng code.
- Thay `_condition_note` (trùng âm tiết) bằng bước này, giữ bản cũ làm fallback.
- **Cổng:** bộ chấm Phase 8 cho nhóm điều kiện/so sánh ≥ 70%; verifier chặn 100% mẫu bịa số cố tình; p95 tổng ≤ 6 s.

## Phase 12 — Bộ nhớ và phiên (1 ngày)
- Reset `session_facts` (nút "Bắt đầu chủ đề mới" + lệnh nhận từ câu "hỏi việc khác").
- Hết hạn fact theo lượt khi đổi thủ tục.
- Danh sách dev để admin duyệt `default_variant` (đã chốt từ plan đầu).
- **Cổng:** test hội thoại 10 lượt có đổi chủ đề, fact cũ không rò sang thủ tục mới.

## Phase 13 — Nghiệm thu và bàn giao (0,5 ngày)
- Chạy toàn bộ DEV + HOLDOUT, cập nhật `README.md`, `BASELINE.md`, bảng số đo.
- Ghi lại giới hạn còn lại, không hứa hơn số đo.

## Thứ tự và phụ thuộc
7 → 8 → (9, 10 song song được) → 11 → 12 → 13.
Phase 8 phải xong trước 9–11 vì các phase đó cần HOLDOUT để chứng minh.

## Quyết định cần bạn (không chặn Phase 7–9)
1. Duyệt lại đáp án mong đợi nhóm clarify/chitchat/multi-intent (Phase 8).
2. Nếu Phase 9 không đạt 3 s với Qwen3-4B: chấp nhận luật làm mặc định, hay thử model khác?
3. Phase 11 có đáng làm không, nếu bộ chấm cho thấy câu trả lời bằng code đã đủ?

## Rủi ro
- LLM 4B không giúp được thật: phương án lùi là bỏ LLM khỏi đường chính, giữ cho điều kiện/so sánh.
- Bộ HOLDOUT do tôi viết có thể cùng văn phong với DEV: nên có ít nhất 20 câu do bạn viết hoặc lấy từ log thật.

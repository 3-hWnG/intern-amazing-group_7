# Báo cáo ngắn đợt 4 — System 3 (2026-10-06)

> Cập nhật 2026-10-07 (sau Phase 23–25): số hiện tại nằm ở [../README.md](../README.md) (HOLDOUT-4 top-1 78%, hành vi 84%; bộ team 8/10; TC02 đã pass nhờ corpus nhóm, TC03 là đáp án nhóm cần sửa, TC06 còn mở: [KNOWN_ISSUES.md](KNOWN_ISSUES.md)). Mục "Cần nhóm quyết" 3 và 4 dưới đây đã được trả lời (TC02 có dữ liệu nhóm; bước sinh chữ bật mặc định). File này giữ nguyên là báo cáo đợt 4.

## Mục tiêu của đợt
Theo phản hồi của nhóm: trả lời **đúng ý hỏi** (concise), bớt multi-intent lung tung, hỏi lại khi mơ hồ, UI có chỉ báo AI, nút "Tạo bảng full"; và thử hướng LLM làm Planner (kiến trúc G7).

## Đã làm
- **Concise:** dựng chỉ số `eval/run_concise.py` (hỏi gì trả đó). DEV focus 70% → 99%, task thừa 11/230 → 0. Nguyên nhân gốc: cụm chỉ-field bắt sai, câu điều kiện/nối rơi về 4 mục mặc định, tách task thừa từ "bao lâu"/lời kể.
- **Bộ test chung của nhóm (10 câu):** PASS 3/10 → 7/10 (chấm luật, không phải điểm chính thức).
- **Planner hybrid (Qwen3-4B nền, timeout 7 s):** đã làm đủ cơ chế (luật mặc định, LLM chỉ sửa khi chắc + qua Policy, trace, `/config`). **Đo cho thấy không có lợi** → mặc định vẫn là luật; hybrid là tuỳ chọn.
- **UI:** nút "Tạo bảng full" (nguyên văn dữ liệu, không LLM), chỉ báo "AI bật/tắt" + panel cấu hình gọn, sửa 2 lỗi "Bắt đầu chủ đề mới" và 1 lỗi bố cục điện thoại.
- **Chuẩn bị RAG:** `knowledge/README.md` + stub interface (chưa build).
- **Dọn kho:** `eval/results/` 58 MB → 2,8 MB.

## Số thật (bộ mù, câu gõ tự do; luật thuần)
| | top-1 | đúng hành vi | hỏi lại đúng |
|---|---|---|---|
| HOLDOUT-4 (mới nhất) | 75% | 82% | 8/16 |
| pseudo_real 2 | 68% | 68% | 0/3 |
| HOLDOUT-3 (chạy lại) | 75% | 86% | - |
Mục tiêu top-1 ≥ 80% và hành vi ≥ 88% **chưa đạt**. Các số 96–99% trên DEV là bộ đã tune, không dùng để khoe.

## So với kiến trúc G7
Box 1, 2, 4, 5A, 6A, 10 đã có. Box 3 (LLM Semantic Planner): đã làm hybrid nhưng đo không có lợi nên tắt. Box 5B/6B (RAG, import): chưa làm, chỉ có thiết kế. Box 7–9: Answerer trích nguyên văn + LLM chỉ sinh chữ cho điều kiện/so sánh, có verifier (kiểm số/tên văn bản, chưa kiểm nghĩa).

## Vì sao LLM Planner không giúp
Qwen3-4B tự báo confidence 0,99 cho 65% câu kể cả khi sai nên ngưỡng không lọc được; hay thêm ý thứ hai từ lời kể và chọn bản "đăng ký lại". Muốn thử tiếp: model lớn hơn hoặc hiệu chỉnh confidence; hạ tầng đã sẵn.

## Cần nhóm quyết
1. Cung cấp 20–30 câu hỏi thật (log/người dân) làm bộ kiểm cuối.
2. Có đầu tư vòng sửa "hỏi lại khi mơ hồ" (điểm yếu số 1) và chọn nhầm anh em trước khi demo không.
3. Đáp án nhóm cho lệ phí khai sinh (TC02: bản sao 8.000đ) không có trong snapshot: cần xác nhận nguồn.
4. Giữ hay tắt hẳn bước LLM sinh chữ (lúc viết báo cáo này chưa đo; đã đo ở Phase 27: không làm tụt chỉ số nào, hơn bản code về độ ngắn gọn, giá trị thật chờ người chấm; xem `eval/P27_REPORT.md`).
5. Có làm RAG/import (Box 5B/6B) trong đợt sau không.

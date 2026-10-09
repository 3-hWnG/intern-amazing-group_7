# Phase 2 — retrieval (không LLM)

Chạy đo: `cd eval && PYTHONPATH=<ROOT> python run.py --adapter retrieval_adapter:adapter --name phase2`
Quét tham số: `python eval/sweep.py` (tune trên id chẵn = DEV, báo id lẻ = TEST).

| | Baseline V10.6 | Phase 2 |
|---|---|---|
| top-1 (141 câu có đáp án) | 11% | 84% |
| top-3 | 18% | 92% |
| p50 / p95 | 32 / 45 ms | 7 / 15 ms |

Giới hạn đã biết (để Planner/Policy xử lý, không cố vá bằng luật):
- Câu ngoài phạm vi vẫn lọt 8/30 (7/8 mang cờ `uncertain`): "làm hộ chiếu" khớp "Trình báo mất hộ chiếu" thật sự có trong kho
  -> cần LLM xác nhận ứng viên có đúng yêu cầu không.
- 61/144 câu in-scope mang `uncertain` (~42%) -> chi phí LLM xác nhận; 70 câu `ambiguous` (nhiều nhóm sát điểm).
- Điều kiện/context ("nếu hộ nghèo…") chưa được tách; bỏ regex tách vì sai hướng. Việc của Planner.
- Chỉ số fields (70%) là cue-rule thô; Planner thay thế.
- Tham số tune trên 185 câu của chính bộ test (DEV/TEST chẵn-lẻ chỉ giảm chứ không loại bỏ quá khớp).

## Bộ nhớ ngữ cảnh (đợt context memory)
- `context.py`: `ConvState` (thủ tục đang nói `topic`, `history` theo lần nói gần nhất, `order` theo lần nói đầu tiên, mục đang hỏi `fields`, lời kể chưa gắn thủ tục `story`, `loose` = thủ tục suy ra từ lời kể) và `markers()` tách chữ DIỄN NGÔN (cái đó, nó, quay lại, ý tôi là, lúc nãy, chắc không...) khỏi chữ NGHIỆP VỤ trước khi xếp hạng. Cờ: anaph, corr, back, meta, conn, tail, cond, need.
- `rank._contextualize` là bước quyết định, mỗi đoạn mang `decision` + `why` (vào `plan.ctx` và `trace["ctx"]`): `follow_up` (cùng thủ tục) | `new_related` (thủ tục mới cùng lĩnh vực, kế thừa mục đang hỏi nếu có từ nối) | `return` (quay lại thủ tục đã nói: theo tên / "cái đầu tiên" / "cái trước đó") | `independent`/`new` | `correction` (sửa ý) | `story` (lời kể sự kiện -> thủ tục).
- Quy tắc kế thừa: có tên thủ tục mới phủ chắc (`_is_named`: >=2 chữ khớp, phủ tên >= 0.2, chữ hiếm không nằm trong tên <= 45%) thì KHÔNG kế thừa; không tên + tín hiệu mạnh ("nếu ... thì sao", "thì sao") thì kế thừa; tín hiệu vừa (từ nối, đại từ, hỏi mục, "cần làm gì") chỉ kế thừa khi không còn chữ nghiệp vụ lạ (trừ thủ tục `loose`). Không tín hiệu nối: độc lập. Chủ đề ngoài hệ thống (OOS_TOPICS, hộ chiếu) không bao giờ kế thừa.
- Trạng thái lưu ở `server/db` (bảng `conv_state`), orchestrator ghi theo thủ tục THỰC SỰ đã trả lời; không có thì `resolve` dựng lại bằng cách chạy lại các lượt user.
- Giới hạn: bảng sự kiện đời sống `_EVENTS` (11 sự kiện), ngưỡng `WEAK_NAME`, `NAMED_PREC`, "đếm >=3 chữ hiếm lạ" chọn theo ctx-dev; câu nối chỉ dựa vào 1 chữ nghiệp vụ trùng tình cờ vẫn có thể lệch.

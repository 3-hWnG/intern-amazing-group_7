# System 3 — Trợ lý thủ tục hành chính cấp xã/phường (trạng thái sau đợt 4, 2026-10-06)

Project RIÊNG, dùng lại dữ liệu của repo V10.6 (snapshot trong `data/snapshot`, 1.350 thủ tục). Không import Backend/Frontend của V10.6.
Tài liệu: [docs/SETUP.md](docs/SETUP.md) (cài đặt) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/EVAL.md](docs/EVAL.md) (cách đo, quy tắc bộ mù) · [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) · [docs/BAO_CAO_DOT4.md](docs/BAO_CAO_DOT4.md) (báo cáo ngắn cho nhóm) · kế hoạch: [PLAN_SYSTEM3](docs/PLAN_SYSTEM3.md), [DOT3](docs/PLAN_SYSTEM3_DOT3.md), [DOT4](docs/PLAN_SYSTEM3_DOT4.md).
Chạy: `PYTHONPATH=<gốc repo> python server/main.py` (cổng 8300; cần Ollama + `qwen3:4b` chỉ khi bật bước sinh chữ).

## Kiến trúc đang chạy
User → Orchestrator → **Planner (luật; Qwen3-4B hybrid là tuỳ chọn, TẮT mặc định)** → Policy/Router (luật) → Answerer (code, nguyên văn + nguồn) → [LLM chỉ sinh chữ giải thích điều kiện/so sánh, mọi ý qua verifier, lỗi/timeout 5 s thì giữ bản bằng code] → câu trả lời. Map với kiến trúc G7 của nhóm: xem [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Box 1–4, 5A, 6A, 10 đã có; 3 (LLM Planner) làm hybrid nhưng không bật; 5B/6B (RAG, import) mới chỉ có thiết kế giao diện trong `knowledge/`.

| Thư mục | Nội dung |
|---|---|
| `data/` | build DB từ snapshot, `fees_clean`, `field_chunks`, `condition_index`, `families`, `synonyms`, `api.py` (cửa vào duy nhất) |
| `retrieval/` | tách câu, xếp hạng IDF có dấu, cổng phạm vi, phủ định/thứ tự (`refs.py`), trạng thái hội thoại (`context.py`) |
| `server/planner/` | luật mặc định; `hybrid.py` = luật + Qwen3-4B nền (tuỳ chọn) |
| `server/policy/` | chống chèn lệnh, che PII, kiểm căn cứ, phạm vi, hỏi lại khi ≥ 3 bản gần nhau |
| `server/answer/` | trả lời bằng code + nguồn; `llm_answer.py` + `verifier.py` (sinh chữ có kiểm) |
| `server/orchestrator.py`, `db/` | bộ nhớ hội thoại, reset chủ đề, trace |
| `web/` | UI chat: quản lý hộp thoại (menu ⋯: ghim/bỏ ghim, xuất Markdown/JSON/PDF, đổi tên, xoá; nhấp đúp để đổi tên; "Xoá tất cả"; API `PATCH {title?, pinned?}`, `GET /conversations/{id}/export?format=md|json|pdf` (pdf = trang in, trình duyệt tự mở hộp thoại in để Lưu thành PDF), `DELETE /conversations`), nút "Tạo bảng full", chỉ báo + panel cấu hình AI (`/config`), "Bắt đầu chủ đề mới", "dạng khác" |
| `knowledge/` | chỉ thiết kế giao diện RAG/import (chưa build) |
| `eval/` | bộ test + bộ chấm (xem docs/EVAL.md) và các báo cáo `P18/P19/P20_REPORT.md` |

## Số đo (chế độ luật, `S3_USE_LLM=0`)
**Số để nói với người ngoài là các bộ MÙ** (câu viết kiểu người dân, hệ thống chưa từng được tune trên chúng):

| Bộ mù | top-1 | top-3 | đúng hành vi | hỏi lại đúng | xin lỗi đúng |
|---|---|---|---|---|---|
| **HOLDOUT-4** (90 mục / 106 lượt, mới nhất) | **75%** (58/77) | 81% | **82%** (87/106) | 8/16 | 13/13 |
| pseudo_real 2 (30 mục / 34 lượt) | 68% (19/28) | 71% | 68% | 0/3 | 2/3 |
| HOLDOUT-3 (88 câu, chạy lại sau đợt 4) | 75% (50/67) | 78% | 86% | - | - |
| pseudo_real 1 (30 mục / 42 lượt; đã bị xem lỗi) | 57% (17/30) | 60% | 74% | 1/6 | 6/6 |
| Bộ team (10 câu của các team, chấm luật) | - | - | 7/10 PASS | - | - |

Bịa số trên HOLDOUT-3: 3,4% (trước đợt 4: 7,1%). Chưa đo bịa số trên HOLDOUT-4/pseudo_real.
**Kết luận trung thực: chọn đúng thủ tục khi người dân gõ tự do còn quanh 75% top-1; hỏi lại khi mơ hồ chỉ đúng một nửa (8/16, 0/3).** Mục tiêu đặt ra cho đợt 4 (top-1 ≥ 80%, hành vi ≥ 88%) **chưa đạt**.

Số trên bộ đã tune (chỉ để theo dõi hồi quy, không dùng để khoe):
| | kết quả |
|---|---|
| DEV cũ 209: top-1 / hành vi / bịa số | 96,3% / 97,6% / 0,0% |
| ngoài phạm vi (DEV) | 30/30 |
| ctx (hội thoại) top-1 lượt cuối | 89/91 |
| synth (câu tự sinh từ DB) TRAIN / TEST | 96,3% / 96,3% |
| Baseline V10.6 (185 câu cũ, lúc đầu) | top-1 11%, hành vi 32% |

### Concise = trả lời đúng ý hỏi (`eval/run_concise.py`)
Định nghĩa của nhóm: hỏi giá thì chỉ báo giá. Chấm bằng luật:
| | gốc (đầu đợt 4) | hiện tại |
|---|---|---|
| DEV focus (không dư mục, không thiếu mục) | 70% | 99% (284/288) |
| HOLDOUT cũ focus | 59% | 96% |
| task thừa (kéo thêm thủ tục không hỏi) | 11/230 | 0/377 |
| bộ team: PASS (chấm luật) | 3/10 | 7/10 |
Lưu ý: số focus 99% nằm trên DEV đã tune (gồm ca agent tự soạn); trên câu thật còn lỗi (bộ team còn 3 câu FAIL: một do dữ liệu lệch với đáp án nhóm (8.000đ không có trong snapshot), một do đáp án mong cả thời hạn khi chỉ hỏi giấy tờ, một do điều kiện tang lễ).

### LLM
- **Planner hybrid (Qwen3-4B): không có lợi, tắt mặc định.** Đo công bằng (timeout 7 s, 0% timeout): không có lần sửa nào làm đúng hơn đáp án; confidence tự báo 0,99 cho 65% câu kể cả khi sai. Trên bộ mù HOLDOUT-4 hybrid kém luật 2 câu (56/77 vs 58/77), team 5/10 vs 7/10. Chi tiết: `eval/P19_REPORT.md`.
- **Bước sinh chữ (Answer Composer)**: điểm bộ chấm không đổi khi bật/tắt; hay chạm timeout 5 s. Giá trị chưa được chứng minh.
- Độ trễ (GTX 1660 Super 6 GB): luật p50 ~20 ms, p95 ~80 ms; bật sinh chữ p95 ~5 s.

## Giới hạn đã biết (đừng hứa hơn)
- Chọn thủ tục tổng quát hoá ~75% top-1 trên câu mù; DEV 96% là tune quá khớp.
- **Hỏi lại khi mơ hồ yếu** (8/16, 0/3 trên hai bộ mù mới); câu mơ hồ kiểu đời sống ("làm giấy tờ cho con") vẫn bị xin lỗi thay vì hỏi lại.
- Top-3 trên HOLDOUT-3 giảm sau đợt 4 (82% → 78%) dù top-1 tăng: danh sách ứng viên ngắn hơn.
- Lời kể chứa tên thủ tục có thể chọn nhầm bản anh em (cùng họ, khác loại).
- "Ở đâu" chung chung trả **cơ quan giải quyết** khi cổng không ghi địa điểm (bộ test cũ không thống nhất giữa `address` và `agency`).
- Khớp hoàn cảnh với `condition_index` là khớp chữ + bảng ~8 nhóm từ đời thường; kết hôn/khai sinh chỉ có dòng "đối tượng" nên trả "cổng không công bố riêng".
- Phí dùng được chỉ 467/1.350 thủ tục (35%); phần còn lại trả "cổng không công bố". Lệ phí 8.000đ nhóm mong ở TC02 không có trong snapshot.
- Verifier của bước sinh chữ chỉ kiểm số, tên văn bản, "miễn phí", không kiểm nghĩa.
- Bảng sự kiện đời sống (`_EVENTS`) chỉ 5 sự kiện viết tay.
- Planner luật không sinh `context_facts`: `session_facts` luôn rỗng ở cấu hình mặc định.
- Còn sai 4 ca ctx (hold-74/76/91, context_memory-15) chưa có nguyên nhân chung.
- Bảng full hiện theo từng biến thể, chưa gộp họ; công tắc AI là trạng thái tiến trình (nhiều worker sẽ không đồng bộ); tải lại trang thì nút cũ không còn bị làm mờ.
- Không có RAG hay import tài liệu (Box 5B/6B).
- **Tất cả bộ test do agent/Claude soạn; chưa có câu hỏi thật từ log người dân.** Đáp án giả định ghi trong `eval/*ASSUMPTIONS.md`.
- `requirements.txt` ghim đúng bản đang chạy nhưng chưa cài thử được trên venv sạch (máy thử không có mạng tin cậy tới PyPI).
- Quy tắc nghiệm thu: không tune trên HOLDOUT-3/4 (xem docs/EVAL.md). Trước khi tune tiếp phải soạn bộ mù mới.

## Việc nên làm tiếp
1. **Câu hỏi thật** (20–30 câu từ log/người dân) làm bộ kiểm cuối; đây là cách duy nhất biết số đo ngoài đời.
2. Sửa nhóm lỗi **hỏi lại khi mơ hồ** và chọn nhầm anh em/chọn thứ tự; sau đó soạn HOLDOUT-5 để kiểm.
3. Quyết định số phận bước sinh chữ: dựng bộ chấm riêng (người chấm 20 câu), không có lợi thì tắt hẳn (`S3_USE_LLM=0`).
4. Nếu nhóm vẫn muốn LLM Planner: cần model lớn hơn hoặc hiệu chỉnh confidence (cơ chế hợp nhất, trace, công tắc đã có sẵn).
5. RAG/import (Box 5B/6B) theo thiết kế trong `knowledge/README.md`.

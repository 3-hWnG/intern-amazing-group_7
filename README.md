# System 3 — trạng thái sau đợt 3 (2026-10-05)

Project RIÊNG, dùng lại dữ liệu của repo V10.6 (`repo/Database`, snapshot trong `data/snapshot`). Không import Backend/Frontend của V10.6.
Tài liệu: [docs/SETUP.md](docs/SETUP.md) (cài đặt), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/EVAL.md](docs/EVAL.md) (đo và quy tắc bộ mù), [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md), kế hoạch: [docs/PLAN_SYSTEM3.md](docs/PLAN_SYSTEM3.md), [docs/PLAN_SYSTEM3_DOT3.md](docs/PLAN_SYSTEM3_DOT3.md).
Chạy: `PYTHONPATH=<gốc repo> python server/main.py` (cần Ollama + `qwen3:4b` nếu bật bước sinh chữ). Cổng 8300.

## Kiến trúc đang chạy
User -> Orchestrator -> **Planner (luật, không LLM)** -> Policy/Router (luật) -> Answerer (code) -> [LLM chỉ sinh chữ giải thích điều kiện/so sánh, mọi ý qua verifier, lỗi/timeout thì giữ bản bằng code] -> câu trả lời.

| Thư mục | Nội dung |
|---|---|
| `eval/` | bộ test: DEV 209, HOLDOUT 67 (đã dùng để sửa), HOLDOUT-2 62 (ô nhiễm một phần), **HOLDOUT-3 88 (mù, số chính thức)**; `run.py`, `rules_scorer.py`, `synth_retrieval.py` (câu tự sinh từ DB), `cases_ctx.*` + `run_ctx.py` (hội thoại nhiều lượt) |
| `data/` | build DB, `fees_clean`, `field_chunks`, `condition_index`, `families`, `synonyms`, `api.py` |
| `retrieval/` | tách câu, xếp hạng IDF có dấu, cổng phạm vi/chủ đề ngoài hệ thống, phủ định, thứ tự (`refs.py`), **trạng thái hội thoại (`context.py`)** |
| `server/planner/` | luật mặc định; nhánh LLM còn trong code nhưng tắt (`S3_PLANNER_LLM=1` mới bật) |
| `server/policy/` | chống chèn lệnh, che PII, kiểm căn cứ, phạm vi, field_status, biến thể mặc định, hỏi lại khi >= 3 bản gần nhau |
| `server/answer/` | soạn bằng code + nguồn; `llm_answer.py` + `verifier.py` cho bước sinh chữ có kiểm |
| `server/orchestrator.py`, `db/` | bộ nhớ: thủ tục đã nói, mục đang hỏi, `session_facts` gắn thủ tục, `conv_state`; reset chủ đề |
| `web/` | UI chat: nút "Bắt đầu chủ đề mới", nút "dạng khác", trang dev duyệt `default_variant` (`/dev/variants.html`, chỉ khi `S3_DEV=1`) |

## Số đo (rules-only, `S3_USE_LLM=0`)
| | top-1 | top-3 | đúng hành vi | bịa số |
|---|---|---|---|---|
| Baseline V10.6 (185 câu cũ) | 11% | 18% | 32% | - |
| Cuối đợt 2 (185 câu cũ, đã tune) | 84% | 92% | 90% | 6% |
| DEV 209 (đã tune) | 90,2% | 97,0% | 96,7% | 2,9% |
| HOLDOUT 67 (đã dùng để sửa) | 94,5% | 98,2% | 94,0% | 4,5% |
| HOLDOUT-2 62 (ô nhiễm một phần) | 70,2% | 74,5% | 79,0% | 7,0% |
| **HOLDOUT-3 88 (mù)** | **73,1%** | **82,1%** | **83,0%** | **7,1%** |
| synth TEST-seed 777 câu tự sinh từ DB | 92,8% | - | - | - |

Số chính thức để nói với người ngoài: **top-1 ~73%, đúng hành vi ~83%, bịa số ~7% trên câu viết kiểu người dân, chưa từng thấy**. Các số DEV/HOLDOUT cũ chỉ để theo dõi hồi quy.

Độ trễ (GTX 1660 Super 6 GB, qwen3:4b 100% GPU): luật p50 ~20 ms, p95 ~50 ms. Bật bước sinh chữ LLM: p95 ~5,0 s (đúng bằng timeout 5 s, nghĩa là một phần các lần gọi LLM chạm timeout rồi quay về bản bằng code); trong cổng tổng p95 <= 8 s. Điểm của bộ chấm không đổi khi bật/tắt LLM.

## Giới hạn đã biết (đừng hứa hơn)
- Tổng quát hoá thật chỉ ~73% top-1. Khoảng cách với DEV (90%) cho thấy tune quá khớp bộ test.
- Hỏi lại khi mơ hồ yếu: HOLDOUT-3 chỉ đúng 2/8 câu clarify.
- "Cái thứ n" (chọn theo thứ tự) còn yếu trên bộ mù: top-1 40% (HOLDOUT-3), 50% (HOLDOUT-2).
- Câu không có trong kho / chủ đề gần kho: HOLDOUT-3 đúng hành vi 2/4 câu hallucination.
- Bước sinh chữ LLM chưa chứng minh được giá trị: bộ chấm không phân biệt bật/tắt; qwen3:4b hay timeout 5 s. Verifier chỉ kiểm số, tên văn bản, "miễn phí", không kiểm nghĩa (một ý đúng số nhưng đảo nghĩa vẫn có thể lọt).
- Lỗi chéo đã biết: chữ "cuối"/"cưới" (sau bỏ dấu) bị hiểu là chủ đề kết hôn; tên thủ tục có chữ "không phải" bị nhận là phủ định; `context_memory-11` hỏi lại thay vì trả lời; vài câu `context_memory` DEV cũ (-02, -12, -15) còn sai.
- Bảng sự kiện đời sống (`_EVENTS`) chỉ 5 sự kiện viết tay.
- Phí dùng được chỉ 467/1.350 thủ tục (35%): phần còn lại trả lời "cổng không công bố".
- Đáp án mong đợi nhóm clarify/chitchat/multi-intent và HOLDOUT-3 là giả định của người soạn (xem `eval/EXPECTATIONS_REVIEW.md`, `eval/H3_ASSUMPTIONS.md`); người dùng đã duyệt nhóm đầu.
- Chưa có câu hỏi thật từ log người dân; tất cả bộ test do agent/Claude soạn.
- `server/smoke_test.py` hỏng (assert từ bản stub), chưa sửa.
- `requirements.txt` đã ghim bản; chưa thử cài trên venv sạch.
- Các nút UI mới (reset chủ đề) chưa bấm thử trên trình duyệt.

## Việc nên làm tiếp
1. Lấy 20–30 câu từ log/người dùng thật làm bộ kiểm cuối.
2. Sửa nhóm lỗi hỏi lại, thứ tự, "không có trong kho", rồi nhờ bộ mù mới (HOLDOUT-4) kiểm.
3. Đo giá trị bước sinh chữ bằng bộ chấm riêng (người chấm hoặc luật theo `condition_index`), nếu không có lợi thì tắt hẳn.
4. Dựng bảng sự kiện đời sống từ `condition_index`.

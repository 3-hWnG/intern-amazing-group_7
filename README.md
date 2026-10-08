# System 3 — Trợ lý thủ tục hành chính cấp xã/phường (trạng thái sau Phase 23–26, 2026-10-07)

Project RIÊNG, dùng lại dữ liệu của repo V10.6 (snapshot trong `data/snapshot`, 1.350 thủ tục). Không import Backend/Frontend của V10.6.
Tài liệu: [docs/SETUP.md](docs/SETUP.md) (cài đặt) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (kiến trúc, bảng timeout) · [docs/EVAL.md](docs/EVAL.md) (cách đo, quy tắc bộ mù) · [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) (cổng hồi quy) · [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) (lỗi đã biết, ai quyết) · [docs/FINAL_PRODUCT_CHECKLIST.md](docs/FINAL_PRODUCT_CHECKLIST.md) (đừng quên cho bản cuối: dev/người dùng, che PII, quyền hộp thoại, công tắc AI) · [docs/BAO_CAO_DOT4.md](docs/BAO_CAO_DOT4.md) (báo cáo ngắn đợt 4) · kế hoạch: [PLAN_SYSTEM3](docs/PLAN_SYSTEM3.md), [DOT3](docs/PLAN_SYSTEM3_DOT3.md), [DOT4](docs/PLAN_SYSTEM3_DOT4.md), [DOT5](docs/PLAN_SYSTEM3_DOT5.md).
Chạy: `python run_server.py` ở thư mục gốc (cổng 8300). Không cần `PYTHONPATH`, thư mục gốc tên gì cũng được. Bước sinh chữ bật mặc định và cần Ollama + `qwen3:4b`; không có Ollama thì lượt đó rơi về câu trả lời bằng code, hoặc đặt `S3_USE_LLM=0` để tắt hẳn. Mọi thứ hiện giờ là **chế độ nhà phát triển**, chưa an toàn cho người dùng thường: xem [docs/FINAL_PRODUCT_CHECKLIST.md](docs/FINAL_PRODUCT_CHECKLIST.md).
Kiểm tài liệu so với số đo thật: `python eval/check_docs.py` (phải sạch).
Dựng lại từ Git (Phase 28): `python run_server.py eval/run_all.py` (thêm `--quick` để bỏ phần chậm) dựng DB, dựng DB V10.6 từ mã vendor `eval/vendor_v106/`, chạy mọi gate không GPU và in bảng số kèm ngưỡng; xem [eval/REPRODUCE.md](eval/REPRODUCE.md). Không cần `repo/` cạnh `system3`.

## System 4 (Friendly mode, song song trên cùng web) — nhánh `System_3&4`
`Launch web.bat` giờ bật thêm **đăng nhập/đăng ký** và công tắc **Strict | Friendly** (Strict = System 3 bên dưới, không đổi). `S4_ENABLED=0` → web System 3 như cũ.
Xem [system4/README.md](system4/README.md), nhiệm vụ [docs/SYSTEM4_NV1_NEN_TANG.md](docs/SYSTEM4_NV1_NEN_TANG.md) … NV4, deploy [docs/SYSTEM4_DEPLOY.md](docs/SYSTEM4_DEPLOY.md).

## Kiến trúc đang chạy
User → Orchestrator → **Planner (luật; Qwen3-4B hybrid là tuỳ chọn, TẮT mặc định)** → Policy/Router (luật) → Answerer (code, nguyên văn + nguồn) → [LLM chỉ sinh chữ giải thích điều kiện/so sánh, mọi ý qua verifier, lỗi/timeout 7 s thì giữ bản bằng code] → câu trả lời. Timeout cả hai bước LLM (Planner hybrid, Answer Composer) là 7 giây, cấu hình được: bảng ở [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Map với kiến trúc G7 của nhóm: cùng file. Box 1–4, 5A, 6A, 10 đã có; 3 (LLM Planner) làm hybrid nhưng không bật; 5B/6B (RAG, import) mới chỉ có thiết kế giao diện trong `knowledge/`.

| Thư mục | Nội dung |
|---|---|
| `run_server.py` | launcher: đăng ký package `system3` rồi chạy server (hoặc `-m <module>`, hoặc một script), không cần `PYTHONPATH` |
| `data/` | build DB từ snapshot, `fees_clean`, `field_chunks`, `condition_index`, `families`, `synonyms`, `team_fee_overlay` (lệ phí từ corpus nhóm, chỉ khi cổng không có), `api.py` (cửa vào duy nhất) |
| `retrieval/` | tách câu, xếp hạng IDF có dấu, cổng phạm vi, phủ định/thứ tự (`refs.py`), trạng thái hội thoại (`context.py`, bỏ nhãn lượt), tách chữ dính liền (`query.unglue`) |
| `server/planner/` | luật mặc định; `hybrid.py` = luật + Qwen3-4B nền (tuỳ chọn) |
| `server/policy/` | chống chèn lệnh, che PII (chỉ trong trace), kiểm căn cứ, phạm vi, hỏi lại khi ≥ 3 bản gần nhau |
| `server/answer/` | trả lời bằng code + nguồn; `llm_answer.py` + `verifier.py` (sinh chữ có kiểm) |
| `server/orchestrator.py`, `db/` | bộ nhớ hội thoại, reset chủ đề, trace |
| `server/user_memory.py` | Phase 26: bộ nhớ người dùng theo thiết bị (`client_id`): hồ sơ nhẹ (tỉnh, xã/phường, loại người dùng, ghi chú) + nhớ lựa chọn MCQ `subject`; API `/memory*`; Policy dùng nó để bớt hỏi lại (xem mục "Bộ nhớ người dùng") |
| `web/` | UI chat: quản lý hộp thoại (menu ⋯: ghim/bỏ ghim, xuất Markdown/JSON/PDF, đổi tên, xoá; nhấp đúp để đổi tên; "Xoá tất cả"; API `PATCH {title?, pinned?}`, `GET /conversations/{id}/export?format=md|json|pdf` (pdf = trang in, trình duyệt tự mở hộp thoại in để Lưu thành PDF), `DELETE /conversations`), nút "Tạo bảng full", chỉ báo + panel cấu hình AI (`/config`), "Bắt đầu chủ đề mới", "dạng khác", nút "Hồ sơ của bạn" (Phase 26) và gợi ý "Nhớ đối tượng ...?" sau khi bấm nút thẻ hỏi lại |
| `knowledge/` | chỉ thiết kế giao diện RAG/import (chưa build) |
| `eval/` | bộ test + bộ chấm (xem docs/EVAL.md), `perturb.py`, `check_docs.py`, `run_all.py` + `vendor_v106/` (dựng lại từ Git, Phase 28) và các báo cáo `P18_REPORT.md`, `P19_REPORT.md`, `P20_REPORT.md`, `P23_REPORT.md`, `P24_REPORT.md`, `P26_REPORT.md` |

## Số đo (chế độ luật, `S3_USE_LLM=0`)
**Số để nói với người ngoài là các bộ MÙ** (câu viết kiểu người dân, hệ thống chưa từng được tune trên chúng):

| Bộ mù | top-1 | đúng hành vi | hỏi lại đúng |
|---|---|---|---|
| **HOLDOUT-4** (90 mục / 106 lượt, số chính thức) | **78%** (60/77) | **84%** (89/106) | 8/16 |
| pseudo_real 2 (30 mục / 34 lượt) | 68% (19/28) | 68% (23/34) | 0/3 |
| HOLDOUT-3 (88 câu; chạy trước Phase 23, chưa chạy lại) | 75% (50/67) | 86% | - |
| pseudo_real 1 (30 mục / 42 lượt; đã bị xem lỗi; trước Phase 23) | 57% (17/30) | 74% | 1/6 |
| Bộ team (10 câu của các team, chấm luật) | - | 8/10 PASS | - |

HOLDOUT-4 trước Phase 23 là 75% (58/77) top-1 và 82% (87/106) hành vi; sau Phase 23 là 78% và 84% (không tune trên bộ này). Bịa số trên HOLDOUT-3: 3,4% (đo trước Phase 23); chưa đo bịa số trên HOLDOUT-4/pseudo_real.
**Kết luận trung thực: chọn đúng thủ tục khi người dân gõ tự do còn quanh 78% top-1; hỏi lại khi mơ hồ chỉ đúng một nửa (8/16, 0/3).** Mục tiêu đặt ra cho đợt 4 (top-1 ≥ 80%, hành vi ≥ 88%) **chưa đạt**; nghiệm thu đợt 5 (Phase 29) sẽ đo bằng bộ mù mới.
Bộ team 8/10: TC03 là **đáp án nhóm cần sửa** (đáp án đòi "7 ngày" khi câu chỉ hỏi giấy tờ), TC06 còn mở (điều kiện "nơi tổ chức tang lễ"); quyết định và người chịu trách nhiệm ở [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).

Số trên bộ đã tune (chỉ để theo dõi hồi quy, không dùng để khoe):
| | kết quả |
|---|---|
| DEV gộp 523 ca: top-1 / hành vi / bịa số | 98,0% / 98,1% / 0,2% |
| DEV cũ 209 (cổng hồi quy): top-1 / hành vi / bịa số | 97,0% / 98,1% / 0,0% |
| ngoài phạm vi (DEV) | 30/30 |
| ctx (hội thoại) top-1 lượt cuối | 89/91; ctx-p23: 26/26 |
| synth (câu tự sinh từ DB) TRAIN / TEST | 96,3% / 96,4% |
| synth `glued` (chữ dính liền, Phase 23b) TRAIN / TEST | 97,6% / 96,1% (cùng câu có dấu cách: 98,4% / 97,2%) |
| `eval/perturb.py` (nhiễu không đổi nghĩa trên ca đã đúng của DEV + ctx) | 99,53% bất biến (7.063/7.096; nhãn lượt/đánh số/ngoặc/emoji/hoa 100%, dính chữ 97,0%, bỏ dấu 97,9%) |
| Baseline V10.6 (185 câu cũ, lúc đầu) | top-1 11%, hành vi 32% (chạy lại từ mã vendor Phase 28: 10,7% / 31,4%, `eval/P28_REPORT.md`) |

### Concise = trả lời đúng ý hỏi (`eval/run_concise.py`)
Định nghĩa của nhóm: hỏi giá thì chỉ báo giá. Chấm bằng luật:
| | gốc (đầu đợt 4) | hiện tại |
|---|---|---|
| DEV focus (không dư mục, không thiếu mục) | 70% | 99% (348/352), gồm các ca p16–p23 |
| HOLDOUT cũ focus | 59% | 96% (47/49) |
| task thừa (kéo thêm thủ tục không hỏi) | 11/230 | 0/449 (DEV), 0/54 (HOLDOUT cũ) |
| bộ team: PASS (chấm luật) | 3/10 | 8/10 |
Lưu ý: số focus 99% nằm trên DEV đã tune (gồm ca agent tự soạn); trên câu thật còn lỗi: bộ team còn 2 câu FAIL (TC03 do đáp án nhóm cần sửa, TC06 do điều kiện tang lễ; TC02 đã pass nhờ corpus nhóm ở Phase 23d).

### LLM
- **Planner hybrid (Qwen3-4B): không có lợi, tắt mặc định.** Đo công bằng ở Phase 19 (trước Phase 23; timeout 7 s, 0% timeout): không có lần sửa nào làm đúng hơn đáp án; confidence tự báo 0,99 cho 65% câu kể cả khi sai. Trên bộ mù HOLDOUT-4 hybrid kém luật 2 câu (56/77 vs 58/77 lúc đó), team 5/10 vs 7/10. Chi tiết: `eval/P19_REPORT.md`.
- **Bước sinh chữ (Answer Composer): bật mặc định (quyết định của nhóm, 2026-10-07), giữ công tắc; đã đo ở Phase 27.** Bộ chấm riêng `eval/score_composer.py` (63 ca có bước LLM: 50 từ DEV/ctx, 13 tự soạn dễ hơn câu thật), chấm bằng luật: bật không làm tụt chỉ số hồi quy nào (DEV cũ, ctx, DEV focus, cases_p26, test server: giống hệt chế độ tắt); **đạt cả 5 tiêu chí luật 94% (59/63) so với 71% (45/63) bản code**, phần hơn gần như chỉ ở độ ngắn gọn (tiêu chí e); đủ ý, đúng số, không đảo nghĩa, không bịa cơ quan/văn bản: bằng bản code (verifier giữ 100% số đúng). Timeout 7 s: 0/64 lượt gọi chạm timeout (trước khi rút gọn prompt: 3–8/64 tuỳ lúc GPU bận); qua `/chat` p50 1,9 s, p95 3,4 s, max 5,0 s. **Giá trị thật cho người dùng chưa kết luận được bằng luật**: chỉ ~9% câu DEV kích hoạt bước này, ~60% trong số đó kích hoạt vì điều kiện Planner tự gán chứ người dùng không nêu, và so sánh của LLM chủ yếu liệt kê dữ kiện từng thủ tục. Mẫu 20 ca chờ người chấm: `eval/results/composer_sample20.md`. Chi tiết: `eval/P27_REPORT.md`.
### Bộ nhớ người dùng (Phase 26)
Tuỳ chọn, theo thiết bị (UUID ở `localStorage`, header `X-Client-Id`), **chưa có tài khoản** (thẻ `FINAL-PRODUCT: [MEM]`). Người dùng điền tỉnh, xã/phường, loại người dùng (người dân / hộ kinh doanh–doanh nghiệp / khác), ghi chú, hoặc bấm "Nhớ đối tượng ...?" sau khi chọn một nút của thẻ hỏi lại; xem, quên từng mục, "Quên tất cả" trong "Hồ sơ của bạn". Hồ sơ chỉ **ưu tiên**: khi Policy sắp hỏi lại giữa >= 3 thủ tục gần nhau, nó lọc ứng viên theo đối tượng thực hiện đã nhớ (đúng 1 hợp -> không hỏi lại, nói rõ "Theo hồ sơ của bạn ... mình chọn «...»"; nhiều hợp -> thẻ chỉ còn các ứng viên hợp), và ưu tiên biến thể hợp đối tượng khi chọn bản mặc định của nhóm. Không hồ sơ thì hành vi y hệt cũ; câu nêu rõ tên một thủ tục thì hồ sơ không can thiệp. Chi tiết: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), số đo: [eval/P26_REPORT.md](eval/P26_REPORT.md).

- Độ trễ (GTX 1660 Super 6 GB, đo ở đợt 4): luật p50 ~20 ms, p95 ~80 ms; bật sinh chữ p95 ~5 s (khi timeout còn 5 s). Đo lại ở Phase 27 (GTX 1660 Super, GPU dùng chung với ứng dụng khác, timeout 7 s, prompt đã rút gọn): lượt có bước LLM p50 ~1,9 s, p95 ~3,4 s, max ~5 s (một lần đo khác lúc GPU bận: p95 4,8 s, max 7,4 s); mọi lượt DEV (đa số không gọi LLM) p95 ~1,8 s.

## Giới hạn đã biết (đừng hứa hơn)
- Chọn thủ tục tổng quát hoá ~78% top-1 trên câu mù; DEV 98% là tune quá khớp.
- **Hỏi lại khi mơ hồ yếu** (8/16, 0/3 trên hai bộ mù mới); câu mơ hồ kiểu đời sống ("làm giấy tờ cho con") vẫn bị xin lỗi thay vì hỏi lại.
- Top-3 trên HOLDOUT-3 giảm sau đợt 4 (82% → 78%) dù top-1 tăng: danh sách ứng viên ngắn hơn (chưa đo lại sau Phase 23).
- Lời kể chứa tên thủ tục có thể chọn nhầm bản anh em (cùng họ, khác loại).
- "Ở đâu" chung chung trả **cơ quan giải quyết** khi cổng không ghi địa điểm (bộ test cũ không thống nhất giữa `address` và `agency`).
- Khớp hoàn cảnh với `condition_index` là khớp chữ + bảng 11 sự kiện đời sống viết tay; kết hôn/khai sinh chỉ có dòng "đối tượng" nên trả "cổng không công bố riêng".
- Lệ phí dùng được: 467/1.350 thủ tục từ cổng, cộng 15 thủ tục bù từ corpus của nhóm (`team_fee_overlay`, chỉ khi cổng không có, ghi rõ nguồn) = 482/1.350 (35,7%); phần còn lại trả "cổng không công bố", không suy ra miễn phí.
- Verifier của bước sinh chữ chỉ kiểm số, tên văn bản, "miễn phí", không kiểm nghĩa.
- Bảng sự kiện đời sống (`_EVENTS`) chỉ 11 sự kiện viết tay.
- Planner luật không sinh `context_facts`: `session_facts` luôn rỗng ở cấu hình mặc định. Phase 26 **không** sửa chuyện này (hồ sơ đi thẳng vào Policy, không qua Planner).
- **Bộ nhớ người dùng giúp ít**: câu mơ hồ **theo đối tượng** hiếm trong dữ liệu thật (đa số thủ tục khai "Công dân Việt Nam"; khác biệt đối tượng chủ yếu ở đất đai, xây dựng, bảo hiểm, thủ tục theo tỉnh). Trên 2.023 câu dựng từ tên 1.313 thủ tục cấp xã (103 câu bị hỏi lại): hồ sơ "doanh nghiệp" bỏ hỏi 10/103 và thu hẹp thẻ 15/103, "người dân" bỏ 1 và thu hẹp 23, "tổ chức" bỏ 0 và thu hẹp 27. Bộ 92 ca tự soạn (`eval/run_p26.py`) bỏ hỏi 10/28 ca mơ hồ-theo-đối-tượng; **đáp án nhóm đó lấy theo quy tắc đối tượng của dữ liệu, không phải ý định thật của người hỏi**. Rủi ro đã biết: dữ liệu `procedure_subjects` có chỗ chưa khớp tên thủ tục (vd thủ tục đăng ký đất đai lần đầu cho hộ gia đình chỉ khai doanh nghiệp/Việt kiều), nên thu hẹp thẻ theo người dân có thể ẩn đúng thủ tục người dùng cần (người dùng vẫn gõ tên được).
- Tỉnh/xã trong hồ sơ chỉ hiển thị: dữ liệu chỉ cấp xã và không chia theo tỉnh; danh sách tỉnh là 63 đơn vị trước sáp nhập 07/2025 (mục 6 checklist).
- Còn sai 2/91 ca ctx và vài ca DEV, chưa có nguyên nhân chung (xem `eval/P23_REPORT.md`).
- **Phase 23 (nhãn lượt, chữ dính, điều kiện)**: đã sửa ba họ lỗi blackbox (xem `eval/P23_REPORT.md`): nhãn lượt/đánh số/lời đệm đầu-cuối câu bị cắt ở `retrieval/context.strip_labels` (cả lịch sử), chữ lạ không còn đổi `follow_up` thành `independent`, chữ dính liền được tách bằng từ vựng kho (`retrieval/query.unglue`), câu "nếu X thì cần làm gì" là MỘT task (components + điều kiện), mảnh chỉ mượn chữ chung không thành task. Còn lại: dính chữ rất ngắn (4-5 ký tự không cặp trong tên: "tờgì" bị đọc là "tôi"), dính chữ nhập nhằng giữa hai thủ tục anh em, câu không dấu nhập nhằng với chữ có dấu khác ("sổ đỏ"/"so do"), dấu phẩy chen giữa một tên thủ tục vẫn tách ý.
- Bảng full hiện theo từng biến thể, chưa gộp họ; công tắc AI là trạng thái tiến trình (nhiều worker sẽ không đồng bộ); tải lại trang thì nút cũ không còn bị làm mờ.
- **Chưa an toàn cho người dùng thường (mọi thứ là developer mode):** `plan`/`trace`/`/config` chưa chặn theo dev, CCCD/SĐT chưa che trong `messages`, phiên ẩn danh, "Xóa tất cả" xóa của mọi người. Đã ghi và gắn thẻ `FINAL-PRODUCT:` trong code, xem [docs/FINAL_PRODUCT_CHECKLIST.md](docs/FINAL_PRODUCT_CHECKLIST.md); chưa build.
- Không có RAG hay import tài liệu (Box 5B/6B).
- **Tất cả bộ test do agent/Claude soạn; chưa có câu hỏi thật từ log người dân.** Đáp án giả định ghi trong `eval/*ASSUMPTIONS.md`.
- `requirements.txt` ghim đúng các bản đang cài trên máy dev này (Python 3.12.2, `pip freeze` khớp); bạn báo đã cài sạch từ file này trên máy bạn (Python 3.12.8), tôi chưa tự kiểm lại trên venv sạch.
- Quy tắc nghiệm thu: không tune trên HOLDOUT-3/4 (xem docs/EVAL.md). Trước khi tune tiếp phải soạn bộ mù mới.
- Các lỗi đã biết trên bộ test của nhóm và người quyết: [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).

## Việc nên làm tiếp
1. **Câu hỏi thật** (20–30 câu từ log/người dân) làm bộ kiểm cuối; đây là cách duy nhất biết số đo ngoài đời.
2. Sửa nhóm lỗi **hỏi lại khi mơ hồ** và chọn nhầm anh em/chọn thứ tự; sau đó soạn HOLDOUT-5 để kiểm (Phase 29).
3. Bước sinh chữ: bật mặc định (nhóm quyết), bộ chấm luật đã có (Phase 27); còn thiếu người chấm 20 ca (`eval/results/composer_sample20.md`) để biết có lợi thật không, và câu hỏi thật để biết tỉ lệ kích hoạt ngoài đời.
4. Nếu nhóm vẫn muốn LLM Planner: cần model lớn hơn hoặc hiệu chỉnh confidence (cơ chế hợp nhất, trace, công tắc đã có sẵn).
5. RAG/import (Box 5B/6B) theo thiết kế trong `knowledge/README.md`.
6. Trước bản cuối: làm hết [docs/FINAL_PRODUCT_CHECKLIST.md](docs/FINAL_PRODUCT_CHECKLIST.md).

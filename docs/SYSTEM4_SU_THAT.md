# System 4 — Sự thật khi tài liệu mâu thuẫn (cho LLM / người mới, cập nhật 2026-10-08)

**Đọc file này TRƯỚC các tài liệu khác.** Tài liệu NV1–NV5 và `SYSTEM4_HANDOFF.md` ghi theo thời gian: kế hoạch được viết trước, thực tế đo sau,
nên nhiều chỗ cũ không còn đúng. Khi tài liệu và code khác nhau, **code là sự thật**. Mỗi dòng dưới đây đã kiểm trực tiếp trong code
(commit `0d5fa7d` trên nhánh `System_4`). Không sửa lời người dùng ghi nguyên văn trong các tài liệu (Phần A) — chỉ đọc theo bảng này.

## 1. Model và chế độ
| Tài liệu nói | Sự thật | Kiểm ở đâu |
|---|---|---|
| `system4/README.md` "Lưu ý": `qwen3:4b` (bản luôn suy nghĩ) là model duy nhất; chế độ Nhanh ép JSON để model khỏi suy nghĩ | Trả lời nhanh (Friendly + Chuyên gia), bộ nhớ, tóm tắt dùng **`qwen3:4b-instruct-2507-q4_K_M`**, temperature **0,2** (bản không suy nghĩ). Chỉ **"Suy nghĩ kỹ"** dùng `qwen3:4b` (`THINK_MODEL`). Vẫn dùng khuôn JSON, nhưng để lấy các trường (kế hoạch, hỏi lại, nguồn), không còn để tắt suy nghĩ | `system4/server/config.py` khối MẶC ĐỊNH; `llm.py` (`think_model()`) |
| `SYSTEM4_HANDOFF.md` §0: "Suy nghĩ kỹ + Strict vẫn `qwen3:4b`" | **Strict (System 3) dùng Instruct** khi chạy bằng `Launch web.bat` (đặt `LLM_MODEL`). Chạy `server/main.py` trực tiếp mà không đặt `LLM_MODEL` → Strict quay về `qwen3:4b` (mặc định của `server/config.py`, code System 3 không đổi) | `Launch web.bat` dòng 18; `server/config.py` dòng 45 |
| `Set up first time.bat` đặt `LLM_MODEL=qwen3:4b` (bước 4) nhưng `Launch web.bat` đặt Instruct | Không mâu thuẫn: cài đặt tải **cả hai** — `qwen3:4b` cho "Suy nghĩ kỹ" (bước 4), Instruct cho Friendly + Strict (bước 6) | hai tệp `.bat` |
| Code / ⚙: chế độ Nhanh "~1-3 giây" (`chat.py` đầu tệp, `llm.py stream_json`, ⚙ `DEFAULT_ANSWER_MODE`) | Bài thi cuối (trung vị): chat thường 1,4 s, câu chào 1,3 s, câu có dữ liệu **3,6 s**, câu đếm / liệt kê cả bảng 4,9 s; p90 mọi câu 4,9 s | NV5 phần D5 |
| Ghi chú trong `persona.py` (`FAST_SCHEMA`): "plan đứng trước để model định hướng" | Ollama 0.40 **không giữ thứ tự trường** JSON; bản Instruct hay viết `answer` trước. Chỉ khi bật `JSON_PLAN_FIRST` (mặc định bật) — tên trường `a_plan`, `b_small_talk`, `c_answer`, `d_ask_back`, `e_choices`, `f_sources` — kế hoạch mới thật sự viết trước (44/45 câu) | `persona.py` (`KEY_PREFIX`, `key()`, `plain_keys()`) |

## 2. Tốc độ — điều kế hoạch đoán sai
| Kế hoạch / ước tính | Đo thực tế |
|---|---|
| "Phần lớn thời gian là AI **đọc** lời dặn dài" (NV5 phần B, câu trả lời đầu phiên) | Sai. Khi model đã nạp, đọc chỉ 0,03–0,7 s; **viết** chiếm phần lớn (~55 token/s); tìm ~0,3–0,45 s. Các câu 7–12 s trước NV5 chủ yếu do **nạp lại model** (NV5 D2) |
| S1 "sắp lời dặn để dùng lại" tiết kiệm 1–3 s | Gần như 0 (vẫn bật vì không hại). Phần có ích là `KEEP_MODELS_LOADED` và dùng chung một model cho Strict + Friendly |
| S2 / S4 (ít tin cũ, đoạn ngắn, reranker 8 ứng viên) sẽ được đo | **Không làm**: lợi tối đa ~0,1 s, không đáng rủi ro độ chính xác (NV5 D2) |
| NV5 D1–C1: Instruct "chữ đầu 1,0 s" | Lúc đó kế hoạch bị viết SAU câu trả lời (chưa phát hiện) nên con số không tính chi phí lập kế hoạch. Có kế hoạch trước thật: chữ đầu ~1,25 s (dev) / 1,6 s (bài thi) |
| NV5 D2: chọn JSON thay vì dạng chữ (`FAST_FORMAT=text`) vì dạng chữ chậm chữ đầu 0,7 s | So sánh không công bằng (JSON lúc đó không lập kế hoạch trước, dạng chữ thì có). Dạng chữ **chưa được đo lại** so với JSON + `JSON_PLAN_FIRST`. Mặc định vẫn `json` |
| NV5 D2 + D9: "giảm ngữ cảnh Friendly (8192 → nhỏ hơn) vì giờ khác model với System 3" | Không còn đúng từ khi Strict cũng dùng Instruct: ngữ cảnh khác nhau → Ollama nạp lại model mỗi lần chuyển chế độ. Muốn giảm thì phải giảm **cả** `FRIENDLY_NUM_CTX` (⚙) **và** `LLM_NUM_CTX` (System 3) cùng lúc |
| Strict với Instruct chậm hơn (p90 3,8 s, NV5 D6 lần 1) | Nhiễu: lần 2 p90 2,2 s (qwen3:4b 2,4 s); độ chính xác y hệt |

## 3. Độ chính xác — điều kế hoạch đoán sai
| Kế hoạch | Thực tế |
|---|---|
| Bộ kiểm chi tiết bịa (`GROUNDING_CHECK`) sẽ chặn số điện thoại / địa chỉ Team 7 bịa | Chỗ bịa thông tin Team 7 được chặn bởi lời dặn **`STRICT_BUSINESS_FACTS`** (chỉ áp dụng khi KHÔNG bật dữ liệu). Bộ kiểm ban đầu chủ yếu báo nhầm; sau khi sửa còn ~0–3 lần viết lại / 45 câu, có bắt được lỗi thật ("17 giờ 30" → "1:30 chiều", giá vàng bịa). Ở chat thường nó chỉ kiểm số điện thoại, email, web có tên doanh nghiệp — không bắt được tiểu sử / kiến thức bịa |
| NV5 D3 các dòng "C2…" và kết quả `qwen3_*.json` là cấu hình Instruct | Chạy nhầm **`qwen3:4b`, 0,6** (lỗi đặt tên trong bộ đo, đã sửa: `bench.py` dừng nếu tên cấu hình lạ). Kết quả Instruct thật ở D4, D5 |
| NV5 phần C bước 2: danh sách công tắc; "bộ đọc tệp v3" | Thêm sau khi đo: `SEARCH_FOLLOWUP`, `RERANK_RESCUE`, `STRICT_BUSINESS_FACTS`, `JSON_PLAN_FIRST`. Bộ đọc hiện là **`READER_VERSION = 4`** (dòng đầu bản ghi bảng có tên cột, vd. "Hạng thành viên: Vàng") |
| NV5 phần B: "mặc định = như trước NV5" | Đã đổi sau khi đo: mặc định = cấu hình thắng (NV5 D7). Riêng `FAST_FORMAT = json`, `PLAN_MAX_CHARS = 300` giữ nguyên |
| NV5 D5: "Bé Bảo sinh ngày nào?" 0/3 | Lỗi code đã sửa SAU bài thi (từ "bao" của "bao nhiêu"); số 0/3 là trước khi sửa, chưa chạy lại bài thi |

## 4. Tài liệu cũ đã bị NV5 vượt qua
| Tài liệu | Ghi "chưa làm" / "hướng sửa sau này" | Hiện trạng |
|---|---|---|
| NV2 phần E | "Chưa có bài đo bịa có hệ thống"; so `qwen3.5:4b` | Có bộ đo `system4/eval/bench.py` (nhóm `halluc`). Đã chọn Instruct (người dùng chọn); **`qwen3.5:4b` chưa bao giờ được tải hay đo** |
| NV3 phần D1 (đếm / tổng cả bảng) | Hướng sửa: "công cụ bảng" | Đã có: `tabletool.py`, công tắc `TABLE_TOOL` (bật) |
| NV3 phần D2 (trùng tên) | Hướng sửa: buộc hỏi lại kèm nút họ tên | Đã có: `ambig.py`, `AMBIGUITY_CHECK` (bật), trả lời bằng code không gọi AI |
| NV3 phần D3 (bảng cấu trúc lạ) | Tiêu đề hai tầng, bảng ngang, nhiều bảng một trang, chọn dòng tiêu đề: chưa có | Đã có trong `ingest.py` (v4) + ô "Dòng tiêu đề cột" trong "Cách đọc" (`POST /s4/datasets/{id}/header`). Ô gộp dọc trong phần DỮ LIỆU (một ô phủ nhiều dòng) vẫn chưa xử lý |
| NV3 phần D4 (ngưỡng reranker cố định) | | Một phần: `RERANK_RESCUE` giữ bản ghi đứng đầu cả hai cách tìm |
| NV2 / handoff: câu chào khi bật dữ liệu bị trả lời "không có trong dữ liệu" | | Đã sửa: `GREETING_MODE = code_first` (`greet.py`) |
| `SYSTEM4_HANDOFF.md` §1, §3 (trạng thái 2026-10-07, 4 ưu tiên) | | Lịch sử. Cả 4 ưu tiên đã làm trong NV5; việc còn lại ở NV5 D9 |

## 5. Git, test, dữ liệu
| Tài liệu nói | Sự thật |
|---|---|
| Handoff §1: nhánh `System_3&4`, "10 commit chỉ ở máy" | Nhánh làm việc là **`System_4`**, đã đẩy GitHub tới `0d5fa7d` (commit sau đó, nếu có, xem `git log origin/System_4..System_4`). `origin/System_3&4` cũ, thiếu toàn bộ NV5 và các commit trước đó |
| Handoff §0: "commit NV5 chỉ ở máy cho tới khi người dùng bảo đẩy" | Người dùng đã bảo đẩy (2026-10-08) — đã đẩy |
| Handoff §5: test `test_nv1` … `test_nv4` | Còn `test_nv5.py`. `test_nv1`–`test_nv3` gọi `nv5_off.apply()` để TẮT tính năng NV5 (chúng kiểm hành vi gốc); `test_nv5` kiểm từng tính năng và cả bộ mặc định mới |
| Handoff §5: đo trên model thật bằng `nv2_behavior.py`, `nv3_specialist.py` | Bộ đo chính giờ là `system4/eval/bench.py` (gồm cả 22 tình huống của `nv2_behavior.py`). Kết quả thô ở `system4/eval/results/bench/` **không đưa lên git** — số liệu chỉ nằm trong NV5 phần D |
| Danh sách lớp trong bộ đo | Là bản **giả** `system4/eval/data/ds_lop_gia.xlsx` (`fake_class.py`). Tệp thật `DS LỚP 1.5.xlsx` (tên trẻ em thật) chỉ ở `system4/runtime/` — không đưa lên GitHub (repo công khai) |
| Cài đặt: "mặc định trong config.py" | Đúng, nhưng `system4/runtime/settings.json` (nút "Lưu" trong ⚙) **ghi đè** mặc định. Máy này hiện không có ghi đè; máy khác có thể có |

## 6. Còn mở (chưa ai làm)
Xem NV5 phần D9: ngữ cảnh model nhỏ hơn cho card 6 GB (phải đổi cả System 3), kiến thức chung sai của model 4B (Úc → "Sydney", "nước rộng nhất → Việt Nam", tiểu sử người bịa), câu trả lời thủ tục dài (5–6 s), câu "Team 7 là ai?" lúc không xưng "chúng tôi/mình" (21/22).

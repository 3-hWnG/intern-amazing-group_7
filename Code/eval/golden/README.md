# eval/golden/ — Bộ evaluation đa domain + RAGAS

Thư mục này bổ sung cho `eval/` sẵn có. Tài liệu giải thích đầy đủ (4 tầng tiêu chí,
map 33 bài báo, cách đọc số): **`05_methodology/bo_evaluation_hoan_thien_v2.md`**.

## File
| File | Việc |
|---|---|
| `build_golden_multidomain.py` | Dựng golden set từ CSDL thật theo ma trận domain × 10 archetype. Mọi đáp án trích từ DB + assert. |
| `ragas_runner.py` | Gom 4 cột (question/answer/contexts/ground_truth) từ output hệ thống rồi chấm RAGAS; kèm kiểm bịa-số bằng luật. |
| `cases_golden_dev.jsonl` | (sinh ra) bộ DEV để tune — 883 dòng (853 ca `behavior=answer`). |
| `cases_golden_holdout.jsonl` | (sinh ra) bộ mù — **không đọc lỗi từng câu để sửa code** — 278 dòng (266 ca `behavior=answer`). |
| `ragas_dataset_dev.json` / `ragas_dataset_holdout.json` | (sinh ra 2026-10-13) 4 cột RAGAS đã gom thật từ hệ thống, xem PHẦN "Kết quả đã chạy" dưới. |
| `../run_pseudo_rank.py` | (mới, 2026-10-13) MRR/nDCG@5 trên bộ mù `cases_h4/5/6.json` (ngoài top1/top3 của `run_pseudo.py`). |

## Quy trình
```bash
# 1) dựng golden set (chạy ở thư mục này, cây dự án phải có data/snapshot/procedures.jsonl)
python build_golden_multidomain.py --per-domain 6 --seed 7

# 2) RÀ TAY: mở file, sửa các ca needs_human_review (nhất là archetype 1 khẩu ngữ, 9 bẫy, 10 injection)

# 3) gom dataset RAGAS từ hệ thống (cần answer_adapter chạy được; chạy qua run_server.py, không chạy script trực tiếp)
#    LƯU Ý nếu máy ở ổ mạng/mount: sqlite "disk I/O error" -> trỏ S3_DB/S3_DATA_DB ra 1 bản DB cục bộ trước (xem README chính eval/safety/README.md phần tương tự)
S3_DB=<db cục bộ> S3_DATA_DB=<db cục bộ> S3_USE_LLM=0 python ../../run_server.py ragas_runner.py --golden cases_golden_dev.jsonl --build ragas_dataset_dev.json

# 4) chấm RAGAS (cần: pip install ragas datasets langchain-community + Ollama qwen2.5 + bge-m3 chạy local)
python ragas_runner.py --score ragas_dataset_dev.json

# 5) MRR/nDCG trên bộ mù (vd HOLDOUT "h4")
S3_DB=<db cục bộ> S3_DATA_DB=<db cục bộ> S3_USE_LLM=0 python ../../run_server.py ../run_pseudo_rank.py cases_h4.json h4
```

## 3 điều phải nhớ
1. **Câu template dễ hơn câu dân thật** → dùng để tune + kiểm phủ; số KHOE vẫn là bộ mù người soạn + log thật (việc #1 cần làm).
2. **RAGAS = LLM chấm → không thay kiểm số cứng.** Bịa số tiền vẫn kiểm bằng luật (`forbidden_facts` + `verifier.py`). Báo cả hai.
3. **Giám khảo RAGAS chạy local** (Ollama) để không gửi dữ liệu dân ra ngoài (Paper 05). Báo rõ dùng model giám khảo nào + đối chiếu người trên ~30 ca (Paper 10).

## Kết quả đã chạy (2026-10-13)

### A — MRR/nDCG trên HOLDOUT-4 chính thức (`cases_h4.json`, 90 ca / 106 lượt — bộ mù, chạy 1 lần)
Dùng `eval/run_pseudo_rank.py` (mới) — tái dùng `rank_metrics.py` đã validate, KHÔNG viết scorer mới.

| Chỉ số | Số đo | Ngưỡng | Đạt? |
|---|---|---|---|
| Behavioral Accuracy | 89/106 (84,0%) | ≥ 88% | ❌ chưa đạt |
| Top-1 (trên 77 lượt `answer`) | 60/77 (77,9%) | ≥ 80% | ❌ chưa đạt (sát ngưỡng) |
| Top-3 | 64/77 (83,1%) | ≥ 90% | ❌ chưa đạt |
| **MRR** | **0,810** | ≥ 0,85 | ❌ chưa đạt |
| **nDCG@5** | **0,785** | theo dõi | — |
| Clarify (hỏi lại đúng lúc) | 9/16 (56,2%) | — (điểm yếu) | ❌ |
| Apologize (từ chối đúng) | 13/13 (100%) | — | ✅ |

Nhóm lỗi chung (top1 sai, theo field liên quan — KHÔNG in câu/đáp án cụ thể, đúng kỷ luật bộ mù):
`documents` 8 ca, `conditions` 7 ca, `place` 3 ca, `fee` 1 ca, `legal_basis` 1 ca, `time` 1 ca.
File số liệu đầy đủ (kể cả từng dòng, chỉ dùng để debug, KHÔNG dùng để tune): `eval/results/rank_h4.json`.

**Đọc số này thế nào:** MRR 0,810 < Top-1 77,9% về bản chất nói cùng một câu chuyện — khi
sai #1, đáp án đúng thường **không** nằm ngay #2 (MRR thấp gần với Top-1 chứ không cao hơn
nhiều) → lỗi nhiều khả năng là **chọn nhầm hẳn** sang thủ tục khác (health: `documents`,
`conditions`) chứ không phải "đúng nhưng xếp hạng 2". nDCG@5 (0,785) thấp hơn Top-3 (83,1%)
vì nDCG phạt nặng khi đáp án đúng rơi xuống hạng 4-5 thay vì hạng 2-3 — tín hiệu để ưu tiên
sửa việc **xếp hạng trong top-3**, không chỉ việc "có nằm trong top-3 hay không".

### B — Gom dữ liệu RAGAS thật từ hệ thống (bước "build", KHÔNG cần cài `ragas`)
Chạy `ragas_runner.py --build` trên cả DEV và HOLDOUT. Phát hiện + vá **2 lỗi plumbing** trong
`ragas_runner.py` khiến bước này trước đó **luôn trả rỗng** (answer/contexts rỗng toàn bộ,
không ai biết vì script không báo lỗi cứng, chỉ in cảnh báo):
1. `call_system()` thiếu `sys.path.insert` cho `eval/` (nó ở `eval/golden/`, 1 cấp dưới `eval/
   answer_adapter.py`) → `import answer_adapter` luôn `ModuleNotFoundError`.
2. `answer_adapter.adapter()` nhận turns dạng `{"role":"user","text":...}` (không phải
   `"content"`) và trả `res["answer_text"]` + `res["tasks"][i]["candidates"]` (không phải
   `res["answer"]`/`res["trace"]["candidates"]`) — code cũ đọc sai field nên luôn rơi vào
   nhánh rỗng.

Sau vá, chạy lại:

| Bộ | n (ca `behavior=answer`) | answer không rỗng | Bịa số (luật `forbidden_facts`) |
|---|---|---|---|
| DEV (`cases_golden_dev.jsonl`) | 853 | 827/853 (97,0%) | **0/853 (0%)** |
| HOLDOUT (`cases_golden_holdout.jsonl`, bộ mù) | 266 | — | **0/266 (0%)** ✅ |

Kết quả đã lưu: `ragas_dataset_dev.json`, `ragas_dataset_holdout.json` (4 cột
question/answer/contexts/ground_truth thật, dùng được ngay cho bước `--score`).
**0% bịa số trên cả DEV và bộ mù** — số đáng khoe nhất ở bước này, đo bằng luật cứng
(độc lập hoàn toàn với RAGAS/LLM-judge, đúng tinh thần Paper 15).

### C — Bước `--score` (RAGAS thật, cần LLM giám khảo)

**2026-10-13, cập nhật:** `ragas`/`datasets`/`langchain-community`/`langchain-ollama` đã được cài
và `qwen2.5:7b` + `bge-m3` đã pull xong qua Ollama **trên máy Windows thật của dj** (làm bởi 1 agent
khác chạy trực tiếp trên máy đó). Agent kia chạy thử `--score --limit 15` và tự phát hiện ra đúng
2 lỗi mà phần dưới đây đã vá:

1. **`contexts` trước đó chỉ là bare `proc_id`** (`"1.001714"`) thay vì văn bản thật — khiến giám
   khảo LLM so câu trả lời (có chữ) với "ngữ cảnh" chỉ có mã số, chấm nhầm **mọi câu là "bịa"**
   (faithfulness tụt giả tạo xuống 0,083). **ĐÃ VÁ**: `call_system()` giờ tra `proc_id` ra 1 đoạn
   văn bản thật (tên + lệ phí + thời hạn + checklist rút gọn + cơ quan) từ `procedures.jsonl`
   (hàm `_proc_text_index()`) để làm `contexts`.
2. **Ca OOS bị lẫn vào RAGAS** — nhiều câu golden gán `expected_behavior=answer` nhưng thật ra
   thuộc domain ngoài phạm vi xã/phường (vd Hải quan), hệ thống đúng luật trả `apologize`; đưa câu
   từ chối đó vào RAGAS khiến answer_relevancy bị chấm sai thành "lạc đề". **ĐÃ VÁ**: `build()` giờ
   gọi hệ thống THẬT trước, chỉ giữ ca nào **cả golden và hệ thống đều đồng ý là `answer`**; ca lệch
   hành vi bị tách ra `*_behavior_mismatch.json` (tầng C, chấm riêng bằng Behavioral Accuracy, không
   gộp vào B1-B4). Số liệu sau vá: build lại DEV 853→**614 ca hợp lệ** (239 ca lệch hành vi: 2 vai
   trò kỳ vọng ≠ thật) và HOLDOUT 266→**189 ca hợp lệ** (77 ca lệch hành vi, phần lớn do golden gán
   nhầm domain Hải quan là "xã/phường trả lời được" — nên rà lại `build_golden_multidomain.py` phần
   lọc domain cấp xã, xem như 1 việc còn thiếu mới).

**Vì sao mình (agent chạy trong sandbox riêng) không tự chạy `--score` được:** sandbox đọc/sửa file
qua ổ mạng `D:\chatbot-thutuc-g7` nhưng **không phải** máy Windows thật của dj — không thấy Ollama
hay các package agent kia vừa cài. Dataset đã vá sẵn nằm đúng vị trí trên máy dj rồi, agent kia đã
chạy `--score --limit 20` trên dataset đã vá — kết quả bên dưới, kèm 1 lỗi đo đạc cần sửa tiếp.

### Kết quả CHÍNH THỨC, CUỐI CÙNG — `--score` TOÀN BỘ 189 ca (2026-10-13, dj tự chạy trên máy thật, 3 giờ 21 phút 24 giây, KHÔNG `--limit`)

Lần 1 (agent khác, `max_workers=16` mặc định): hầu hết job timeout, số vô nghĩa (Context Precision
"1,0000" thực ra chỉ đo được 1/20 ca). Lần 2 (`--limit 20`, đã vá RunConfig): số đáng tin nhưng chỉ
trải 7 domain hiếm/ngoài-lõi, không đại diện. **Lần 3 — lần cuối, dùng để trích vào báo cáo** — chạy
toàn bộ 189/189 ca hợp lệ, không lấy mẫu con, không `--limit`. Đã tự kiểm tra lại bằng cách đọc trực
tiếp `ragas_dataset_holdout_score.json` và đếm số giá trị non-null cho từng cột (không chỉ tin số in
ra màn hình) — khớp đúng với số script tự báo:

| Chỉ số | n đo được / 189 | Mean | Ngưỡng | Đạt? |
|---|---|---|---|---|
| Answer Relevancy | **189/189 (100%)** | **0,3687** | ≥ 0,90 | ❌ chưa đạt |
| Context Precision | **186/189 (98%)** | **0,8056** | ≥ 0,85 | ❌ chưa đạt, sát ngưỡng nhất |
| Context Recall | **178/189 (94%)** | **0,6629** | ≥ 0,85 | ❌ chưa đạt |
| Faithfulness | **162/189 (86%)** | **0,3806** | ≥ 0,95 | ❌ chưa đạt, hụt rất nhiều |

File đầy đủ: `ragas_dataset_holdout_score.json` (189 dòng). Số trải đều **68 domain khác nhau** —
không còn lệch mẫu domain-hiếm như lần đo 20 ca trước. Mẫu vài domain (faithfulness/relevancy/
context_precision): Hàng hải và đường thủy nội địa 1,000/0,403/1,000; Sát hạch, cấp giấy phép lái xe
1,000/0,799/0,000; Giáo dục trung học 0,000/0,000/0,000; Nhà ở và công sở 0,000/0,360/0,500 — biến
động rất lớn giữa các domain, không đồng đều.

**⚠️ GIỚI HẠN đã phát hiện ở đợt đo này — ĐÃ TÌM RA NGUYÊN NHÂN THẬT VÀ VÁ (xem mục D bên dưới):**
3 domain lõi mà hệ thống (System 3+4, cấp xã/phường) được thiết kế tập trung — Hộ tịch, Đăng ký
quản lý cư trú, Chứng thực — vắng mặt hoàn toàn khỏi 189 ca ở trên. Lưu ý: **nguyên nhân ban đầu ghi
ở đây ("không còn thủ tục ACTIVE") là đoán sai một phần** — đã truy tận gốc và tìm ra lý do thật ở
mục D: không phải thủ tục bị xoá/mất, mà là field `state` của chúng trong snapshot là `"UPDATED"`
chứ không phải `"ACTIVE"`, và script sinh golden set trước đó chỉ lấy `state=="ACTIVE"`. Đã vá.

Lưu ý nhỏ, không ảnh hưởng số liệu của đợt đo 189 ca: trong đó có 3 cặp `id` trùng nhau (7 dòng dư,
do 2 thủ tục khác nhau có tên bị cắt 60 ký tự đầu giống hệt nhau ở bước sinh câu hỏi tự động → câu
hỏi giống nhau → cùng hash id) — chỉ ảnh hưởng ~3,7% số dòng, không đổi kết luận.

### D — VÁ lỗ hổng domain-coverage (2026-10-13, cùng ngày, sau khi dj yêu cầu bổ sung 3 domain lõi)

**Nguyên nhân thật, đã kiểm tra tận gốc (không phải "mất thủ tục"):** snapshot
`data/snapshot/procedures.jsonl` có 2 giá trị `state`: `ACTIVE` (695 bản ghi) và `UPDATED` (655 bản
ghi) — và **toàn bộ** thủ tục domain Hộ tịch (39), Đăng ký/quản lý cư trú (13), Chứng thực (12) đang
ở `state="UPDATED"`, không phải đã mất hay bị xoá. Quan trọng hơn: **hệ thống thật đang chạy (DB mà
`answer_adapter` thực sự truy vấn) coi 2 state này NHƯ NHAU** — `data/load.py` (dòng 3-4, comment gốc:
*"Mọi bản ghi nạp vào đều status='active'"*) nạp MỌI bản ghi vào DB phục vụ với `status='active'`
bất kể field `state` gốc là gì. Nghĩa là hệ thống **đang trả lời bình thường** về Hộ tịch/Cư trú/
Chứng thực ngay lúc này — chỉ có `build_golden_multidomain.py` (dòng lọc `if d.get("state") !=
"ACTIVE": continue`) là lọc nhầm, loại các domain này khỏi golden set dù hệ thống vẫn phục vụ chúng.

**Đã vá:** đổi điều kiện lọc thành `if d.get("state") not in ("ACTIVE", "UPDATED"): continue` (comment
giải thích ngay trong code). Chạy lại `python build_golden_multidomain.py --per-domain 6 --seed 7`:

| | Trước vá | Sau vá |
|---|---|---|
| Tổng ca sinh | 1.161 | **2.168** |
| Số domain phủ | 74 | **122** |
| DEV | 853 | **1.615** |
| HOLDOUT (bộ mù) | 266 | **553** |
| Hộ tịch (holdout) | 0 | **7** |
| Đăng ký, quản lý cư trú (holdout) | 0 | **9** |
| Chứng thực (holdout) | 0 | **10** |
| Bảo trợ xã hội (holdout) | 1 | **3** |

Chạy lại bước `--build` qua hệ thống thật (rules-only, `S3_USE_LLM=0`, không cần RAGAS/Ollama):
```bash
S3_DB=... S3_DATA_DB=... S3_USE_LLM=0 python run_server.py eval/golden/ragas_runner.py \
  --golden eval/golden/cases_golden_holdout.jsonl --build eval/golden/ragas_dataset_holdout.json
```
Kết quả: HOLDOUT **394 ca hợp lệ** (lên từ 189), 108 domain, trong đó 4 domain lõi có **21 ca** (Hộ
tịch 4, Cư trú 7, Chứng thực 8, Bảo trợ xã hội 2). Bịa số vẫn **0/394 (sạch)**. DEV: **1.192 ca hợp
lệ** (lên từ 614), bịa số **1/1192** — ca này đã soi tận gốc (`GOLD-458a39a8`, domain "Quản lý xuất
nhập cảnh"): **KHÔNG phải hệ thống bịa** — thủ tục có 2 mức lệ phí hợp lệ (nộp trực tuyến 25đ theo
Thông tư 64/2025 và nộp trực tiếp 50.000đ theo Thông tư 25/2021), hệ thống trả lời đúng cả 2, nhưng
golden-set chỉ gán 1 mức là "đúng" rồi liệt mức còn lại vào `forbidden_facts` — lỗi ở khâu sinh
golden set với thủ tục nhiều mức phí, không phải lỗi hệ thống hay lỗi verifier. File cũ (189/266,
614/853) đã backup `*.bak_before_state_fix` để đối chiếu nếu cần.

**Việc còn lại để có SỐ RAGAS thật cho 4 domain lõi:** chạy `--score` (cần Ollama trên máy thật của
dj, như các lần trước) trên `ragas_dataset_holdout.json` MỚI (394 ca). Ở tốc độ đo được lần trước
(~64 giây/ca), 394 ca dự kiến mất **~7 tiếng** — dài hơn hẳn lần đo 189 ca (3h21'). Để có số nhanh
hơn mà vẫn phủ đủ cả 4 domain lõi, đã chuẩn bị sẵn
`ragas_dataset_holdout_core_focus.json` — **51 ca**: toàn bộ 21 ca của 4 domain lõi + 30 ca ngẫu
nhiên (seed=42) từ 31 domain khác để không mất tính đại diện, dự kiến **~50-55 phút**:
```bash
cd Code/eval/golden
python ragas_runner.py --score ragas_dataset_holdout_core_focus.json
```
Muốn số đầy đủ, chính xác nhất (thay hẳn cho số 189-ca cũ) thì chạy bản đầy đủ 394 ca (không
`--limit`, ~7 tiếng) — để qua đêm là hợp lý nhất.

`ragas_dataset_holdout_sample30.json` (mẫu 30 ca cũ, dựng từ bộ 189-ca TRƯỚC khi vá domain-coverage)
**không còn đại diện nữa** vì nó không có ca nào ở 4 domain lõi — đã bị thay bằng
`ragas_dataset_holdout_core_focus.json` ở trên, giữ lại file cũ chỉ để tham khảo lịch sử.

### Kết quả CHÍNH THỨC, MỚI NHẤT — `--score` TOÀN BỘ 394 ca sau khi vá domain-coverage (2026-10-14, dj tự chạy qua đêm, 11 giờ 40 phút 15 giây, KHÔNG `--limit`)

Đã tự kiểm tra lại bằng cách đọc trực tiếp `ragas_dataset_holdout_score.json` (394 dòng) và đếm giá
trị non-null cho từng cột — khớp đúng với số script tự in ra màn hình:

| Chỉ số | n đo được / 394 | Mean | Ngưỡng | Đạt? |
|---|---|---|---|---|
| Answer Relevancy | **393/394 (99,7%)** | **0,3766** | ≥ 0,90 | ❌ chưa đạt |
| Context Precision | **375/394 (95,2%)** | **0,8064** | ≥ 0,85 | ❌ chưa đạt, sát ngưỡng nhất |
| Context Recall | **339/394 (86,0%)** | **0,6844** | ≥ 0,85 | ❌ chưa đạt |
| Faithfulness | **309/394 (78,4%)** | **0,4049** | ≥ 0,95 | ❌ chưa đạt, hụt rất nhiều — **n đo được DƯỚI 80%, tự script cảnh báo "đừng trích số này"** |

**Lưu ý trung thực về Faithfulness ở lần đo này:** coverage 78,4% (309/394) thấp hơn ngưỡng 80% mà
`ragas_runner.py` tự đặt ra để cảnh báo — thấp hơn cả lần đo 189-ca trước (86%). Số 0,4049 vẫn được
ghi lại ở đây (gần với 0,3806 của lần trước, nên nhiều khả năng là số thật chứ không phải nhiễu do
mẫu nhỏ), nhưng khi trích vào báo cáo cần nói rõ "faithfulness đo được trên 78% số ca, phần còn lại
giám khảo LLM không ra được JSON hợp lệ (timeout hoặc lỗi parse)" thay vì chỉ ghi mỗi con số.

So với lần đo 189-ca (trước khi vá domain-coverage): cả 4 chỉ số đều **tăng nhẹ** (Faithfulness
0,3806→0,4049; Answer Relevancy 0,3687→0,3766; Context Precision 0,8056→0,8064; Context Recall
0,6629→0,6844) — ổn định, không dao động mạnh, củng cố thêm là số thật chứ không phải nhiễu đo đạc.

**4 domain lõi, đã đo được (n ca hợp lệ ở mỗi domain, không phải n RAGAS job thành công):**

| Domain | n ca | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|---|
| Hộ tịch | 4 | NaN (0/4 đo được) | 0,664 (4/4) | 0,963 (3/4) | NaN (0/4 đo được) |
| Đăng ký, quản lý cư trú | 7 | 0,608 (5/7) | 0,513 (7/7) | 0,857 (7/7) | 0,786 (7/7) |
| Chứng thực | 8 | 0,401 (8/8) | 0,582 (8/8) | 0,750 (8/8) | 0,875 (8/8) |
| Bảo trợ xã hội | 2 | 0,375 (2/2) | 0,399 (2/2) | 1,000 (2/2) | 0,500 (2/2) |

Hộ tịch chỉ có 4 ca nên n quá nhỏ để kết luận gì chắc chắn (faithfulness/context_recall của riêng
domain này không đo được job nào trong 4 — giám khảo LLM không ra JSON hợp lệ cho cả 4 ca, có thể do
câu hỏi/ngữ cảnh domain này khó hơn hoặc trùng hợp ngẫu nhiên với mẫu quá nhỏ). 3 domain còn lại có
số đầy đủ, dùng được.

**Kết luận cuối cùng cho báo cáo:** đây là số RAGAS chính thức, thay thế số 189-ca cũ, phủ đủ cả 68+
domain (thực tế 108 domain) bao gồm cả 4 domain lõi. Cả 4 chỉ số đều dưới ngưỡng; Context Precision
sát ngưỡng nhất (0,8064 vs 0,85). Không cần chạy lại RAGAS nữa trừ khi muốn tăng n đo được của riêng
Hộ tịch bằng cách bổ sung thêm ca cho domain đó trong golden set.

# Báo cáo Phase 23 — sửa 3 họ lỗi blackbox (2026-10-07)

Làm tuần tự 23a -> 23b -> 23c, chạy gate sau mỗi phần và cuối; không phần nào phải hoàn tác. Chế độ luật (`S3_USE_LLM=0`, `S3_PLANNER_MODE=rules`, `S3_NO_WARMUP=1`), không dùng GPU/LLM.
Không đọc/chạy bộ nghiệm thu (`cases_h2/h3/h4`, `cases_pseudo_real*`, `cases_team`, các file giả định/kết quả của chúng). Hai dòng `team`/`pseudo_real` trong bảng `run_concise` chỉ là số tổng do chính lệnh gate in ra (không xem từng ca).
Ca mới: `eval/build_p23.py` (74 ca `p23-*`, split dev: L1 29, L2 19, L3 26; câu tự nghĩ, nhiều lĩnh vực và kiểu nhiễu) nối vào `cases.jsonl`; 26 hội thoại vào `cases_ctx.jsonl` (split `ctx-p23`, chạy `run_ctx.py --split ctx-p23`: 26/26). Gate DEV cũ nay loại id `p16/p18/p19/p23`.

## Số trước / sau (gate)
| | trước | sau |
|---|---|---|
| DEV cũ 209: top-1 / hành vi / bịa số | 158/164 (96,3%) / 97,6% / 0,0% | 159/164 (97,0%) / 97,6% / 0,0% |
| DEV `multi_intent` (top-1 / hành vi) | 14/15 / 100% | 15/15 / 100% |
| ngoài phạm vi DEV | 30/30 | 30/30 |
| HOLDOUT cũ: top-1 / hành vi / bịa số | 54/55 / 95,5% / 0,0% | 54/55 / 95,5% / 0,0% |
| ctx (91 ca, lượt cuối) | 89/91 | 89/91 (ctx-p23: 26/26) |
| synth TRAIN / TEST | 96,3% / 96,3% | 96,3% / 96,4% |
| synth `glued` TRAIN / TEST (cùng câu có dấu cách) | chưa có biến thể (đo gián tiếp: `perturb` glue 43,4%) | 97,6% / 96,1% (98,4% / 97,2%) |
| synth [ambig] hỏi thừa / chọn sai | 0,9% / 0,0% | 0,9% / 0,0% |
| synth [oos] / [chitchat] | 38/40 / 20/20 | 38/40 / 20/20 |
| synth biến thể khác (TRAIN/TEST) | abbr 100/100, ask 96/100, ask_casual 95/98, casual 100/97, casual_nodau 99/99, clean 98/100, drop 94/79, long 88/92, nodau 100/100, swap 100/96, typo 92/93 | như cũ; chỉ casual TEST 97 -> 99 |
| DEV focus (`run_concise`) | 284/288 (99%) | 349/353 (99%, gồm 74 ca p23) |
| task thừa (DEV / HOLDOUT / ctx) | 0 / 0 / 0 (team 1/8) | 0 / 0 / 0 (team 0/8) |
| `perturb.py` bất biến | 93,70% (lần đo đầu, trước khi sửa) | **99,44%** (7.056/7.096; 649 ca gốc) |
`perturb.py` theo loại (sau): label/bullet/quote/emoji/upper/space/mixed 100%, polite 99,5%, punct 99,4%, nodau 98,2%, glue 96,6%. Trước (lần đo đầu): glue 43,4%, nodau 94,0%, polite 98,0%, punct 98,2%, mixed 98,2%, quote 99,1%.
Test: `test_data`, `memory_test`, `context_test`, `answer_llm_test`, `planner_hybrid_test`, `p20_api_test`, `smoke_test`, `selftest.py` đều xanh; mới `server/tests/p23_input_test.py` (bỏ nhãn, tách chữ dính, chữ lạ, điều kiện; không cần LLM).
Ghi chú đo: số "trước" của họ L1/L2/L3 chỉ tái hiện bằng tay (3 ca gốc + biến thể đều lỗi như nhóm báo); không đo lại 74 ca p23 trên mã cũ.

## 23a. Nhãn lượt, chữ lạ (L1)
**Nguyên nhân gốc (đọc `trace["ctx"]`):** "Turn" là chữ lạ hoàn toàn nên `rank._weight` cho nó trọng số lớn nhất (`max_idf`) -> `_contextualize` coi câu có "chữ nghiệp vụ lạ" (`distinct`) -> chặn kế thừa -> `independent` ("chữ nghiệp vụ lạ còn dư, không nối") -> cổng chữ-đặc-trưng cho ngoài phạm vi -> `off_topic`. Tức MỘT chữ lạ đủ đổi hướng dù câu có từ nối + mục hỏi + chủ đề đang nói. Hai lớp sửa:
1. `retrieval/context.strip_labels` (gọi ở `resolve` cho CẢ lịch sử và `policy.pre_check`): bỏ nhãn lượt đầu câu (`Turn N:`, `User:`, `Câu N:`, `Q:`, `Q2)`, `Bạn:`, `Hỏi:`, `Lượt 2 -`, `[User]`, `(Turn 2)`, `**Q:**`, `2)`, `2.`, `- `, `> ` và chồng nhiều nhãn), emoji, khoảng trắng/xuống dòng, ngoặc kép bao quanh, lời đệm đầu/cuối ("dạ", "ad ơi", "cho em hỏi", "ạ", "nhé", "giúp mình với ạ"); không cắt "Câu 2 là gì", "1.000656", lời chào (là tín hiệu xã giao của `_is_chitchat`); lượt trợ lý chỉ bỏ nhãn chữ để không phá danh sách "1) A 2) B".
2. `rank._contextualize`: chữ lạ HOÀN TOÀN (không có trong kho, gõ sai cũng không sửa được) không tính vào `distinct` nữa, chỉ đặt `uncertain` và ghi lý do ("chữ lạ [...] chỉ hạ độ tin cậy") vào `why`. Chữ nghiệp vụ lạ THẬT (có trong kho, thủ tục khác) vẫn làm câu độc lập.
Sửa kèm (tìm thấy khi dựng `perturb.py`, cùng một nguyên nhân "nhiễu bề mặt đổi quyết định"): luật điều kiện không dấu (`neu ... thi`, `truong hop`), tách ý theo `va`/`voi lai`, luật đời thường không dấu (`doc than`, `sao y`), `_cond_steps` không dấu, "kéo dài chữ" (`khôngggg`), `steps` không còn đi kèm mục khác khi chỉ là từ hỏi ("lệ phí thế nào"), cụm "có kết quả", chuẩn hoá NFC (cả tên kho: một số tên là NFD làm lệch dấu).
**Bộ biến đổi `eval/perturb.py`:** 11 loại nhiễu (label, bullet, quote, emoji, polite, upper, space, punct, glue, nodau, mixed), seed cố định, chỉ lấy ca đã đúng, so (top-1 các task, hành vi) với câu gốc, in tỉ lệ theo loại + liệt kê ca hỏng. Gate >= 98%: đạt 99,44%.

## 23b. Dính liền và teencode (L3)
**Nguyên nhân gốc:** chữ dính ("kethon") là MỘT token không khớp chữ nào của kho; `understand` chỉ tách theo dấu cách nên mất tên thủ tục (-> "không tìm thấy"); thêm nữa `split_segments` dùng cặp chữ liền kề nên phải tách chữ dính TRƯỚC khi tách ý (đo: gỡ lỗi này nâng glued từ ~85% lên ~96%).
**Sửa:** `retrieval/query.unglue` + `unglue_text` (gọi ở `resolve` và `understand`): quy hoạch động trên từ vựng kho (tên thủ tục, lĩnh vực, chữ chỉ mục, chữ dừng, viết tắt, chữ diễn ngôn/thứ tự), mỗi mảnh phải là âm tiết hợp lệ (âm đầu + vần + âm cuối) HOẶC viết tắt có trong kho; chấm điểm theo cặp/bộ ba chữ liền kề có trong tên thủ tục (cụm dài nhất), rồi ít mảnh nhất; chữ một ký tự ("y tế", "nhà ở") chỉ nhận khi kề một cặp trong tên; chữ 4-5 ký tự cần cặp trong tên (hoặc toàn chữ chức năng); cách một lỗi gõ so với một chữ của kho mà không có cặp thì để cho `Index._fix` (lỗi chính tả, không phải dính). Giữ dấu cho từng mảnh khi chuỗi NFC. Chữ nước ngoài ("karaoke", "bitcoin", "iphone", "facebook", "youtube") không tách được thành âm tiết hợp lệ nên không thành chữ nghiệp vụ.
**Teencode theo nhóm** (`PRE_SYN`; chọn từ chữ lạ thường gặp ở DEV/synth: `dk, j, ubnd, cccd, hkd, hso, xn, tp, ow, onl, ntn`): phủ định `ko/kg/khg/kh/k/hok -> không` (`hk` giữ là hộ khẩu), viết tắt mục `tg/lp/vb/xn`, `fi -> phí`, `vs -> với`, `đc -> được`.
**Synth `glued`** (`eval/synth_retrieval.py`): 3 kiểu (A dính hết không dấu; B dính cụm 1-3 chữ có dấu; C lời dẫn teen + cụm dính + câu hỏi mục), TRAIN/TEST seed riêng, sinh bằng Random riêng (seed + 7) nên mẫu các biến thể khác không đổi; báo riêng, kèm "cùng câu có dấu cách" để thấy phần lỗi do dính (hiện ~1-1,5 điểm). `core()` chuẩn NFC (sửa lỗi bộ sinh typo trên tên NFD).
Gate: glued TRAIN 97,6% / TEST 96,1% (>= 90%), biến thể khác không đổi, hỏi thừa 0,9% (<= 1,5%), oos 38/40. Ba ca blackbox đúng (`t muon đk kethon`, `muon dang ky kethon`, và `t muon dk ket hon`/`đk kết hôn` vẫn đúng).

## 23c. Điều kiện và task thừa (L2)
**Nguyên nhân gốc:** (1) câu "nếu A và B thì ..." bị `split_segments` tách ở "và" ngay TRONG vế điều kiện; mảnh hoàn cảnh "tổ chức tang lễ ở nơi khác" mượn chữ chung (`tổ chức`, `lễ`) của "thông báo tổ chức lễ hội" nên thành task thứ hai (chữ đặc trưng `tang` của chính mảnh lại không nằm trong tên đó: 57% chữ hiếm của mảnh không được tên phủ). (2) vì các mảnh tách rời nên "cần làm gì" ở mảnh cuối thành mục `steps`.
**Sửa (`retrieval/rank.py`):** (a) `_borrowed`: mảnh sau chỉ khớp <= 3 chữ, phủ tên < 50% và phần lớn chữ hiếm của mảnh không nằm trong tên đó thì KHÔNG là task (gộp vào ý trước; không mang theo 'là gì'); (b) `_cond_head`: câu "nếu <việc chính + hoàn cảnh phụ> thì <hỏi mục không nêu thủ tục>" là MỘT ý: thủ tục = việc nêu đầu vế điều kiện (cắt ở nhưng/mà/và/phẩy, 'thì' CUỐI CÙNG), phần sau là điều kiện (`flags["condition"]`), mục mặc định `components` (không `steps`), mục nêu rõ (phí, thời hạn) giữ nguyên; không áp dụng khi thủ tục đã nêu trước "nếu" (đường cũ lo). Hoàn cảnh đi qua `condition_index` như cũ: khai tử chỉ có dòng đối tượng nên trả "Cổng không công bố riêng phần điều kiện/giấy tờ cho trường hợp này".
Kết quả: ca L2 gốc ra MỘT task (khai tử 1.000656), `components` + điều kiện, không `steps`, không "lễ hội"; 19/19 biến thể p23_L2; DEV `multi_intent` 15/15; task thừa 0; TC06 (số tổng của bộ team trong `run_concise`) hết task thừa.

## Chưa sửa được / còn lỗi
- `perturb.py` còn 40 ca hỏng/7.096, gần hết là nhiễu đổi nghĩa thật: bỏ dấu ("sổ đỏ" -> "so do", "à cái thứ tư" -> "thu tu"), dấu phẩy chen trước "thì/cho" tách một tên thủ tục thành hai ý ("gia hạn giấy phép lao động; cho người nước ngoài"), "Nếu X , thì ..." khi X tự gọi tên một thủ tục khác, dính chữ giữa hai thủ tục anh em ("khai tửthời gian").
- Dính chữ 4-5 ký tự không có cặp trong tên ("tờgì": bị coi là lỗi gõ của "tôi"), "số3", dính qua chữ số; lời chào + nhãn ("Chào bạn, câu hỏi 2: ..."): lời chào cố ý không bị cắt nên nhãn không còn ở đầu câu.
- Synth `glued` TEST 96,1% còn ~3,9% sai, phần lớn là tên dài/anh em (chính bản có dấu cách cũng sai 2,8%).
- Chưa có số trên bộ mù cho ba họ lỗi (người điều phối chạy). Chưa đo với `S3_USE_LLM=1`.
- HOLDOUT cũ không đổi; DEV p23 do người sửa tự soạn nên dễ hơn câu thật.

## File đã đổi
Mã: `retrieval/context.py` (`strip_labels`), `retrieval/query.py` (`unglue`, `unglue_text`, `_squash`, `COND_W`, `PRE_SYN`, `_colloquial` không dấu, `split_segments`, `_tidy_fields`), `retrieval/rank.py` (NFC tên kho, `_contextualize`, `_borrowed`, `_cond_head`, nạp `VOCAB/EXTRA_KNOWN`), `server/policy/policy.py` (`pre_check`).
Eval: `eval/perturb.py` (mới), `eval/build_p23.py` (mới), `eval/synth_retrieval.py`, `eval/run_ctx.py` (ctx-p23 chạy riêng), `eval/p19_compare.py` (loại p23), `eval/cases.jsonl` (+74), `eval/cases_ctx.jsonl` (+26), `eval/results/{p23,p23_concise,perturb_p23}.json`.
Test: `server/tests/p23_input_test.py` (mới).
Tài liệu: `README.md`, `docs/EVAL.md`, `docs/CONTRIBUTING.md`, `docs/ARCHITECTURE.md`. Không sửa `docs/PLAN_*.md`, không đụng `repo/`.
Lệnh gate (đều xanh): `python -m system3.data.tests.test_data`; `cd server && python tests/memory_test.py && python tests/context_test.py && python tests/answer_llm_test.py && python tests/planner_hybrid_test.py && python tests/p20_api_test.py && python tests/p23_input_test.py && python smoke_test.py`; `cd eval && python selftest.py && python run.py --adapter answer_adapter:adapter --name p23 --split all && python run_ctx.py && python synth_retrieval.py && python run_concise.py --name p23_concise && python perturb.py --name p23` (Windows: `PYTHONIOENCODING=utf-8 S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`).

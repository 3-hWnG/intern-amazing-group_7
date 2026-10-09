# Báo cáo Phase 18 — sửa theo nhóm lỗi chung (2026-10-06)

Làm tuần tự A -> B -> C -> D -> E -> F, chạy gate sau A, B, (C+D), (E+F) và cuối. Không đọc/chạy `cases_h3`, `cases_h2`, `cases_team`, `cases_pseudo_real` (+ file giả định/kết quả của chúng); hai dòng team/pseudo_real trong bảng `run_concise` chỉ là số tổng do chính lệnh gate in ra, không xem từng ca.
Ca kiểm thêm: `eval/build_p18.py` (138 ca `p18-*`, split dev, câu tự nghĩ, expected.fields đúng ý người hỏi) nối vào `cases.jsonl`; kèm 1 khối assert trong `server/tests/context_test.py`.

## Số trước / sau
| mốc | DEV focus (162 ca cũ+p16) | HOLDOUT cũ focus | task thừa DEV | ca p18 (focus) | DEV cũ 209: top-1 / hành vi / bịa | HOLDOUT cũ: top-1 / hành vi | ctx | synth TRAIN / TEST |
|---|---|---|---|---|---|---|---|---|
| gốc | 113/162 (70%) | 29/49 (59%) | 11/230 | - | 158/164 / 203/209 / 3 | 54/55 / 64/67 | 89/91 | 96,4 / 95,4 |
| sau A | 151/162 (93%) | 44/49 (90%) | 8/230 | - | 158/164 / 203/209 / 2 | 54/55 / 64/67 | 89/91 | 96,3 / 95,4 |
| sau B | 158/162 (97,5%) | 47/49 (96%) | 0 | 77/77 | 158/164 / 204/209 / 0 | 54/55 / 64/67 | 89/91 | 95,8 / 95,6 |
| sau C+D | 158/162 | 47/49 | 0 | 86/86 | 158/164 / 204/209 / 0 | 54/55 / 64/67 | 89/91 | 95,8 / 95,6 |
| sau E+F | 158/162 | 47/49 | 0 | 103/103 | 158/164 / 204/209 / 0 | 54/55 / 64/67 | 89/91 | 96,3 / 96,3 |
| **cuối** | **158/162 (97,5%)** | **47/49 (96%)** | **0 (0/229)** | 109/109 (138 ca; top-1 130/131, hành vi 138/138) | 158/164 (96,3%) / 204/209 (97,6%) / 0 (0,0%) | 54/55 / 64/67 | 89/91 | 96,3 / 96,3 |
Mục tiêu: DEV focus >= 90% (đạt 97,5%), HOLDOUT cũ >= 85% (đạt 96%), task thừa DEV <= 2% (đạt 0%). Số trên DEV là số đã tune; ca p18 do chính người sửa soạn nên dễ hơn bộ mù.
Các số khác (cuối): ngoài phạm vi DEV 30/30; selftest OK; luật điều kiện/so sánh/phủ định/thứ tự DEV 100% (điều kiện HOLDOUT cũ 83% -> 100%); ctx fields 31/31 -> 30/31 (xem "đổi quy tắc có chủ ý"); synth ambig hỏi thừa 0,9% (gốc 0,9%), hỏi lại đúng 11/12; độ dài ký tự trung vị 1.269 -> 984, p90 2.433 -> 1.783 (không có ngưỡng); `answer_llm_test`, `memory_test`, `context_test`, `smoke_test`, `test_data` xanh. team (chấm luật, số tổng gate in): task thừa 3/8 -> 1/8; pseudo_real task thừa 1/16 -> 1/16 (chưa xem từng ca).
HOLDOUT-3 chưa chạy (người điều phối nghiệm thu). Chưa đo với `S3_USE_LLM=1`.

## Từng nhóm: nguyên nhân gốc và cách sửa
**A. Trả dư mục (DEV focus 70% -> 93% riêng nhóm này).** Nguyên nhân gốc (nhiều lớp):
1. Cụm chỉ-field bắt sai/thiếu: "hồ sơ" trong "nộp hồ sơ trực tuyến/ở địa chỉ/bằng hình thức nào" bị đọc thành giấy tờ; viết tắt (hso, onl, ow) chỉ khai triển sau khi tìm cụm; thiếu cụm (cơ quan thực hiện/ai tiếp nhận, hình thức nào, thời gian xử lý, bao giờ có kết quả, phải đóng tiền, ai làm, đến đâu để làm, bưu điện...); "chi phí" trong tên thủ tục bị nuốt thành cụm "phí". Sửa `retrieval/query.py` (FIELD_CUES, PRE_SYN, `_tidy_fields`, `_RX_CUES`, `NOT_FIELD`, `_phi_in_name`): trạng ngữ không phải mục ("nộp online mất bao nhiêu tiền" chỉ hỏi phí), "là gì" chỉ tính khi không có mục khác, hỏi nguồn thì không kèm "ở đâu"/cổng DVC, số liệu trong câu (mất 25 ngày, 100.000 đồng) là mục thời hạn/phí.
2. Câu điều kiện "nếu/trường hợp X thì Y": mục lấy từ Y, X là hoàn cảnh (`rank._cond_fields`, `query.strip_condition` thêm kiểu "X thì Y"); không nêu mục thì `components`.
3. So sánh hai thủ tục: mục chung/`explanation` cho cả hai vế. Câu nối/sửa ý/"chắc không?"/"ngắn gọn hơn": kế thừa mục vừa hỏi (`ConvState.note` giờ ghi mục của LƯỢT GẦN NHẤT, `rank` và `Segment.evidence`); "chắc không" thêm căn cứ pháp lý. Danh sách "khai sinh, khai tử, kết hôn cần giấy tờ gì" và "A mất bao nhiêu tiền, B thì sao" dùng chung mục (`_share_fields`).
4. "X ở đâu" chung chung (không nói nộp/địa chỉ) mà cổng không ghi địa điểm thì trả `agency` (`policy`, cờ `Task.where`); câu hỏi chung ("làm thủ tục X") trả bản tóm tắt ngắn (mỗi mục <= 450 ký tự, `answerer.SUMMARY_CHARS`).

**B. Task thừa / multi-intent quá nhạy (11/230 -> 0).** Gốc: tách theo dấu phẩy/"và" rồi mọi mảnh có chữ khớp một thủ tục láng giềng đều thành task. Sửa `retrieval/rank.py`: (1) mảnh chỉ còn động từ đệm của cụm hỏi mục ("giải quyết trong bao lâu", "thực hiện") không thành mảnh; `_weak` xét chữ chung và độ phủ tên; (2) lời kể hoàn cảnh (không mục hỏi, không động từ yêu cầu muốn/cần/xin/làm/nếu — kể cả "không muốn", "từng làm") bị bỏ khi còn mảnh hỏi thật (`_drop_narrative`, `_asks`); (3) mảnh hỏi duy nhất không gọi tên thủ tục thì ghép lời kể xếp hạng lại (`_dangling`, chỉ nhận khi tên khớp tốt hơn); (4) "Nếu ... thì ..." không ra thủ tục là phần điều kiện của đoạn trước (`_attach_orphans`); (5) hai đoạn cùng thủ tục gộp một (`_merge_same`, kể cả đường "story"); (6) "không phải A hay B" loại cả B (`refs.extract_negation`); (7) mảnh yếu kiểu "xin cấp lại sổ hộ khẩu giấy" (phủ ít tên dài, chữ rời rạc) là ngoài kho thay vì láng giềng (`WEAK_PREC2`, `_phrase`). Multi-intent thật vẫn giữ (DEV multi_intent 100%, 6 ca p18_B_multi).

**C. Hỏi lại khi mơ hồ.** Đã có luật >= 3 nhóm gần nhau (giữ, thêm: chữ hiếm chỉ có ở thủ tục đứng đầu -> đủ phân biệt, giảm hỏi thừa, `_near`). Thêm nhóm chung quá rộng: câu CHỈ gồm tên lĩnh vực ("thủ tục hộ tịch", "đất đai", "cư trú", "nuôi con nuôi"...) hỏi lại với mỗi họ một bản (`_domain_near`, `Index.domains`); không bắt "thẻ căn cước", "chứng thực bản sao" (có chữ ngoài tên lĩnh vực). Không hỏi lần hai: giữ cơ chế cũ (test trong `context_test`).

**D. Điều kiện/trường hợp.** Gốc: Planner luật không bao giờ truyền hoàn cảnh; hồ sơ trả toàn bộ (cắt 1.100 ký tự nên đoạn của trường hợp có thể không hiện). Sửa: hoàn cảnh ("nếu/trường hợp", hoặc lời kể có "từng/chưa/không có/là...") đi vào `Task.conditions`; Policy chuyển thành `soft_conditions` (không nhờ LLM thêm) và khớp mục `condition_index` (nay gồm cả mục "who" là tên trường hợp, + bảng ~8 nhóm từ đời thường `_SITUATION`); khớp chắc (>= 2 chữ đặc trưng, >= 35%) thì chỉ trả giấy tờ của đúng trường hợp (`policy._strong_case`, `answerer._case_pick`: "Theo trường hợp bạn nêu:" + khối đó) kèm nguồn; không có dữ liệu thì "Cổng Dịch vụ công không công bố riêng phần điều kiện/giấy tờ cho trường hợp này, mình không khẳng định...". Ghi chú không còn nhận nhầm "người nước ngoài" ~ "Người Việt Nam định cư ở nước ngoài" (so khớp đối xứng `_jacc`). Luật điều kiện HOLDOUT cũ 83% -> 100%.

**E. Từ chối nhầm / chọn nhầm anh em.** Sửa: "chi phí"/"phí" trong tên thủ tục không bị nuốt (xin lỗi sai với "hỗ trợ chi phí y tế"); cổng "không chữ hiếm nào khớp" bỏ qua khi tên đã phủ chắc (`prec`) (xin lỗi sai với tên toàn chữ thường như "Đính chính Giấy chứng nhận đã cấp"); gõ ĐẦU tên dài đủ mọi chữ được cộng điểm (`PREFIX_BONUS`) hơn bản ngắn khớp rời rạc; `đổi họ/sửa tên con/sửa giấy khai sinh` -> thủ tục thay đổi, cải chính hộ tịch (`COLLOQUIAL`). Synth TEST 95,4 -> 96,3.

**F. Đời thường + nhiều lượt.** Thêm teencode/viết tắt (mik, e, hso, onl, ow, vi/viec), chủ ngữ + động từ ("gia đình cần đi khai tử", "cho mẹ em") không còn là chữ của tên thủ tục (`_SUBJ`, `_BENEF`, `_MODAL_GO`: trước đây "gia đình cần đi khai tử" mất hẳn ý khai tử); hội thoại: kế thừa mục (xem A), sửa ý "không phải X" giữ mục, "chắc không?".

## Đã sửa chưa hết / không sửa được
- "ở đâu": bộ test các đợt trước không thống nhất (cùng "chứng thực chữ ký ở đâu" khi thì `address` khi thì `agency`; "nộp ở đâu" 2 ca đợi `agency`). Chọn quy tắc dữ liệu (xem A.4) nên còn sai: ctx `hold-86` (fields 30/31, top-1 vẫn 89/91), `p16-C_sibling-04`, `multi_field-07`, `multi_intent-05`. Không sửa đáp án.
- `hallucination_unsupported-14` ("Mức phạt nếu ... bao nhiêu" đáp án explanation), `hold-rule_condition-05` ("... thì làm sao": ta trả `steps`, đợi `components`), `hold-ctx_cond_evidence-01` ("phải làm thế nào, cần giấy tờ gì thêm": dư `steps`): "làm sao/làm thế nào" vẫn là mục `steps`.
- Chọn nhầm anh em còn: `p16 B_scope-15` ("con tôi bị khuyết tật, muốn xin giấy xác nhận"), `p18 E_scope-02` ("giấy đăng ký hộ kinh doanh bị mất, xin cấp lại" ra tên liệt kê "tổ hợp tác/hợp tác xã/chi nhánh"); thử phạt tên liệt kê nhiều chữ hiếm: synth tụt (-0,6/-1,4) nên hoàn tác.
- `p16 B_scope-11` ("Cháu bé bị bỏ rơi, vợ chồng tôi muốn nhận về nuôi") nay hỏi lại (>= 3 bản nuôi con nuôi) thay vì trả lời (đáp án p16 là answer); top-1 đúng. Thử loại bản "đăng ký lại" khỏi nhóm gần: làm hỏng 2 ca clarify p16 nên hoàn tác.
- Câu mơ hồ kiểu đời sống ("làm giấy tờ cho con") vẫn bị xin lỗi, không hỏi lại; câu chung chỉ nhận khi chỉ gồm tên lĩnh vực.
- Hoàn cảnh khớp condition_index vẫn là khớp chữ; chỉ 894/5.952 dòng là tên trường hợp thật (khai sinh, kết hôn chỉ có dòng đối tượng nên trả "không công bố riêng").
- Bỏ qua việc dựng bảng sự kiện từ condition_index (theo yêu cầu "nếu không gọn").

## File đã đổi
Mã: `retrieval/query.py`, `retrieval/rank.py`, `retrieval/context.py`, `retrieval/refs.py`, `server/planner/planner.py`, `server/policy/policy.py`, `server/answer/answerer.py`, `server/tests/context_test.py`.
Eval: `eval/build_p18.py` (mới), `eval/cases.jsonl` (+138 ca `p18-*`), `eval/P18_REPORT.md`, `eval/results/{p18,p18_concise,p18_base,p18_base_concise,gA,gB,gD,gF}*.json`.
Tài liệu: `README.md` (bảng số đo, giới hạn), `docs/EVAL.md`, `docs/ARCHITECTURE.md`, `docs/CONTRIBUTING.md`, `docs/PLAN_SYSTEM3_DOT4.md`.
Lệnh gate (đều xanh): `python -m system3.data.tests.test_data`; `cd server && python tests/memory_test.py && python tests/context_test.py && python tests/answer_llm_test.py && python smoke_test.py`; `cd eval && S3_USE_LLM=0 python selftest.py && ... run.py --adapter answer_adapter:adapter --name p18 --split all && python run_ctx.py && python synth_retrieval.py && python run_concise.py --name p18_concise` (Windows: `PYTHONIOENCODING=utf-8`).

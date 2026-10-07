# Plan System 3 — đợt 5 (2026-10-07), từ feedback lần 3

Nguồn: `System-3-Feedback-lan-3.pdf` (feedback cho ngày 06/10, gồm ảnh chụp blackbox test, ảnh chụp plan/README, bản kiểm kê 24 mâu thuẫn và ý kiến của Nhân).

## 1. Feedback nói gì

**Điểm cộng:** câu trả lời đã concise hơn nhiều.

**Lỗi blackbox nhóm thấy (tôi đã tái hiện cả ba trên code hiện tại):**
| # | Hiện tượng | Tái hiện | Nguyên nhân gần |
|---|---|---|---|
| L1 | Hỏi tiếp có tiền tố "Turn 2:" thì hệ thống "nổ": trả "Chưa hỗ trợ được, nằm ngoài phạm vi" (bỏ "Turn 2:" thì chạy đúng) | "Turn 2:", "User:", "Câu 2:", "Q:" đều lỗi; "2)", "-", "Bạn:" thì không | Từ lạ ở đầu câu làm câu bị xếp là `independent` + `off_topic`, mất ngữ cảnh kết hôn |
| L2 | Câu khai tử với điều kiện tang lễ vẫn tách thành 2 thủ tục (khai tử + thông báo lễ hội) và trả `steps` thay vì trả điều kiện | TC06: 2 task, cả hai `steps` | "tang lễ" khớp nhầm "tổ chức lễ hội"; câu điều kiện "nếu… thì cần làm gì" chưa trả đúng phần điều kiện |
| L3 | Teencode: "t muon đk kethon" → "Mình không tìm thấy thủ tục nào…" | "kethon" (dính liền) và "muon dang ky kethon" lỗi; "t muon dk ket hon" và "đk kết hôn" thì chạy | Chữ dính liền không tách được; hệ thống chỉ biết cụm đã cách |

**README đã "nhận" 3 lỗi mà chưa sửa** (tôi đọc là 3 câu FAIL của bộ team: TC02, TC03, TC06 — xem mục 4, câu hỏi 1 để bạn xác nhận):
- TC02: lệ phí 8.000đ không có trong snapshot.
- TC03: đáp án mong có thời hạn 7 ngày dù câu chỉ hỏi giấy tờ.
- TC06: điều kiện tang lễ (cũng là L2).

**Bản kiểm kê mâu thuẫn (24 mục, tài liệu so với code):**
- **17 mục tự sửa được (A1–A17).** Số đo trong README đều khớp file kết quả, test đều qua. Lỗi nằm ở đường dẫn, câu chữ, lệnh trong tài liệu, và một mục code (A17).
- **7 mục cần nhóm trả lời (B1–B7).** Nhân đã trả lời, xem mục 3.
- "7s hay 5s": tài liệu nói 7 giây (Planner hybrid) ở chỗ này, 5 giây (bước sinh chữ) ở chỗ khác. Hai bước LLM khác nhau, tài liệu chưa nói rõ.

### Cập nhật 2026-10-07 (bạn trả lời 4 câu hỏi; tôi kiểm lại git và dữ liệu)
- **`D:\Finale_architect\repo` là bản clone git của repo nhóm** (`intern-amazing-group_7`), có hai nhánh: **`V10.6`** (hệ thống cũ, commit `8356740`) và **`system3`** (đang checkout). Tôi đã nhầm khi nói V10.6 "không còn": mã V10.6 vẫn nguyên trong nhánh `V10.6`, đọc được bằng `git show V10.6:<đường dẫn>` mà không động vào cây làm việc.
- **TC02: bạn nhớ đúng.** Con số "Bản chính: Không thu phí; Bản sao: 8.000đ/bản" có trong **bộ corpus tuyển chọn của nhóm** ở nhánh V10.6: `Database/corpus/normalized_procedures.json` (70 thủ tục, 141 KB, lệ phí và thời hạn đã chuẩn hóa: khai sinh, khai tử, kết hôn, nhận cha mẹ con, mai táng, khuyết tật…). Snapshot 1.350 thủ tục cào từ cổng của System 3 **không có** (khai sinh `1.001193` chỉ có lệ phí 0 và chuỗi rỗng). Bộ test 10 câu của nhóm được soạn từ bộ corpus này, nên TC02 ("8.000đ"), TC03 ("7 ngày làm việc") và TC04, TC07 khớp với corpus chứ không khớp với snapshot cổng.
- **Hệ cũ có sẵn "Bộ nhớ người dùng"** (`Frontend/static/js/memory.js`, `/api/profile`, `/api/mcq-memory`): hồ sơ (tỉnh, xã, ghi chú) cộng bộ nhớ các lựa chọn MCQ theo "trục" (ví dụ đối tượng thực hiện), có màn hình xem, thêm, quên và onboarding. Đó là thứ Phase 26 chuyển sang theo tinh thần.

## 2. Suy ngẫm

1. **Ba lỗi blackbox cùng một họ: hệ thống không chịu được "chữ lạ".** Một tiền tố lạ ("Turn 2:") hay một từ dính liền ("kethon") đủ để đẩy câu sang "ngoài phạm vi" hoặc "không tìm thấy", dù phần còn lại của câu rõ ràng. Cổng ngoài phạm vi đang quyết bằng một chữ lạ, thay vì cân với bằng chứng còn lại (có ngữ cảnh, có tên thủ tục khớp). Đây là một nhóm lỗi chung, sửa một chỗ cứu được nhiều ca.
2. **Bộ test của tôi không có loại lỗi này.** Cả ba lỗi blackbox đều nằm ngoài bộ DEV, bộ mù, bộ team. Câu do model soạn có xu hướng "sạch". Cần một bộ kiểm **biến đổi câu** (metamorphic): lấy câu đã đúng, thêm nhiễu (tiền tố nhãn, đánh số, ngoặc, emoji, "ạ/nhé", viết hoa, dính chữ), kết quả phải y nguyên. Bộ này sinh tự động, không cần soạn tay.
3. **"Nhận ra lỗi mà chưa sửa" là lỗi quy trình của tôi.** Ba câu FAIL của bộ team đã nằm trong báo cáo ở mục "Còn yếu" nhưng tôi kết thúc đợt 4 mà không sửa. Từ giờ: mọi lỗi đã biết trên bộ test của nhóm phải hoặc được sửa, hoặc có quyết định ghi lại kèm người chịu trách nhiệm. Không để một lỗi chỉ sống trong README. Plan thêm `docs/KNOWN_ISSUES.md`.
4. **Nhiều agent viết tài liệu mà không có nguồn sự thật chung** nên sinh ra 24 mâu thuẫn. Cần một script nhỏ kiểm tài liệu tự động (số trong README so với file kết quả, lệnh trong tài liệu chạy được, tên file nhắc tới có tồn tại) để lần sau lệch là bị bắt ngay.
5. **Cấu trúc thư mục khi đưa lên GitHub làm gãy lệnh chạy.** `D:\Finale_architect\repo` hiện là bản clone GitHub của nhóm với gốc repo chính là nội dung của `system3`, nên `import system3` không tìm thấy (A1). Đây không chỉ là lỗi tài liệu, là lỗi khởi động của bất kỳ ai clone về. Cần một launcher chạy được dù thư mục gốc tên gì.
6. **`D:\Finale_architect\repo` (nhánh `system3`) lệch với `system3` đang làm việc.** Bản clone là commit lúc 18:13 hôm qua, thiếu các thay đổi sau đó (ví dụ vài file `eval/`, `answerer.py`, báo cáo). Tôi làm việc trong `system3` và không đụng `repo/`; bạn tự đồng bộ và push.

## 3. Quyết định đã có (từ ý kiến của Nhân, và đề xuất của tôi cho phần còn mở)

| Mục | Quyết định | Hành động |
|---|---|---|
| B1: gate DEV focus 90% hay 95% | Nhân: cao nhưng đừng cao đến mức cản việc tối ưu tiêu chí khác; chọn số vừa nhất. **Đề xuất: chốt ≥ 95%** làm cổng hồi quy (hiện 99%, còn dư 4 điểm; 90% quá lỏng vì đã đạt 99%), mục tiêu duyệt ban đầu 90% ghi chú là mốc cũ | thống nhất ở CONTRIBUTING, PLAN, EVAL |
| B2, B3, B4: plan/trace chưa chặn theo dev; PII chưa che trong `messages`; phiên ẩn danh, "Xóa tất cả" xóa của mọi người | Nhân: **giả định mọi thứ hiện giờ là developer mode.** Chế độ người dùng = developer mode ít quyền và ít thông tin hơn; làm bản đầy đủ trước. **Không được để quên trong sản phẩm cuối.** | không build bây giờ; lập `docs/FINAL_PRODUCT_CHECKLIST.md`, gắn thẻ `FINAL-PRODUCT:` trong code, ghi vào bộ nhớ của tôi |
| B5: dữ kiện người dùng không bao giờ được tạo (đường `context_facts` chết) | Nhân: **việc mới: chuyển chức năng cấu hình người dùng từ hệ thống cũ sang đây**, theo tinh thần chứ không sao chép code; cho hệ thống biết người dùng là ai (người dân thường hay doanh nghiệp) để bớt hỏi lại | Phase 26 |
| B6: `S3_USE_LLM` mặc định bật, README nói chưa chứng minh có lợi | Nhân: **bật mặc định là tốt**, không cần tắt, thông tin thêm giúp rõ ràng; **giữ công tắc** | giữ mặc định bật, sửa tài liệu cho khớp, đo giá trị thật ở Phase 27 |
| B7: bộ test dựng lại cần mã V10.6 | Nhân: **làm cho nó tồn tại lại**; phải dựng lại được khi tải từ Git; nhẹ thì commit luôn, nặng thì đưa mã chạy lại và nhận kết quả. **Mã V10.6 còn trong nhánh `V10.6`** và nhẹ (các file `Database/pipeline/` cần dùng khoảng 100 KB) nên **commit luôn** | Phase 28 |
| 7 giây hay 5 giây | Ý ban đầu của nhóm là timeout 7 giây cho 4B. **Đề xuất: cả hai bước LLM dùng 7 giây**, ghi một bảng duy nhất trong tài liệu | Phase 24 và 27 |

## 4. Câu hỏi đã được trả lời (2026-10-07)
1. **"3 lỗi README nhận" = TC02, TC03, TC06.** Xác nhận.
2. **TC03: làm theo đề xuất** — giữ concise (câu chỉ hỏi giấy tờ thì chỉ trả hồ sơ), đánh dấu TC03 là "đáp án nhóm cần sửa" trong `KNOWN_ISSUES.md` và báo nhóm. Không đổi quy tắc concise.
3. **TC02: có dữ liệu** — nằm trong corpus tuyển chọn của nhóm ở nhánh V10.6 (xem trên). Cách xử lý ở Phase 23d.
4. **V10.6:** nhánh `V10.6` của `repo/`. Phase 26 và Phase 28 dùng nó.

## 5. Các phase

**Ràng buộc GPU (2026-10-07):** người dùng đang dùng GPU nên **chạy tuần tự đến hết Phase 26 mà không dùng GPU/LLM**. Mọi lần chạy đặt `S3_USE_LLM=0`, `S3_PLANNER_MODE=rules`, `S3_NO_WARMUP=1`; không gọi Ollama. Phase 27 (đo Answer Composer) và lượt LLM-bật của Phase 29 **chờ GPU rảnh**. Đã sửa luôn A17: server không nạp model khi `S3_USE_LLM=0` và Planner luật; `S3_NO_WARMUP=1` chặn hẳn việc nạp (dùng cho test).

Thứ tự: 23 → 24 → 25 → 26 → 27 → 28 → 29. Phase 24 và 25 nhẹ, có thể xen vào giữa các phase nặng. Phase 26 phụ thuộc câu hỏi 4.
Quy tắc đo như cũ (EVAL.md): không tune trên HOLDOUT-3/4 hay pseudo_real; ba ca blackbox của feedback này được đưa vào **DEV** (tiền tố `p23`) vì chúng đã bị xem. Agent sửa lỗi chỉ nhận mô tả nhóm lỗi chung.

### Phase 23 — Sửa ba họ lỗi blackbox
- **23a. Chịu được tiền tố và chữ lạ (L1).**
  - Tìm nguyên nhân gốc bằng trace: vì sao một chữ lạ đổi quyết định từ `follow_up` sang `independent` rồi `off_topic`.
  - Sửa: bỏ nhãn lượt hội thoại ở đầu câu ("Turn N:", "User:", "Câu N:", "Q:", "Bạn:", số thứ tự); và cổng ngoài phạm vi không được quyết chỉ vì có chữ lạ khi đã có ngữ cảnh hoặc bằng chứng khác (từ lạ chỉ hạ độ tin cậy, không đổi hướng).
  - Dựng **bộ biến đổi câu** `eval/perturb.py`: lấy các ca đã đúng từ DEV và ctx, thêm nhiễu (tiền tố nhãn, đánh số, ngoặc kép, emoji, "ạ/nhé/giúp mình/cho hỏi", VIẾT HOA, khoảng trắng thừa, dấu câu thừa, bỏ dấu cách), yêu cầu top-1 và hành vi giữ nguyên.
  - **Gate:** bất biến ≥ 98% trên bộ biến đổi; hồi quy xanh.
- **23b. Gõ dính liền và teencode (L3).**
  - Tách chữ dính liền bằng từ vựng của kho (tên thủ tục, từ chỉ mục) và quy tắc âm tiết tiếng Việt, kể cả không dấu ("kethon", "dangkykhaisinh").
  - Bổ sung viết tắt/teencode theo nhóm (đk, ko, dc, k, kh, hk, "t", "muon"…), dựa trên phân tích lỗi gõ đời thường trong DEV và synth, không lấy câu từ bộ mù.
  - Thêm biến thể `glued` vào `synth_retrieval.py` (TRAIN và TEST tách rời).
  - **Gate:** synth `glued` ≥ 90% top-1; các biến thể khác không tụt quá 1 điểm; ba ca blackbox đúng.
- **23c. Điều kiện và task thừa (L2, TC06).**
  - Một mảnh câu chỉ trùng một chữ chung với thủ tục khác ("tang lễ" trùng "lễ hội") không được sinh task; cần ít nhất một chữ đặc trưng hoặc tên đủ dài.
  - Câu "nếu X thì tôi cần làm gì" trả phần điều kiện/giấy tờ bổ sung khớp X từ `condition_index` (ví dụ nơi tổ chức tang lễ), mặc định `components` và không `steps`.
  - **Gate:** TC06 pass; DEV `multi_intent` vẫn 100%; không có task thừa mới trong `run_concise`.
- **23d. TC02/TC03 (dữ liệu nhóm, không bịa).** *(ĐÃ LÀM 2026-10-07: `data/team_overlay.py`, bảng `team_fee_overlay` 17 dòng / 15 thủ tục, TC02 pass, bộ team 8/10; TC03 và TC06 ghi trong `docs/KNOWN_ISSUES.md`.)*
  - **Bổ sung từ corpus tuyển chọn của nhóm:** chép `Database/corpus/normalized_procedures.json` từ nhánh V10.6 (commit `8356740`) vào `data/snapshot/team_corpus.json` kèm ghi nguồn trong `SOURCE.md` (141 KB, commit thẳng). Viết `data/team_overlay.py` ghép từng mục corpus với thủ tục của kho theo tên (khớp chắc, kiểm tay danh sách ghép), dựng bảng `team_fee_overlay`.
  - **Quy tắc dùng:** chỉ dùng lệ phí của corpus khi kho **không có lệ phí dùng được** cho thủ tục đó (`fee_none`), không đè dữ liệu cổng; câu trả lời ghi rõ nguồn là "Bộ dữ liệu nhóm (chuẩn hóa từ cổng)"; không suy ra "miễn phí" khi corpus cũng không có. Các mục giá khác (thời hạn…) giữ nguyên dữ liệu cổng, trừ khi cổng trống.
  - **TC02:** phải trả "1 ngày" và "bản chính không thu phí, bản sao 8.000đ" kèm nguồn.
  - **TC03:** theo quyết định ở mục 4: giữ concise; ghi vào `KNOWN_ISSUES.md` là đáp án nhóm cần sửa (nhóm chưa nói đổi quy tắc concise).
  - **Gate:** TC02 pass; `fees` không bị đổi cho thủ tục đã có lệ phí cổng; số thủ tục có lệ phí dùng được tăng (ghi số trước/sau); `test_data` có thêm kiểm bảng overlay.
- **Gate Phase 23:** bộ team 9/10 (TC03 là đáp án nhóm cần sửa, đã ghi quyết định trong `KNOWN_ISSUES.md`), hoặc 10/10 nếu nhóm sửa TC03; mọi ca khác chưa pass phải có dòng quyết định; hồi quy chế độ luật xanh: DEV cũ 209 top-1 ≥ 95%, hành vi ≥ 96%, bịa số ≤ 3%, ngoài phạm vi 30/30, ctx ≥ 89/91, synth TEST ≥ 94%, DEV focus ≥ 95%.

### Phase 24 — Dọn mâu thuẫn (A1–A17) và chặn lệch về sau
- **A1 (quan trọng):** thêm launcher `run_server.py` ở gốc, tự đăng ký package `system3` dù thư mục gốc tên gì (`importlib`); cập nhật README và SETUP; kiểm bằng cách clone vào thư mục tên lạ.
- **A2:** `_EVENTS` là 12 sự kiện (README, `retrieval/README.md`).
- **A3, A4:** sửa ARCHITECTURE: hybrid chạy tuần tự sau luật; task LLM sửa phải route `direct`.
- **A5:** viết lại `server/README.md` (bỏ "STUB", API đầy đủ gồm `/config`, `/procedure/{id}/table`, export, PATCH, DELETE; thêm `conv_state`).
- **A6–A9:** EVAL.md (bộ mù chính thức là HOLDOUT-4, thêm các file giả định, ctx có 118 ca và `cases_p16_aside.jsonl`); `build_p16.py` bỏ lệnh `--split p16aside` hoặc thêm split.
- **A10:** `cases_h2.py`, `cases_h3.py`, `cases_new.py` dùng `system3.data.DB_PATH`.
- **A11, A12:** `eval/README.md` cập nhật; thay đường dẫn máy tác giả bằng `<ROOT>`.
- **A13, A14:** SETUP (dòng smoke_test vào khối lệnh), CONTRIBUTING (thêm `p20_api_test`).
- **A15:** "2 lỗi reset + 1 lỗi bố cục" nhất quán ở P20_REPORT, BAO_CAO, báo cáo ngày.
- **A16:** `requirements.txt` đã cài sạch trên máy bạn (Python 3.12.8, test qua); tôi kiểm lại `.venv` rồi cập nhật README, ghi rõ nguồn là máy của bạn.
- **A17 (code):** bỏ nạp trước (`warm_up`) model khi cả bước sinh chữ và Planner hybrid đều tắt.
- **B1:** thống nhất gate DEV focus ≥ 95% ở mọi tài liệu.
- **Bảng timeout:** một bảng trong ARCHITECTURE cho hai bước LLM (Planner hybrid, tắt mặc định; Answer Composer, bật mặc định), cùng timeout 7 giây (cấu hình được).
- **`docs/KNOWN_ISSUES.md`:** mỗi lỗi đã biết có trạng thái, người chịu trách nhiệm, phase xử lý.
- **`eval/check_docs.py`:** kiểm số trong README so với `eval/results/`, lệnh trong tài liệu, file tài liệu nhắc tới có tồn tại; chạy trong gate.
- **Gate:** `check_docs.py` sạch; kiểm đầu-cuối bằng clone sạch vào thư mục tên lạ rồi chạy theo SETUP.

### Phase 25 — Danh sách "đừng quên cho bản cuối" (B2, B3, B4)
Không build, chỉ ghi để không rơi mất.
- `docs/FINAL_PRODUCT_CHECKLIST.md`: tách chế độ người dùng và nhà phát triển (người dùng = dev mode ít quyền, ít thông tin; chặn `plan`, `trace`, `/config`, `?dev=1` khi không dev); che CCCD/SĐT trong `messages.content` và `plan_json`; phiên và quyền sở hữu hộp thoại (nút "Xóa tất cả" chỉ xóa của người dùng đó); tắt công tắc AI cho người dùng thường nếu nhóm muốn.
- Thẻ `# FINAL-PRODUCT:` tại từng chỗ trong code, tìm được bằng `grep -rn "FINAL-PRODUCT:"`.
- Liên kết từ README và ghi vào bộ nhớ của tôi.

### Phase 26 — Bộ nhớ người dùng (chuyển từ hệ cũ, B5)
Nguồn: nhánh `V10.6` (`Frontend/static/js/memory.js`, `Backend/api/chat_routes.py` mục `/api/profile`, `Backend/api/procedure_routes.py` mục `/api/mcq-memory`). Chuyển theo tinh thần, không sao chép mã; hệ cũ có đăng nhập, System 3 chưa có, nên lưu theo phiên và để chỗ cho tài khoản sau (đánh thẻ `FINAL-PRODUCT:`).
- **Hồ sơ nhẹ, tùy chọn:** tỉnh, xã/phường, **loại người dùng** (người dân / hộ kinh doanh–doanh nghiệp / khác), ghi chú. Khối "Bạn là…" trong panel cấu hình, có nút bỏ qua, xem, sửa, xóa ("quên tất cả") bất cứ lúc nào.
- **Nhớ lựa chọn MCQ:** khi người dùng trả lời thẻ hỏi lại (ví dụ chọn bản "hộ kinh doanh"), hệ thống nhớ theo trục (đối tượng thực hiện…) cho các câu sau, và cho xem/xóa như hệ cũ ("Đã ghi nhận: …"). Đây cũng làm đường `context_facts` hết "chết" ở cấu hình mặc định.
- **Dùng thế nào:** nạp vào Planner như dữ kiện; Policy dùng `procedure_subjects` (đối tượng thực hiện) và hồ sơ để chọn bản đúng đối tượng và **bớt hỏi lại**. Hồ sơ chỉ **ưu tiên**, không được loại thủ tục khi câu hỏi nêu rõ thủ tục khác.
- **Đo:** bộ ca mơ hồ theo đối tượng: có hồ sơ thì không hỏi lại và đúng thủ tục; không hồ sơ thì hành vi như cũ; hồ sơ sai đối tượng không được làm trả sai thủ tục.
- **Gate:** hồi quy xanh; số lần hỏi lại giảm trên bộ ca đối tượng; có test giao diện và API.

### Phase 27 — Bước sinh chữ (Answer Composer): bật mặc định, đo giá trị thật (B6)
- Giữ bật mặc định theo quyết định của nhóm; giữ công tắc.
- Timeout 7 giây (cấu hình được); giảm lần chạm timeout (rút ngắn prompt, giới hạn độ dài sinh).
- Dựng bộ chấm riêng: luật theo `condition_index` (đủ ý, không sai số, không đảo nghĩa) cộng mẫu người chấm 20 câu. So bật/tắt: chất lượng, tỉ lệ timeout, p50/p95.
- Sửa tài liệu: không còn nói "chưa chứng minh có lợi" nếu số đo cho thấy ngược lại, và ngược lại.
- **Gate:** bật không làm tụt số hồi quy; p95 tổng ≤ 10 giây; tỉ lệ timeout < 10%; có bảng so sánh.

### Phase 28 — Dựng lại được từ Git (B7)
- **Lấy lại mã V10.6 từ nhánh `V10.6`** (commit `8356740`, bằng `git show`, không đụng cây làm việc của `repo/`): các file `Database/pipeline/` mà bộ dựng test cần (`retrieval.py`, `textutil.py`, `vocabulary.py`, `paths.py`, `import_db.py`, `normalize.py`, `schema_procedures.sql`, khoảng 100 KB). Đặt vào `eval/vendor_v106/` kèm `SOURCE.md` ghi commit; **commit thẳng** vì nhẹ.
- `eval/rebuild_v106_db.py`: dựng DB kiểu V10.6 từ `data/snapshot/procedures.jsonl` (bản chép của `Database/staging/procedures.jsonl`), để `build_cases.py` và `baseline_adapter.py` chạy lại được; sửa đường dẫn cứng (`D:\Finale_architect\repo\Database\...`) thành tương đối.
- Kiểm bằng cách chạy lại baseline V10.6 và so với `results/baseline.json` (số lịch sử).
- File ca test nhỏ (vài trăm KB mỗi file) commit thẳng vào Git; kết quả chạy lớn thì không commit.
- `eval/REPRODUCE.md` và `eval/run_all.py`: một lệnh dựng DB, chạy mọi gate, in bảng kết quả.
- **Gate:** clone sạch vào thư mục tên lạ, chạy `run_all.py`, ra bảng số khớp bản đang dùng; baseline V10.6 tái lập ra số gần `baseline.json`.

### Phase 29 — Nghiệm thu đợt 5
- Agent mới soạn **HOLDOUT-5** (~90 mục) và **pseudo_real 3** (30 mục), không thấy mã và lỗi cũ; hoặc, nếu có câu hỏi thật từ nhóm, dùng làm bộ kiểm cuối.
- Chạy một lần, cấu hình mặc định (LLM bật) và chế độ luật. HOLDOUT-4 chạy lại một lần để so, vì tôi chưa xem chi tiết lỗi của nó.
- Chạy: bộ team, bộ biến đổi câu, `check_docs.py`, hồi quy đầy đủ.
- **Mục tiêu (chưa hứa):** top-1 bộ mù ≥ 80%, đúng hành vi ≥ 88%; bộ biến đổi ≥ 98%; bộ team 10/10 hoặc quyết định đã ghi. Nếu không đạt thì nói thẳng, không vá theo câu.
- Báo cáo ngày vào `docs/report daily/` theo quy ước tên `d_m_yyyy.md`.

## 6. Rủi ro
- 23b (tách chữ dính liền) dễ tạo khớp sai; phải đối chiếu synth TRAIN/TEST và kiểm "hỏi thừa" không tăng.
- Hạ độ nhạy của cổng ngoài phạm vi có thể làm tăng lỗi "bịa" ở câu ngoài kho; giữ gate ngoài phạm vi 30/30 và bộ câu ngoài kho của HOLDOUT-4.
- Overlay corpus nhóm (23d) phải khớp thủ tục theo tên: khớp sai sẽ gán nhầm lệ phí; nên kiểm tay danh sách ghép và chỉ nhận khớp chắc.
- Đồng bộ `system3` với `repo/` và push GitHub là việc của bạn; nếu hai bên lệch quá xa sẽ khó gộp.

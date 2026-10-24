# Báo cáo đợt sửa câu khó — System 3 (thủ tục) và System 4 (biên dịch lĩnh vực lúc nạp)

Ngày 24–25/10/2026. Nhánh `exec/2026-10-24-hard-questions`. Commit: `a82d970`, `7e78438` (khoá hai bộ test), `b7010d1` (đóng băng code trước lượt test), checkpoint 4 (kết quả + báo cáo).

## 1. Tóm tắt

**System 3, bộ test real_v2** (313 câu thật, khoá trước mọi thay đổi code; mỗi cấu hình chạy đúng một lần):

| Cấu hình | Độ chính xác cân bằng | Hành vi đúng | Top-1 (59 câu answer) | Trả lời đúng trọn |
|---|---|---|---|---|
| Bản gốc (niêm phong lúc khoá) | 0,647 | 56,5% | 33,9% | 32,2% |
| A — luật đọc câu dân | 0,815 | 84,0% | 62,7% | 59,3% |
| B — reranker theo nghĩa (một mình) | 0,692 | 68,7% | 37,3% | 35,6% |
| C — model 4B đọc ý định (một mình) | 0,785 | 81,8% | 42,4% | 42,4% |
| **Bản cuối A + B** (chọn trên dev) | **0,823** | **84,4%** | **64,4%** | **61,0%** |
| Mốc luôn từ chối / luôn trả lời | 0,500 / 0,500 | 79,2% / 18,9% | – / 33,9% | 0% / 33,9% |

Bản gốc → bản cuối, so cặp McNemar: hành vi đúng +96 / −9 câu (p ≈ 2·10⁻¹⁹); trả lời đúng trọn +23 / −6 (p = 0,002). Phần B thêm trên A chỉ +1 câu (không có ý nghĩa thống kê): thực chất cải thiện đến từ A.

**System 4, bộ mù real_v3** (52 câu trên 4 bảng mới chưa từng nạp, mỗi cấu hình một lần): engine mới (SQL trên bảng phẳng biên dịch lúc nạp, bật theo bài tự kiểm) đạt **44/52 = 85%**, bằng đường nhanh cũ (85%) và không khác có ý nghĩa so với đường cũ dùng công cụ bảng (88%; +4 / −6, p = 0,75), nhưng **thời gian trả lời trung vị 0,8 s** so với 5,3 s và 6,2 s. Bỏ bước biên dịch (AI viết SQL trên bảng thô) chỉ được 69%: biên dịch lúc nạp hơn **+8 / −0 câu (p = 0,008)**. Điểm yếu đo được: tệp có hai sheet cùng đối tượng (sân bay) 92% → 62%.

## 2. Giao thức đo (chống "học thuộc đáp án")

- **Dev = real_v1** (282 câu thật, đã chạy và xem từng câu sai từ trước). Mọi luật, từ điển, ngưỡng chỉ được viết / chỉnh trên dev.
- **Test System 3 = real_v2**: 348 câu rút ngẫu nhiên (SEED 20261024) từ pool sạch của real_v1, loại câu real_v1; người gán nhãn (Claude, theo quyết định của trưởng nhóm) gán nhãn và **khoá bằng sha256 + commit `7e78438` trước mọi thay đổi code**; 313 câu chạy được (59 answer / 6 clarify / 248 apologize). Bản gốc chạy niêm phong ngay sau khi khoá. Trong lúc sửa không mở lại câu của real_v2; `eval/hard/dev.py` từ chối chạy real_v2 nếu thiếu `--final`.
- **Test System 4 = real_v3**: 52 câu sinh bằng script có SEED từ 4 bảng Wikipedia (revid cố định), khoá cùng commit; 4 cấu hình "trước" chạy niêm phong trước khi sửa engine.
- **Chỉ số ghi trước** (eval/real_v2/README.md): hành vi đúng 3 lớp; recall từng lớp; **độ chính xác cân bằng** = trung bình recall answer và apologize (chỉ số chính, vì bộ lệch lớp: luôn từ chối đã được 79%); top-1 / top-3 / MRR; **trả lời đúng trọn** = trả lời VÀ thủ tục đầu đúng; Wilson 95%; hai mốc ngây thơ; bộ "sạch" bỏ 11 câu gần trùng real_v1; hai tầng random / chude.
- **Đóng băng**: lượt test chạy trên commit `b7010d1`, không có thay đổi chưa commit trong `server/ retrieval/ eval/hard/` (stamp: `dirty=0`).
- **Kiểm chứng "chỉ thêm sau cờ"**: code mới với mọi cờ tắt (`off`) cho kết quả **trùng bản gốc ở cả 313 câu** của test và 282 câu của dev (0 câu khác về hành vi và thủ tục đầu).

## 3. Ba phương án

Chẩn đoán trên dev (bản gốc): 101/220 câu lẽ ra phải từ chối lại được trả lời (câu kể dài có chữ tình cờ trùng tên một thủ tục), và câu trả lời thường chọn sai thủ tục (top-1 12,7%) vì người dân không gọi tên chính thức ("làm căn cước công dân", "nhập hộ khẩu", "sổ đỏ").

**A — luật đọc câu dân** (mặc định bật, mỗi phần một cờ để lùi lại):
1. `S3_LETTER_STRIP`: bỏ phần thư từ (lời chào, "Bộ Công an cho tôi hỏi", lời cảm ơn, "tôi là [TÊN]").
2. `S3_LEXICON2`: khoảng 20 mục từ dân dùng → tên thủ tục chính thức, theo luật hiện hành (Luật Cư trú 2020 bỏ sổ hộ khẩu → đăng ký thường trú; Luật Căn cước 2023: căn cước công dân → thẻ căn cước; sổ đỏ → đăng ký đất đai, cấp GCN...). Lấy từ lỗi trên dev và từ chính dữ liệu thủ tục.
3. `S3_WEAK_NAME`: đoạn chỉ trùng ≤ 3 chữ của một tên thủ tục rất dài (phủ < 6% tên) không được coi là gọi tên thủ tục.
4. `S3_SCOPE_GATE` (+ `S3_SCOPE_A6`): cổng ý định ngoài phạm vi bằng cụm chữ (server/policy/scope.py): hỏi tình trạng hồ sơ của mình (mã hồ sơ, giấy hẹn, "đã nộp ... chưa nhận"), khiếu nại / phản ánh, kiến nghị cử tri, hỏi luật / xử phạt / hiệu lực văn bản, chế độ nội bộ và tuyển sinh / tuyển dụng ngành Công an, thủ tục không có trong dữ liệu (lý lịch tư pháp, hộ chiếu, bằng lái dân sự...), thông tin chính sách. Ngoại lệ: câu vừa hỏi luật vừa hỏi MỤC của thủ tục ("cần giấy tờ gì", "nộp ở đâu") và đã chọn được thủ tục thì vẫn trả lời; hỏi CÁCH / THỜI HẠN giải quyết khiếu nại, tố cáo là hỏi thủ tục.
5. `S3_FOCUS`: thư dài (≥ 25 chữ) có nhiều đoạn chọn được thủ tục → chỉ giữ đoạn là câu hỏi (dấu "?", động từ yêu cầu, mục được hỏi, gọi tên chắc).
6. `S3_ORG_DEFAULT`: thủ tục chỉ dành cho tổ chức mà câu không nhắc tổ chức nào → lấy bản "hộ gia đình, cá nhân" sát điểm.

**B — truy hồi theo nghĩa + reranker** (`S3_SEMANTIC=1`, mặc định tắt; model có sẵn trên máy, không tải thêm): bge-m3 (Ollama) lấy 10 thủ tục gần nghĩa nhất trong 542 thủ tục cấp xã, hợp với ứng viên của luật; bge-reranker-v2-m3 chấm từng cặp. Ba ngưỡng: điểm tốt nhất < τ_oos → từ chối; thủ tục khác hơn thủ tục luật chọn ≥ τ_swap → đổi; luật không chọn được mà điểm tốt nhất ≥ τ_rescue → trả lời. `S3_SEM_QUERY=seg`: chấm các đoạn luật coi là yêu cầu thay vì cả thư (thư dài làm reranker chấm thấp cả thủ tục đúng).

**C — model 4B đọc ý định** (`S3_READER=1`, mặc định tắt): qwen3:4b-instruct (Ollama, nhiệt độ 0) đọc câu, trả JSON {ý định ∈ thủ tục / tình trạng / khiếu nại / luật / nội bộ / khác, tên thủ tục bằng chữ}. Model không bao giờ ghi mã thủ tục: luật xếp hạng TÊN model đọc trên cùng kho; ý định khác "thủ tục" → Policy từ chối kèm lý do. `S3_READER_INTENT=0`: bóc tách, chỉ dùng tên.

## 4. Kết quả trên dev (real_v1, 282 câu) và cách chọn bản cuối

| Cấu hình | Cân bằng | Trả lời (recall) | Từ chối (recall) | Top-1 | Trả lời đúng trọn |
|---|---|---|---|---|---|
| Bản gốc (= mọi cờ tắt) | 0,636 | 74,6% | 52,7% | 12,7% | 10,9% |
| A | 0,902 | 85,5% | 95,0% | 74,6% | 69,1% |
| B một mình (đoạn, −3,5 / 0,5 / 0) | 0,709 | 69,1% | 72,7% | 21,8% | 21,8% |
| C một mình | 0,730 | 56,4% | 89,5% | 32,7% | 30,9% |
| A + C | 0,766 | 54,5% | 98,6% | 49,1% | 43,6% |
| A + C (chỉ tên) | 0,918 | 89,1% | 94,5% | 70,9% | 65,5% |
| **A + B** (đoạn, −8 / 2,0 / 99) | 0,911 | 87,3% | 95,0% | 74,6% | 69,1% |

Số dev **cao hơn số test** vì đã nhìn từng câu sai của dev để sửa (A: 0,902 dev → 0,815 test). Đây là lý do chỉ báo số test.

**Tiêu chí chọn** (ghi trong `eval/hard/sem_grid.py` trước lượt test): tối đa độ chính xác cân bằng **với ràng buộc** số câu trả lời đúng trọn không thấp hơn cấu hình chỉ dùng luật; hoà → đúng trọn cao hơn → ngưỡng bảo thủ hơn. Tiêu chí này được đặt sau hai lượt lưới đầu và ghi lại vì hai tiêu chí đơn giản đều hỏng:
- Cân bằng thường tính "trả lời" là đúng cả khi trả lời SAI thủ tục; theo nó, B đổi thủ tục bừa (top-1 trên dev rơi 65% → 35%).
- "Cân bằng chặt" (trung bình đúng trọn và recall từ chối) chọn cấu hình từ chối gần hết (luôn từ chối đã được 0,5).

Theo tiêu chí: A + C (chỉ tên) bị loại (đúng trọn 36 < 38 câu của A); **bản cuối = A + B**. Trên test, A + C (chỉ tên) lại cao nhất (cân bằng 0,834, đúng trọn 66,1%), nhưng không được chọn lại sau khi thấy test; chênh lệch so với A cũng không có ý nghĩa thống kê (đúng trọn +8 / −4, p = 0,39).

Hai lỗi thiết kế tìm thấy trong lúc làm B (sửa trước lượt test, ghi lại cho minh bạch): (1) lượt lưới đầu "cứu" mọi câu luật từ chối khi điểm reranker chỉ cần trên ngưỡng thấp → thêm τ_rescue riêng; (2) khi thủ tục luật chọn không được reranker chấm, B vẫn "đổi" mà không so điểm → giữ quyết định của luật. Bộ mô phỏng lưới khớp lượt chạy thật của bản cuối trên dev ở mọi số; với B một mình, lượt chạy thật có top-1 cao hơn mô phỏng (21,8% so với 14,5%) vì thủ tục B đổi còn qua Policy (mô phỏng không có bước này). Bảng trên là số chạy thật.

## 5. Kết quả trên test (real_v2) — đầy đủ

Cả bộ 313 câu (Wilson 95% trong `eval/hard/results/test`, bảng đủ bằng `python eval/hard/report.py real_v2 real_v2_base real_v2_off real_v2_A real_v2_B real_v2_C real_v2_AC real_v2_ACname real_v2_final`):

| Cấu hình | Hành vi đúng | Cân bằng | Cân bằng 3 lớp | Trả lời | Hỏi lại | Từ chối | Top-1 | Top-3 | MRR@5 | Đúng trọn |
|---|---|---|---|---|---|---|---|---|---|---|
| base | 56,5% | 0,647 | 0,432 | 45/59 | 0/6 | 132/248 | 20/59 | 23/59 | 0,365* | 19/59 |
| off | 56,5% | 0,647 | 0,432 | 45/59 | 0/6 | 132/248 | 20/59 | 23/59 | 0,365 | 19/59 |
| A | 84,0% | 0,815 | 0,543 | 44/59 | 0/6 | 219/248 | 37/59 | 39/59 | 0,648 | 35/59 |
| B | 68,7% | 0,692 | 0,461 | 40/59 | 0/6 | 175/248 | 22/59 | 30/59 | 0,443 | 21/59 |
| C | 81,8% | 0,785 | 0,579 | 42/59 | 1/6 | 213/248 | 25/59 | 28/59 | 0,444 | 25/59 |
| A + C | 88,8% | 0,817 | 0,600 | 40/59 | 1/6 | 237/248 | 33/59 | 33/59 | 0,559 | 32/59 |
| A + C (chỉ tên) | 84,4% | 0,834 | 0,611 | 47/59 | 1/6 | 216/248 | 41/59 | 41/59 | 0,695 | 39/59 |
| **A + B (bản cuối)** | **84,4%** | **0,823** | 0,549 | 45/59 | 0/6 | 219/248 | 38/59 | 39/59 | 0,657 | **36/59** |

\* Tệp niêm phong của bản gốc (định dạng `run_pseudo.py`) không lưu danh sách ứng viên nên không tính được MRR; số MRR lấy từ lượt `off`, trùng bản gốc ở cả 313 câu.

Bộ sạch (302 câu, bỏ 11 câu gần trùng real_v1): bản gốc 0,650 → A 0,810 → bản cuối 0,818 (đúng trọn 32,8% → 58,6% → 60,3%): kết luận không đổi. Tầng random (102 câu): 0,512 → 0,859 → 0,859; tầng chude (211 câu): 0,688 → 0,801 → 0,812.

So cặp McNemar (chính xác, hai phía):

| So sánh | Hành vi đúng (+ / −, p) | Trả lời đúng trọn (+ / −, p) |
|---|---|---|
| base → A | +96 / −10, p ≈ 9·10⁻¹⁹ | +22 / −6, p = 0,004 |
| base → bản cuối | +96 / −9, p ≈ 2·10⁻¹⁹ | +23 / −6, p = 0,002 |
| base → B | +51 / −13, p ≈ 2·10⁻⁶ | +6 / −4, p = 0,75 |
| base → C | +106 / −27, p ≈ 3·10⁻¹² | +11 / −5, p = 0,21 |
| A → bản cuối | +1 / −0, p = 1 | +1 / −0, p = 1 |
| A → A + C | +25 / −10, p = 0,02 | +8 / −11, p = 0,65 |
| A → A + C (chỉ tên) | +4 / −3, p = 1 | +8 / −4, p = 0,39 |

Lỗi còn lại của bản cuối: 29/248 câu lẽ ra từ chối vẫn được trả lời (khớp tình cờ với tên thủ tục có thật); 12/59 câu answer bị từ chối, 2 bị hỏi lại; 9 câu trả lời sai thủ tục; 6 câu clarify không câu nào đúng (bộ chỉ có 6 câu, không kết luận).

**Đọc kết quả:**
- A (luật) là phần đóng góp chính và có ý nghĩa thống kê ở cả hai chỉ số.
- B một mình cải thiện hành vi (từ chối được nhiều câu hơn) nhưng gần như không cải thiện thủ tục đúng; trên nền A không thêm gì đáng kể. Giả thuyết (chưa kiểm riêng): reranker đa ngữ chấm kém cặp "thư kể dài tiếng Việt – tên thủ tục rất dài"; chấm theo đoạn câu hỏi đã đỡ hơn chấm cả thư trên dev (cân bằng theo bộ mô phỏng: 0,707 so với 0,675).
- C một mình tốt hơn B (cân bằng 0,785), nhưng model 4B gán nhầm nhiều câu hỏi thủ tục kể hoàn cảnh dài là "khiếu nại" / "hỏi luật" (trên dev chỉ ~65% câu answer được đọc là "thủ tục"). Ghép phân loại ý định của C với A làm mất câu trả lời đúng; phần "gọi tên thủ tục" của C thì có ích (A + C chỉ tên tốt nhất trên test, chưa có ý nghĩa thống kê). Đây là hướng đáng thử tiếp với bộ dev riêng mới.

## 6. Hồi quy (không làm hỏng tính năng cũ)

- **Golden thu-tuc** (1352 ca, hàng blind 518 ca là số chính thức), cùng DB bản 3, mọi cờ tắt → A bật (mặc định mới):

| | Hành vi đúng | Top-1 | Top-3 | MRR | Đúng trường | Nhiều thủ tục | Hỏi lại đúng | Từ chối đúng |
|---|---|---|---|---|---|---|---|---|
| Cờ tắt | 400/518 | 274/381 | 302/381 | 0,752 | 184/363 | 8/10 | 38/76 | 52/58 |
| A | 400/518 | 275/381 | 302/381 | 0,752 | 182/363 | 7/10 | 37/76 | 55/58 |

  Lượt golden đầu cho thấy A làm tụt 9 ca (bằng lái nước ngoài / của công an, quân đội bị coi là không có dữ liệu; "giải quyết tố cáo mất bao lâu" bị coi là khiếu nại; "có phải làm không" của câu ngắn bị coi là hỏi chính sách). Đã sửa bằng quy tắc chung trước khi đóng băng; ba sửa đó không đổi câu nào của dev. Còn lệch 1–2 ca nhỏ (đổi thẻ căn cước kèm điều chỉnh dữ liệu dân cư: hai thủ tục sát điểm → hỏi lại).
- **Test đơn vị** (`eval/run_tests.py`, 53 test S3 + S4 trên DB cố định, không mạng, không Ollama): 51 đạt, 1 hồi quy đã biết từ trước (`p23_input_test`: câu khai tử bị tách >1 ý, G4.8), 1 trượt là `test_fastpath` vì kết quả tự kiểm có thêm route "sql" sau khi bật SQL mặc định (test không có model → route tắt đúng như thiết kế); sửa dòng kỳ vọng đó rồi chạy lại: đạt.

## 7. System 4 — biên dịch lĩnh vực lúc nạp

**Mục tiêu 2**: thêm lĩnh vực mới bằng cách nạp tệp, không viết hệ thống mới. Trước đợt này, đường nhanh đã biên dịch lúc nạp (suy kiểu cột, gợi ý tên cột, bài tự kiểm bật / tắt từng loại câu) và tra cứu một dòng tốt, nhưng câu đếm / liệt kê / lớn nhất / tổng trên dữ liệu chưa thấy còn yếu (phép tính bằng code bị bài tự kiểm tắt trên cả ba bảng dev).

**Thay đổi** (`system4/server/fastpath/sqlroute.py`, `engine.py`, `selftest.py`):
1. Lúc nạp, mỗi bảng được dựng thành **một bảng SQLite phẳng có kiểu**: số đọc đúng cách viết của cột ("1.404.587", "6.700,39", "4.4"), cột chữ có bản bỏ dấu, cột chữ chứa năm ("11/1979", "Côn Đảo (1945)") có thêm cột năm, giá trị mẫu của cột liệt kê đưa vào mô tả cho model.
2. Lúc hỏi, câu cần tính trên nhiều dòng đi lộ trình SQL: model 4B viết **một câu SELECT trên đúng một bảng** (không JOIN, theo ADR-09), chạy trong hộp cát (bản sao trong bộ nhớ, `query_only`, authorizer chỉ cho đọc bảng này, LIMIT, giới hạn bước); **code viết câu trả lời** từ kết quả. Model không viết câu trả lời.
3. Chuẩn hoá câu SQL của model: lọc chữ trên bản bỏ dấu khớp nguyên âm tiết ("nhi" không khớp "nhiệt"); lọc ra 0 dòng thì thử khớp chuỗi con rồi thử trên cột tên; "= 'giá trị'" không có trong cột thì chuyển sang tìm chứa; bỏ danh từ chỉ loại dòng khỏi mẫu lọc.
4. **Bài tự kiểm lúc nạp có thêm route "sql"**: câu sinh từ kiểu cột của chính bảng, đáp án tính bằng Python; đạt ≥ 90% mới bật SQL cho bảng đó. `FASTPATH_SQL` bật mặc định; bảng không qua tự kiểm vẫn đi đường cũ. `FASTPATH_SQL_RAW` là mốc đo (SQL trên bảng thô, không biên dịch, không tự kiểm).
5. Sửa lỗi: bộ nhớ đệm engine đọc sai vị trí khoá khi xoá (nạp bộ thứ hai lúc đã có engine → "Lỗi khi xử lý").

**Dev** (3 bảng thật đã dùng từ 19/10: bệnh viện, trường đại học, di tích; 16 câu viết khi sửa): biên dịch 16/16, bảng thô 10/16; bài tự kiểm bật SQL cho cả 3 bảng. Ba đáp án dev sai do script của em (đọc "1.800" thành 1,8; tính cả "dự kiến đề cử UNESCO") đã sửa, ghi trong `sql_dev.py`.

**Bộ mù real_v3** (`python system4/eval/real_v3/report_v3.py v3b_rag v3b_old v3b_fp v3b_fpagg v3a_new v3a_sqlraw`):

| Cấu hình | Đạt (Wilson 95%) | Tra cứu | Không dấu | Đếm | Liệt kê | Lớn/nhỏ nhất | Tổng | Không có trong bảng | Hỏi tiếp | Trung vị s | Đường nhanh / SQL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| trước: rag | 32/52 = 62% (48–74) | 12/12 | 3/4 | 2/8 | 3/8 | 3/8 | 1/4 | 4/4 | 4/4 | 3,7 | 0 / 0 |
| trước: old (công cụ bảng) | 46/52 = 88% (77–95) | 12/12 | 2/4 | 7/8 | 8/8 | 6/8 | 3/4 | 4/4 | 4/4 | 6,2 | 0 / 0 |
| trước: fp (đường nhanh) | 44/52 = 85% (72–92) | 12/12 | 3/4 | 7/8 | 6/8 | 6/8 | 3/4 | 4/4 | 3/4 | 5,3 | 19 / 0 |
| trước: fp + phép tính code | 43/52 = 83% (70–91) | 12/12 | 3/4 | 5/8 | 7/8 | 6/8 | 3/4 | 4/4 | 3/4 | 0,1 | 30 / 0 |
| **sau: SQL đã biên dịch** | **44/52 = 85% (72–92)** | 11/12 | 3/4 | 7/8 | 8/8 | 5/8 | 4/4 | 3/4 | 3/4 | **0,8** | 46 / 29 |
| sau: SQL bảng thô (mốc) | 36/52 = 69% (56–80) | 11/12 | 3/4 | 4/8 | 8/8 | 1/8 | 3/4 | 3/4 | 3/4 | 0,7 | 47 / 30 |

Theo lĩnh vực (13 câu mỗi bộ): sân bay 12 → 8, thủy điện 11 → 12, tỉnh thành 10 → 12, vườn quốc gia 11 → 12 (fp → sau). So cặp: fp → sau +5 / −5 (p = 1); old → sau +4 / −6 (p = 0,75); bảng thô → biên dịch +8 / −0 (p = 0,008).

**Phân tích lỗi của engine mới** (sau khi mở kết quả; không sửa rồi chạy lại trên bộ mù):
- **Tệp hai sheet cùng đối tượng** (sân bay: sheet "Sân bay dân dụng" — năm xây dựng, đường băng, cấp — và sheet "Năng lực khai thác" — năng lực, sản lượng 2023, hãng; cùng 22 sân bay, tên ghi khác nhau giữa hai sheet): SQL chạy trên MỘT bảng nên câu hỏi cột của sheet kia ("sản lượng 2023", "năng lực khai thác") bị viết trên nhầm bảng (4 câu). Bài tự kiểm không bắt được vì mỗi bảng chỉ tự hỏi về cột của chính nó. Hướng sửa: lúc biên dịch ghép các sheet cùng khoá thành MỘT bảng rộng (đúng tinh thần "một bảng, không JOIN" mà trưởng nhóm đã duyệt).
- **Hỏi thuộc tính bảng không có** ("Sân bay Đồng Hới có bao nhiêu nhân viên?"): SQL đếm ra "1 sân bay" thay vì nói không có dữ liệu (1 câu).
- **Bỏ dấu làm trùng tên**: "Sông Lô" khớp cả "Sông Lò" (1 câu). Hướng sửa: khớp có dấu trước, bỏ dấu khi không ra dòng nào.
- Hai lỗi hiển thị **có từ trước** (cả fp cũng sai): năm 1904 hiện "1.904", diện tích 8053 ha hiện "8.053".

Kết luận cho bài báo: biên dịch lúc nạp + SQL do model 4B viết trên bảng phẳng có kiểu **giữ nguyên độ chính xác của đường cũ, nhanh hơn khoảng 7 lần**, và **bước biên dịch là phần quyết định** so với text-to-SQL thẳng trên bảng thô. Lợi rõ ở câu đếm / liệt kê / tổng; tệp nhiều sheet là việc cần làm tiếp. Không khẳng định engine mới "chính xác hơn" đường cũ: bộ 52 câu, khoảng tin cậy rộng.

## 8. Nhiệt độ máy (yêu cầu ≤ 70 °C)

Đo bằng cảm biến ACPI `\_TZ.TZ01` (PDH) và `nvidia-smi`; mọi lượt đo có ngắt nhiệt `eval/thermal.py` (tạm dừng khi ≥ ngưỡng, chạy tiếp khi nguội, nghỉ theo nhịp, giới hạn 2 lõi, ưu tiên thấp); log 15 s suốt phiên: `_test_tmp/thermal_session_2026-10-24*.csv`.

| Giai đoạn | Ngưỡng dừng / chạy tiếp | Lần đọc | CPU cao nhất | ≥ 70 °C |
|---|---|---|---|---|
| Sự cố 24/10 14:20–14:26 (lượt System 4 đầu tiên: runtime mới tự nạp dữ liệu thật + FLM bên trong server, ngoài tầm ngắt nhiệt) | – | 113 | **100 °C** (27 lần ≥ 90) | – |
| Cả phiên sau 14:30 (log 15 s) | – | 1710 | 88 °C | 151 (8,8%) |
| System 4 "trước" (model trả lời trên GPU) | 66 / 62 | 515 | 84 °C | 184 (36%) |
| System 4 "sau" | 62 / 55 | 93 | 76 °C | 18 (19%) |
| System 3 lượt test real_v2 (7 cấu hình) | 62 / 55 | 890 | 65 °C | 0 |

**Không đạt yêu cầu ≤ 70 °C** ở các lượt System 4 có model sinh câu trả lời: ngắt nhiệt chỉ chen được giữa hai câu, còn trong một câu model chạy liên tục 10–20 s. Sự cố 100 °C: đã dừng ngay, nguyên nhân (bootstrap của runtime mới) đã tắt trong bộ đo. Em không đổi thiết lập nguồn / giới hạn công suất của máy (thay đổi cấp hệ thống, chưa được phép). Nhiệt nền khi chỉ có ứng dụng của người dùng: ~55–62 °C.

## 9. Giới hạn và mối đe doạ tính hợp lệ

1. **Một người gán nhãn real_v2, và cũng là người sửa hệ thống** (Claude). Biện pháp: khoá trước khi sửa, không mở lại câu test, mọi luật viết từ dev. Chưa có người thứ hai gán nhãn / kiểm. Nên có lượt kiểm của người trước khi nộp bài.
2. **Luật và từ điển của A viết từ lỗi trên dev**: số dev phóng đại (cân bằng 0,902 dev → 0,815 test). Chỉ báo số test.
3. **Tiêu chí chọn ngưỡng / bản cuối đặt sau khi xem hai lượt lưới đầu trên dev** (không phải trên test), ghi trong code và mục 4 trước lượt test.
4. **11 câu gần trùng real_v1** trong real_v2: báo cả bộ sạch, kết luận không đổi.
5. **Câu clarify chỉ 6 câu**: không kết luận về hỏi lại. Quyết định D5 (hỏi tỉnh khi thủ tục có bản theo tỉnh) đôi khi lệch nhãn "answer" (2 câu test).
6. **real_v3 sinh bằng khuôn** từ 4 bảng (52 câu, khoảng tin cậy rộng); chấm bằng luật bao hàm (câu trả lời chứa chữ / số cần có thì đạt): câu trả lời dài dòng vẫn có thể đạt.
7. **Lượt "rag" của System 4 chạy lại một lần**: lượt đầu server chết khi đang nạp bảng 372 dòng, **trước khi trả lời câu nào** (log `v3b_rag.crash1.log`). Máy lúc đó còn < 1 GB RAM trống.
8. Lượt "sau" dùng ngưỡng nhiệt chặt hơn lượt "trước" (62/55 so với 66/62): chỉ đổi thời gian nghỉ GIỮA các câu; thời gian trả lời đo trong từng câu.
9. **Ba tệp chưa commit của trưởng nhóm** (`system4/server/db.py`, `system4/eval/real_domains/seed.py`, `system4/tests/test_hard_extra.py`) có trong thư mục làm việc ở mọi lượt đo (giống nhau trước / sau); em không commit chúng.
10. Server đo của System 4 lúc chạy "trước" có gọi **một lần API chính thức `/site/settings` của abi.com.vn** (bộ lập lịch đồng bộ ABI, không có khoá → 401; không phải API AI, không tốn token). Đã tắt (`S4_ABI_SYNC=0`) trong bộ đo cho lượt "sau".
11. Máy đo khác máy của các số trước (RTX 4050 so với GTX 1660 SUPER): không so thời gian với báo cáo cũ.
12. Bản cuối A + B cần thêm hai model trên GPU mà chỉ hơn A một câu: **mặc định khi chạy vẫn là A** (`S3_SEMANTIC=0`); bật B bằng cờ khi muốn đúng cấu hình bài báo.

## 10. Checkpoint và cách lùi lại

| Commit | Nội dung |
|---|---|
| `a82d970` | Rút 348 câu real_v2 (chưa nhãn) |
| `7e78438` | Khoá nhãn real_v2 và bộ mù real_v3 trước mọi thay đổi code |
| `b7010d1` | Ba phương án System 3, lộ trình SQL System 4, công cụ đo; đóng băng trước lượt test |
| checkpoint 4 | Kết quả test, báo cáo này |

Lùi từng phần không cần revert: System 3 tắt từng mảnh của A bằng `S3_LETTER_STRIP=0`, `S3_LEXICON2=0`, `S3_WEAK_NAME=0`, `S3_SCOPE_GATE=0` (hoặc chỉ `S3_SCOPE_A6=0`), `S3_FOCUS=0`, `S3_ORG_DEFAULT=0`; B và C mặc định tắt. System 4: ⚙ Cài đặt → tắt "Đường nhanh: đếm / liệt kê / lớn nhất / tổng bằng SQL" (`FASTPATH_SQL`) là quay về đường nhanh cũ.

## 11. Tái tạo

```bash
# System 3 (máy bất kỳ có DB bản 3 data/runtime/knowledge/3-423eff02f8.db; B cần Ollama bge-m3 + system4/models/bge-reranker-v2-m3; C cần qwen3:4b-instruct)
bash eval/hard/final_runs.sh               # 7 cấu hình trên real_v2, mỗi cấu hình một lần
python eval/hard/report.py real_v2 real_v2_base real_v2_off real_v2_A real_v2_B real_v2_C real_v2_AC real_v2_ACname real_v2_final
python run_server.py eval/hard/sem_grid.py grid --name semAseg     # lưới ngưỡng trên dev (từ điểm đã chấm)
bash eval/hard/regress.sh                  # golden + test đơn vị
# System 4
bash system4/eval/real_v3/run_before.sh && bash system4/eval/real_v3/run_after.sh
python system4/eval/real_v3/report_v3.py v3b_rag v3b_old v3b_fp v3b_fpagg v3a_new v3a_sqlraw --pair v3b_fp v3a_new
python system4/eval/real_v3/sql_dev.py [--raw]    # dev của lộ trình SQL
```

Kết quả gốc (đã commit): `eval/hard/results/{dev,test,regress}/`, `system4/eval/real_v3/results/` (6 cấu hình, stamp trước / sau, log lượt rag hỏng).

# III/ Metrics

## 3.1 Quy trình eval bằng câu hỏi thật

Làm trong 3 ngày, cho cả hai hệ thống: thu câu hỏi, lọc, gán nhãn, khoá, chạy đúng một lần rồi chấm. Quy tắc lọc và cách chấm viết trước khi chạy, không chọn câu theo kết quả của hệ thống.

| Bước | System 3 (Strict): câu hỏi của người dân | System 4 (Friendly): câu thật và câu viết trên Wikipedia |
|---|---|---|
| **1. Thu thập** | Hỏi đáp Cổng dịch vụ công trên Hugging Face: Bình Định 1.074 + Bộ Công an 809 = **1.883 câu thô** | Du lịch: ViQuAD2.0, bài Phong Nha (75 câu). Y tế: hỏi đáp bác sĩ (85 câu). Bảng: 3 bảng Wikipedia (40 câu) |
| **2. Lọc và làm sạch** | Bỏ 176 câu nhóm từng dùng để chọn luật (không còn mù). Bỏ 65 câu trùng, 60 câu quá ngắn, 92 câu chỉ là lời chào. Còn **1.490 câu**. Che CCCD, SĐT, email, tên người | Y tế: bỏ câu hệ thống đã nạp, câu dưới 30 hoặc trên 700 ký tự, câu trùng. Che CCCD, SĐT, email, tên người |
| **3. Lấy mẫu** | Lấy **300 câu** theo seed cố định: 120 ngẫu nhiên + 180 theo chủ đề cấp xã (160 Bình Định, 140 Bộ Công an) | Giữ **200 câu**: 75 du lịch + 85 y tế + 40 bảng |
| **4. Gán nhãn** | Hai lượt gán độc lập: trả lời / hỏi lại / từ chối. Thống nhất 31 câu lệch nhau; κ = 0,753. Bỏ 18 câu cụt, thiếu ngữ cảnh. Còn **282 câu** | Hai lượt gán độc lập: đáp án, từ chối, hỏi lại, khẩn cấp, cần ảnh, bỏ câu. Thống nhất các câu lệch. Bỏ 22 câu du lịch không đáp án và 1 câu bảng. Còn **177 câu** |
| **5. Khoá và chạy** | Khoá bộ câu và nhãn bằng sha256 (LOCK.md). Chạy đúng một lần, không chỉnh theo kết quả. Chế độ luật (tắt LLM), dữ liệu bản 3 (1.517 thủ tục) | Khoá bằng sha256, chạy đúng một lần. Cấu hình inst02 (qwen3:4b-instruct), GTX 1660 SUPER 6 GB. Runtime riêng, 3 lĩnh vực nạp từ Wikipedia |
| **6. Chấm và đánh giá** | So cách xử lý của hệ thống với nhãn: top-1, top-3, MRR. Khoảng tin cậy Wilson 95%, tách theo tầng lấy mẫu. Báo cả chỗ sai: ma trận trả lời / hỏi lại / từ chối | Chấm bằng luật so khớp chữ, viết trước khi chạy. Chấm nghiêm và chấm nới; không nhờ AI chấm. Khoảng tin cậy Wilson 95%; Y tế theo luật khuyên khám |

---

## 3.2 System 3 (Strict): bộ mù và câu hỏi thật

Bộ mù: 518 câu nhóm soạn, hệ thống chưa từng gặp khi chỉnh; dữ liệu bản 3 (1.517 thủ tục), chế độ luật, tắt LLM. Số là của lần eval đầy đủ #2 và #3 (18/10), hai lần cho kết quả giống hệt. Câu hỏi thật: 282 câu của người dân, chạy một lần.

| Chỉ số | Bộ mù (nhóm soạn, 518 câu) | Câu hỏi thật (282 câu) |
|---|---|---|
| Hành vi đúng | 77% | **56,0%** |
| Top-1 (tìm đúng thủ tục) | 72% | **12,7%** |
| Từ chối đúng | 90% | **52,7%** |

| Chỉ số | Bộ mù (nhóm soạn) | Câu hỏi thật | Vì sao chênh |
|---|---|---|---|
| Có **tìm đúng thủ tục** không (top-1 / top-3)? | **72%** (274/381) / 79%; MRR 0,752 | **12,7%** (7/55) / 21,8%; MRR 0,227 | Câu nhóm soạn nêu tên thủ tục; câu thật kể hoàn cảnh, ít nhắc tên. Chỉ 55 câu có đáp án (CI 6,3–24,0%) |
| Có **phản ứng đúng kiểu** không (trả lời, hỏi lại, từ chối)? | **77%** (400/518) | **56,0%** (158/282), CI 50,2–61,7% | Cơ cấu câu khác: câu thật 78% là ngoài phạm vi (220/282), bộ mù chỉ 11% (58/518) |
| Gặp câu mơ hồ thì có **hỏi lại** không? | **50%** (38/76) | 14,3% (1/7), CI 2,6–51,3% | Vẫn là điểm yếu nhất ở cả hai bộ; câu thật chỉ có 7 câu mơ hồ |
| Gặp câu **ngoài phạm vi** thì có từ chối không? | **90%** (52/58) | 52,7% (116/220), CI 46,1–59,2% | Câu thật hỏi luật, xử phạt, khiếu nại, tra hồ sơ; hệ thống hay trả lời thay vì từ chối (101/220) |
| **Liệt kê / đếm** thủ tục có đúng lĩnh vực không? | **98%** (bộ khuôn 40 câu); 93% (42/45, bộ đo riêng) | — | Chỉ chạy khi có LLM; lần đo câu thật chạy chế độ luật |
| Lệ phí có đọc đúng không? | **Đã sửa** khi dựng DB: 4/150 câu mẫu đổi đúng ý (10 đồng thành 10 USD) | — | Xong; có test hồi quy |
| Có hỏi tỉnh khi thủ tục có bản riêng của tỉnh không? | **Có**: mẫu 20 câu bản 3 đúng 20/20 | — | Mới; nhãn bộ mù viết trước nên 9 ca bị tính sai (đã giải thích kèm số) |
| Có **chặn câu cố ý lừa** hệ thống không? | Strict 11/11 | — | Không có câu cố ý lừa trong bộ câu thật |
| Có **che CCCD/SĐT** không? | 12/12 phép thử, **che ngay lúc ghi vào cả 2 DB** (tin nhắn, tiêu đề, tóm tắt, bộ nhớ, trace, log đánh giá) | Che trước khi lưu bộ câu | Không che cả câu trả lời (dữ liệu Cổng có 1.852 mã dịch vụ) |
| Câu cần AI viết mất bao lâu khi **10 người dùng cùng lúc**? | **p50 2,9 s / p95 4,0 s** (10 người giả, nghỉ 20–40 s) | — | Đạt mục tiêu (dưới 8 s) nhờ bộ lập lịch GPU chung |
| Câu chỉ dùng luật mất bao lâu khi **10 người dùng cùng lúc**? | **p95 1,18 s** (10 người); một người dưới 0,2 s | — | Chưa đạt mục tiêu 0,5 s (CPU dùng chung với Ollama + reranker) |

*Dấu "—" nghĩa là bộ đó không đo chỉ số này, không phải bằng 0 và không phải lỗi. Đợt eval câu thật chỉ đo chất lượng trả lời; các chỉ số khác (lệ phí, tốc độ khi nhiều người dùng, chặn chèn lệnh…) chỉ có ở bộ mù hoặc không có trong bộ câu thật.*

---

## 3.3 System 4 (Friendly): bộ mù và câu hỏi thật

Đường nhanh đo kiểu "cũ so với mới" bằng model thật trên cùng một runtime sạch. Bộ du lịch và bộ cửa hàng là hai bộ mù soạn và commit trước khi sửa; dữ liệu của chúng là dữ liệu giả để đo, không dùng khi demo. Câu hỏi thật: 177 câu, chạy một lần.

| Chỉ số | Bộ mù (nhóm soạn) | Câu hỏi thật | Vì sao chênh |
|---|---|---|---|
| Có **trả lời đúng** không? | **96%** (75/78, bài thi nhóm soạn) | Du lịch văn bản **92,0%** (46/50); bảng **65,4%** (17/26) | Bảng thấp hơn vì câu liệt kê hay thiếu dòng hoặc nhầm cột |
| **Tra cứu một dòng** trên dữ liệu lạ (bộ mù cửa hàng) | **14/14 đúng**, 0,09 s (không gọi AI); đường cũ 3–7 s | — | Hơn đường cũ cả đúng lẫn nhanh |
| **Đếm / liệt kê** bằng đường nhanh trên dữ liệu lạ | 1/6, nên **tắt mặc định** (đi đường cũ) | — | Chưa dùng được; chờ sửa lỗi còn sót và đo trên bộ mù thứ ba |
| Tổng trên bộ mù, đường cũ so với mới | 27/32 so với 25/32 (ước tính 29/32 nếu tắt đếm: suy ra, chưa đo) | — | Chưa hơn trên tổng; hơn ở tra cứu và tốc độ |
| Tốc độ cả câu (trung vị, có GPU) | 3,3–11,4 s tuỳ loại câu; đường nhanh 0,09 s | Câu đầu 13,0 s, cả câu **19,4 s** (p90 32,4 s) | GTX 1660 SUPER 6 GB phải chia GPU cho reranker; câu thật dài hơn bài thi cũ |
| **Chờ hàng GPU** khi 10 người dùng cùng lúc | Chữ đầu p50 6,2 / p95 15,2 s; cả câu p50 11,2 / p95 21,3 s; chờ hàng p95 13,6 s | — | Trên mục tiêu 10 s; trưởng nhóm chấp nhận khoảng 15 s cho thí điểm |
| Gặp **câu cố ý lừa** (chèn lệnh) | **11/11 bị chặn** (trước đó 4/11) | — | Xong (lớp chính sách chung) |
| Phải từ chối khi dữ liệu không có | — | 71,4% (10/14) | Hay hỏi lại thừa ở câu không mơ hồ |
| Y tế: khuyên khám / câu nguy hiểm khuyên cấp cứu | — | 94,1% (80/85) / **4/10** | Chỉ có 10 câu nguy hiểm (CI 16,8–68,7%); cần sửa trước |

*Dấu "—" nghĩa là bộ đó không đo chỉ số này, không phải bằng 0 và không phải lỗi. Đợt eval câu thật chỉ đo chất lượng trả lời; các chỉ số khác (lệ phí, tốc độ khi nhiều người dùng, chặn chèn lệnh…) chỉ có ở bộ mù hoặc không có trong bộ câu thật.*

---


## 3.4 Câu thật, Strict: kết quả chi tiết (282 câu)

Chạy bằng chế độ luật (tắt LLM), không cần GPU, trên dữ liệu thủ tục bản 3 (1.517 thủ tục). Trong 282 câu có 55 câu cần trả lời, 7 câu cần hỏi lại và 220 câu nằm ngoài phạm vi, hệ thống phải từ chối.

| Chỉ số | Kết quả | Khoảng tin cậy 95% |
|---|---|---|
| Xử lý đúng cách (282 câu) | **158/282 = 56,0%** | 50,2–61,7% |
| Top-1 (55 câu có đáp án) | **7/55 = 12,7%** | 6,3–24,0% |
| Top-3 | 12/55 = 21,8% | 12,9–34,4% |
| MRR (tối đa 6 ứng viên) | 0,227 | không áp dụng |

MRR là trung bình của 1/hạng, không phải tỷ lệ đúng/sai nên không có khoảng tin cậy Wilson.

| Trả lời khi câu có đáp án | 41/55 = 74,5% | 61,7–84,2% |
| Hỏi lại khi câu mơ hồ | 1/7 = 14,3% | 2,6–51,3% |
| Từ chối khi câu ngoài phạm vi | 116/220 = 52,7% | 46,1–59,2% |

**Theo tầng lấy mẫu**

| Tầng | Số câu | Xử lý đúng | Câu có đáp án | Top-1 | Top-3 |
|---|---|---|---|---|---|
| Ngẫu nhiên | 111 | 63/111 = 56,8% (47,5–65,6%) | 13 | 2/13 (4,3–42,2%) | 3/13 (8,2–50,3%) |
| Theo chủ đề cấp xã | 171 | 95/171 = 55,6% (48,1–62,8%) | 42 | 5/42 (5,2–25,0%) | 9/42 (11,7–35,9%) |

**Hệ thống làm gì với từng loại câu**

| Đáng lẽ phải | Trả lời | Hỏi lại | Từ chối |
|---|---|---|---|
| Trả lời (55 câu) | 41 | 1 | 13 |
| Hỏi lại (7 câu) | 3 | 1 | 3 |
| Từ chối (220 câu) | **101** | 3 | 116 |

**Chỗ sai chính**

- Điểm yếu lớn nhất: **101/220** câu ngoài phạm vi (luật, xử phạt, khiếu nại, tra tình trạng hồ sơ) vẫn bị trả lời thay vì từ chối.
- Thủ tục **1.115406** (xét hưởng chế độ trợ cấp đối tượng Công an nhân dân) bị chọn nhầm ở 26 câu ngoài phạm vi và 10 câu có đáp án, vì cụm "Công an nhân dân" xuất hiện trong nhiều câu gửi Bộ Công an.
- Hầu như không hỏi lại được (1/7). Câu của người dân dài và kể hoàn cảnh, khác hẳn bộ nhóm tự soạn (top-1 72%, xử lý đúng 77%).

---

## 3.5 Câu thật, Friendly: kết quả chi tiết (177 câu)

Chạy cấu hình **inst02** (qwen3:4b-instruct, nhiệt độ 0,2) trên máy GTX 1660 SUPER 6 GB, với 3 lĩnh vực nạp từ Wikipedia (10/2026). Cách chấm là so khớp chữ theo luật viết sẵn trước khi chạy, không nhờ AI chấm. Cả 177 câu chạy xong, không có lỗi.

| Nhóm | Số câu | Kết quả | Khoảng tin cậy 95% |
|---|---|---|---|
| Du lịch văn bản, có đáp án (chấm nghiêm) | 50 | **46/50 = 92,0%** | 81,2–96,8% |
| Du lịch văn bản (chấm nới: một đáp án có từ 70% số từ) | 50 | 47/50 = 94,0% | 83,8–97,9% |
| Phần bảng, có đáp án | 26 | **17/26 = 65,4%** | 46,2–80,6% |
| Phải từ chối (dữ liệu không có) | 14 | 10/14 = 71,4% | 45,4–88,3% |
| Phải hỏi lại (mơ hồ) | 2 | 0/2 | 0,0–65,8% |
| Y tế: khuyên khám / đến cơ sở y tế | 85 | 80/85 = 94,1% | 87,0–97,5% |
| Y tế: câu nguy hiểm (urgent) khuyên cấp cứu / đi ngay | 10 | **4/10 = 40,0%** | 16,8–68,7% |
| Y tế: câu tham chiếu ảnh nói không xem được | 2 | 1/2 | 9,5–90,5% |
| Y tế: có liều thuốc cụ thể (guardrail cấm) | 85 | 2/85 = 2,4% | 0,6–8,2% |
| Y tế: khẳng định chẩn đoán | 85 | 1/85 = 1,2% | 0,2–6,4% |

**Thời gian (177 câu)**

Chữ đầu tiên hiện ra sau khoảng **13,0 giây** (trung vị). Cả câu trả lời xong sau khoảng **19,4 giây**, 9/10 câu dưới 32,4 giây, câu chậm nhất 51,7 giây. Chậm vì máy 6 GB phải chia GPU cho model, bge-m3 và reranker, và câu Du lịch văn bản phải đọc đoạn dài.

**Chỗ sai chính**

- **Hay hỏi lại thừa:** 6 câu bị trả lời "Trong dữ liệu có 2 mục cùng khớp…" dù câu không mơ hồ, hoặc lẽ ra phải từ chối vì bảng không có cột đó. Đây là lý do chính làm phần từ chối chưa cao.
- **Y tế khẩn cấp:** chỉ 4/10 câu nguy hiểm được khuyên đi cấp cứu. Câu về người già hôn mê do ngộ độc khí CO không có lời khuyên đi khám. Có 5 câu y tế không khuyên đi khám và 2 câu nêu liều thuốc cụ thể.
- **Câu liệt kê** (thành viên đại học, di tích UNESCO, di tích năm 2012): bảng trả về thiếu một phần dòng, và một câu hỏi "năm nào" lấy nhầm cột (ra "Đợt 2" thay vì 2012).
- Cách chấm nghiêm đôi khi tính sai câu đúng ý (trả lời "25 đến 30 độ" nhưng đáp án ghi "25-30 độ"), nên số chấm nới sát thực tế hơn.

---

## 3.6 Câu thật: dữ liệu và lý do lọc bỏ câu

Câu nào bị loại là do quy tắc đặt ra từ trước, không phải do hệ thống trả lời đúng hay sai. Câu hỏi giữ nguyên chữ của người viết, kể cả lỗi chính tả; nhóm chỉ gộp khoảng trắng và che CCCD, số điện thoại, email, tên người.

**Strict: từ kho thô đến 282 câu**

| Bước | Số câu | Lý do |
|---|---|---|
| Kho thô (hỏi đáp Cổng dịch vụ công Bình Định 1.074, Bộ Công an 809) | 1.883 | Hai tập câu hỏi của người dân trên Hugging Face; giấy phép ghi "không rõ" nên chỉ dùng để đánh giá nội bộ |
| Loại: đã dùng để chọn luật trước đây | −176 | Nhóm đã xem các câu này khi chọn luật hỏi lại nên không còn là câu "mù" |
| Loại: trùng | −65 | Cùng câu (so sau khi bỏ dấu, hạ chữ thường) |
| Loại: quá ngắn | −60 | Dưới 4 chữ, không đủ nghĩa |
| Loại: chỉ là lời chào | −92 | Dòng "Kính gửi…", "Xin chào…" bị cắt từ tiêu đề |
| Pool sạch | 1.490 | |
| Lấy mẫu (SEED cố định) | 300 | 120 ngẫu nhiên + 180 theo chủ đề cấp xã (từ khoá lấy từ tên nhóm thủ tục, viết trước); 160 Bình Định, 140 Bộ Công an; bỏ tập Zalo vì là truy hồi văn bản luật |
| Loại khi gán nhãn: 18 câu skip | −18 | Câu cụt hoặc không có câu hỏi (ví dụ chỉ lời chào "Kính thưa Giám đốc sở…", "Tôi vừa thay đổi CMND 9 số sang CCCD 12 số."), thiếu ngữ cảnh |
| **Bộ để chạy** | **282** | 55 câu cần trả lời, 7 cần hỏi lại, 220 cần từ chối |

**Friendly: từ nguồn đến 177 câu**

| Phần | Thu | Chấm | Lý do bỏ câu |
|---|---|---|---|
| Du lịch văn bản (ViQuAD2.0, bài Phong Nha) | 75 (50 có đáp án + 25 không có) | **53** | Bỏ 22 câu "không có đáp án" của ViQuAD vì bài Wikipedia hiện tại (bản 2026) **đã có đáp án**, hoặc câu hỏi có tiền đề lệch (ví dụ "kỳ họp lần thứ 27", "sông Chay"). Giữ lại 3 câu thật sự không có đáp án |
| Y tế (hỏi đáp bác sĩ) | 85 | **85** | Đã loại trước các câu hệ thống đã nạp (300 câu), câu dưới 30 hoặc trên 700 ký tự và câu trùng; không có đáp án chuẩn nên chỉ đo cách xử lý |
| Phần bảng (3 bảng Wikipedia) | 40 | **39** | Bỏ 1 câu vì "lịch sử cách mạng" không phải một hạng mục trong bảng |
| Tổng | 200 | **177** | Bỏ 23 câu (22 + 1) |

**Độ tin cậy của nhãn**

| Chỉ số | Kết quả |
|---|---|
| Strict: độ đồng thuận Cohen's κ | **0,753**; hai lượt gán nhãn độc lập cho cùng kết luận ở 258/281 câu (91,8%) và cùng mã thủ tục ở 36/39 câu (92,3%). 31 câu lệch nhau đã được thống nhất lại |
| Strict: lỗi đã bắt được | Lượt gán thứ nhất tra sót thủ tục ở 9 câu (ví dụ xác nhận số CMND), lượt thứ hai tìm ra |
| Friendly: khớp | bỏ câu 94%, từ chối 95%, hỏi lại 100%, câu khẩn cấp và câu cần ảnh 100%, đáp án 176/176 (coi các cách viết khác nhau là một); 12 câu lệch về bỏ câu đã được thống nhất lại |

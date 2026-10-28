# Ràng buộc cho bài báo 1 (System 3, nộp VJCS)

Tệp này là **bộ ràng buộc chuẩn** cho người viết và agent phản biện (bước f). Mỗi mục có nguồn và trạng thái.

- **[ĐÃ XÁC NHẬN]**: đã đọc trực tiếp nguồn gốc.
- **[QUYẾT ĐỊNH NHÓM]**: trưởng nhóm đã duyệt (25/10/2026, kể cả phiếu Task_3).

Nguồn của mục A là các PDF trang chính thức và gói template do trưởng nhóm lưu ngày 25/10/2026 trong `07_paper_draft/sources/`.

Ngày lập: 25/10/2026.

---

## A. Tạp chí: Vietnam Journal of Computer Science (VJCS) [ĐÃ XÁC NHẬN]

| # | Ràng buộc | Nguồn trong `sources/` |
|---|---|---|
| A1 | World Scientific, hợp tác với ĐH Nguyễn Tất Thành. Truy cập mở kim cương theo giấy phép CC BY, **không thu phí**. Chỉ số 2025: IF 0,8; CiteScore 4,0; SJR 0,308. Có trong Scopus, ESCI, Ei Compendex. **Tỷ lệ nhận 5%**, 4 số mỗi năm | `Vietnam Journal of Computer Science.pdf` |
| A2 | Phạm vi: tạp chí chào đón "advances in the use of computer science methods … for solving tasks in management, industry, engineering, **administration** … and also **evaluations of existing intelligent systems and tools, emphasizing comparative studies** and user experiences". Bài 1 khớp đúng chỗ này: hệ thống hành chính, so sánh có kiểm soát | như trên |
| A3 | Nộp qua Editorial Manager (editorialmanager.com/wspc-vjcs). Khi nộp phải chọn mục (section) của bài. **Tác giả liên hệ bắt buộc có ORCID**; khuyến khích mọi tác giả có ORCID | `Vietnam Journal of Computer Science _.pdf`, `Login.pdf` |
| A4 | Trang đầu gồm tên bài, tóm tắt **≤ 150 từ** (template ghi < 200, theo hướng dẫn nộp là 150), **≤ 6 từ khoá** (cách nhau bằng dấu chấm phẩy, như các bài mẫu). Giới hạn 35 trang | như trên |
| A5 | **Phản biện single-blind**, ít nhất 2 người. Ban biên tập lọc phạm vi trước, ngoài phạm vi thì loại ngay | như trên, `Author's Responsibilities.pdf` |
| A6 | **Không được nộp song song** ở tạp chí khác. Bài được kiểm đạo văn và tự đạo văn bằng CrossCheck. Bài 1 và bài 2 không được trùng nội dung đáng kể | `Ethical Policy for journals.pdf`, `Peer Review Policy.pdf` |
| A7 | Template LaTeX2e: `ws-vjcs.cls`, `ws-vjcs.bst` (BibTeX), bản mẫu `ws-vjcs.tex` và `ws-vjcs_bib.tex`. Cũng có template Word `ws-vjcs.docx`. Chữ 10 pt Times; tên bài tối đa 3 dòng; running head ≤ 8 chữ; tiêu đề lớn in đậm; bảng có chú thích ở trên, hình có chú thích ở dưới (8 pt); chú thích cuối trang đánh chữ a, b… | `vjcs-2e.zip`, `vjcs-doc.zip` |
| A8 | Tiếng Anh, **chính tả Mỹ**. Bài viết tiếng Anh kém có thể bị trả về hoặc loại chỉ vì lý do đó | `ws-vjcs.pdf`, `Author's Responsibilities.pdf` |
| A9 | Tài liệu tham khảo **đánh số theo thứ tự xuất hiện**, dạng "1. C. M. Wang, J. N. Reddy and K. H. Lee, Title, …". Acknowledgments đứng trước References; Appendix đứng sau References. Các bài mẫu có mục ORCID trước References | template, `Example 1–3.pdf` |
| A10 | **Khai báo AI**: có mục riêng tên "**Declaration of AI Use**", đặt ngay trước Acknowledgements hoặc References. Ghi tên công cụ kèm phiên bản, mục đích và mức độ dùng. AI không được đứng tên tác giả. Tác giả phải tự kiểm mọi thông tin, tài liệu tham khảo, trích dẫn, dữ liệu và code do AI tạo. Phải khai báo khi dùng AI để **tạo hoặc sửa đáng kể văn bản, code, hoặc để thu thập hay phân tích dữ liệu** | `World Scientific Policy on AI and Authorship.pdf` |
| A11 | Phải khai báo xung đột lợi ích. Khuyến khích có Data availability statement. Liệt kê đầy đủ đơn vị của mọi tác giả. Người có đóng góp mà không đứng tên thì ghi ở Acknowledgements | `Ethical Policy for journals.pdf` |
| A12 | Nghiên cứu có dùng dữ liệu của người phải nêu: không có thông tin nhận diện được người (tên, ảnh…). Có phê duyệt đạo đức thì ghi, hoặc nói rõ vì sao không cần. Ở đây là dữ liệu công khai đã che thông tin cá nhân, không thu thập dữ liệu từ người tham gia | như trên |
| A13 | Có thể đề xuất tối đa 5 người phản biện (tuỳ chọn) | `Author's Responsibilities.pdf` |

Ba bài mẫu dài 18–33 trang. Trưởng nhóm muốn bài 1 **khoảng 10 trang trở lại** (D10). Vẫn nằm trong giới hạn 35 trang.

---

## B. Khuôn của repo môn học (NCKH-LongT/chatbot-thutuc-g7, README nhánh main)

[ĐÃ XÁC NHẬN], đọc ngày 25/10/2026.

| # | Ràng buộc |
|---|---|
| B1 | Giữ cấu trúc thư mục 01_topic_proposal … 08_final_submission và weekly_reports. Chỉ thư mục `Code/` được sửa tự do [QUYẾT ĐỊNH NHÓM] |
| B2 | Tối thiểu: **5 bài liên quan trực tiếp**, **3 bài về model hay phương pháp AI**, **2 bài về lĩnh vực ứng dụng** |
| B3 | Mỗi bài tham khảo có một tệp tóm tắt theo mẫu: Citation (tên, tác giả, năm, nguồn, DOI/Link), Problem, Method, Dataset, Evaluation, Results, Limitations, Relevance to our topic, Possible improvement |
| B4 | Có literature review matrix; problem statement; research gap; **2–4 câu hỏi nghiên cứu** |
| B5 | Có kiến trúc hệ thống, mô tả model AI (là gì, vì sao chọn, lấy từ đâu, input, output, cách tích hợp), **baseline**, dataset, metric |
| B6 | Cấu trúc bài: Title, Abstract, Keywords, 1 Introduction, 2 Related Work, 3 Proposed System / Methodology, 4 Experimental Setup, 5 Results, 6 Discussion, 7 Conclusion and Future Work, References. Mỗi phần viết riêng một tệp trong 07_paper_draft rồi ghép lại |
| B7 | Checklist trước khi nộp (README mục 16): đủ các mục trên, có discussion, limitation, future work, references đúng định dạng, có lịch sử commit, có weekly reports |
| B8 | Bài phải trả lời 9 câu của README mục 17: vấn đề thực tế; vì sao cần AI; model có phù hợp không; tích hợp thế nào; có dữ liệu đánh giá không; có baseline không; có tốt hơn cách cũ không; hạn chế; hướng mở rộng |
| B9 | Câu định vị (README mục 18): bài **không đề xuất model mới**, mà khảo sát cách tích hợp model có sẵn vào hệ thống của một lĩnh vực và đánh giá hiệu quả trong bối cảnh thực tế |
| B10 | Commit message theo dạng `<type>: <nội dung>`, với type ∈ docs, topic, review, method, experiment, result, fix, figure |

Ghi chú: khung tuần của môn (16 tuần) dành cho người mới bắt đầu, nên nhóm không cần đi lại từng tuần. Chỉ cần đủ tệp và nội dung.

---

## C. Luật viết báo cơ bản

Tổng hợp từ chuẩn chung của bài báo thực nghiệm ngành Khoa học máy tính. Áp dụng cho mọi câu trong bài.

### C1. Khẳng định và bằng chứng
1. Mỗi khẳng định phải dựa vào một trong hai thứ:
   - **số đo của chính nhóm**, kèm cỡ mẫu và phép kiểm;
   - **một trích dẫn đã đọc**: có PDF trong `02_related_work/`, hoặc đã mở trang gốc.
2. Không khẳng định tuyệt đối khi không chứng minh được. Cấm các chữ như "eliminates", "zero hallucination", "guarantees", "state-of-the-art", "enterprise-grade", "production-ready". Dùng "reduces … from X to Y on N questions".
3. Không lấy số của bài khác khi chưa đọc đúng bảng hay đoạn chứa số đó. Lấy số thì ghi kèm số bảng hoặc số trang của bài gốc vào tệp tóm tắt.
4. Không gán cho hệ thống một thành phần mà code không có. Bản draft cũ đã ghi GPTCache, Redis, RouteLLM, vLLM, MCP, Nougat, trong khi code không có cái nào.

### C2. Số liệu và thống kê
1. Mọi tỷ lệ phải ghi dạng **k/n (x%)**, kèm **khoảng tin cậy Wilson 95%** ở bảng kết quả chính.
2. So hai cấu hình chạy trên cùng bộ câu thì dùng **McNemar chính xác hai phía**, ghi số câu +/− và p.
3. Báo cả **balanced accuracy** lẫn **end-to-end** (trả lời đúng thủ tục). Balanced accuracy không phạt câu trả lời sai thủ tục, nên báo riêng nó là thiếu.
4. Mỗi cấu hình **chạy một lần** trên code đã đóng băng. Ghi phiên bản model, mức lượng tử hoá, nhiệt độ sinh, phần cứng, commit.
5. Có độ đồng thuận nhãn: **Cohen's κ** trên mẫu gán lại độc lập, kèm khoảng tin cậy. Nêu rõ ai gán nhãn.

### C3. So sánh công bằng
1. Không đặt cạnh nhau, như thể so được, các số đo trên bộ dữ liệu khác nhau. Bảng so sánh với bài khác chỉ được mô tả nhiệm vụ, dữ liệu và metric (bảng định tính), không được xếp hạng.
2. Baseline phải chạy trên **cùng bộ câu, cùng giao thức** với hệ thống của nhóm.
3. Báo **mọi** cấu hình đã chạy trên test, kể cả cấu hình thua (B một mình, C một mình, A + C).

### C4. Giao thức dev/test
1. **Chọn cấu hình chỉ trên dev** (real_v1), theo tiêu chí viết trước. Không chọn lại theo test. A + C (chỉ tên) cao nhất trên test nhưng đã bị loại trên dev, nên chỉ được báo là phân tích phụ.
2. Nêu rõ thứ tự: rút câu → gán nhãn → khoá (sha256 + commit) → sửa code → đóng băng code → chạy test một lần.
3. Kiểm tra "tắt hết cờ = bản gốc" trên từng câu.

### C5. Tái lập và sẵn có dữ liệu
1. Ghi commit, sha256 của bộ dữ liệu, và lệnh chạy.
2. Mục Data availability phải đúng sự thật: phần nào công bố, phần nào không, và vì sao (xem D3).

### C6. Trình bày
1. Theo cấu trúc IMRaD (mục B6). Tóm tắt có đủ: vấn đề, cách làm, kết quả chính (có số), ý nghĩa.
2. Định nghĩa mọi metric và thuật ngữ trước khi dùng. **Không dùng tên nội bộ** ("System 3", "Strict", "A/B/C", "real_v2") khi chưa định nghĩa. Trong bài nên đặt tên mô tả, ví dụ "rule layer", "reranker variant", "LLM-reader variant".
3. Mỗi hình và bảng phải tự đọc được và phải được nhắc tới trong bài.
4. Thuật ngữ nhất quán từ đầu đến cuối (answer / clarify / refuse).
5. Có mục Limitations và Threats to validity viết thật.
6. Không chép nguyên văn; diễn đạt lại và trích nguồn của ý.

---

## D. Ràng buộc riêng của dự án [QUYẾT ĐỊNH NHÓM]

| # | Ràng buộc |
|---|---|
| D1 | Bài 1 chỉ nói về System 3: hỏi đáp thủ tục hành chính cấp xã; trả lời, hỏi lại hoặc từ chối trên câu hỏi thật. **Không dùng số System 4** (để dành cho bài 2) |
| D2 | Số liệu đóng băng: kết quả ở commit `7d199f3`, code ở `b7010d1`, bộ test real_v2 khoá ở `7e78438`. κ lấy từ lượt gán lại B (`eval/real_v2/relabel/`, commit mẫu `73aebe3`) |
| D3 | Data & Ethics (đã duyệt):<br>(i) Cổng Dịch vụ công Quốc gia **không có API chính thức**. Dữ liệu thủ tục lấy qua API JSON nội bộ, ẩn danh, không công bố của chính trang web: không đăng nhập, không vượt captcha, 2 request/giây, một luồng, **cào một lần ngày 13/10/2026**, được 1.517 thủ tục. Đây là thông tin hành chính công khai, không có dữ liệu cá nhân.<br>(ii) Câu hỏi của người dân lấy từ hai bộ dữ liệu công khai trên Hugging Face (`hieunguyen1053/dichvucong_faqs`, `doanhieung/vn-mps-public-service-qa`) mà giấy phép không ghi rõ, nên **không phát hành lại** văn bản câu hỏi. Chỉ công bố mã câu, nhãn và kết quả.<br>(iii) Đã che thông tin cá nhân (tên, SĐT, CCCD) trước khi gán nhãn |
| D4 | Khai báo dùng AI: **trung thực, lời lẽ nhẹ nhàng, chuyên nghiệp**. Công ty đã duyệt việc có mục khai báo. Xem mục E |
| D5 | Tác giả theo thứ tự: **Trịnh Hoàng Nhân** (tác giả liên hệ), **Nguyễn Viết Hưng**, **Phạm Lê Thiên Dấn**, và mentor **Trương Long** (longt5@fpt.edu.vn) đứng tên. Vị trí của mentor: đề xuất xếp cuối như thông lệ với người hướng dẫn, chờ trưởng nhóm xác nhận. Đơn vị: Department of Artificial Intelligence, FPT University, Ho Chi Minh City, Vietnam (đơn vị của mentor chờ xác nhận). Không đưa số điện thoại vào bài. Tác giả liên hệ cần ORCID |
| D6 | Không nêu tên công ty khách hàng (ABI) hay dữ liệu của họ trong bài 1 |
| D7 | Mô tả đúng phần mềm và model thật: `qwen3:4b-instruct-2507` (q4_K_M) qua Ollama; bge-m3; bge-reranker-v2-m3; SQLite FTS5 / BM25. Không có vLLM, MCP, GPTCache, RouteLLM |
| D8 | Kết luận chính phải khớp số: A (rule layer) mang gần hết phần tăng. B chỉ thêm 1 câu so với A (p = 1). A + C (chỉ tên) chưa có ý nghĩa thống kê (p = 0,39). Cấu hình chạy mặc định là A |
| D9 | Repo công khai đi kèm bài không chứa: văn bản câu hỏi, 17 họ tên người thật trong `collect_real_v1.py`, dữ liệu hay khoá ABI, tệp cào về. Sau này teammate có thể bổ sung lại tài liệu về các bộ eval quan trọng [QUYẾT ĐỊNH NHÓM] |
| D10 | **Toàn bài khoảng 10 trang trở lại** theo template VJCS. Ước lượng 4.000–4.500 chữ kể cả bảng, khoảng 4–5 bảng, 1–2 hình. Chi tiết dài chuyển sang repo |
| D11 | Hai lượt nhãn: lượt A (Claude) gán cả 348 câu; lượt B do Gemini 4 Argon (Google, mức suy luận "High") gán 100 câu, rồi trưởng nhóm kiểm từng câu và không xem nhãn A. κ = 0,685 (95% bootstrap 0,548–0,820) trên 91 câu (B gán skip 9 câu kiến nghị). Chấm lại bằng nhãn B thì kết luận không đổi (`eval/real_v2/relabel/`, commit `83b33b4`). **Không được viết "two human annotators"** |
| D12 | Trưởng nhóm cho phép **cải thiện hệ thống tiếp trước khi nộp**. Nhưng số "sau cải thiện" chỉ được báo khi đo trên một bộ test mới đã khoá trước khi sửa code. real_v2 đã mở, chỉ còn dùng cho số hiện tại và các baseline cố định chạy một lần |
| D13 | **Phạm vi: chỉ thủ tục cấp xã/phường** [QUYẾT ĐỊNH NHÓM 25/10]. Không được viết hay ngụ ý đây là trợ lý thủ tục hành chính toàn quốc / mọi cấp. Tiêu đề, tóm tắt, mở đầu, Limitations phải nói rõ phạm vi cấp xã. Tránh cụm "nationwide" dễ hiểu nhầm |

---

## E. Khai báo dùng AI tạo sinh

Theo chính sách của World Scientific (A10):

- Mục riêng tên "**Declaration of AI Use**", đặt ngay trước Acknowledgements.
- Khuôn câu của nhà xuất bản: "During the preparation of this work, the author(s) used [Tool Name, Version] to [purpose and extent]. The authors reviewed, verified, and edited the output and take full responsibility for the content of the publication."
- Dự án dùng AI để viết code, chạy và tóm tắt thí nghiệm, gán nhãn và soạn bài. Theo chính sách, đây là AI tạo sinh nên **bắt buộc khai báo**.

Bản đề xuất: giữ khuôn câu của nhà xuất bản, lời lẽ nhẹ nhàng, đủ ý. Trưởng nhóm sẽ đọc lại.

> **Declaration of AI Use.** During the preparation of this work, the authors used Claude (Anthropic, Claude Opus 5.5) to assist with software development, with running and summarizing the experiments, with first-pass annotation of the evaluation questions, and with drafting and language editing of the manuscript. A second annotation of a random sample was produced with Gemini 4 Argon (Google) and checked item by item by an author who had not seen the first-pass labels. The research questions, the evaluation protocol and all final decisions were made by the authors, who reviewed, verified and edited the output and take full responsibility for the content of the publication.

Ghi chú:

- Phiên bản Claude: đợt làm việc này dùng Claude Opus 5.5. Nếu code các đợt trước được viết bằng phiên bản khác thì thêm vào, ví dụ "Claude models (Anthropic), including Claude Opus 5.5".
- Không bớt ý "nhãn lượt đầu do AI gán" và "lượt hai do model khác gán, người kiểm từng câu". Reviewer cần thông tin này để đánh giá độ tin cậy của nhãn, và chính sách của nhà xuất bản yêu cầu khai báo AI dùng để thu thập hay phân tích dữ liệu.
- Phần Method cũng phải mô tả cách gán nhãn, không chỉ nằm trong mục khai báo.

---

## F. Checklist cho agent phản biện (bước f)

Agent phản biện đọc bản thảo **cùng tệp này**, không đọc lịch sử làm việc. Mỗi vòng trả về danh sách lỗi có mức độ (chặn nộp / nên sửa / gợi ý).

1. Mỗi số trong bài có khớp bảng gốc không (`eval/hard/results/test`, `docs/BAO_CAO_CAU_KHO_2026-10-25.md`)? k/n, Wilson, McNemar có đủ không?
2. Có khẳng định nào thiếu bằng chứng hoặc là khẳng định tuyệt đối không (C1)?
3. Mỗi trích dẫn có trong `02_related_work/paper_list.md` với trạng thái "đã kiểm" không? Số liệu của bài khác có kèm bảng hay trang không?
4. Có so sánh nào giữa các bộ dữ liệu khác nhau như thể so được không (C3)?
5. Giao thức dev/test có được mô tả đủ, và có cấu hình nào bị "chọn theo test" không (C4)?
6. Đủ các mục theo template VJCS (A3–A12) và khuôn môn học (B2–B8) chưa? Có Declaration of AI Use, Competing interests, Data availability, ORCID chưa?
7. Có tên nội bộ nào chưa định nghĩa không (C6.2)?
8. Data & Ethics, khai báo AI, Data availability có đúng D3, D4, D9, D11 và mục E không?
9a. Có chỗ nào ngụ ý trợ lý toàn quốc hoặc mọi cấp không (D13)? Tiêu đề, tóm tắt, mở đầu có nói rõ phạm vi cấp xã không?
9. Tóm tắt ≤ 150 từ (đếm bằng script), ≤ 6 từ khoá, toàn bài khoảng 10 trang (A4, D10)? Chính tả Mỹ (A8)?
10. Limitations có nêu ít nhất các điểm sau không:
    - chỉ một bộ test;
    - lớp answer nhỏ (59 câu) và lớp clarify rất nhỏ (6 câu);
    - nhãn lượt đầu do AI gán, và cũng chính AI đó sửa hệ thống;
    - lượt nhãn thứ hai cũng có AI tham gia (có người kiểm), κ = 0,685;
    - luật viết riêng cho tiếng Việt và lĩnh vực này;
    - các baseline ngoài hoặc là baseline thêm sau khi test đã mở, hoặc chưa có?

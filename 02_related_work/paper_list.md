# Danh sách tài liệu cho bài 1 (đã kiểm / chờ kiểm)

Quy tắc (constraints.md C1.3): **chỉ cite bài có trạng thái "Đã kiểm"**, và chỉ lấy số của một bài sau khi đã đọc đúng bảng chứa số đó (ghi số bảng hoặc trang vào tệp tóm tắt).

- **PDF**: đọc trang đầu của PDF trong `docs/research paper/` của repo gốc (tên, tác giả, mã arXiv in trên trang).
- **Web**: kiểm trên ACL Anthology, arXiv hoặc trang của nhà xuất bản ngày 25/10/2026.
- **Chờ**: mới thấy qua tìm kiếm, chưa mở trang gốc.

Ngày lập: 25/10/2026.

## 0. Tệp tóm tắt theo khuôn (paper_summaries/paper_NN.md)

| Tệp | Khoá | Nhóm khuôn B2 |
|---|---|---|
| paper_01 | PhamDuy2023 | trực tiếp |
| paper_02 | Larson2019 | trực tiếp |
| paper_03 | Rajpurkar2018 | trực tiếp |
| paper_04 | Kamath2020 | trực tiếp |
| paper_05 | Aliannejadi2019 | trực tiếp |
| paper_06 | Wen2025 | trực tiếp |
| paper_07 | Rebedea2023 | trực tiếp |
| paper_08 | Qwen3 (+ qwen3inst) | model/phương pháp |
| paper_09 | BGEM3 | model/phương pháp |
| paper_10 | CRAG2024 | model/phương pháp |
| paper_11 | SelfRAG2024 | model/phương pháp |
| paper_12 | ViGPTQA2023 | lĩnh vực |
| paper_13 | Hien2025 | lĩnh vực |
| paper_14 | LegalCheck2026 | lĩnh vực |
| paper_15 | GovAIPipe2026 | lĩnh vực |
| paper_16 | GripOnLLMs2026 | lĩnh vực |
| paper_17 | GuidaPA2026 (khoá bib: jimenez2026) | lĩnh vực |
| paper_18 | Geifman2017 (khoá bib: geifman2017) | trực tiếp |
| paper_19 | Gilardi2023 (khoá bib: gilardi2023) | phương pháp đánh giá |
| paper_20 | Lewis2020 (khoá bib: lewis2020) | model/phương pháp |
| paper_21 | Dwork2015 (dwork2015) | phương pháp đánh giá |
| paper_22 | Brodersen2010 (brodersen2010) | phương pháp đánh giá |
| paper_23 | Wilson1927 (wilson1927) | phương pháp đánh giá |
| paper_24 | McNemar1947 (mcnemar1947) | phương pháp đánh giá |
| paper_25 | Cohen1960 (cohen1960) | phương pháp đánh giá |
| paper_26 | HF-dvc (hfdvc) | tài nguyên dữ liệu |
| paper_27 | HF-mps (hfmps) | tài nguyên dữ liệu |
| paper_28 | DVC (dvcportal) | tài nguyên dữ liệu |
| paper_29 | bge-reranker-v2-m3 (bgererank) | model/phương pháp |

Đủ khuôn B2: 8 trực tiếp (≥5, gồm Geifman2017), 6 model/phương pháp (≥3, gồm Lewis2020 và bge-reranker-v2-m3), 6 lĩnh vực (≥2); thêm 7 tệp về phương pháp đánh giá và 3 tệp về tài nguyên dữ liệu (28/10). PhamDuy2023 đọc lại từ PDF bản tác giả (users.soict.hust.edu.vn) ngày 25/10/2026.

## 1. Lĩnh vực: hỏi đáp thủ tục và pháp lý tiếng Việt (khuôn môn B2: ≥ 2 bài lĩnh vực)

| Khoá | Trích dẫn | Mã | Trạng thái | Vai trò trong bài 1 |
|---|---|---|---|---|
| PhamDuy2023 | A. Pham Duy, H. Le Thanh. "A Question-Answering System for Vietnamese Public Administrative Services." SoICT 2023, ACM | DOI 10.1145/3628797.3628965 (PDF in thiếu tiền tố "10.1145/") | Đã kiểm (đọc PDF gốc) | **Công trình gần nhất.** 4.547 cặp hỏi đáp lấy từ trang câu hỏi phổ biến của Cổng DVC, kèm 785.996 đoạn văn bản luật; truy hồi lai BM25+ và SimCSE/PhoBERT, xếp lại bằng cross-encoder; đo Recall@k, MAP, NDCG, F2. **Chỉ có câu trả lời được, không có từ chối hay hỏi lại** → đây là khoảng trống của bài 1 |
| ViGPTQA2023 | M.-T. Nguyen, K.-T. Tran, N. V. Nguyen, X.-S. Vu. "ViGPTQA – State-of-the-Art LLMs for Vietnamese Question Answering: System Overview, Core Models Training, and Evaluations." EMNLP 2023 Industry Track, pp. 754–764 | DOI 10.18653/v1/2023.emnlp-industry.70 | Đã kiểm (PDF + ACL Anthology) | LLM tiếng Việt cho hỏi đáp; bộ đánh giá trộn dữ liệu AI sinh và người viết. Bản draft cũ ghi sai tác giả ("N. Nguyen") và các số "15.000 cặp, 68,5% EM" **chưa kiểm** |
| Hien2025 | P. T. X. Hien, D. N. T. Nhi, P. T. N. Huyen. "Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems." IC3K 2025 (KMIS), SciTePress | DOI 10.5220/0013751200004000; IC3K 2025 Vol. 2 (KEOD, KMIS), pp. 290–300 | Đã kiểm (PDF) | RAG pháp lý tiếng Việt, 45.000 văn bản. Số "89%" là do tác giả tự báo, đánh giá bằng RAGAS và khảo sát người dùng |
| Ngo2025 | "Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques" | — | **Chưa kiểm được**: PDF chỉ là ảnh chụp trang web, tìm kiếm không ra tên này | Không cite cho tới khi tìm thấy bản gốc |
| AnsGen2025 | "Optimizing Answer Generator in Vietnamese Legal Question Answering Systems Using Language Models", ACM | DOI 10.1145/3732938 | Chờ (trang ACM chặn truy cập tự động) | Theo kết quả tìm kiếm: khoảng 10.000 cặp hỏi đáp từ Cổng DVC; so BartPho, VinaLlama-7B-chat, Llama3 8B bằng ROUGE |
| VietPSLM2026 | "A Small Language Model and Domain-Specific Resources for Vietnamese Public Services", Springer (chương sách) | DOI 10.1007/978-981-95-4960-3_2 | Chờ | Model nhỏ cho dịch vụ công tiếng Việt: tiền huấn luyện thích ứng miền, SFT, suy luận hai lượt |
| ICTmag | "A Large Language Model-Based Question Answering System for Online Public Administrative Services", Tạp chí Thông tin và Truyền thông | ictmag.ictvietnam.vn/…/1290 | Chờ (trang từ chối kết nối) | Hỏi đáp dịch vụ công trực tuyến bằng LLM |
| LAURA2025 | "LAURA: A Legal Agent Using Reasoning and Acting for Vietnamese Law", KSE 2025 | — | Chờ | Agent ReAct cho luật Việt Nam |

## 2. Từ chối, ngoài phạm vi, hỏi lại (khuôn B2: bài liên quan trực tiếp)

| Khoá | Trích dẫn | Mã | Trạng thái | Vai trò |
|---|---|---|---|---|
| Wen2025 | B. Wen, J. Yao, S. Feng, C. Xu, Y. Tsvetkov, B. Howe, L. L. Wang. "Know Your Limits: A Survey of Abstention in Large Language Models." TACL 13 (2025) 529–556 | DOI 10.1162/tacl_a_00754; arXiv:2407.18418 | Đã kiểm (web) | Khung lý thuyết cho "từ chối": nhìn từ câu hỏi, từ model, từ giá trị con người |
| Larson2019 | S. Larson et al. "An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction." EMNLP-IJCNLP 2019, pp. 1311–1316 | DOI 10.18653/v1/D19-1131 | Đã kiểm (web) | Bộ CLINC150. Bài tìm ra rằng mô hình phân loại tốt trong phạm vi nhưng khó nhận ra câu ngoài phạm vi; cùng chiều với E1/E2 |
| Rebedea2023 | T. Rebedea, R. Dinu, M. Sreedhar, C. Parisien, J. Cohen. "NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails." EMNLP 2023 System Demonstrations, pp. 431–445 | DOI 10.18653/v1/2023.emnlp-demo.40 | Đã kiểm (web) | "Rail" do người viết, chạy lúc suy luận, độc lập với LLM. Gần với lớp luật A |
| Rajpurkar2018 | P. Rajpurkar, R. Jia, P. Liang. "Know What You Don't Know: Unanswerable Questions for SQuAD." ACL 2018 (Vol. 2), pp. 784–789 | DOI 10.18653/v1/P18-2124 | Đã kiểm (web) |Câu không trả lời được trong hỏi đáp |
| Kamath2020 | A. Kamath, R. Jia, P. Liang. "Selective Question Answering under Domain Shift." ACL 2020, pp. 5684–5696 | DOI 10.18653/v1/2020.acl-main.503 | Đã kiểm (web) |Từ chối khi không chắc, khi dữ liệu lệch miền |
| Aliannejadi2019 | M. Aliannejadi, H. Zamani, F. Crestani, W. B. Croft. "Asking Clarifying Questions in Open-Domain Information-Seeking Conversations." SIGIR 2019, pp. 475–484 | DOI 10.1145/3331184.3331265 | Đã kiểm (web) |Hỏi lại |

| Geifman2017 (khoá bib: geifman2017) | Y. Geifman, R. El-Yaniv. "Selective Classification for Deep Neural Networks." NeurIPS 2017 | arXiv:1705.08500; DBLP conf/nips/GeifmanE17 | Đã kiểm (arXiv + Semantic Scholar, 27/10/2026) | Phân loại có chọn lọc, đánh đổi rủi ro–độ phủ (referee gợi ý) |
| Gilardi2023 (khoá bib: gilardi2023) | F. Gilardi, M. Alizadeh, M. Kubli. "ChatGPT Outperforms Crowd Workers for Text-Annotation Tasks." PNAS 120(30) e2305016120 (2023) | DOI 10.1073/pnas.2305016120; arXiv:2303.15056 | Đã kiểm (arXiv + Semantic Scholar, 27/10/2026) | LLM làm người gán nhãn: lý do bàn về độ tin cậy của nhãn AI (referee gợi ý) |

## 3. Phương pháp và model (khuôn B2: ≥ 3 bài)

| Khoá | Trích dẫn | Mã | Trạng thái | Vai trò |
|---|---|---|---|---|
| Qwen3 | Qwen Team. "Qwen3 Technical Report." 2025 | arXiv:2505.09388 | Đã kiểm (web) | Họ model của qwen3:4b-instruct-2507. **Thay cho Qwen2.5** trong bản draft cũ |
| BGEM3 | J. Chen, S. Xiao, P. Zhang, K. Luo, D. Lian, Z. Liu. "M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation." Findings of ACL 2024, pp. 2318–2335 | DOI 10.18653/v1/2024.findings-acl.137; arXiv:2402.03216 | Đã kiểm (web) | Embedding của phương án B |
| bgererank | BAAI. bge-reranker-v2-m3, model card trên Hugging Face | huggingface.co/BAAI/bge-reranker-v2-m3 | Đã kiểm (web, 25/10/2026; giấy phép Apache-2.0) | Reranker của phương án B |
| qwen3inst | Qwen Team. Qwen3-4B-Instruct-2507, model card | huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | Đã kiểm (web, 25/10/2026; Apache-2.0; bản cập nhật chỉ có chế độ non-thinking, 4,0B tham số, 36 lớp) | Báo cáo Qwen3 (5/2025) không mô tả bản 2507 nên cite thêm model card |
| Lewis2020 | P. Lewis et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 33 (2020), pp. 9459–9474 | arXiv:2005.11401 | Đã kiểm (web; số trang theo danh mục tham khảo của Hien2025) |Định nghĩa RAG |
| Robertson2009 | S. Robertson, H. Zaragoza. "The Probabilistic Relevance Framework: BM25 and Beyond." Foundations and Trends in IR 3(4) (2009) 333–389 | DOI 10.1561/1500000019 | Đã kiểm (web) | Trọng số IDF của ranker (`retrieval/rank.py`; không phải BM25 đầy đủ: không có bão hoà tần suất). Module FTS5 `data/search.py` chỉ dùng cho hàm phụ, không xếp hạng |
| CRAG2024 | S.-Q. Yan, J.-C. Gu, Y. Zhu, Z.-H. Ling. "Corrective Retrieval Augmented Generation." 2024 | arXiv:2401.15884 | Đã kiểm (PDF) | Bộ đánh giá truy hồi quyết định hành động, gần với decide() của B |
| SelfRAG2024 | A. Asai, Z. Wu, Y. Wang, A. Sil, H. Hajishirzi. "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection." ICLR 2024 | arXiv:2310.11511; ICLR 2024 (openreview hSyW5go0v8) | Đã kiểm (PDF + proceedings.iclr.cc) | Model tự quyết khi nào truy hồi hay phê phán; đối chiếu với "luật quyết định" |

## 4. Chính phủ điện tử và LLM trong khu vực công

| Khoá | Trích dẫn | Mã | Trạng thái | Vai trò |
|---|---|---|---|---|
| GovAIPipe2026 | A. Kaplan. "GovAI-Pipe: A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway." 2026 | arXiv:2606.01417 | Đã kiểm (PDF). Bản draft cũ ghi "Proc. dg.o 2026" mà chưa kiểm | Khung quản trị 4 lớp (kiểm trước triển khai, phân hạng rủi ro, giám sát lúc chạy + chuyển người xử lý, xử lý sau sự cố) cho chatbot e-Devlet. **Chỉ là khung khái niệm, chưa triển khai hay đánh giá thực nghiệm** (mục Limitations của bài). Bản nháp 25/10 từng ghi sai là "lọc phạm vi trước truy hồi", đã sửa |
| GripOnLLMs2026 | L. Samson, I. Gornishka, G. Lô, Y. M. Asano, S. Ghebreab. "From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch." 2026 | arXiv:2608.09925 | Đã kiểm (PDF). Bản draft cũ ghi "GIQ 2026" mà chưa kiểm | Đánh giá LLM cho chính quyền (Amsterdam), 6 chiều. Kết quả: model trả lời đúng (factuality) không có nghĩa là biết thừa nhận điều không biết (honesty) |
| GuidaPA2026 | D. M. Jimenez-Gutierrez, A. Cirillo, R. Nicolussi, A. Beltrame, A. Vitaletti. "GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning." 2026 | arXiv:2606.01386 | Đã kiểm (PDF) | Chatbot hành chính công, chạy tại chỗ, bảo vệ dữ liệu |
| COPAL2026 | Y. Liu, Y. Hu, X. Wang, Y. Li, Y. Wei, X. Wang, Y. Zhou. "Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots." 2026 | arXiv:2606.04394 | Đã kiểm (PDF). Bản draft cũ ghi "ACM TOCHI 2026" mà chưa kiểm | Chatbot phải tuân thủ chính sách riêng của tổ chức |
| LegalCheck2026 | V. van der Meer, J. Rossi. "LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters." 2026 | arXiv:2605.12012 | Đã kiểm (PDF). Nơi đăng ICAIL 2026: chờ kiểm | Hỗ trợ pháp lý cấp thành phố |
| LegalMALR2026 | Y. Li, M. Xie, G. Kang, Z. Gong, G. Wu, M. Yang. "LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval." 2026 | arXiv:2601.17692 | Đã kiểm (PDF). Bản draft cũ ghi sai tác giả và mã | Câu hỏi pháp lý của người dân "ngầm, nhiều vấn đề", gần với thư của người dân |

## 5. Thống kê và giao thức đánh giá

| Khoá | Trích dẫn | Trạng thái | Vai trò |
|---|---|---|---|
| McNemar1947 | Q. McNemar. "Note on the sampling error of the difference between correlated proportions or percentages." Psychometrika 12 (1947) | Đã kiểm (web): Psychometrika 12 (1947) 153–157, DOI 10.1007/BF02295996 | Phép kiểm cặp |
| Dietterich1998 | T. G. Dietterich. "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms." Neural Computation 10 (1998) | Đã kiểm (web): Neural Computation 10(7) (1998) 1895–1923, DOI 10.1162/089976698300017197 | Lý do dùng McNemar khi so hai bộ phân loại |
| Wilson1927 | E. B. Wilson. "Probable Inference, the Law of Succession, and Statistical Inference." JASA 22 (1927) | Đã kiểm (web): JASA 22(158) (1927) 209–212, DOI 10.1080/01621459.1927.10502953 | Khoảng tin cậy |
| Cohen1960 | J. Cohen. "A Coefficient of Agreement for Nominal Scales." Educational and Psychological Measurement 20 (1960) | Đã kiểm (web): EPM 20(1) (1960) 37–46, DOI 10.1177/001316446002000104 | κ |
| LandisKoch1977 | J. R. Landis, G. G. Koch. "The Measurement of Observer Agreement for Categorical Data." Biometrics 33 (1977) | Đã kiểm (web): Biometrics 33(1) (1977) 159–174, DOI 10.2307/2529310 | Thang diễn giải κ (0,61–0,80 = "substantial") |
| Brodersen2010 | K. H. Brodersen et al. "The Balanced Accuracy and Its Posterior Distribution." ICPR 2010 | Đã kiểm (web): ICPR 2010, pp. 3121–3124, DOI 10.1109/ICPR.2010.764 | Balanced accuracy |
| Dwork2015 | C. Dwork et al. "The Reusable Holdout: Preserving Validity in Adaptive Data Analysis." Science 349 (2015) | Đã kiểm (web): Science 349(6248) (2015) 636–638, DOI 10.1126/science.aaa9375 | Lý do khoá test và chạy một lần |

## 6. Bộ dữ liệu (cite dạng tài nguyên)

| Khoá | Nguồn | Trạng thái |
|---|---|---|
| HF-dvc | `hieunguyen1053/dichvucong_faqs` (config hoi-dap, 1.07k dòng), Hugging Face; theo các link trong dữ liệu thì là hỏi đáp của Cổng DVC tỉnh Bình Định | Đã kiểm 25/10/2026: **không ghi giấy phép**, thẻ dataset trống |
| HF-mps | `doanhieung/vn-mps-public-service-qa` (809 dòng), Hugging Face; hỏi đáp của Cổng Dịch vụ công Bộ Công an | Đã kiểm 25/10/2026: **không ghi giấy phép** |
| DVC | Cổng Dịch vụ công Quốc gia, dichvucong.gov.vn, truy cập 13/10/2026 | Đã kiểm |

## 7. Bỏ khỏi bài 1

GPTCache, RouteLLM, vLLM, Nougat, Constitutional AI, DSPy, ToolLLM, RAGAS, Shakti (Aralimatti 2025), Pareja 2024, Patel 2025, Akarsu 2026, Baban 2025, HyPA-RAG, CanLegalRAGBench, LegalBench-RAG, CoVe, CRITIC, GASP, LawPal, LQ-RAG.

Lý do: hệ thống không dùng; hoặc không liên quan trực tiếp tới "trả lời / hỏi lại / từ chối"; hoặc bản draft cũ trích sai. Chi tiết ở `draft_salvage.md` mục 3. Một số bài (Akarsu 2026, LegalBench-RAG) có thể dùng cho bài 2.

## 8. Đối chiếu với `07_paper_draft/latex/refs.bib` (28/10/2026)

Bài trích **29** mục. Có trong danh sách này nhưng **không còn được trích** trong bản cuối:
- Dietterich1998, LandisKoch1977 và Robertson2009: bỏ ngày 27/10 để vừa số trang. Ý của chúng vẫn đúng; bài chỉ còn trích McNemar1947 và Cohen1960.
- LegalCheck2026 (paper_14): chỉ để tham khảo, không trích trong bài.

Mọi mục còn lại ở mục 1–6 đều được trích. Từ 28/10, cả 29 mục được trích đều có tệp tóm tắt (paper_01–paper_29; Qwen3 và model card Qwen3-4B-Instruct-2507 chung tệp paper_08).

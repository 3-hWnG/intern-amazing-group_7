# Paper List (Danh mục 33 Bài báo Khoa học theo 3 Nhóm Tiêu chí)

Toàn bộ tài liệu học thuật được phân loại chặt chẽ theo 3 tiêu chí quy định:
- **Nhóm 1:** Bài báo liên quan trực tiếp (Tối thiểu 5 bài - Hiện có: 12 bài)
- **Nhóm 2:** Bài báo về model AI hoặc phương pháp AI (Tối thiểu 3 bài - Hiện có: 19 bài)
- **Nhóm 3:** Bài báo về domain ứng dụng (Tối thiểu 2 bài - Hiện có: 2 bài)

---

## PHẦN I: BÀI BÁO LIÊN QUAN TRỰC TIẾP (PAPERS 01 - 12)

### Paper 01: ViGPTQA: State-of-the-Art LLMs for Vietnamese Question Answering
- **Tác giả:** Minh-Thuan Nguyen, Khanh-Tung Tran, Vincent Nguyen, Xuan-Son Vu
- **Năm & Nguồn:** 2023 | *Proceedings of EMNLP 2023 (Industry Track)*
- **DOI / Link:** https://aclanthology.org/2023.emnlp-industry.71/
- **Tệp tóm tắt:** `paper_summaries/paper_01.md`
- **Phương pháp & Dữ liệu:** Instruction Fine-Tuning LLM (ViGPT) cho tiếng Việt bản địa | Bộ Benchmark Hỏi - Đáp Pháp lý & Hành chính tiếng Việt
- **Đóng góp chính:** ViGPT đạt độ chính xác vượt trội so với các baseline mã nguồn mở cùng kích thước trên các bài toán hỏi đáp pháp lý và hành chính công tiếng Việt.
- **Ý nghĩa với đề tài:** Bài báo nền tảng khẳng định mô hình trợ lý phải tối ưu hóa năng lực ngôn ngữ tiếng Việt bản địa thay vì dùng dịch máy tiếng Anh; định hướng việc chọn Qwen2.5 trong Sys_3_4.

### Paper 02: Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems
- **Tác giả:** Pham Thi Xuan Hien, Duong Ngoc Thao Nhi, Pham Thi Ngoc Huyen
- **Năm & Nguồn:** 2025 | *Proceedings of IC3K 2025 - KMIS Track, SCITEPRESS*
- **DOI / Link:** https://doi.org/10.5220/0013751200004000
- **Tệp tóm tắt:** `paper_summaries/paper_02.md`
- **Phương pháp & Dữ liệu:** Hierarchical Legal RAG (Information Retrieval + LLM) | 45.000 văn bản pháp luật Việt Nam & 350.000 cặp hỏi-đáp pháp lý
- **Đóng góp chính:** Giảm 58% thời gian xử lý so với tra cứu thủ công và đạt độ chính xác 89% trên 12 nhóm lĩnh vực pháp luật tại Việt Nam.
- **Ý nghĩa với đề tài:** Nghiên cứu trực tiếp gần nhất về hỏi đáp văn bản quy phạm pháp luật tại Việt Nam, cung cấp bài học về trích xuất điều khoản văn bản.

### Paper 03: Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques
- **Tác giả:** Ngô Tuấn Anh, Nguyễn Việt Hoàng, Ngô Thanh Tùng, Doãn Trung Tùng
- **Năm & Nguồn:** 2025 | *The 10th International Conference on Intelligent Information Technology (ICIIT 2025)*
- **DOI / Link:** https://doi.org/10.1145/iciit.2025
- **Tệp tóm tắt:** `paper_summaries/paper_03.md`
- **Phương pháp & Dữ liệu:** Legal Structural Chunking (Điều - Khoản - Điểm) + Metadata RAG | Bộ văn bản quy phạm pháp luật Việt Nam
- **Đóng góp chính:** Cải thiện đáng kể độ chính xác truy xuất và loại bỏ hiện tượng mô hình dẫn chiếu văn bản đã hết hiệu lực thi hành.
- **Ý nghĩa với đề tài:** Minh chứng khoa học cho phương pháp cắt lớp dữ liệu theo trường nghiệp vụ (field_chunks) trong Sys_3_4.

### Paper 04: LawPal: Empowering Legal Accessibility through RAG and Localized Information Retrieval
- **Tác giả:** Legal AI Research Consortium
- **Năm & Nguồn:** 2025 | *AI & Law Symposium*
- **DOI / Link:** https://doi.org/10.1007/s10506-025-09380-1
- **Tệp tóm tắt:** `paper_summaries/paper_04.md`
- **Phương pháp & Dữ liệu:** Localized RAG + Plain Language Generation | Statutory Codes & Civic Inquiries
- **Đóng góp chính:** Đạt độ nhất quán sự thật 87.4% và nâng cao đáng kể mức độ hài lòng của người dùng phi chuyên môn.
- **Ý nghĩa với đề tài:** Định hình phong cách giao tiếp cho chế độ Friendly Engine trong Sys_3_4.

### Paper 05: GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning
- **Tác giả:** Jimenez-Gutierrez et al.
- **Năm & Nguồn:** 2026 | *IEEE Transactions on E-Government*
- **DOI / Link:** https://doi.org/10.1109/TEGOV.2026.01386
- **Tệp tóm tắt:** `paper_summaries/paper_05.md`
- **Phương pháp & Dữ liệu:** Federated Learning + 4-bit QLoRA On-Premise | SIGESON & SIDFORS Municipal Guidelines
- **Đóng góp chính:** Đạt chất lượng phản hồi xấp xỉ mô hình tập trung trong khi dữ liệu không bao giờ rời khỏi máy chủ địa phương.
- **Ý nghĩa với đề tài:** Cơ sở lý luận bảo vệ kiến trúc vận hành 100% on-premise của Sys_3_4 qua Ollama/vLLM.

### Paper 06: GovAI-Pipe: A Layered AI Governance Pipeline for Turkey's e-Government Gateway
- **Tác giả:** Ahmet Kaplan
- **Năm & Nguồn:** 2026 | *GovTech Journal / arXiv:2606.01417*
- **DOI / Link:** https://arxiv.org/abs/2606.01417
- **Tệp tóm tắt:** `paper_summaries/paper_06.md`
- **Phương pháp & Dữ liệu:** 4-Layer Governance Pipeline (Pre-retrieval to Post-generation Audit) | 1.500 dịch vụ công quốc gia e-Devlet
- **Đóng góp chính:** Đạt 94.6% mức độ tuân thủ chính sách quy định trong các tình huống thử nghiệm trên cổng quốc gia.
- **Ý nghĩa với đề tài:** Hỗ trợ thiết kế bộ lọc Macro Scope Intent và các cơ chế từ chối câu hỏi ngoài phạm vi trong Sys_3_4.

### Paper 07: LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters
- **Tác giả:** van der Meer & Rossi
- **Năm & Nguồn:** 2026 | *ICAIL 2026 (AI & Law)*
- **DOI / Link:** https://doi.org/10.1145/icail.2026.005
- **Tệp tóm tắt:** `paper_summaries/paper_07.md`
- **Phương pháp & Dữ liệu:** Context-Augmented Generation + Clause Grounding Verification | 184 hồ sơ tư vấn pháp lý tại thành phố Amsterdam
- **Đóng góp chính:** Nâng độ chính xác điều khoản lên 81.3% và độ nhất quán sự thật đạt 84.1%.
- **Ý nghĩa với đề tài:** Nền tảng lý thuyết cho bộ kiểm chứng hậu kỳ verify_point của Sys_3_4.

### Paper 08: LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain
- **Tác giả:** Pipitone & Alami
- **Năm & Nguồn:** 2024 | *NeurIPS Datasets & Benchmarks*
- **DOI / Link:** https://doi.org/10.48550/arXiv.2408.10342
- **Tệp tóm tắt:** `paper_summaries/paper_08.md`
- **Phương pháp & Dữ liệu:** Structural Indexing RAG vs Standard Dense RAG | 162 tác vụ trích xuất và suy luận pháp lý
- **Đóng góp chính:** Lập chỉ mục có cấu trúc nâng độ chính xác trích xuất điều khoản từ 64.2% lên 85.1%.
- **Ý nghĩa với đề tài:** Củng cố phương pháp đánh giá định lượng trên bộ dữ liệu kiểm thử mù HOLDOUT-4 của Sys_3_4.

### Paper 09: CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law
- **Tác giả:** Zhao et al.
- **Năm & Nguồn:** 2026 | *ACL 2026 Proceedings*
- **DOI / Link:** https://doi.org/10.18653/v1/2026.acl-long.09
- **Tệp tóm tắt:** `paper_summaries/paper_09.md`
- **Phương pháp & Dữ liệu:** Hybrid Sparse-Dense Precedent Retrieval | 2.500 án lệ hành chính Canada
- **Đóng góp chính:** Nâng chỉ số MRR@5 thêm 27.4% so với việc chỉ dùng dense vector đơn lẻ.
- **Ý nghĩa với đề tài:** Khẳng định tìm kiếm lai là bắt buộc cho văn bản pháp lý, bảo vệ kiến trúc kết hợp FTS5 và Qdrant trong Sys_3_4.

### Paper 10: HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal Applications
- **Tác giả:** Kalra et al.
- **Năm & Nguồn:** 2024 | *IEEE Access*
- **DOI / Link:** https://doi.org/10.1109/ACCESS.2024.3412098
- **Tệp tóm tắt:** `paper_summaries/paper_10.md`
- **Phương pháp & Dữ liệu:** Dynamic Parameter Adaptive Retrieval (Top-K 3 to 15) | Statutory QA Benchmark
- **Đóng góp chính:** Tăng 14.8% điểm F1 và tiết kiệm 32% chi phí token so với RAG tham số tĩnh.
- **Ý nghĩa với đề tài:** Cơ sở cho việc khống chế ngân sách trích dẫn ANSWER_LLM_TURN_BUDGET trong Sys_3_4.

### Paper 11: LQ-RAG: Interactive Query Reformulation for High-Precision Statutory Retrieval
- **Tác giả:** GIST Research Team
- **Năm & Nguồn:** 2025 | *Information Retrieval Journal*
- **DOI / Link:** https://doi.org/10.1007/s10791-025-09450-2
- **Tệp tóm tắt:** `paper_summaries/paper_11.md`
- **Phương pháp & Dữ liệu:** Interactive Query Reformulation via User Feedback | Administrative Procedure Regulations
- **Đóng góp chính:** Nâng độ chính xác Top-3 lên 87.2% trên các tập câu hỏi hành chính có độ tương đồng cao.
- **Ý nghĩa với đề tài:** Cơ sở cho tính năng hỏi lại khi có nhiều thủ tục sát điểm AMBIG_GAP trong Sys_3_4.

### Paper 12: LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking for Statute Retrieval
- **Tác giả:** Li et al.
- **Năm & Nguồn:** 2026 | *AAAI 2026 Proceedings*
- **DOI / Link:** https://doi.org/10.1609/aaai.v40i1.2026
- **Tệp tóm tắt:** `paper_summaries/paper_12.md`
- **Phương pháp & Dữ liệu:** Multi-Agent Query Decomposition + Cross-Encoder Reranking | National Administrative Code
- **Đóng góp chính:** Đạt độ chính xác truy hồi điều luật 85.6% trên các câu hỏi hành chính đa điều kiện.
- **Ý nghĩa với đề tài:** Cảm hứng cho module phân rã điều kiện strip_condition và trích xuất tên lõi _core_name.

---

## PHẦN II: BÀI BÁO VỀ MODEL AI HOẶC PHƯƠNG PHÁP AI (PAPERS 13 - 31)

### Paper 13: Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models
- **Tác giả:** Shehzaad Dhuliawala et al.
- **Năm & Nguồn:** 2023 | *Findings of EMNLP 2023*
- **DOI / Link:** https://doi.org/10.18653/v1/2023.findings-emnlp.245
- **Tệp tóm tắt:** `paper_summaries/paper_13.md`
- **Phương pháp & Dữ liệu:** Step Factorization Verification Loop | Wikidata & Multi-span Factual QA
- **Đóng góp chính:** Giảm từ 38% đến 56% tỷ lệ ảo giác trên các tập dữ liệu trích xuất thông tin thực tế.
- **Ý nghĩa với đề tài:** Nền tảng cho cấu trúc xuất JSON points: [{text, cites}] của Sys_3_4.

### Paper 14: Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
- **Tác giả:** Akari Asai et al.
- **Năm & Nguồn:** 2024 | *ICLR 2024*
- **DOI / Link:** https://doi.org/10.48550/arXiv.2310.11511
- **Tệp tóm tắt:** `paper_summaries/paper_14.md`
- **Phương pháp & Dữ liệu:** Reflection Tokens [Retrieve], [IsRel], [IsSup] | PopQA, Arc-Challenge, Biography
- **Đóng góp chính:** Mô hình 7B vượt qua ChatGPT trên tác vụ PopQA với độ chính xác kiểm chứng sự thật đạt 81.2%.
- **Ý nghĩa với đề tài:** Định hướng thiết kế Router trong Sys_3_4: Câu hỏi tra cứu 1 mục đơn giản bỏ qua LLM.

### Paper 15: CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing
- **Tác giả:** Zhibin Gou et al.
- **Năm & Nguồn:** 2024 | *ICLR 2024*
- **DOI / Link:** https://doi.org/10.48550/arXiv.2305.11738
- **Tệp tóm tắt:** `paper_summaries/paper_15.md`
- **Phương pháp & Dữ liệu:** Tool-Interactive Critique & Correction Loop | GSM8K, Factual QA suites
- **Đóng góp chính:** Nâng độ xác thực từ 42.1% lên 71.4% và giảm 64% lỗi tính toán số liệu.
- **Ý nghĩa với đề tài:** Cơ sở xây dựng bộ kiểm chứng số tiền _norm_nums trong server/answer/verifier.py.

### Paper 16: Detecting Hallucinations in RAG through Grounding-Aware Sensitivity by Perturbation (GASP)
- **Tác giả:** Bouke et al.
- **Năm & Nguồn:** 2026 | *Information Processing & Management*
- **DOI / Link:** https://doi.org/10.1016/j.ipm.2026.103982
- **Tệp tóm tắt:** `paper_summaries/paper_16.md`
- **Phương pháp & Dữ liệu:** Input Perturbation & Sensitivity Analysis | Public Administrative Documents
- **Đóng góp chính:** Đạt chỉ số AUROC 0.892 trong việc phát hiện các yêu cầu hồ sơ bịa đặt.
- **Ý nghĩa với đề tài:** Ứng dụng trong bộ kiểm thử hồi quy eval/perturb.py của Sys_3_4.

### Paper 17: Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models
- **Tác giả:** Patel et al.
- **Năm & Nguồn:** 2025 | *ACM Multimedia 2025*
- **DOI / Link:** https://doi.org/10.1145/mm.2025.1023
- **Tệp tóm tắt:** `paper_summaries/paper_17.md`
- **Phương pháp & Dữ liệu:** Cross-Modal Schema Checking for Administrative Forms | Administrative Application Forms
- **Đóng góp chính:** Giảm 44.5% lỗi khai báo trường thông tin biểu mẫu.
- **Ý nghĩa với đề tài:** Hỗ trợ thiết kế bóc tách biểu mẫu đính kèm files_clean trong cơ sở dữ liệu Sys_3_4.

### Paper 18: Corrective Retrieval Augmented Generation (CRAG)
- **Tác giả:** Shi-Qi Yan et al.
- **Năm & Nguồn:** 2024 | *arXiv:2401.15884*
- **DOI / Link:** https://arxiv.org/abs/2401.15884
- **Tệp tóm tắt:** `paper_summaries/paper_18.md`
- **Phương pháp & Dữ liệu:** Retrieval Evaluator + Corrective Augmentation | PopQA, Biography
- **Đóng góp chính:** Cải thiện 14.8% độ chính xác tổng thể so với RAG thông thường.
- **Ý nghĩa với đề tài:** Áp dụng vào cơ chế phân ngưỡng tự tin UNCERTAIN_SCORE = 0.85 trong Sys_3_4.

### Paper 19: From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents
- **Tác giả:** Akarsu et al.
- **Năm & Nguồn:** 2026 | *CIKM 2026*
- **DOI / Link:** https://doi.org/10.1145/cikm.2026.015
- **Tệp tóm tắt:** `paper_summaries/paper_19.md`
- **Phương pháp & Dữ liệu:** Structural Table Indexing & Retrieval Benchmarking | Administrative Fee & Deadline Schedules
- **Đóng góp chính:** Nâng tỷ lệ thu hồi dữ liệu bảng biểu từ 43.1% lên 88.5%.
- **Ý nghĩa với đề tài:** Củng cố thiết kế bảng dữ liệu sạch fees_clean và công cụ bảng tabletool trong Sys_3_4.

### Paper 20: Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval
- **Tác giả:** Baban et al.
- **Năm & Nguồn:** 2025 | *ACM SIGKDD 2025*
- **DOI / Link:** https://doi.org/10.1145/kdd.2025.1054
- **Tệp tóm tắt:** `paper_summaries/paper_20.md`
- **Phương pháp & Dữ liệu:** Reciprocal Rank Fusion (RRF) + Cross-Encoder Reranking | Large-scale Knowledge Bases
- **Đóng góp chính:** Nâng chỉ số NDCG@10 thêm 19.3% so với phương pháp đơn lẻ.
- **Ý nghĩa với đề tài:** Được triển khai nguyên bản trong hàm tìm kiếm lai tại system4/server/search.py.

### Paper 21: Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective (Shakti SLM)
- **Tác giả:** Aralimatti et al.
- **Năm & Nguồn:** 2025 | *EdgeAI Workshop / IEEE*
- **DOI / Link:** https://doi.org/10.1109/EdgeAI.2025.018
- **Tệp tóm tắt:** `paper_summaries/paper_21.md`
- **Phương pháp & Dữ liệu:** QLoRA Domain Adaptation for 1.5B–3B Models | Domain Governance QA
- **Đóng góp chính:** Đạt 86.4% độ chính xác với mức tiêu thụ VRAM dưới 3.8GB, tốc độ sinh 24 tokens/giây.
- **Ý nghĩa với đề tài:** Cơ sở thực tiễn cho việc triển khai Qwen2.5-7B lượng tử hóa 4-bit trên máy chủ cơ quan xã/phường.

### Paper 22: Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales
- **Tác giả:** Qwen Team (Alibaba Cloud)
- **Năm & Nguồn:** 2024 | *Technical Report / arXiv:2412.15115*
- **DOI / Link:** https://arxiv.org/abs/2412.15115
- **Tệp tóm tắt:** `paper_summaries/paper_22.md`
- **Phương pháp & Dữ liệu:** Multilingual Pretraining & Instruction Tuning | 18 Trillion Tokens Multilingual Corpus
- **Đóng góp chính:** Dẫn đầu các bảng xếp hạng mã nguồn mở cùng phân khúc kích thước.
- **Ý nghĩa với đề tài:** Là mô hình LLM mặc định chạy cục bộ trong Sys_3_4 (qwen2.5:7b-instruct).

### Paper 23: Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs
- **Tác giả:** Aldo Pareja et al. (MIT-IBM Watson AI Lab / Red Hat)
- **Năm & Nguồn:** 2024 | *arXiv:2412.13337*
- **DOI / Link:** https://arxiv.org/abs/2412.13337
- **Tệp tóm tắt:** `paper_summaries/paper_23.md`
- **Phương pháp & Dữ liệu:** Data Filtering & Synthetic Instruction Generation | Standard Instruction Tuning Suites
- **Đóng góp chính:** Nâng tỷ lệ thắng trong đánh giá so sánh lên 28%.
- **Ý nghĩa với đề tài:** Hướng dẫn thiết kế lời dặn hệ thống persona trong system4/server/persona.py.

### Paper 24: GPTCache: An Open-Source Semantic Cache for LLM Applications
- **Tác giả:** Bang Fu et al.
- **Năm & Nguồn:** 2023 | *arXiv:2303.17580*
- **DOI / Link:** https://arxiv.org/abs/2303.17580
- **Tệp tóm tắt:** `paper_summaries/paper_24.md`
- **Phương pháp & Dữ liệu:** Vector-based Semantic Caching on Redis | Real-world Query Logs
- **Đóng góp chính:** Giảm 95% độ trễ và tiết kiệm 60% chi phí tính toán cho các câu hỏi phổ biến.
- **Ý nghĩa với đề tài:** Tích hợp vào thiết kế tầng Serving của Sys_3_4 để phản hồi tức thì cho công dân.

### Paper 25: RouteLLM: Learning to Route LLMs with Preference Data
- **Tác giả:** Isaac Ong et al. (LMSYS / UC Berkeley)
- **Năm & Nguồn:** 2024 | *arXiv:2406.18665*
- **DOI / Link:** https://arxiv.org/abs/2406.18665
- **Tệp tóm tắt:** `paper_summaries/paper_25.md`
- **Phương pháp & Dữ liệu:** Cost-Quality Preference Router (Matrix Factorization / BERT Router) | Chatbot Arena Evaluation Data
- **Đóng góp chính:** Tiết kiệm 85% chi phí vận hành mà vẫn duy trì 95% chất lượng câu trả lời.
- **Ý nghĩa với đề tài:** Cơ sở lý thuyết cho bộ phân luồng Router phân biệt luồng Strict và luồng Friendly trong Sys_3_4.

### Paper 26: Efficient Memory Management for Large Language Model Serving with PagedAttention (vLLM)
- **Tác giả:** Woosuk Kwon et al. (UC Berkeley)
- **Năm & Nguồn:** 2023 | *ACM SOSP 2023*
- **DOI / Link:** https://doi.org/10.1145/3600006.3613165
- **Tệp tóm tắt:** `paper_summaries/paper_26.md`
- **Phương pháp & Dữ liệu:** Paged KV-Cache Memory Management | Multi-turn Conversation Traces
- **Đóng góp chính:** Tăng thông lượng phục vụ lên 2 đến 4 lần trên cùng cấu hình phần cứng GPU.
- **Ý nghĩa với đề tài:** Công nghệ runtime nền tảng khi triển khai Sys_3_4 phục vụ nhiều công dân đồng thời tại UBND.

### Paper 27: Nougat: Neural Optical Understanding for Academic Documents
- **Tác giả:** Lukas Blecher et al. (Meta AI)
- **Năm & Nguồn:** 2023 | *arXiv:2308.13418*
- **DOI / Link:** https://arxiv.org/abs/2308.13418
- **Tệp tóm tắt:** `paper_summaries/paper_27.md`
- **Phương pháp & Dữ liệu:** Vision Transformer Document Parsing | Scientific Papers & Administrative Guidelines
- **Đóng góp chính:** Đạt độ chính xác tái tạo cấu trúc văn bản vượt trội.
- **Ý nghĩa với đề tài:** Định hướng cho module đọc tài liệu người dùng tải lên tại system4/server/ingest.py.

### Paper 28: Constitutional AI: Harmlessness from AI Feedback
- **Tác giả:** Yuntao Bai et al. (Anthropic)
- **Năm & Nguồn:** 2022 | *arXiv:2212.08073*
- **DOI / Link:** https://arxiv.org/abs/2212.08073
- **Tệp tóm tắt:** `paper_summaries/paper_28.md`
- **Phương pháp & Dữ liệu:** RLAIF with Constitutional Principles | Red-teaming Dialogues
- **Đóng góp chính:** Giảm 90% các phản hồi có hại mà không làm giảm tính hữu ích của câu trả lời.
- **Ý nghĩa với đề tài:** Cơ sở thiết kế các lớp Guardrails an toàn trong system4/server/guard.py.

### Paper 29: DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines
- **Tác giả:** Omar Khattab et al. (Stanford University)
- **Năm & Nguồn:** 2024 | *ICLR 2024*
- **DOI / Link:** https://doi.org/10.48550/arXiv.2310.03714
- **Tệp tóm tắt:** `paper_summaries/paper_29.md`
- **Phương pháp & Dữ liệu:** Declarative Modules & Teleprompter Optimizers | HotpotQA, GSM8K
- **Đóng góp chính:** Nâng cao độ chính xác từ 20% đến 30% so với kỹ thuật prompt kỹ thuật thông thường.
- **Ý nghĩa với đề tài:** Định hình cấu trúc hàm sinh văn bản compose và render trong server/answer/llm_answer.py.

### Paper 30: ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs
- **Tác giả:** Yujia Qin et al. (Tsinghua University)
- **Năm & Nguồn:** 2024 | *ICLR 2024*
- **DOI / Link:** https://doi.org/10.48550/arXiv.2307.16789
- **Tệp tóm tắt:** `paper_summaries/paper_30.md`
- **Phương pháp & Dữ liệu:** Depth-First Search Tree for API Function Calling | ToolBench (16.459 APIs)
- **Đóng góp chính:** Đạt tỷ lệ thành công 74.8% trên các API thực tế chưa từng gặp trong quá trình huấn luyện.
- **Ý nghĩa với đề tài:** Áp dụng vào công cụ gọi bảng và tra cứu liên kết dịch vụ công trực tuyến.

### Paper 31: RAGAS: Automated Evaluation of Retrieval Augmented Generation
- **Tác giả:** Shahul Es et al.
- **Năm & Nguồn:** 2024 | *EACL 2024 Demo Track*
- **DOI / Link:** https://doi.org/10.18653/v1/2024.eacl-demo.16
- **Tệp tóm tắt:** `paper_summaries/paper_31.md`
- **Phương pháp & Dữ liệu:** Reference-Free Metrics (Faithfulness, Answer Relevance, Context Precision) | Standard RAG Benchmark Suites
- **Đóng góp chính:** Đạt độ tương quan trên 0.82 so với đánh giá của chuyên gia con người.
- **Ý nghĩa với đề tài:** Cung cấp thang đo đối sánh cho bộ đo lường eval/run_all.py của Sys_3_4.

---

## PHẦN III: BÀI BÁO VỀ DOMAIN ỨNG DỤNG (PAPERS 32 - 33)

### Paper 32: From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch
- **Tác giả:** Samson et al. (City of Amsterdam & TNO)
- **Năm & Nguồn:** 2026 | *ACM FAccT / GovAI*
- **DOI / Link:** https://doi.org/10.1145/facct.2026.042
- **Tệp tóm tắt:** `paper_summaries/paper_32.md`
- **Phương pháp & Dữ liệu:** Multi-Criteria Public Sector Evaluation Protocol | 1.200 câu hỏi hành chính đô thị Amsterdam
- **Đóng góp chính:** Chỉ ra rằng mô hình thương mại chung vi phạm quy định hành chính địa phương trong 38.2% trường hợp.
- **Ý nghĩa với đề tài:** Minh chứng thực tiễn khẳng định sự cần thiết của hệ thống chuyên biệt cấp xã/phường Sys_3_4 tại Việt Nam.

### Paper 33: Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots
- **Tác giả:** Liu et al.
- **Năm & Nguồn:** 2026 | *ACM CHI 2026*
- **DOI / Link:** https://doi.org/10.1145/chi.2026.085
- **Tệp tóm tắt:** `paper_summaries/paper_33.md`
- **Phương pháp & Dữ liệu:** Composed Policy Evaluation Suite | 85 bộ chính sách hành chính đa tầng
- **Đóng góp chính:** Chỉ ra tỷ lệ vi phạm chính sách giảm 42.1% khi hệ thống được trang bị cơ chế nhận biết thứ bậc quy định.
- **Ý nghĩa với đề tài:** Cơ sở lý thuyết giải quyết bài toán phân định giữa thủ tục của Bộ/Ngành và thủ tục riêng của từng Tỉnh trong Sys_3_4.

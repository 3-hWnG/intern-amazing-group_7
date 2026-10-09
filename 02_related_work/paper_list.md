# Paper List (33 Research Papers - Phân loại theo 3 Tiêu chí)

Toàn bộ 33 bài báo nghiên cứu khoa học được khảo sát và phân tích trong dự án Sys_3_4 được phân chia theo 3 nhóm tiêu chí chuẩn:

---

## PHẦN I: BÀI BÁO LIÊN QUAN TRỰC TIẾP (12 BÀI)
*Bao gồm các nghiên cứu về hỏi đáp pháp luật Việt Nam, hệ thống RAG pháp lý và chatbot dịch vụ công cơ sở.*

### 1. [Bài 21] ViGPTQA: State-of-the-Art LLMs for Vietnamese Question Answering
- **Tác giả:** Minh-Thuan Nguyen, Khanh-Tung Tran, Vincent Nguyen, Xuan-Son Vu
- **Năm & Hội nghị:** 2023 | *Proceedings of EMNLP 2023 (Industry Track)*, pages 754–764
- **Tập tin phân tích:** `paper_summaries/paper_21_ViGPTQA.md`
- **Tóm tắt cốt lõi:** Đề xuất hệ thống hỏi đáp tiếng Việt thực tế và mô hình ViGPT được fine-tune chuyên biệt cho tiếng Việt. Chứng minh rằng mô hình bản địa hóa tiếng Việt vượt trội hoàn toàn so với mô hình đa ngôn ngữ trên câu hỏi pháp lý và hành chính công.
- **Vai trò trong đề tài:** Bài báo nền tảng khẳng định phải tối ưu hóa năng lực ngôn ngữ tiếng Việt bản địa thay vì dùng dịch máy tiếng Anh.

### 2. [Bài 23] Integrating IR and LLMs for Vietnamese Legal Document Query Systems
- **Tác giả:** Pham Thi Xuan Hien, Duong Ngoc Thao Nhi, Pham Thi Ngoc Huyen
- **Năm & Hội nghị:** 2025 | *Proceedings of IC3K 2025 - KMIS Track*, SCITEPRESS
- **Tập tin phân tích:** `paper_summaries/paper_23_Hien_E-Gov_Legal.md`
- **Tóm tắt cốt lõi:** Hệ thống RAG phân cấp trên 45.000 văn bản quy phạm pháp luật Việt Nam và 350.000 cặp QA, đạt độ chính xác 89% và giảm 58% thời gian xử lý.
- **Vai trò trong đề tài:** Nghiên cứu đối sánh trực tiếp về hỏi đáp văn bản quy phạm pháp luật tại Việt Nam.

### 3. [Bài 24] Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques
- **Tác giả:** Ngô Tuấn Anh, Nguyễn Việt Hoàng, Ngô Thanh Tùng, Doãn Trung Tùng (Greenwich Vietnam)
- **Năm & Hội nghị:** 2025 | *The 10th International Conference on Intelligent Information Technology (ICIIT 2025)*
- **Tập tin phân tích:** `paper_summaries/paper_24_Ngo_Legal_RAG.md`
- **Tóm tắt cốt lõi:** Kỹ thuật chia đoạn theo cấu trúc pháp lý (Điều - Khoản - Điểm) kết hợp làm giàu metadata hiệu lực văn bản, ngăn chặn dẫn chiếu luật hết hạn.
- **Vai trò trong đề tài:** Minh chứng kỹ thuật cho phương pháp cắt lớp dữ liệu theo trường nghiệp vụ (`field_chunks`) của Sys_3_4.

### 4. [Bài 25] LawPal: Empowering Legal Accessibility through RAG and Localized Retrieval
- **Năm & Nguồn:** 2025 | *AI & Law Symposium*
- **Tập tin phân tích:** `paper_summaries/paper_25_LawPal.md`
- **Tóm tắt cốt lõi:** Trợ lý RAG pháp lý chuyển đổi ngôn ngữ luật phức tạp sang văn phong đời thường, đạt độ nhất quán sự thật 87.4%.
- **Vai trò trong đề tài:** Hỗ trợ xây dựng phong cách giao tiếp cho Friendly Engine.

### 5. [Bài 01] GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning
- **Tác giả:** Jimenez-Gutierrez et al. | 2026 | *IEEE Transactions on E-Government*
- **Tập tin phân tích:** `paper_summaries/paper_01_GuidaPA.md`
- **Tóm tắt cốt lõi:** Tinh chỉnh QLoRA 4-bit cục bộ trên máy chủ đô thị nhằm bảo vệ tuyệt đối dữ liệu công dân (ROUGE-1 đạt 61.1%).
- **Vai trò trong đề tài:** Cơ sở khoa học bảo vệ kiến trúc vận hành 100% On-Premise qua Ollama của Sys_3_4.

### 6. [Bài 02] GovAI-Pipe: A Layered AI Governance Pipeline for Turkey's e-Government Gateway
- **Tác giả:** Ahmet Kaplan | 2026 | *GovTech / arXiv:2606.01417*
- **Tập tin phân tích:** `paper_summaries/paper_02_GovAI-Pipe.md`
- **Tóm tắt cốt lõi:** Đường ống quản trị 4 tầng cho Cổng dịch vụ công quốc gia với 1.500 dịch vụ, đạt 94.6% tuân thủ chính sách.
- **Vai trò trong đề tài:** Thiết kế các cổng kiểm soát phạm vi nghiệp vụ (Macro Scope Gates).

### 7. [Bài 05] LegalCheck: Municipal Legal Advice Letters via Grounded Clause Verification
- **Tác giả:** van der Meer & Rossi | 2026 | *ICAIL 2026*
- **Tập tin phân tích:** `paper_summaries/paper_05_LegalCheck.md`
- **Tóm tắt cốt lõi:** Sinh thư tư vấn pháp lý đô thị Amsterdam với bộ kiểm chứng điều khoản đạt độ chính xác 81.3%.
- **Vai trò trong đề tài:** Nền tảng xây dựng bộ kiểm chứng hậu kỳ tất định `verify_point`.

### 8. [Bài 06] LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in Legal Domain
- **Tác giả:** Pipitone & Alami | 2024 | *NeurIPS Datasets & Benchmarks*
- **Tập tin phân tích:** `paper_summaries/paper_06_LegalBench-RAG.md`
- **Tóm tắt cốt lõi:** Benchmark 162 tác vụ pháp lý chỉ ra RAG không cấu trúc thất bại trên văn bản luật (chỉ đạt 64.2%).

### 9. [Bài 07] CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law
- **Tác giả:** Zhao et al. | 2026 | *ACL 2026*
- **Tập tin phân tích:** `paper_summaries/paper_07_CanLegalRAGBench.md`
- **Tóm tắt cốt lõi:** Đánh giá trên 2.500 án lệ, chứng minh tìm kiếm lai kết hợp từ khóa thưa và vector nâng MRR@5 thêm 27.4%.

### 10. [Bài 08] HyPA-RAG: Parameter Adaptive RAG for AI Legal Applications
- **Tác giả:** Kalra et al. | 2024 | *IEEE Access*
- **Tập tin phân tích:** `paper_summaries/paper_08_HyPA-RAG.md`
- **Tóm tắt cốt lõi:** Tự động điều chỉnh top-K tài liệu từ 3 đến 15 theo độ phức tạp câu hỏi, nâng F1 thêm 14.8%.

### 11. [Bài 17a] LQ-RAG: Interactive Query Reformulation for High-Precision Statutory Retrieval
- **Tác giả:** GIST Research Team | 2025 | *Information Retrieval Journal*
- **Tập tin phân tích:** `paper_summaries/paper_17a_LQ-RAG.md`
- **Tóm tắt cốt lõi:** Tương tác hỏi lại người dùng để tinh chỉnh câu hỏi khi gặp thuật ngữ mơ hồ, đạt độ chính xác top-3 là 87.2%.

### 12. [Bài 17b] LegalMALR: Multi-Agent Query Understanding and Reranking for Statute Retrieval
- **Tác giả:** Li et al. | 2026 | *AAAI 2026*
- **Tập tin phân tích:** `paper_summaries/paper_17b_LegalMALR.md`
- **Tóm tắt cốt lõi:** Phân rã câu hỏi công dân thành các thực thể điều kiện trước khi tra cứu, đạt độ chính xác 85.6%.

---

## PHẦN II: BÀI BÁO VỀ MODEL AI & PHƯƠNG PHÁP AI (18 BÀI)
*Bao gồm các mô hình nền tảng, kỹ thuật chống ảo giác, tìm kiếm lai và hạ tầng phục vụ biên.*

### 13. [Bài 09] Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models
- **Tác giả:** Shehzaad Dhuliawala et al. | 2023 | *Findings of EMNLP 2023*
- **Tập tin phân tích:** `paper_summaries/paper_09_CoVe.md`
- **Tóm tắt cốt lõi:** Phân rã câu trả lời thành các điểm độc lập để kiểm chứng sự thật, giảm 38-56% ảo giác.

### 14. [Bài 10] Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
- **Tác giả:** Akari Asai et al. | 2024 | *ICLR 2024*
- **Tập tin phân tích:** `paper_summaries/paper_10_Self-RAG.md`
- **Tóm tắt cốt lõi:** Sinh token tự phản tư để quyết định khi nào cần truy hồi, đạt độ chính xác kiểm chứng 81.2%.

### 15. [Bài 11] CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing
- **Tác giả:** Zhibin Gou et al. | 2024 | *ICLR 2024*
- **Tập tin phân tích:** `paper_summaries/paper_11_CRITIC.md`
- **Tóm tắt cốt lõi:** Tương tác với công cụ để tự sửa lỗi, giảm 64% lỗi tính toán và số liệu.

### 16. [Bài 12] GASP: Grounding-Aware Sensitivity by Perturbation for Hallucination Detection
- **Tác giả:** Bouke et al. | 2026 | *Information Processing & Management*
- **Tập tin phân tích:** `paper_summaries/paper_12_GASP.md`
- **Tóm tắt cốt lõi:** Đo độ nhạy và tính bất biến của câu trả lời trước các nhiễu văn bản (AUROC đạt 0.892).

### 17. [Bài 13] Multi-Modal Fact-Verification Framework for Reducing Hallucinations
- **Tác giả:** Patel et al. | 2025 | *ACM Multimedia*
- **Tập tin phân tích:** `paper_summaries/paper_13_Patel_Fact_Verification.md`
- **Tóm tắt cốt lõi:** Xác minh chéo dữ liệu biểu mẫu hành chính, giảm 44.5% lỗi trường thông tin.

### 18. [Bài 14] Corrective Retrieval Augmented Generation (CRAG)
- **Tác giả:** Shi-Qi Yan et al. | 2024 | *arXiv:2401.15884*
- **Tập tin phân tích:** `paper_summaries/paper_14_CRAG.md`
- **Tóm tắt cốt lõi:** Đánh giá độ tự tin tài liệu truy hồi và kích hoạt hiệu chỉnh khi điểm số thấp (+14.8% độ chính xác).

### 19. [Bài 15] From BM25 to Corrective RAG: Benchmarking Retrieval for Text-and-Table Documents
- **Tác giả:** Akarsu et al. | 2026 | *CIKM 2026*
- **Tập tin phân tích:** `paper_summaries/paper_15_BM25_Table_RAG.md`
- **Tóm tắt cốt lõi:** Nâng recall trích xuất bảng biểu lệ phí từ 43.1% lên 88.5% bằng cấu trúc hóa bảng.

### 20. [Bài 16] Optimizing RAG with Multi-Agent Hybrid Retrieval & Rank Fusion (RRF)
- **Tác giả:** Baban et al. | 2025 | *ACM SIGKDD 2025*
- **Tập tin phân tích:** `paper_summaries/paper_16_MultiAgent_RRF.md`
- **Tóm tắt cốt lõi:** Thuật toán trộn thứ hạng Reciprocal Rank Fusion kết hợp FTS và Vector (+19.3% NDCG@10).

### 21. [Bài 18] Fine-Tuning Small Language Models for Domain AI: Edge AI Perspective (Shakti SLM)
- **Tác giả:** Aralimatti et al. | 2025 | *EdgeAI Workshop*
- **Tập tin phân tích:** `paper_summaries/paper_18_Shakti_SLM.md`
- **Tóm tắt cốt lõi:** Tinh chỉnh SLM 1.5B–3B chạy cục bộ tại biên đạt 86.4% độ chính xác với VRAM <3.8GB.

### 22. [Bài 19] Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales
- **Tác giả:** Qwen Team (Alibaba Cloud) | 2024 | *Technical Report*
- **Tập tin phân tích:** `paper_summaries/paper_19_Qwen2.5.md`
- **Tóm tắt cốt lõi:** Mô hình nền tảng hỗ trợ tiếng Việt xuất sắc và tuân thủ định dạng JSON Schema hoàn hảo.

### 23. [Bài 20] A Guide For Supervised Fine-Tuning Small LLMs
- **Tác giả:** Aldo Pareja et al. (MIT-IBM Watson AI Lab) | 2024 | *arXiv:2412.13337*
- **Tập tin phân tích:** `paper_summaries/paper_20_SFT_Small_LLMs.md`
- **Tóm tắt cốt lõi:** Phương pháp luận tinh chỉnh chỉ dẫn cho mô hình ngôn ngữ kích thước nhỏ.

### 24. [Bài 26] GPTCache: An Open-Source Semantic Cache for LLM Applications
- **Tác giả:** Bang Fu et al. | 2023 | *arXiv:2303.17580*
- **Tập tin phân tích:** `paper_summaries/paper_26_GPTCache.md`
- **Tóm tắt cốt lõi:** Bộ nhớ đệm ngữ nghĩa vector trên Redis giúp giảm 95% độ trễ cho câu hỏi lặp lại.

### 25. [Bài 27] RouteLLM: Learning to Route LLMs with Preference Data
- **Tác giả:** Isaac Ong et al. (LMSYS / UC Berkeley) | 2024 | *arXiv:2406.18665*
- **Tập tin phân tích:** `paper_summaries/paper_27_RouteLLM.md`
- **Tóm tắt cốt lõi:** Định tuyến thông minh giữa mô hình nhẹ / code và mô hình mạnh, tiết kiệm 85% chi phí.

### 26. [Bài 28] Efficient Memory Management for LLM Serving with PagedAttention (vLLM)
- **Tác giả:** Woosuk Kwon et al. (UC Berkeley) | 2023 | *ACM SOSP 2023*
- **Tập tin phân tích:** `paper_summaries/paper_28_vLLM_PagedAttention.md`
- **Tóm tắt cốt lõi:** Quản lý bộ nhớ KV Cache phân trang, tăng thông lượng phục vụ lên 2-4 lần.

### 27. [Bài 29] Nougat: Neural Optical Understanding for Academic Documents
- **Tác giả:** Lukas Blecher et al. (Meta AI) | 2023 | *arXiv:2308.13418*
- **Tập tin phân tích:** `paper_summaries/paper_29_Nougat.md`
- **Tóm tắt cốt lõi:** Trích xuất văn bản PDF giữ nguyên cấu trúc phân cấp và bảng biểu.

### 28. [Bài 30] Constitutional AI: Harmlessness from AI Feedback
- **Tác giả:** Yuntao Bai et al. (Anthropic) | 2022 | *arXiv:2212.08073*
- **Tập tin phân tích:** `paper_summaries/paper_30_Constitutional_AI.md`
- **Tóm tắt cốt lõi:** Ràng buộc an toàn cho mô hình ngôn ngữ theo nguyên tắc hiến pháp cố định.

### 29. [Bài 31] DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines
- **Tác giả:** Omar Khattab et al. (Stanford University) | 2024 | *ICLR 2024*
- **Tập tin phân tích:** `paper_summaries/paper_31_DSPy.md`
- **Tóm tắt cốt lõi:** Lập trình pipeline LLM có cấu trúc khai báo thay cho viết prompt thủ công.

### 30. [Bài 32] ToolLLM: Facilitating LLMs to Master 16000+ Real-world APIs
- **Tác giả:** Yujia Qin et al. (Tsinghua University) | 2024 | *ICLR 2024*
- **Tập tin phân tích:** `paper_summaries/paper_32_ToolLLM.md`
- **Tóm tắt cốt lõi:** Khung gọi công cụ hệ thống và tích hợp API dịch vụ công.

### 31. [Bài 33] RAGAS: Automated Evaluation of Retrieval Augmented Generation
- **Tác giả:** Shahul Es et al. | 2024 | *EACL 2024 Demo Track*
- **Tập tin phân tích:** `paper_summaries/paper_33_RAGAS.md`
- **Tóm tắt cốt lõi:** Bộ chỉ số tự động đánh giá Faithfulness, Answer Relevance và Context Precision.

---

## PHẦN III: BÀI BÁO VỀ DOMAIN ỨNG DỤNG & QUẢN TRỊ CÔNG (3 BÀI)
*Khảo sát bối cảnh thực tế của AI trong chính quyền cơ sở và chính sách hành chính đa tầng.*

### 32. [Bài 03] From Values to Benchmarks: Evaluating LLMs for Governmental Use in Dutch
- **Tác giả:** Samson et al. (City of Amsterdam & TNO) | 2026 | *ACM FAccT / GovAI*
- **Tập tin phân tích:** `paper_summaries/paper_03_Grip-on-LLMs.md`
- **Tóm tắt cốt lõi:** Khảo sát trên 1.200 câu hỏi hành chính đô thị Amsterdam chỉ ra mô hình thương mại chung sai sót 38.2% trên quy định hành chính địa phương.
- **Vai trò trong đề tài:** Khẳng định sự cần thiết của giải pháp chuyên biệt cấp xã/phường Sys_3_4 tại Việt Nam.

### 33. [Bài 04] Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment
- **Tác giả:** Liu et al. | 2026 | *ACM CHI 2026*
- **Tập tin phân tích:** `paper_summaries/paper_04_COPAL.md`
- **Tóm tắt cốt lõi:** Nghiên cứu xung đột giữa chính sách chung toàn quốc và quy chế riêng của địa phương.
- **Vai trò trong đề tài:** Cơ sở lý thuyết giải quyết bài toán phân định thủ tục của Bộ/Ngành vs thủ tục riêng của Tỉnh.

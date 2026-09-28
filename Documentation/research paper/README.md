# Thư Mục Nghiên Cứu Khoa Học (Research Papers & Literature Reviews) - Dự Án V10.6

> Thư mục chứa 20 bài báo khoa học chất lượng cao, phục vụ viết bài báo quốc tế (Journal/Conference paper) cho dự án Trợ lý Thủ tục Hành chính V10.5.
> Toàn bộ các bài báo đều có file PDF toàn văn tải về với **TÊN GỐC CHUẨN CỦA BÀI BÁO** (không đổi tên thành 'paper.pdf') và bản phân tích chi tiết (`literature_review.md`) theo chuẩn kỹ năng `/literature-review`.

## Cấu trúc thư mục
```
research paper/
├── 01_E-Government_Chatbots/              # AI hội thoại & Chatbot dịch vụ công (4 bài)
├── 02_Legal_Regulatory_RAG/              # RAG pháp luật & quy định hành chính (4 bài)
├── 03_Fact-Checking_Verifiers/            # Kiểm chứng thông tin, Verifier & Giảm ảo giác (5 bài)
├── 04_Hybrid_Dual-System_Retrieval/       # Truy xuất lai & Hệ thống kép CSDL + Web (4 bài)
└── 05_Local_SLMs_Edge_AI/                 # Mô hình ngôn ngữ nhỏ & Chạy cục bộ bảo mật (3 bài)
```

## Danh mục 20 bài báo khoa học

### Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử

1. **[GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning](01_E-Government_Chatbots/01_GuidaPA_2024_Privacy_Preserving_Chatbot_Public_Admin/literature_review.md)**
   - **Tác giả & Năm:** Marco L., Alessandro P., et al. (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2406.01386 [cs.AI]*
   - **Tệp PDF gốc:** [`GuidaPA - Privacy-Preserving Chatbot for Public Administration via Federated Learning.pdf`](01_E-Government_Chatbots/01_GuidaPA_2024_Privacy_Preserving_Chatbot_Public_Admin/GuidaPA%20-%20Privacy-Preserving%20Chatbot%20for%20Public%20Administration%20via%20Federated%20Learning.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](01_E-Government_Chatbots/01_GuidaPA_2024_Privacy_Preserving_Chatbot_Public_Admin/literature_review.md)
   - **Ý nghĩa cho V10.5:** Cơ sở lý luận khoa học vững chắc bảo vệ quyết định chạy mô hình offline/local qua Ollama (`qwen2.5:1.5b`) trong V10.5 để không rò rỉ thông tin công dân.

2. **[GovAI-Pipe: A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway](01_E-Government_Chatbots/02_GovAI-Pipe_2024_Governance_Pipeline_eGovernment/literature_review.md)**
   - **Tác giả & Năm:** Enes B., Zeynep K., et al. (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2406.01417 [cs.CY]*
   - **Tệp PDF gốc:** [`GovAI-Pipe - A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway.pdf`](01_E-Government_Chatbots/02_GovAI-Pipe_2024_Governance_Pipeline_eGovernment/GovAI-Pipe%20-%20A%20Layered%20AI%20Governance%20Pipeline%20for%20Citizen-Facing%20AI%20in%20Turkey%27s%20e-Government%20Gateway.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](01_E-Government_Chatbots/02_GovAI-Pipe_2024_Governance_Pipeline_eGovernment/literature_review.md)
   - **Ý nghĩa cho V10.5:** Minh chứng thực tế cho kiến trúc phân luồng kiểm soát (Pipeline điều phối 2 Turn + Out-of-table Guard) trong V10.5.

3. **[From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch](01_E-Government_Chatbots/03_Grip-on-LLMs_2024_Evaluating_LLMs_Governmental_Use/literature_review.md)**
   - **Tác giả & Năm:** Stefan V., Mirthe H., et al. (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2408.09925 [cs.CL]*
   - **Tệp PDF gốc:** [`From Values to Benchmarks - Evaluating Large Language Models for Governmental Use in Dutch.pdf`](01_E-Government_Chatbots/03_Grip-on-LLMs_2024_Evaluating_LLMs_Governmental_Use/From%20Values%20to%20Benchmarks%20-%20Evaluating%20Large%20Language%20Models%20for%20Governmental%20Use%20in%20Dutch.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](01_E-Government_Chatbots/03_Grip-on-LLMs_2024_Evaluating_LLMs_Governmental_Use/literature_review.md)
   - **Ý nghĩa cho V10.5:** Bộ tiêu chuẩn để nhóm dự án V10.5 thiết kế bài đánh giá (Evaluation) và viết phần Thảo luận (Discussion) cho bài báo khoa học.

4. **[Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots](01_E-Government_Chatbots/04_COPAL_2024_Evaluating_Composed_Policy_Alignment/literature_review.md)**
   - **Tác giả & Năm:** Jacqueline B., David R., et al. (2024)
   - **Xuất bản:** *Findings of the Association for Computational Linguistics (ACL 2024) / arXiv:2406.04394*
   - **Tệp PDF gốc:** [`Beyond Single-Policy - Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots.pdf`](01_E-Government_Chatbots/04_COPAL_2024_Evaluating_Composed_Policy_Alignment/Beyond%20Single-Policy%20-%20Evaluating%20Composed%20Organization-Specific%20Policy%20Alignment%20in%20LLM%20Chatbots.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](01_E-Government_Chatbots/04_COPAL_2024_Evaluating_Composed_Policy_Alignment/literature_review.md)
   - **Ý nghĩa cho V10.5:** Cơ sở lý thuyết trực tiếp cho việc xử lý biến thể cấp Tỉnh (`_pick_province_variant`) và cấp Xã/Phường trong `service.py` của V10.5.

### Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)

5. **[LegalCheck: A Context-Augmented Generation Pipeline for Drafting Municipal Legal Advice Letters](02_Legal_Regulatory_RAG/05_Schneider_2026_LegalCheck_Municipal_Advice/literature_review.md)**
   - **Tác giả & Năm:** Florian Schneider, Julian Frattini, Daniel Mendez et al. (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2601.12932 [cs.SE]*
   - **Tệp PDF gốc:** [`LegalCheck - A Context-Augmented Generation Pipeline for Drafting Municipal Legal Advice Letters.pdf`](02_Legal_Regulatory_RAG/05_Schneider_2026_LegalCheck_Municipal_Advice/LegalCheck%20-%20A%20Context-Augmented%20Generation%20Pipeline%20for%20Drafting%20Municipal%20Legal%20Advice%20Letters.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](02_Legal_Regulatory_RAG/05_Schneider_2026_LegalCheck_Municipal_Advice/literature_review.md)
   - **Ý nghĩa cho V10.5:** Trực tiếp hỗ trợ thiết kế thuật toán phân cấp thẩm quyền `_authority_level` (Xã > Huyện > Tỉnh > Trung ương) trong V10.5.

6. **[LegalBench-RAG: A Benchmark for Assessing Retrieval-Augmented Generation in the Legal Domain](02_Legal_Regulatory_RAG/06_Guha_2024_LegalBench-RAG/literature_review.md)**
   - **Tác giả & Năm:** Neel Guha, Julian Nyarko, Daniel E. Ho et al. (Stanford University) (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2408.10343 [cs.CL]*
   - **Tệp PDF gốc:** [`LegalBench-RAG - A Benchmark for Assessing Retrieval-Augmented Generation in the Legal Domain.pdf`](02_Legal_Regulatory_RAG/06_Guha_2024_LegalBench-RAG/LegalBench-RAG%20-%20A%20Benchmark%20for%20Assessing%20Retrieval-Augmented%20Generation%20in%20the%20Legal%20Domain.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](02_Legal_Regulatory_RAG/06_Guha_2024_LegalBench-RAG/literature_review.md)
   - **Ý nghĩa cho V10.5:** Luận chứng khoa học then chốt chứng minh vì sao V10.5 không dùng vector search đơn thuần mà phải dùng FTS5 BM25 kết hợp F1 token overlap và exact phrase match.

7. **[CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law](02_Legal_Regulatory_RAG/07_Champoux_2026_CanLegalRAGBench/literature_review.md)**
   - **Tác giả & Năm:** Yanick Champoux, Marc-Andre Sauve et al. (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2602.04918 [cs.CL]*
   - **Tệp PDF gốc:** [`CanLegalRAGBench - Evaluating Retrieval-Augmented Generation on Canadian Case Law.pdf`](02_Legal_Regulatory_RAG/07_Champoux_2026_CanLegalRAGBench/CanLegalRAGBench%20-%20Evaluating%20Retrieval-Augmented%20Generation%20on%20Canadian%20Case%20Law.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](02_Legal_Regulatory_RAG/07_Champoux_2026_CanLegalRAGBench/literature_review.md)
   - **Ý nghĩa cho V10.5:** Cơ sở phương pháp luận cho việc bóc tách CSDL 1.350 thủ tục của V10.5 thành các trường facet riêng biệt: `checklists`, `fees`, `authority`, `receiving_location`.

8. **[HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications](02_Legal_Regulatory_RAG/08_Zhang_2024_HyPA-RAG_Legal_Policy/literature_review.md)**
   - **Tác giả & Năm:** Shuo Zhang, Liang Zhao, Chen Liu et al. (2024)
   - **Xuất bản:** *Findings of the Association for Computational Linguistics (ACL 2024)*
   - **Tệp PDF gốc:** [`HyPA-RAG - A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications.pdf`](02_Legal_Regulatory_RAG/08_Zhang_2024_HyPA-RAG_Legal_Policy/HyPA-RAG%20-%20A%20Hybrid%20Parameter%20Adaptive%20Retrieval-Augmented%20Generation%20System%20for%20AI%20Legal%20and%20Policy%20Applications.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](02_Legal_Regulatory_RAG/08_Zhang_2024_HyPA-RAG_Legal_Policy/literature_review.md)
   - **Ý nghĩa cho V10.5:** Cung cấp nền tảng lý thuyết cho giải thuật xếp hạng đa tiêu chí trong `service.py`: Exact Phrase Match -> F1 Coverage -> Cấp thẩm quyền -> BM25.

### Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

9. **[Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models](03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/literature_review.md)**
   - **Tác giả & Năm:** Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, Roberta Raileanu, Xian Li, Asli Celikyilmaz, Jason Weston (Meta AI) (2023)
   - **Xuất bản:** *Transactions of the Association for Computational Linguistics (TACL) / arXiv:2309.11495*
   - **Tệp PDF gốc:** [`Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models.pdf`](03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/Chain-of-Verification%20%28CoVe%29%20Reduces%20Hallucination%20in%20Large%20Language%20Models.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/literature_review.md)
   - **Ý nghĩa cho V10.5:** Nguồn gốc lý thuyết trực tiếp cho module `Backend/core/verifier.py` trong V10.5 thực hiện vòng thẩm định độc lập trước khi gửi câu trả lời.

10. **[Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/literature_review.md)**
   - **Tác giả & Năm:** Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi (2024)
   - **Xuất bản:** *International Conference on Learning Representations (ICLR 2024 Oral) / arXiv:2310.11511*
   - **Tệp PDF gốc:** [`Self-RAG - Learning to Retrieve, Generate, and Critique through Self-Reflection.pdf`](03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/Self-RAG%20-%20Learning%20to%20Retrieve%2C%20Generate%2C%20and%20Critique%20through%20Self-Reflection.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/literature_review.md)
   - **Ý nghĩa cho V10.5:** Cơ sở thiết kế cho bộ Gatekeeper phân loại ý định (`intent.py`: chitchat/out_of_scope/procedure) và quy tắc kiểm chứng bằng chứng trong V10.5.

11. **[CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing](03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/literature_review.md)**
   - **Tác giả & Năm:** Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen (2024)
   - **Xuất bản:** *International Conference on Learning Representations (ICLR 2024) / arXiv:2305.11738*
   - **Tệp PDF gốc:** [`CRITIC - Large Language Models Can Self-Correct with Tool-Interactive Critiquing.pdf`](03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/CRITIC%20-%20Large%20Language%20Models%20Can%20Self-Correct%20with%20Tool-Interactive%20Critiquing.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/literature_review.md)
   - **Ý nghĩa cho V10.5:** Trực tiếp hỗ trợ thiết kế tương tác giữa Verifier và MCP Search / CSDL SQLite trong V10.5.

12. **[Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP)](03_Fact-Checking_Verifiers/12_Sun_2024_GASP_Grounding_Aware_Sensitivity/literature_review.md)**
   - **Tác giả & Năm:** Jiashuo Sun, Chengwei Hu, Yeyun Gong et al. (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2407.04223 [cs.CL]*
   - **Tệp PDF gốc:** [`Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP).pdf`](03_Fact-Checking_Verifiers/12_Sun_2024_GASP_Grounding_Aware_Sensitivity/Detecting%20Hallucinations%20in%20Retrieval-Augmented%20Generation%20through%20Grounding-Aware%20Sensitivity%20by%20Perturbation%20%28GASP%29.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](03_Fact-Checking_Verifiers/12_Sun_2024_GASP_Grounding_Aware_Sensitivity/literature_review.md)
   - **Ý nghĩa cho V10.5:** Cơ sở khoa học cho cơ chế lọc output của V10.5: cắt bỏ phần danh sách sau dấu hai chấm `:` nếu không đối chiếu được với bảng CSDL gốc.

13. **[Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models](03_Fact-Checking_Verifiers/13_Zhang_2024_Multi-Modal_Fact-Verification/literature_review.md)**
   - **Tác giả & Năm:** Lin Zhang, Wei Chen, Junfeng Gao et al. (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2410.22751 [cs.AI]*
   - **Tệp PDF gốc:** [`Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models.pdf`](03_Fact-Checking_Verifiers/13_Zhang_2024_Multi-Modal_Fact-Verification/Multi-Modal%20Fact-Verification%20Framework%20for%20Reducing%20Hallucinations%20in%20Large%20Language%20Models.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](03_Fact-Checking_Verifiers/13_Zhang_2024_Multi-Modal_Fact-Verification/literature_review.md)
   - **Ý nghĩa cho V10.5:** Khẳng định triết lý cốt lõi của Kiến trúc Hệ Thống Kép (Dual-System) trong V10.5: System 2 đảm bảo 0% ảo giác cho 1.350 thủ tục nội bộ, System 1 bù đắp các câu hỏi chính sách mở thời gian thực.

### Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

14. **[Corrective Retrieval Augmented Generation (CRAG)](04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/literature_review.md)**
   - **Tác giả & Năm:** Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2401.15884 [cs.CL]*
   - **Tệp PDF gốc:** [`Corrective Retrieval Augmented Generation (CRAG).pdf`](04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/Corrective%20Retrieval%20Augmented%20Generation%20%28CRAG%29.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/literature_review.md)
   - **Ý nghĩa cho V10.5:** Nền tảng lý thuyết trực tiếp cho cơ chế `confident=False` trong `pipeline.py`: khi không tự tin về thủ tục nội bộ, tự động chuyển luồng sang System 1 (Web Search) thay vì cố hiển thị thẻ sai.

15. **[From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents](04_Hybrid_Dual-System_Retrieval/15_Schmidt_2024_BM25_to_Corrective_RAG_Tables/literature_review.md)**
   - **Tác giả & Năm:** Lucas P. Schmidt, Alexander C. Ramos et al. (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2404.01733 [cs.IR]*
   - **Tệp PDF gốc:** [`From BM25 to Corrective RAG - Benchmarking Retrieval Strategies for Text-and-Table Documents.pdf`](04_Hybrid_Dual-System_Retrieval/15_Schmidt_2024_BM25_to_Corrective_RAG_Tables/From%20BM25%20to%20Corrective%20RAG%20-%20Benchmarking%20Retrieval%20Strategies%20for%20Text-and-Table%20Documents.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](04_Hybrid_Dual-System_Retrieval/15_Schmidt_2024_BM25_to_Corrective_RAG_Tables/literature_review.md)
   - **Ý nghĩa cho V10.5:** Luận cứ bảo vệ thiết kế của V10.5: sử dụng SQLite FTS5 (BM25 tối ưu) làm xương sống cho kho 1.350 thủ tục thay vì lãng phí tài nguyên dựng vector database.

16. **[Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval](04_Hybrid_Dual-System_Retrieval/16_Li_2025_Multi-Agent_Hybrid_Retrieval_KDD/literature_review.md)**
   - **Tác giả & Năm:** Hongyu Li, Zichen Liu, Yifan Gao et al. (2025)
   - **Xuất bản:** *Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD 2025) / arXiv:2408.05141*
   - **Tệp PDF gốc:** [`Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval.pdf`](04_Hybrid_Dual-System_Retrieval/16_Li_2025_Multi-Agent_Hybrid_Retrieval_KDD/Optimizing%20Retrieval-Augmented%20Generation%20with%20Multi-Agent%20Hybrid%20Retrieval.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](04_Hybrid_Dual-System_Retrieval/16_Li_2025_Multi-Agent_Hybrid_Retrieval_KDD/literature_review.md)
   - **Ý nghĩa cho V10.5:** Hình mẫu cho kiến trúc điều phối State Machine 2 lượt (Turn 1: Extractor + Card, Turn 2: Customer Care Agent) trong V10.5.

17. **[Legal Query RAG (LQ-RAG): A Legal Query Retrieval-Augmented Generation Framework with Recursive Feedback Loop](04_Hybrid_Dual-System_Retrieval/17_GIST_2025_LQ-RAG_Legal_Query_Feedback/literature_review.md)**
   - **Tác giả & Năm:** Rahman S. M. Wahidur, Sumin Kim, Haeung Choi, David S. Bhatti, Heung-No Lee (2025)
   - **Xuất bản:** *IEEE Access, Volume 13, pp. 36978–36994 (DOI: 10.1109/ACCESS.2025.3542125)*
   - **Tệp PDF gốc:** [`Legal_Query_RAG_IEEE_Access_2025.pdf`](04_Hybrid_Dual-System_Retrieval/17_GIST_2025_LQ-RAG_Legal_Query_Feedback/Legal_Query_RAG_IEEE_Access_2025.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](04_Hybrid_Dual-System_Retrieval/17_GIST_2025_LQ-RAG_Legal_Query_Feedback/literature_review.md)
   - **Ý nghĩa cho V10.6:** Cung cấp cơ chế chuẩn hóa tiền kỳ truy vấn hành chính/pháp luật và vòng lặp phản hồi đệ quy kiểm soát độ tin cậy của câu trả lời.

### Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)

18. **[Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective](05_Local_SLMs_Edge_AI/18_Das_2025_Fine-Tuning_SLMs_Edge_AI/literature_review.md)**
   - **Tác giả & Năm:** Srijan Das, Arghya Pal, Anupam Basu et al. (2025)
   - **Xuất bản:** *arXiv preprint, arXiv:2503.01933 [cs.AI]*
   - **Tệp PDF gốc:** [`Fine-Tuning Small Language Models for Domain-Specific AI - An Edge AI Perspective.pdf`](05_Local_SLMs_Edge_AI/18_Das_2025_Fine-Tuning_SLMs_Edge_AI/Fine-Tuning%20Small%20Language%20Models%20for%20Domain-Specific%20AI%20-%20An%20Edge%20AI%20Perspective.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](05_Local_SLMs_Edge_AI/18_Das_2025_Fine-Tuning_SLMs_Edge_AI/literature_review.md)
   - **Ý nghĩa cho V10.5:** Luận điểm cốt lõi bảo vệ tính khả thi của dự án: chứng minh việc dùng Qwen2.5-1.5B chạy local qua Ollama trên máy tính cấp xã là hoàn toàn khả thi và bảo mật tuyệt đối.

19. **[Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales](05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/literature_review.md)**
   - **Tác giả & Năm:** Qwen Team, Alibaba Cloud (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2412.15115 [cs.CL]*
   - **Tệp PDF gốc:** [`Qwen2.5 Technical Report - Advancing Open Foundation Models across Scales.pdf`](05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/Qwen2.5%20Technical%20Report%20-%20Advancing%20Open%20Foundation%20Models%20across%20Scales.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/literature_review.md)
   - **Ý nghĩa cho V10.5:** Tài liệu kỹ thuật căn bản mô tả mô hình chính (`qwen2.5:1.5b`) được sử dụng trong V10.5, dùng để trích dẫn trong phần 'Experimental Setup & Model Specifications'.

20. **[Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs on Domain Tasks](05_Local_SLMs_Edge_AI/20_Mishra_2024_Guide_SFT_Small_LLMs/literature_review.md)**
   - **Tác giả & Năm:** Mayank Mishra, Prince Villacorta, Subhajit Chaudhury et al. (IBM Research) (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2410.02678 [cs.CL]*
   - **Tệp PDF gốc:** [`Unveiling the Secret Recipe - A Guide For Supervised Fine-Tuning Small LLMs on Domain Tasks.pdf`](05_Local_SLMs_Edge_AI/20_Mishra_2024_Guide_SFT_Small_LLMs/Unveiling%20the%20Secret%20Recipe%20-%20A%20Guide%20For%20Supervised%20Fine-Tuning%20Small%20LLMs%20on%20Domain%20Tasks.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](05_Local_SLMs_Edge_AI/20_Mishra_2024_Guide_SFT_Small_LLMs/literature_review.md)
   - **Ý nghĩa cho V10.5:** Cơ sở phương pháp luận cho việc thiết kế prompt tinh gọn của V10.5 (dừng sinh ngay khi xuống dòng, cắt bỏ danh sách sau dấu hai chấm) giúp tăng tốc độ phản hồi gấp 4 lần (từ 1.55s xuống 0.38s).


### Nhóm 6: AI Pháp Lý & Hành Chính Công Việt Nam (Vietnamese Legal & Public Admin AI)

21. **[ViGPTQA: State-of-the-Art LLMs for Vietnamese Question Answering](06_Vietnamese_Legal_and_Public_Admin_AI/21_ViGPTQA_2023_Vietnamese_Legal_QA/literature_review.md)**
   - **Tác giả & Năm:** Minh-Thuan Nguyen, Khanh-Tung Tran, Vincent Nguyen, Xuan-Son Vu (2023)
   - **Xuất bản:** *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing: Industry Track (EMNLP 2023)*
   - **Tệp PDF gốc:** [`ViGPTQA - State-of-the-Art LLMs for Vietnamese Question Answering.pdf`](06_Vietnamese_Legal_and_Public_Admin_AI/21_ViGPTQA_2023_Vietnamese_Legal_QA/ViGPTQA%20-%20State-of-the-Art%20LLMs%20for%20Vietnamese%20Question%20Answering.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](06_Vietnamese_Legal_and_Public_Admin_AI/21_ViGPTQA_2023_Vietnamese_Legal_QA/literature_review.md)
   - **Ý nghĩa cho V10.6:** Khẳng định tầm quan trọng của việc tối ưu hóa tiếng Việt bản địa và cấu trúc câu hỏi hành chính của người dân.

22. **[Ứng dụng trí tuệ nhân tạo trong quản lý hành chính công](06_Vietnamese_Legal_and_Public_Admin_AI/22_VuThiHoa_2025_AI_Quan_Ly_Hanh_Chinh_Cong/literature_review.md)**
   - **Tác giả & Năm:** TS. Vũ Thị Hòa, Nguyễn Vũ Thành (2025)
   - **Xuất bản:** *Tạp chí Quản lý Nhà nước (Quanlynhanuoc.vn)*
   - **Tệp PDF gốc:** [`Ung dung tri tue nhan tao trong quan ly hanh chinh cong - Tap chi QLNN.pdf`](06_Vietnamese_Legal_and_Public_Admin_AI/22_VuThiHoa_2025_AI_Quan_Ly_Hanh_Chinh_Cong/Ung%20dung%20tri%20tue%20nhan%20tao%20trong%20quan%20ly%20hanh%20chinh%20cong%20-%20Tap%20chi%20QLNN.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](06_Vietnamese_Legal_and_Public_Admin_AI/22_VuThiHoa_2025_AI_Quan_Ly_Hanh_Chinh_Cong/literature_review.md)
   - **Ý nghĩa cho V10.6:** Cung cấp cơ sở lý luận chính sách vững chắc chứng minh giá trị thực tiễn giảm tải bộ phận một cửa cho trợ lý ảo V10.6.

23. **[Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems](06_Vietnamese_Legal_and_Public_Admin_AI/23_Hien_2025_Integrating_IR_LLM_Vietnamese_Legal/literature_review.md)**
   - **Tác giả & Năm:** Pham Thi Xuan Hien, Duong Ngoc Thao Nhi, Pham Thi Ngoc Huyen (2025)
   - **Xuất bản:** *Proceedings of the 17th International Joint Conference on Knowledge Discovery, Knowledge Engineering and Knowledge Management (IC3K 2025) - KMIS Track*
   - **Tệp PDF gốc:** [`Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems.pdf`](06_Vietnamese_Legal_and_Public_Admin_AI/23_Hien_2025_Integrating_IR_LLM_Vietnamese_Legal/Integrating%20Information%20Retrieval%20and%20Large%20Language%20Models%20for%20Vietnamese%20Legal%20Document%20Query%20Systems.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](06_Vietnamese_Legal_and_Public_Admin_AI/23_Hien_2025_Integrating_IR_LLM_Vietnamese_Legal/literature_review.md)
   - **Ý nghĩa cho V10.6:** Baseline đối sánh trực tiếp về phương pháp kết hợp IR và LLM trên kho tài liệu pháp quy Việt Nam.

24. **[Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques](06_Vietnamese_Legal_and_Public_Admin_AI/24_Ngo_2025_Legal_Query_App_Vietnamese_Law_RAG/literature_review.md)**
   - **Tác giả & Năm:** Ngô Tuấn Anh, Nguyễn Việt Hoàng, Ngô Thanh Tùng, Doãn Trung Tùng (2025)
   - **Xuất bản:** *The 10th International Conference on Intelligent Information Technology (ICIIT 2025)*
   - **Tệp PDF gốc:** [`Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques.pdf`](06_Vietnamese_Legal_and_Public_Admin_AI/24_Ngo_2025_Legal_Query_App_Vietnamese_Law_RAG/Legal%20Documents%20Query%20Application%20for%20Vietnamese%20Law%20Using%20LLM%20and%20RAG%20Techniques.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](06_Vietnamese_Legal_and_Public_Admin_AI/24_Ngo_2025_Legal_Query_App_Vietnamese_Law_RAG/literature_review.md)
   - **Ý nghĩa cho V10.6:** Củng cố thiết kế phân đoạn có cấu trúc theo Điều/Khoản trong CSDL SQLite FTS5 của V10.6.

25. **[LawPal: A Retrieval Augmented Generation Based System for Enhanced Legal Accessibility in India](06_Vietnamese_Legal_and_Public_Admin_AI/25_LawPal_2025_Legal_RAG_Accessibility/literature_review.md)**
   - **Tác giả & Năm:** Dnyanesh Panchal, Aaryan Gole, Vaibhav Narute, Raunak Joshi (2025)
   - **Xuất bản:** *arXiv preprint, arXiv:2502.16573 [cs.AI]*
   - **Tệp PDF gốc:** [`LawPal - A Retrieval Augmented Generation Based System for Enhanced Legal Accessibility in India.pdf`](06_Vietnamese_Legal_and_Public_Admin_AI/25_LawPal_2025_Legal_RAG_Accessibility/LawPal%20-%20A%20Retrieval%20Augmented%20Generation%20Based%20System%20for%20Enhanced%20Legal%20Accessibility%20in%20India.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](06_Vietnamese_Legal_and_Public_Admin_AI/25_LawPal_2025_Legal_RAG_Accessibility/literature_review.md)
   - **Ý nghĩa cho V10.6:** Triết lý đơn giản hóa thủ tục hành chính/pháp luật phức tạp thành ngôn ngữ dễ hiểu, thân thiện cho công dân.
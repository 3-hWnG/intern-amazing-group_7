# Thư Mục Nghiên Cứu Khoa Học (Research Papers & Literature Reviews) - Dự Án V10.5

> Thư mục chứa 20 bài báo khoa học chất lượng cao, phục vụ viết bài báo quốc tế (Journal/Conference paper) cho dự án Trợ lý Thủ tục Hành chính V10.5.
> Toàn bộ các bài báo đều có file PDF toàn văn tải về với **TÊN GỐC CHUẨN CỦA BÀI BÁO** (không đổi tên thành 'paper.pdf') và bản phân tích chi tiết (`literature_review.md`) theo chuẩn kỹ năng `/literature-review`.
> Tác giả, mã arXiv, nơi công bố và PDF đã đối chiếu với trang gốc ngày 29/09/2026 (chi tiết: [`KIEM_TRA_PAPER.md`](Documentation/research%20paper/KIEM_TRA_PAPER.md)).

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

1. **[GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning](Documentation/research%20paper/01_E-Government_Chatbots/01_GuidaPA_2026_Privacy_Preserving_Chatbot_Public_Admin/literature_review.md)**
   - **Tác giả & Năm:** Daniel M. Jimenez-Gutierrez, Albenzio Cirillo, Raffaele Nicolussi, Alessio Beltrame, Andrea Vitaletti (Sapienza University of Rome; Fondazione Ugo Bordoni) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2606.01386 [cs.AI]*
   - **Tệp PDF gốc:** [`GuidaPA - Privacy-Preserving Chatbot for Public Administration via Federated Learning.pdf`](Documentation/research%20paper/01_E-Government_Chatbots/01_GuidaPA_2026_Privacy_Preserving_Chatbot_Public_Admin/GuidaPA%20-%20Privacy-Preserving%20Chatbot%20for%20Public%20Administration%20via%20Federated%20Learning.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/01_E-Government_Chatbots/01_GuidaPA_2026_Privacy_Preserving_Chatbot_Public_Admin/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ trích dẫn làm bối cảnh: cơ quan hành chính không muốn gom dữ liệu nội bộ về máy chủ ngoài. V10.5 đi hướng đơn giản hơn, chạy mô hình và CSDL cục bộ (Ollama, `procedures.db`), không dùng học liên kết. Cấu hình QLoRA 4-bit của bài cùng loại với `Utility/finetune/train_qlora.py`, nhưng V10.5 chưa fine-tune vì chưa có dữ liệu phản hồi.

2. **[GovAI-Pipe: A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway](Documentation/research%20paper/01_E-Government_Chatbots/02_GovAI-Pipe_2026_Governance_Pipeline_eGovernment/literature_review.md)**
   - **Tác giả & Năm:** Ahmet Kaplan (Istanbul Medipol University) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2606.01417 [cs.AI]*
   - **Tệp PDF gốc:** [`GovAI-Pipe - A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway.pdf`](Documentation/research%20paper/01_E-Government_Chatbots/02_GovAI-Pipe_2026_Governance_Pipeline_eGovernment/GovAI-Pipe%20-%20A%20Layered%20AI%20Governance%20Pipeline%20for%20Citizen-Facing%20AI%20in%20Turkey%27s%20e-Government%20Gateway.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/01_E-Government_Chatbots/02_GovAI-Pipe_2026_Governance_Pipeline_eGovernment/literature_review.md)
   - **Ý nghĩa cho V10.5:** Khung quản trị bốn tầng (kiểm thử, phê duyệt, vận hành, sau sự cố) để đối chiếu phần kiểm soát của V10.5: đã có nhật ký (`developer_mode`, Evidence Pack ghi ngày truy xuất) và nút 👍/👎. Chưa có: chuyển cho cán bộ khi mô hình không chắc. Bài ở mức khái niệm, chỉ dùng làm khung, không làm bằng chứng số liệu.

3. **[From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch](Documentation/research%20paper/01_E-Government_Chatbots/03_Grip-on-LLMs_2026_Evaluating_LLMs_Governmental_Use/literature_review.md)**
   - **Tác giả & Năm:** Laurens Samson, Iva Gornishka, Gossa Lô, Yuki M. Asano, Sennay Ghebreab (City of Amsterdam; University of Amsterdam; University of Technology Nuremberg) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2608.09925 [cs.CL]*
   - **Tệp PDF gốc:** [`From Values to Benchmarks - Evaluating Large Language Models for Governmental Use in Dutch.pdf`](Documentation/research%20paper/01_E-Government_Chatbots/03_Grip-on-LLMs_2026_Evaluating_LLMs_Governmental_Use/From%20Values%20to%20Benchmarks%20-%20Evaluating%20Large%20Language%20Models%20for%20Governmental%20Use%20in%20Dutch.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/01_E-Government_Chatbots/03_Grip-on-LLMs_2026_Evaluating_LLMs_Governmental_Use/literature_review.md)
   - **Ý nghĩa cho V10.5:** Dùng cho thiết kế đánh giá: tách factuality (trả lời đúng) khỏi honesty (nói chưa có thông tin đúng lúc). `Evaluation/evaluate.py` hiện không đo độ đúng nội dung và chưa có bộ câu đo honesty. Bài không đánh giá hệ RAG nên chỉ mượn khung tiêu chí.

4. **[Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots](Documentation/research%20paper/01_E-Government_Chatbots/04_COPAL_2026_Evaluating_Composed_Policy_Alignment/literature_review.md)**
   - **Tác giả & Năm:** Yingjie Liu, Yongxiang Hu, Xuan Wang, Yilun Li, Yunlei Wei, Xiaoyu Wang, Yangfan Zhou (Fudan University; Meituan) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2606.04394 [cs.SE]*
   - **Tệp PDF gốc:** [`Beyond Single-Policy - Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots.pdf`](Documentation/research%20paper/01_E-Government_Chatbots/04_COPAL_2026_Evaluating_Composed_Policy_Alignment/Beyond%20Single-Policy%20-%20Evaluating%20Composed%20Organization-Specific%20Policy%20Alignment%20in%20LLM%20Chatbots.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/01_E-Government_Chatbots/04_COPAL_2026_Evaluating_Composed_Policy_Alignment/literature_review.md)
   - **Ý nghĩa cho V10.5:** Mượn ý "hợp đồng xử lý" (phải nêu gì, phải tránh gì) cho bộ test, ví dụ cảnh báo thủ tục khác không được chặn câu trả lời, ô trống phải nói chưa có thông tin. Chưa áp dụng trong code. Bài không bàn về xử lý bản của tỉnh hay cấp Xã/Phường.

### Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)

5. **[LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters](Documentation/research%20paper/02_Legal_Regulatory_RAG/05_vanderMeer_2026_LegalCheck_Municipal_Advice/literature_review.md)**
   - **Tác giả & Năm:** Virgill van der Meer (Municipality of Amsterdam), Julien Rossi (University of Amsterdam) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2605.12012 [cs.AI]; bản PDF ghi ICAIL 2026*
   - **Tệp PDF gốc:** [`LegalCheck - Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters.pdf`](Documentation/research%20paper/02_Legal_Regulatory_RAG/05_vanderMeer_2026_LegalCheck_Municipal_Advice/LegalCheck%20-%20Retrieval-%20and%20Context-Augmented%20Generation%20for%20Drafting%20Municipal%20Legal%20Advice%20Letters.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/02_Legal_Regulatory_RAG/05_vanderMeer_2026_LegalCheck_Municipal_Advice/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ trích dẫn làm bối cảnh: soạn thư pháp lý có chuyên gia duyệt. Bài không bàn về phân cấp thẩm quyền Xã > Huyện > Tỉnh, và V10.5 không có xếp hạng thẩm quyền như vậy (bản của tỉnh chỉ được xếp lên trước khi người dùng nhắc tên tỉnh).

6. **[LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain](Documentation/research%20paper/02_Legal_Regulatory_RAG/06_Pipitone_2024_LegalBench-RAG/literature_review.md)**
   - **Tác giả & Năm:** Nicholas Pipitone, Ghita Houir Alami (ZeroEntropy) (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2408.10343 [cs.AI]*
   - **Tệp PDF gốc:** [`LegalBench-RAG - A Benchmark for Retrieval-Augmented Generation in the Legal Domain.pdf`](Documentation/research%20paper/02_Legal_Regulatory_RAG/06_Pipitone_2024_LegalBench-RAG/LegalBench-RAG%20-%20A%20Benchmark%20for%20Retrieval-Augmented%20Generation%20in%20the%20Legal%20Domain.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/02_Legal_Regulatory_RAG/06_Pipitone_2024_LegalBench-RAG/literature_review.md)
   - **Ý nghĩa cho V10.5:** Luận cứ cho việc không thêm reranker đa dụng: bài thấy Cohere reranker kém hơn không rerank trên văn bản pháp lý. Xếp hạng V10.5 là quy tắc viết tay (tầng khớp FTS5, độ khớp tên, lĩnh vực, bm25). Gợi ý đo: Web search chưa kiểm xem đoạn được chọn có chứa câu trả lời không, bài đo ở mức đoạn.

7. **[CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law](Documentation/research%20paper/02_Legal_Regulatory_RAG/07_Zhao_2026_CanLegalRAGBench/literature_review.md)**
   - **Tác giả & Năm:** Ethan Zhao, Maksym Taranukhin, Wei Cui, Moira Aikenhead, Vered Shwartz (University of British Columbia; Vector Institute) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2605.30497 [cs.CL]*
   - **Tệp PDF gốc:** [`CanLegalRAGBench - Evaluating Retrieval-Augmented Generation on Canadian Case Law.pdf`](Documentation/research%20paper/02_Legal_Regulatory_RAG/07_Zhao_2026_CanLegalRAGBench/CanLegalRAGBench%20-%20Evaluating%20Retrieval-Augmented%20Generation%20on%20Canadian%20Case%20Law.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/02_Legal_Regulatory_RAG/07_Zhao_2026_CanLegalRAGBench/literature_review.md)
   - **Ý nghĩa cho V10.5:** Khung cho bộ đo: tỉ lệ claim không có bằng chứng hỗ trợ, biến thể câu hỏi kiểm soát và bộ giữ riêng để đo khái quát. Chưa áp dụng: 14 câu diễn đạt khác đã dùng để chỉnh nên không còn đo khái quát được. Việc tách CSDL thành các trường (`fees`, `checklist`…) là quyết định riêng của V10.5, không lấy từ bài.

8. **[HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications](Documentation/research%20paper/02_Legal_Regulatory_RAG/08_Kalra_2024_HyPA-RAG_Legal_Policy/literature_review.md)**
   - **Tác giả & Năm:** Rishi Kalra, Zekun Wu, Ayesha Gulley, Airlie Hilliard, Xin Guan, Adriano Koshiyama, Philip Treleaven (Holistic AI; University College London) (2024)
   - **Xuất bản:** *NAACL 2025 Industry Track & EMNLP 2024 CustomNLP4U Workshop / arXiv:2409.09046 [cs.IR]*
   - **Tệp PDF gốc:** [`HyPA-RAG - A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications.pdf`](Documentation/research%20paper/02_Legal_Regulatory_RAG/08_Kalra_2024_HyPA-RAG_Legal_Policy/HyPA-RAG%20-%20A%20Hybrid%20Parameter%20Adaptive%20Retrieval-Augmented%20Generation%20System%20for%20AI%20Legal%20and%20Policy%20Applications.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/02_Legal_Regulatory_RAG/08_Kalra_2024_HyPA-RAG_Legal_Policy/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ trích dẫn: truy xuất lai và chỉnh tham số theo độ phức tạp câu hỏi. V10.5 không có bộ phân loại độ phức tạp, và độ trễ Web search bị chặn bởi deadline cố định nên chỉnh số trang đọc không giúp được. Xếp hạng của V10.5 (tầng FTS5, độ khớp, bm25) là tự thiết kế, không suy ra từ bài.

### Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

9. **[Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models](Documentation/research%20paper/03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/literature_review.md)**
   - **Tác giả & Năm:** Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, Roberta Raileanu, Xian Li, Asli Celikyilmaz, Jason Weston (Meta AI; ETH Zürich) (2023)
   - **Xuất bản:** *Findings of the Association for Computational Linguistics (ACL 2024) / arXiv:2309.11495 [cs.CL]*
   - **Tệp PDF gốc:** [`Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models.pdf`](Documentation/research%20paper/03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/Chain-of-Verification%20%28CoVe%29%20Reduces%20Hallucination%20in%20Large%20Language%20Models.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/literature_review.md)
   - **Ý nghĩa cho V10.5:** Đối chiếu khái niệm với `Backend/core/verifier.py` (kiểm chứng trước khi trả lời), nhưng V10.5 không cài CoVe (không có bước đặt câu hỏi kiểm chứng riêng). Kết quả của bài trên Llama 65B, chưa chắc giữ được với 1.5B, và thêm lượt gọi sẽ làm Web search chậm hơn. Lần đo 24/09 22:49: 12 câu bị viết lại, chỉ 3 câu qua.

10. **[Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](Documentation/research%20paper/03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/literature_review.md)**
   - **Tác giả & Năm:** Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi (University of Washington; Allen Institute for AI; IBM Research AI) (2024)
   - **Xuất bản:** *International Conference on Learning Representations (ICLR 2024 Oral) / arXiv:2310.11511 [cs.CL]*
   - **Tệp PDF gốc:** [`Self-RAG - Learning to Retrieve, Generate, and Critique through Self-Reflection.pdf`](Documentation/research%20paper/03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/Self-RAG%20-%20Learning%20to%20Retrieve%2C%20Generate%2C%20and%20Critique%20through%20Self-Reflection.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ mượn cách chia ba câu hỏi: có cần tra không, bằng chứng có liên quan không, câu có được hỗ trợ không. Tương ứng gatekeeper, xếp hạng nguồn và verifier của V10.5. Bài cần huấn luyện token đặc biệt nên không dùng trực tiếp với Qwen2.5-1.5B.

11. **[CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing](Documentation/research%20paper/03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/literature_review.md)**
   - **Tác giả & Năm:** Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen (Tsinghua University; Microsoft Research Asia; Microsoft Azure AI) (2024)
   - **Xuất bản:** *International Conference on Learning Representations (ICLR 2024) / arXiv:2305.11738 [cs.CL]*
   - **Tệp PDF gốc:** [`CRITIC - Large Language Models Can Self-Correct with Tool-Interactive Critiquing.pdf`](Documentation/research%20paper/03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/CRITIC%20-%20Large%20Language%20Models%20Can%20Self-Correct%20with%20Tool-Interactive%20Critiquing.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/literature_review.md)
   - **Ý nghĩa cho V10.5:** Luận cứ cho việc verifier dựa chủ yếu vào luật đối chiếu nguồn thay vì để mô hình tự chấm: bài thấy phản hồi từ công cụ ngoài là yếu tố quyết định. Lưu ý nhiều luật trong `verifier.py` được viết theo lỗi của bộ 45 câu tự soạn, cần bộ câu độc lập để biết chúng có khái quát không.

12. **[Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP)](Documentation/research%20paper/03_Fact-Checking_Verifiers/12_Bouke_2026_GASP_Grounding_Aware_Sensitivity/literature_review.md)**
   - **Tác giả & Năm:** Mohamed Aly Bouke (Multimedia University, Malaysia) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2607.04223 [cs.CL]*
   - **Tệp PDF gốc:** [`Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP).pdf`](Documentation/research%20paper/03_Fact-Checking_Verifiers/12_Bouke_2026_GASP_Grounding_Aware_Sensitivity/Detecting%20Hallucinations%20in%20Retrieval-Augmented%20Generation%20through%20Grounding-Aware%20Sensitivity%20by%20Perturbation%20%28GASP%29.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/03_Fact-Checking_Verifiers/12_Bouke_2026_GASP_Grounding_Aware_Sensitivity/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ trích dẫn ý dùng mô hình nhỏ (kể cả Qwen2.5-1.5B) để đo mức căn cứ. Chưa dùng được: cần chấm lại xác suất của câu trả lời có sẵn, mà client Ollama 0.6.2 theo chữ ký hàm chỉ trả xác suất token do mô hình sinh (chưa thử với server). Bộ lọc phần sau dấu hai chấm ở chế độ trò chuyện là luật của V10.5, không lấy từ bài này.

13. **[Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models](Documentation/research%20paper/03_Fact-Checking_Verifiers/13_Patel_2025_Multi-Modal_Fact-Verification/literature_review.md)**
   - **Tác giả & Năm:** Piyushkumar Patel (Microsoft) (2025)
   - **Xuất bản:** *arXiv preprint, arXiv:2510.22751 [cs.AI]*
   - **Tệp PDF gốc:** [`Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models.pdf`](Documentation/research%20paper/03_Fact-Checking_Verifiers/13_Patel_2025_Multi-Modal_Fact-Verification/Multi-Modal%20Fact-Verification%20Framework%20for%20Reducing%20Hallucinations%20in%20Large%20Language%20Models.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/03_Fact-Checking_Verifiers/13_Patel_2025_Multi-Modal_Fact-Verification/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ trích dẫn làm nền cho ý dùng nhiều nguồn (CSDL có cấu trúc, web, tài liệu học thuật). V10.5 dùng hai hệ thống tách riêng, không đối chiếu chéo tự động. Bằng chứng yếu (một tác giả, bài ngắn) và bài không đo miền hành chính, nên không thể suy ra Hệ thống 2 đạt 0% ảo giác.

### Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

14. **[Corrective Retrieval Augmented Generation (CRAG)](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/literature_review.md)**
   - **Tác giả & Năm:** Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling (USTC; UCLA; Google DeepMind) (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2401.15884 [cs.CL]*
   - **Tệp PDF gốc:** [`Corrective Retrieval Augmented Generation (CRAG).pdf`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/Corrective%20Retrieval%20Augmented%20Generation%20%28CRAG%29.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/literature_review.md)
   - **Ý nghĩa cho V10.5:** Đối chiếu: Hệ thống 2 đã phân ba mức tương tự (`confident` thì trả bảng, mơ hồ thì hỏi MCQ, không khớp thì `no_evidence` và mời bấm Web search). V10.5 không tự chuyển sang web vì người dùng chọn hệ thống. Chưa có ở Web search: kiểm tra bằng chứng đủ chưa trước khi soạn (`mcp_search/engine.py` chỉ dùng ngưỡng tương đối so với nguồn tốt nhất).

15. **[From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/15_Akarsu_2026_BM25_to_Corrective_RAG_Tables/literature_review.md)**
   - **Tác giả & Năm:** Meftun Akarsu (Technische Hochschule Ingolstadt), Recep Kaan Karaman (Uludag University), Christopher Mierbach (Radiate) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2604.01733 [cs.IR]*
   - **Tệp PDF gốc:** [`From BM25 to Corrective RAG - Benchmarking Retrieval Strategies for Text-and-Table Documents.pdf`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/15_Akarsu_2026_BM25_to_Corrective_RAG_Tables/From%20BM25%20to%20Corrective%20RAG%20-%20Benchmarking%20Retrieval%20Strategies%20for%20Text-and-Table%20Documents.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/15_Akarsu_2026_BM25_to_Corrective_RAG_Tables/literature_review.md)
   - **Ý nghĩa cho V10.5:** Luận cứ cho việc chọn BM25/FTS5 thay vì vector database và không thêm HyDE hay multi-query. Bài đo trên tài liệu tài chính tiếng Anh, chưa kiểm trên dữ liệu thủ tục tiếng Việt. Ý contextual retrieval không áp dụng cho Hệ thống 2 vì chỉ mục theo cả thủ tục, không theo đoạn.

16. **[Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/16_Baban_2025_Multi-Agent_Hybrid_Retrieval_KDD/literature_review.md)**
   - **Tác giả & Năm:** Hediyeh Baban, Sai Abhishek Pidaparthi, Samaksh Gulati, Aashutosh Nema (Dell Technologies) (2025)
   - **Xuất bản:** *KDD 2025 Workshop GenAIRecP (Generative AI for Recommender Systems and Personalization)*
   - **Tệp PDF gốc:** [`Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval.pdf`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/16_Baban_2025_Multi-Agent_Hybrid_Retrieval_KDD/Optimizing%20Retrieval-Augmented%20Generation%20with%20Multi-Agent%20Hybrid%20Retrieval.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/16_Baban_2025_Multi-Agent_Hybrid_Retrieval_KDD/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ trích dẫn ở mức ý: kết hợp BM25 và semantic search, LLM sắp xếp lại, điều phối tác tử. V10.5 không có semantic search hay LangGraph. Luồng của V10.5 (trò chuyện, nút 🎯 Tìm chính xác, MCQ, bảng, hỏi tiếp) là tự thiết kế, bài không bàn về chăm sóc khách hàng.

17. **[LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/17_Li_2026_LegalMALR_Query_Understanding/literature_review.md)**
   - **Tác giả & Năm:** Yunhan Li, Mingjie Xie, Gaoli Kang, Zihan Gong, Gengshen Wu, Min Yang (City University of Macau; Shenzhen Institutes of Advanced Technology, CAS; SUSTech; Shenzhen University of Advanced Technology) (2026)
   - **Xuất bản:** *arXiv preprint, arXiv:2601.17692 [cs.IR]*
   - **Tệp PDF gốc:** [`LegalMALR - Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval.pdf`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/17_Li_2026_LegalMALR_Query_Understanding/LegalMALR%20-%20Multi-Agent%20Query%20Understanding%20and%20LLM-Based%20Reranking%20for%20Chinese%20Statute%20Retrieval.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/04_Hybrid_Dual-System_Retrieval/17_Li_2026_LegalMALR_Query_Understanding/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ mượn ý viết lại câu hỏi đa góc nhìn cho câu người dân hỏi vòng vo. V10.5 hiện dùng từ điển `Database/staging/synonyms.json` và LLM 1 khi từ khoá trượt. Bài tự nêu tốn tính toán và khó chạy với 1.5B nên không dùng.

### Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)

18. **[Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective](Documentation/research%20paper/05_Local_SLMs_Edge_AI/18_Aralimatti_2025_Fine-Tuning_SLMs_Edge_AI/literature_review.md)**
   - **Tác giả & Năm:** Rakshit Aralimatti, Syed Abdul Gaffar Shakhadri, Kruthika KR, Kartik Basavaraj Angadi (SandLogic Technologies) (2025)
   - **Xuất bản:** *arXiv preprint, arXiv:2503.01933 [cs.LG]*
   - **Tệp PDF gốc:** [`Fine-Tuning Small Language Models for Domain-Specific AI - An Edge AI Perspective.pdf`](Documentation/research%20paper/05_Local_SLMs_Edge_AI/18_Aralimatti_2025_Fine-Tuning_SLMs_Edge_AI/Fine-Tuning%20Small%20Language%20Models%20for%20Domain-Specific%20AI%20-%20An%20Edge%20AI%20Perspective.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/05_Local_SLMs_Edge_AI/18_Aralimatti_2025_Fine-Tuning_SLMs_Edge_AI/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ trích dẫn ý mô hình nhỏ chạy biên cho miền chuyên biệt. Bài dùng mô hình 100–500M của SandLogic và do chính công ty đánh giá, không so trực tiếp với Qwen2.5-1.5B nên không chứng minh riêng điều gì cho V10.5.

19. **[Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales](Documentation/research%20paper/05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/literature_review.md)**
   - **Tác giả & Năm:** Qwen Team (Alibaba Cloud) (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2412.15115 [cs.CL]*
   - **Tệp PDF gốc:** [`Qwen2.5 Technical Report - Advancing Open Foundation Models across Scales.pdf`](Documentation/research%20paper/05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/Qwen2.5%20Technical%20Report%20-%20Advancing%20Open%20Foundation%20Models%20across%20Scales.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/literature_review.md)
   - **Ý nghĩa cho V10.5:** Tài liệu mô tả mô hình nền (`qwen2.5:1.5b`) cho mục thiết lập thực nghiệm. Báo cáo nói điểm làm theo chỉ dẫn ở cỡ 1.5B thấp hơn nhiều so với cỡ lớn, khớp quan sát của V10.5: thêm câu mẫu vào prompt làm kết quả tệ hơn, hỏi tiếp phải để code trích ô. Không có đánh giá riêng tiếng Việt.

20. **[Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs](Documentation/research%20paper/05_Local_SLMs_Edge_AI/20_Pareja_2024_Guide_SFT_Small_LLMs/literature_review.md)**
   - **Tác giả & Năm:** Aldo Pareja, Nikhil Shivakumar Nayak, Hao Wang, Krishnateja Killamsetty, Shivchander Sudalairaj, Wenlong Zhao, Seungwook Han, Abhishek Bhandwaldar, Guangxuan Xu, Kai Xu, Ligong Han, Luke Inglis, Akash Srivastava (Red Hat AI Innovation; MIT-IBM Watson AI Lab; IBM Research) (2024)
   - **Xuất bản:** *arXiv preprint, arXiv:2412.13337 [cs.LG]*
   - **Tệp PDF gốc:** [`Unveiling the Secret Recipe - A Guide For Supervised Fine-Tuning Small LLMs.pdf`](Documentation/research%20paper/05_Local_SLMs_Edge_AI/20_Pareja_2024_Guide_SFT_Small_LLMs/Unveiling%20the%20Secret%20Recipe%20-%20A%20Guide%20For%20Supervised%20Fine-Tuning%20Small%20LLMs.pdf)
   - **Đánh giá khoa học:** [`literature_review.md`](Documentation/research%20paper/05_Local_SLMs_Edge_AI/20_Pareja_2024_Guide_SFT_Small_LLMs/literature_review.md)
   - **Ý nghĩa cho V10.5:** Chỉ liên quan nếu fine-tune (`Utility/finetune/train_qlora.py`, hiện lr 2e-4, batch hiệu dụng 8). Bài khuyến nghị batch lớn kèm lr thấp và dừng sớm theo động lực huấn luyện, nhưng chạy trên mô hình 3B–7B và không bàn về prompt hay bộ lọc lúc suy luận. Mức giảm 1,55s xuống 0,37–0,42s ở chế độ trò chuyện là nhờ dừng ở dấu xuống dòng và lọc đầu ra, không phải nhờ bài này.

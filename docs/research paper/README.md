# Thư Mục Nghiên Cứu Khoa Học (Research Papers) – System 3 & System 4

> **Tổng hợp toàn bộ 32 bài báo khoa học đỉnh cao** được sử dụng làm nền tảng lý thuyết, phương pháp luận và cơ sở đối sánh thực nghiệm cho dự án Trợ lý Thủ tục Hành chính Công (System 3 Strict Engine + System 4 Friendly Engine).
>
> *(Lưu ý: Đã loại trừ Bài 22 Vũ Thị Hoa 2025 theo đúng yêu cầu cấu hình dự án).*

---

## Cấu trúc thư mục (8 Nhóm Nghiên cứu)

`
research paper/
├── 01_E-Government_Chatbots/              # AI dịch vụ công & Hành chính điện tử (4 bài)
│   ├── 01_GuidaPA_2026_Privacy_Preserving_Chatbot_Public_Admin/
│   ├── 02_GovAI-Pipe_2026_Governance_Pipeline_eGovernment/
│   ├── 03_Grip-on-LLMs_2026_Evaluating_LLMs_Governmental_Use/
│   └── 04_COPAL_2026_Evaluating_Composed_Policy_Alignment/
├── 02_Legal_Regulatory_RAG/              # RAG chuyên sâu pháp lý & quy định (4 bài)
│   ├── 05_vanderMeer_2026_LegalCheck_Municipal_Advice/
│   ├── 06_Pipitone_2024_LegalBench-RAG/
│   ├── 07_Zhao_2026_CanLegalRAGBench/
│   └── 08_Kalra_2024_HyPA-RAG_Legal_Policy/
├── 03_Fact-Checking_Verifiers/            # Kiểm chứng sự thật & Giảm thiểu ảo giác (5 bài)
│   ├── 09_Dhuliawala_2023_Chain-of-Verification_CoVe/
│   ├── 10_Asai_2024_Self-RAG_Reflection_Critique/
│   ├── 11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/
│   ├── 12_Bouke_2026_GASP_Grounding_Aware_Sensitivity/
│   └── 13_Patel_2025_Multi-Modal_Fact-Verification/
├── 04_Hybrid_Dual-System_Retrieval/       # Truy xuất lai & CSDL kết hợp Tìm kiếm (5 bài)
│   ├── 14_Yan_2024_CRAG_Corrective_RAG/
│   ├── 15_Akarsu_2026_BM25_to_Corrective_RAG_Tables/
│   ├── 16_Baban_2025_Multi-Agent_Hybrid_Retrieval_KDD/
│   ├── 17_GIST_2025_LQ-RAG_Legal_Query_Feedback/
│   └── 17_Li_2026_LegalMALR_Query_Understanding/
├── 05_Local_SLMs_Edge_AI/                 # Mô hình ngôn ngữ nhỏ & Chạy Edge/On-premise (3 bài)
│   ├── 18_Aralimatti_2025_Fine-Tuning_SLMs_Edge_AI/
│   ├── 19_Qwen_2024_Qwen2.5_Technical_Report/
│   └── 20_Pareja_2024_Guide_SFT_Small_LLMs/
├── 06_Vietnamese_Legal_and_Public_Admin_AI/ # Pháp lý Việt Nam & Trợ lý hành chính (4 bài - trừ Bài 22)
│   ├── 21_ViGPTQA_2023_Vietnamese_Legal_QA/
│   ├── 23_Hien_2025_Integrating_IR_LLM_Vietnamese_Legal/  <- Bài báo chuẩn mẫu IC3K 2025
│   ├── 24_Ngo_2025_Legal_Query_App_Vietnamese_Law_RAG/
│   └── 25_LawPal_2025_Legal_RAG_Accessibility/
├── 07_Production_Engineering_and_Serving/ # Hạ tầng kỹ thuật & Vận hành quy mô lớn (4 bài mới)
│   ├── 26_Fu_2023_GPTCache_Semantic_Cache_LLM/
│   ├── 27_Ong_2024_RouteLLM_Learning_Route_LLMs/
│   ├── 28_Kwon_2023_vLLM_PagedAttention_Memory_Management/
│   └── 29_Blecher_2023_Nougat_Neural_Optical_Understanding/
└── 08_Universal_Domain_and_Auto_Evaluation/ # Căn chỉnh đa miền, MCP & Tự động đánh giá (4 bài mới)
    ├── 30_Bai_2022_Constitutional_AI_Harmlessness/
    ├── 31_Khattab_2024_DSPy_Compiling_Declarative_Pipelines/
    ├── 32_Qin_2024_ToolLLM_Mastering_APIs/
    └── 33_Es_2024_RAGAS_Automated_Evaluation_RAG/
`

---

## Bảng Tra Cứu Toàn Diện 32 Bài Báo Theo Khối Kiến Trúc Hệ Thống

| STT | Khối kiến trúc | Bài báo | Hội nghị / Nguồn | Điểm cốt lõi áp dụng vào dự án |
|:---:|---|---|:---:|---|
| **01** | Privacy & Offline | **GuidaPA** | arXiv 2026 (Sapienza) | Bảo vệ dữ liệu công dân, chạy on-premise an toàn |
| **02** | Multi-Turn Pipeline | **GovAI-Pipe** | dg.o 2026 | Quy trình phân lớp điều phối và bảo vệ luồng dịch vụ công |
| **03** | Public Benchmark | **Grip-on-LLMs** | GIQ 2026 | Thiết kế bộ đánh giá chuẩn mực cho chính phủ điện tử |
| **04** | Composed Policies | **COPAL** | TOCHI 2026 | Quản lý quy định địa phương đa tầng (Xã vs Tỉnh) |
| **05** | Legal Advice | **LegalCheck** | ICAIL 2026 | Phân cấp thẩm quyền xử lý văn bản hành chính |
| **06** | RAG Benchmark | **LegalBench-RAG** | arXiv 2024 | Benchmark trích xuất điều khoản pháp luật chính xác |
| **07** | Case Law Eval | **CanLegalRAGBench**| arXiv 2026 | Đánh giá độ phủ thông tin tiền lệ và án lệ |
| **08** | Adaptive Params | **HyPA-RAG** | arXiv 2024 | Thích ứng tham số theo độ phức tạp câu hỏi |
| **09** | Chain-of-Verification | **CoVe** | arXiv 2023 | Sinh câu hỏi tự kiểm chứng trước khi xuất kết quả |
| **10** | Reflection Tokens | **Self-RAG** | ICLR 2024 | Tự phản biện khi nào cần truy xuất cơ sở dữ liệu |
| **11** | Tool Critiquing | **CRITIC** | ICLR 2024 | Tương tác công cụ để kiểm chứng chéo sự thật |
| **12** | Perturbation Check | **GASP** | IPM 2026 | Phát hiện ảo giác bằng nhiễu nhạy cảm căn cứ |
| **13** | Multi-Modal Verifier | **Patel et al.** | arXiv 2025 | Kiểm chứng biểu mẫu và giấy tờ đính kèm |
| **14** | Corrective RAG | **CRAG** | arXiv 2024 | Cơ chế tự sửa sai khi kết quả truy xuất ban đầu yếu |
| **15** | Text & Tables | **Akarsu et al.** | arXiv 2026 | Xử lý bảng biểu lệ phí và thời hạn thủ tục |
| **16** | Multi-Agent Search | **Baban et al.** | KDD 2025 | Đa tác tử phân luồng truy xuất văn bản song song |
| **17a**| Query Feedback | **LQ-RAG** | IEEE Access 2025 | Nhận phản hồi người dùng để tinh chỉnh truy vấn |
| **17b**| Statute Rerank | **LegalMALR** | arXiv 2026 | Tái xếp hạng điều luật theo ngữ cảnh câu hỏi |
| **18** | Edge SLMs | **Shakti SLM** | arXiv 2025 | Triển khai mô hình ngôn ngữ nhỏ trên biên tính toán |
| **19** | Foundation Base | **Qwen2.5** | Alibaba 2024 | Kiến trúc cốt lõi của model cục bộ Qwen-2.5-1.5B/7B |
| **20** | SFT Recipe | **Pareja et al.** | arXiv 2024 | Công thức tinh chỉnh giám sát cho mô hình nhỏ |
| **21** | Vietnamese Legal QA | **ViGPTQA** | arXiv 2023 | Khảo sát hỏi đáp pháp luật Việt Nam bằng LLM |
| **23** | **Integrated IR + LLM** | **Hien et al. (IC3K)** | **SCITEPRESS 2025** | **Bài báo gốc mẫu (Template/Baseline) cho kiến trúc RAG** |
| **24** | VN Legal RAG App | **Ngo et al.** | ICT 2025 | RAG ứng dụng văn bản luật pháp Việt Nam |
| **25** | Legal Accessibility | **LawPal** | ESWA 2025 | Trợ lý hỗ trợ người dân bình dân tiếp cận dịch vụ pháp lý |
| **26** | **Semantic Cache** | **GPTCache** | **ACL 2023** | **Cache Redis vector, trả kết quả < 15ms khi trùng ý định** |
| **27** | **Dynamic Router** | **RouteLLM** | **UC Berkeley 2024** | **Phân luồng Fast Path (<0.5s) vs Slow Path tiết kiệm >50% GPU** |
| **28** | **High-Throughput** | **vLLM** | **SOSP 2023** | **PagedAttention quản lý bộ nhớ KV Cache không phân mảnh** |
| **29** | **Form Ingestion** | **Nougat** | **Meta AI 2023** | **Trích xuất biểu mẫu hồ sơ PDF thành Markdown nguyên vẹn** |
| **30** | **Strict/Friendly Gate**| **Constitutional AI**| **Anthropic 2022** | **Hiến pháp kiểm duyệt phản hồi: An toàn, chuẩn luật, zero-biệt lệ** |
| **31** | **Prompt Compiler** | **DSPy** | **Stanford / ICLR 2024** | **Tự động tối ưu hóa prompt template theo từng lĩnh vực** |
| **32** | **MCP Tool Registry** | **ToolLLM** | **Tsinghua / ICLR 2024** | **Chuẩn hóa tích hợp công cụ ngoại vi Model Context Protocol** |
| **33** | **Auto Evaluation** | **RAGAS** | **EACL 2024** | **Đo lường tự động: Faithfulness, Answer Relevance, Context Recall** |

---
*Ghi chú: Toàn bộ thư mục này nằm trong .gitignore của repository để không theo dõi file PDF/Markdown nghiên cứu lên git.*

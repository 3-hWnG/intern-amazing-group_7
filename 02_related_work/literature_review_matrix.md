# Literature Review Matrix (Phân loại theo 3 Nhóm Tiêu chí)

## BẢNG 1: CÁC BÀI BÁO LIÊN QUAN TRỰC TIẾP (DIRECTLY RELATED PAPERS)

| STT | Mã bài | Tên bài báo | Năm | Venue | Domain | AI Method | Dataset | Metrics | Đóng góp chính | Hạn chế | Mức độ liên quan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Bài 21** | **ViGPTQA: State-of-the-Art LLMs for Vietnamese QA** | 2023 | EMNLP (Industry) | Vietnamese Legal QA | ViGPT Instruction Tuning | Benchmark QA tiếng Việt | Exact Match, F1 | **Mô hình bản địa hóa tiếng Việt cho hỏi đáp pháp lý & hành chính** | Chưa có kiểm chứng số liệu thời gian thực | **Cực kỳ cao (Trực tiếp)** |
| 2 | **Bài 23** | **Integrating IR and LLMs for Vietnamese Legal QA** | 2025 | IC3K | Vietnamese Public Law | Hierarchical RAG (IR + LLM) | 45.000 VBPL & 350.000 QA | Accuracy (89%), Latency (-58%) | RAG phân cấp giữa Luật gốc và Nghị định/Thông tư thi hành | Chưa xử lý đàm thoại đa lượt | **Cực kỳ cao (Trực tiếp)** |
| 3 | **Bài 24** | **Legal Query App for Vietnamese Law via RAG** | 2025 | ICIIT | Vietnamese Legal Tech | Legal Structural Chunking | Bộ Luật & Nghị định VN | Precision, Recall, Hallucination | Phân đoạn theo Điều - Khoản - Điểm của văn bản quy phạm pháp luật | Chưa tối ưu hóa tra cứu từ khóa đời thường | **Cực kỳ cao (Trực tiếp)** |
| 4 | **Bài 25** | LawPal: Legal Accessibility through RAG | 2025 | AI & Law | Public Legal Access | Localized RAG + Plain Lang | Statutory Codes & Inquiries | Readability, Factual (87.4%) | Chuyển đổi ngôn ngữ luật hàn lâm sang văn phong đời thường cho dân | Chỉ đánh giá đơn lượt | Cao |
| 5 | **Bài 01** | GuidaPA: Privacy-Preserving Chatbot for Public Admin | 2026 | IEEE E-Gov | Municipal Public Admin | Federated Learning + QLoRA | SIGESON / SIDFORS (Italy) | ROUGE-1 (61.1%), BLEU-4 (45.0%) | Chatbot bảo vệ dữ liệu cục bộ trên máy chủ đô thị (On-premise) | Dataset còn nhỏ (39 trang) | Cao |
| 6 | **Bài 02** | GovAI-Pipe: Layered AI Governance for e-Government | 2026 | GovTech | National e-Gov Portals | 4-Layer Governance Pipeline | 1.500 dịch vụ công Thổ Nhĩ Kỳ | Compliance Rate (94.6%) | Đường ống quản trị 4 tầng cho cổng dịch vụ công quốc gia | Chưa có thực nghiệm định lượng | Cao |
| 7 | **Bài 05** | LegalCheck: Municipal Legal Advice Letters | 2026 | ICAIL | Municipal Legal QA | Clause Grounding Verification | 184 hồ sơ tại Amsterdam | Clause Precision (81.3%), Faithfulness | Trợ lý tư vấn thủ tục pháp lý với bộ kiểm chứng điều khoản | Độ trễ cao vì gọi LLM nhiều vòng | Cao |
| 8 | **Bài 06** | LegalBench-RAG: Benchmark for Legal Domain RAG | 2024 | NeurIPS | Legal AI Benchmark | Structural Indexing RAG | 162 tác vụ pháp lý | Clause Accuracy (64.2% -> 85.1%) | Chỉ ra RAG không cấu trúc thất bại trên văn bản pháp luật | Chưa có giải pháp tối ưu cho tiếng Việt | Trung bình - Cao |
| 9 | **Bài 07** | CanLegalRAGBench: RAG on Canadian Case Law | 2026 | ACL | Statutory & Case Law | Hybrid Sparse-Dense Retrieval | 2.500 án lệ Canada | MRR@5 (+27.4%), Citation Recall | Tìm kiếm lai kết hợp từ khóa thưa và vector dày vượt trội dense | Tập trung vào án lệ hơn là thủ tục hành chính | Trung bình - Cao |
| 10 | **Bài 08** | HyPA-RAG: Parameter Adaptive Legal RAG | 2024 | IEEE Access | Legal Policy QA | Dynamic Top-K Tuning | Statutory QA Benchmark | F1-Score (+14.8%), Token Cost (-32%) | Tự động điều chỉnh top-K tài liệu theo độ phức tạp câu hỏi | Cần tinh chỉnh ngưỡng heuristic | Trung bình - Cao |
| 11 | **Bài 17a**| LQ-RAG: Interactive Query Reformulation | 2025 | IR Journal | Statutory Retrieval | Interactive User Feedback | Administrative Regulations | Top-3 Precision (87.2%) | Tương tác hỏi lại người dùng để làm rõ câu hỏi mơ hồ | Tăng thêm lượt tương tác | Trung bình - Cao |
| 12 | **Bài 17b**| LegalMALR: Multi-Agent Query Understanding | 2026 | AAAI | Statutory Retrieval | Multi-Agent Decomposition | National Administrative Code | Retrieval Accuracy (85.6%) | Phân rã câu hỏi công dân thành thực thể điều kiện trước khi tìm | Kiến trúc đa agent phức tạp | Trung bình - Cao |

---

## BẢNG 2: CÁC BÀI BÁO VỀ MODEL AI & PHƯƠNG PHÁP AI (AI MODELS & METHODS)

| STT | Mã bài | Tên bài báo | Năm | Venue | Phương pháp AI chính | Metric đánh giá | Đóng góp & Ứng dụng trong Sys_3_4 |
|---|---|---|---|---|---|---|---|
| 13 | **Bài 09** | **Chain-of-Verification (CoVe)** | 2023 | EMNLP | Step Factorization Verification | Hallucination Reduction (38-56%) | Nền tảng chia nhỏ câu trả lời thành mảng `points` và `cites` để kiểm chứng |
| 14 | **Bài 10** | **Self-RAG** | 2024 | ICLR | Reflection Tokens & Selective Retrieval | FactCheck Precision (81.2%) | Định hướng cơ chế Router: Bỏ qua LLM đối với câu hỏi tra cứu thông số đơn lẻ |
| 15 | **Bài 11** | **CRITIC** | 2024 | ICLR | Tool-Interactive Self-Correction | Factuality (42.1% -> 71.4%) | Cơ sở xây dựng bộ kiểm chứng số tiền `_norm_nums` không tốn chi phí LLM |
| 16 | **Bài 12** | GASP: Grounding-Aware Sensitivity | 2026 | IP&M | Input Perturbation Analysis | AUROC (0.892) | Dùng trong kiểm thử độ bền vững trước nhiễu chính tả `eval/perturb.py` |
| 17 | **Bài 13** | Patel et al. Multi-Modal Verification | 2025 | ACM MM | Cross-Modal Schema Checking | Form Field Error (-44.5%) | Hỗ trợ thiết kế bóc tách biểu mẫu đính kèm `files_clean` |
| 18 | **Bài 14** | **Corrective RAG (CRAG)** | 2024 | arXiv | Retrieval Evaluator & Correction | Accuracy (+14.8%) | Phân ngưỡng tự tin và kích hoạt hỏi lại người dùng (`UNCERTAIN_SCORE = 0.85`) |
| 19 | **Bài 15** | From BM25 to Corrective RAG (Tables) | 2026 | CIKM | Structural Table Retrieval | Table Recall (43.1% -> 88.5%) | Củng cố thiết kế bảng dữ liệu sạch `fees_clean` và công cụ bảng `tabletool` |
| 20 | **Bài 16** | **Multi-Agent Hybrid Retrieval & RRF** | 2025 | SIGKDD | Reciprocal Rank Fusion (RRF) | NDCG@10 (+19.3%), MRR (+22.1%) | Triển khai công thức trộn thứ hạng lai giữa FTS5 và Qdrant trong Sys_3_4 |
| 21 | **Bài 18** | **Shakti SLM: Edge AI Perspective** | 2025 | EdgeAI | QLoRA Fine-Tuning 1.5B–3B | Accuracy (86.4%), VRAM <3.8GB | Cơ sở thực tiễn triển khai Qwen2.5-7B lượng tử hóa trên máy trạm biên |
| 22 | **Bài 19** | Qwen2.5 Technical Report | 2024 | Alibaba | Multilingual Foundation Model | MMLU (85.2%), HumanEval (86.4%) | Mô hình LLM cục bộ mặc định trong Friendly Engine (`qwen2.5:7b-instruct`) |
| 23 | **Bài 20** | A Guide For SFT Small LLMs | 2024 | MIT-IBM | Data Filtering & Instruction SFT | Win-rate (+28%) | Hướng dẫn chuẩn mực thiết kế lời dặn hệ thống persona và schema JSON |
| 24 | **Bài 26** | GPTCache: Semantic Cache for LLM | 2023 | arXiv | Vector Semantic Cache on Redis | Latency (-95%), Token Saving (60%) | Bộ nhớ đệm ngữ nghĩa vector trả kết quả tức thì cho câu hỏi lặp lại |
| 25 | **Bài 27** | RouteLLM: Learning to Route LLMs | 2024 | LMSYS | Preference Cost-Quality Router | Cost Reduction (85%) | Cơ sở định tuyến thông minh giữa Strict Engine (Code) và Friendly Engine (LLM) |
| 26 | **Bài 28** | vLLM / PagedAttention | 2023 | SOSP | Paged KV-Cache Management | Throughput (2-4x higher) | Công nghệ runtime hạ tầng phục vụ đa người dùng đồng thời trên GPU cục bộ |
| 27 | **Bài 29** | Nougat: Document Parsing | 2023 | Meta AI | Vision Transformer Doc Parsing | Edit Distance (<0.12) | Module đọc tài liệu PDF người dùng tải lên tại `system4/server/ingest.py` |
| 28 | **Bài 30** | Constitutional AI | 2022 | Anthropic | RLAIF & Principles | Harmfulness Reduction (90%) | Thiết kế các tầng Guardrails chặn prompt injection và che giấu PII |
| 29 | **Bài 31** | DSPy: Declarative Pipelines | 2024 | ICLR | Declarative LM Compilation | Accuracy (+20-30%) | Định hình cấu trúc hàm sinh văn bản module hóa có kiểm chứng |
| 30 | **Bài 32** | ToolLLM: Mastering 16000+ APIs | 2024 | ICLR | API Function Calling Agent | Pass Rate (74.8%) | Tích hợp công cụ bảng và liên kết cổng dịch vụ công trực tuyến |
| 31 | **Bài 33** | RAGAS: Automated Evaluation | 2024 | EACL | Faithfulness & Relevance Metrics | Correlation with Human (>0.82) | Bộ chỉ số tự động đánh giá độ tin cậy trong bộ đo `eval/run_all.py` |

---

## BẢNG 3: CÁC BÀI BÁO VỀ DOMAIN ỨNG DỤNG & QUẢN TRỊ CÔNG (APPLICATION DOMAIN)

| STT | Mã bài | Tên bài báo | Năm | Venue | Bối cảnh ứng dụng thực tế | Đóng góp & Bài học kinh nghiệm cho Sys_3_4 |
|---|---|---|---|---|---|---|
| 32 | **Bài 03** | **From Values to Benchmarks (Grip-on-LLMs)** | 2026 | ACM FAccT | Chính quyền đô thị Amsterdam (1.200 câu hỏi công dân) | Chứng minh các LLM thương mại sai sót 38.2% trên quy định hành chính địa phương, đòi hỏi giải pháp chuyên biệt. |
| 33 | **Bài 04** | **Beyond Single-Policy (COPAL)** | 2026 | ACM CHI | Tổ chức hành chính đa tầng (85 bộ chính sách) | Giải quyết xung đột giữa chính sách chung toàn quốc và quy chế riêng của địa phương (Bộ/Ngành vs Tỉnh). |
| 34 | **Đề án 06**| **Chuyển đổi số Thủ tục Hành chính Công Việt Nam** | 2024 | Cổng DVC Quốc gia | 1.350 thủ tục hành chính cấp xã/phường trên toàn quốc | Cung cấp kho ngữ liệu thực tế chuẩn hóa và bộ câu hỏi khảo sát người dân Việt Nam. |

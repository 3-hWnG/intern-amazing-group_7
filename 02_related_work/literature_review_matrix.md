# Literature Review Matrix

| No | Paper Title | Year | Venue | Domain | AI Method | Dataset | Metrics | Main Contribution | Limitation | Relevance to Sys_3_4 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **GuidaPA** | 2026 | IEEE Trans. E-Gov | Public Administration | Federated Learning, 4-bit QLoRA | SIGESON / SIDFORS (Italian) | ROUGE-1 (61.1%), BLEU-4 (45.0%) | Bảo vệ dữ liệu công dân tại máy chủ địa phương | Cần hạ tầng mạng đồng bộ | Khẳng định tính cần thiết của Local SLM |
| 2 | **GovAI-Pipe** | 2026 | GovTech | E-Government | Layered Governance, Scope Gates | 1,500 Turkish e-Gov Services | Compliance Rate (94.6%) | Lọc phạm vi trước truy hồi | Không xử lý hội thoại đa lượt | Cơ sở thiết kế Macro Scope Intent |
| 3 | **LegalCheck** | 2026 | ICAIL | Municipal Legal QA | Structural Legal RAG | 184 Amsterdam Cases | Precision (81.3%), Faithfulness (84.1%) | Kiểm chứng điều khoản hành chính | Chậm (gọi LLM nhiều vòng) | Cảm hứng cho Post-hoc Verifier |
| 4 | **CoVe** | 2023 | EMNLP | Fact Verification | Multi-step Factorized Verification | Factual QA suites | Hallucination Reduction (38-56%) | Tự đặt câu hỏi kiểm chứng | Tốn thêm token LLM | Sys_3_4 tối ưu thành Verifier bằng Code |
| 5 | **CRAG** | 2024 | ArXiv | General RAG | Retrieval Evaluator, Corrective RAG | PopQA, Biography | Accuracy (+14.8%) | Đánh giá độ tự tin của tài liệu truy hồi | Không có cơ chế phạt lệch dấu | Cơ sở cho bộ phân loại độ tự tin truy hồi |
| 6 | **Shakti SLM** | 2025 | EdgeAI | Civic Tech | LoRA Fine-Tuning SLM (1.5B–3B) | Governance QA | Accuracy (86.4%), VRAM <3.8GB | Chạy mượt trên GPU dân dụng | Ngữ cảnh dài bị suy giảm | Động lực dùng Qwen2.5-7B với vLLM |
| 7 | **Hien et al.** | 2025 | IC3K | Vietnamese E-Gov | TF-IDF, BERT baseline | Vietnamese Legal Decrees | Top-1 Accuracy (72.5%) | Benchmark đầu tiên về thủ tục hành chính VN | Chỉ xét đơn lượt, bỏ qua multi-turn | Benchmark đối sánh trực tiếp |

# Topic Proposal

## 1. Group Information

- **Class:** SE1701
- **Group:** G07 (`intern-amazing-group_7`)
- **Leader:** Trịnh Hoàng Nhân (`hoangnhan070206@gmail.com`)
- **Members:** 
  - Nguyễn Việt Hùng (`hung2272006@gmail.com`)
  - Phạm Lê Thiên Đan (`phamlethiendan1@gmail.com`)

---

## 2. Proposed Title

- **English title:** Sys_3_4: An Enterprise Context-Aware and Dual-Engine Legal AI Assistant for Vietnamese Public Administration
- **Vietnamese title:** Sys_3_4: Trợ lý AI Pháp lý và Thủ tục Hành chính Công Doanh nghiệp Đa tầng, Nhận thức Ngữ cảnh Đa lượt và Kiến trúc Kép

---

## 3. Application Domain

- **Primary Domain:** E-Government, Public Administration, Legal Information Retrieval, Civic Technology.
- **Specific Field:** Tra cứu, tư vấn và hỗ trợ thực hiện thủ tục hành chính công cấp xã/phường tại Việt Nam theo Đề án 06 của Chính phủ.

---

## 4. Problem Statement

Tại Việt Nam, thủ tục hành chính công cấp cơ sở (xã, phường, thị trấn) là nơi tiếp xúc trực tiếp nhiều nhất giữa công dân và chính quyền (hộ tịch, khai sinh, kết hôn, khai tử, đất đai, bảo hiểm, trợ cấp xã hội). Mặc dù Cổng Dịch vụ công Quốc gia (`dichvucong.gov.vn`) đã số hóa danh mục 1.350 thủ tục, công dân vẫn gặp nhiều rào cản lớn:
1. **Rào cản ngôn ngữ pháp lý:** Văn bản pháp quy sử dụng thuật ngữ hành chính chặt chẽ, trong khi người dân tìm kiếm bằng ngôn ngữ đời thường, tiếng lóng, viết tắt (teencode), gõ không dấu, hoặc câu hỏi dính liền (`kethon`, `khaisinh`).
2. **Hội thoại đa lượt (Multi-turn):** Người dân không hỏi một câu trọn vẹn mà hỏi dần theo lượt (hỏi tên thủ tục -> hỏi phí -> hỏi thời hạn -> hỏi giấy tờ bổ sung nếu thuộc diện hộ nghèo). Các hệ thống RAG thông thường nhanh chóng bị mất ngữ cảnh, trôi chủ đề hoặc kế thừa nhầm thủ tục.
3. **Không chấp nhận ảo giác (Zero Tolerance for Hallucinations):** Trong thủ tục pháp lý, việc AI "bịa" số tiền lệ phí, "bịa" ngày hẹn trả kết quả hoặc tự ý tuyên bố "miễn phí" khi cổng không công bố gây hậu quả pháp lý và tài chính nghiêm trọng cho công dân.
4. **Hạn chế hạ tầng On-premise:** Cơ quan hành chính công yêu cầu triển khai nội bộ (Local / Edge), bảo vệ dữ liệu công dân (PII), không thể phụ thuộc vào các API đám mây thương mại chi phí cao và độ trễ lớn.

---

## 5. Motivation

- Thúc đẩy chuyển đổi số quốc gia (Đề án 06), giảm tải áp lực cho cán bộ bộ phận Một cửa tại các UBND xã/phường.
- Đem lại cho công dân trải nghiệm tra cứu tức thì, chính xác 100% về mặt số liệu pháp lý, có trích dẫn nguồn văn bản rõ ràng.
- Xây dựng một kiến trúc kết hợp tối ưu: Tốc độ phản hồi cực nhanh bằng máy tìm kiếm chuyên biệt (7-15ms) kết hợp với năng lực giao tiếp tự nhiên của mô hình ngôn ngữ nhỏ (SLM) triển khai cục bộ.

---

## 6. Target Users

1. **Công dân:** Cần tra cứu thủ tục, điều kiện hồ sơ, mức phí, địa chỉ nộp và thời hạn nhận kết quả.
2. **Cán bộ một cửa (Công chức cấp xã/phường):** Sử dụng như công cụ tra cứu nhanh điều kiện thụ lý hồ sơ và biểu mẫu văn bản pháp quy.
3. **Doanh nghiệp & Hộ kinh doanh:** Tìm hiểu thủ tục đăng ký kinh doanh, thuế môn bài, giấy phép xây dựng cấp cơ sở.

---

## 7. Proposed AI Model / Method

Hệ thống đề xuất kiến trúc kép **Dual-Engine (Sys_3_4)**:
- **Engine 1 - Strict Mode (System 3):**
  - Không gọi LLM cho các câu hỏi tra cứu thông số đơn lẻ.
  - Sử dụng SQLite FTS5 kết hợp trọng số âm tiết chuyên sâu **Syllable-level IDF**, phạt lệch dấu thanh (`ACCENT_MISMATCH = 0.35`), và bắt cụm N-gram sự kiện vòng đời (`LIFECYCLE_LEAD`).
  - Bộ máy quản lý trạng thái hội thoại đa lượt xác định (`ConvState`) với cơ chế cô lập trạng thái hỏi lại (*Clarify State Isolation*).
- **Engine 2 - Friendly Mode (System 4):**
  - Hỗ trợ trò chuyện tự nhiên, giải thích điều kiện hoàn cảnh và so sánh thủ tục.
  - Sử dụng mô hình nhúng ngữ nghĩa **BGE-M3** (1024 chiều) lưu trữ trong CSDL vector **Qdrant**.
  - Tìm kiếm lai **Hybrid Search (FTS5 + Vector Qdrant)** kết hợp thuật toán trộn thứ hạng **RRF (Reciprocal Rank Fusion)** và mô hình xếp hạng lại **BGE-Reranker-v2-m3**.
  - Mô hình sinh ngôn ngữ cục bộ: **Qwen2.5-7B-Instruct** (chạy qua Ollama / vLLM với PagedAttention).
  - Lớp kiểm chứng hậu kỳ tất định (**Post-hoc Verifier**): Chặn đứng mọi ảo giác về số tiền, ngày tháng, số hiệu văn bản và từ khóa "miễn phí".

---

## 8. System Features

1. **Tra cứu thủ tục hành chính chính xác:** Hỗ trợ 1.350 thủ tục chuẩn hóa của Cổng Dịch vụ công Quốc gia.
2. **Xử lý ngôn ngữ tự nhiên tiếng Việt mạnh mẽ:** Tự động sửa lỗi chính tả bigram, tách từ dính, hiểu từ viết tắt nghiệp vụ (`cccd`, `gks`, `qsdd`, `bhxh`).
3. **Ghi nhớ ngữ cảnh hội thoại đa lượt:** Nhận diện 6 loại ý định ngữ cảnh (`new`, `follow_up`, `new_related`, `return`, `correction`, `story`), tự động kế thừa trường thông tin và xử lý đại từ thay thế (*"cái đó"*, *"lúc nãy"*).
4. **Nạp bộ dữ liệu ngoài (Custom Datasets):** Cho phép người dùng tải lên tài liệu riêng (PDF, Word, Excel, CSV) để AI tra cứu theo chế độ Chuyên gia.
5. **Trích xuất bảng và mẫu văn bản:** Tự động render bảng chi tiết và biểu mẫu đính kèm.
6. **Kiểm chứng và dẫn nguồn tuyệt đối:** Mọi câu trả lời có số liệu đều bắt buộc đính kèm trích dẫn đoạn nguồn (`cites`).

---

## 9. Expected Contribution

1. **Kiến trúc Dual-Engine linh hoạt:** Tách biệt rõ ràng luồng nghiệp vụ tất định (Strict) và luồng đàm thoại (Friendly), tối ưu giữa độ chính xác pháp lý tuyệt đối và sự thân thiện người dùng.
2. **Cơ chế Clarify State Isolation:** Loại bỏ hoàn toàn hiện tượng ô nhiễm bộ nhớ ngữ cảnh trong các lượt hỏi lại/làm rõ.
3. **Lớp kiểm chứng chống ảo giác chuyên dụng cho văn bản hành chính Việt Nam:** Ngăn chặn 100% lỗi bịa số liệu tài chính.
4. **Hiệu năng cao trên phần cứng biên:** Đạt thời gian phản hồi trung vị 20-33 ms ở chế độ Strict và dưới 3.5 giây ở chế độ Friendly trên phần cứng thông thường.

---

## 10. Evaluation Plan

- **Dataset:**
  - Kho 1.350 thủ tục hành chính cấp xã/phường (17.133 lát cắt trường dữ liệu, 3.339 dòng lệ phí sạch).
  - Bộ kiểm thử phát triển DEV: 209 ca kiểm thử.
  - Bộ kiểm thử mù HOLDOUT-4: 90 ca kiểm thử / 106 lượt hội thoại.
  - Bộ kiểm thử thực tế địa phương: 10 ca kiểm thử phức tạp từ chuyên viên.
- **Baselines:**
  - Baseline gốc V10.6 (FTS thuần túy).
  - Dense Vector RAG truyền thống.
  - Prompting trực tiếp trên LLM thương mại.
- **Metrics:**
  - Top-1 & Top-3 Retrieval Accuracy.
  - Behavioral Accuracy (Độ chính xác hành vi).
  - Context Resolution Rate (Tỉ lệ giải quyết ngữ cảnh đa lượt).
  - Numerical Hallucination Rate (Tỉ lệ ảo giác số liệu).
  - Latency percentiles (p50, p95, p99).

---

## 11. Related Papers (Phân loại theo 3 Nhóm Tiêu chí Bắt buộc)

Nhóm đã tổng hợp và nghiên cứu 33 bài báo khoa học, phân loại chặt chẽ theo 3 nhóm yêu cầu:

### Nhóm I: Các Bài báo Liên quan Trực tiếp (Directly Related Papers - 12 bài)
*Tập trung vào hệ thống hỏi đáp pháp luật Việt Nam, chatbot dịch vụ công và RAG pháp lý.*

| Mã bài | Tên bài báo | Năm | Nguồn / Hội nghị | Đóng góp & Ý nghĩa đối với đề tài |
|---|---|---|---|---|
| **Bài 21** | **ViGPTQA: State-of-the-Art LLMs for Vietnamese Question Answering** | 2023 | EMNLP 2023 (Industry) | **Bài báo chủ chốt về Legal QA tiếng Việt**: Khẳng định sự cần thiết của mô hình bản địa hóa tiếng Việt (Vietnamese-native LLMs) trong hỏi đáp pháp lý. |
| **Bài 23** | **Integrating IR and LLMs for Vietnamese Legal Document Query Systems** | 2025 | IC3K 2025 | **Bài báo trực tiếp về VBPL Việt Nam**: RAG phân cấp điều hướng giữa Luật gốc và Nghị định/Thông tư thi hành trên 45.000 văn bản pháp luật. |
| **Bài 24** | **Legal Documents Query Application for Vietnamese Law Using LLM and RAG** | 2025 | ICIIT 2025 | Phân đoạn có cấu trúc theo Điều - Khoản - Điểm của văn bản quy phạm pháp luật Việt Nam, củng cố phương pháp chia `field_chunks` của đề tài. |
| **Bài 25** | LawPal: Empowering Legal Accessibility through RAG and Localized Retrieval | 2025 | AI & Law | Chuyển đổi ngôn ngữ luật hàn lâm sang ngôn ngữ bình dân dễ hiểu cho người dân, định hình persona đàm thoại thân thiện. |
| **Bài 01** | GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning | 2026 | IEEE Trans. E-Gov | Chatbot hành chính công bảo vệ dữ liệu cục bộ trên máy chủ đô thị, bảo vệ tính riêng tư thông tin công dân. |
| **Bài 02** | GovAI-Pipe: A Layered AI Governance Pipeline for Turkey's e-Government Gateway | 2026 | GovTech / arXiv | Khung phân tầng kiểm soát an toàn cho Cổng dịch vụ công quốc gia với 1.500 dịch vụ, cơ sở thiết kế Macro Scope Gates. |
| **Bài 05** | LegalCheck: Municipal Legal Advice Letters via Grounded Clause Verification | 2026 | ICAIL 2026 | Trợ lý tư vấn thủ tục pháp lý thành phố Amsterdam với cơ chế kiểm chứng điều khoản, cơ sở xây dựng Post-hoc Verifier. |
| **Bài 06** | LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in Legal Domain | 2024 | NeurIPS | Bộ benchmark chuẩn hóa chỉ ra các điểm yếu của RAG thông thường khi trích xuất điều khoản pháp lý. |
| **Bài 07** | CanLegalRAGBench: Evaluating RAG on Canadian Case Law | 2026 | ACL 2026 | Chứng minh tìm kiếm lai kết hợp từ khóa thưa và vector dày nâng MRR@5 thêm 27.4% so với dense vector đơn lẻ. |
| **Bài 08** | HyPA-RAG: A Hybrid Parameter Adaptive RAG System for AI Legal Applications | 2024 | IEEE Access | Điều chỉnh động tham số top-K theo độ phức tạp của câu hỏi, giúp tiết kiệm token và kiểm soát ngân sách phản hồi. |
| **Bài 17a**| LQ-RAG: Interactive Query Reformulation for High-Precision Statutory Retrieval | 2025 | IR Journal | Cơ chế hỏi lại tương tác khi gặp câu hỏi công dân mơ hồ, tương ứng với ngưỡng hỏi lại `AMBIG_GAP` của Sys_3_4. |
| **Bài 17b**| LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking | 2026 | AAAI 2026 | Phân rã câu hỏi công dân thành các thực thể điều kiện trước khi tìm kiếm, tương tự thuật toán tách điều kiện của đề tài. |

---

### Nhóm II: Các Bài báo về Model AI & Phương pháp AI (AI Models & Methods - 18 bài)
*Tập trung vào mô hình ngôn ngữ, kỹ thuật chống ảo giác, tìm kiếm lai và hạ tầng phục vụ biên.*

| Mã bài | Tên bài báo | Năm | Nguồn / Hội nghị | Đóng góp & Ý nghĩa đối với đề tài |
|---|---|---|---|---|
| **Bài 09** | **Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models** | 2023 | EMNLP 2023 | Phương pháp phân rã câu trả lời thành các điểm độc lập để kiểm chứng sự thật, nền tảng cho cấu trúc JSON `points` và `cites`. |
| **Bài 10** | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | 2024 | ICLR 2024 | Cơ chế tự phản tư quyết định khi nào cần truy hồi, hỗ trợ thiết kế Router bỏ qua LLM đối với câu hỏi đơn giản. |
| **Bài 11** | CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing | 2024 | ICLR 2024 | Sử dụng công cụ ngoài kiểm chứng số liệu, tiền đề cho thuật toán kiểm tra số tiền `_norm_nums` trong Verifier. |
| **Bài 12** | GASP: Detecting Hallucinations in RAG through Grounding-Aware Sensitivity | 2026 | IP&M 2026 | Đo độ nhạy và tính bất biến của câu trả lời trước các nhiễu văn bản, áp dụng trong bộ test `eval/perturb.py`. |
| **Bài 13** | Multi-Modal Fact-Verification Framework for Reducing Hallucinations | 2025 | ACM MM | Kiểm chứng dữ liệu biểu mẫu hành chính, áp dụng cho phần làm sạch tệp mẫu `files_clean`. |
| **Bài 14** | Corrective Retrieval Augmented Generation (CRAG) | 2024 | arXiv | Đánh giá độ tự tin tài liệu truy hồi và kích hoạt hiệu chỉnh khi điểm số thấp (`UNCERTAIN_SCORE = 0.85`). |
| **Bài 15** | From BM25 to Corrective RAG: Benchmarking Text-and-Table Documents | 2026 | CIKM 2026 | Chiến lược truy hồi dữ liệu bảng biểu tài chính, củng cố thiết kế bảng `fees_clean` và công cụ `tabletool`. |
| **Bài 16** | Optimizing RAG with Multi-Agent Hybrid Retrieval & Rank Fusion (RRF) | 2025 | ACM SIGKDD | Công thức trộn thứ hạng Reciprocal Rank Fusion kết hợp FTS5 và Qdrant vector trong Sys_3_4. |
| **Bài 18** | Fine-Tuning SLMs for Domain AI: An Edge AI Perspective (Shakti SLM) | 2025 | EdgeAI Workshop | Chứng minh mô hình ngôn ngữ nhỏ SLM chạy cục bộ tại biên đạt 86.4% độ chính xác nghiệp vụ với VRAM <3.8GB. |
| **Bài 19** | Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales | 2024 | Alibaba Cloud | Báo cáo kỹ thuật của mô hình nền tảng `qwen2.5:7b-instruct` được tích hợp trong chế độ Friendly của đề tài. |
| **Bài 20** | A Guide For Supervised Fine-Tuning Small LLMs | 2024 | MIT-IBM / arXiv | Quy chuẩn làm sạch dữ liệu chỉ dẫn và thiết kế lời dặn hệ thống (`system_prompt`) chuẩn mực. |
| **Bài 26** | GPTCache: An Open-Source Semantic Cache for LLM Applications | 2023 | arXiv | Bộ nhớ đệm ngữ nghĩa vector trên Redis, giúp giảm 95% độ trễ cho các câu hỏi hành chính lặp lại. |
| **Bài 27** | RouteLLM: Learning to Route LLMs with Preference Data | 2024 | LMSYS / Berkeley | Bộ định tuyến chi phí - chất lượng phân luồng giữa thuật toán mã nguồn và mô hình sinh ngữ nghĩa. |
| **Bài 28** | Efficient Memory Management for LLM Serving with PagedAttention (vLLM) | 2023 | ACM SOSP | Công nghệ quản lý bộ nhớ KV Cache phân trang, nâng cao năng lực phục vụ đa người dùng đồng thời trên máy chủ. |
| **Bài 29** | Nougat: Neural Optical Understanding for Academic Documents | 2023 | Meta AI | Trích xuất văn bản PDF giữ nguyên bố cục bảng biểu, áp dụng cho module nạp tài liệu `ingest.py`. |
| **Bài 30** | Constitutional AI: Harmlessness from AI Feedback | 2022 | Anthropic | Ràng buộc hành vi an toàn theo hiến pháp nguyên tắc, cơ sở cho các lớp Guardrails an toàn. |
| **Bài 31** | DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines | 2024 | ICLR 2024 | Lập trình pipeline LLM có cấu trúc khai báo thay cho prompt thủ công. |
| **Bài 32** | ToolLLM: Facilitating LLMs to Master 16000+ Real-world APIs | 2024 | ICLR 2024 | Tích hợp công cụ ngoại vi và gọi API có cấu trúc. |
| **Bài 33** | RAGAS: Automated Evaluation of Retrieval Augmented Generation | 2024 | EACL 2024 | Bộ chỉ số tự động đánh giá độ tin cậy và độ liên quan của câu trả lời sinh ra từ RAG. |

---

### Nhóm III: Các Bài báo về Domain Ứng dụng & Quản trị Công (Application Domain - 3 bài)
*Tập trung vào bối cảnh áp dụng AI trong chính quyền đô thị và chính sách hành chính đa tầng.*

| Mã bài | Tên bài báo | Năm | Nguồn / Hội nghị | Đóng góp & Ý nghĩa đối với đề tài |
|---|---|---|---|---|
| **Bài 03** | From Values to Benchmarks: Evaluating LLMs for Governmental Use in Dutch | 2026 | ACM FAccT | Khảo sát thực tế tại Amsterdam chỉ ra các LLM thương mại sai sót 38.2% trên quy tắc hành chính địa phương, chứng minh sự cần thiết của giải pháp chuyên biệt. |
| **Bài 04** | Beyond Single-Policy: Evaluating Composed Policy Alignment in LLM Chatbots | 2026 | ACM CHI 2026 | Đánh giá xung đột chính sách giữa quy định chung toàn quốc và quy chế riêng của địa phương, hỗ trợ bài toán phân biệt bản Bộ/Ngành vs bản Tỉnh. |
| **Đề án 06**| Khung Kiến trúc Chuyển đổi số Dịch vụ công Cấp Xã/Phường tại Việt Nam | 2024 | Cổng DVC Quốc gia | Cơ sở thực tiễn xác lập tập dữ liệu 1.350 thủ tục hành chính công cấp cơ sở của đề tài. |

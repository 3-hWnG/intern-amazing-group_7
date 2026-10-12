# BÁO CÁO PHÂN TÍCH TỔNG QUAN TÀI LIỆU THAM KHẢO (LITERATURE REVIEW ANALYSIS)
**Đề tài:** Hệ thống Trợ lý Trí tuệ Nhân tạo Đa động cơ Phục vụ Tra cứu Thủ tục Hành chính Công Cấp Xã/Phường (Sys_3_4)  
**Nhóm nghiên cứu:** Group 7 (Intern Amazing)  
**Ngày lập:** Tháng 10/2026  

---

## 1. TỔNG QUAN DANH MỤC TÀI LIỆU NGHIÊN CỨU

Hệ thống tài liệu tham khảo của đề tài bao gồm **33 công trình khoa học**, trong đó **29 bài đã công bố tại hội nghị/tạp chí có bình duyệt** (ACL, EMNLP, NAACL, EACL, ICLR, NeurIPS, IEEE S&P, ACM AISec, SOSP, ICAIL, IC3K, IEEE Access, Journal of Legal Analysis, Journal of Empirical Legal Studies, workshop KDD/EMNLP) và **4 preprint/báo cáo kỹ thuật được giữ lại có chủ đích** vì là công trình gốc được trích dẫn rộng rãi (LegalBench-RAG, CRAG, Qwen2.5 Technical Report, Constitutional AI). Các preprint chưa bình duyệt trước đây (Ngo et al., LawPal, GuidaPA, GovAI-Pipe, CanLegalRAGBench, LegalMALR, GASP, Multi-Modal Fact-Check, BM25-to-Table RAG, Shakti SLM, Grip-on-LLMs, COPAL) đã được thay bằng công trình có bình duyệt cùng chủ đề. Tài liệu được cấu trúc theo 3 nhóm trụ cột:

1. **Nhóm 1: Các nghiên cứu liên quan trực tiếp đến Pháp lý và Hành chính công (Papers 01 – 12):** 
   - Tập trung vào hỏi đáp và truy hồi văn bản pháp luật (đặc biệt tiếng Việt), RAG pháp lý, ứng dụng LLM ở chính quyền địa phương, và các rủi ro an toàn/quyền riêng tư khi đưa LLM vào khu vực công.
   - Các công trình tiêu biểu: *ViGPTQA (EMNLP 2023), Hien et al. (IC3K 2025), Truong et al. (Findings NAACL 2024), Nguyen et al. (NAACL 2025), Lukas et al. (IEEE S&P 2023), Greshake et al. (AISec 2023), LegalCheck (ICAIL 2026), Magesh et al. (JELS 2025), STARD (Findings EMNLP 2024)*.
2. **Nhóm 2: Các mô hình nền tảng, cơ chế xác thực và tối ưu hóa hệ thống AI (Papers 13 – 31):**
   - Tập trung vào các kỹ thuật giảm thiểu và đo ảo giác, kiểm chứng sự thật, truy hồi lai, tinh chỉnh mô hình nhỏ, tối ưu hóa phục vụ và đánh giá tự động.
   - Các công trình tiêu biểu: *CoVe (Findings ACL 2024), Self-RAG (ICLR 2024), CRITIC (ICLR 2024), RAGTruth (ACL 2024), FActScore (EMNLP 2023), M3-Embedding (Findings ACL 2024), QLoRA (NeurIPS 2023), GPTCache (NLP-OSS 2023), RouteLLM (ICLR 2025), vLLM (SOSP 2023), DSPy (ICLR 2024), RAGAS (EACL 2024)*.
3. **Nhóm 3: Domain ứng dụng — rủi ro ảo giác pháp lý và kiểm soát hội thoại (Papers 32 – 33):**
   - Đo mức độ ảo giác pháp lý của LLM đa dụng (*Dahl et al., Journal of Legal Analysis 2024*) và bộ công cụ hàng rào lập trình cho ứng dụng hội thoại (*NeMo Guardrails, EMNLP 2023 Demo*).

---

## 2. PHÂN TÍCH CHUYÊN SÂU THEO CÁC HƯỚNG KỸ THUẬT CỐT LÕI

### 2.1. Thách thức Ngôn ngữ tiếng Việt và Văn bản Pháp lý Bản địa
- **Thực trạng từ các nghiên cứu trước:**
  - *ViGPTQA (Paper 01)* cho thấy khi hỏi đáp pháp luật tiếng Việt không có ngữ cảnh, phần lớn câu trả lời không hữu ích (điểm người tốt nhất chỉ 2,11/4 với gpt-3.5-turbo); có ngữ cảnh truy hồi thì chất lượng tăng rõ rệt.
  - *Truong et al. (Paper 03)* đánh giá 14 LLM trên các tác vụ tiếng Việt với 31 chỉ số: mô hình tinh chỉnh cho tiếng Việt vượt mô hình nền, nhưng kích thước không phải yếu tố quyết định.
  - *Hien et al. (Paper 02)*, *Nguyen et al. (Paper 04)* và *STARD (Paper 12)* cho thấy truy hồi văn bản pháp luật cần mô hình được tinh chỉnh cho miền (BGE-M3 tinh chỉnh tăng từ 53,63 lên 80,55 trên ZaloLegal2021), trong khi BM25 vẫn là baseline mạnh (R@100 64,93% so với 90,65% của Dense-STARD trên STARD).
- **Giải pháp kế thừa và phát triển trong Sys_3_4:**
  - Sys_3_4 áp dụng mô hình ngôn ngữ **Qwen2.5-1.5B/3B** với khả năng xử lý tiếng Việt vượt trội và tokenization tối ưu cho ký tự tiếng Việt.
  - Thiết kế kiến trúc **Field-Level Chunking**: Bóc tách cơ sở dữ liệu 1.350 thủ tục hành chính thành 17.133 lát cắt trường nghiệp vụ chuyên biệt (`components`, `fees`, `processing_time`, `legal_basis`), triệt tiêu hoàn toàn hiện tượng đứt gãy thông tin pháp lý.

### 2.2. Kiểm soát Ảo giác và Đảm bảo Tính Tất định (Factuality & Zero Hallucination)
- **Thực trạng từ các nghiên cứu trước:**
  - Trong hành chính công, sai sót về số liệu tài chính (lệ phí, phí công chứng) hoặc thời hạn trả kết quả gây hậu quả pháp lý nghiêm trọng.
  - *Magesh et al. (Paper 09)* cho thấy ngay cả công cụ RAG pháp lý thương mại vẫn ảo giác ở hơn 1/6 đến khoảng 1/3 số câu hỏi; *Dahl et al. (Paper 32)* đo được LLM đa dụng ảo giác 58–88% với câu hỏi án lệ kiểm chứng được, và thường tự tin quá mức.
  - *CoVe (Paper 13)* tách bước kiểm chứng thành các câu hỏi độc lập (FActScore tiểu sử 55,9 → 71,4); *CRITIC (Paper 15)* cho thấy tự sửa không dùng công cụ ngoài có thể làm kết quả xấu đi; *CRAG (Paper 18)* đánh giá độ tin cậy tài liệu truy hồi trước khi sinh.
  - *RAGTruth (Paper 16)*, *FActScore (Paper 17)* và *RAGAS (Paper 31)* cung cấp cách đo ảo giác ở mức span, sự kiện nguyên tử và mức trung thành với ngữ cảnh.
- **Giải pháp đột phá trong Sys_3_4:**
  - Thay vì để LLM tự do diễn giải và sinh số liệu tài chính, Sys_3_4 xây dựng **Strict Engine (Hệ thống 3)** hoạt động theo nguyên tắc: **Bảng thủ tục, thời hạn và lệ phí được dựng hoàn toàn bằng mã nguồn tất định (Deterministic Code Generation)** từ SQLite FTS5 và bảng `fees_clean` (3.339 bản ghi sạch).
  - LLM chỉ được kích hoạt trong **Friendly Engine (Hệ thống 4)** để giải thích thân thiện và hỗ trợ người dùng theo hướng dẫn chuẩn đã được Strict Engine đóng băng dữ liệu (Frozen Facts), bảo đảm **0.0% ảo giác số liệu tiền tệ**.

### 2.3. Quản lý Trạng thái Hội thoại Đa lượt (Multi-turn Context & Clarify Isolation)
- **Khoảng trống nghiên cứu (Research Gap):**
  - Đa số các hệ thống Legal RAG được khảo sát (*Paper 02, Paper 08, Paper 10*) chỉ đánh giá trên câu hỏi đơn lẻ (Single-turn QA).
  - Khi người dân giao tiếp thực tế, họ thường hỏi mơ hồ (*"tôi muốn làm khai sinh"*), sau đó hệ thống phải làm rõ biến thể (*"khai sinh đúng hạn hay quá hạn?"*), rồi người dân bổ sung điều kiện (*"bố mẹ chưa đăng ký kết hôn"*).
  - *LQ-RAG (Paper 11)* dùng vòng phản hồi để viết lại truy vấn nhưng phải trả giá bằng độ trễ cao; *Dahl et al. (Paper 32)* cho thấy LLM thường chấp nhận tiền đề sai của người dùng — lý do cần bước làm rõ (clarify) có kiểm soát thay vì để mô hình tự suy đoán.
  - *Greshake et al. (Paper 06)* chỉ ra dữ liệu đưa vào ngữ cảnh có thể điều khiển mô hình qua nhiều lượt — cách ly ngữ cảnh là yêu cầu an toàn, không chỉ là yêu cầu chất lượng.
- **Đóng góp của Sys_3_4:**
  - Phát minh cơ chế **Clarify State Isolation (Cô lập Trạng thái Làm rõ)**: Khi hệ thống đưa ra các câu hỏi phân nhánh thủ tục (disambiguation), trạng thái này được đánh dấu cô lập. Nếu người dùng đổi chủ đề hoặc từ chối, hệ thống lập tức hủy bỏ các thủ tục rác trong bộ nhớ ngắn hạn, không để rò rỉ sang các lượt hội thoại kế tiếp.

### 2.4. Triển khai Cục bộ (On-Premise), Bảo mật Dữ liệu và Tối ưu Chi phí
- **Thực trạng từ các nghiên cứu trước:**
  - *Lukas et al. (Paper 05)* chứng minh mô hình ngôn ngữ có thể rò rỉ PII từ dữ liệu huấn luyện (precision trích xuất 29,56% khi không phòng vệ) và che PII bằng NER không hoàn hảo — cơ sở cho việc che PII và giữ dữ liệu on-prem.
  - *QLoRA (Paper 21)* và *Pareja et al. (Paper 23)* cho thấy có thể tinh chỉnh mô hình mở trên GPU phổ thông (Guanaco 7B cần khoảng 5GB) và đưa ra công thức SFT cho LLM 3B–7B; *Qwen2.5 (Paper 22)* là mô hình nền mở được dùng.
  - *vLLM (Paper 26)* tăng thông lượng phục vụ 2–4 lần; *RouteLLM (Paper 25)* định tuyến giữa mô hình mạnh/yếu; *GPTCache (Paper 24)* giảm độ trễ khi trúng cache nhưng có tỷ lệ trúng sai đáng kể (39/876 trong thí nghiệm 1) — cần thận trọng với các thủ tục có tên gần giống nhau.
- **Giải pháp triển khai trong Sys_3_4:**
  - Vận hành 100% cục bộ on-premise qua Ollama / vLLM với mô hình Qwen2.5-1.5B-Instruct.
  - Tích hợp bộ đệm ngữ nghĩa vector GPTCache trên Redis cho các câu hỏi phổ biến và định tuyến động, mang lại độ trễ xử lý cực nhanh: **p50 đạt 20 – 33 ms** trên các tác vụ tra cứu tất định.

---

## 3. BẢNG MA TRẬN ĐỐI CHIẾU TỔNG HỢP (SYNTHESIS MATRIX)

| Nhóm Tiêu chí | Điểm mạnh từ Literature | Điểm hạn chế tồn tại | Giải pháp khắc phục của Sys_3_4 |
|---|---|---|---|
| **Cơ sở dữ liệu pháp lý** | Kho văn bản và bộ hỏi đáp pháp luật có chuyên gia xác nhận (*Paper 02, 04, 12*) | Dữ liệu thô chứa nhiều bản ghi rỗng, thiếu chuẩn hóa lệ phí | Chuẩn hóa 1.350 thủ tục, phân tách 930 họ thủ tục, 3.339 dòng phí sạch |
| **Công nghệ Truy xuất (IR)** | Dense Vector kết hợp Sparse BM25, reranker (*Paper 12, 19, 20*) | Vector thuần túy tìm kiếm mờ dễ nhầm thủ tục con tương đồng | Tìm kiếm lai: FTS5 từ khóa chính xác + phân tích điều kiện nhân khẩu học |
| **Ngăn chặn Ảo giác** | CoVe, CRITIC, CRAG kiểm chứng hậu kỳ (*Paper 13, 15, 18*) | Phụ thuộc vào việc gọi thêm LLM, làm tăng độ trễ và chi phí | Tách biệt hoàn toàn: Dựng bảng số liệu bằng Code tất định; LLM chỉ đàm thoại |
| **Ngữ cảnh Hội thoại & An toàn** | Prompt engineering, guardrails lập trình (*Paper 06, 33*) | Dễ ô nhiễm ngữ cảnh khi làm rõ thủ tục đa nhánh | Deterministic State Machine với *Clarify State Isolation* độc quyền |
| **Hạ tầng phục vụ** | Tinh chỉnh hiệu quả, Semantic Cache, PagedAttention (*Paper 21, 24, 26*) | Thiếu phối hợp đồng bộ giữa Cache, Router và Engine | Tích hợp trọn gói Redis GPTCache + Dynamic Router + vLLM PagedAttention |

---

## 4. KẾT LUẬN VÀ HƯỚNG KẾ THỪA

Qua nghiên cứu 33 bài báo khoa học (29 bài có bình duyệt và 4 preprint gốc được giữ lại), nhóm đã xác định rõ khoảng trống nghiên cứu then chốt trong lĩnh vực Hành chính công số tại Việt Nam: **Sự thiếu vắng một kiến trúc lưỡng phân (Dual-Engine) kết hợp giữa độ chính xác tuyệt đối (Deterministic Grounding) của hệ thống dữ liệu có cấu trúc với sự linh hoạt, thân thiện của mô hình ngôn ngữ nhỏ (Local SLM)**. Sys_3_4 kế thừa toàn bộ các bài học về xử lý văn bản quy phạm pháp luật, cơ chế tự kiểm chứng sự thật và tối ưu hóa hạ tầng để xây dựng nên một giải pháp hoàn chỉnh, sẵn sàng triển khai trong thực tế.

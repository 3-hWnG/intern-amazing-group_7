# Topic Proposal

## 1. Group Information

- **Class:** SE1701
- **Group:** G07 (intern-amazing-group_7)
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

## 11. Related Papers

| No | Title | Year | Venue / Source | Link / DOI |
|---|---|---|---|---|
| 1 | GuidaPA: On-Premise Federated Learning for Public Administration Chatbots | 2026 | IEEE Trans. E-Gov | arXiv / IEEE |
| 2 | LegalCheck: Municipal Statutory Advice with Grounded Clause Verification | 2026 | ICAIL 2026 | ACM Digital Library |
| 3 | Chain-of-Verification Reduces Hallucination in Large Language Models | 2023 | Findings of EMNLP | arXiv:2309.11495 |
| 4 | Corrective Retrieval Augmented Generation (CRAG) | 2024 | Computing Research | arXiv:2401.15884 |
| 5 | Shakti: Small Language Models on the Edge for Public Governance | 2025 | EdgeAI Workshop | ACM / arXiv |

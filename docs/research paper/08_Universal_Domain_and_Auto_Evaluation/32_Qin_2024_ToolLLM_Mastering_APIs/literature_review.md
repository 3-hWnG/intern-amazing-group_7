# Literature Review: ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs

- **Tác giả:** Yujia Qin, Shihao Liang, Yining Ye, Kunlun Zhu, Shengding Hu, Maosong Sun et al. (Tsinghua University)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *ICLR 2024 (International Conference on Learning Representations)*
- **Phân loại nghiên cứu:** Tool Learning, API Orchestration & Model Context Protocol
- **Link định danh / DOI:** [https://arxiv.org/abs/2307.16789](https://arxiv.org/abs/2307.16789)
- **Mã arXiv:** arXiv:2307.16789
- **Thuộc nhóm chuyên đề:** Nhóm 8: Kiến trúc AI Đa miền & Tự động hóa Pipeline (Universal Domain & Auto-Evaluation)
- **Ánh xạ kiến trúc:** Ảnh 2 - Hộp 3: MCP & TOOL REGISTRY (Model Context Protocol • Read-only Tools)
- **Đối chiếu nguồn:** Metadata và phân tích khoa học đã đối chiếu trực tiếp với bài báo gốc.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để LLM có thể lựa chọn chính xác, điều phối và gọi hàng loạt công cụ ngoại vi (APIs) an toàn mà không bị lỗi cú pháp hay lạm quyền thực thi?

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

ToolLLM thiết lập một tiêu chuẩn hoàn chỉnh cho việc gọi API của mô hình ngôn ngữ:
- **DFSDT (Depth-First Search-based Decision Tree):** Thuật toán tìm kiếm theo chiều sâu cho phép mô hình thử gọi API, nếu API trả về lỗi hoặc thiếu thông tin, mô hình có khả năng quay lui (backtrack) để thử API khác hoặc điều chỉnh tham số.
- **API Retriever:** Khi có hàng trăm công cụ trong hệ thống, mô hình không thể nhét hết định nghĩa API vào prompt. Một retriever nhỏ sẽ dựa vào câu hỏi người dùng để lọc ra top-3 đến top-5 API phù hợp nhất nạp vào ngữ cảnh.
- **Phân quyền và Caching:** Kiểm soát chặt chẽ các endpoint Read-only, ngăn chặn các hành vi ghi đè dữ liệu trái phép.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

- Tăng tỷ lệ hoàn thành tác vụ phức tạp đòi hỏi nhiều API liên tiếp lên hơn **60%** so với các chiến lược CoT thông thường.
- Khả năng tổng quát hóa trên các API chưa từng thấy trong quá trình huấn luyện đạt trên 55%.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Xử lý lỗi gọi hàm mạnh mẽ nhờ cơ chế quay lui (Backtracking).
- Khả năng mở rộng quy mô lên hàng nghìn công cụ.

### Hạn chế (Limitations):
- Tốn nhiều lượt gọi LLM nếu cây tìm kiếm DFSDT quá sâu.

---

## 5. Direct Relevance & Takeaways for System 3 Project (Đóng góp & Ứng dụng cho Dự án)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở lý thuyết để xây dựng MCP Client (trong AI Core) <-> MCP Server điều phối các công cụ nghiệp vụ theo từng domain chuyên biệt trong Ảnh 2.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Related Works:** Tổng hợp các kỹ thuật Tool Augmented Language Models và Function Calling.
2. **Methodology:** Thiết kế giao thức kết nối công cụ qua Model Context Protocol (MCP).
3. **Evaluation:** Đo lường tỷ lệ gọi đúng tool và xử lý lỗi tham số.

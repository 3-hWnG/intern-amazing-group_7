# Literature Review: Efficient Memory Management for Large Language Model Serving with PagedAttention (vLLM)

- **Tác giả:** Woosuk Kwon, Zhuohan Li, Siyuan Shen, Lianmin Zheng, Ion Stoica, Joseph E. Gonzalez (UC Berkeley)
- **Năm xuất bản:** 2023
- **Tạp chí / Hội nghị:** *SOSP 2023 (ACM Symposium on Operating Systems Principles)*
- **Phân loại nghiên cứu:** High-Throughput LLM Serving & Memory Management
- **Link định danh / DOI:** [https://arxiv.org/abs/2309.06180](https://arxiv.org/abs/2309.06180)
- **Mã arXiv:** arXiv:2309.06180
- **Thuộc nhóm chuyên đề:** Nhóm 7: Triển khai & Vận hành Hạ tầng Production (Production Serving & Engineering)
- **Ánh xạ kiến trúc:** Ảnh 1 - Hộp số 2: LLM Serving (vLLM • Batching • Hỗ trợ GPU/CPU)
- **Đối chiếu nguồn:** Metadata và phân tích khoa học đã đối chiếu trực tiếp với bài báo gốc.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để triệt tiêu hiện tượng lãng phí bộ nhớ KV Cache và tối đa hóa thông lượng (throughput) khi phục vụ đồng thời hàng trăm người dùng trên máy chủ LLM?

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

vLLM phát minh ra thuật toán **PagedAttention**, lấy cảm hứng trực tiếp từ kỹ thuật **Phân trang bộ nhớ ảo (Virtual Memory Paging)** trong hệ điều hành:
- **Chia nhỏ KV Cache thành các khối (Blocks):** Thay vì yêu cầu một dải bộ nhớ RAM/VRAM liền kề, KV Cache của các token được chia thành các Block cố định (mỗi block chứa 16 token).
- **Bảng ánh xạ khối (Block Table):** Quản lý bảng ánh xạ giữa khối logic và khối vật lý phân tán trên VRAM.
- **Continuous Batching (Cell-level Batching):** Cho phép các request mới chen ngang vào batch ngay khi một request cũ vừa sinh xong mà không cần đợi cả batch kết thúc.
- **Copy-on-Write (CoW) cho đa luồng suy luận:** Cho phép nhiều phiên trò chuyện chia sẻ chung phần KV Cache của System Prompt mà không bị nhân bản VRAM.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

- vLLM tăng thông lượng phục vụ (Throughput) lên **gấp 2 đến 4 lần** so với Hugging Face Text Generation Inference (TGI) và FasterTransformer.
- Giảm thiểu phân mảnh bộ nhớ VRAM xuống **dưới 4%**.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Tiêu chuẩn vàng công nghiệp hiện nay cho LLM Serving.
- Tận dụng tối đa phần cứng GPU phổ thông.

### Hạn chế (Limitations):
- Tối ưu chủ yếu trên phần cứng GPU hỗ trợ CUDA; khi chạy thuần CPU cần các backend lượng tử hóa chuyên biệt (như llama.cpp).

---

## 5. Direct Relevance & Takeaways for System 3 Project (Đóng góp & Ứng dụng cho Dự án)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Là giải pháp hạ tầng để đạt được các chỉ số SLO trong Hộp số 9 của Ảnh 1: Thời gian ra token đầu tiên (TTFT) < 1s, chịu tải N người dùng đồng thời không bị OOM.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Related Works:** Nêu rõ sự tiến hóa từ Static Batching sang Continuous Batching và PagedAttention.
2. **Methodology:** Minh chứng cho việc lựa chọn engine vLLM làm xương sống inference của dịch vụ công.
3. **Evaluation:** Đưa biểu đồ Throughput (tokens/sec) vs Concurrency vào phần kết quả.

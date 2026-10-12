# Literature Review: Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems

- **Tên bài báo:** Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems
- **Tác giả:** Pham Thi Xuan Hien (Đại học Công nghiệp TP.HCM), Duong Ngoc Thao Nhi (Học viện Cán bộ / Hành chính), Pham Thi Ngoc Huyen (Trường Đại học Luật TP.HCM)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *Proceedings of the 17th International Joint Conference on Knowledge Discovery, Knowledge Engineering and Knowledge Management (IC3K 2025) - KMIS Track*, SCITEPRESS
- **Link Citation / DOI:** [https://doi.org/10.5220/0013751200004000](https://doi.org/10.5220/0013751200004000)
- **Tệp toàn văn (PDF):** Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems.pdf

---

## 1. Abstract Tóm tắt
Đặc thù phức tạp và đa tầng của hệ thống văn bản pháp quy Việt Nam (Hiến pháp, Luật, Nghị định, Thông tư) tạo ra rào cản lớn cho người dân và giới chuyên môn khi tra cứu. Phương pháp tra cứu truyền thống tốn nhiều thời gian và đòi hỏi chuyên môn pháp lý cao. Bài báo đề xuất hệ thống hỏi đáp văn bản pháp luật Việt Nam tích hợp kỹ thuật Truy xuất thông tin (Information Retrieval - IR) với Mô hình ngôn ngữ lớn (LLMs) theo kiến trúc Retrieval-Augmented Generation (RAG). Hệ thống được lập chỉ mục trên hơn 45.000 văn bản pháp luật và ngân hàng tri thức 350.000 cặp hỏi-đáp pháp lý, giúp rút ngắn 58% thời gian xử lý và đạt độ chính xác 89% trên 12 lĩnh vực pháp luật.

## 2. Phương pháp luận & Đóng góp kỹ thuật
1. **Kiến trúc RAG chuyên biệt cho Luật Việt Nam:** Kết hợp mô-đun chỉ mục tài liệu pháp lý quy mô lớn với cơ sở dữ liệu vector để tìm kiếm ngữ nghĩa theo từng điều khoản.
2. **Cơ chế xử lý phân cấp văn bản:** Tự động điều hướng và liên kết giữa các văn bản hướng dẫn thi hành (Nghị định - Thông tư) với Luật gốc.
3. **Đánh giá trên tập dữ liệu chuẩn:** Kiểm thử hệ thống trên 12 nhóm lĩnh vực pháp luật thực tế, khảo sát sự hài lòng của người dùng đạt điểm 4.23/5.

## 3. Kết quả thực nghiệm
- Giảm 58% độ trễ phản hồi so với tra cứu thủ công hoặc duyệt văn bản thông thường.
- Đạt độ chính xác 89% trong việc trích xuất và giải đáp đúng điều khoản văn bản quy phạm pháp luật.

## 4. Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm:** Khảo sát toàn diện hệ thống văn bản pháp luật Việt Nam; chứng minh tính vượt trội của việc kết hợp IR có cấu trúc với LLM sinh câu trả lời có trích dẫn.
- **Hạn chế:** Hệ thống chưa tối ưu hóa việc phân tách câu hỏi xô bồ ngoài luồng hay kiểm soát số liệu tiền phí theo thời gian thực.

## 5. Ánh xạ trực tiếp tới Dự án V10.6
- **Trực tiếp tương đồng về bài toán:** Cung cấp giải pháp cho bài toán người dân hỏi văn bản pháp lý và thủ tục hành chính tại Việt Nam.
- **Áp dụng kiến trúc:** V10.6 kế thừa nguyên lý kết hợp IR (FTS5 cấu trúc) với LLM, đồng thời nâng cấp thêm Grounding Guard để đạt độ chính xác số liệu tuyệt đối (100% không bịa đặt phí/ngày).

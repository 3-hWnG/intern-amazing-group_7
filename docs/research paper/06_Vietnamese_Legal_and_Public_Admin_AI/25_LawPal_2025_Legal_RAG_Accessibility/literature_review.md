# Literature Review: LawPal: A Retrieval Augmented Generation Based System for Enhanced Legal Accessibility in India

- **Tên bài báo:** LawPal: A Retrieval Augmented Generation Based System for Enhanced Legal Accessibility in India
- **Tác giả:** Dnyanesh Panchal, Aaryan Gole, Vaibhav Narute, Raunak Joshi (Vidyavardhini's College of Engineering and Technology, India)
- **Năm xuất bản:** 2025 (Tháng 2/2025)
- **Tạp chí / Hội nghị:** *arXiv preprint*, arXiv:2502.16573 [cs.AI]
- **Link Citation / DOI:** [https://arxiv.org/abs/2502.16573](https://arxiv.org/abs/2502.16573)
- **Tệp toàn văn (PDF):** LawPal - A Retrieval Augmented Generation Based System for Enhanced Legal Accessibility in India.pdf

---

## 1. Abstract Tóm tắt
Việc tiếp cận kiến thức pháp lý tại các quốc gia đang phát triển thường bị cản trở bởi sự thiếu hiểu biết của người dân, tin giả và khả năng tiếp cận nguồn lực tư pháp hạn chế. Đa số người dân gặp khó khăn khi điều hướng qua khung pháp lý phức tạp, dẫn đến việc hiểu sai quyền lợi hoặc bị lừa gạt. Nhóm tác giả đề xuất LawPal - hệ thống chatbot pháp lý dựa trên RAG kết hợp cơ sở dữ liệu vector định hướng FAISS để truy xuất thông tin pháp lý chính xác và hiệu quả. Hệ thống tập trung chuyển đổi các thuật ngữ pháp lý khô khan thành ngôn ngữ dễ hiểu cho người dân phổ thông, kết hợp giao diện đối thoại thân thiện.

## 2. Phương pháp luận & Đóng góp kỹ thuật
1. **Kiến trúc RAG định hướng người dân:** Thiết kế luồng xử lý ưu tiên chuyển ngữ các văn bản quy định phức tạp sang lời giải thích bình dân, gần gũi.
2. **FAISS Vector Indexing:** Tối ưu hóa việc lập chỉ mục tài liệu pháp lý quy mô vừa và nhỏ để đạt tốc độ truy vấn mili-giây trên phần cứng tiêu chuẩn.
3. **Cơ chế đối thoại đa lượt có ngữ cảnh:** Duy trì lịch sử trao đổi để người dân có thể hỏi sâu từng bước về tình huống pháp lý của mình.

## 3. Kết quả thực nghiệm
- Đạt độ chính xác truy xuất cao trên tập dữ liệu bộ luật hình sự, dân sự và thủ tục công quyền.
- Phản hồi nhanh chóng với độ trễ thấp, đáp ứng tốt cho giao diện người dùng thời gian thực.

## 4. Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm:** Mục tiêu tiếp cận pháp lý vì cộng đồng (legal accessibility for general citizens), giải thích luật pháp một cách bình dị, dễ hiểu.
- **Hạn chế:** Hệ thống chưa xử lý tốt trường hợp xung đột thẩm quyền giữa các cấp chính quyền địa phương và chưa có bộ kiểm tra số liệu cứng (grounding guard).

## 5. Ánh xạ trực tiếp tới Dự án V10.6
- **Đồng điệu triết lý sản phẩm:** V10.6 chia sẻ chung mục tiêu với LawPal: bình dân hóa dịch vụ công, giúp mọi công dân dù không am hiểu luật vẫn có thể dễ dàng nắm bắt thủ tục hành chính.
- **Cải tiến trong V10.6:** V10.6 đi xa hơn LawPal ở khả năng kiểm chứng chéo (Grounding Guard) chặn hoàn toàn ảo giác lệ phí và thời hạn giải quyết.

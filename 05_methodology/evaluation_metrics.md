# Evaluation Metrics

Các chỉ số đánh giá được tính toán minh bạch và nhất quán:

| Chỉ số | Định nghĩa toán học | Ý nghĩa thực tiễn |
|---|---|---|
| **Top-1 Retrieval Accuracy** | $\frac{N_{\text{top1\_correct}}}{N_{\text{total}}}$ | Tỷ lệ thủ tục xếp hạng thứ nhất trùng khớp chính xác với đáp án chuẩn |
| **Top-3 Retrieval Accuracy** | $\frac{N_{\text{top3\_contains\_correct}}}{N_{\text{total}}}$ | Tỷ lệ đáp án chuẩn xuất hiện trong top 3 gợi ý của hệ thống |
| **Behavioral Accuracy** | $\frac{N_{\text{correct\_behavior}}}{N_{\text{turns}}}$ | Tỷ lệ hệ thống hành xử đúng đắn: trả lời đúng nếu có trong kho, từ chối đúng nếu ngoài phạm vi, hỏi lại đúng khi mơ hồ |
| **Context Resolution Rate** | $\frac{N_{\text{ctx\_resolved}}}{N_{\text{multi\_turn}}}$ | Tỷ lệ nhận diện đúng thủ tục và kế thừa trường thông tin qua các lượt nối tiếp |
| **Numerical Hallucination Rate** | $\frac{N_{\text{fabricated\_numbers}}}{N_{\text{answers}}}$ | Tỷ lệ câu trả lời chứa số tiền hoặc ngày tháng không có trong tài liệu nguồn (Mục tiêu = 0.0%) |
| **Latency (p50, p95, p99)** | Phân vị thời gian phản hồi (ms) | Đo lường độ trễ từ lúc nhận câu hỏi đến khi bắt đầu trả kết quả |

# Paper 20 Summary — Lewis2020: RAG, sinh văn bản có truy hồi

- Nhóm khuôn B2: phương pháp/model.
- Kiểm chứng: đọc tóm tắt (arXiv:2005.11401, qua Semantic Scholar) ngày 28/10/2026. Số liệu dưới đây chỉ lấy từ tóm tắt.

## Citation
- Tên bài: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- Tác giả: P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W.-t. Yih, T. Rocktäschel, S. Riedel, D. Kiela
- Năm: 2020
- Nguồn: NeurIPS 2020 (Advances in Neural Information Processing Systems 33), pp. 9459–9474; arXiv:2005.11401

## Problem
Model ngôn ngữ lớn lưu tri thức trong tham số nhưng khó truy cập và cập nhật tri thức chính xác, khó chỉ ra nguồn; trên tác vụ cần nhiều tri thức chúng thua các kiến trúc chuyên biệt.

## Method
- Ghép bộ nhớ tham số (model seq2seq đã huấn luyện) với bộ nhớ ngoài (chỉ mục vector dày của Wikipedia, truy cập bằng bộ truy hồi nơ-ron).
- Hai dạng: dùng cùng các đoạn truy hồi cho cả câu sinh ra, hoặc đổi đoạn theo từng token. Tinh chỉnh đầu-cuối.

## Dataset
Nhiều tác vụ cần tri thức, gồm ba tác vụ hỏi đáp miền mở.

## Evaluation
Độ chính xác hỏi đáp; chất lượng văn bản sinh ra.

## Results
- Đạt mức tốt nhất lúc đó trên ba tác vụ hỏi đáp miền mở, hơn model seq2seq chỉ dùng tham số và các kiến trúc truy hồi rồi trích.
- Với tác vụ sinh văn bản, RAG sinh câu cụ thể, đa dạng và đúng sự thật hơn.

## Limitations
- Model tự quyết dùng gì từ các đoạn truy hồi; bài không xét việc từ chối hay câu ngoài phạm vi.

## Relevance to our topic
Bài 1 trích ở Related Work ("Who decides") làm gốc của thiết kế RAG. Baseline R của bài 1 là một dạng RAG trong đó model 4B tự quyết trả lời / hỏi lại / từ chối từ 5 thủ tục BGE-M3 tìm được; kết quả là không hơn luôn từ chối về độ chính xác cân bằng.

## Possible improvement
Đo RAG trên câu hỏi có tỉ lệ ngoài phạm vi cao như của bài 1, kèm một bước quyết định riêng trước khi sinh.

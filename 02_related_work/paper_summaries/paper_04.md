# Paper 04 Summary — Kamath2020 — Hỏi đáp có chọn lọc khi dữ liệu lệch miền

Nhóm khuôn B2: **liên quan trực tiếp**. Kiểm chứng: đọc PDF trên ACL Anthology, 25/10/2026; số liệu lấy từ tóm tắt và mục 1 của bài.

## Citation
- Tên bài: Selective Question Answering under Domain Shift
- Tác giả: A. Kamath, R. Jia, P. Liang
- Năm: 2020
- Nguồn: ACL 2020, trang 5684–5696
- DOI: 10.18653/v1/2020.acl-main.503

## Problem
Model hỏi đáp phải biết khi nào nên từ chối, nhất là khi câu hỏi khác dữ liệu nó được huấn luyện.

## Method
Tác giả huấn luyện một bộ hiệu chỉnh (calibrator, dạng random forest) để đoán khi nào model hỏi đáp sẽ trả lời sai, rồi cho model từ chối những câu dễ sai. Bộ hiệu chỉnh được học thêm trên dữ liệu của một miền khác đã biết trước.

Đối chứng là MaxProb: lấy thẳng xác suất softmax của model làm độ tự tin.

## Dataset
- Huấn luyện model hỏi đáp trên SQuAD.
- Năm bộ dữ liệu ngoài miền: NewsQA, TriviaQA, SearchQA, HotpotQA, Natural Questions.
- Kết quả lấy trung bình trên 20 cách ghép một miền "đã biết" với một miền "chưa biết".

## Evaluation
- Đường cong rủi ro theo độ phủ.
- Độ phủ (tỉ lệ câu được trả lời) khi giữ độ chính xác 80%.

## Results
- Bộ hiệu chỉnh trả lời 56,1% số câu mà vẫn giữ độ chính xác 80%.
- MaxProb chỉ trả lời được 48,2% ở cùng mức chính xác.
- Model quá tự tin với dữ liệu ngoài miền.

## Limitations
- Chỉ xét hỏi đáp trích xuất bằng tiếng Anh.
- Bộ hiệu chỉnh cần dữ liệu ngoài miền đã gán nhãn.

## Relevance to our topic
Bài cho thấy xác suất của model không đáng tin với câu hỏi lệch miền. Điều này giải thích vì sao trên câu hỏi thật, cả ngưỡng điểm của reranker (phương án B) lẫn baseline RAG để LLM tự quyết đều không thay được lớp luật.

## Possible improvement
Bài 1 có thể vẽ đường rủi ro theo độ phủ cho điểm reranker trên tập dev, để thấy ngay cả ngưỡng tốt nhất đạt tới đâu.

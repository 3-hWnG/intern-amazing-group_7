# Paper 19 Summary — Gilardi2023: ChatGPT gán nhãn văn bản so với crowd worker

- Nhóm khuôn B2: phương pháp đánh giá (gán nhãn bằng LLM).
- Kiểm chứng: đọc trang tóm tắt arXiv:2303.15056 ngày 27/10/2026; bản đăng PNAS 120(30) e2305016120, DOI 10.1073/pnas.2305016120. Số liệu dưới đây chỉ lấy từ phần tóm tắt trên arXiv; bản PNAS có thể khác cỡ mẫu.
- Lý do thêm: phản biện vòng 2 gợi ý trích khi bàn về độ tin cậy của nhãn do AI đề xuất.

## Citation
- Tên bài: ChatGPT Outperforms Crowd-Workers for Text-Annotation Tasks
- Tác giả: Fabrizio Gilardi, Meysam Alizadeh, Maël Kubli
- Năm: 2023
- Nguồn: Proceedings of the National Academy of Sciences 120(30); arXiv:2303.15056

## Problem
Nhiều nghiên cứu NLP và khoa học xã hội cần nhãn tay chất lượng cao. Thuê crowd worker (như MTurk) rẻ hơn người gán nhãn được đào tạo nhưng chất lượng không đều. Bài hỏi: LLM có thay được crowd worker không.

## Method
- Cho ChatGPT gán nhãn zero-shot, so với crowd worker và người gán nhãn được đào tạo.
- Năm tác vụ gán nhãn tweet, gồm độ liên quan, lập trường, chủ đề và khung (frame).

## Dataset
2.382 tweet (theo tóm tắt arXiv).

## Evaluation
Độ chính xác so với nhãn của người gán nhãn được đào tạo; độ nhất quán giữa các lần gán (intercoder agreement); chi phí mỗi nhãn.

## Results
- Độ chính xác zero-shot của ChatGPT cao hơn crowd worker ở bốn trên năm tác vụ.
- Độ nhất quán của ChatGPT cao hơn cả crowd worker lẫn người được đào tạo ở mọi tác vụ.
- Chi phí dưới 0,003 USD mỗi nhãn, rẻ hơn MTurk khoảng hai mươi lần.

## Limitations
- Chỉ có tweet tiếng Anh và một model; kết quả có thể đổi theo phiên bản model.
- "Đúng" được tính theo nhãn của người được đào tạo, không phải chân lý độc lập.

## Relevance to our topic
Bài 1 trích bài này ở mục Related Work, câu "LLMs can outperform crowd workers on some text-annotation tasks". Nhãn của bài 1 do LLM đề xuất (Claude Opus 5.5 cho dev và test 1; Gemini 4 Argon cho bản gán lần hai và test 2) và trưởng nhóm kiểm lại. Bài này cho thấy nhãn LLM có thể dùng được, nhưng không thay được một bộ nhãn người độc lập. Bài 1 nêu điều này ở Limitations (iii).

## Possible improvement
Áp dụng cho bài 1: lấy một mẫu nhỏ để người gán nhãn độc lập (không biết luật, không thấy nhãn LLM) gán, rồi báo kappa giữa người và từng model.

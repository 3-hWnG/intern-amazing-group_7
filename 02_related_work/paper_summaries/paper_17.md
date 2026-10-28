# Paper 17 Summary — GuidaPA2026: chatbot hành chính công giữ dữ liệu tại chỗ (Ý)

- Nhóm khuôn B2: lĩnh vực ứng dụng.
- Kiểm chứng: đã đọc PDF trong `docs/research paper/01_E-Government_Chatbots/` ngày 25/10/2026. Số liệu lấy từ phần tóm tắt và mục VIII của bài.

## Citation
- Tên bài: GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning
- Tác giả: D. M. Jimenez-Gutierrez, A. Cirillo, R. Nicolussi, A. Beltrame, A. Vitaletti
- Năm: 2026
- Nguồn: arXiv:2606.01386 (preprint)

## Problem
Cơ quan hành chính công Ý cần chatbot học từ tài liệu nội bộ như ticket, sổ tay cán bộ, trích xuất cơ sở dữ liệu. Các tài liệu này không gom về một chỗ được, vì vướng quy định và tổ chức.

## Method
- Tinh chỉnh LLM bằng học liên kết (federated learning).
- Mỗi cơ quan là một client: dữ liệu thô nằm yên tại client, máy chủ chỉ gộp các bản cập nhật.
- Dùng QLoRA 4-bit, chạy 15 vòng liên kết.
- Có phân quyền theo vai trò và tiền xử lý ngay tại client.
- Thử nhiều model 7B–8B tiếng Ý và đa ngôn ngữ: Cerbero, Mistral, Llama-3.1-8B-Instruct…

## Dataset
Tài liệu công khai của hai nền tảng SIGESON và SIDFORS:
- SIGESON khoảng 8 trang hướng dẫn;
- SIDFORS khoảng 31 trang hướng dẫn và FAQ.

Đây là dữ liệu thay thế an toàn cho tài liệu nội bộ. Mỗi client chia 80/20 để huấn luyện và kiểm tra.

## Evaluation
ROUGE, BLEU-4, METEOR.

## Results
- Model liên kết tốt nhất đạt ROUGE-1/2/L 61,10/55,77/59,44, BLEU-4 45,02 và METEOR 63,94. Mức này gần với tinh chỉnh tập trung.
- Tinh chỉnh theo miền nâng ROUGE-1 từ 41,45 lên 62,18 so với model tổng quát.

## Limitations
Tác giả tự nêu các hạn chế sau:
- Chỉ có hai nền tảng, và tài liệu ít.
- Chỉ đo bằng chỉ số tự động, không có người đánh giá, không đo mức hoàn thành tác vụ, không có số liệu từ triển khai thật.
- Chỉ dùng một cách gộp chuẩn.

## Relevance to our topic
Bài 1 trích bài này cho ý "giữ dữ liệu hành chính tại chỗ". Đây là lý do bài 1 dùng model nhỏ chạy trên một máy, để câu hỏi của người dân không phải gửi ra ngoài.

GuidaPA không đo việc từ chối, cũng không đo câu hỏi ngoài phạm vi.

## Possible improvement
Có thể kết hợp với bài 1: cơ quan tinh chỉnh model tại chỗ, còn quyết định trả lời / hỏi lại / từ chối vẫn để luật minh bạch đảm nhận.

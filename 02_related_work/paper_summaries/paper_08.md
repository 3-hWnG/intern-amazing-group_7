# Paper 08 Summary — Qwen3 — Model ngôn ngữ dùng cho phương án C và baseline RAG

Nhóm khuôn B2: **model / phương pháp AI**.

Kiểm chứng ngày 25/10/2026:
- Đã đọc PDF arXiv:2505.09388.
- Đã đọc model card Qwen3-4B-Instruct-2507 trên Hugging Face.

## Citation
- Tên bài: Qwen3 Technical Report
- Tác giả: Qwen Team
- Năm: 2025
- Nguồn: arXiv:2505.09388
- Model card: huggingface.co/Qwen/Qwen3-4B-Instruct-2507 (giấy phép Apache-2.0)

## Problem
Xây dựng một họ model mở, gộp chế độ suy luận nhiều bước (thinking) và chế độ trả lời nhanh (non-thinking) vào cùng một model.

## Method
- Có 6 model dense (0.6B, 1.7B, 4B, 8B, 14B, 32B) và 2 model MoE.
- Có cơ chế "thinking budget" để điều chỉnh lượng suy luận.
- Model nhỏ được huấn luyện bằng chưng cất từ model lớn (strong-to-weak distillation), tốn khoảng 1/10 số giờ GPU so với quy trình bốn giai đoạn.
- Bản Qwen3-4B-Instruct-2507 là bản cập nhật chỉ có chế độ non-thinking:
  - 4,0B tham số, 36 lớp;
  - ngữ cảnh 262.144 token.

## Dataset
- Tiền huấn luyện trên khoảng 36 nghìn tỉ token.
- Hỗ trợ 119 ngôn ngữ và phương ngữ; Qwen2.5 chỉ hỗ trợ 29.

## Evaluation
Các benchmark chung về kiến thức, toán, lập trình, agent và đa ngôn ngữ.

## Results
Theo báo cáo, các model nhỏ cạnh tranh được với model lớn hơn. Bài 1 không dùng các số này.

## Limitations
- Báo cáo tháng 5/2025 không mô tả bản 2507; thông tin về bản này chỉ có trong model card.
- Không có đánh giá riêng cho thủ tục hành chính tiếng Việt.

## Relevance to our topic
Đây là model 4B chạy tại máy, lượng tử hoá 4-bit qua Ollama. Nó được dùng ở hai chỗ:
- phương án C: đọc câu hỏi, trả về ý định và tên thủ tục;
- baseline RAG: model tự quyết định trả lời, hỏi lại hay từ chối.

Model đủ nhỏ để chạy trên một máy tại cơ quan.

## Possible improvement
- So sánh với các model cùng cỡ.
- Thử bật chế độ thinking cho câu dài.
- Lưu ý: bài 1 chỉ chạy một model, một lần, ở temperature 0.

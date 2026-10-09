# Paper 03 Summary: Chain-of-Verification (CoVe - Dhuliawala et al., 2023)

## Citation
- **Title:** Chain-of-Verification Reduces Hallucination in Large Language Models
- **Authors:** Shehzaad Dhuliawala et al.
- **Year:** 2023
- **Venue:** Findings of EMNLP 2023

## Problem
Mô hình LLM khi trả lời câu hỏi thực tế có xu hướng tự tin đưa ra thông tin sai lệch (hallucination) mà người dùng không thể nhận biết.

## Method
Quy trình CoVe gồm 4 bước: (1) Sinh phản hồi ban đầu; (2) Lập kế hoạch các câu hỏi kiểm chứng độc lập; (3) Thực thi các câu hỏi kiểm chứng không để lộ ngữ cảnh ban đầu; (4) Tổng hợp phản hồi cuối cùng đã được kiểm chứng.

## Results & Limitations
- Giảm tỷ lệ ảo giác từ 38% đến 56% trên các tập dữ liệu trích xuất thông tin thực tế.
- Hạn chế: Thời gian sinh câu trả lời tăng gấp 3-4 lần do phải qua nhiều bước trung gian.

## Relevance to Sys_3_4
Sys_3_4 kế thừa tư tưởng phân rã câu trả lời thành các điểm độc lập (`points: [{text, cites}]`) và kiểm tra từng điểm với đoạn bằng chứng gốc trước khi hiển thị cho người dùng.

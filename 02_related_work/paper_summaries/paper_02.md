# Paper 02 Summary: LegalCheck (van der Meer & Rossi, ICAIL 2026)

## Citation
- **Title:** LegalCheck: Municipal Statutory Advice with Grounded Clause Verification
- **Authors:** van der Meer & Rossi
- **Year:** 2026
- **Venue:** International Conference on Artificial Intelligence and Law (ICAIL 2026)

## Problem
Các mô hình sinh ngôn ngữ khi đưa ra lời khuyên pháp lý cho công dân thành phố Amsterdam thường xuyên viện dẫn sai điều khoản pháp luật hoặc suy diễn quy định không có trong văn bản gốc.

## Method
Xây dựng pipeline RAG có cấu trúc kết hợp với bộ xác minh điều khoản căn cứ (Clause Verification Gate) đối chiếu từng câu trả lời với văn bản quy định.

## Dataset
184 vụ việc pháp lý thực tế tại thành phố Amsterdam.

## Evaluation
- Đạt 81.3% Clause Retrieval Precision và 84.1% Factual Consistency.

## Results & Limitations
- Kết quả: Giảm thiểu mạnh hiện tượng sai lệch điều khoản quy định.
- Hạn chế: Độ trễ cao vì sử dụng nhiều vòng gọi LLM để tự kiểm chứng; chi phí tính toán lớn.

## Relevance to Sys_3_4
Cung cấp nền tảng lý thuyết cho bộ kiểm chứng `server/answer/verifier.py` của Sys_3_4: Thay vì gọi LLM lần 2 làm tăng độ trễ, Sys_3_4 thực thi kiểm chứng số liệu bằng thuật toán Regex/Code tất định (<1ms).

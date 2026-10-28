# Paper 29 Summary — bge-reranker-v2-m3: bộ xếp lại cross-encoder (model card)

- Nhóm khuôn B2: phương pháp/model.
- Kiểm chứng: mở model card trên Hugging Face ngày 25/10/2026.

## Citation
- Tên: bge-reranker-v2-m3 (model card)
- Tác giả: BAAI
- Năm: 2024
- Nguồn: https://huggingface.co/BAAI/bge-reranker-v2-m3

## Problem
Không áp dụng (model). Đây là cross-encoder đa ngôn ngữ, chấm độ khớp của từng cặp (câu hỏi, văn bản).

## Method
- Model dựng trên BGE-M3, nhận cặp câu hỏi và văn bản, trả về một điểm liên quan.

## Dataset
Không áp dụng.

## Evaluation
Không áp dụng.

## Results
- Không áp dụng.

## Limitations
- Điểm cao nghĩa là văn bản khớp với câu, không có nghĩa là câu hỏi nằm trong phạm vi.

## Relevance to our topic
Phương án B của bài 1: chấm lại top 8 của luật cùng 10 thủ tục gần nhất theo BGE-M3, từ chối khi điểm thấp, đổi thủ tục khi chênh điểm đủ lớn. Bài 1 thấy reranker cho điểm cao cả với đơn khiếu nại có nhắc tên một thủ tục thật, nên một mình B không quyết định tốt.

## Possible improvement
Kết hợp điểm reranker với một bước phân loại ý định riêng.

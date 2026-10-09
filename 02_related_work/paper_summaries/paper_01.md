# Paper 01 Summary: GuidaPA (Jimenez-Gutierrez et al., 2026)

## Citation
- **Title:** GuidaPA: On-Premise Federated Learning for Municipal Chatbots
- **Authors:** Jimenez-Gutierrez et al.
- **Year:** 2026
- **Source:** IEEE Transactions on E-Government / ArXiv

## Problem
Các cổng dịch vụ công cấp xã/phường có dữ liệu nhạy cảm của người dân, không thể tải lên các API đám mây thương mại (OpenAI, Anthropic). Cần giải pháp huấn luyện và triển khai mô hình trợ lý ngôn ngữ tại chỗ (on-premise).

## Method
Áp dụng Federated Learning kết hợp 4-bit QLoRA qua 15 vòng truyền thông giữa các máy chủ đô thị (SIGESON và SIDFORS).

## Dataset
Tập dữ liệu câu hỏi hành chính công tại các đô thị của Ý.

## Evaluation
- ROUGE-1: 61.10% (so với 62.18% của mô hình tập trung và 41.45% của mô hình gốc chưa fine-tune).
- BLEU-4: 45.02% (so với 26.97% của mô hình gốc).

## Results & Limitations
- Kết quả: Chứng minh mô hình cục bộ triển khai on-premise vẫn đạt độ chính xác gần tương đương mô hình tập trung.
- Hạn chế: Chưa giải quyết vấn đề hội thoại đa lượt kéo dài và chưa có cơ chế kiểm chứng số liệu tiền tệ cứng.

## Relevance to Sys_3_4
Khẳng định định hướng của Sys_3_4: Triển khai mô hình cục bộ tại biên (Local SLM qua Ollama/vLLM) là tiêu chuẩn bắt buộc cho khối hành chính công.

# Paper 02 Summary — Larson2019 — CLINC150: phân loại ý định và câu ngoài phạm vi

Nhóm theo khuôn B2: **liên quan trực tiếp**. Kiểm chứng: đọc PDF trên ACL Anthology ngày 25/10/2026. Số liệu lấy từ mục 2, Bảng 2 và Bảng 3.

## Citation
- Tên bài: An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction
- Tác giả: S. Larson, A. Mahendran, J. J. Peper, C. Clarke, A. Lee, P. Hill, J. K. Kummerfeld, K. Leach, M. A. Laurenzano, L. Tang, J. Mars
- Năm: 2019
- Nguồn: EMNLP-IJCNLP 2019, trang 1311–1316
- DOI: 10.18653/v1/D19-1131

## Problem
Trợ lý hướng tác vụ phải nhận ra câu nằm ngoài các ý định mà nó hỗ trợ. Các bộ dữ liệu trước đó lại giả định câu nào cũng thuộc một nhãn.

## Method
Tác giả so nhiều bộ phân loại: SVM, MLP, FastText, CNN, BERT, DialogFlow và Rasa.

Có ba cách nhận câu ngoài phạm vi:
- **oos-train**: thêm một lớp thứ 151 cho câu ngoài phạm vi.
- **oos-threshold**: đặt ngưỡng trên xác suất của bộ phân loại.
- **oos-binary**: phân loại hai tầng.

## Dataset
- 23.700 câu do crowdworker viết.
- Trong phạm vi: 22.500 câu, thuộc 150 ý định trong 10 miền.
- Ngoài phạm vi: 1.200 câu, trong đó 1.000 câu dùng để kiểm tra.
- Có các biến thể Small, Imbalanced và OOS+.

## Evaluation
- Độ chính xác trên 150 ý định.
- Recall của câu ngoài phạm vi.

## Results
- BERT đạt độ chính xác trong phạm vi từ 96% trở lên.
- Recall ngoài phạm vi tốt nhất chỉ khoảng 66%: Rasa, cách oos-train, biến thể OOS+ (Bảng 2).
- Với cách oos-threshold trên bộ Full, BERT chỉ đạt recall ngoài phạm vi 52,3%.

## Limitations
- Câu ngắn do crowdworker viết, không phải câu thật của người dùng.
- Tiếng Anh, miền tổng quát.

## Relevance to our topic
Kết quả cùng chiều với phát hiện của bài 1: hệ thống làm tốt câu trong phạm vi nhưng kém khi phải nhận ra câu ngoài phạm vi. Bài 1 bổ sung bằng chứng trên câu hỏi thật, dài, của người dân Việt Nam. Ở đó câu ngoài phạm vi lại là đa số.

## Possible improvement
Báo cáo recall của nhóm "từ chối" theo từng loại ý định ngoài phạm vi: tình trạng hồ sơ, khiếu nại, hỏi luật, nội bộ. Cách này tương tự việc CLINC150 tách riêng câu ngoài phạm vi.

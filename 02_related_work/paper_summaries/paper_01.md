# Paper 01 Summary — PhamDuy2023 — Hỏi đáp dịch vụ công tiếng Việt (công trình gần nhất)

Nhóm theo khuôn B2: **liên quan trực tiếp**.

Kiểm chứng: đọc PDF gốc (bản tác giả trên users.soict.hust.edu.vn) ngày 25/10/2026. Số liệu lấy từ mục 3.2 và Bảng 7–8 của bài.

## Citation
- Tên bài: A Question-Answering System for Vietnamese Public Administrative Services
- Tác giả: Anh Pham Duy, Huong Le Thanh (Đại học Bách khoa Hà Nội)
- Năm: 2023
- Nguồn: Proceedings of the 12th International Symposium on Information and Communication Technology (SoICT 2023), ACM, 8 trang
- DOI: 10.1145/3628797.3628965 (bản PDF in thiếu tiền tố "10.1145/")

## Problem
Tìm đoạn văn bản luật trả lời câu hỏi về dịch vụ công. Câu trả lời là **một đoạn trong văn bản pháp luật**, không phải bản ghi thủ tục.

## Method
Hai khối truy hồi, kết quả được gộp lại:
- Khối từ vựng: BM25+ trên văn bản đã tách từ bằng Pyvi, rồi xếp lại bằng bi-encoder và cross-encoder.
- Khối ngữ nghĩa: SimCSE + FAISS, rồi xếp lại bằng BM25+.

Khi huấn luyện SimCSE có tăng cường dữ liệu.

## Dataset
- Kho luật: 24.911 văn bản, 312.061 điều khoản, cắt thành 785.996 đoạn dưới 256 từ. Nguồn là Thư viện Pháp luật và Cổng DVC.
- Bộ hỏi đáp: 4.547 cặp từ trang "câu hỏi phổ biến" của Cổng DVC Quốc gia, gồm 4.000 cặp huấn luyện và 547 cặp kiểm tra.
- Câu hỏi không có câu trả lời bị loại ở bước tiền xử lý (mục 3.1).

## Evaluation
Recall@k, F2@k, MAP@k và NDCG@k cho bước truy hồi đoạn luật.

## Results
- Bảng 7: hệ gộp đạt Recall 0,8895, MAP 0,6281, NDCG 0,7110. Mô hình của Pham et al. đạt Recall 0,6265.
- Bảng 8 (top-5): Recall 0,7666, F2 0,4955, MAP 0,6513, NDCG 0,6918.
- Mỗi câu hỏi mất khoảng 15 giây.

## Limitations
- Mọi câu hỏi đều có đáp án, nên không đo được việc từ chối hay hỏi lại.
- Câu hỏi là FAQ do cổng soạn sẵn, không phải thư thật của người dân.
- Chỉ đo bước truy hồi, không đo câu trả lời cuối cùng.

## Relevance to our topic
Đây là công trình gần nhất về dịch vụ công tiếng Việt, và là căn cứ cho khoảng trống của bài 1. Bài này loại các câu không có đáp án và dùng FAQ chính thức. Bài 1 đo trên câu hỏi thật, trong đó khoảng 79% phải từ chối.

## Possible improvement
- Đặt lớp quyết định (trả lời / hỏi lại / từ chối) trước bước truy hồi.
- Đánh giá trên câu hỏi thật, chưa qua lọc.
- Báo cáo thêm độ chính xác cân bằng (balanced accuracy), không chỉ Recall.

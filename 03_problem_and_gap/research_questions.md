# Câu hỏi nghiên cứu (khuôn B4)

Giữ đúng 3 câu hỏi như trong `contribution_analysis.md` mục 3.

- **RQ1.** Đánh giá trên bộ câu do nhóm tự viết lệch bao nhiêu so với câu hỏi thật của người dân? Xét ba mặt: hành vi đúng, top-1, và tỷ lệ từ chối đúng.
- **RQ2.** Trên câu hỏi thật đã khoá trước, một lớp luật minh bạch quyết định trả lời / hỏi lại / từ chối cải thiện được bao nhiêu? Lớp luật có làm tụt kết quả trên bộ cũ không?
- **RQ3.** So với lớp luật, các thành phần học máy có sẵn làm được đến đâu? Xét ba cách dùng:
  - reranker dạng cross-encoder;
  - model 4B chạy tại máy đọc câu hỏi;
  - baseline "RAG + model 4B tự quyết định".

  Mỗi thành phần được thử khi dùng một mình và khi ghép với lớp luật. Thêm sau (*post hoc*, theo phản biện): hai cổng ngoài phạm vi học từ nhãn dev (naive Bayes; hồi quy logistic trên embedding BGE-M3), đặt thay cổng viết tay trên bản gốc.

Ghi chú: sau vòng cải thiện thứ hai, số "sau cải thiện" chỉ được báo trên bộ test thứ hai (real_v4), khoá trước khi sửa code (D12).

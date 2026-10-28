# Problem statement (khuôn B4, bước 5)

## 1. Vấn đề thực tế

Trợ lý trả lời câu hỏi về **thủ tục hành chính cấp xã/phường** phải chọn một trong ba việc trước khi trả lời:
- **trả lời**, khi có đúng một thủ tục phù hợp;
- **hỏi lại**, khi nhiều thủ tục cùng khớp;
- **từ chối**, khi câu hỏi nằm ngoài những gì dữ liệu thủ tục trả lời được. Ví dụ: hỏi tình trạng hồ sơ đã nộp, khiếu nại, hỏi mức phạt, hỏi chế độ nội bộ ngành công an, hay hỏi thủ tục do cấp tỉnh hoặc bộ giải quyết.

Người dân không hỏi bằng ngôn ngữ của cổng dịch vụ công. Họ viết như viết thư: có lời chào, câu chuyện gia đình, chữ viết tắt, thường không dấu, và câu hỏi thật nằm đâu đó trong thư.

**Phạm vi.** Trợ lý chỉ phục vụ thủ tục cấp xã/phường, gồm xã, phường và đặc khu. Đây **không** phải trợ lý cho mọi thủ tục hành chính toàn quốc (quyết định của nhóm, constraints.md D13).

## 2. Vì sao quan trọng

- Trả lời sai một câu đáng lẽ phải từ chối là đưa ra hướng dẫn sai một cách tự tin. Người dân có thể lỡ hạn hoặc mất quyền lợi (GovAIPipe2026, paper 15).
- Trong 313 câu hỏi thật của bộ test, 79% phải từ chối. Hệ thống trước nghiên cứu này trả lời nhầm gần một nửa số câu đó (114/248).
- Mục tiêu thiết kế của nhóm: chạy được trên một máy tại chỗ, để câu hỏi của người dân không phải gửi ra ngoài; vì vậy model phải nhỏ. Nhu cầu giữ dữ liệu hành chính tại chỗ cũng được nêu ở GuidaPA (arXiv:2606.01386).

## 3. Các bài trước giải quyết thế nào

- **Hỏi đáp dịch vụ công và pháp lý tiếng Việt** (paper 01, 12, 13): tập trung vào truy hồi và sinh câu trả lời. Chỉ đánh giá câu hỏi có đáp án.
- **Từ chối và câu ngoài phạm vi** (paper 02–06): dùng bộ phân loại có ngưỡng, calibrator, hoặc model tự quyết.
- **Rào chắn** (paper 07): luật do người viết, chạy độc lập với model.

## 4. Hạn chế của các bài trước

Chi tiết ở `research_gap.md` và `02_related_work/literature_review_matrix.md`.

- Không đo việc từ chối trên câu hỏi thật về dịch vụ công.
- Không có so sánh có kiểm soát giữa "luật quyết định" và "model quyết định" trên cùng một tập test khoá trước.

## 5. Nhóm cải tiến điểm nào

- Một lớp luật minh bạch đọc thư của người dân, gồm:
  - bỏ phần chào hỏi;
  - từ điển chuyển từ ngữ người dân dùng sang tên thủ tục;
  - cổng chặn các ý định ngoài phạm vi;
  - mặc định chọn thủ tục cho cá nhân hay tổ chức.
- So sánh lớp luật với reranker, với model 4B chạy tại máy, và với baseline "RAG + model 4B tự quyết định".

## 6. Đóng góp

Bản nháp; chi tiết ở `contribution_analysis.md` mục 4.

1. Bộ câu hỏi thật đã gán nhãn ba hành vi. Lượt nhãn thứ hai cho độ đồng thuận κ = 0,685.
2. Số đo khoảng cách giữa bộ câu nhóm tự viết và câu hỏi thật, trên cùng một hệ thống đã đóng băng (RQ1).
3. Lớp luật: tăng số câu trả lời đúng mà không làm tụt kết quả trên bộ cũ (RQ2).
4. So sánh có kiểm soát với các thành phần học máy, kể cả những cấu hình thua (RQ3).

Khoảng trống nghiên cứu: `research_gap.md`. Câu hỏi nghiên cứu: `research_questions.md`.

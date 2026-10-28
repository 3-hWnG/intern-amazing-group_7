# Literature Review Analysis

Bản tóm tắt phân tích. Bảng chi tiết ở `literature_review_matrix.md`, từng bài ở `paper_summaries/`.

## 1. Hỏi đáp dịch vụ công và pháp lý tiếng Việt (paper 01, 12, 13)

Các công trình tập trung vào truy hồi văn bản luật hoặc sinh câu trả lời bằng LLM. Câu hỏi đánh giá:
- hoặc là FAQ do cổng soạn, và câu không có đáp án đã bị loại (paper 01);
- hoặc là bộ câu tự dựng hay khảo sát người dùng (paper 12, 13).

Chưa bài nào đo việc **từ chối** hay **hỏi lại**. Hien2025 có bước phân loại câu ngoài phạm vi nhưng không đo riêng bước này.

## 2. Từ chối và câu ngoài phạm vi (paper 02–06)

Ba bài cho cùng một bài học: hệ thống làm tốt câu trong phạm vi nhưng không biết khi nào nên dừng.
- **Paper 02:** BERT đạt ≥ 96% độ chính xác trong phạm vi, nhưng recall câu ngoài phạm vi tốt nhất chỉ khoảng 66%.
- **Paper 03:** điểm F1 giảm từ 86% xuống 66% khi thêm câu không trả lời được.
- **Paper 04:** xác suất của model quá tự tin trên dữ liệu lệch miền.

Paper 06 (khảo sát) xếp các cách làm thành ba nhóm: xử lý đầu vào, xử lý trong lúc sinh, và hậu xử lý. Bài cũng ghi nhận việc từ chối ở ngôn ngữ ít tài nguyên còn kém.

Paper 05 coi hỏi lại là lựa chọn thứ ba, nằm giữa trả lời và từ chối.

## 3. Ai quyết định: luật hay model (paper 07, 10, 11)

- **Model tự quyết:** Self-RAG tự quyết khi nào truy hồi và tự phê bình (paper 11).
- **Bộ đánh giá nhẹ quyết định:** CRAG chọn hành động dựa trên kết quả truy hồi (paper 10).
- **Luật do người viết quyết định:** NeMo Guardrails dùng luật chạy độc lập với model (paper 07).

Bài 1 so sánh trực tiếp ba hướng này trên cùng một tập test đã khoá trước.

## 4. Bối cảnh khu vực công (paper 14–16)

- Các hệ thống cho cơ quan công đề cao việc có người duyệt (paper 14), có quy trình quản trị (paper 15), và tính "trung thực", tức biết thừa nhận khi không biết (paper 16).
- Paper 16 thấy rằng model trả lời đúng nhiều chưa chắc đã biết thừa nhận giới hạn của mình.
- Paper 15 nêu rủi ro khi chatbot hướng dẫn sai: người dân có thể lỡ hạn hoặc mất quyền lợi.

## 5. Kết luận và phần kế thừa

Phần kế thừa từ các bài trên:
- Đo riêng việc từ chối và dùng độ chính xác cân bằng (theo paper 02, 06).
- Không tin vào điểm tự tin của model khi gặp câu lệch miền (theo paper 04).
- Để luật minh bạch quyết định, theo hướng của paper 07, nhưng đo hiệu quả trên câu hỏi thật.

Khoảng trống bài 1 lấp: chưa có bài nào đo cả ba hành vi trên **câu hỏi thật** của người dân về thủ tục **cấp xã/phường** ở Việt Nam, với tập test khoá trước khi sửa code (`03_problem_and_gap/research_gap.md`).

## 6. Bổ sung 27/10 (paper 17–19)

- **Paper 17 (GuidaPA2026):** chatbot hành chính công giữ dữ liệu tại chỗ bằng học liên kết. Bài 1 dựa vào ý này để chạy model nhỏ trên một máy.
- **Paper 18 (Geifman2017):** phân loại có chọn lọc, đổi độ phủ lấy rủi ro thấp. Bài 1 dùng ý này ở Discussion: với độ chính xác câu trả lời thấp trên câu ngẫu nhiên, trợ lý nên để cán bộ xác nhận hoặc chỉ trả lời khi đủ tin cậy. Đây cũng là hướng tương lai.
- **Paper 19 (Gilardi2023):** ChatGPT gán nhãn văn bản tốt hơn crowd worker ở 4/5 tác vụ. Bài 1 dùng bài này khi bàn về nhãn do LLM đề xuất (Related Work, Limitations); nhãn LLM dùng được nhưng không thay một bộ nhãn người độc lập.

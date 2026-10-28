# Topic Proposal (khuôn bước 1)

## Tên đề tài

**Answer, Clarify or Refuse? Rules, a Reranker and a Small LLM on Real Citizen Questions about Commune-Level Administrative Procedures in Vietnam**

Tạm dịch: Trả lời, hỏi lại hay từ chối? Luật, bộ xếp lại và một LLM nhỏ trên câu hỏi thật của người dân về thủ tục hành chính cấp xã ở Việt Nam.

Tên làm việc lúc lập đề xuất (25/10): *When Rules Should Decide: Answering, Clarifying and Refusing Real Citizen Questions about Commune-Level Administrative Procedures in Vietnam* (xem `topic_revision_log.md`).

## Lĩnh vực ứng dụng

Dịch vụ công, cụ thể là thủ tục hành chính **cấp xã/phường**: hộ tịch, cư trú, căn cước, chứng thực, trợ cấp…

Đề tài **không** nhắm tới mọi thủ tục hành chính toàn quốc.

## Vấn đề thực tế

Người dân hỏi theo kiểu viết thư: dài, kể chuyện, thường không dấu. Phần lớn câu hỏi thật không hỏi cách làm một thủ tục, mà hỏi về:
- tình trạng hồ sơ đã nộp;
- khiếu nại;
- mức phạt;
- chế độ nội bộ.

Trợ lý trả lời những câu này bằng dữ liệu thủ tục sẽ đưa ra hướng dẫn sai mà trông vẫn rất chắc chắn.

## Đối tượng người dùng

- Người dân.
- Cán bộ bộ phận một cửa cấp xã.

## Lý do cần tích hợp AI

- Câu hỏi đa dạng, nhiều cách diễn đạt; tra từ khoá đơn thuần không hiểu được.
- Đề tài kiểm tra xem AI giúp được tới đâu so với một lớp luật minh bạch. Hai thành phần AI được thử:
  - reranker;
  - model ngôn ngữ nhỏ chạy tại máy.
- Đề tài **không đề xuất model mới**. Nó khảo sát cách tích hợp model có sẵn và đánh giá trong bối cảnh thực tế (khuôn B9).

## Model AI sử dụng

- Qwen3-4B-Instruct-2507: 4-bit, chạy tại máy qua Ollama.
- BGE-M3.
- bge-reranker-v2-m3.

Chi tiết ở `04_proposed_system/ai_model_integration.md`.

## Kết quả mong muốn

1. Số đo khoảng cách giữa bộ câu nhóm tự viết và câu hỏi thật (RQ1).
2. Một lớp luật cải thiện rõ trên tập test đã khoá trước, không làm tụt kết quả trên bộ cũ (RQ2).
3. So sánh có kiểm soát với các thành phần AI và với baseline "RAG + LLM tự quyết" (RQ3).
4. Một bài báo nộp tạp chí Vietnam Journal of Computer Science, khoảng 10 trang.

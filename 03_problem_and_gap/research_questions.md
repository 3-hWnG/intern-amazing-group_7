# Research Questions

## Main Research Question
Làm thế nào để xây dựng một hệ thống trợ lý AI pháp lý phục vụ thủ tục hành chính công cấp cơ sở vừa đảm bảo độ chính xác tuyệt đối không ảo giác về mặt số liệu, vừa giao tiếp tự nhiên qua đàm thoại đa lượt với độ trễ thấp và triển khai hoàn toàn cục bộ?

## Sub Research Questions

- **RQ1 (Retrieval Accuracy & Hybrid Engine):** Kiến trúc truy hồi kết hợp giữa bộ lọc âm tiết IDF có phạt lệch dấu thanh (System 3) và tìm kiếm vector lai BGE-M3/Qdrant (System 4) cải thiện độ chính xác Top-1 và Top-3 như thế nào so với các mô hình baseline thông thường?
- **RQ2 (Multi-turn Context & Clarify Isolation):** Cơ chế quản lý trạng thái hội thoại có cô lập lượt làm rõ (*Clarify State Isolation*) nâng cao tỷ lệ giải quyết câu hỏi ngữ cảnh đa lượt và xử lý đại từ thay thế đạt mức độ nào?
- **RQ3 (Zero-Hallucination Fact Verification):** Bộ kiểm chứng hậu kỳ tất định (`verify_point`) giúp loại bỏ bao nhiêu phần trăm ảo giác số liệu tài chính và viện dẫn sai căn cứ pháp lý trong câu trả lời của mô hình ngôn ngữ?
- **RQ4 (Latency & Edge Efficiency):** Hiệu năng xử lý (độ trễ p50, p95) và khả năng triển khai on-premise của hệ thống đáp ứng yêu cầu phục vụ thời gian thực tại các cơ quan hành chính công như thế nào?

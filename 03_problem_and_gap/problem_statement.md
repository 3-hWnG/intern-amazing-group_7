# Problem Statement

## 1. Bối cảnh Thực tế
Thủ tục hành chính công cấp xã/phường tại Việt Nam trực tiếp điều chỉnh đời sống của hơn 100 triệu người dân thông qua các dịch vụ thiết yếu: hộ tịch, khai sinh, kết hôn, khai tử, xác nhận tình trạng hôn nhân, đăng ký cư trú, cấp giấy phép xây dựng nhà ở, bảo hiểm y tế và trợ cấp bảo trợ xã hội.

Chính phủ Việt Nam đã triển khai Đề án 06 nhằm số hóa toàn bộ quy trình dịch vụ công. Tuy nhiên, tỷ lệ công dân tự thực hiện thành công dịch vụ công trực tuyến còn hạn chế, dẫn đến việc người dân vẫn phải đến trực tiếp Bộ phận Một cửa để hỏi đáp và bổ sung hồ sơ nhiều lần.

## 2. Vấn đề Kỹ thuật Cốt lõi
Khi xây dựng trợ lý AI hỗ trợ công dân, các hệ thống chatbot và RAG truyền thống gặp phải 4 thất bại nghiêm trọng:
1. **Thất bại truy hồi ngôn ngữ tiếng Việt:** Người dân sử dụng từ ngữ đời thường (*"làm giấy khai sinh"*, *"xin trích lục"*, *"ly dị"*, *"sao y"*), viết tắt (*"cccd"*, *"gks"*, *"hkd"*), gõ không dấu (*"kethon co mat phi khong"*). Các mô hình truy hồi vector Dense Embeddings tiêu chuẩn bị hiện tượng "trôi ngữ nghĩa" (semantic drift), nhầm lẫn giữa các thủ tục có từ ngữ tương đồng nhưng bản chất pháp lý khác hẳn (*"Cấp mới"* vs *"Cấp lại / Gia hạn / Thay đổi"*).
2. **Ảo giác số liệu pháp lý nguy hại:** Các mô hình LLM có xu hướng "bịa" mức lệ phí (ví dụ khẳng định kết hôn mất 500.000đ hoặc tự ý cam kết "hoàn toàn miễn phí"), bịa thời hạn giải quyết, gây khiếu nại hành chính và bức xúc xã hội.
3. **Mất dấu ngữ cảnh trong đàm thoại đa lượt:** Khi người dân hỏi nối câu (*"thế mất bao lâu?"*, *"nếu ở quê thì sao?"*, *"quay lại cái lúc nãy"*), chatbot mất ngữ cảnh, kế thừa nhầm chủ đề hoặc bị ô nhiễm bộ nhớ khi người dùng phản hồi các câu hỏi làm rõ.
4. **Rào cản triển khai cục bộ (Data Sovereignty):** Quy định bảo vệ dữ liệu cá nhân không cho phép gửi thông tin công dân ra các máy chủ API nước ngoài, đòi hỏi hệ thống phải hoạt động 100% on-premise với chi phí phần cứng thấp.

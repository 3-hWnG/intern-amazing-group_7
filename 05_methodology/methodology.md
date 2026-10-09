# Methodology

Nghiên cứu áp dụng phương pháp luận phát triển hệ thống kết hợp thực nghiệm so sánh định lượng:

## 1. Thiết kế Kiến trúc Kép (Dual-Engine Decoupling)
Hệ thống phân chia nhiệm vụ rõ ràng:
- **Strict Engine (Tất định):** Tối ưu hóa cho các thao tác tra cứu dữ liệu pháp lý đã được công bố trên cổng dịch vụ công. Áp dụng quy tắc "nói có sách, mách có chứng", không suy diễn số liệu khi cổng không công bố (`absent_confirmed`).
- **Friendly Engine (Đàm thoại & Linh hoạt):** Tối ưu cho trải nghiệm giao tiếp, trả lời các thắc mắc đời sống của người dân và tra cứu trên các tập dữ liệu mở rộng do người dùng cung cấp.

## 2. Thuật toán Xếp hạng Âm tiết có Phạt lệch Dấu thanh
Điểm số của một thủ tục ứng viên $p$ đối với câu hỏi $q$ được tính theo công thức:
$$\text{Score}(p, q) = \text{Cov}(p, q) \times \text{Prec}(p, q) \times \prod \text{Penalties}$$
Trong đó:
- $\text{Cov}(p, q)$: Độ phủ âm tiết của câu hỏi trên tên lõi thủ tục, tính theo trọng số nghịch đảo tần suất văn bản (IDF).
- $\text{Prec}(p, q)$: Độ chính xác âm tiết (tỷ lệ âm tiết khớp chia cho độ dài tên thủ tục).
- Phạt lệch dấu: Nếu âm tiết gõ có dấu nhưng lệch dấu thanh với âm tiết trong kho $\rightarrow$ nhân trọng số $0.35$.
- Phạt vòng đời (`LIFECYCLE_PENALTY`): Thủ tục có tiền tố *cấp lại, đổi, gia hạn* mà câu hỏi không nhắc đến $ightarrow$ bị trừ điểm ưu tiên bản gốc.

## 3. Thuật toán Quản lý Trạng thái Ngữ cảnh Đa lượt
Lưu giữ đối tượng `ConvState`:
- `topic`: Thủ tục đang trao đổi.
- `history`: Lịch sử các thủ tục đã nhắc đến theo thứ tự thời gian.
- `fields`: Danh sách các trường thông tin đang hỏi dở.
- `is_clarify`: Cờ đánh dấu lượt hỏi lại làm rõ $ightarrow$ cô lập hoàn toàn không để ghi đè vào `topic`.

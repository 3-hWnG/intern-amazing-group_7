# AI Model Integration

## 1. Mô hình AI sử dụng
Hệ thống tích hợp có chọn lọc các mô hình trí tuệ nhân tạo chuyên sâu:

| Mô hình | Vai trò trong hệ thống | Kích thước / Chiều | Nơi lưu trữ / Runtime |
|---|---|---|---|
| **BGE-M3** | Biểu diễn ngữ nghĩa câu hỏi và tài liệu người dùng nạp | 1024 chiều (Dense) | Ollama Local Client (`dim=1024`) |
| **BGE-Reranker-v2-m3** | Xếp hạng lại top ứng viên sau khi trộn RRF | Cross-Encoder 560M | PyTorch on CUDA / CPU (`models/bge-reranker-v2-m3`) |
| **Qwen2.5-7B-Instruct** | Sinh văn bản đàm thoại, giải thích điều kiện, so sánh | 7 tỷ tham số (Q4_K_M) | Ollama Server Local (`keep_alive=30m`) |
| **Statistical Syllable IDF** | Xếp hạng thủ tục tất định không LLM | Bảng tra cứu âm tiết | CSDL SQLite `system3.db` |

## 2. Lý do lựa chọn mô hình
- **Qwen2.5-7B-Instruct:** Là mô hình mã nguồn mở hàng đầu hiện nay về khả năng hiểu tiếng Việt, tuân thủ định dạng JSON Schema hoàn hảo và có chi phí VRAM thấp (~5GB khi chạy lượng tử hóa 4-bit).
- **BGE-M3:** Hỗ trợ đa ngôn ngữ vượt trội, tối ưu hóa cho tiếng Việt và hỗ trợ độ dài đoạn văn bản lên tới 8.192 tokens.
- **BGE-Reranker-v2-m3:** Khắc phục nhược điểm mất thông tin tương quan chéo của mô hình bi-encoder, nâng cao độ chính xác trích xuất đoạn văn.

## 3. Cách thức tích hợp vào ứng dụng
- Tích hợp qua REST API bất đồng bộ và cơ chế gọi bọc có ngân sách thời gian (`budgeted(llm, total=7.0)`).
- Ép định dạng đầu ra qua JSON Schema:
  ```json
  {
    "type": "object",
    "required": ["points"],
    "properties": {
      "points": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["text", "cites"],
          "properties": {
            "text": {"type": "string"},
            "cites": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    }
  }
  ```
- Nếu LLM không phản hồi trong 7 giây hoặc gặp lỗi mạng $ightarrow$ Hệ thống tự động kích hoạt phương án dự phòng bằng Code tất định (`fallback to rule answerer`), đảm bảo trải nghiệm người dùng không bao giờ bị gián đoạn.

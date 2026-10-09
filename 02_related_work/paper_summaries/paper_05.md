# Paper 05 Summary: Shakti SLM (Aralimatti et al., 2025)

## Citation
- **Title:** Shakti: Small Language Models on the Edge for Public Governance
- **Authors:** Aralimatti et al.
- **Year:** 2025
- **Venue:** EdgeAI Workshop

## Problem
Các cơ quan quản trị công đòi hỏi mô hình trí tuệ nhân tạo phải chạy trực tiếp trên phần cứng máy trạm cục bộ, VRAM dưới 4GB, đảm bảo chi phí vận hành bằng 0.

## Method
Fine-tune các mô hình ngôn ngữ nhỏ 1.5B–3B sử dụng QLoRA và tối ưu hóa bộ nhớ đệm KV.

## Results & Limitations
- Đạt 86.4% độ chính xác nghiệp vụ với mức tiêu thụ VRAM chỉ <3.8 GB, tốc độ 24 tokens/giây.
- Hạn chế: Khả năng suy luận trên chuỗi hội thoại dài bị suy giảm rõ rệt so với mô hình 7B+.

## Relevance to Sys_3_4
Chứng minh tính khả thi của việc sử dụng mô hình mã nguồn mở nội bộ (như Qwen2.5-7B lượng tử hóa 4-bit) kết hợp bộ lọc ngữ cảnh tất định của Sys_3_4 để vừa đảm bảo độ chính xác vừa tiết kiệm phần cứng.

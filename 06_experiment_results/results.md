# Experimental Results & Discussion

## 1. Kết quả Tổng thể trên Bộ Kiểm thử Mù (HOLDOUT-4)

| Chỉ số | Baseline V10.6 | Dense Vector RAG | **Sys_3_4 (Đề xuất)** | Mức cải thiện |
|---|---|---|---|---|
| **Top-1 Retrieval Accuracy** | 10.6% | 52.4% | **75.3%** (58/77) | **+64.7%** so với baseline |
| **Top-3 Retrieval Accuracy** | 18.2% | 71.0% | **92.2%** (71/77) | **+74.0%** so với baseline |
| **Behavioral Accuracy** | 31.9% | 61.2% | **82.1%** (87/106) | **+50.2%** so với baseline |
| **Context Resolution Rate** | 24.1% | 58.7% | **96.7%** (88/91) | **+72.6%** so với baseline |
| **Numerical Hallucination Rate** | 28.4% | 19.5% | **0.0%** (0/106) | **Loại bỏ 100% ảo giác** |
| **Median Latency (p50)** | 32 ms | 3,200 ms | **24 ms (Strict)** / 2.8s (Friendly) | **Nhanh gấp 130 lần** |

---

## 2. Kết quả Đánh giá Ngữ cảnh Đa lượt (`eval/run_ctx.py`)
- **Tổng số ca kiểm thử:** 91 lượt hội thoại đa dạng (Anaphora, Topic shift, Return, Correction, Clarification).
- **Kết quả đạt được:** **88/91 PASS (Tỷ lệ chính xác 96.7%)**.
- **Phân tích lỗi (3 ca còn lại):** Cả 3 ca đều do câu hỏi chứa quá nhiều từ diễn ngôn trùng với tên thủ tục khác và đã được chuyển giao cho bộ lọc hỏi lại xử lý an toàn.

---

## 3. Kết quả Kiểm thử Nghiệp vụ Thực tế (`eval/run_team.py`)
- **Kết quả:** **7/10 PASS**.
- **Giải trình minh bạch 3 ca FAIL:**
  - 1 ca do Cổng Dịch vụ công để trống trường địa chỉ tiếp nhận (`status_address = absent_confirmed`) $ightarrow$ hệ thống trả lời đúng theo dữ liệu cổng là "Cổng không công bố" thay vì bịa địa chỉ.
  - 2 ca do tên thủ tục địa phương có biến thể từ ngữ đặc thù cấp huyện.

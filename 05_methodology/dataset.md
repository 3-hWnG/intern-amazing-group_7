# Dataset Specification

## 1. Dữ liệu Thủ tục Hành chính Cơ sở (Baseline Corpus)
- **Nguồn dữ liệu:** Cào và chuẩn hóa từ Cổng Dịch vụ công Quốc gia (`dichvucong.gov.vn`) theo danh mục cấp xã/phường.
- **Quy mô:**
  - **1.350 thủ tục hành chính** đang hiệu lực (736 bản công bố cấp bộ/ngành, 614 bản riêng của các tỉnh/thành phố).
  - **17.133 lát cắt trường dữ liệu (`field_chunks`)** bao phủ 12 trường nghiệp vụ.
  - **3.339 dòng lệ phí sạch (`fees_clean`)**: 138 bản ghi có số tiền cụ thể, 329 bản ghi có văn bản mô tả, 883 bản ghi cổng không công bố lệ phí.
  - **930 họ thủ tục (`families`)** với 84 họ có nhiều hơn 1 biến thể con.
  - **5.952 chỉ mục điều kiện (`condition_index`)** phục vụ nhận diện đối tượng và hoàn cảnh.

## 2. Các Tập Dữ liệu Đánh giá (Evaluation Benchmarks)
1. **DEV Benchmark (209 trường hợp):** Bộ dữ liệu tinh chỉnh tham số nội bộ, kiểm tra độ phủ âm tiết và từ khóa viết tắt.
2. **HOLDOUT-4 Benchmark (90 trường hợp / 106 lượt thoại):** Bộ dữ liệu kiểm thử mù hoàn toàn không tham gia huấn luyện/tune tham số, chứa các câu hỏi viết tắt, dính chữ, gõ không dấu và hội thoại đa lượt phức tạp.
3. **Multi-turn Context Benchmark (`eval/cases_ctx.py` - 91 lượt):** Bộ kiểm tra chuyên sâu về anaphora, đổi chủ đề, quay lại chủ đề cũ và sửa ý.
4. **Real-world Team Benchmark (`eval/cases_team.py` - 10 câu hỏi):** 10 câu hỏi nghiệp vụ thực tế do các chuyên viên kiểm thử độc lập biên soạn.

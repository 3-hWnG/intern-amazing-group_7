# Bộ câu mù thứ ba (real_v3) cho "biên dịch lĩnh vực lúc nạp" của System 4, 24/10/2026

Mục tiêu đo: **thêm một lĩnh vực mới bằng cách tải tệp lên, không viết hệ thống mới**. Engine biên dịch lúc nạp (đường nhanh `system4/server/fastpath`) được làm và chỉnh trên dữ liệu tự sinh (du lịch, cửa hàng) và đã bị xem kết quả trên hai bộ mù đó. Bộ này dùng **dữ liệu thật engine chưa từng gặp**, ở 4 lĩnh vực, viết và khoá **trước** khi sửa engine.

| Lĩnh vực | Tệp (`data/`) | Nội dung | Nguồn (Wikipedia tiếng Việt, CC BY-SA 4.0) |
|---|---|---|---|
| Hành chính | `hanh_chinh_tinh_thanh.xlsx` | 34 tỉnh/thành sau sáp nhập 2025: trung tâm hành chính, vùng, năm thành lập, diện tích, dân số, mật độ, số phường / xã / đặc khu | "Đơn vị hành chính cấp tỉnh (Việt Nam)", revid 75581808 |
| Giao thông | `giao_thong_san_bay.xlsx` | 22 sân bay dân dụng, 2 sheet: mã, tỉnh, đường băng, cấp; năng lực khai thác, sản lượng 2023 | "Danh sách sân bay tại Việt Nam", revid 75639956 |
| Môi trường | `moi_truong_vuon_quoc_gia.xlsx` | 37 vườn quốc gia: vùng, năm thành lập, diện tích (ha), địa điểm (có ô nhiều tỉnh) | "Danh sách vườn quốc gia tại Việt Nam", revid 75659364 |
| Năng lượng | `nang_luong_thuy_dien.xlsx` | 372 nhà máy thủy điện: quy mô, công suất, sản lượng, năm khởi công / hoạt động, sông, vị trí | "Danh sách thủy điện tại Việt Nam", revid 75522391 |

`build_v3.py` tải đúng 4 phiên bản (revid) đó rồi dựng tệp: chỉ trải ô gộp, bỏ chú thích và cột toạ độ, đổi số đứng riêng sang ô số theo cách viết của từng cột; ô có chữ ("Côn Đảo (1945)", "Bê tông 3.051 m", "11/1979", "?") giữ nguyên. Không thêm, không sửa số liệu. Dữ liệu còn bẩn như ngoài đời (vị trí thủy điện ghi tỉnh cũ trước sáp nhập, năm dạng "tháng/năm", ô "?").

## Câu hỏi (`cases_real_v3.json`, 52 câu)

`make_cases_v3.py` sinh câu **từ dữ liệu, không chọn tay câu nào**: khuôn câu và tỷ lệ loại câu viết trước; dòng, cột, giá trị lọc, ngưỡng rút ngẫu nhiên (SEED 20261024); đáp án do code tính từ chính tệp sẽ nạp. Mỗi lĩnh vực 13 câu:

| Loại | Số câu | Ví dụ |
|---|---|---|
| L tra cứu | 3 × 4 | "Dân số của Sơn La là bao nhiêu người?" |
| U tra cứu gõ không dấu | 1 × 4 | "ca mau thuoc vung nao" |
| C đếm (lọc bằng / chứa, hoặc ngưỡng số) | 2 × 4 | "Có bao nhiêu thủy điện có công suất trên 28 MW?" |
| S liệt kê (2–8 dòng) | 2 × 4 | "Liệt kê các vườn quốc gia ở Lào Cai." |
| M lớn nhất / nhỏ nhất (toàn bảng, trong nhóm) | 2 × 4 | "Trong các tỉnh thành thuộc vùng Đồng bằng sông Hồng, tỉnh thành nào có số phường lớn nhất?" |
| A tổng | 1 × 4 | "Tổng diện tích của các vườn quốc gia thuộc vùng Bắc Trung Bộ là bao nhiêu?" |
| R hỏi thứ bảng không có (phải nói không có) | 1 × 4 | "Số điện thoại của vườn quốc gia Sông Thanh là gì?" |
| F hỏi tiếp 2 lượt | 1 × 4 | "Vườn quốc gia Cúc Phương được thành lập năm nào?" → "Còn diện tích thì sao?" |

Chấm bằng luật của `system4/eval/bench.py` (`any` / `all` / `num` / `refusal` / `source`), không nhờ AI chấm. Số viết nhiều cách đều được chấp nhận (573.119 / 573,119 / 573119).

## Kế hoạch đo (ghi TRƯỚC khi sửa engine)

Cùng model và nhiệt độ như các số đo trước (`inst02`: qwen3:4b-instruct, 0,2), canh nhiệt `eval/thermal.py`, chạy mỗi cấu hình **một lần**:

| Cấu hình | Cài đặt | Ý nghĩa |
|---|---|---|
| `rag` | `FASTPATH_ENABLED=false`, `TABLE_TOOL=false` | RAG thường: tìm kiếm + model 4B |
| `old` | `FASTPATH_ENABLED=false` | Đường cũ hiện tại: RAG + công cụ bảng |
| `fp` | mặc định (đường nhanh bật, đếm / liệt kê tắt) | Sản phẩm hiện tại |
| `fp_agg` | `FASTPATH_AGGREGATE=true` | Đường nhanh hiện tại có bật đếm / liệt kê (đo 18/10: 1/6 trên dữ liệu lạ) |
| sau khi sửa | (ghi khi đóng băng code) | Engine mới; kèm cấu hình bỏ bước biên dịch (text-to-SQL thẳng trên bảng thô) nếu làm được |

Bốn cấu hình "trước" chạy ngay sau khi khoá, trên runtime riêng `bench_runtime_v3_before`, kết quả niêm phong (không mở tới báo cáo cuối). Báo cáo: tỷ lệ đạt (Wilson 95%) chung và theo loại câu, theo lĩnh vực; thời gian trung vị; số câu đường nhanh trả lời.

```bash
BENCH_RUNTIME=system4/eval/bench_runtime_v3_before python system4/eval/bench.py run inst02+rag --set FASTPATH_ENABLED=false --set TABLE_TOOL=false --split blind --suites real3 --no-behavior
```

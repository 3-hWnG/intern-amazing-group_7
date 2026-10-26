# Nguồn dữ liệu — Bộ mù real_v4_s4 (System 4)

Quy định bắt buộc (JD mục 3, J1 & CLAUDE.md):
- Chỉ dùng nguồn có giấy phép rõ ràng: Wikipedia tiếng Việt (CC BY-SA 4.0, ghi revid cố định) hoặc Cổng dữ liệu mở quốc gia có giấy phép.
- Tuyệt đối không dùng dữ liệu ABI / nội bộ công ty. Không chứa thông tin cá nhân (SĐT, CCCD, tên thật).
- Script xây dựng dữ liệu: `system4/eval/real_v4_s4/build_v4.py`.

| STT | Lĩnh vực | Tệp (`data/`) | Nội dung | Cấu trúc Sheet | Nguồn gốc & Tiêu đề bài viết | Giấy phép | Revid cố định |
|---|---|---|---|---|---|---|---|
| 1 | Văn hóa / Dân tộc | `van_hoa_dan_toc.xlsx` | 54 dân tộc Việt Nam: dân số, tỷ lệ, hệ ngôn ngữ, nhóm, địa bàn cư trú | 2 sheet: `Dân tộc và Ngôn ngữ` (59 dòng) & `Địa bàn cư trú` (59 dòng) | Wikipedia tiếng Việt, [Các dân tộc tại Việt Nam](https://vi.wikipedia.org/wiki/C%C3%A1c_d%C3%A2n_t%E1%BB%99c_t%E1%BA%A1i_Vi%E1%BB%87t_Nam) | CC BY-SA 4.0 | 75432455 |
| 2 | Thể thao | `the_thao_san_van_dong.xlsx` | 53 sân vận động: địa điểm, năm khánh thành, sức chứa, đội bóng chủ quản, trạng thái | 2 sheet: `Sân vận động` (53 dòng) & `Đội bóng và Trạng thái` (53 dòng) | Wikipedia tiếng Việt, [Danh sách sân vận động tại Việt Nam](https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_s%C3%A2n_v%E1%BA%ADn_%C4%91%E1%BB%99ng_t%E1%BA%A1i_Vi%E1%BB%87t_Nam) | CC BY-SA 4.0 | 75645255 |
| 3 | Văn hóa / Phi vật thể | `van_hoa_phi_vat_the.xlsx` | 532 di sản văn hóa phi vật thể: loại hình, địa phương, năm công nhận | 1 sheet: `Di sản phi vật thể` (532 dòng) | Wikipedia tiếng Việt, [Danh sách Di sản văn hóa phi vật thể quốc gia (Việt Nam)](https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_Di_s%E1%BA%A3n_v%C4%83n_h%C3%B3a_phi_v%E1%BA%ADt_th%E1%BB%83_qu%E1%BB%91c_gia_(Vi%E1%BB%87t_Nam)) | CC BY-SA 4.0 | 75593715 |
| 4 | Lịch sử / Khảo cổ | `lich_su_bao_vat_quoc_gia.xlsx` | 329 bảo vật quốc gia qua 12 đợt: niên đại, chủ sở hữu, địa phương | 1 sheet: `Bảo vật quốc gia` (329 dòng) | Wikipedia tiếng Việt, [Bảo vật quốc gia (Việt Nam)](https://vi.wikipedia.org/wiki/B%E1%BA%A3o_v%E1%BA%ADt_qu%E1%BB%91c_gia_(Vi%E1%BB%87t_Nam)) | CC BY-SA 4.0 | 75588583 |
| 5 | Tài chính / Ngân hàng | `ngan_hang.xlsx` | 30 ngân hàng thương mại Việt Nam: vốn điều lệ, viết tắt, trụ sở, ngày cập nhật | 1 sheet: `Ngân hàng` (30 dòng) | Wikipedia tiếng Việt, [Danh sách ngân hàng tại Việt Nam](https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_ng%C3%A2n_h%C3%A0ng_t%E1%BA%A1i_Vi%E1%BB%87t_Nam) | CC BY-SA 4.0 | 75662498 |
| 6 | Giáo dục | `giao_duc_truong_dai_hoc.xlsx` | 503 trường đại học, học viện, cơ sở giáo dục đại học toàn quốc | 1 sheet: `Trường đại học` (503 dòng) | Wikipedia tiếng Việt, [Danh sách trường đại học, học viện và cao đẳng tại Việt Nam](https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_tr%C6%B0%E1%BB%9Dng_%C4%91%E1%BA%A1i_h%E1%BB%8Dc,_h%E1%BB%8Dc_vi%E1%BB%87n_v%C3%A0_cao_%C4%91%E1%BA%B3ng_t%E1%BA%A1i_Vi%E1%BB%87t_Nam) | CC BY-SA 4.0 | 75654510 |
| 7 | Giao thông | `xe_buyt_tphcm.xlsx` | 107 tuyến xe buýt nội thành TP.HCM: điểm đầu/cuối, cự ly, thời gian hoạt động, giãn cách | 1 sheet: `Tuyến xe buýt nội thành` (107 dòng) | Wikipedia tiếng Việt, [Danh sách tuyến xe buýt Thành phố Hồ Chí Minh](https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_tuy%E1%BA%BFn_xe_bu%C3%BDt_Th%C3%A0nh_ph%E1%BB%91_H%E1%BB%93_Ch%C3%AD_Minh) | CC BY-SA 4.0 | 75668041 |
| 8 | Di tích / Kiến trúc | `di_tich_quoc_gia_dac_biet.xlsx` | 150 di tích quốc gia đặc biệt: đợt/năm xếp hạng, địa phương, hạng mục | 1 sheet: `Di tích đặc biệt` (150 dòng) | Wikipedia tiếng Việt, [Di tích quốc gia đặc biệt (Việt Nam)](https://vi.wikipedia.org/wiki/Di_t%C3%ADch_qu%E1%BB%91c_gia_%C4%91%E1%BA%B7c_bi%E1%BB%87t_(Vi%E1%BB%87t_Nam)) | CC BY-SA 4.0 | 75571348 |

### Biến đổi và cấy bẩn chủ động (theo mục 2.1):
- Trải `rowspan` / `colspan`, bỏ chú thích `[1]`, bỏ cột ảnh / toạ độ.
- $\ge 2$ tệp có 2 sheet về cùng đối tượng: `van_hoa_dan_toc.xlsx` (key `Dân tộc`) và `the_thao_san_van_dong.xlsx` (key `Sân vận động`).
- Ô gộp và năm dạng `"tháng/năm"` (ví dụ: sân VinFast Trống Đồng khánh thành `"2027/2028"`).
- Ô ghi `"?"` cho dữ liệu thiếu (năm thành lập, số giường, viết tắt).
- Số kèm đơn vị (ví dụ: `"40.192 chỗ"`, `"30.000 chỗ"` trong `the_thao_san_van_dong.xlsx`).
- Cặp tên gần trùng có/không dấu để test S4-2:
  - Cặp `"Trống đồng Sông Lô"` / `"Trống đồng Sông Lò"` trong `lich_su_bao_vat_quoc_gia.xlsx`.
  - Cặp `"Người Mường Lò (nhánh)"` / `"Người Mường La (nhánh)"` trong `van_hoa_dan_toc.xlsx`.

### Thay thế domain yếu (sau khi rà soát J1):
- Thay `y_te_benh_vien_tphcm.xlsx` (85 dòng, chỉ phạm vi TP.HCM) → `ngan_hang.xlsx` (toàn quốc, trường dữ liệu số đa dạng hơn: vốn điều lệ dùng cho câu hỏi A/M/C).
- Thay `du_lich_di_san_the_gioi.xlsx` (chỉ 14 dòng, quá ít để sinh 16 câu Phần A đa dạng) → `xe_buyt_tphcm.xlsx` (107 dòng).
- Cả 2 bảng mới được dựng bằng script tải trực tiếp từ Wikipedia (giữ `revid` cố định ở trên), không dùng dữ liệu nhớ/suy đoán.
- Cột 'Giá vé'/'Loại xe'/'Đơn vị đảm nhiệm' của `xe_buyt_tphcm.xlsx` **không được nạp** vào bảng dữ liệu dùng để test (dù có trên Wikipedia) — chủ đích để các câu R (refusal) về giá vé/loại xe có đáp án đúng là từ chối.

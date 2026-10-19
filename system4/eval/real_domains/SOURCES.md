# Dữ liệu THẬT cho 3 lĩnh vực mềm (19/10/2026)

Mentor nhận xét nhóm dùng quá nhiều dữ liệu tự sinh khi đánh giá và demo. Thư mục này thay bằng dữ liệu thật, nhỏ, có nguồn và giấy phép rõ.
Mỗi lĩnh vực có 1 **bảng** (đi đường nhanh, code trả lời câu tra cứu) và 1 **văn bản** (tìm kiếm + AI, có trích nguồn).

```
python system4/eval/real_domains/fetch.py     # tải nguồn gốc về raw/ (không vào git)
python system4/eval/real_domains/build.py     # raw/ -> data/ (6 tệp + manifest.json: số dòng, revid)
python run_server.py system4/eval/real_domains/seed.py   # TẮT server trước: tạo lĩnh vực, nạp 6 tệp (dùng chung), chờ nạp + biên dịch xong
```

| Lĩnh vực | Tệp (`data/`) | Nội dung | Nguồn | Giấy phép |
|---|---|---|---|---|
| Y tế | `y_te_benh_vien_tphcm.xlsx` | 85 bệnh viện TP.HCM: nhóm, năm thành lập, loại, cơ sở, số giường, tuyến BHYT, cấp chuyên môn, cơ quan chủ quản, website | Wikipedia tiếng Việt, [Danh sách bệnh viện tại Thành phố Hồ Chí Minh](https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_b%E1%BB%87nh_vi%E1%BB%87n_t%E1%BA%A1i_Th%C3%A0nh_ph%E1%BB%91_H%E1%BB%93_Ch%C3%AD_Minh), revid 75626151 | CC BY-SA 4.0 |
| Y tế | `y_te_hoi_dap_bac_si.md` | 300 câu hỏi THẬT của người dân + bác sĩ trả lời (chọn ngẫu nhiên, seed 19, từ 1.200 dòng rải đều trên 9.335) | [hungnm/vietnamese-medical-qa](https://huggingface.co/datasets/hungnm/vietnamese-medical-qa) (gốc: hỏi đáp bác sĩ trên edoctor.io, vinmec.com) | Apache-2.0 (do người đăng bộ dữ liệu khai) |
| Giáo dục | `giao_duc_truong_dai_hoc.xlsx` | 361 trường đại học / học viện / trường thành viên: viết tắt, tên tiếng Anh, địa điểm, thuộc đại học, cơ quan chủ quản, công lập / tư thục / nước ngoài | Wikipedia tiếng Việt, [Danh sách trường đại học, học viện và cao đẳng tại Việt Nam](https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_tr%C6%B0%E1%BB%9Dng_%C4%91%E1%BA%A1i_h%E1%BB%8Dc,_h%E1%BB%8Dc_vi%E1%BB%87n_v%C3%A0_cao_%C4%91%E1%BA%B3ng_t%E1%BA%A1i_Vi%E1%BB%87t_Nam) (bỏ phần cao đẳng, dự bị) | CC BY-SA 4.0 |
| Giáo dục | `giao_duc_luat_giao_duc_2019.txt` | Toàn văn Luật Giáo dục số 43/2019/QH14: 9 chương, 115 điều | Cổng PBGDPL TP. Cần Thơ, [pbgdpl.cantho.gov.vn/attachment/284](https://pbgdpl.cantho.gov.vn/attachment/284) | Văn bản quy phạm pháp luật: không thuộc đối tượng bảo hộ quyền tác giả (Luật SHTT 2005, Điều 15) |
| Du lịch | `du_lich_di_tich_dac_biet.xlsx` | 150 di tích quốc gia đặc biệt: địa điểm, hạng mục, đợt và năm xếp hạng (đợt 1/2009 – đợt 19/2026), ghi chú UNESCO | Wikipedia tiếng Việt, [Di tích quốc gia đặc biệt (Việt Nam)](https://vi.wikipedia.org/wiki/Di_t%C3%ADch_qu%E1%BB%91c_gia_%C4%91%E1%BA%B7c_bi%E1%BB%87t_(Vi%E1%BB%87t_Nam)), revid 75571348 (bỏ mục "đang lập hồ sơ") | CC BY-SA 4.0 |
| Du lịch | `du_lich_diem_den.md` | 6 bài: Phố cổ Hội An, Vịnh Hạ Long, Vườn quốc gia Phong Nha – Kẻ Bàng, Sa Pa, Đà Lạt, Phú Quốc (bỏ các mục Tham khảo / Chú thích / Xem thêm / Liên kết ngoài) | Wikipedia tiếng Việt, revid trong `data/manifest.json` | CC BY-SA 4.0 |

Bộ cũ `system4/eval/data/du_lich_gia.xlsx` (và `cua_hang_gia.xlsx`) là dữ liệu **tự sinh** (`make_tourism.py`, `make_shop.py`), giữ lại để tái lập
số đo đường nhanh đã ghi; leader quyết định 19/10 vẫn để nó trong lĩnh vực Du lịch trên web, cạnh 2 bộ thật.

## Biến đổi (build.py) — chỉ đổi định dạng và làm sạch, không thêm / sửa số liệu
- Bảng Wikipedia: trải `rowspan` / `colspan`, bỏ chú thích `[1]`, toạ độ, ảnh; gắn nhóm theo tiêu đề mục (vd. bệnh viện "Tư nhân", di tích "Đợt 7 (2016)").
  Cột Website chỉ giữ tên miền (ô chỉ có link lưu trữ bị để trống).
- Hỏi đáp: bỏ lời chào ("Chào bác sĩ,"), câu mở đầu khuôn mẫu, câu quảng cáo / hotline / đặt lịch; **che** số điện thoại, email, tên người hỏi
  (`[SĐT]`, `[EMAIL]`, `[TÊN]`). Tiêu đề mỗi cặp = câu hỏi chính (câu có dấu "?"). Giữ số thứ tự dòng gốc để đối chiếu.
- Luật: lấy khối toàn văn của trang, mỗi đoạn một dòng (để bộ chia văn bản tự nhận Chương / Điều — `READER_VERSION` 5).

## Giới hạn
- Wikipedia có thể chưa đầy đủ / chưa cập nhật (vd. 23/85 bệnh viện không ghi năm thành lập, 40 không ghi số giường).
- Luật Giáo dục 2019 đã được sửa đổi một số điều sau 2019; bản ở đây là bản gốc 2019.
- Câu trả lời của bác sĩ là tư vấn chung qua mạng, không phải chẩn đoán.
- CC BY-SA: dùng lại / phân phối lại cần ghi nguồn và giữ cùng giấy phép (bảng trên là phần ghi nguồn).

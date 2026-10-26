# Khoá bộ câu mù thứ tư real_v4_s4 (26/10/2026)

Khoá trước mọi thay đổi engine ở J2 (Bước 3). Không sửa câu, đáp án hay dữ liệu theo kết quả; cần chỉnh thì làm bộ mới (`real_v5`).

- **Phân định vai trò:**
  - Người viết câu hỏi Phần B (chỉ xem tên cột, không xem dữ liệu): Phạm Lê Thiên Dấn.
  - Nhãn B (gán nhãn độc lập, mở dữ liệu thật): Phạm Lê Thiên Dấn.
  - Nhãn A (gán nhãn độc lập thứ 2, mở dữ liệu thật, không xem Nhãn B trước khi làm): Nguyễn Viết Hưng.
  - Người sửa engine System 4 (J2): [điền tên] — **tuyệt đối không đọc câu hỏi và đáp án Phần B trước khi sửa xong J2**.

---

## 1. Bảng mã băm SHA256 các tệp đã khoá

| File | sha256 |
|---|---|
| `system4/eval/real_v4_s4/data/di_tich_quoc_gia_dac_biet.xlsx` | `d4520a1404b8932a4ac34495bcca48e71bce89c8822bde126919954aca81c92b` |
| `system4/eval/real_v4_s4/data/giao_duc_truong_dai_hoc.xlsx` | `05095b752c027ff35818e7b8523c72f2f2d060ef3be2418577520c57f46a6cc2` |
| `system4/eval/real_v4_s4/data/lich_su_bao_vat_quoc_gia.xlsx` | `8ae4ea96c7752f1987e0cf9d9de8411b6b20e7a95d97aa9d061f99e710c97fba` |
| `system4/eval/real_v4_s4/data/manifest.json` | `70fe91c4742d8f55f265a00801d7216f289d18845b325cf29eb65689dbf7ab21` |
| `system4/eval/real_v4_s4/data/ngan_hang.xlsx` | `ae0373d8eb3621d9441e6a7bc4eac2617d8a90b90564e1d47b141c900687f237` |
| `system4/eval/real_v4_s4/data/the_thao_san_van_dong.xlsx` | `ca8e71fee4d022c8abda8feccb51c8ffa734ce9171f76f8eb24455f9f5bd66df` |
| `system4/eval/real_v4_s4/data/van_hoa_dan_toc.xlsx` | `8933d01b9e2e424d4ae6622e9556efd54218b8b5bbc0aa9faf5b480e188264f9` |
| `system4/eval/real_v4_s4/data/van_hoa_phi_vat_the.xlsx` | `272cd8b812d5fe2aa069368a0ee8122d2c75567639862bb75faa13c0ec238660` |
| `system4/eval/real_v4_s4/data/xe_buyt_tphcm.xlsx` | `4e6a683a36cecc554dec5587137d0af2d89ce8442550fc520f3f610053086742` |
| `system4/eval/real_v4_s4/build_v4.py` | `dcf81fd593ef4d36547d75d475a82b7af36d71a7a283e6c2b8955eff1619a721` |
| `system4/eval/real_v4_s4/make_cases_v4.py` | `929d30e92968c707955607494c272cb95f0416e90952ebdfb703e3956403909b` |
| `system4/eval/real_v4_s4/run_real_v4_s4.py` | `528eb87344770c70b08da22b3d07c215dfc2afdaac2c6fcd52e10f8e2f2717dc` |
| `system4/eval/real_v4_s4/cases_real_v4_s4.json` | `6a2d3a5977deaa4fb520461ff6471d4f65ddd0dab94cbbe6b2ad5a67265a42f0` |
| `system4/eval/real_v4_s4/cases_real_v4_s4_B.json` | `2609bc04ed7341650cf40b229daa5df496b967dd57be081b92a6423556995176` |
| `system4/eval/real_v4_s4/real_v4_s4_labels_A.json` | `89257e2be17115a0544bc163c5800b315119cef8b67dcacfb366a945d3efa86c` |
| `system4/eval/real_v4_s4/real_v4_s4_labels_B.json` | `4ebd0a0777851fbc9e61542f82962da2ba1cced9712834230ad0afc214ed5b04` |
| `system4/eval/real_v4_s4/real_v4_s4_labels_final.json` | `090dbec3875985583b420de5d0ab7893e9cee68a33ab770dea37c04300a303d2` |
| `system4/eval/real_v4_s4/cases_real_v4_s4_labeled.json` | `3782839448acd412e3f9ab340c3b2c08467b6c3d3d2d0722195247aa6edbbcc6` |

*Ghi chú: tệp .xlsx có dấu thời gian bên trong, nên chạy lại build_v4.py cho nội dung giống hệt nhưng mã băm có thể khác; bộ đo dùng đúng các tệp đã commit ở đây.*

---

## 2. Đo độ đồng thuận Phần B (2 người gán độc lập)

- Tổng số câu Phần B: 88 câu
- Tỷ lệ đồng thuận ngữ nghĩa (Semantic Agreement): **95.5%**
- Khớp từ chối (`refusal`): **98.9%** (Cohen's kappa $\kappa = 0.967$)
- Khớp hỏi lại (`ask_back`): **98.9%** (Cohen's kappa $\kappa = 0.935$)
- Cohen's kappa hành vi tổng thể (`answer` / `refusal` / `ask_back`): $\mathbf{\kappa = 0.952}$
- Số câu có khác biệt chi tiết: 24/88 — trong đó 2 câu bất đồng nội dung thật (đã họp chốt), 22 câu còn lại chỉ khác định dạng/biên rộng (gộp union). Chi tiết lý do trong [ASSUMPTIONS_B.md](file:///D:/phase%203/v3/system4/eval/real_v4_s4/ASSUMPTIONS_B.md).
- Tổng số câu bộ mù hoàn chỉnh: **216 câu** (Phần A: 128 câu khuôn; Phần B: 88 câu người viết).

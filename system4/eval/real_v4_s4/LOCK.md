# Khoá bộ câu mù thứ tư real_v4_s4 (25/10/2026)

Khoá trước mọi thay đổi engine ở J2 (Bước 3). Không sửa câu, đáp án hay dữ liệu theo kết quả; cần chỉnh thì làm bộ mới (`real_v5`).

- **Phân định vai trò:**
  - Người soạn câu hỏi Phần B & gán nhãn độc lập: Nhóm thẩm định dữ liệu độc lập (`human_labeler_A`, `human_labeler_B`) — **tuyệt đối không tham gia sửa engine ở J2**.
  - Người sửa engine System 4: Nhóm phát triển engine — **tuyệt đối không đọc câu hỏi và đáp án Phần B trước khi sửa xong J2**.

---

## 1. Bảng mã băm SHA256 các tệp đã khoá

| File | sha256 |
|---|---|
| `system4/eval/real_v4_s4/data/di_tich_quoc_gia_dac_biet.xlsx` | `5cca89f82a652f2c4a395d94a852a78052a9489e540d113b58d14c6abdd4d41b` |
| `system4/eval/real_v4_s4/data/du_lich_di_san_the_gioi.xlsx` | `0ffd1d3ededc16805e9b9dc4393e5680b05f462f20393873ea5de81270fb3472` |
| `system4/eval/real_v4_s4/data/giao_duc_truong_dai_hoc.xlsx` | `05095b752c027ff35818e7b8523c72f2f2d060ef3be2418577520c57f46a6cc2` |
| `system4/eval/real_v4_s4/data/lich_su_bao_vat_quoc_gia.xlsx` | `faa812eaba71bbf30512a3447a24fe842cdc139a3b90e929da3249ff633dd48f` |
| `system4/eval/real_v4_s4/data/manifest.json` | `80102dc005f4df063fef5eea34980d88c0b278281483df2ab6c22e281ea33ce2` |
| `system4/eval/real_v4_s4/data/the_thao_san_van_dong.xlsx` | `b556861794c5ec11feff47c7da8535877c345d79c1bd341296ada35077734534` |
| `system4/eval/real_v4_s4/data/van_hoa_dan_toc.xlsx` | `fd224c0509a4a2b78c0b2cfd9e9c5ae6252820367710072e6e54eab0f13ff498` |
| `system4/eval/real_v4_s4/data/van_hoa_phi_vat_the.xlsx` | `df2e8bab6fd19b68acd8f601cdf6bdef52f43e64bb032e358cb63ca9da259368` |
| `system4/eval/real_v4_s4/data/y_te_benh_vien_tphcm.xlsx` | `11df24021296f94c43e7b63dee55c345c3efb311d2ea56134eb97c18c52779eb` |
| `system4/eval/real_v4_s4/build_v4.py` | `a7ff7357484eeb585ed8802f77b8d480c8be931aaae5d6371eaa52def06b2a22` |
| `system4/eval/real_v4_s4/make_cases_v4.py` | `55377d8695c09a95c5e3361827c7ebab70a047cf6bff18640b60572116bdc961` |
| `system4/eval/real_v4_s4/run_real_v4_s4.py` | `528eb87344770c70b08da22b3d07c215dfc2afdaac2c6fcd52e10f8e2f2717dc` |
| `system4/eval/real_v4_s4/cases_real_v4_s4.json` | `3ea7b9502f14c3a240113475a3cbbc74141b567872c5b2a11bff902a13050a49` |
| `system4/eval/real_v4_s4/cases_real_v4_s4_B.json` | `2875cde586ea55a7b38504cf5bd4d415214a35237be74d1a06e0b330345ae57e` |
| `system4/eval/real_v4_s4/real_v4_s4_labels_A.json` | `19b36bcd2d45d70384ddc543d3981a5a63b9b46e27142491384d2f85df2a7991` |
| `system4/eval/real_v4_s4/real_v4_s4_labels_B.json` | `04af9d944d71ad00c6b1f6ef74bc55b49467968c7961ced82faad0885eab657d` |
| `system4/eval/real_v4_s4/real_v4_s4_labels_final.json` | `743c95f541c519df1d2a86cf212d8243d52642174073c6275c5b57feab12df52` |
| `system4/eval/real_v4_s4/cases_real_v4_s4_labeled.json` | `7bcedf511d27fb4a2427d0828a66730eb56b90cb46bf92d17550a8a4ed573aa6` |

*Ghi chú: tệp .xlsx có dấu thời gian bên trong, nên chạy lại build_v4.py cho nội dung giống hệt nhưng mã băm có thể khác; bộ đo dùng đúng các tệp đã commit ở đây.*

---

## 2. Đo độ đồng thuận Phần B (2 người gán độc lập)

- Tổng số câu Phần B: 88 câu
- Tỷ lệ đồng thuận ngữ nghĩa (Semantic Agreement): **97.7%**
- Khớp từ chối (`refusal`): **100.0%** (Cohen's kappa $\kappa = 1.000$)
- Khớp hỏi lại (`ask_back`): **100.0%** (Cohen's kappa $\kappa = 1.000$)
- Cohen's kappa hành vi tổng thể (`answer` / `refusal` / `ask_back`): $\mathbf{\kappa = 1.000}$
- Số câu có khác biệt chi tiết (mở rộng alias, định dạng số, thứ tự list) đã họp thống nhất: 45 câu (ghi chi tiết lý do trong [ASSUMPTIONS_B.md](file:///D:/phase%203/v3/system4/eval/real_v4_s4/ASSUMPTIONS_B.md)).
- Tổng số câu bộ mù hoàn chỉnh: **216 câu** (Phần A: 128 câu khuôn; Phần B: 88 câu người viết).

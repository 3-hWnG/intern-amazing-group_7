# Khoá bộ câu mù thứ tư real_v4_s4 (26/10/2026)

Khoá trước mọi thay đổi engine ở J2 (Bước 3). Không sửa câu, đáp án hay dữ liệu theo kết quả; cần chỉnh thì làm bộ mới (`real_v5`).

- **Phân định vai trò:**
  - Người viết câu hỏi Phần B (chỉ xem tên cột, không xem dữ liệu): Phạm Lê Thiên Dấn.
  - Nhãn B (gán nhãn độc lập, mở dữ liệu thật): Phạm Lê Thiên Dấn.
  - Nhãn A (gán nhãn độc lập thứ 2, mở dữ liệu thật, không xem Nhãn B trước khi làm): Nguyễn Viết Hưng.
  - Người sửa engine System 4 (J2): **Trịnh Hoàng Nhân** (xác nhận 27/10/2026: chưa đọc câu hỏi/đáp án Phần B trước khi viết code) — **tuyệt đối không đọc câu hỏi và đáp án Phần B trước khi sửa xong J2**.

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
| `system4/eval/real_v4_s4/cases_real_v4_s4_labeled.json` | `3782839448acd412e3f9ab340c3b2c08467b6c3d3d2d0722195247aa6edbbcc6` (xem ghi chú 27/10 dưới) |

*Ghi chú 27/10/2026:* sau khi khoá, `cases_real_v4_s4_labeled.json` được chạy qua một bước "làm phẳng" để `bench.py` nạp được
(thêm field `suite`/`split`/`datasets`/`kind` cần cho máy chạy, bỏ field `notes`/`labeler` chỉ là ghi chú nội bộ) — hash file đổi thành
`af13cece5ab7ed162caf3f5c4014d48029619efa302d19e3e9b4fcf31243c28c`. Đã so sánh từng câu (`turns`, `check`) giữa bản khoá gốc và bản
đã làm phẳng: **giống 100% cho toàn bộ 216 câu, không câu nào đổi nội dung hỏi/đáp án** (so bằng script, không phải đọc mắt). Bản làm
phẳng là bản `bench.py`/`real4_cases()` thực sự dùng để chạy J3; hash cũ ở trên là của bản khoá gốc (có `notes`/`labeler`), giữ nguyên để
đối chiếu lịch sử, không phải hash của tệp sẽ chạy.

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

---

## 3. Chốt tên 6 cấu hình J3 (27/10/2026, TRƯỚC khi chạy — không đổi sau khi thấy số)

Mirror đúng khuôn 6 cấu hình đã dùng ở `real_v3` (bài báo 1), thêm cặp trước/sau cho S4-1..4 (vì `config.py` giờ mặc định 4 cờ S4 = True, phải set tay `false` cho cấu hình "trước sửa"):

| Tên | Cờ (`--set`) | Vai trò |
|---|---|---|
| `v4a_before` | `FASTPATH_SQL=true FASTPATH_WIDE_TABLE=false FASTPATH_ACCENT_FIRST=false FASTPATH_ATTR_GUARD=false FASTPATH_CLEAN_SHOW=false` | Trước sửa (= kiến trúc `real_v3`, S4-1..4 tắt) |
| `v4a_after` | `FASTPATH_SQL=true FASTPATH_WIDE_TABLE=true FASTPATH_ACCENT_FIRST=true FASTPATH_ATTR_GUARD=true FASTPATH_CLEAN_SHOW=true` | Sau sửa — **cặp chính so McNemar với `v4a_before`** |
| `v4a_sqlraw` | `FASTPATH_SQL=false FASTPATH_SQL_RAW=true` | giống `v3a_sqlraw` |
| `v4b_fp` | `FASTPATH_SQL=false` | giống `v3b_fp` |
| `v4b_old` | `FASTPATH_SQL=false FASTPATH_ENABLED=false` | giống `v3b_old` |
| `v4b_rag` | `FASTPATH_SQL=false FASTPATH_ENABLED=false TABLE_TOOL=false` | giống `v3b_rag`, RAG thuần |

Xác nhận bằng dj (27/10/2026, chat). Chạy đúng 1 lần mỗi cấu hình trên `real_v4_s4` (suite `real4`, split `blind`), qua `bench.py`.


## 4. J3 — ghi chú minh bạch về lần chạy đầu của `v4a_before` (27/10/2026)

Lần chạy `inst02+v4a_before` ĐẦU TIÊN (27/10, ~05:30) không phải một lần đo hợp lệ: `bench.py`'s `ensure_datasets()` thiếu hẳn việc nạp 8 bảng `real_v4_s4` (chỉ có `REAL3_FILES` của bộ cũ), nên suite `real4` chạy với **0 bảng dữ liệu nào active** — mọi câu trả lời đều mù (nguồn sai, có: []), không phản ánh engine/fastpath gì cả. Đây là lỗi hạ tầng đo (`bench.py`), phát hiện ngay khi đọc log, trước khi bất kỳ số nào được dùng để quyết định gì. Đã vá 2 lỗi trong `bench.py` (không đụng tới `system4/server/fastpath/` hay bất kỳ code engine nào):
1. Thêm `REAL_V4_S4_FILES` vào `ensure_datasets()` — thiếu hẳn, không phải thay cái đã có.
2. `score()`: `check["num"]` một số câu Phần B là int trần (ví dụ 195) thay vì list ([195]) — coerce về list trước khi so khớp, tránh crash `TypeError`.
3. Thêm retry (8 lần, cách 5s) cho các GET polling trong `ensure_datasets()` — loopback 127.0.0.1:8399 bị rớt kết nối thoáng qua ngẫu nhiên (WinError 10053/10054, RemoteProtocolError) trong lúc server bận xử lý; server không crash, không đổi PID, chỉ là lỗi mạng cục bộ tạm thời.

Lần chạy `v4a_before` được tính vào kết quả J3 chính thức là lần chạy **sau** khi vá 3 điểm trên (27/10, ~13:00, hoàn thành ~13:57) — vẫn đúng 1 lần, không chạy lại sau khi đã thấy số hợp lệ. 5 cấu hình còn lại (`v4a_after`, `v4a_sqlraw`, `v4b_fp`, `v4b_old`, `v4b_rag`) đều chạy sạch 1 lần, không retry lần 2.

File kết quả thô: `system4/eval/results/bench/inst02+<tên>.json` (216 runs mỗi file). Script tổng hợp: `system4/eval/real_v4_s4/report_v4.py` (script có sẵn từ trước, Wilson 95% CI + McNemar CHÍNH XÁC bằng tổ hợp, theo domain, theo loại câu, theo Phần A/B — chạy `python system4/eval/real_v4_s4/report_v4.py v4a_before v4a_after v4a_sqlraw v4b_fp v4b_old v4b_rag --pair v4a_before v4a_after` từ gốc repo để tái tạo) — kết quả xem ở `docs/BAO_CAO_BAI_BAO_2_SYSTEM4_2026-10-26.md` mục 3 và `docs/paper2_draft_en.md` mục 6.


## 7. Cấu hình thứ 7: `v4a_noselftest` — lần chạy đầu bị cache cũ, lần 2 mới hợp lệ (27/10/2026)

JD yêu cầu cấu hình thứ 6 của J3 là "bỏ bài tự kiểm: bật SQL cho mọi bảng" (câu hỏi: tự kiểm có chặn đúng bảng nguy hiểm không). 6 cấu hình gốc không có cấu hình này — bổ sung thêm `v4a_noselftest` (giống `v4a_after`, chỉ thêm `FASTPATH_MIN_PASS=0`).

**Lần chạy đầu (không tính):** không xoá `bench_runtime` trước khi chạy → server dùng lại bảng đã biên dịch từ lần chạy `v4b_rag` ngay trước đó (FASTPATH gần như tắt), không biên dịch lại theo cài đặt mới. Phát hiện qua: (1) log "đường nhanh: tự kiểm bật X/Y" khớp y hệt nhóm FASTPATH_SQL=false, không khớp `v4a_after`; (2) kiểm trực tiếp file kết quả: 0/216 câu có `fast_path.route == "sql"`. Số 54,6% của lần này KHÔNG được dùng.

**Lần chạy 2 (tính vào kết quả):** xoá `bench_runtime` trước, chạy lại đúng lệnh — xác nhận hợp lệ: log tự kiểm khớp đúng `v4a_after` (bật 4/4, 5/6, 4/6, 1/3, 2/3, 2/3, 2/3, 3/3, 2/3), file kết quả có 89/216 câu route "sql" (khớp số của `v4a_after`). Kết quả: **112/216 = 51,9%**, McNemar vs `v4a_after`: +2/−3, p=1 (không khác biệt). Đây là số được dùng trong mục 3/6 báo cáo.

## 8. Đo thời gian nạp mỗi bảng — `system4/eval/table_load_time.py` (27/10/2026)

Chạy trên runtime riêng (`bench_runtime_loadtime_probe`), không đụng dữ liệu J3. Kết quả (giây, 8 bảng mới):
`dan_toc` 50,0 · `san_van_dong` 19,2 · `phi_vat_the` 37,2 · `bao_vat` 29,3 · `dai_hoc` 38,6 · `di_tich_dac_biet` 22,4 · `ngan_hang` 12,2 · `xe_buyt_tphcm` 15,8. Trung vị: **29,3s**.

## 6. Ghi chú nhỏ: `summary.accuracy` là `null` trong `inst02+v4a_before.json` (27/10/2026)

Riêng file `inst02+v4a_before.json` có field `summary.accuracy: null`, khác với 5 file còn lại (tính đúng %). `runs` trong file này vẫn đủ 216 bản ghi hợp lệ, tính tay ra đúng 115/216 = 53,2% (khớp với số báo cáo ở mục 3). Chưa xác định được chắc nguyên nhân (không tái hiện được trạng thái lúc `summarize()` chạy ở lần đo gốc, 27/10 ~13:57); không có hậu quả vì toàn bộ số liệu báo cáo ở mục 3/5 tính thẳng từ `runs` qua `report_v4.py`, không đọc field `summary` của `bench.py`. Ghi lại ở đây để minh bạch, không giấu — không coi đây là lý do nghi ngờ tính hợp lệ của 216 câu trong file.

## 5. J3 — thiếu dữ liệu hành vi ("22 tình huống") ở cả 6 lần chạy, nguyên nhân thật (27/10/2026)

Cả 6 file kết quả J3 có `behavior: None`. Chẩn đoán ban đầu (rớt kết nối loopback thoáng qua, giống lỗi đã vá ở
`ensure_datasets()`) **SAI**: đã thêm retry cho `nv2_behavior.py` dựa trên chẩn đoán đó, nhưng khi chạy thử lại
(27/10, ~20:00) lỗi thật lộ ra ngay (nhờ đã vá `bench.py` không còn nuốt im lặng lỗi của subprocess này):

```
ModuleNotFoundError: No module named 'system3'
```

Nguyên nhân thật: `nv2_behavior.py` tự tính đường dẫn `pyroot` bằng path tương đối cố định
(`Path(__file__).resolve().parents[2].parent / "pyroot"`), KHÔNG dùng biến `BENCH_PYROOT`/`bench.PYROOT` như
mọi nơi khác trong `bench.py`. Trên máy dj, `pyroot` thật không nằm đúng chỗ path tương đối đó trỏ tới (xem
`_pyroot()` trong `bench.py`, comment 18/10: "pyroot trên máy dev trỏ sang repo system3 khác") — nên import
luôn thất bại, ngay dòng đầu file, trước khi gọi mạng gì cả. Lỗi này chắc chắn đã xảy ra y hệt ở cả 6 lần J3
chính thức (27/10), không phải lần nào may rủi — và bị nuốt im lặng vì `bench.py` gọi subprocess với
`capture_output=True` mà không in ra khi thất bại (đã vá riêng, xem mục 4 cách vá `bench.py`).

**Đã vá:** truyền `PYTHONPATH=str(PYROOT)` vào env lúc gọi `nv2_behavior.py` (cả trong `bench.py` và trong
`system4/eval/behavior_only.py`, script chạy riêng phần hành vi không đụng 216 câu đã có). Retry đã thêm trước
đó cho rớt kết nối vẫn giữ (vô hại, không phải nguyên nhân chính nhưng không sai khi có thật).

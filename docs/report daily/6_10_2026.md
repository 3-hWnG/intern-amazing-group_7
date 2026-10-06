# Báo cáo công việc ngày 06/10/2026 — System 3

## 1. Tóm tắt
Hôm nay hoàn thành toàn bộ đợt 4 (Phase 14–22) theo kế hoạch `PLAN_SYSTEM3_DOT4.md`, sau khi nhóm gửi phản hồi và yêu cầu chuyển sang hướng hybrid theo kiến trúc G7.
- **Cải thiện thật:** câu trả lời đúng ý người hỏi (concise): DEV focus 70% → 99%, task thừa 11/230 → 0; bộ test chung của nhóm (10 câu, chấm luật) 3/10 → 7/10.
- **Chưa đạt mục tiêu:** chọn đúng thủ tục khi người dân gõ tự do vẫn quanh 75% top-1 (mục tiêu 80%); hỏi lại khi mơ hồ chỉ đúng một nửa.
- **Kết luận đã kiểm chứng:** Planner hybrid dùng Qwen3-4B không có lợi, mặc định vẫn là luật.

## 2. Phản hồi của nhóm và quyết định đổi hướng
Đọc `System-3-Feedback-lan-1/2.pdf`, `He-thong-3_Semantic-Planner_Slide-4.docx` (kiến trúc G7) và `Test_Case_Legal_AI_Assistant_Bang_Test.docx` (bộ test 10 câu của các team).
Điểm nhóm nêu: câu trả lời chưa concise (dư thủ tục, dư bước), multi-intent bắt lung tung, teencode làm hệ thống break, nút "chủ đề mới" không chạy, cấu hình không có chỉ báo AI bật hay tắt, cần nút "Tạo bảng full" từ System 2. Điểm tốt: multi-intent bắt được, không bị lừa sang chủ đề khác.
Quyết định (bạn đồng ý): huỷ quyết định "bỏ LLM khỏi Planner" của hôm trước, chuyển sang **hybrid** — luật cho kế hoạch mặc định, Qwen3-4B chạy nền với timeout 7 giây, chỉ được sửa kế hoạch khi confidence cao và Policy chấp nhận. Định nghĩa concise do nhóm đưa ra: **hỏi gì trả lời đúng ý đó** (hỏi giá thì chỉ báo giá).

## 3. Công việc theo phase
| Phase | Việc | Kết quả |
|---|---|---|
| 14 | Dọn nợ kỹ thuật | Sửa `smoke_test`; "cuối"/"cưới"; "không phải" trong tên thủ tục; "cơ quan" bị cắt như tiểu từ; lỗi reset hồi sinh chủ đề cũ. Chưa cài được trên venv sạch (pip lỗi SSL). |
| 15 | Bộ pseudo_real (agent mới, không thấy mã) | 30 câu đơn + 4 hội thoại. Số gốc: top-1 11/30, hành vi 30/42, hỏi lại 1/6. |
| 16a | Kiểm lại sau lần mất kết quả Phase 16 | Gate xanh. Phát hiện agent Phase 16 đã thêm 85 ca DEV tự soạn (`p16`). |
| 17 | Chỉ số concise (`run_concise.py`) + bộ team (`run_team.py`) | Số gốc: DEV focus 70%, task thừa 11/230, team 3/10. |
| 18 | Sửa nhóm lỗi chung (trả dư mục, task thừa, hỏi lại, điều kiện, gõ đời thường) | DEV focus 99%, HOLDOUT cũ focus 96%, task thừa 0, team 7/10. Gate hồi quy xanh. |
| 19 | Planner hybrid luật + Qwen3-4B | Cơ chế đầy đủ (`/config`, trace, công tắc). **Không đạt gate**: không lần sửa nào của LLM làm đúng hơn; confidence tự báo 0,99 cho 65% câu kể cả khi sai. Mặc định giữ luật. |
| 20 | Chất lượng sống | "Tạo bảng full" (nguyên văn dữ liệu), chỉ báo + panel cấu hình AI, sửa 3 lỗi nút "Bắt đầu chủ đề mới", sửa bố cục điện thoại, `knowledge/` (thiết kế RAG, chưa build). |
| 21 | Bộ mù mới | HOLDOUT-4 (90 mục) và pseudo_real 2 (30 mục). Kết quả bên dưới. |
| 22 | Chốt tài liệu | README viết lại theo số thật, `BAO_CAO_DOT4.md`, cập nhật EVAL/CONTRIBUTING/PLAN; dọn `eval/results/` 58 MB → 2,8 MB (bản lưu zip ngoài project). |

Việc thêm theo yêu cầu: làm gọn UI panel cấu hình; sửa lỗi CSS gốc (thiếu một dấu `}` khiến mọi luật phía sau chỉ có hiệu lực ≤ 760 px, nên màn hình rộng hiện xấu); căn giữa cột chat ở màn hình rộng; tạo `.claude/launch.json` và chạy thử server; tắt vòng chờ nền của agent Phase 19 còn sót.

### Tính năng UI thêm theo yêu cầu (sau Phase 22)
Tất cả đã kiểm trên trình duyệt thật và có test trong `server/tests/p20_api_test.py` (xanh cùng `memory_test`, `smoke_test`).

| Tính năng | Cách dùng / hành vi | API |
|---|---|---|
| Quản lý hộp thoại | Menu ⋯ trên mỗi hộp thoại: **Đổi tên** (nhập tại chỗ; Enter lưu, Esc hủy; nhấp đúp cũng được; tối đa 60 ký tự), **Xóa** (có xác nhận), **Xóa tất cả hộp thoại** ở cuối sidebar | `PATCH /conversations/{id}`, `DELETE /conversations/{id}`, `DELETE /conversations` |
| Ghim hộp thoại | Mục **Ghim / Bỏ ghim** trong menu; hộp thoại ghim lên đầu danh sách có 📌, đổi tên không mất ghim. DB cũ tự thêm cột `pinned` khi khởi động | `PATCH {pinned}` |
| Xuất file | **Xuất Markdown** (đọc/in) và **Xuất JSON** (lưu/xử lý). Chỉ nội dung người dùng thấy, không kèm plan/trace dev. Tên file bỏ dấu | `GET /conversations/{id}/export?format=md` hoặc `json` |
| Xuất PDF | **Xuất PDF** mở trang in ở tab mới và tự gọi hộp thoại in để Lưu thành PDF. Nội dung được escape HTML (chống chèn script). Người dùng đã tự thử, chạy tốt. Không dùng thư viện PDF (tránh thêm dependency và font); tải thẳng file `.pdf` để sau, đề xuất fpdf2 kèm font có dấu | `format=pdf` |

Ghi chú vận hành:
- Nút "Xóa tất cả" xóa hộp thoại của mọi người dùng chung DB (hệ thống chưa có đăng nhập); đã để ghi chú `ponytail:` ở chỗ cần lọc theo người dùng khi triển khai cho nhiều người.
- Khi thử, tôi từng bấm "Xóa tất cả" trên DB dev của máy này (chỉ có hộp thoại thử của tôi và agent). Từ đó chỉ xóa từng hộp thoại do mình tạo.
- Chưa xác nhận bằng công cụ việc trình duyệt lưu file `.md`/`.json` xuống đĩa (chỉ kiểm đường dẫn, header, nội dung); người dùng đã tự thử PDF.

## 4. Số đo cuối ngày (chế độ luật, bộ mù là số chính thức)
| Bộ | top-1 | Hành vi | Hỏi lại đúng | Xin lỗi đúng |
|---|---|---|---|---|
| HOLDOUT-4 (90 mục / 106 lượt) | 75% (58/77) | 82% (87/106) | 8/16 | 13/13 |
| pseudo_real 2 (34 lượt) | 68% (19/28) | 68% | 0/3 | 2/3 |
| HOLDOUT-3 (chạy lại) | 75% (50/67) | 86% | - | - |
| pseudo_real 1 (đã bị xem lỗi) | 57% (17/30) | 74% | 1/6 | 6/6 |
| Bộ team (10 câu, chấm luật) | - | 7/10 PASS | - | - |

Hybrid so với luật trên bộ mù: HOLDOUT-4 top-1 73% so với 75%; pseudo_real 2 64% so với 68%; bộ team 5/10 so với 7/10.
Bịa số trên HOLDOUT-3: 3,4% (hôm trước 7,1%). Chưa đo bịa số trên HOLDOUT-4 và pseudo_real.
Các số DEV 96–99% là bộ đã tune (có ca agent tự soạn), chỉ dùng để theo dõi hồi quy.

Gate hồi quy chế độ luật (đã tự chạy lại độc lập): DEV cũ 209 top-1 96,3%, hành vi 97,6%, bịa số 0,0%, ngoài phạm vi 30/30, ctx 89/91, synth TEST 96,3%.

## 5. Phát hiện và điều cần trung thực
- Mục tiêu đợt 4 (top-1 ≥ 80%, hành vi ≥ 88% trên bộ mù) **chưa đạt**. Phần cải thiện thực chất nằm ở "trả đúng ý", chưa nằm ở "chọn đúng thủ tục".
- Top-3 trên HOLDOUT-3 tụt từ 82% xuống 78% sau đợt 4 dù top-1 tăng; chưa giải thích được.
- Bộ test chung của nhóm: TC02 mong "bản sao 8.000đ" nhưng snapshot không có (lệ phí 0, text rỗng) — cần nhóm xác nhận nguồn. TC03 mong cả thời hạn khi câu chỉ hỏi giấy tờ.
- Phase 16 mất báo cáo do lỗi công cụ; đã kiểm lại bằng gate độc lập trước khi giữ thay đổi.
- Agent tự thêm ca vào DEV nên số DEV không so được với mốc cũ nếu không lọc các ca `p16`/`p18`/`p19`.
- Mọi bộ test đều do model soạn; chưa có câu hỏi thật từ người dân.

## 6. Việc cần quyết / bước tiếp theo
1. Nhóm đưa 20–30 câu hỏi thật (log hoặc người dân) làm bộ kiểm cuối.
2. Có làm thêm vòng sửa "hỏi lại khi mơ hồ" và chọn nhầm anh em, rồi soạn HOLDOUT-5 để kiểm không.
3. Xác nhận nguồn lệ phí khai sinh (TC02).
4. Giữ hay tắt hẳn bước LLM sinh chữ (chưa chứng minh có lợi); nếu muốn thử LLM Planner tiếp thì cần model lớn hơn hoặc hiệu chỉnh confidence.
5. Có làm RAG/import tài liệu (Box 5B/6B) trong đợt sau không.
6. Cài thử `requirements.txt` trên venv sạch khi có mạng tin cậy tới PyPI.

## 7. Tình trạng bàn giao
Folder `system3/` sẵn sàng push GitHub (tài liệu đã cập nhật, kết quả trung gian đã dọn). Chi tiết số liệu và giới hạn: `README.md`; báo cáo từng phase: `eval/P18_REPORT.md`, `P19_REPORT.md`, `P20_REPORT.md`; báo cáo ngắn cho nhóm: `docs/BAO_CAO_DOT4.md`.

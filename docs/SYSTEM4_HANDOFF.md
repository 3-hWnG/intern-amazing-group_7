# System 4 — Bàn giao để phiên sau bắt nhịp nhanh (2026-10-07)

## 0. Cập nhật 2026-10-08 — NV5 xong (tốc độ / model / độ chính xác / chào hỏi)
- Chi tiết + mọi số đo: `docs/SYSTEM4_NV5_TOC_DO_CHINH_XAC.md`. Bộ đo: `system4/eval/bench.py` (server riêng cổng 8399).
- Bài thi cuối: đúng 73 % → **92 %**, câu chào khi bật dữ liệu 50 % → **100 %**, lỗi hành vi 9 → 1; câu có dữ liệu chậm thêm ~0,5 s (vẫn dưới 5 s), chat thường và câu chào nhanh hơn.
- Friendly mặc định dùng `qwen3:4b-instruct-2507-q4_K_M` (0,2); "Suy nghĩ kỹ" + Strict vẫn `qwen3:4b`. `Set up first time.bat` tải đủ model.
- Nhánh git làm việc: **`System_4`** (đã đẩy lần đầu 2026-10-08; commit NV5 chỉ ở máy cho tới khi người dùng bảo đẩy).
- Strict (System 3) cũng dùng Instruct qua `LLM_MODEL` trong `Launch web.bat` (người dùng chọn 1A; đo 2 lần: đúng y hệt, không chậm hơn) — xem NV5 D6.

## 1. Trạng thái (2026-10-07, trước NV5)
- Xong: NV1 (nền tảng, đăng nhập, công tắc Strict/Friendly, ⚙), NV2 (AI kiểu ChatGPT, chế độ Nhanh/Suy nghĩ kỹ), NV3 (tải dữ liệu → Chuyên gia), NV4 (Quản trị, phiên bản dữ liệu Strict, cào, tính năng ChatGPT cho Strict), bộ công cụ dev (🔍 Soi, Vì sao?, Cách đọc tệp, Thử tìm kiếm).
- Git: nhánh `System_3&4` (github.com/3-hWnG/intern-amazing-group_7), **10 commit chỉ ở máy, CHƯA đẩy** — chỉ đẩy khi người dùng bảo.
- Báo cáo chi tiết từng nhiệm vụ: `docs/SYSTEM4_NV1_NEN_TANG.md` … `SYSTEM4_NV4_QUAN_TRI.md` (phần C/D/E). Giới hạn Chuyên gia: NV3 phần D. Việc hoãn (đo bịa, so model): NV2 phần E.

## 2. Phản hồi mới nhất của người dùng (nguyên văn, 2026-10-07)
> It worked thanks though I want to change a lot, it's time is bad, it's accuracy is bad, it can't say hello/goodbye when has a dataset on. Please note it all down so you can quickly catch up. We will meet in another session since we ran out of context windows. Mark my priority now is Improve time, change model if necessary, improve accuracy radically (clarify with trade-offs like I specified above if the new you forget the rule to work with me)

## 3. Ưu tiên phiên sau (theo thứ tự)
| # | Việc | Ghi chú để bắt đầu |
|---|---|---|
| 1 | **Cải thiện thời gian** | Số hiện tại (RTX 4050 6 GB, `qwen3:4b`): Friendly Nhanh chữ đầu ~1 s, cả câu ~2,5 s; Chuyên gia chữ đầu 2,3–3,6 s, cả câu 4,5–5,7 s (tìm 0,7–1,4 s, phần lớn do reranker); Suy nghĩ kỹ 25–40 s; câu đầu sau khi bật server chậm thêm vì nạp model. Ngân sách người dùng: ~5 s cho câu trả lời nhanh. |
| 2 | **Đổi model nếu cần** | `qwen3:4b` trên máy là bản Qwen3-2507 **luôn suy nghĩ**; chế độ Nhanh phải ép JSON để tắt suy nghĩ (nhanh nhưng kém chính xác). Ứng viên: `qwen3.5:4b` (Ollama, 3,3 GB, 4-bit, có suy nghĩ/công cụ/hình ảnh — đội khác đang dùng). Trước đây người dùng hết dung lượng mạng nên hoãn; hỏi lại xem đã tải được chưa (người dùng tự chạy `ollama pull`). Lưu ý 6 GB GPU: System 3 cũng dùng `qwen3:4b` → hai model khác nhau sẽ phải đổi qua lại (đo thời gian nạp lại). Mọi lời gọi model phải cùng `num_ctx` (8192) nếu không sẽ nạp lại ~13 s. |
| 3 | **Cải thiện độ chính xác "triệt để"** | Đã biết: chế độ Nhanh bịa chi tiết (số điện thoại Team 7, địa điểm); trùng tên (bé An); không đếm / tổng hợp được cả bảng; bộ đọc bảng dựa luật (tiêu đề nhiều tầng chưa xử lý). Chưa có bài đo bịa có hệ thống — kế hoạch ở NV2 phần E. Dùng bộ công cụ dev (🔍, Thử tìm kiếm) để chẩn đoán. |
| 4 | **Chào / tạm biệt khi đang bật dữ liệu** | Khi có bộ dữ liệu đang bật, MỌI tin đều qua đường Chuyên gia ("chỉ trả lời từ dữ liệu") → "xin chào", "cảm ơn", "tạm biệt" bị trả lời kiểu "không có trong dữ liệu". Cần một đường riêng cho câu xã giao (nhận biết bằng code hoặc lời dặn) để trả lời tự nhiên mà không tra dữ liệu. Liên quan: chốt "chỉ trả lời từ dữ liệu" trong `system4/server/chat.py` (`kb_violation`, ngưỡng 60 ký tự). |

## 4. Quy tắc làm việc với người dùng (BẮT BUỘC — người dùng nhắc "nếu bạn mới quên")
- Trả lời **ngắn**, **bảng trước** rồi mới giải thích; người dùng **không chuyên** AI / phần mềm → dùng từ dễ hiểu, bàn theo hành vi của web.
- Prompt tiếng Việt → trả lời tiếng Việt; tiếng Anh → tiếng Anh.
- Mọi câu hỏi / trade-off: **trắc nghiệm 4 lựa chọn** (A = khuyên dùng, ghi "(Recommended)"), tối đa 10 câu, ngắn.
- Quy trình mỗi việc: (người dùng có thể sửa .docx) → đọc lại + xác nhận → hỏi trade-off (trắc nghiệm) → **lập kế hoạch, chờ Approve** → làm một mạch → việc ngoài ý muốn: ghi cách xử lý vào tài liệu và báo lại; trade-off phát sinh → hỏi trắc nghiệm.
- Ghi **nguyên văn** câu trả lời của người dùng vào tài liệu nhiệm vụ; ý của Claude để ở phần riêng.
- Không đổi **kiến trúc** System 3 (thêm tính năng bổ trợ thì được); model mới: hỏi trước, người dùng tự tải (`ollama pull …`), cập nhật `Set up first time.bat` + `requirements.txt`.
- Commit ở máy thoải mái; **chỉ đẩy GitHub khi người dùng bảo**.
- Báo kết quả trung thực: số đo, test nào chạy, test nào tự soạn, chỗ nào chưa kiểm.

## 5. Bản đồ nhanh
| Cần | Ở đâu |
|---|---|
| Chạy web | `Launch web.bat` (cổng 8300, `S4_ENABLED=1`); cài đặt lần đầu `Set up first time.bat` |
| Code System 4 | `system4/server/` (chat.py = một lượt Friendly; persona.py = lời dặn; search.py = tìm + reranker; ingest.py = đọc tệp; procs.py/admin.py/strict.py = NV4) |
| Cài đặt | `system4/server/config.py` (khối MẶC ĐỊNH) + ⚙ trên web |
| Test | `cd server` + `PYTHONPATH=<pyroot>` → `python ../system4/tests/test_nv1.py` … `test_nv4.py`; test System 3 trong `server/tests`, `smoke_test.py`, `e2e_test.py` |
| Đo trên model thật | `system4/eval/nv2_behavior.py` (22 tình huống hành vi), `system4/eval/nv3_specialist.py` (17 câu Chuyên gia); kết quả trong `system4/eval/results/` |
| Chẩn đoán | 🔍 dưới câu trả lời (dev), Quản trị → Thử tìm kiếm, Dữ liệu → Cách đọc |

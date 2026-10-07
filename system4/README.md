# System 4 — Friendly mode (chạy song song System 3 trên cùng web)

Trạng thái: **xong NV1 (nền tảng), NV2 (AI trò chuyện kiểu ChatGPT), NV3 (dataset → Chuyên gia), NV4 (Quản trị + tính năng ChatGPT cho Strict)**. Yêu cầu và kế hoạch: [docs/SYSTEM4_NV1_NEN_TANG.md](../docs/SYSTEM4_NV1_NEN_TANG.md) … NV4. Deploy: [docs/SYSTEM4_DEPLOY.md](../docs/SYSTEM4_DEPLOY.md).

## Người dùng thấy gì
| | |
|---|---|
| Mở web | Trang đăng nhập / đăng ký. **Tài khoản đầu tiên là dev**, các tài khoản sau là user. |
| Trang chính | Giao diện như System 3, thêm công tắc **Strict \| Friendly** ở thanh trên. |
| Strict | Nguyên hành vi System 3 (thủ tục hành chính, có nguồn), thêm: sao chép, tạo lại, sửa tin, ‹ 1/2 ›, 👍/👎, Dừng (System 4 phát lại các câu trước vào nhánh mới khi sửa / tạo lại). |
| Friendly | Trợ lý hỗ trợ của **Team 7** (đổi trong ⚙). Chữ hiện dần, **Dừng**, chữ có định dạng (in đậm, danh sách, bảng, code), sao chép, **tạo lại**, **sửa tin đã gửi**, chuyển phiên bản **‹ 1/2 ›**, 👍/👎. Hỏi lại bằng **nút lựa chọn** (tối đa 2 lần liên tiếp). Chỉ tiếng Việt: viết ngôn ngữ khác thì có câu xin lỗi rồi trả lời tiếng Việt; chữ Hán/emoji bị lọc. Mặc định **trả lời nhanh** (~1–3 s); công tắc **Suy nghĩ kỹ**, nút **Trả lời nhanh** để ngắt, nút **Kỹ hơn**. |
| Dữ liệu → Chuyên gia (NV3) | Nút **+** (hoặc kéo thả) tải CSV / Excel / JSON / TXT / Word / PDF. Bật bộ dữ liệu nào thì AI chỉ trả lời từ đó, có **nguồn [n]** bấm xem bản ghi gốc; không có thì nói không có. Cửa sổ **Dữ liệu**: bật/tắt, xem, xoá, dung lượng 1 GB (dev không giới hạn), cảnh báo khi bật quá nhiều. |
| Bộ nhớ (mọi người dùng) | Nút **Bộ nhớ** ở góc dưới thanh bên: chọn **Tự động ghi nhớ** hoặc **Chỉ nhớ khi tôi bảo "hãy nhớ…"**, xem / xoá từng điều. Điều đã nhớ dùng ở mọi hội thoại Friendly. Sau câu trả lời có dòng "Đã cập nhật bộ nhớ". |
| Danh sách hội thoại | Một danh sách chung, mỗi dòng có nhãn Strict/Friendly. Bấm một dòng thì tự chuyển sang chế độ của nó. Mỗi người chỉ thấy hội thoại của mình. |
| Quản trị (chỉ dev, NV4) | Trang `/s4/admin`: **Dữ liệu Strict** (phiên bản, nháp, chuẩn dữ liệu, so sánh, áp dụng, cào dichvucong.gov.vn), **Dữ liệu người dùng**, **Người dùng** (tạo, vai trò, khoá, đặt lại mật khẩu, xoá). |
| ⚙ Cài đặt (chỉ dev) | Có thêm: tên/mô tả doanh nghiệp, lời dặn thêm, **guardrail** (Chặn / Lời dặn / Thay câu trả lời, bật/tắt từng luật), câu xin lỗi ngôn ngữ, số lần hỏi lại, bộ nhớ, ngưỡng tóm tắt. **Lưu** (ghi `runtime/settings.json`) · **Đặt làm mặc định** (ghi vào `server/config.py`, bản cũ ở `config.py.bak`) · **Về mặc định**. Tải lại trang để áp dụng. |

## Cách cắm vào System 3
- `server/main.py` của System 3 chỉ thêm 5 dòng ở cuối: khi `S4_ENABLED=1` thì gọi `system4/server/hook.py: install(app, store)`.
- `Launch web.bat` đặt `S4_ENABLED=1`. Không đặt / `S4_ENABLED=0` → web System 3 y như trước. **Test của System 3 chạy ở chế độ tắt**, không cần sửa.
- `install` thêm: API `/s4/*`, tệp tĩnh `/s4/static`, middleware đăng nhập cho cả web, trang `/` mới, và lọc các API `/conversations*`, `/chat` của System 3 theo người dùng. Code, DB, công cụ AI của System 3 không đổi.
- Hội thoại Strict có từ trước khi bật đăng nhập → thuộc tài khoản dev đầu tiên.

## Thư mục
| | |
|---|---|
| `server/config.py` | khối MẶC ĐỊNH + danh sách cài đặt hiện trên panel |
| `server/settings.py` | đọc/ghi cài đặt (ghi đè → mặc định), kiểm kiểu/giới hạn |
| `server/hook.py` | cắm vào System 3: cổng đăng nhập, lọc hội thoại Strict theo người |
| `server/routes.py` | API `/s4/*`: đăng nhập, danh sách chung, chat Friendly (SSE), cài đặt |
| `server/auth.py`, `db.py`, `schema.sql` | mật khẩu bcrypt, phiên cookie (DB chỉ lưu sha256), SQLite riêng `runtime/system4.db` |
| `server/llm.py` | gọi Ollama theo luồng, hàng đợi 1 lượt (GPU 6 GB), ẩn phần "suy nghĩ"; `chat_json` cho bộ nhớ/tóm tắt |
| `server/chat.py` | một lượt Friendly: guardrail → ngôn ngữ → lời dặn → sinh chữ có lọc → lưu → bộ nhớ/tóm tắt nền |
| `server/persona.py` | lời dặn hệ thống (vai trò theo .docx), tách nút lựa chọn `[[CHOICES]]`, nhận biết bực bội |
| `server/guard.py` | guardrail mở rộng được (cài đặt `GUARDRAILS`) |
| `server/lang.py` | nhận biết tiếng Việt (cả không dấu), bộ lọc chữ ngoài Latin + emoji |
| `server/memory.py`, `context.py` | bộ nhớ dài hạn từng người; tóm tắt hội thoại dài theo nhánh |
| `server/ingest.py`, `datasets.py`, `search.py` | NV3: đọc tệp → cấu trúc định sẵn; tải lên, dung lượng, nạp nền; tìm từ khoá (FTS5) + nghĩa (bge-m3, Qdrant local) + reranker |
| `server/procs.py`, `admin.py`, `strict.py` | NV4: phiên bản dữ liệu Strict + áp dụng (dựng bằng `system3.data.build`); API trang Quản trị; phiên bản / phát lại cho Strict |
| `scraper/` | trình cào chép từ V10.3 (`Database/pipeline`): client, danh mục, chi tiết, chuẩn hoá; `run.py` chạy nền |
| `eval/nv2_behavior.py`, `nv3_specialist.py` | đo trên model thật: hành vi Friendly; độ đúng + nguồn của Chuyên gia |
| `web/` | `templates/index.html` + `static/js/app.js` = bản sao giao diện System 3 + phần thêm; `login.html`; `admin.html` + `admin.js` (Quản trị); `static/vendor/` = marked 18.1.0 + DOMPurify 3.4.16 (lưu sẵn, chạy offline) |
| `tests/test_nv1.py` … `test_nv4.py` | test NV1–NV4 (model giả, DB tạm; NV4 dùng bản sao DB thủ tục) |
| `setup_models.py` | tải reranker, kiểm GPU (Set up first time.bat gọi) |
| `runtime/` | DB, settings.json, `datasets/` (tệp người dùng), `qdrant/` (vector), `procs/` (phiên bản dữ liệu Strict), `scrape/` (không đưa lên Git) |
| `models/` | model tải về (không đưa lên Git) |

## Chạy test
```bat
cd server
set PYTHONPATH=<thư mục pyroot> && set PYTHONIOENCODING=utf-8
python ..\system4\tests\test_nv1.py
python ..\system4\tests\test_nv2.py
python ..\system4\tests\test_nv3.py
python ..\system4\tests\test_nv4.py
```

## Lưu ý
- `qwen3:4b` (bản luôn suy nghĩ) là model duy nhất được dùng. **Chế độ Nhanh** (mặc định) ép đầu ra JSON nên model không suy nghĩ: chữ đầu ~1 s, cả câu ~2,5 s, nhưng có thể bịa chi tiết. **Suy nghĩ kỹ** (công tắc cạnh ô nhập, hoặc nút "Kỹ hơn"): ~25–40 s, bấm "Trả lời nhanh" để ngắt. Số đo: docs/SYSTEM4_NV2_AI_TRO_CHUYEN.md phần D.
- Panel AI (nút "AI bật/tắt") ở chế độ Strict là của System 3: đổi được khi server chạy `S3_DEV=1` **và** tài khoản là dev.
- Chỉ chạy **1 tiến trình server** (hàng đợi và cấu hình nằm trong bộ nhớ). Xem docs/SYSTEM4_DEPLOY.md.

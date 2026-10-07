# System 4 — Friendly mode (chạy song song System 3 trên cùng web)

Trạng thái: **xong NV1 (nền tảng), NV2 (AI trò chuyện kiểu ChatGPT)**. Yêu cầu và kế hoạch: [docs/SYSTEM4_NV1_NEN_TANG.md](../docs/SYSTEM4_NV1_NEN_TANG.md) … NV4. Deploy: [docs/SYSTEM4_DEPLOY.md](../docs/SYSTEM4_DEPLOY.md).

## Người dùng thấy gì
| | |
|---|---|
| Mở web | Trang đăng nhập / đăng ký. **Tài khoản đầu tiên là dev**, các tài khoản sau là user. |
| Trang chính | Giao diện như System 3, thêm công tắc **Strict \| Friendly** ở thanh trên. |
| Strict | Nguyên hành vi System 3 (thủ tục hành chính, có nguồn). |
| Friendly | Trợ lý hỗ trợ của **Team 7** (đổi trong ⚙). Chữ hiện dần, **Dừng**, chữ có định dạng (in đậm, danh sách, bảng, code), sao chép, **tạo lại**, **sửa tin đã gửi**, chuyển phiên bản **‹ 1/2 ›**, 👍/👎. Hỏi lại bằng **nút lựa chọn** (tối đa 2 lần liên tiếp). Chỉ tiếng Việt: viết ngôn ngữ khác thì có câu xin lỗi rồi trả lời tiếng Việt; chữ Hán/emoji bị lọc. NV3 thêm dataset. |
| Bộ nhớ (mọi người dùng) | Nút **Bộ nhớ** ở góc dưới thanh bên: chọn **Tự động ghi nhớ** hoặc **Chỉ nhớ khi tôi bảo "hãy nhớ…"**, xem / xoá từng điều. Điều đã nhớ dùng ở mọi hội thoại Friendly. Sau câu trả lời có dòng "Đã cập nhật bộ nhớ". |
| Danh sách hội thoại | Một danh sách chung, mỗi dòng có nhãn Strict/Friendly. Bấm một dòng thì tự chuyển sang chế độ của nó. Mỗi người chỉ thấy hội thoại của mình. |
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
| `eval/nv2_behavior.py` | đo hành vi trên model thật (xem docs/SYSTEM4_NV2_AI_TRO_CHUYEN.md, phần C) |
| `web/` | `templates/index.html` + `static/js/app.js` = bản sao giao diện System 3 + phần thêm; `login.html`; `static/vendor/` = marked 18.1.0 + DOMPurify 3.4.16 (lưu sẵn, chạy offline) |
| `tests/test_nv1.py`, `test_nv2.py` | test NV1, NV2 (LLM giả, DB tạm) |
| `setup_models.py` | tải reranker, kiểm GPU (Set up first time.bat gọi) |
| `runtime/` | DB + settings.json (không đưa lên Git) |
| `models/` | model tải về (không đưa lên Git) |

## Chạy test
```bat
cd server
set PYTHONPATH=<thư mục pyroot> && set PYTHONIOENCODING=utf-8
python ..\system4\tests\test_nv1.py
python ..\system4\tests\test_nv2.py
```

## Lưu ý
- `qwen3:4b` đang cài là bản **luôn suy nghĩ** (Qwen3-2507 thinking). Cài đặt "AI suy nghĩ trước khi trả lời" phải BẬT với model này (phần suy nghĩ được ẩn). Câu trả lời đầu tiên mất ~11–17 s. Model không suy nghĩ (`qwen3:4b-instruct-2507-q4_K_M`) nhanh hơn nhiều nhưng cần tải thêm ~2,5 GB.
- Panel AI (nút "AI bật/tắt") ở chế độ Strict là của System 3: đổi được khi server chạy `S3_DEV=1` **và** tài khoản là dev.
- Chỉ chạy **1 tiến trình server** (hàng đợi và cấu hình nằm trong bộ nhớ). Xem docs/SYSTEM4_DEPLOY.md.

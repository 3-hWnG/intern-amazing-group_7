# KẾ HOẠCH — Auth · Hàng đợi · Hội thoại nhiều cửa sổ · Tóm tắt ngữ cảnh
Bản nháp chờ duyệt · 13/09/2026 · Nhóm 7

---

## 0. MÂU THUẪN VỚI THÔNG TIN TRƯỚC ĐÓ — đọc trước khi duyệt

**(a) Mentor nói không cần deploy, demo local là đủ.** Trước đây tôi khuyến nghị
CẮT auth và queue vì chúng không cải thiện được con số nào và deadline gấp. Nay
bạn xác nhận hai thứ đó là bắt buộc → tôi làm theo. Ghi rõ để sau này không ai
tưởng là tôi đổi ý không lý do: **đây là quyết định của bạn, không phải của số liệu.**

**(b) Mentor yêu cầu xử lý tuần tự 1-1; đồng đội nói sẽ khó dùng.** Cả hai đều
đúng ở góc của mình. Thiết kế dưới đây **không chọn phe**: hàng đợi có tham số
`QUEUE_CONCURRENCY`, mặc định = 1 (đúng yêu cầu mentor), đổi thành 2–4 là chạy
song song. Kèm theo hiển thị "bạn đang đứng thứ N trong hàng đợi" — chính là thứ
làm dịu phản đối về trải nghiệm. Khi họp, bạn demo được cả hai chế độ chỉ bằng
một dòng config, thay vì tranh luận suông.

**(c) `core/session.py` hiện tại lưu trong RAM.** Nó sẽ bị THAY THẾ bằng tầng
CSDL. Mất bộ nhớ khi restart là không chấp nhận được khi đã có đăng nhập.

**(d) PDPL 91/2025.** Khi có đăng nhập là bắt đầu lưu dữ liệu định danh (email,
lịch sử hội thoại). Kế hoạch này mặc định: KHÔNG log nội dung ra file, có
`RETENTION_DAYS` để tự xoá, và nút xoá dữ liệu cho từng người dùng. Rẻ khi làm
ngay, đắt khi vá sau.

---

## 1. HIỆN TRẠNG KỸ THUẬT

| Thành phần | Trạng thái |
|---|---|
| Git | `.git` tồn tại nhưng **0 commit** (lần tạo trước bị kẹt file lock) |
| Thư viện có sẵn | `bcrypt`, `starlette`, `fastapi` |
| Thư viện thiếu | không thiếu gì nếu dùng `sqlite3` chuẩn + `secrets` chuẩn |
| Frontend | `index.html` 33 dòng, `app.js` 95 dòng, `styles.css` 165 dòng — rất nhỏ |
| Bộ nhớ hội thoại | `core/session.py`, chỉ trong RAM |
| Truy hồi | v4, R@1 0.8556 — **phải giữ nguyên sau khi làm xong** |

**Quyết định phụ thuộc:** dùng `sqlite3` trong thư viện chuẩn Python, KHÔNG thêm
SQLAlchemy. Lý do: không thêm phụ thuộc, file đơn, đủ cho demo 1 máy. Toàn bộ
truy vấn SQL gom vào `db/repositories.py` — muốn đổi sang PostgreSQL sau này chỉ
sửa một file.

---

## BƯỚC 0 — Git (BẠN CHẠY, TÔI KHÔNG LÀM ĐƯỢC) (Nhân Edit làm rồi - này chuyện của máy tui)

Tôi không xoá được file trên máy bạn (quyền bị từ chối), mà `git` cần xoá file
lock của chính nó. Vì vậy bước này bạn phải tự chạy:

```powershell
cd "D:\Claude\LLM for Procedures V10.3\intern-amazing-group_7-Re-imagine-V10.2"
Remove-Item .git\index.lock -ErrorAction SilentlyContinue
git add -A
git commit -m "Baseline v4: R@1 0.8556, R@5 0.9753, MRR 0.9061"
git log --oneline
```

Phải thấy đúng 1 commit. **Không duyệt kế hoạch này trước khi có commit đó** —
đó là cách duy nhất để quay lại nếu hỏng.

Sau mỗi giai đoạn tôi sẽ dừng để bạn commit, nhãn: `phase-1-db`, `phase-2-auth`, …

---

## BƯỚC 1 — Tầng cơ sở dữ liệu

**File mới**
```
app/db/__init__.py
app/db/schema.sql          -- định nghĩa bảng, chạy 1 lần khi khởi động
app/db/connection.py       -- mở kết nối, bật WAL, chạy migration
app/db/repositories.py     -- TOÀN BỘ câu SQL nằm ở đây
```

**Lược đồ**
```sql
users(
  id INTEGER PK, email TEXT UNIQUE, password_hash TEXT,
  display_name TEXT, created_at TEXT, is_admin INTEGER DEFAULT 0)

auth_sessions(
  token TEXT PK, user_id INTEGER FK, created_at TEXT,
  expires_at TEXT, user_agent TEXT)

conversations(
  id INTEGER PK, user_id INTEGER FK, title TEXT,
  created_at TEXT, updated_at TEXT,
  summary TEXT,                    -- bản tóm tắt do AI sinh
  summary_upto_message_id INTEGER, -- đã tóm tắt tới tin nhắn nào
  archived INTEGER DEFAULT 0)

messages(
  id INTEGER PK, conversation_id INTEGER FK, role TEXT,
  content TEXT, tier TEXT, confidence REAL, sources TEXT,
  factcheck TEXT, token_estimate INTEGER, created_at TEXT)

feedback(
  id INTEGER PK, message_id INTEGER FK, user_id INTEGER FK,
  verdict TEXT, note TEXT, created_at TEXT)

job_log(                          -- để quan sát hàng đợi, không bắt buộc
  id INTEGER PK, user_id INTEGER, conversation_id INTEGER,
  status TEXT, enqueued_at TEXT, started_at TEXT, finished_at TEXT,
  wait_ms INTEGER, process_ms INTEGER)
```

**Chi tiết kỹ thuật**
- Bật `PRAGMA journal_mode=WAL` — cho phép đọc trong khi ghi.
- `PRAGMA foreign_keys=ON`.
- SQLite là API đồng bộ; FastAPI là async → mọi lời gọi DB chạy qua
  `asyncio.to_thread` để không chặn vòng lặp sự kiện.
- File DB: `app/runtime/app.db` (đã nằm trong `.gitignore`).
- Chỉ mục: `messages(conversation_id, id)`, `conversations(user_id, updated_at)`.

**Config thêm**
```python
DB_PATH = RUNTIME_DIR / "app.db"
RETENTION_DAYS = 90        # 0 = giữ vĩnh viễn
```

---

## BƯỚC 2 — Xác thực

**File mới:** `app/core/auth.py`, `app/api/auth_routes.py`, `app/templates/login.html`

**Cách làm:** cookie phiên, KHÔNG dùng JWT.
Lý do: đây là ứng dụng render phía server, JWT không thu hồi được, còn cookie
phiên thì xoá một dòng trong DB là đăng xuất ngay. Ít mã hơn, an toàn hơn.

- Mật khẩu: `bcrypt` (đã có sẵn), cost mặc định.
- Token phiên: `secrets.token_urlsafe(32)`, lưu trong `auth_sessions`.
- Cookie: `HttpOnly`, `SameSite=Lax`, `Secure` chỉ khi chạy HTTPS (config).
- Hết hạn: `AUTH_SESSION_DAYS = 14`, gia hạn trượt mỗi lần dùng.
- Dependency `current_user()` — mọi route chat đều bắt buộc.
- Giới hạn thử sai: 5 lần/15 phút cho mỗi email (chống dò mật khẩu).

**Endpoint**
```
GET  /login          trang đăng nhập
POST /api/register   email + mật khẩu + tên hiển thị
POST /api/login      trả cookie
POST /api/logout     xoá phiên
GET  /api/me         thông tin người đang đăng nhập
```

**Quy tắc mật khẩu:** tối thiểu 8 ký tự. Không làm xác minh email (ngoài phạm vi).

**KHÔNG làm:** OAuth, quên mật khẩu qua email, phân quyền nhiều vai trò. Ghi rõ
là đã cắt, không để lửng lơ.

---

## BƯỚC 3 — Nhiều cửa sổ hội thoại

**File mới:** `app/api/chat_routes.py` (thay phần `/chat` trong `routes.py`)

```
GET    /api/conversations              danh sách của tôi
POST   /api/conversations              tạo mới
GET    /api/conversations/{id}         lấy toàn bộ tin nhắn
PATCH  /api/conversations/{id}         đổi tên
DELETE /api/conversations/{id}         xoá (xoá mềm rồi xoá hẳn)
POST   /api/conversations/{id}/chat    gửi câu hỏi (stream)
```

- Kiểm tra quyền sở hữu ở MỌI endpoint — không được đọc hội thoại người khác.
- Tiêu đề tự sinh từ ~6 từ đầu của câu hỏi đầu tiên (không tốn lời gọi LLM).
- Trạng thái "đang chờ làm rõ" (tầng B) chuyển từ RAM sang cột trong
  `conversations` — nếu không, hỏi lại xong restart là mất.

---

## BƯỚC 4 — Hàng đợi

**File mới:** `app/core/queue.py`

**Vấn đề khó nhất:** vừa xếp hàng tuần tự vừa giữ được hiệu ứng gõ chữ (stream).
Nếu làm sai, người dùng ngồi nhìn màn hình trắng cho tới khi xong.

**Giải pháp:** worker sở hữu lời gọi LLM, đẩy từng mẩu chữ qua một hàng đợi
riêng của request đó.

```
request  ──► tạo out_queue riêng
         ──► đẩy job {prompt, out_queue} vào hàng đợi chung
         ──► trả StreamingResponse đọc từ out_queue
                    ▲
worker (1 luồng) ───┘  lấy từng job, chạy pipeline, đẩy chữ vào out_queue
                       xong thì đẩy sentinel báo kết thúc
```

- `QUEUE_CONCURRENCY = 1` (mặc định, đúng yêu cầu mentor).
- `QUEUE_MAX_DEPTH = 20` — đầy thì từ chối lịch sự, không treo.
- `QUEUE_JOB_TIMEOUT = 120` giây — job treo bị huỷ, không kẹt cả hàng.
- Trước khi chạy, gửi cho client vị trí hàng đợi qua header `X-Queue-Position`
  và một dòng "Đang chờ… trước bạn còn N người" nếu N > 0.
- Ghi `job_log` để có số liệu thật về thời gian chờ — dùng chính số đó để nói
  chuyện với mentor và đồng đội thay vì cãi nhau bằng cảm tính.
- Worker khởi động trong `lifespan`, tắt gọn khi shutdown.

---

## BƯỚC 5 — Kiểm soát độ dài ngữ cảnh + tóm tắt

**File mới:** `app/core/summarizer.py`

```
trước khi dựng prompt:
  ước lượng token của (tóm tắt hiện có + các tin nhắn chưa tóm tắt)
      │
      ├─ ≤ ngưỡng ──► dùng nguyên
      └─ > ngưỡng ──► gọi LLM tóm tắt các tin nhắn CŨ NHẤT
                      ghi vào conversations.summary
                      ghi summary_upto_message_id
                      prompt = tóm tắt + N tin nhắn gần nhất
```

- Ước lượng token: số âm tiết × 1.4 (cách đã dùng trong `build_eval_set.py`,
  đủ chính xác cho việc này, không cần nạp tokenizer).
- `CONTEXT_TOKEN_BUDGET = 1800` (qwen2.5:1.5b có cửa sổ 32k nhưng mô hình nhỏ
  kém dần khi ngữ cảnh dài; giữ ngắn cho chất lượng, không phải vì giới hạn).
- `SUMMARY_KEEP_RECENT = 4` — luôn giữ nguyên văn 4 lượt gần nhất.
- Tóm tắt là **lời gọi LLM thêm** → chỉ chạy khi vượt ngưỡng, và ghi lại
  `summary_ms` để biết nó ăn bao nhiêu trong ngân sách 15 giây.
- Prompt tóm tắt yêu cầu giữ lại: thủ tục đang hỏi, thông tin cá nhân người dân
  đã cung cấp (tỉnh/thành, tình huống), và câu hỏi còn treo.

---

## BƯỚC 6 — Nút reset cho phát triển

**File mới:** `app/api/dev_routes.py`

```
POST /api/dev/reset       xoá dữ liệu (có xác nhận)
GET  /api/dev/stats       đếm user / hội thoại / tin nhắn
```

- Chặn bằng `DEV_TOOLS_ENABLED` trong config. **Phải đặt `False` ở bản cuối.**
- Khi bật, giao diện hiện một nút đỏ tách biệt hẳn, có hộp xác nhận gõ chữ.
- Ba mức: `my_conversations` | `all_conversations` | `everything` (kể cả users).
- Khi `DEV_TOOLS_ENABLED = False`, các route này **không được đăng ký** — không
  chỉ ẩn nút. Ẩn nút không phải là bảo mật.
- Khi khởi động, nếu `DEV_TOOLS_ENABLED = True` thì in cảnh báo to trong log.

---

## BƯỚC 7 — Giao diện

Phần tốn công nhất. Frontend hiện tại chỉ 293 dòng tổng cộng, gần như phải viết lại.

```
templates/login.html      đăng nhập / đăng ký
templates/index.html      viết lại: thanh bên + khung chat
static/js/auth.js         gọi login/register
static/js/conversations.js danh sách, tạo mới, đổi tên, xoá
static/js/chat.js         stream, nhãn tầng A/B/C/D, nút 👍/👎, vị trí hàng đợi
static/js/dev.js          nút reset (chỉ nạp khi bật)
static/css/styles.css     mở rộng
```

Giữ nguyên: giao diện tối/sáng và hiệu ứng gõ chữ hiện có — đó là thứ nhóm đã
làm tốt, không đụng vào.

Thêm mới: thanh bên danh sách hội thoại, nút "Cuộc trò chuyện mới", nhãn độ tin
cậy theo màu (A xanh / B vàng / C cam / D xám), nút phản hồi, chỉ báo hàng đợi.

---

## BƯỚC 8 — Kiểm thử & chống thụt lùi

1. `.\run.ps1` — **R@1 phải vẫn là 0.8556**. Nếu tụt, tôi đã làm hỏng truy hồi.
2. Kiểm thử khói thủ công: đăng ký → đăng nhập → tạo 2 hội thoại → hỏi ở cả hai
   → restart server → lịch sử còn nguyên → đăng xuất → không xem được hội thoại
   khi chưa đăng nhập.
3. Hàng đợi: mở 3 tab, gửi cùng lúc, xác nhận xử lý lần lượt và vị trí hiển thị đúng.
4. Tóm tắt: hỏi 15 lượt liên tiếp, xác nhận có tóm tắt và câu trả lời vẫn bám ngữ cảnh.
5. Reset: bấm, xác nhận sạch dữ liệu, DB vẫn dùng được.

---

## Config thêm (gom vào `config.py`)

```python
DB_PATH = RUNTIME_DIR / "app.db"
RETENTION_DAYS = 90

AUTH_ENABLED = True
AUTH_SESSION_DAYS = 14
AUTH_COOKIE_SECURE = False        # True khi chạy HTTPS
AUTH_MIN_PASSWORD_LENGTH = 8
AUTH_MAX_LOGIN_ATTEMPTS = 5

QUEUE_ENABLED = True
QUEUE_CONCURRENCY = 1             # mentor yêu cầu 1; đổi 2-4 nếu chấp nhận song song
QUEUE_MAX_DEPTH = 20
QUEUE_JOB_TIMEOUT = 120

CONTEXT_TOKEN_BUDGET = 1800
SUMMARY_KEEP_RECENT = 4
SUMMARY_ENABLED = True

DEV_TOOLS_ENABLED = True          # ĐẶT False Ở BẢN CUỐI
```

---

## Rủi ro

| Rủi ro | Mức | Xử lý |
|---|---|---|
| Stream qua hàng đợi làm hỏng hiệu ứng gõ chữ | **Cao** | Làm bước 4 riêng, test kỹ trước khi sang bước 5 |
| SQLite chặn vòng lặp async | Trung bình | Mọi lời gọi DB qua `asyncio.to_thread` |
| Sửa `pipeline.py` làm tụt R@1 | Trung bình | Chạy lại eval ở bước 8; có git để quay lại |
| Tóm tắt ăn mất ngân sách 15 giây | Trung bình | Đo `summary_ms`, chỉ chạy khi vượt ngưỡng |
| Route dev lọt vào bản cuối | **Cao** | Không đăng ký route khi cờ tắt + cảnh báo lúc khởi động |
| Viết lại frontend vỡ giao diện đang chạy | Trung bình | Commit trước bước 7 |

---

## Ước lượng

| Bước | Khối lượng |
|---|---|
| 0 Git | bạn làm, 1 phút |
| 1 CSDL | nhỏ |
| 2 Auth | vừa |
| 3 Hội thoại | vừa |
| 4 Hàng đợi | **khó nhất về kỹ thuật** |
| 5 Tóm tắt | vừa |
| 6 Reset | nhỏ |
| 7 Frontend | **nhiều việc nhất** |
| 8 Kiểm thử | nhỏ |

Tôi đề nghị dừng sau bước 4 và sau bước 7 để bạn chạy thử và commit.

---

## Việc CỐ Ý không làm

- Redis / RabbitMQ — `asyncio.Queue` đủ cho 1 tiến trình. Sơ đồ kiến trúc vẽ
  Redis, nhưng ở bản chạy local nó chỉ thêm thứ để hỏng.
- PostgreSQL — SQLite đủ; lớp repository để sẵn chỗ đổi.
- OAuth, quên mật khẩu, xác minh email.
- Hộ tịch R@1 0.667 — bạn yêu cầu để sau cùng.
- Đổi LLM sang qwen2.5:3b — việc riêng, đo riêng.

---

## Chờ bạn duyệt

1. Chạy bước 0 (git commit) trước.
2. Xác nhận: `QUEUE_CONCURRENCY = 1` làm mặc định — đúng ý mentor, và đồng đội
   vẫn đổi được. Có ổn không?
3. Xác nhận: SQLite thư viện chuẩn, không thêm SQLAlchemy.
4. Xác nhận: cookie phiên thay vì JWT.
5. Nói rõ nếu muốn tôi làm hết một mạch hay dừng ở từng chốt.

# Modular Refactor — 2026-09-12

Tách `app/main.py` (298 dòng, gộp backend + HTML + CSS + JS) thành 14 file nhỏ,
mỗi file một nhiệm vụ. Chức năng giữ nguyên, đã test chạy thật trước và sau.

---

## 1. Bản đồ file — sửa gì thì vào đâu

| File | Chịu trách nhiệm |
|---|---|
| `app/config.py` | **Mọi hằng số**: đường dẫn, tên model, tham số LLM, port |
| `app/main.py` | Điểm khởi chạy: tạo FastAPI, gắn static + routes, nạp sẵn model |
| `app/api/routes.py` | Hai endpoint: `GET /` và `POST /chat` |
| `app/api/schemas.py` | Kiểu dữ liệu request (`Query`) |
| `app/core/anchors.py` | 3 danh sách câu mẫu — **dữ liệu thuần, không có code** |
| `app/core/router.py` | Semantic Router (cosine similarity) |
| `app/core/embeddings.py` | Nạp SBERT, chọn device, phép toán vector |
| `app/core/vectorstore.py` | Truy vấn ChromaDB (RAG) |
| `app/core/websearch.py` | Cổng DuckDuckGo |
| `app/core/llm.py` | Cổng Ollama (stream) |
| `app/core/pipeline.py` | Ráp luồng: intent → bằng chứng → prompt |
| `app/prompts/templates.py` | Toàn bộ text prompt (giữ nguyên từng chữ) |
| `app/templates/index.html` | Khung giao diện |
| `app/static/css/styles.css`, `app/static/js/app.js` | Giao diện & logic front-end |

**Tra nhanh:**
- Đổi model / port → `config.py`
- Đổi văn phong AI → `prompts/templates.py`
- Router bắt sai luồng → `core/anchors.py`
- Đổi giao diện → `static/` + `templates/`

---

## 2. Kiểm thử đã chạy

Chạy bản gốc trước để lấy mốc so sánh, rồi chạy bản mới. Cả hai đều phục vụ `/`
và stream `/chat`.

Bản mới, cả 3 luồng đều đúng:

| Câu hỏi | Intent | Score |
|---|---|---|
| "Thủ tục đăng ký kết hôn cần giấy tờ gì?" | LUAT | 0.51 |
| "xin chào bạn" | XAGIAO | 0.70 |
| "vượt đèn đỏ phạt bao nhiêu tiền" | NGOAI | 0.58 |

Static assets (`/static/css/styles.css`, `/static/js/app.js`) đều trả 200.

---

## 3. Bốn lỗi đã sửa kèm theo

Đều là lỗi thật, không phải dọn dẹp cho đẹp:

1. **Đường dẫn tương đối** — `../data/chromadb` bắt buộc phải `cd app` mới chạy được.
   Giờ resolve tuyệt đối từ `__file__`, chạy ở thư mục nào cũng được.
2. **`"\\n\\n".join(...)`** — chèn ký tự `\n\n` dạng chữ vào giữa các tài liệu RAG
   thay vì xuống dòng thật, làm bẩn prompt gửi cho LLM.
3. **Encode thừa** — mỗi câu hỏi pháp lý gọi `embed_model.encode()` hai lần, kết quả
   lần một bị vứt đi.
4. **`innerHTML` ở front-end** — câu hỏi chứa HTML sẽ được render thành markup.
   Đã chuyển sang `textContent` + DOM API.

Ngoài ra đổi `@app.on_event("startup")` (đã deprecated) sang lifespan handler.

### Một lỗi tự gây ra khi refactor, đã bắt được

Lúc tách `vectorstore.py`, tôi viết `list(query_embedding)` thay cho `.tolist()`.
Kết quả là list chứa `np.float32` chứ không phải `float` thuần → ChromaDB từ chối,
luồng LUAT trả `X-Intent: ERROR`. Smoke test bắt được ngay. Đã sửa thành
`np.asarray(query_embedding).tolist()`.

**Bài học:** đừng đổi cách convert numpy → Python list khi refactor.

---

## 4. Cần biết về môi trường

- **Có hai virtualenv.** `.venv` có đủ thư viện và là cái đang dùng được.
  Thư mục `venv` (cái README bảo tạo) đang **rỗng**. Chưa xoá cái nào.
- Ollama đã có sẵn model `qwen2.5:1.5b`.
- `data/chromadb/` đã build sẵn, không cần chạy lại `ingest.py`.
- `test_llm.py` và `test_route.py` là script rời, không import gì từ app — **không đụng tới**.

---

## 5. Cách chạy

Từ thư mục gốc project:

```
.venv\Scripts\python.exe app\main.py
```

Rồi mở `http://localhost:8000`.

### Lưu ý khi nhờ Claude chạy hộ

Server do Claude khởi động **không truy cập được từ trình duyệt của bạn**, vì:

1. Bash tool của Claude chạy trong sandbox — cổng mạng có thể bị giới hạn trong đó,
   `127.0.0.1` của Claude không chắc là `127.0.0.1` của bạn.
2. Tiến trình nền của Claude chết theo tool call / phiên làm việc.
3. Panel chat VSCode chặn điều hướng tới URL không nằm trong allowlist.

**Cách làm đúng:** Claude tự kiểm tra bằng `curl` trong shell của nó, rồi đưa bạn
một dòng lệnh để bạn tự chạy ở terminal của mình — tiến trình thuộc về bạn nên
nó sống lâu hơn phiên của Claude.

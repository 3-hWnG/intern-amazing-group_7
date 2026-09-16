# LLM giải đáp thủ tục hành chính

Trợ lý chạy **local** giúp người dân hỏi về thủ tục hành chính (khai sinh, kết
hôn, thường trú, tạm trú, căn cước, hộ chiếu, đăng ký kinh doanh, đất đai, BHXH,
thuế…). Mô hình nhẹ (3–4B lượng tử hoá; 1.5B để thử nhanh) lo **hiểu và diễn
đạt**; thông tin luôn **tra cứu realtime qua MCP**; câu trả lời được **kiểm chứng**
với nguồn trước khi gửi.

```
HTML/JS UI ─> FastAPI ─> Hàng đợi tuần tự ─> ORCHESTRATOR
                                               │
     ngữ cảnh ─> HIỂU ý định + BỘ GÁC ─┬─> hỏi lại (thiếu thông tin)
                                       └─> MCP search ─> Evidence Pack ─> SOẠN ─> KIỂM CHỨNG ─> PASS / sửa lại
                                                                                  │
                                         SQLite: người dùng · lịch sử · tóm tắt · Evidence Pack · phản hồi
```

Chi tiết kiến trúc, sơ đồ, cách tinh chỉnh từng thành phần: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
Lượng tử hoá + fine-tune: [`finetune/README.md`](finetune/README.md)

## Đáp ứng yêu cầu

| Yêu cầu | Ở đâu |
|---|---|
| Mô hình nhẹ, chạy local, 3–4B | Ollama, `LLM_MODEL` (1.5B để thử, 3B để triển khai) |
| Lượng tử hoá, fine-tune | `finetune/`: QLoRA → GGUF Q4_K_M → Ollama; benchmark FP16 vs 4-bit |
| MCP cập nhật realtime | `app/mcp_search/server.py` (MCP server) + `app/core/mcp_client.py` |
| Search engine cho Evidence Pack | `app/mcp_search/engine.py` — ưu tiên .gov.vn, đọc toàn văn, chọn đoạn |
| Không nói dối theo kiến thức chung | trả lời CHỈ từ Evidence Pack; không tra được thì nói thật |
| Model kiểm tra lại mới trả lời | `app/core/verifier.py` — luật + LLM, FAIL thì tra bổ sung / viết lại |
| Dùng intent, không keyword; AI làm rõ prompt, hỏi lại khi không rõ | `app/core/intent.py` — LLM hiểu ý định + LLM gác hỏi lại, JSON schema |
| Nhớ ngữ cảnh, 1 phiên mỗi người, lần sau vẫn nhớ | lịch sử theo tài khoản + `user_profile` (tỉnh/xã) xuyên hội thoại |
| Ngữ cảnh quá dài thì AI tóm tắt | `app/core/summarizer.py` (`MAX_CONTEXT_TOKENS`) |
| Đăng nhập định danh | `app/core/auth.py` (bcrypt + cookie phiên) |
| Xử lý tuần tự | `app/core/queue.py` (`QUEUE_CONCURRENCY=1`) |
| Backend API + Docker + biến môi trường | `app/api/`, `Dockerfile`, `docker-compose.yml`, `.env.example` |
| HTML demo, chứng minh RAG, lịch sử như ChatGPT | thanh bên lịch sử; nguồn + **Evidence Pack** dưới mỗi câu trả lời |
| Phản hồi Phù hợp / Không phù hợp | nút 👍/👎; không chấm = trung bình; thống kê ở bảng Dev |
| So sánh thời gian fine-tune với thời gian cập nhật | `finetune/runs.jsonl` ↔ ngày đăng nguồn, hiển thị trong Evidence Pack |

## Chạy local (Windows)

```powershell
# 1. Ollama: https://ollama.com rồi tải mô hình
ollama pull qwen2.5:1.5b          # thử nhanh
# ollama pull qwen2.5:3b          # triển khai — đặt LLM_MODEL=qwen2.5:3b trong .env

# 2. Chạy (lần đầu: -Install tạo .venv + cài thư viện, tự tạo .env từ .env.example)
.\run.ps1 -Install
.\run.ps1                          # các lần sau
```

Mở http://127.0.0.1:8000 → đăng ký tài khoản → hỏi. MCP search server được app
tự bật (stdio), không cần chạy riêng.

## Chạy bằng Docker

```powershell
copy .env.example .env
docker compose up --build                                                   # CPU
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build   # GPU NVIDIA
```

Bốn dịch vụ: `ollama` · `ollama-pull` (tải mô hình rồi thoát) · `mcp-search`
(MCP Streamable HTTP, cổng 8765) · `app` (API + hàng đợi + UI, cổng 8000).
Dùng Ollama có sẵn trên máy: `OLLAMA_HOST_DOCKER=http://host.docker.internal:11434`
rồi `docker compose up --build --no-deps app mcp-search`.

## Đánh giá

```powershell
.\run.ps1 -EvalIntent      # nhanh: độ chính xác ý định + hỏi lại (không tra web)
.\run.ps1 -Eval            # cả pipeline: nguồn chính thống, trích dẫn, PASS, độ trễ
.\run.ps1 -Bench           # token/s, VRAM, dung lượng của mô hình
```

Bộ câu hỏi tự soạn: `Evaluation/eval_set.jsonl`. Kết quả: `Evaluation/results/`.

### Số đo gần nhất (16/09/2026 · RTX 4050 6GB · tìm kiếm ddgs)

| Chỉ số | qwen2.5:1.5b | qwen2.5:3b |
|---|---|---|
| Độ chính xác ý định | 84.4% (45 câu) | 80.0% (20 câu đầu) |
| Hỏi lại / trò chuyện / từ chối đúng luồng | 100% (42/42) | 100% |
| Token/s · VRAM · dung lượng (Q4_K_M) | 144 · 1.36 GB · 0.99 GB | 81 · 2.40 GB · 1.93 GB |
| Một lượt có tra cứu (tổng) | ~11–20 giây | ~30–35 giây |

Lưu ý khi báo cáo: bộ câu hỏi này cũng được dùng lúc tinh chỉnh prompt, nên hai
dòng đầu là "đo trên chính bộ đã tinh chỉnh" — soạn thêm câu mới để đo khách quan.
Mô hình 3B viết trích dẫn `[S#]` tốt hơn 1.5B nhưng hay chèn nhãn tự đặt trong
ngoặc vuông; bộ kiểm chứng bắt và lược bỏ những chỗ đó.

## Cấu trúc

```text
app/
├── main.py                  khởi động: CSDL, Ollama, MCP, hàng đợi
├── config.py                mọi cấu hình, đọc từ biến môi trường / .env
├── api/                     auth · chat (NDJSON) · files · dev · health
├── core/
│   ├── orchestrator.py      pipeline 6 bước
│   ├── intent.py            hiểu ý định + hỏi lại + bộ nhớ tỉnh/xã
│   ├── evidence.py          gọi MCP -> Evidence Pack (+ tệp đính kèm)
│   ├── answer.py            soạn câu trả lời
│   ├── verifier.py          kiểm chứng (luật + LLM)
│   ├── summarizer.py        tóm tắt khi ngữ cảnh dài
│   ├── llm.py               cổng Ollama, tham số theo vai
│   ├── mcp_client.py        phiên MCP lâu dài (stdio / http)
│   ├── queue.py · auth.py · parsers.py · resources.py · chunk_index.py
├── mcp_search/
│   ├── server.py            MCP server: search_evidence · web_search · fetch_page
│   └── engine.py            tìm kiếm -> xếp hạng -> đọc trang -> chọn đoạn
├── prompts/templates.py     TẤT CẢ prompt
├── db/                      schema.sql · connection.py · repositories.py (mọi SQL)
├── static/ · templates/     giao diện HTML/CSS/JS
Evaluation/                  eval_set.jsonl · evaluate.py
finetune/                    export_dataset · train_qlora · merge_and_export · benchmark_quant
docs/ARCHITECTURE.md
```

Muốn sửa gì vào đúng chỗ đó: đổi mô hình/tham số → `.env`; đổi cách trả lời → `app/prompts/templates.py`;
đổi cách xếp hạng nguồn → `app/mcp_search/engine.py`; đổi giao diện → `app/static/`.

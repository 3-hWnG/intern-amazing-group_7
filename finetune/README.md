# Lượng tử hoá + fine-tune

## Fine-tune ở dự án này là gì — và KHÔNG là gì

```
TRỌNG SỐ MÔ HÌNH (fine-tune được)        TRA CỨU QUA MCP (cập nhật tức thì)
├── hiểu ý định người dân nói            ├── thủ tục hiện hành
├── biết lúc nào phải hỏi lại            ├── thành phần hồ sơ
├── bám bằng chứng, trích dẫn [S#]       ├── lệ phí, thời hạn
├── trả lời đúng trọng tâm, hỏi xoáy     ├── nơi nộp
└── văn phong                            └── văn bản mới thay thế văn bản cũ
```

Fine-tune dạy **hành vi** (dạng in → out đơn giản), không nhồi kiến thức thủ tục.
Kiến thức thay đổi liên tục; nhồi vào trọng số thì sai ngay khi có văn bản mới.

## So sánh thời gian cập nhật

| Cách cập nhật | Việc phải làm | Thời gian |
|---|---|---|
| Nguồn trên mạng đổi | Không làm gì — MCP tra lại ở câu hỏi sau | tức thì (tối đa `SEARCH_CACHE_SECONDS`, mặc định 30 phút) |
| Đổi hành vi mô hình | thu phản hồi → export → QLoRA → gộp → GGUF → lượng tử → `ollama create` | đo thật bằng `runs.jsonl` (`duration_seconds`) + thời gian export/convert |

`train_qlora.py` ghi `started_at / finished_at / duration_seconds` vào `runs.jsonl`.
Ứng dụng đọc file này: `/health` và bảng **Evidence Pack** hiển thị *mô hình
fine-tune lúc nào, kiến thức tới khi nào* đặt cạnh *ngày đăng của nguồn* — nhìn
là biết thông tin nào mới hơn.

## Quy trình

```
dùng app thật ──> 👍 Phù hợp ──> export_dataset.py ──> train_qlora.py ──> merge_and_export.py
                                   (data/train.jsonl)   (adapter + runs.jsonl)  (GGUF f16 + Q4_K_M + Ollama)
                                                                                         │
                          Evaluation/evaluate.py  <── benchmark_quant.py  <──────────────┘
                          (so chất lượng gốc vs FT)   (so FP16 vs 4-bit)
```

```powershell
# 0. cài thư viện fine-tune (torch CUDA cài trước theo pytorch.org)
.venv\Scripts\python.exe -m pip install -r finetune\requirements-finetune.txt

# 1. dữ liệu từ hội thoại thật được chấm Phù hợp
.venv\Scripts\python.exe finetune\export_dataset.py

# 2. QLoRA (4-bit NF4, LoRA r=16 trên attention + MLP, loss chỉ trên phần trả lời)
.venv\Scripts\python.exe finetune\train_qlora.py --base Qwen/Qwen2.5-3B-Instruct --ollama-model tthc-qwen2.5-3b

# 3. gộp adapter -> GGUF FP16 -> Q4_K_M -> tạo 2 mô hình Ollama (tthc-qwen2.5-3b-f16, tthc-qwen2.5-3b)
.venv\Scripts\python.exe finetune\merge_and_export.py --base Qwen/Qwen2.5-3B-Instruct `
    --adapter finetune\output\<run>\adapter --llama-cpp D:\tools\llama.cpp --name tthc-qwen2.5-3b

# 4. lượng tử hoá: FP16 vs 4-bit — dung lượng, VRAM, RAM, token/s, TTFT, độ trễ
.venv\Scripts\python.exe finetune\benchmark_quant.py --models tthc-qwen2.5-3b-f16 tthc-qwen2.5-3b

# 5. chất lượng: gốc vs fine-tune (đổi LLM_MODEL giữa hai lần chạy).
#    Dữ liệu huấn luyện không kèm ví dụ mẫu -> mô hình fine-tune chạy với UNDERSTAND_FEWSHOT=false
$env:LLM_MODEL="qwen2.5:3b";      .venv\Scripts\python.exe Evaluation\evaluate.py
$env:LLM_MODEL="tthc-qwen2.5-3b"; .venv\Scripts\python.exe Evaluation\evaluate.py
```

Không muốn fine-tune mà vẫn cần so sánh lượng tử hoá: Ollama có sẵn các bản
`qwen2.5:3b-instruct-fp16` và `qwen2.5:3b-instruct-q4_K_M` — pull cả hai rồi chạy bước 4.

## Bảng so sánh cần nộp

| Chỉ số | Gốc | Fine-tune | Nguồn số liệu |
|---|---|---|---|
| Intent accuracy | | | `evaluate.py` |
| Clarification accuracy | | | `evaluate.py` |
| Có trích dẫn / nguồn chính thống | | | `evaluate.py` |
| Verifier PASS | | | `evaluate.py` |
| Token/s, VRAM, dung lượng | | | `benchmark_quant.py` |
| Thời gian fine-tune | — | | `runs.jsonl` |

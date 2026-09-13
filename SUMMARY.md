# Nhóm 7 — LLM Thủ tục hành chính · Tổng kết tái cấu trúc
**11–13/09/2026**

## Kết quả một dòng

> **Recall@1 tăng từ 53% lên 86%. Không đổi mô hình nào.**
> Độ trễ truy hồi 236 ms (p95 328 ms), trong ngân sách 15 giây.

| | v0 (demo cũ) | **v4 (hiện tại)** |
|---|---|---|
| Recall@1 | 0.5272 | **0.8556** |
| Recall@5 | 0.8037 | **0.9753** |
| MRR@10 | 0.6400 | **0.9061** |
| Câu gõ không dấu (R@1) | 0.056 | **0.611** |
| Tầng A trả lời sai | — | **3.6%** |
| Câu ngoài phạm vi → tra web | — | **92%** |
| Đo lường | *không có gì* | 862 câu có nhãn |

## Vì sao demo cũ hỏng

Khi hỏi "Tôi muốn làm giấy khai sinh", demo xin lỗi và đẩy người dân sang Công an
— dù khai sinh nằm ở **dòng 2** của dataset.

Đo được: `khai_sinh` có **R@1 = 0.00**, và dòng đó **chưa bao giờ** được xếp hạng 1
trong cả 862 câu hỏi. **Không phải prompt từ chối — mà truy hồi không tìm ra.**
Chẩn đoán ban đầu (đổ lỗi cho prompt) đã sai; số liệu chỉ ra chỗ khác.

Ba nguyên nhân gốc:
1. `vietnamese-sbert` giới hạn **256 token**; 27% tài liệu bị cắt, 23% có lệ phí
   và thời gian nằm ngoài cửa sổ nhúng — không bao giờ được đánh chỉ mục.
2. Tên thủ tục bị phần "thành phần hồ sơ" nhấn chìm trong cùng một vector.
3. Router centroid: trung bình 53 câu mẫu tạo ra vector "ngôn ngữ hành chính
   chung chung". Lớp càng nhiều câu mẫu càng bị pha loãng — **thêm câu mẫu làm
   router yếu đi**, ngược với điều nhóm tin.

## Điều gì thực sự tạo ra mức tăng

| Thay đổi | R@1 | Ghi chú |
|---|---|---|
| v0 gốc | 0.527 | |
| BM25 bỏ dấu + đa view + cosine | 0.746 | **+0.22, không đổi mô hình** |
| Sửa trọng số hoà + luật hỏi lại | 0.777 | |
| Reranker (GPU) | 0.836 | |
| Sửa hiệu chỉnh reranker | **0.856** | |
| ~~Đổi mô hình nhúng~~ | 0.849 | **hoàn nguyên — không cải thiện** |

Điều đáng chú ý nhất: **BM25 thuần (30 dòng Python, không mô hình) đạt R@1 0.72
một mình**, cao hơn toàn bộ hệ thống neural cũ. Phần lớn "hiểu ngữ nghĩa kém"
thực chất là **thiếu khớp từ khoá**, không phải thiếu ngữ nghĩa.

## Sự cố hạ tầng phát hiện

`.venv` cài **torch CPU-only** → `torch.cuda.is_available()` luôn `False`.
RTX 4050 **chưa từng được dùng** — kể cả trong demo. Đoạn "Ép xung Phần cứng,
nhanh gấp 10–20 lần" trong `log code main.md` chưa bao giờ chạy.
Sau khi cài `torch==2.14.0+cu130`: reranker từ **6214 ms** xuống **240 ms/câu**.

## Kiến trúc hiện tại

```
câu hỏi
  └─ xã giao?  ──yes──► trả lời ngắn (không tra DB)
  └─ đang chờ làm rõ? ──► ghép với câu hỏi gốc
  └─ truy hồi:  BM25 (bỏ dấu) + dense (đa view) ──RRF có trọng số──►
                cross-encoder xếp hạng lại ──► độ tin cậy (dense+BM25)
       ├─ ≥ 0.75 ──► TẦNG A  in thẳng bản ghi, KHÔNG qua LLM (không thể bịa)
       ├─ ≥ 0.65 ──► TẦNG B  hỏi lại cho rõ
       └─ < 0.65 ──► tra nguồn chính thống (allowlist)
                       ├─ có ──► TẦNG C  + ghi rõ nguồn, chưa đối chiếu
                       └─ không ──► TẦNG D  kiến thức chung, ghi rõ KHÔNG chắc
  └─ kiểm chứng bằng luật (số tiền / số ngày phải có trong nguồn)
  └─ trả lời + nhãn độ tin cậy + 👍/👎
```

### Cấu trúc mã (mô-đun hoá)
```
domain/records.py   ← NƠI DUY NHẤT biết cấu trúc dataset. Thêm cột → sửa ở đây.
domain/text.py      fold (bỏ dấu), tokenize, trích số tiền/số ngày
core/lexical.py     BM25 trên chuỗi đã bỏ dấu
core/retrieval.py   hoà dense + BM25 (RRF có trọng số) + gọi reranker
core/reranker.py    cross-encoder, tự tắt nếu không nạp được
core/tiers.py       toàn bộ logic phân tầng A/B/C/D
core/factcheck.py   luật kiểm chứng — THÊM LUẬT: viết hàm, thêm vào RULES
core/formatter.py   dựng câu trả lời tầng A (không LLM)
core/session.py     bộ nhớ hội thoại + trạng thái "đang chờ làm rõ"
core/smalltalk.py   thay router centroid cũ
core/websearch.py   chỉ nhận nguồn .gov.vn trong allowlist
core/pipeline.py    CHỈ điều phối, không chứa logic riêng
config.py           mọi hằng số + cờ bật/tắt từng tầng
```

## Cách chạy
```powershell
.\run.ps1              # kiểm tra môi trường + chấm điểm
.\run.ps1 -Ingest      # nạp lại DB (sau khi đổi dataset/mô hình) rồi chấm điểm
.\run.ps1 -Serve       # chạy web server
.\run.ps1 -Limit 30    # chấm thử nhanh
```
Dùng `.venv` (KHÔNG phải `venv` — thư mục đó rỗng, README cũ chỉ sai).

## Bài học lặp lại 3 lần
**Đổi công thức độ tin cậy thì PHẢI hiệu chỉnh lại ngưỡng.** Đã mắc lỗi này ba
lần trong 2 ngày. Nên để ngưỡng sinh tự động từ file hiệu chỉnh thay vì gõ tay
trong `config.py`.

## Việc còn lại
| Việc | Trạng thái |
|---|---|
| Xác thực (auth) | **chưa** — nhóm xác nhận là bắt buộc |
| Hàng đợi (queue) | **chưa** — nhóm xác nhận là bắt buộc |
| Đổi LLM sang qwen2.5:3b | chưa đo |
| Bộ nhớ hội thoại | đã viết, chưa đo |
| Kiểm chứng bằng luật | đã viết, chưa đo |
| Dọn dataset (mã thủ tục, cấp thực hiện, gộp dòng trùng) | chưa |
| Hộ tịch R@1 0.667 | **yếu nhất** — mà đây là nhóm thủ tục dân hỏi nhiều nhất |

## Câu hỏi chưa chốt với mentor
1. Công ty chưa bao giờ yêu cầu RAG; mentor nói dataset để **fine-tune**.
   Đề xuất dung hoà: fine-tune cho **văn phong/hành vi**, tra bảng cho **con số**.
2. 862 câu đã gắn nhãn dùng được cho cả hai hướng — không phí công dù chọn hướng nào.
3. Dataset vẫn thiếu `mã thủ tục` và `cấp thực hiện`; còn 4 cặp dòng trùng
   (8/21, 10/13, 9/14, 23/25).

## Mốc đo đã lưu
`Evaluation/baselines/` — v0, v1, v3, v4, v5(hoàn nguyên), mỗi mốc kèm
`eval_results.csv` đầy đủ 862 dòng để so sánh về sau.

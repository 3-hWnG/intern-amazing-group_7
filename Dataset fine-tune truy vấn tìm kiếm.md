# Task: Dataset fine-tune mô hình tạo truy vấn tìm kiếm

**Người phụ trách:** Hưng · **Nhánh code:** `Reimage-V10.1` · **Thư mục:** `D:\reimagine_V10.1`
**Cập nhật:** 17/09/2026

---

## 0. Mục tiêu

Mô hình 1.5B đang tạo truy vấn web search kém: lệch thủ tục, mất dấu, mất khía cạnh được hỏi.
Mục tiêu là tạo một dataset nhỏ (khoảng 300–500 cặp) **câu hỏi người dân → truy vấn tìm kiếm đúng**
để fine-tune một mô hình tạo truy vấn riêng (cách 2):

```
Câu hỏi → [mô hình tạo truy vấn 1.5B đã fine-tune] → web search → [1.5B thường] → trả lời
```

Nguyên tắc đã thống nhất:
- Đo **baseline trước** (gồm cả cách 4: đưa thẳng câu hỏi gốc đi tìm) rồi mới fine-tune.
- **Tách train/test theo thủ tục (`topic_key`)** để tránh rò rỉ dữ liệu.
- **Nhãn phải được kiểm chứng bằng tra web thật** (ra đúng trang thủ tục thì mới giữ).
- Trộn khoảng 70% câu lỗi + 30% câu đang tốt; 1–2 epoch, LoRA rank thấp.
- Giữ riêng một nhóm câu **mới hoàn toàn** để kiểm tra cuối.

---

## 1. Tiến độ

| # | Bước | Trạng thái |
|---|---|---|
| 1 | Tìm bộ câu hỏi đánh giá | ✅ Xong |
| 2 | Sinh truy vấn baseline (few-shot TẮT) | ✅ Xong |
| 3 | Sinh truy vấn baseline (few-shot BẬT) | ✅ Xong |
| 4 | Chấm sơ bộ bằng luật (không tra web) | ✅ Xong |
| 5 | **Tra web thật: mô hình vs câu hỏi gốc vs gộp** | ⏳ **Đang làm (chờ Hưng chạy)** |
| 6 | Tách train/test theo thủ tục + chọn câu ứng viên | ⬜ Chưa làm |
| 7 | Sinh nhãn bằng mô hình lớn + lọc bằng tra web | ⬜ Chưa làm |
| 8 | Soạn bộ test mới hoàn toàn (hold-out) | ⬜ Chưa làm |
| 9 | Fine-tune QLoRA (`finetune/`) | ⬜ Chưa làm |
| 10 | Lượng tử hoá Q4_K_M + đo lại | ⬜ Chưa làm |
| 11 | Ghép vào hệ thống (`QUERY_MODEL`) + so sánh cuối | ⬜ Chưa làm |

---

## 2. Đã làm

### Bước 1 — Bộ câu hỏi
- `Evaluation/eval_questions.csv` gồm **862 câu, 55 thủ tục**, khôi phục từ lịch sử git (bị xoá ở commit V10).
  Sinh bởi `build_eval_set.py` từ `data/data_merged.xlsx`.
- Kiểu câu (`variant`): `facet_*` (dễ, chứa nguyên tên thủ tục), `situational`, `colloquial`,
  `abbrev`, `no_diacritics`, `typo`, `keyword` (khó), `out_of_scope` (52 câu).
- `eval_results.csv` là kết quả truy hồi của hệ RAG cũ, **không có search query**.

### Bước 2–3 — Truy vấn baseline (`gen_queries_baseline.py`)
- `results/queries_baseline_1.5b_fewshot_off.csv`
- `results/queries_baseline_1.5b_fewshot_on.csv`
- Lưu ý: `.env` đang để `UNDERSTAND_FEWSHOT=false` nên lượt đầu tiên thực chất là few-shot TẮT.
  Script giờ có `--fewshot on|off` và in trạng thái ở dòng đầu.

### Bước 4 — Chấm sơ bộ (`analyze_queries.py --sent`, luật từ khoá)

| | Few-shot TẮT | Few-shot BẬT |
|---|---|---|
| Truy vấn đến từ | mô hình sinh | ~97% là câu viết lại + năm |
| Có lỗi (tổng) | 49,6% | 39,3% |
| Lệch thủ tục | 31,1% | 25,3% |
| Mất khía cạnh được hỏi | 37,0% | 30,8% |
| Mất dấu | 19,6% | 0,1% |
| Đi tra cứu / hỏi lại | 93,2% / 5,7% | 84,4% / 12,7% |

Kết luận tạm:
- Ô `search_queries` do mô hình sinh là phần tệ nhất; câu viết lại tốt hơn.
- Few-shot BẬT làm tỉ lệ hỏi lại tăng gấp đôi và kéo nhiều câu về "đăng ký kinh doanh".
- Hai lượt sai ở những câu khác nhau (chỉ 218 câu lỗi ở cả hai), nên gộp nhiều nguồn truy vấn có thể bù cho nhau.
- Điểm yếu chung, cần ưu tiên trong dataset: `no_diacritics` (~81% lỗi) và `facet_place` (~80%, mất "nộp ở đâu").
- Danh sách intent thiếu nhóm (trợ cấp, con dấu, vũ khí…), nên "intent accuracy" chưa có ý nghĩa.

---

## 3. Đang làm — Bước 5: tra web thật

Script `search_baseline.py` lấy 154 câu (14 câu × 11 kiểu) và chấm top-5 theo 3 cấu hình:
**A** truy vấn mô hình · **B** câu hỏi gốc (cách 4) · **C** gộp A + B.
Kết quả tra được lưu cache trong `results/search_cache.json`; dừng giữa chừng thì chạy lại sẽ tiếp tục.

```powershell
# thử nhanh
.venv\Scripts\python.exe Evaluation\search_baseline.py --n 22
# chạy đủ, mỗi lệnh ~40–50 phút
.venv\Scripts\python.exe Evaluation\search_baseline.py
.venv\Scripts\python.exe Evaluation\search_baseline.py --input Evaluation\results\queries_baseline_1.5b_fewshot_on.csv
```

- [ ] Chạy thử `--n 22` (kiểm tra ddgs có chặn không; nếu chặn nhiều thì thêm `--delay 3`)
- [ ] Chạy đủ với few-shot TẮT
- [ ] Chạy đủ với few-shot BẬT
- [ ] Gửi 2 file `results/search_baseline_*.md` (+ `.csv`) để phân tích
- [ ] Đọc lướt cột `top_titles` vài chục dòng để chắc luật chấm không sai nhiều

**Quyết định sau bước này:** nếu B hoặc C đã tốt hơn A rất nhiều, ghi vào báo cáo và cân nhắc áp
dụng cách 4 ngay. Fine-tune chỉ làm tiếp nếu vẫn còn khoảng cách đáng kể.

---

## 4. Sẽ làm

### Bước 6 — Tách tập + chọn ứng viên
- Chia 55 `topic_key` thành train (~40) / test (~15), cố định seed, lưu danh sách chủ đề.
- Ứng viên train = câu lỗi (bước 4–5) thuộc chủ đề train + khoảng 30% câu đang tốt.
- Ưu tiên `no_diacritics`, `facet_place`, `abbrev`, `colloquial`, `situational`.

### Bước 7 — Sinh nhãn + lọc
- Mô hình lớn sinh 2–3 phương án truy vấn cho mỗi câu. Yêu cầu: có dấu, giữ tên thủ tục,
  giữ khía cạnh được hỏi, giữ tỉnh/trường hợp đặc biệt; không tự thêm số văn bản hoặc năm.
- Tra thử từng phương án; chỉ giữ phương án ra đúng trang thủ tục trong top-5.
- Thêm biến thể câu hỏi (có dấu / không dấu / viết tắt) dùng chung một nhãn.
- Xuất JSONL: `{"question": ..., "queries": [...]}`.

### Bước 8 — Bộ test mới
- Soạn vài chục câu mới hoàn toàn (nhiều teen code / không dấu), chưa từng dùng để chỉnh prompt.

### Bước 9–10 — Fine-tune
- Mô hình gốc: `qwen2.5:1.5b` instruct (không train chồng lên các bản fine-tune cũ).
- LoRA r = 8–16, learning rate 1e-4 đến 2e-4, 1–2 epoch; đo tỉ lệ ra trang đúng sau mỗi epoch và giữ checkpoint tốt nhất.
- Chat template lúc train phải khớp Modelfile của Ollama; chạy với temperature 0.
- Lượng tử hoá Q4_K_M rồi **đo lại** (mô hình 1.5B mất độ chính xác rõ hơn mô hình lớn).

### Bước 11 — Ghép + so sánh cuối
- Thêm `QUERY_MODEL` vào `.env`; mô hình này lỗi thì quay về truy vấn cũ.
- So sánh trên tập test và bộ câu mới: truy vấn cũ · mô hình mới · mô hình mới + câu gốc song song.
- Báo cáo tỉ lệ ra trang đúng và độ trễ.

---

## 5. File liên quan

| File | Vai trò |
|---|---|
| `Evaluation/eval_questions.csv` | 862 câu có nhãn chủ đề |
| `Evaluation/gen_queries_baseline.py` | sinh truy vấn baseline (`--fewshot on\|off`, chạy tiếp được) |
| `Evaluation/analyze_queries.py` | chấm sơ bộ bằng luật (`--sent`, `--examples`) |
| `Evaluation/search_baseline.py` | tra web thật, so sánh A/B/C |
| `Evaluation/results/` | kết quả (bị `.gitignore` bỏ qua) |
| `finetune/` | pipeline QLoRA → GGUF → Ollama có sẵn |

## 6. Câu hỏi còn mở
- Deadline của task fine-tune? Không kịp thì dùng cách 4 thay thế.
- Mô hình lớn nào dùng để sinh nhãn (ChatGPT hay Claude), và ai chạy bước đó?
- Có merge V10.1 vào V11 không? Các script ở đây đang bám theo code V10.1.

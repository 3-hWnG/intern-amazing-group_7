# Tiêu chí chấm System 3 và System 4 (bộ evaluation thống nhất)

Tài liệu này gộp hai bộ đánh giá của nhóm: bộ trên branch `merge_sys_3_4` (công cụ chạy trên code hiện tại) và khung 4 tầng A–D của branch `draft` (`05_methodology/bo_evaluation_hoan_thien_v2.md`, bản đầy đủ vẫn nằm trên branch đó). Số liệu dưới đây đều đo lại trên code hiện tại (2026-10-14), trừ chỗ ghi rõ. Kế hoạch gộp và các quyết định nằm ở `docs/KE_HOACH_GIAI_QUYET_MERGE_PLAN.md`.

Quy tắc giữ số đo trung thực ở [../docs/EVAL.md](../docs/EVAL.md) (không tune trên bộ mù) vẫn áp dụng.

## 0. Quy tắc đọc số

1. **Bộ mù mới là số khoe.** Bộ `dev` đã tune nên luôn cao hơn: hành vi đúng 98% (dev) so với 78% (blind). Mọi bảng báo cả hai, nhưng kết luận chỉ dựa vào blind.
2. **Mỗi tỷ lệ có khoảng tin cậy Wilson 95%.** Bộ nhỏ (HOLDOUT-4 có 77 ca có đáp án) dao động vài điểm phần trăm; một ca đổi khoảng 1,3%.
3. **Mỗi con số ghi nguồn:** `máy` (luật hoặc truy vấn DB), `LLM` (giám khảo hoặc người chấm là một LLM) hoặc `người`. Hiện chưa có con số nào do người chấm.
4. **Ngưỡng là mục tiêu của nhóm, không phải chuẩn của văn liệu**, trừ chỗ ghi rõ bài báo. Đừng trình bày ngưỡng như tiêu chuẩn.
5. **Không đưa vào báo cáo:** điểm RAGAS (xem mục B), "bộ mù" hoặc "chuyên gia rà" cho các bộ sinh tự động, và số đo trên code cũ như thể là của code hiện tại.

## 1. Bộ test

| Bộ | Quy mô | Ghi chú |
|---|---|---|
| Golden set Thủ tục (`eval/golden/thu-tuc.jsonl`, dựng bằng `build_golden.py`, chấm bằng `run_golden.py`) | 1.352 ca: `dev` 641, `holdout-used` 158, `blind` 553 | Gom mọi bộ có sẵn về một định dạng. `tro-chuyen-chung` (System 4 Friendly) rỗng: chưa có bộ có đáp án |
| Bộ khuôn (`golden/template_thu-tuc.jsonl`, `build_template_set.py`) | 430 ca, 12 chủ đề | Câu dùng nguyên tên thủ tục nên dễ hơn câu người thật; dùng để so chủ đề và bắt hồi quy |
| Real-log v1 (`cases_real_log_v1.json`, `REAL_LOG_v1.md`) | 29 lượt viết tay kiểu người dùng thật | Đã bị đọc lỗi (real-11, real-13) nên gắn `holdout-used`, không phải số mù |
| Bộ sinh đa lĩnh vực của branch `draft` | 2.168 ca | **Chưa dùng** (D1c): nhãn có lỗi (đáp án mẫu placeholder, holdout trùng thủ tục với dev, nhãn miễn phí sai). Danh sách lỗi ở `MERGE_PLAN.md` mục 2.5 |

Bộ mù chính thức: HOLDOUT-3/4, h5, h6, pseudo_real 1–3, bộ team (theo `docs/EVAL.md`). Bộ sinh tự động và bộ real-log đã đọc **không** được gọi là mù.

## 2. Bốn tầng tiêu chí

Mỗi hàng: đo gì, script, **số hiện tại**, mục tiêu của nhóm.

### Tầng A: truy xuất ("có tìm đúng thủ tục không?")
Chỉ chấm câu có thủ tục đáp án và `behavior=answer`. MRR và nDCG@5 tính trên danh sách ứng viên của task đầu (cùng danh sách với top-1; RR = 1 khi và chỉ khi top-1 đúng); ca nhiều thủ tục tính theo từng task kỳ vọng.

| Chỉ số | Script | Blind (n=406) | HOLDOUT-4 (n=77) | Mục tiêu nhóm (blind) |
|---|---|---|---|---|
| top-1 | `run_golden.py`, `run.py`, `run_pseudo.py` | 295/406, 73% (68–77%) | 60/77, 78% (67–86%) | ≥ 80% |
| top-3 | như trên | 323/406, 80% (75–83%) | 67/77, 87% (78–93%) | ≥ 90% |
| MRR | `run_golden.py` (`rank_metrics.py`) | 0,759 | 0,824 | ≥ 0,85 |
| nDCG@5 | như trên | 0,752 | 0,805 | theo dõi |
| ctx top-1 (hội thoại nhiều lượt) | `run_ctx.py` | ctx-dev + ctx-hold 88/91 | | ≥ 89/91 (đang trượt, từ commit `b7a7b9f`) |
| tổng quát hoá | `synth_retrieval.py` | TEST-seed (xem `docs/EVAL.md`) | | ≥ 94% |

Nguồn: `máy`. Khi sai, chủ yếu là chọn nhầm thủ tục anh em (hai thủ tục cùng họ), không phải xếp đúng thủ tục ở hạng hai; câu trả lời sai vẫn trích số liệu thật của thủ tục sai, nên đó là lỗi truy xuất, không phải bịa.

### Tầng B: chất lượng câu trả lời và chống bịa
| Chỉ số | Script | Số hiện tại | Mục tiêu nhóm |
|---|---|---|---|
| bịa số tiền/ngày/SĐT (không có trong nguồn) | `run.py` (luật, không LLM) | DEV cũ 0,5% (1/204) | ≤ 3% (nhóm đặt mục tiêu 0% cho số tiền) |
| số tiền/ngày/giờ trong câu trả lời có trong ngữ cảnh | `run_ragas_lite.py` (`numbers_ok`, luật) | 80/92 (87%) | theo dõi |
| đúng trọng tâm (hỏi giá thì chỉ trả giá), task thừa | `run_concise.py` | DEV 98,6%, task thừa 0/450 | ≥ 95%, ≤ 2% |
| chất lượng bước sinh chữ (đủ ý, đúng số, không đảo nghĩa) | `score_composer.py` | xem `docs/PLAN_TUAN_TOI.md` | |
| trích nguồn, nói "không công bố" đúng lúc | `run.py` | xem `docs/PLAN_TUAN_TOI.md` | |
| RAGAS (faithfulness, relevancy, context precision, context recall) | `run_ragas_lite.py`, `ragas_calib.py` | **không dùng được** (bên dưới) | |

**RAGAS: chưa đo đáng tin.** Hai giám khảo đã thử trên cùng phép đối chứng:

| Phép thử | qwen3:4b (n=30) | qwen2.5:7b (n=92) |
|---|---|---|
| Chèn một ý bịa ("miễn phí hoàn toàn, giải quyết trong 1 giờ"); faithfulness phải giảm | 9/30 (30%) | 47/92 (51%) |
| Ghép câu trả lời với câu hỏi của ca khác; relevancy phải giảm | giảm ở mọi ca | 74/76 (97%) |
| Câu trả lời đúng bị chấm relevancy 0 | 17/30 | 16/92 |
| κ faithfulness so với LLM chuẩn (30 ca) | chưa đo | **0,02** |
| κ relevancy so với LLM chuẩn (30 ca) | chưa đo | **0,20** |

Cả hai giám khảo bỏ sót nhiều ý bịa, và κ thấp hơn nhiều ngưỡng ~0,6. Điểm thô (7B: faithfulness 0,83, relevancy 0,78, precision 0,44, recall 0,90) **không đưa vào báo cáo như điểm chất lượng**. Context recall cao tự nhiên vì tham chiếu lấy từ chính DB. Các chỉ số luật ở trên thay thế cho RAGAS. Chi tiết và hạn chế (ngữ cảnh đưa cho giám khảo chưa phải đúng thứ Answerer đã dùng): `docs/KE_HOACH_GIAI_QUYET_MERGE_PLAN.md` mục 7. Chuẩn LLM chưa được người đối chiếu: phiếu 15 ca bất đồng chờ điền (`eval/results/ragas_calib_human_sheet_d2.md`).

Phép ánh xạ gần đúng khi cần nói theo ngôn ngữ RAGAS: faithfulness ≈ "không bịa" + `score_composer`; context recall ≈ top-3; context precision và answer relevancy ≈ "đúng trọng tâm".

### Tầng C: hành vi và hội thoại
| Chỉ số | Script | Blind | HOLDOUT-4 | Mục tiêu nhóm |
|---|---|---|---|---|
| đúng hành vi (`answer` / `clarify` / `apologize`) | `run_golden.py` | 431/553, 78% (74–81%) | 90/106, 85% (77–90%) | ≥ 88% |
| hỏi lại đúng lúc (recall) | `run_golden.py`, `run_p30.py`, `run_p31.py` | **40/86, 47% (36–57%)** | 10/16, 62% | theo dõi (điểm yếu) |
| từ chối đúng (ngoài phạm vi, chèn lệnh) | `run_golden.py` | 52/58, 90% (79–95%) | 13/13 | ≥ 90% |
| không lệch khi nhiễu (bỏ dấu, dính chữ, emoji…) | `perturb.py` | 99,53% (đo 2026-10-13, chưa chạy lại) | | ≥ 98% |
| bộ viết tay kiểu người dùng thật (real-log v1) | `run_golden.py --by source` | | 22/29 hành vi, 17/23 top-1 | |
| so sánh "A khác gì so với B" (bộ khuôn) | `run_golden.py template_thu-tuc` | 16/20 (sau sửa `split_compare`, trước đó 0/20) | | |
| liệt kê theo lĩnh vực | như trên | 32/40 có trả danh sách; chỉ 12% mục đúng lĩnh vực (hệ thống chưa có truy vấn theo lĩnh vực); câu đếm/liệt kê theo phí có truy vấn SQL (`server/fee_query.py`) | | |

Nguồn: `máy`. Hỏi lại là hành vi yếu nhất ở mọi bộ mù; từ chối thì tốt.

### Tầng D: an toàn và hệ thống
| Chỉ số | Script | Số hiện tại | Mục tiêu nhóm |
|---|---|---|---|
| D1 che CCCD/SĐT viết liền | `eval/safety/test_pii_injection.py` | 9/9 | ≥ 99% |
| D1 che CCCD/SĐT có dấu cách/gạch/chấm | như trên | 3/3 (trước khi vá: **0/3**, lỗi đã sửa trong `server/policy/policy.py`) | 3/3 |
| D1 che nhầm câu không có PII | như trên | 0/5 | 0 |
| D2 chặn chèn lệnh / chặn nhầm câu thường | như trên | 11/11 / 0/6 | ≥ 95% / 0 |
| D2 hành vi thật của hệ thống (đầu-cuối) | `--e2e --adapter answer_adapter:adapter` | 17/17 | |
| độ trễ p50 / p95 | `measure_latency.py` | xem bảng dưới | p95 ≤ 5 s |
| chạy song song, nạp lại model | `measure_parallel.py`, `measure_ollama_reload.py` | xem bên dưới | |
| dữ liệu đúng nguồn | `sample_dataset_check.py` | **chưa có**: phiếu 50 bản ghi chưa điền | |

Rủi ro chấp nhận: số 9–12 chữ số không kèm đơn vị tiền vẫn bị che (ví dụ `quyết định số 123456789` thành `[ID]`). Bản cũ cũng che số liền mạch như vậy; bản vá chỉ mở rộng sang số có dấu phân cách.

Độ trễ (đo 2026-10-13, GTX 1660 SUPER 6 GB, qwen3:4b-instruct; p95 dao động mạnh giữa các lần chạy vì n nhỏ, lần chạy lại 2026-10-14 ra p95 "đơn giản" 544 ms):

| Loại | LLM tắt (CPU) p50 / p95 | LLM bật p50 / p95 |
|---|---|---|
| đơn giản (1 thủ tục, 1 ý) | 82 / 122 ms | 78 / 196 ms |
| phức tạp (nhiều ý hoặc nhiều lượt) | 63 / 122 ms | 59 / 1.624 ms |
| hỏi lại | 85 / 105 ms | 72 / 143 ms |
| ngoài phạm vi | 57 / 113 ms | 52 / 85 ms |
| **có bước sinh chữ bằng LLM** | không có | **3.192 / 6.268 ms** |

Câu thường chạy bằng luật và truy xuất nên chỉ vài chục ms; chỉ câu cần LLM sinh chữ mất vài giây. Đổi model Ollama mất khoảng 7 giây, cùng model 0,16 giây. Chạy song song chậm hơn chạy tuần tự trên 6 GB. Hạn chế: Planner dùng luật (`S3_PLANNER_MODE=rules`), chưa đo Planner bằng LLM; "LLM tắt" là CPU của chính máy này.

## 3. Cách chạy

```bash
# Git Bash; PowerShell: đặt $env:VAR = '...' trước
PYTHONIOENCODING=utf-8 S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 python run_server.py eval/<script>.py
python eval/report.py            # một lệnh: bảng A (status), B (bộ gốc), C (bộ khuôn), D (tốc độ), D' (an toàn), F (RAGAS, chỉ trích kết quả mới nhất); ~2 phút
python run_server.py eval/run_ragas_lite.py --phase build --n 100 --blind 30 --name x
python run_server.py eval/run_ragas_lite.py --phase score --name x --judge-model qwen2.5:7b    # ~100 s/ca, cần GPU
python eval/ragas_calib.py export --name x --k 30      # rồi chấm, rồi: ragas_calib.py kappa --name x --ratings ... [--human ...]
```

## 4. Bản đồ bài báo (đánh số theo `docs/research paper/PAPER_LIST_33.md`)

Chỉ ghi cái bài báo thật sự hỗ trợ. Các bài tóm tắt nằm ở `docs/research paper/paper_summaries/`.

| Lựa chọn thiết kế | Bài | Bài báo hỗ trợ điều gì |
|---|---|---|
| Engine Strict dựa trên luật, chống bịa số | 09 (Magesh et al.), 32 (Large Legal Fictions) | Công cụ RAG pháp lý thương mại vẫn đưa ra phát biểu sai; LLM thường bịa 58–88% khi hỏi án lệ trực tiếp. 09 định nghĩa đúng × có căn cứ, báo CI 95% và Cohen's κ |
| Bốn chỉ số RAGAS và việc phải kiểm giám khảo | 31 (RAGAS), 10 | RAGAS kiểm trên WikiEval (50 trang, phần lớn do ChatGPT sinh) và có ghi chú về tái lập; vì vậy nhóm kiểm giám khảo bằng ý bịa cài sẵn và κ |
| Tách câu trả lời thành sự kiện nguyên tử | 17 (FActScore) | So giám khảo tự động với người |
| Luật cạnh giám khảo LLM | 15 (CRITIC) | LLM tự sửa tốt hơn khi có công cụ bên ngoài; tự kiểm không đủ |
| Đo truy xuất riêng (top-k) | 08 (LegalBench-RAG) | Đánh giá riêng bước truy xuất, Precision@k, Recall@k |
| MRR; câu thật khó hơn câu khuôn | 12 (STARD) | 1.543 câu hỏi thật từ người không chuyên; Recall@k và MRR@k |
| Số tham chiếu cho RAG pháp luật tiếng Việt | 02 | Context Precision 0,792, Context Recall 0,847, MRR 0,783, citation accuracy 94,2%. Chỉ là điểm tham chiếu: khác bài toán và dữ liệu |
| nDCG, embedding dense + sparse | 19 (M3-Embedding), 04 | bge-m3 mà hệ thống dùng |
| Che CCCD/SĐT, chạy tại chỗ | 05 (Lukas et al.) | Che tự động không hoàn hảo; lớp che chỉ là một lớp, không phải bảo đảm tuyệt đối |
| Thử chèn lệnh | 06 (Greshake et al.) | Lệnh nằm trong nội dung truy xuất có thể chiếm quyền ứng dụng LLM. D2 hiện chỉ thử chèn lệnh trực tiếp; tài liệu người dùng tải lên ở System 4 (chèn lệnh gián tiếp) **chưa thử** |
| So sánh phiên bản có ý nghĩa thống kê | 20 | Báo cải thiện với p < 0,001 |
| p50 / p95 | 26 (vLLM) | Khung độ trễ phục vụ (liên quan gián tiếp) |

**Sửa trước khi trình bày (bản draft nói quá):**
- **Bài 18 (CRAG):** trạng thái "Ambiguous" của nó nghĩa là độ tin cậy truy xuất ở giữa nên kết hợp tri thức trong và ngoài; nó **không** hỏi lại người dùng. Chỉ dùng như phép so sánh ("ba hành động theo độ tin cậy tốt hơn hai") và ghi nó là arXiv chưa bình duyệt.
- **Bài 25 (RouteLLM):** cho thấy chất lượng bộ định tuyến phụ thuộc độ giống giữa dữ liệu huấn luyện và benchmark; không phải bài về rò rỉ tập test. Dùng bài 09 (nêu rò rỉ dữ liệu kiểm thử như mối đe doạ độ tin cậy) và 12 để lập luận cho kỷ luật bộ mù.
- **Ngưỡng:** ngoài recall 0,847 của bài 02, các ngưỡng (faithfulness ≥ 95%, relevancy ≥ 90%, MRR ≥ 0,85, hành vi ≥ 88%…) là mục tiêu của nhóm.
- **Bài 23** là bài về công thức fine-tuning, chỉ hỗ trợ yếu cho nhiều seed hay CI; dùng bài 09 cho "báo khoảng tin cậy".

## 5. Hạn chế phải ghi trong báo cáo
- Bộ dev, ctx, khuôn, synth, p* do nhóm và agent tự soạn; bộ blind do agent soạn từ giả định, chưa có người ngoài kiểm. Chưa có nhãn nào do chuyên gia hoặc người rà tay.
- Chất lượng câu trả lời theo LLM giám khảo chưa đo đáng tin (mục B); chỉ có chỉ số luật.
- Domain Trò chuyện chung (System 4 Friendly) chưa có số đo nào; chèn lệnh gián tiếp qua tài liệu tải lên chưa được thử.
- Tỷ lệ dữ liệu đúng nguồn chưa có.
- Số đo tốc độ trên một máy (GTX 1660 SUPER 6 GB), Planner luật; chưa đo máy không GPU hay Planner LLM.
- Hỏi lại đúng chỉ 47% ở bộ mù là điểm yếu lớn nhất đã biết.

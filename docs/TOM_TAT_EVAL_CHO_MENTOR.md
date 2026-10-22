# Tóm tắt 1 phút về bộ evaluation, cho mentor

Viết lại 2026-10-14. Mọi số đo trên code hiện tại, `S3_USE_LLM=0`, Planner luật. Nguồn các con số: `eval/CRITERIA.md`, `docs/PLAN_TUAN_TOI.md` (bảng A–D), `docs/KE_HOACH_GIAI_QUYET_MERGE_PLAN.md` (mục 7).

## Bản nói (khoảng 1 phút)

"Bộ evaluation chấm hệ thống trên bốn tầng: truy xuất, chất lượng câu trả lời và chống bịa, hành vi và hội thoại, an toàn và hệ thống. Mỗi tỷ lệ có khoảng tin cậy 95%, và nhóm tách rõ bộ đã tune với bộ mù. Trên bộ mù (553 ca), hệ thống chọn đúng hành vi 78%, top-1 73%, MRR 0,76. Bộ dev đã tune thì 98%, nên nhóm chỉ báo số mù. Trên HOLDOUT-4, top-1 78%, MRR 0,82. Điểm yếu lớn nhất đã đo được là hỏi lại đúng lúc: chỉ 47% ở bộ mù; từ chối câu ngoài phạm vi thì tốt, 90%. Về an toàn, bộ test tự phát hiện lỗi thật: che CCCD/SĐT hoạt động với số viết liền nhưng bỏ sót hoàn toàn khi người dân gõ có dấu cách hoặc gạch (0/3). Nhóm đã vá, đo lại 3/3, và thêm test hồi quy; chèn lệnh chặn 11/11 với 0 lần chặn nhầm. Về chất lượng câu trả lời bằng LLM giám khảo, nhóm chạy RAGAS-lite với giám khảo qwen2.5:7b trên 92 ca và **kiểm chính giám khảo**: nó chỉ bắt được 51% ý bịa cài sẵn và đồng ý với chuẩn LLM chỉ ở mức κ 0,02, nên nhóm không dùng điểm RAGAS, mà dùng chỉ số luật (số tiền, ngày, giờ phải có trong nguồn)."

## Số cần nhớ

| Điều | Số | Ghi chú |
|---|---|---|
| Hành vi đúng, bộ mù | 431/553, 78% (74–81%) | dev 98% |
| top-1 / MRR, bộ mù | 73% (68–77%) / 0,759 | |
| HOLDOUT-4: top-1 / MRR / nDCG@5 | 78% / 0,824 / 0,805 | 77 ca có đáp án |
| Hỏi lại đúng, bộ mù | 40/86, 47% (36–57%) | điểm yếu lớn nhất |
| Từ chối đúng, bộ mù | 52/58, 90% | |
| Che PII có dấu phân cách | 0/3 trước vá, 3/3 sau vá | lỗi thật, đã vá, có test |
| Chèn lệnh | chặn 11/11, chặn nhầm 0/6, đầu-cuối 17/17 | chỉ chèn lệnh trực tiếp |
| RAGAS-lite 7B: bắt ý bịa cài sẵn | 47/92 (51%) | giám khảo không đủ tin cậy |
| RAGAS-lite 7B: κ faithfulness / relevancy | 0,02 / 0,20 | chuẩn là LLM, chưa phải người |

## Những điều được phép nói và không được nói

**Được nói:** hai bộ chấm độc lập cho số gần như trùng trên HOLDOUT-4 (hành vi 89/106 và 90/106, top-1 cùng 60/77; bản đo của draft chạy trên code cũ); bộ test tìm ra lỗi che PII và bản vá đã xác nhận; chất lượng câu trả lời theo LLM "chưa đo đáng tin" và nhóm biết vì sao.

**Không nói:**
- "Bộ mù" cho bộ sinh tự động hoặc bộ real-log (đã bị đọc lỗi).
- "Chuyên gia rà" hoặc "đã hiệu chuẩn theo người": chưa có nhãn nào do người chấm. Chuẩn hiệu chuẩn hiện là LLM (Claude); phiếu 15 ca cho người chấm đã chuẩn bị.
- Điểm RAGAS 0,83 / 0,78 như điểm chất lượng, hoặc điểm RAGAS cũ của branch draft (0,40 / 0,38 / 0,81 / 0,68).
- "0% số bịa trên 394 ca" như bằng chứng không bịa.
- Các ngưỡng (≥ 80%, MRR ≥ 0,85, ≥ 88%…) như tiêu chuẩn của văn liệu: đó là mục tiêu của nhóm (trừ recall 0,847 của Paper 02, chỉ để tham chiếu).
- Paper 18 (CRAG) như bằng chứng cho hỏi lại; Paper 25 (RouteLLM) như bằng chứng cho rò rỉ tập test.
- Chèn lệnh "đã được kiểm toàn diện": chỉ thử trực tiếp, chưa thử chèn lệnh gián tiếp qua tài liệu System 4 tải lên (Paper 06).

## Còn thiếu (nói thẳng nếu bị hỏi)
Domain Trò chuyện chung chưa có số đo; tỷ lệ dữ liệu đúng nguồn chưa có (phiếu 50 bản ghi chưa điền); chưa đo máy không GPU và Planner bằng LLM; mọi bộ test do nhóm hoặc agent soạn, chưa có người ngoài kiểm.

## Cập nhật 22/10/2026: câu hỏi thật (real_v1)

Từ 22/10 có bộ đo trên **câu hỏi thật của người dân** (Strict, 282 câu sau khi bỏ câu cụt) và câu hỏi thật hoặc do người viết trên Wikipedia (Friendly, 177 câu); chạy một lần, nhãn khoá trước khi chạy. Báo cáo: `docs/EVAL_THAT_V1.md`.

| Điều | Số | Ghi chú |
|---|---|---|
| Strict, hành vi đúng | 158/282, **56,0%** (50,2–61,7%) | thấp hơn bộ nhóm soạn (77–78%) |
| Strict, top-1 / top-3 | 7/55, **12,7%** / 12/55, 21,8% | chỉ 55 câu có đáp án |
| Strict, từ chối đúng | 116/220, 52,7% | trả lời ở 101/220 câu ngoài phạm vi |
| Friendly, Du lịch văn bản / bảng | 92,0% (46/50) / 65,4% (17/26) | một bài Wikipedia; 40 câu bảng soạn khi chỉ nhìn tên cột |
| Friendly, từ chối | 71,4% (10/14) | |
| Friendly, Y tế `urgent` khuyên cấp cứu | 4/10 | điểm yếu an toàn |

**Được nói:** có bộ câu hỏi thật của người dân, nhãn khoá trước khi chạy, chạy một lần, báo cả số thấp. **Không nói:** "nhãn do chuyên gia" hoặc "độc lập giữa hai người" (hai lượt đều là AI); "log người dùng thật" (đây là câu hỏi công khai trên Cổng).

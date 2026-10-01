# Gems từ CoVe, CRITIC, CRAG áp dụng cho V10.5

> Nguồn: ba file breakdown `Cove_breakdown.md` (paper 9), `CRITIC_breakdown.md` (paper 11), `CRAG_breakdown.md` (paper 14) trong `Documentation/research paper/`. Số liệu của paper lấy từ các file đó, chưa đối chiếu lại với PDF gốc.
> Số liệu của V10.5 lấy từ đợt chấm tay ngày 30/09 (57 câu, file `Evaluation/results/cham_tay_*.csv`) và từ code hiện tại (`system_websearch.py`, `verifier.py`, `evidence.py`).
> Đây là đề xuất, chưa cái nào được cài hay đo trên V10.5.

## 0. Công nghệ core của ba paper (tên gốc)

Cột "Gem" là phần V10.5 có thể mượn. "Đã có" nghĩa là V10.5 đã có bản tương đương trong code.

### Paper 9: CoVe (Chain-of-Verification)
| Tên kỹ thuật | Là gì | V10.5 |
|---|---|---|
| **Chain-of-Verification (CoVe)** | Quy trình 4 bước: (1) sinh `baseline response`, (2) `plan verification questions` (đặt câu hỏi kiểm cho từng mệnh đề), (3) `execute verification` (trả lời câu hỏi kiểm), (4) sinh `final verified response`. | Chưa có. Gem ở mục 2 |
| **Joint** | Lập và trả lời câu hỏi kiểm trong cùng một prompt; mô hình thấy bản nháp nên chép lại lỗi. Yếu nhất. | `verifier.verify()` đang gần dạng này |
| **2-Step** | Bước trả lời câu hỏi kiểm không nhìn thấy bản nháp. Precision Wikidata cao nhất (0,36). | Chưa có |
| **Factored** | Mỗi câu hỏi kiểm một prompt riêng, độc lập, chạy song song được. | Chưa có |
| **Factor+Revise** | Factored cộng bước tường minh phân loại từng dữ kiện `consistent` / `inconsistent` / `partially consistent`, rồi chỉ giữ phần nhất quán. FACTSCORE cao nhất (71,4). | `apply_fail_policy` gọt dòng sai là bản gần nhất |
| **Open vs yes/no verification questions** | Câu hỏi kiểm dạng mở tốt hơn có/không, vì mô hình hay đồng ý với câu hỏi dẫn. | Verifier hiện hỏi cờ đúng/sai |
| **CoVe-RAG** (hướng tác giả đề xuất) | Kiểm bằng tài liệu truy xuất thay vì tri thức của mô hình. | Chính là kiến trúc V10.5 (kiểm với Evidence Pack) |
| **FACTSCORE** | Metric: tách văn bản thành sự kiện nguyên tử (`atomic facts`), kiểm từng sự kiện. | Chưa dùng; chấm tay thay thế |
| **Hallucination, exposure bias** | Bịa thông tin; lỗi câu trước làm ngữ cảnh cho lỗi câu sau trong văn bản dài. | Thuật ngữ nền |

### Paper 11: CRITIC
| Tên kỹ thuật | Là gì | V10.5 |
|---|---|---|
| **CRITIC (Tool-Interactive Critiquing)** | Vòng lặp `validate → critique → correct`: sinh nháp, dùng công cụ ngoài kiểm, biến kết quả kiểm thành phê bình, sửa theo phê bình. Dừng khi đạt hoặc hết số vòng. | `rule_check` + `fix_notes` + viết lại là bản rút gọn |
| **External tools** | `Google Search` (kiểm sự kiện), `Python interpreter` (kiểm chương trình), `Perspective API` (điểm độc hại). | Công cụ của V10.5 là luật code đối chiếu Evidence Pack |
| **Free-form vs structured critique** | Phê bình tự do (kiểu ReAct, hỏi đáp mở) và có cấu trúc (điểm số, lỗi thực thi). | `fix_notes()` là dạng có cấu trúc |
| **Self-correction / Self-Refine / Reflexion / Self-Verification** | Mô hình tự phê bình và sửa không có tín hiệu ngoài. Paper cho là kém tin cậy với kiến thức ngoài. | Verifier LLM 1,5B thuộc nhóm này |
| **AUROC** | Metric đo khả năng phân biệt câu đúng/sai của tín hiệu tự đánh giá; CRITIC cao hơn xác suất token, entropy, self-evaluation. | Chưa dùng |
| **Oracle setting** | Chỉ sửa các mẫu đã biết là sai, để đo trần lợi ích. | Chưa dùng |
| **In-context learning (few-shot, kiểu ReAct)** | Dạy bằng ví dụ trong prompt, không huấn luyện thêm. Phụ thuộc prompt. | Đã có (prompt trong `prompts/`) |
| **Wrong-correction rate** | Tỷ lệ sửa từ đúng thành sai (~10% hỏi đáp, 14,3% chương trình). | Chưa đo; gem 5 mục 3 |
| **Related**: `LLM-Augmenter`, `KALMV`, `ConsistencyVerify`, `PALADIN`, `TALM`, `Toolformer` | Hệ thống cùng hướng (phản hồi ngoài, verifier riêng, nhất quán đa mẫu, phục hồi lỗi công cụ). | Chỉ tham khảo |

### Paper 14: CRAG (Corrective RAG)
| Tên kỹ thuật | Là gì | V10.5 |
|---|---|---|
| **Retrieval Evaluator** | Mô hình `T5-large` (khoảng 0,77 tỷ tham số) tinh chỉnh, chấm từng cặp câu hỏi–tài liệu. Chính xác 84,3% trên PopQA, hơn các cách dùng ChatGPT. | Chưa có ở Hệ thống 1. Gem 2 mục 4 làm bằng code |
| **Ba hành động Correct / Incorrect / Ambiguous** | Có tài liệu vượt ngưỡng trên: Correct; tất cả dưới ngưỡng dưới: Incorrect; còn lại: Ambiguous. | Hệ thống 2 có `confident` / MCQ / `no_evidence` |
| **Decompose-then-Recompose + Knowledge Strips** | Cắt tài liệu thành đoạn 1-vài câu (`strips`), chấm từng đoạn, bỏ đoạn thừa, nối lại theo thứ tự. | Chưa có. Gem 2 mục 4 |
| **Web Search action + Query Rewriting** | Khi Incorrect/Ambiguous: viết lại câu hỏi thành từ khóa, tìm web, ưu tiên Wikipedia. | Đã có: bước hiểu câu hỏi, `site:gov.vn`, `better_search_query` |
| **Self-CRAG** | CRAG gắn trên `Self-RAG` (paper 10). | Không dùng |
| **Plug-and-play** | Evaluator đứng giữa retriever và generator, không huấn luyện lại generator. | Vị trí đề xuất cho cổng bằng chứng |
| Dữ liệu thử: `PopQA`, `Biography`, `PubHealth`, `ARC-Challenge`; retriever `Contriever` | Các bộ đo của paper. | Không liên quan trực tiếp |

### Thước đo hay gặp
`precision`, `recall`, `F1`, `accuracy` (hỏi đáp, phân loại); `FACTSCORE` (văn bản dài); `AUROC` (độ phân biệt của tín hiệu tự đánh giá).

## 1. Kết luận ngắn

Cả ba paper cùng một ý: **mô hình tự chấm bài của chính nó thì không đáng tin; tín hiệu kiểm tra phải đến từ ngoài mô hình** (nguồn, công cụ, luật). Chấm tay của V10.5 khớp với ý này: trước khi thêm luật "không dòng nào khớp nguồn", câu có verifier PASS trung bình chỉ đúng 43% và 47% có chi tiết bịa. Sau khi thêm luật, PASS đúng 65%, bịa 21%.

Ba gem đáng làm trước, theo thứ tự lợi/chi phí:

| # | Gem | Từ paper | Chi phí | Nhắm vào lỗi nào |
|---|---|---|---|---|
| 1 | Không để bản viết lại ghi đè bản nháp nếu nó không tốt hơn (chống `wrong-correction`, vòng `validate → critique → correct`) | CRITIC | Rất thấp (vài dòng) | Viết lại làm hỏng câu đúng |
| 2 | Cổng bằng chứng sau bước tra cứu: `Retrieval Evaluator` + 3 hành động `Correct / Ambiguous / Incorrect`, làm bằng code | CRAG | Thấp (code, không thêm lần gọi LLM) | Trả lời lệch câu hỏi, lẫn thủ tục khác |
| 3 | Ghi chú sửa lỗi cụ thể cho từng luật, kèm dòng nguồn (`structured critique` có bằng chứng) | CRITIC | Thấp | Viết lại chỉ cứu 3/12 câu |

## 2. CoVe (Chain-of-Verification, Dhuliawala 2023): kiểm từng mệnh đề, độc lập với bản nháp

### Điều paper chứng minh
- Mô hình đưa sai khi viết danh sách dài, nhưng trả lời đúng khi được hỏi riêng từng dữ kiện: khoảng 70% đúng khi hỏi riêng, so với 17% trong danh sách gốc (Wikidata).
- Cách thực hiện càng độc lập với bản nháp càng tốt: precision Wikidata là 0,17 (gốc), 0,29 (joint), 0,32 (factored), 0,36 (2-step). Joint kém hơn vì mô hình nhìn thấy bản nháp và chép lại lỗi.
- Câu hỏi kiểm chứng dạng mở tốt hơn dạng có/không, vì mô hình có xu hướng đồng ý với câu hỏi dẫn.
- Bước cuối chỉ giữ phần nhất quán: số sự kiện giảm 16,6 xuống 12,3 nhưng FACTSCORE tăng 55,9 lên 71,4. Bỏ bớt ý đổi lấy độ chính xác.
- Giới hạn: CoVe kiểm bằng tri thức nội tại. Nếu mô hình không biết thì tự kiểm chỉ sinh thêm một lần bịa. Chính tác giả đề xuất kết hợp truy xuất (CoVe-RAG), tức là kiểm với tài liệu.

### So với V10.5
- `verifier.verify()` gọi LLM một lần, đưa cả câu hỏi, nguồn và bản nháp rồi hỏi các cờ đúng/sai (`verdict`, `answers_question`, `wrong_situation`...). Đó là dạng `Joint` + câu hỏi có/không (`yes/no verification`), cách yếu nhất theo paper. Chấm tay xác nhận qwen2.5:1.5b không bắt được câu bịa và câu lệch câu hỏi.
- Đã có sẵn một phần tư tưởng CoVe bằng code: luật `no-source-line` và `cite_lines` tách câu trả lời thành dòng rồi so từng dòng với nguồn.

### Gem áp dụng được
1. **Nguyên tắc `Factored verification` (kiểm từng dòng, không kiểm cả khối), nhưng làm bằng code thay vì LLM.** Đã thử độ phủ từng dòng: câu bịa có trung vị 0,52, câu không bịa 0,88. Nhưng ngưỡng chỉnh trên bộ dev không giữ được trên held-out (bắt 3/6, báo nhầm 1-2), nên chưa đưa vào. Còn khả năng dùng làm tín hiệu phụ, không làm luật chặn.
2. **Kiểm "có trả lời đúng trường được hỏi" theo kiểu câu hỏi kiểm dạng mở (`open verification question`).** Hai câu lệch đề còn lọt qua (`temp-08`: hỏi hạn tạm trú, trả lời xóa tạm trú; `ho-23`: hỏi khai báo tạm vắng, trả lời thời hạn giải quyết). Hướng làm không cần LLM: từ câu hỏi nhận ra trường cần trả lời (thời hạn, lệ phí, nơi nộp, hồ sơ) bằng từ khóa, rồi kiểm câu trả lời có chứa dấu hiệu của trường đó (số ngày/tháng/năm, số tiền, tên cơ quan) không.
3. **Ưu tiên cắt bỏ hơn viết lại (`Factor+Revise`: chỉ giữ phần `consistent`).** `apply_fail_policy` đã gọt dòng sai, đúng tinh thần factor+revise. Số liệu cũ của V10.5 cho thấy viết lại chỉ cứu 3/12 câu FAIL, nên đây là hướng đúng.

### Không nên áp dụng
- Quy trình đủ bốn bước bằng LLM 1.5B: thêm ít nhất vài lần gọi nữa trên nền 3,7 lần gọi/câu và p50 khoảng 27-29 giây. Paper cũng nói chi phí là hạn chế lớn nhất, và paper chạy trên Llama 65B, không phải mô hình 1,5B.
- Tự kiểm bằng tri thức của mô hình: với 1,5B gần như không có tri thức hành chính Việt Nam để kiểm.

## 3. CRITIC (Tool-Interactive Critiquing, Gou 2024): phê bình phải dựa trên công cụ bên ngoài

### Điều paper chứng minh
- Tự phê bình thuần túy thiếu tin cậy; CRITIC dùng tìm kiếm hoặc trình thông dịch làm tín hiệu ngoài và cải thiện đều (trung bình +7,7 F1 trên ChatGPT, tỷ lệ bịa trên HotpotQA giảm 36% xuống 7%).
- Công cụ không bắt được mọi lỗi: lỗi suy luận tăng 5% lên 10%; interpreter bắt tốt lỗi thực thi, yếu ở lỗi hiểu đề.
- **Sửa nhầm là có thật**: khoảng 10% câu hỏi đáp và 14,3% chương trình bị sửa từ đúng thành sai.
- Phê bình phải hành động được (lỗi cụ thể, bằng chứng cụ thể), không phải "hãy kiểm tra lại".
- Phần lớn lợi ích đến sau 2-3 vòng, độ trễ tăng gần tuyến tính theo số vòng.
- Nên phân biệt: câu trả lời sai, không đủ bằng chứng, công cụ lỗi, công cụ mâu thuẫn. Nên đo thêm tỷ lệ sửa nhầm và khả năng truy vết, không chỉ độ chính xác.

### So với V10.5
- Tầng luật của `rule_check` (thẩm quyền, cầm đồ, yếu tố nước ngoài, hồ sơ lẫn thủ tục, lệ phí, cơ quan, `S#` giữ chỗ, chép khung, không dòng khớp nguồn) chính là "công cụ" kiểu CRITIC: kiểm bằng code với nguồn. Hướng này đã được số liệu chấm tay ủng hộ (luật không-dòng-khớp-nguồn bắt 9/11 câu bịa).
- Vòng lặp trong `system_websearch.py` (dòng 112-136): sau khi viết lại, `draft` bị ghi đè và bản nháp đầu mất. Không có bước so sánh nào xem bản mới có ít lỗi hơn bản cũ không. Đây đúng là rủi ro "sửa nhầm" của CRITIC.
- `Verification.fix_notes()` chỉ có ghi chú cho: chi tiết không có trong nguồn, ý không có căn cứ, trích dẫn sai, thiếu trích dẫn, chép khung, câu quá ngắn/giữ chỗ, mâu thuẫn, không trả lời đúng câu hỏi, sai tình huống. **Không có ghi chú** cho các luật thẩm quyền, cầm đồ, yếu tố nước ngoài, hồ sơ lẫn thủ tục, lệ phí, cơ quan. Khi các luật này kích hoạt, lần viết lại chỉ nhận câu chung chung.

### Gem áp dụng được
1. **Chọn bản tốt hơn thay vì luôn lấy bản viết lại (giảm `wrong-correction rate`).** Giữ bản nháp đầu và bản viết lại, chấm cả hai bằng `rule_check` (số `rule_issues`), lấy bản ít lỗi hơn; hòa thì giữ bản đầu. Chi phí rất thấp, không thêm lần gọi LLM, và chặn đúng lỗi sửa nhầm.
2. **Thêm ghi chú sửa lỗi cụ thể (`structured critique`) cho 6 luật còn thiếu**, kèm dòng nguồn liên quan khi có (đúng tinh thần "phê bình có bằng chứng"). Lưu ý: mô hình 1,5B từng chép nguyên văn ghi chú vào câu trả lời (`temp-02`), nên ghi chú phải ngắn, không có nhãn dạng tiêu đề, và luật chép-khung hiện có phải giữ.
3. **Thêm từ điển giấy tờ lỗi thời làm "công cụ" kiểm (`external tool` kiểu CRITIC, nhưng là code).** Chấm tay thấy 4 trong 57 câu dính giấy tờ đã bỏ (hộ khẩu, giấy chuyển hộ khẩu, CMND...), `perm-02` vẫn lọt PASS. Kiểm đây là việc của code, không phải của LLM. Cổng liên quan của CRAG (mục 4) không bắt được lỗi này vì nguồn cũ vẫn "liên quan".
4. **Giữ MAX_VERIFY_RETRIES=1.** Paper nói lợi ích giảm dần sau 2-3 vòng và độ trễ tăng tuyến tính; dữ liệu V10.5 (viết lại cứu 3/12) không ủng hộ thêm vòng.
5. **Ghi thêm số đo vào `evaluate.py`**: kết quả bản nháp đầu và bản cuối, để tính tỷ lệ "viết lại cứu được" và "viết lại làm hỏng". Hiện `evaluate.py` đã ghi `attempts`, `rewrites`, `rule_issues`, chỉ thiếu verdict của lượt đầu.

### Không nên áp dụng
- Vòng lặp công cụ tìm kiếm trong lúc kiểm (kiểu ReAct) trên 1,5B: dài, dễ lạc, và độ trễ đã cao.
- Phân loại lỗi công cụ kiểu PALADIN: ngoài phạm vi hiện tại.

## 4. CRAG (Corrective Retrieval Augmented Generation, Yan 2024): chấm nguồn trước khi dùng

### Điều paper chứng minh
- Bộ đánh giá nhẹ chấm **từng tài liệu** so với câu hỏi, ra ba trạng thái: Correct (ít nhất một tài liệu vượt ngưỡng trên), Incorrect (tất cả dưới ngưỡng dưới), Ambiguous (còn lại). Mỗi trạng thái một cách xử lý: tinh lọc nguồn nội bộ / bỏ và tìm web / trộn cả hai.
- **Knowledge strips**: cắt tài liệu thành đoạn 1-vài câu, chấm từng đoạn, bỏ đoạn không liên quan, nối lại theo thứ tự cũ. Bỏ bước này làm kết quả PopQA giảm (ablation).
- Viết lại câu hỏi thành từ khóa cho tìm kiếm web; ưu tiên Wikipedia để giảm rủi ro nguồn kém.
- Giới hạn tác giả nêu: bộ đánh giá đo **mức liên quan**, không đo đúng sai; ngưỡng đặt theo từng bộ dữ liệu; web có thể thiên lệch; độ trễ chỉ đo ở bước sinh.

### So với V10.5
- Hệ thống 2 (CSDL) đã có tầng tương đương: `confident` / hỏi lại chọn / `no_evidence`.
- Hệ thống 1 (web) **không có cổng bằng chứng**. Trong `system_websearch.py`, chỉ cần `pack["sources"]` khác rỗng là đi tiếp soạn câu trả lời, bất kể nguồn có liên quan hay không (dòng 88-92). Tài liệu của dự án (`RESEARCH_PAPERS.md`, mục paper 14) cũng ghi điểm này là việc tương lai.
- Mô hình soạn câu trả lời nhận **toàn bộ** `title + snippet + content` của các nguồn. Chấm tay thấy nhiều câu lẫn nội dung thủ tục khác (`temp-03` lẫn hồ sơ cán bộ chiến sĩ, `misc-06` thêm "hợp đồng lao động", `ho-13` thêm ý "tên thương mại"). Chưa chứng minh nguyên nhân là nguồn nhiễu hay là lỗi sinh, nên đây chỉ là giả thuyết.
- Đã có sẵn: viết lại truy vấn (bước hiểu câu hỏi), thêm truy vấn `site:gov.vn` (tương đương ưu tiên nguồn tin cậy của CRAG), và tra cứu bổ sung theo `better_search_query` của verifier.

### Gem áp dụng được
1. **Cổng bằng chứng bằng code (thay `Retrieval Evaluator` T5-large, không cần huấn luyện), với 3 trạng thái `Correct / Ambiguous / Incorrect`.** Chấm từng nguồn với câu hỏi bằng độ trùng âm tiết (đã có hàm `terms()` dùng trong `evidence.py`), rồi chia ba trạng thái: có nguồn vượt ngưỡng trên thì đi tiếp; tất cả dưới ngưỡng dưới thì tra lại một lần với truy vấn viết lại hoặc từ chối sớm (tiết kiệm lần gọi LLM soạn câu và kiểm chứng); nằm giữa thì đi tiếp nhưng gắn cờ "bằng chứng yếu". Ngưỡng phải hiệu chỉnh trên bộ dev rồi kiểm trên held-out (paper nhắc đúng điểm này).
2. **`Decompose-then-Recompose` với `Knowledge Strips`: cắt nguồn thành câu, giữ câu liên quan trước khi đưa vào prompt.** Có hai lợi: bớt nhiễu cho mô hình 1,5B và prompt ngắn hơn (có thể giảm độ trễ). Giữ thứ tự gốc như paper. Cần đo: chất lượng câu trả lời và tỷ lệ mất câu chứa đáp án.
3. **Nhớ giới hạn "liên quan khác với đúng"**: cổng này không bắt được tài liệu cũ nhưng đúng chủ đề (xem mục 3, gem 3).

### Không nên áp dụng
- Huấn luyện bộ đánh giá T5-large riêng: cần dữ liệu có nhãn, và dự án đã chọn giữ qwen2.5:1.5b, không mở rộng huấn luyện.
- Tìm kiếm Google API và duyệt trang: V10.5 đã có đường tìm kiếm qua MCP.

## 5. Ánh xạ gem lên các lỗi còn lại

| Lỗi còn lọt PASS (chấm tay 30/09) | Gem có thể bắt | Ghi chú |
|---|---|---|
| `temp-08`, `ho-23` trả lời lệch trường được hỏi | CoVe gem 2 (kiểm trường cần trả lời); có thể CRAG gem 1 nếu lỗi nằm ở nguồn | Chưa biết lỗi do nguồn hay do sinh; cần xem `_evidence.jsonl` của hai câu |
| `perm-02` giấy tờ lỗi thời | CRITIC gem 3 (từ điển giấy tờ cũ) | CRAG không giúp |
| `birth-03` bịa giấy tờ, có dòng chép đúng nguồn nên lọt luật | CoVe gem 1 (độ phủ từng dòng làm tín hiệu phụ) | Đã thử, chưa tổng quát hóa |
| Viết lại làm câu tệ hơn | CRITIC gem 1 | Cần số đo đầu vào (gem 5) |

## 6. Kế hoạch thử, mỗi bước kèm cách đo

Dùng chung hai bộ đã có (dev 45 câu, held-out 30 câu) và hai file chấm tay làm chuẩn. Chạy lại khoảng 25 phút mỗi lần; chênh lệch dưới 2-3 câu coi là nhiễu.

1. CRITIC gem 1 và gem 5 (chọn bản tốt hơn, ghi verdict lượt đầu). Thước đo: số câu "viết lại cứu" so với "viết lại làm hỏng".
2. CRITIC gem 2 và 3 (ghi chú cụ thể, từ điển giấy tờ lỗi thời). Thước đo: `perm-02` và các câu dính giấy tờ cũ; kiểm tra không có câu đúng bị đánh FAIL oan.
3. CRAG gem 1 (cổng bằng chứng). Thước đo: tỷ lệ câu bị chặn mà chấm tay là đúng (báo nhầm) so với câu bịa bị chặn; thêm số lần gọi LLM mỗi câu.
4. CRAG gem 2 (cắt nguồn theo câu). Thước đo: điểm chấm tay trung bình và p50 độ trễ.
5. CoVe gem 2 (kiểm trường được hỏi). Thước đo: `temp-08`, `ho-23`, và không làm hỏng các câu thời hạn/lệ phí đang đúng.

Mỗi bước phải qua `Evaluation/check_natural_questions.py` (hiện 110 ca) và thêm ít nhất một test hồi quy.

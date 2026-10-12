# BỘ HƯỚNG DẪN ĐÁNH GIÁ THỰC NGHIỆM TOÀN DIỆN (COMPREHENSIVE EVALUATION BENCHMARK SUITE)
**Dự án:** Trợ lý Trí tuệ Nhân tạo Pháp lý & Dịch vụ công Cấp Xã/Phường (Sys_3_4)  
**Quy chuẩn học thuật:** RAGAS (Paper 31 - EACL 2024), LegalBench-RAG (Paper 08 - NeurIPS 2024), CoVe (Paper 13 - 2023), CRITIC (Paper 15 - ICLR 2024), LQ-RAG (Paper 11 - 2025).  
**Mục tiêu:** Cung cấp tài liệu hoàn chỉnh, dễ hiểu nhất cho sinh viên và mentor để hiểu rõ: Chấm điểm bằng gì? Bộ test gồm những gì? Áp dụng đa lĩnh vực (multi-domain) như thế nào?

---

## PHẦN 1: TẠI SAO PHẢI CÓ BỘ EVALUATION HOÀN THIỆN? (DÀNH CHO NGƯỜI MỚI BẮT ĐẦU)

Khi làm một hệ thống AI (đặc biệt là RAG hoặc Chatbot tra cứu), nếu chỉ thử vài câu bằng tay trên web rồi nói "hệ thống chạy tốt lắm" thì **không giảng viên hay hội đồng khoa học nào chấp nhận**. Bạn phải chứng minh được:
1. **Đo bằng thước đo gì?** (Các tiêu chí định lượng toán học rõ ràng).
2. **Đo trên tập dữ liệu nào?** (Có bộ câu hỏi chuẩn - Golden Evaluation Set).
3. **Có khách quan không?** (Không được lấy câu hỏi đã dùng để huấn luyện/viết code ra để tự chấm điểm - phải có tập mù Blind Holdout).

---

## PHẦN 2: BẢNG TIÊU CHÍ CHẤM ĐIỂM CHUẨN (EVALUATION METRICS)

Hệ thống đánh giá chia làm 3 nhóm tiêu chí chính: **Truy xuất (Retrieval)**, **Hành vi & Chất lượng câu trả lời (Generation & RAGAS)**, và **Hạ tầng (Latency & System)**:

### 1. Nhóm Tiêu chí Truy xuất (Retrieval Metrics - Tầng Tìm kiếm Dữ liệu)
| Tiêu chí | Công thức / Định nghĩa | Ý nghĩa thực tiễn |
|---|---|---|
| **Top-1 Accuracy** | $\frac{N_{\text{top1\_correct}}}{N_{\text{in\_scope}}}$ | Tỷ lệ thủ tục xếp hạng thứ nhất trùng khớp 100% với thủ tục chuẩn nhà nước. |
| **Top-3 Accuracy** | $\frac{N_{\text{top3\_contains}}}{N_{\text{in\_scope}}}$ | Tỷ lệ thủ tục chuẩn nằm trong top 3 gợi ý đầu tiên của hệ thống. |
| **MRR (Mean Reciprocal Rank)** | $\frac{1}{\|Q\|} \sum_{i=1}^{\|Q\|} \frac{1}{\text{rank}_i}$ | Đo lường vị trí xuất hiện của kết quả đúng. Nếu luôn ở top 1 thì MRR = 1.0. |

### 2. Nhóm Tiêu chí RAGAS & Chống Ảo Giác (Generation & Faithfulness)
Được chuẩn hóa từ nghiên cứu **RAGAS (Paper 31 - EACL 2024)** và **CRITIC (Paper 15 - ICLR 2024)**:
| Tiêu chí RAGAS | Cách chấm điểm | Mục tiêu trong hệ thống |
|---|---|---|
| **Faithfulness (Độ trung thực sự thật)** | Tỷ lệ các luận điểm (claims) trong câu trả lời được suy ra trực tiếp từ tài liệu nguồn (không tự bịa). | $\ge 95\%$ |
| **Answer Relevance (Đúng trọng tâm / Concise)** | Câu trả lời khớp đúng ý người hỏi (hỏi phí chỉ báo phí, hỏi hồ sơ chỉ báo giấy tờ, không tuôn dài dòng). | $\ge 90\%$ (Đạt 97.5% ở DEV) |
| **Context Recall (Độ phủ ngữ cảnh)** | Toàn bộ các thông tin cần thiết trong văn bản pháp luật có được đưa vào câu trả lời hay không. | $\ge 85\%$ |
| **Numerical Hallucination Rate (Tỷ lệ bịa số liệu)** | Tỷ lệ câu trả lời chứa số tiền (lệ phí) hoặc thời hạn không có trong CSDL nhà nước. | **Bắt buộc = 0.0%** (Triệt tiêu hoàn toàn nhờ Strict Engine dựng bảng bằng code) |

### 3. Nhóm Tiêu chí Đàm thoại Đa lượt & Hành vi (Context & Behavioral)
| Tiêu chí | Cách chấm điểm | Mục đích |
|---|---|---|
| **Behavioral Accuracy** | Hệ thống hành xử đúng đắn: Biết trả lời khi có dữ liệu (`answer`), biết lịch sự từ chối khi vượt cấp thẩm quyền (`apologize`), biết hỏi lại khi câu hỏi quá mơ hồ (`clarify`). | Đạt 82.1% trên tập mù HOLDOUT-4 |
| **Context Resolution Rate** | Khi người dân hỏi câu tỉnh lược đa lượt (*"thế còn phí?"*, *"mất mấy ngày?"*), hệ thống vẫn giữ đúng chủ đề. | Đạt 96.7% trên tập `ctx.json` |

---

## PHẦN 3: THIẾT KẾ 1 BỘ TEST LỚN ĐA LĨNH VỰC (CROSS-DOMAIN BENCHMARK)

Để bộ test **không bị bó hẹp trong 1 lĩnh vực**, mà có thể mở rộng áp dụng cho nhiều tập dữ liệu khác nhau (Tư pháp, Đất đai, Y tế, Giáo dục, Lao động - Xã hội), nhóm xây dựng cấu trúc theo **8 Nhóm Chủ đề Khảo nghiệm Tổng quát (General Test Archetypes)**:

```
                          [ 8 CHỦ ĐỀ TEST LỚN ĐA LĨNH VỰC ]
                                          │
    ┌───────────────────┬─────────────────┼───────────────────┬───────────────────┐
    ▼                   ▼                 ▼                   ▼                   ▼
[1. Khẩu ngữ /      [2. Đa điều kiện /    [3. Hỏi số liệu     [4. Đa ý định       [5. Đa lượt /
Viết tắt]           Nhân khẩu học]        định lượng]         (Multi-intent)]     Tỉnh lược]
    │                   │                 │                   │                   │
    ├───────────────────┼─────────────────┴───────────────────┴───────────────────┤
    ▼                   ▼                                                         ▼
[6. Phân nhánh /    [7. Bẫy ngoài phạm vi                                    [8. Nhiễu gõ phím /
Hỏi lại (Clarify)]  (Out-of-scope)]                                          Không dấu]
```

### Chi tiết 8 Chủ đề Test có thể áp dụng cho mọi Dataset:

1. **Chủ đề 1: Câu hỏi khẩu ngữ, viết tắt và teencode (Colloquial & Acronyms):**
   - *Ví dụ Hành chính:* `"dk kết hôn cần cccd không ad"`, `"làm gks cho con"`.
   - *Áp dụng Y tế / Giáo dục:* `"dk khám bhyt"`, `"xin cấp lại btot nghiep"`.
2. **Chủ đề 2: Câu hỏi điều kiện nhân khẩu học phức tạp (Demographic Constraints):**
   - *Ví dụ Hành chính:* `"khai sinh cho con nhưng bố mẹ chưa đăng ký kết hôn"`, `"làm giấy độc thân nhưng đã từng ly hôn"`.
   - *Áp dụng Đất đai:* `"chuyển nhượng quyền sử dụng đất khi người đứng tên đã mất"`.
3. **Chủ đề 3: Tra cứu số liệu định lượng (Quantitative - Lệ phí & Thời hạn):**
   - *Ví dụ Hành chính:* `"chứng thực bản sao tốn bao nhiêu tiền 1 trang?"`, `"sau bao nhiêu ngày thì nhận kết quả?"`.
   - *Kiểm chứng:* Bắt buộc kiểm tra độ trung thực (chống ảo giác số liệu tiền tệ).
4. **Chủ đề 4: Câu hỏi đa ý định (Multi-intent Queries):**
   - *Ví dụ:* Một câu hỏi gồm 2 thủ tục khác nhau: `"vừa muốn khai sinh vừa muốn nhập hộ khẩu cho con thì làm thế nào?"`.
   - *Đánh giá:* Hệ thống có bóc tách được thành 2 tác vụ con song song hay không.
5. **Chủ đề 5: Ngữ cảnh đàm thoại đa lượt (Multi-turn Context & Anaphora):**
   - *Lượt 1:* `"Tôi muốn làm thủ tục tách hộ"`.
   - *Lượt 2:* `"Cần những giấy tờ gì?"`.
   - *Lượt 3:* `"Nộp online được không?"`.
   - *Lượt 4:* `"Thế còn phí thì sao?"`.
6. **Chủ đề 6: Nhận diện thủ tục đa biến thể và hỏi lại (Ambiguity & Clarification):**
   - *Ví dụ:* Khi người dùng chỉ hỏi chung chung `"tôi muốn đăng ký kết hôn"` (trong DB có: kết hôn trong nước, kết hôn có yếu tố nước ngoài, khu vực biên giới). Hệ thống không được đoán mò mà phải hỏi lại để làm rõ.
7. **Chủ đề 7: Câu hỏi bẫy và ngoài phạm vi thẩm quyền (Out-of-Scope & Guardrails):**
   - *Ví dụ:* Người dân ra xã đòi `"cấp hộ chiếu phổ thông"` hoặc `"đăng ký cấp bằng lái xe ô tô"`. Hệ thống phải lịch sự từ chối và hướng dẫn đúng cơ quan thẩm quyền (Công an tỉnh / Sở GTVT).
8. **Chủ đề 8: Khả năng chống chịu nhiễu gõ phím và bỏ dấu (Perturbation Robustness):**
   - Thử nghiệm trên văn bản gõ không dấu (`"dang ky khai sinh"`), gõ dính chữ (`"giayto"`), hoặc chèn icon cảm xúc.

---

## PHẦN 4: HƯỚNG DẪN TẠO VÀ SỬ DỤNG GOLDEN SET THEO TỪNG DOMAIN

### Golden Set là gì?
**Golden Set (Tập kiểm thử vàng)** là một file chứa các câu hỏi chuẩn, trong đó **mỗi câu hỏi đều được chuyên gia gắn nhãn sẵn đáp án đúng tuyệt đối** để phần mềm tự động chấm điểm.

### Cấu trúc 1 ca kiểm thử chuẩn (JSON Schema) áp dụng cho mọi Domain:
```json
{
  "id": "GOLD-001",
  "domain": "Hành chính công cấp Xã",
  "question": "Làm giấy khai sinh cho con hết bao nhiêu tiền?",
  "golden_contexts": [
    "Thủ tục đăng ký khai sinh (Mã TTHC: 1.000894)",
    "Thông tư số 85/2019/TT-BTC: Miễn lệ phí đăng ký khai sinh đúng hạn cho trẻ em."
  ],
  "expected_procedure_id": "1.000894",
  "expected_behavior": "answer",
  "expected_facts": {
    "fee": "Miễn lệ phí (đúng hạn)",
    "time": "Giải quyết trong ngày"
  },
  "forbidden_facts": [
    "100.000đ",
    "50.000đ"
  ]
}
```

### Các trường quan trọng để máy tự chấm:
1. `expected_procedure_id`: Máy so sánh ID hệ thống tìm được với ID chuẩn $\rightarrow$ Tính ra **Top-1 / Top-3 Accuracy**.
2. `expected_behavior`: Kiểm tra xem AI hành xử đúng loại không (`answer`: trả lời, `apologize`: từ chối, `clarify`: hỏi lại) $\rightarrow$ Tính ra **Behavioral Accuracy**.
3. `forbidden_facts`: Chứa các từ khóa bịa đặt phổ biến (như tiền lệ phí bịa). Nếu câu trả lời chứa từ này $\rightarrow$ Đánh rớt tiêu chí **Hallucination**.

---

## PHẦN 5: CÁCH TRIỂN KHAI RAGAS ĐỂ ĐO LƯỜNG TỰ ĐỘNG

Nhóm có thể tích hợp thư viện mã nguồn mở **RAGAS** theo chuẩn Paper 31 qua đoạn mã Python ngắn gọn sau:

```python
# Cài đặt: pip install ragas datasets
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevance,
    context_recall,
    context_precision
)

# 1. Chuẩn bị dữ liệu đầu ra từ hệ thống Sys_3_4
data_samples = {
    'question': ['Làm khai sinh nộp hồ sơ ở đâu?'],
    'answer': ['Bạn nộp tại Ủy ban nhân dân cấp xã nơi cư trú của người cha hoặc người mẹ.'],
    'contexts': [['Theo Luật Hộ tịch 2014, UBND cấp xã nơi cư trú của người cha hoặc người mẹ thực hiện đăng ký khai sinh.']],
    'ground_truth': ['Ủy ban nhân dân cấp xã nơi cư trú của cha hoặc mẹ.']
}

dataset = Dataset.from_dict(data_samples)

# 2. Đánh giá tự động với RAGAS
score = evaluate(
    dataset,
    metrics=[
        faithfulness,         # Đo độ trung thực (không bịa)
        answer_relevance,     # Đo câu trả lời có đúng trọng tâm không
        context_recall        # Đo ngữ cảnh có đầy đủ không
    ]
)

print(score)
# Kết quả mẫu: {'faithfulness': 1.0000, 'answer_relevance': 0.9521, 'context_recall': 1.0000}
```

---

## PHẦN 6: TÓM TẮT ĐỂ BÁO CÁO MENTOR TRONG 1 PHÚT

> *"Thưa mentor, bộ evaluation hoàn thiện của nhóm được xây dựng theo chuẩn RAGAS (Paper 31) và LegalBench-RAG (Paper 08). Nhóm thiết kế một Golden Set lớn bao phủ 8 dạng câu hỏi thực tế (từ khẩu ngữ, viết tắt, không dấu, đến câu hỏi bẫy ngoài thẩm quyền và đàm thoại đa lượt). Tiêu chí chấm điểm được phân rã rành mạch thành 3 tầng: Tầng truy xuất (Top-1/Top-3/MRR), Tầng hành vi & Chống ảo giác (Faithfulness $\ge 95\%$, Phí bịa = $0\%$), và Tầng đàm thoại đa lượt (Context Resolution). Nhờ khung schema chuẩn này, bộ test có thể tái sử dụng dễ dàng cho bất kỳ domain nào khác."*

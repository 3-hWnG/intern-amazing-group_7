# README - Quy trình làm bài báo ứng dụng AI theo nhóm trên Git

## 1. Mục tiêu của repository

Repository này được sử dụng để quản lý quá trình học tập, nghiên cứu và viết bài báo theo nhóm trong các môn học.

Mỗi nhóm sinh viên sẽ làm việc trên **một nhánh Git riêng**, dùng để:

- Phác thảo ý tưởng đề tài.
- Tìm và phân tích bài báo liên quan.
- Thiết kế hệ thống hoặc ứng dụng có tích hợp AI.
- Viết nội dung bài báo theo từng phần.
- Cập nhật tiến độ thường xuyên.
- Lưu minh chứng: tài liệu, hình ảnh, kiến trúc, kết quả thí nghiệm, bảng đánh giá.

Nhánh `main` chỉ dùng để lưu:

- Hướng dẫn chung.
- Template viết bài.
- Quy định đặt tên nhánh.
- Quy trình làm việc.
- Checklist đánh giá.
- Tài liệu tham khảo chung.

Các nhóm **không được viết trực tiếp lên nhánh `main`** nếu không được giảng viên cho phép.

---

## 2. Mô hình tổ chức Git

Repository gồm 2 loại nhánh chính:

```text
main
│
├── SE1701_G01
├── SE1701_G02
├── SE1702_G01
├── SE1702_G02
├── AI1801_G01
├── AI1801_G02
└── ...
```

Trong đó:

- `main`: nhánh hướng dẫn chung.
- Mỗi nhóm có một nhánh riêng.
- Leader nhóm được cấp quyền quản lý nhánh của nhóm.
- Thành viên trong nhóm commit nội dung vào nhánh nhóm.
- Giảng viên theo dõi tiến độ qua lịch sử commit, pull request hoặc báo cáo tuần.

---

## 3. Quy định đặt tên nhánh

### 3.1. Cú pháp đặt tên

```text
<MA_LOP>_G<SO_THU_TU_NHOM>
```

Ví dụ:

```text
SE1701_G01
SE1701_G02
SE1702_G01
AI1801_G01
BDT301_G03
```

### 3.2. Quy tắc

| Thành phần | Ý nghĩa | Ví dụ |
|---|---|---|
| `MA_LOP` | Mã lớp hoặc mã môn/lớp | `SE1701`, `AI1801`, `BDT301` |
| `G` | Viết tắt của Group | `G` |
| `SO_THU_TU_NHOM` | Số thứ tự nhóm, dùng 2 chữ số | `01`, `02`, `03` |

### 3.3. Ví dụ đúng

```text
SE1701_G01
SE1701_G02
BDT301_G05
AIE101_G03
```

### 3.4. Ví dụ không đúng

```text
Group1
Nhom1
SE1701_Nhom1
SE1701_Group_1
se1701_g1
```

---

## 4. Quy định phân quyền

### 4.1. Giảng viên

Giảng viên có quyền:

- Quản lý repository.
- Tạo hoặc duyệt nhánh nhóm.
- Kiểm tra tiến độ.
- Review nội dung.
- Comment góp ý.
- Merge nội dung tốt vào nhánh `main` nếu cần.

### 4.2. Leader nhóm

Leader nhóm có trách nhiệm:

- Quản lý nhánh của nhóm.
- Phân công công việc cho thành viên.
- Kiểm tra chất lượng nội dung trước khi commit.
- Đảm bảo nhóm cập nhật Git thường xuyên.
- Tạo pull request nếu giảng viên yêu cầu.
- Tổng hợp báo cáo tiến độ hằng tuần.

### 4.3. Thành viên nhóm

Thành viên nhóm có trách nhiệm:

- Làm đúng phần được phân công.
- Commit nội dung rõ ràng.
- Không xóa file của thành viên khác nếu chưa thống nhất.
- Ghi rõ nguồn tài liệu tham khảo.
- Cập nhật tiến độ đúng hạn.

---

## 5. Cách tạo nhánh nhóm

Leader hoặc giảng viên tạo nhánh theo cú pháp:

```bash
git checkout main
git pull origin main
git checkout -b SE1701_G01
git push -u origin SE1701_G01
```

Các thành viên clone repository:

```bash
git clone <repository-url>
cd <repository-name>
git checkout SE1701_G01
```

Cập nhật code/tài liệu mới nhất từ nhánh nhóm:

```bash
git pull origin SE1701_G01
```

Commit nội dung:

```bash
git add .
git commit -m "docs: update research topic proposal"
git push origin SE1701_G01
```

---

## 6. Quy định commit message

Commit message nên viết rõ ràng theo cú pháp:

```text
<type>: <nội dung thay đổi>
```

### Loại commit thường dùng

| Type | Ý nghĩa | Ví dụ |
|---|---|---|
| `docs` | Cập nhật tài liệu | `docs: add related work summary` |
| `topic` | Cập nhật đề tài | `topic: refine research objectives` |
| `review` | Thêm phân tích bài báo | `review: analyze five related papers` |
| `method` | Cập nhật phương pháp | `method: add system architecture description` |
| `experiment` | Cập nhật thí nghiệm | `experiment: add evaluation metrics` |
| `result` | Cập nhật kết quả | `result: add baseline comparison table` |
| `fix` | Sửa lỗi nội dung | `fix: correct citation format` |
| `figure` | Thêm hình ảnh/sơ đồ | `figure: add system architecture diagram` |

Ví dụ:

```bash
git commit -m "review: add literature matrix for AI-powered LMS"
git commit -m "method: update RAG-based system architecture"
git commit -m "result: add expert evaluation table"
```

---

## 7. Cấu trúc thư mục đề xuất cho mỗi nhánh nhóm

Mỗi nhóm nên tổ chức thư mục như sau:

```text
.
├── README.md
├── 01_topic_proposal/
│   ├── topic_proposal.md
│   └── topic_revision_log.md
│
├── 02_related_work/
│   ├── search_keywords.md
│   ├── paper_list.md
│   ├── literature_review_matrix.md
│   └── paper_summaries/
│       ├── paper_01.md
│       ├── paper_02.md
│       └── paper_03.md
│
├── 03_problem_and_gap/
│   ├── problem_statement.md
│   ├── research_gap.md
│   └── research_questions.md
│
├── 04_proposed_system/
│   ├── system_overview.md
│   ├── system_architecture.md
│   ├── ai_model_integration.md
│   ├── data_flow.md
│   └── diagrams/
│       ├── architecture.png
│       └── workflow.png
│
├── 05_methodology/
│   ├── methodology.md
│   ├── dataset.md
│   ├── baseline.md
│   └── evaluation_metrics.md
│
├── 06_experiment_results/
│   ├── experimental_setup.md
│   ├── results.md
│   ├── tables/
│   └── figures/
│
├── 07_paper_draft/
│   ├── paper_outline.md
│   ├── abstract.md
│   ├── introduction.md
│   ├── related_work.md
│   ├── methodology.md
│   ├── results.md
│   ├── discussion.md
│   └── conclusion.md
│
├── 08_final_submission/
│   ├── final_paper.docx
│   ├── final_paper.pdf
│   └── presentation.pptx
│
└── weekly_reports/
    ├── week_01.md
    ├── week_02.md
    └── week_03.md
```

---

## 8. Quy trình làm bài báo ứng dụng AI theo từng bước

## Bước 1: Chọn lĩnh vực ứng dụng

Mỗi nhóm chọn một lĩnh vực cụ thể, ví dụ:

- Giáo dục.
- Quản lý học tập.
- Quản lý đề tài sinh viên.
- Nông nghiệp thông minh.
- Quản lý kho.
- Quản lý sự kiện.
- Y tế.
- Giao thông.
- Tài chính.
- Chăm sóc khách hàng.
- Quản lý nhân sự.
- Quản lý tài liệu.

Kết quả cần tạo:

```text
01_topic_proposal/topic_proposal.md
```

Nội dung cần có:

- Tên đề tài dự kiến.
- Lĩnh vực ứng dụng.
- Vấn đề thực tế.
- Đối tượng người dùng.
- Lý do cần tích hợp AI.
- Model AI dự kiến sử dụng.
- Kết quả mong muốn.

---

## Bước 2: Tìm bài báo liên quan

Mỗi nhóm cần tìm tối thiểu:

- 5 bài báo liên quan trực tiếp.
- 3 bài báo về model AI hoặc phương pháp AI.
- 2 bài báo về domain ứng dụng.

Nguồn tìm kiếm đề xuất:

- Google Scholar.
- IEEE Xplore.
- ACM Digital Library.
- SpringerLink.
- ScienceDirect.
- MDPI.
- arXiv, nếu cần tham khảo kỹ thuật mới.
- CEUR Workshop Proceedings.

Từ khóa tìm kiếm mẫu:

```text
AI-powered management system conference paper
machine learning based decision support system
AI-based learning management system
LLM-based academic advising system
RAG-based decision support system
AIoT smart agriculture management system
machine learning inventory management system
supervisor recommendation system
research topic recommendation system
```

Kết quả cần tạo:

```text
02_related_work/search_keywords.md
02_related_work/paper_list.md
02_related_work/literature_review_matrix.md
```

---

## Bước 3: Đọc và tóm tắt từng bài báo

Mỗi bài báo cần được tóm tắt theo mẫu:

```markdown
# Paper 01 Summary

## Citation

Tên bài:
Tác giả:
Năm:
Nguồn:
DOI/Link:

## Problem

Bài báo giải quyết vấn đề gì?

## Method

Bài báo dùng phương pháp/model/hệ thống nào?

## Dataset

Bài báo dùng dữ liệu gì?

## Evaluation

Bài báo đánh giá bằng metric nào?

## Results

Kết quả chính là gì?

## Limitations

Hạn chế của bài báo là gì?

## Relevance to our topic

Bài báo liên quan gì đến đề tài của nhóm?

## Possible improvement

Nhóm có thể cải tiến hoặc mở rộng điểm nào?
```

Lưu tại:

```text
02_related_work/paper_summaries/paper_01.md
02_related_work/paper_summaries/paper_02.md
...
```

---

## Bước 4: Tạo Literature Review Matrix

Nhóm cần tổng hợp các bài báo thành bảng:

```markdown
| Paper | Domain | AI Model / Method | Dataset | Evaluation Metrics | Main Contribution | Limitation | Relevance |
|---|---|---|---|---|---|---|---|
| Paper 1 | Education | LLM, RAG | LMS data | Accuracy, expert rating | AI feedback system | Small dataset | High |
| Paper 2 | Agriculture | Random Forest | Sensor data | F1-score | Disease detection | No explanation | Medium |
```

Lưu tại:

```text
02_related_work/literature_review_matrix.md
```

Mục tiêu của bảng này:

- Biết các bài trước đã làm gì.
- Biết model nào đã được dùng.
- Biết dataset nào phù hợp.
- Biết metric nào thường dùng.
- Tìm ra gap để phát triển bài của nhóm.

---

## Bước 5: Xác định vấn đề nghiên cứu và gap

Nhóm cần trả lời:

1. Vấn đề thực tế là gì?
2. Vì sao vấn đề này quan trọng?
3. Các bài trước đã giải quyết như thế nào?
4. Các bài trước còn hạn chế gì?
5. Nhóm sẽ cải tiến điểm nào?
6. Đóng góp của nhóm là gì?

Kết quả cần tạo:

```text
03_problem_and_gap/problem_statement.md
03_problem_and_gap/research_gap.md
03_problem_and_gap/research_questions.md
```

Ví dụ gap:

> Existing AI-powered learning management systems mainly focus on quiz generation or chatbot support, while limited attention has been given to rubric-based feedback and supervisor recommendation in research topic registration workflows.

---

## Bước 6: Xây dựng câu hỏi nghiên cứu

Mỗi nhóm nên có 2 đến 4 câu hỏi nghiên cứu.

Ví dụ:

```text
RQ1. How accurately can the proposed system detect duplicate or overlapping research topics?

RQ2. How effectively can the AI model recommend suitable supervisors based on topic descriptions and supervisor profiles?

RQ3. How useful is the LLM-generated feedback in improving student topic proposals?

RQ4. How much time can the proposed system reduce compared with the traditional manual review process?
```

Lưu tại:

```text
03_problem_and_gap/research_questions.md
```

---

## Bước 7: Thiết kế hệ thống đề xuất

Nhóm cần mô tả hệ thống ở mức kiến trúc.

Nội dung cần có:

- Người dùng chính.
- Chức năng chính.
- Dữ liệu đầu vào.
- AI model sử dụng.
- Luồng xử lý.
- Kiến trúc frontend/backend/database/AI service.
- Cách tích hợp model AI.
- Output của hệ thống.

Kết quả cần tạo:

```text
04_proposed_system/system_overview.md
04_proposed_system/system_architecture.md
04_proposed_system/ai_model_integration.md
04_proposed_system/data_flow.md
```

Ví dụ kiến trúc:

```text
User Interface
    |
Backend API
    |
Database
    |
AI Service
    |
Model / Vector Database / External API
```

---

## Bước 8: Chọn model AI và mô tả cách tích hợp

Nhóm cần nêu rõ:

| Nội dung | Câu hỏi cần trả lời |
|---|---|
| Model dùng là gì? | LLM, CNN, LSTM, Random Forest, XGBoost, RAG, embedding model? |
| Vì sao chọn model này? | Có phù hợp với bài toán không? |
| Model lấy từ đâu? | Paper trước, HuggingFace, API, thư viện open-source? |
| Input của model là gì? | Text, image, sensor data, log, bảng dữ liệu? |
| Output của model là gì? | Nhãn phân loại, dự báo, khuyến nghị, phản hồi? |
| Cách tích hợp vào app? | REST API, Python service, Node.js service, batch job? |
| Có baseline không? | Rule-based, manual, TF-IDF, LLM-only? |

Lưu tại:

```text
04_proposed_system/ai_model_integration.md
```

---

## Bước 9: Thiết kế phương pháp đánh giá

Một bài báo ứng dụng AI bắt buộc cần có đánh giá.

Tùy bài toán, có thể dùng:

| Loại bài toán | Metric phù hợp |
|---|---|
| Phân loại | Accuracy, Precision, Recall, F1-score |
| Dự báo | MAE, RMSE, MAPE |
| Gợi ý | Top-k Accuracy, Precision@k, Recall@k, NDCG |
| RAG / LLM | Relevance, Faithfulness, Correctness, Expert Rating |
| Hệ thống | Response Time, Throughput, Latency |
| Người dùng | Survey, SUS, User Satisfaction |
| So sánh quy trình | Time Saving, Error Reduction |

Kết quả cần tạo:

```text
05_methodology/evaluation_metrics.md
05_methodology/baseline.md
05_methodology/dataset.md
```

---

## Bước 10: Xây dựng baseline

Baseline là phương pháp dùng để so sánh với hệ thống đề xuất.

Ví dụ:

| Bài toán | Baseline |
|---|---|
| Gợi ý giảng viên | Manual selection, TF-IDF + cosine similarity |
| Phát hiện đề tài trùng | Keyword matching, TF-IDF |
| Chatbot/RAG | LLM-only, keyword search |
| Dự báo kho | Moving average, ARIMA |
| Phân loại ảnh | Simple CNN, pretrained model without fine-tuning |
| Nông nghiệp IoT | Rule-based threshold |

Lưu tại:

```text
05_methodology/baseline.md
```

---

## Bước 11: Viết bản nháp bài báo

Nhóm viết bài theo cấu trúc:

```text
Title
Abstract
Keywords
1. Introduction
2. Related Work
3. Proposed System / Methodology
4. Experimental Setup
5. Results
6. Discussion
7. Conclusion and Future Work
References
```

Lưu tại:

```text
07_paper_draft/
```

Mỗi phần nên được viết trong file riêng trước, sau đó mới ghép thành bản hoàn chỉnh.

---

## Bước 12: Cập nhật tiến độ hằng tuần

Mỗi nhóm cần tạo báo cáo tuần:

```text
weekly_reports/week_01.md
weekly_reports/week_02.md
weekly_reports/week_03.md
```

Mẫu báo cáo tuần:

```markdown
# Weekly Report - Week 01

## Group Information

Class:
Group:
Leader:
Members:

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Nguyễn Văn A | Search papers | Found 5 papers |
| Trần Văn B | Summarize paper 1-2 | Completed |
| Lê Văn C | Draft topic proposal | Completed |

## Git Commits

| Commit ID | Message | Author |
|---|---|---|
| abc123 | docs: add paper list | Nguyen Van A |

## Current Problems

- Chưa tìm được dataset phù hợp.
- Chưa xác định baseline.

## Plan for Next Week

- Hoàn thành literature review matrix.
- Chọn model AI.
- Viết problem statement.

## Questions for Instructor

- Dataset giả lập có được chấp nhận không?
- Có thể dùng Gemini API thay cho local model không?
```

---

## 9. Mẫu file Topic Proposal

Tạo file:

```text
01_topic_proposal/topic_proposal.md
```

Nội dung mẫu:

```markdown
# Topic Proposal

## 1. Group Information

- Class:
- Group:
- Leader:
- Members:

## 2. Proposed Title

English title:

Vietnamese title:

## 3. Application Domain

Ví dụ: education, agriculture, warehouse management, healthcare, finance, student support.

## 4. Problem Statement

Mô tả vấn đề thực tế mà nhóm muốn giải quyết.

## 5. Motivation

Vì sao vấn đề này quan trọng?

## 6. Target Users

Ai là người dùng chính của hệ thống?

## 7. Proposed AI Model / Method

Nhóm dự kiến dùng model hoặc phương pháp AI nào?

Ví dụ:

- LLM
- RAG
- CNN
- LSTM
- XGBoost
- Random Forest
- Embedding model
- Recommendation model

## 8. System Features

Các chức năng chính của hệ thống:

1.
2.
3.
4.

## 9. Expected Contribution

Đóng góp dự kiến:

1.
2.
3.

## 10. Evaluation Plan

Nhóm sẽ đánh giá hệ thống như thế nào?

- Dataset:
- Baseline:
- Metrics:
- Expert evaluation:
- User survey:

## 11. Related Papers

Liệt kê ít nhất 5 bài báo liên quan.

| No | Title | Year | Source | Link / DOI |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
```

---

## 10. Mẫu Literature Review Matrix

Tạo file:

```text
02_related_work/literature_review_matrix.md
```

Nội dung mẫu:

```markdown
# Literature Review Matrix

| No | Paper Title | Year | Venue | Domain | AI Method | Dataset | Metrics | Main Contribution | Limitation | Relevance to Our Topic |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | |
| 2 | | | | | | | | | | |
| 3 | | | | | | | | | | |
| 4 | | | | | | | | | | |
| 5 | | | | | | | | | | |
```

---

## 11. Mẫu Research Questions

Tạo file:

```text
03_problem_and_gap/research_questions.md
```

Nội dung mẫu:

```markdown
# Research Questions

## Main Research Question

How can an AI model be integrated into a domain-specific management system to improve decision support, recommendation, or automation?

## Sub Research Questions

RQ1.

RQ2.

RQ3.

RQ4.
```

---

## 12. Mẫu System Architecture

Tạo file:

```text
04_proposed_system/system_architecture.md
```

Nội dung mẫu:

```markdown
# System Architecture

## 1. Overview

Mô tả tổng quan hệ thống.

## 2. Main Components

| Component | Description |
|---|---|
| Frontend | Giao diện người dùng |
| Backend API | Xử lý nghiệp vụ |
| Database | Lưu dữ liệu hệ thống |
| AI Service | Chạy model AI hoặc gọi API model |
| Vector Database | Lưu embedding nếu dùng RAG |
| External Services | API hoặc công cụ bên ngoài |

## 3. Architecture Diagram

Chèn hình kiến trúc tại đây.

## 4. Data Flow

1. User nhập dữ liệu.
2. Backend lưu dữ liệu.
3. Backend gửi dữ liệu đến AI Service.
4. AI Service xử lý bằng model.
5. Kết quả trả về hệ thống.
6. User xem kết quả hoặc khuyến nghị.

## 5. AI Integration

Mô tả model AI được tích hợp ở bước nào trong hệ thống.
```

---

## 13. Mẫu Evaluation Plan

Tạo file:

```text
05_methodology/evaluation_metrics.md
```

Nội dung mẫu:

```markdown
# Evaluation Plan

## 1. Evaluation Objectives

Mục tiêu đánh giá hệ thống là gì?

## 2. Dataset

Mô tả dữ liệu dùng để đánh giá.

## 3. Baseline

Hệ thống hoặc phương pháp so sánh.

## 4. Metrics

| Metric | Meaning | Why Used |
|---|---|---|
| Accuracy | | |
| F1-score | | |
| Response Time | | |
| Expert Rating | | |
| User Satisfaction | | |

## 5. Evaluation Procedure

1.
2.
3.
4.

## 6. Expected Results

Kết quả kỳ vọng.
```

---

## 14. Quy định cập nhật Git hằng tuần

Mỗi nhóm phải cập nhật Git ít nhất:

- 2 lần mỗi tuần.
- Mỗi thành viên nên có commit riêng.
- Commit phải có nội dung thật, không commit rỗng.
- File cập nhật phải nằm đúng thư mục.
- Không upload file không liên quan.

### Checklist mỗi tuần

| Tuần | Công việc chính | File cần cập nhật |
|---|---|---|
| Week 1 | Chọn đề tài, lập nhóm, tạo nhánh | `topic_proposal.md`, `week_01.md` |
| Week 2 | Tìm bài báo liên quan | `paper_list.md`, `search_keywords.md`, `week_02.md` |
| Week 3 | Tóm tắt bài báo | `paper_summaries/`, `week_03.md` |
| Week 4 | Literature review matrix | `literature_review_matrix.md`, `week_04.md` |
| Week 5 | Xác định gap và RQ | `research_gap.md`, `research_questions.md` |
| Week 6 | Thiết kế hệ thống | `system_architecture.md`, `data_flow.md` |
| Week 7 | Mô tả model AI và baseline | `ai_model_integration.md`, `baseline.md` |
| Week 8 | Thiết kế evaluation | `evaluation_metrics.md`, `dataset.md` |
| Week 9 | Viết Introduction và Related Work | `introduction.md`, `related_work.md` |
| Week 10 | Viết Methodology | `methodology.md` |
| Week 11 | Thực nghiệm và kết quả | `experimental_setup.md`, `results.md` |
| Week 12 | Discussion và Conclusion | `discussion.md`, `conclusion.md` |
| Week 13 | Ghép bản nháp hoàn chỉnh | `paper_outline.md`, full draft |
| Week 14 | Review và chỉnh sửa | revision log |
| Week 15 | Hoàn thiện bài | final paper |
| Week 16 | Nộp bài và thuyết trình | final paper, slides |

---

## 15. Tiêu chí đánh giá nhóm

| Tiêu chí | Trọng số gợi ý |
|---|---|
| Chất lượng ý tưởng đề tài | 10% |
| Chất lượng literature review | 15% |
| Xác định gap và research questions | 15% |
| Thiết kế hệ thống | 15% |
| Tích hợp model AI hợp lý | 15% |
| Evaluation plan và kết quả | 15% |
| Chất lượng bài viết | 10% |
| Cập nhật Git và làm việc nhóm | 5% |

---

## 16. Checklist trước khi nộp bài cuối

Trước khi nộp, nhóm cần kiểm tra:

- [ ] Tên đề tài rõ ràng.
- [ ] Có ít nhất 5 bài báo liên quan.
- [ ] Có literature review matrix.
- [ ] Có problem statement.
- [ ] Có research gap.
- [ ] Có research questions.
- [ ] Có kiến trúc hệ thống.
- [ ] Có mô tả model AI.
- [ ] Có baseline.
- [ ] Có dataset hoặc dữ liệu giả lập hợp lý.
- [ ] Có metric đánh giá.
- [ ] Có kết quả thực nghiệm hoặc đánh giá chuyên gia.
- [ ] Có discussion.
- [ ] Có limitation.
- [ ] Có future work.
- [ ] Có references đúng định dạng.
- [ ] Có commit history đầy đủ.
- [ ] Có weekly reports.

---

## 17. Lưu ý quan trọng

Một bài báo ứng dụng AI không nên chỉ trình bày rằng nhóm đã làm một ứng dụng.

Bài cần trả lời được:

1. Vấn đề thực tế là gì?
2. Vì sao cần AI?
3. Model AI được chọn có phù hợp không?
4. Hệ thống tích hợp AI như thế nào?
5. Có dữ liệu để đánh giá không?
6. Có baseline để so sánh không?
7. Kết quả có tốt hơn cách làm cũ không?
8. Hạn chế của hệ thống là gì?
9. Có thể mở rộng nghiên cứu như thế nào?

---

## 18. Câu định vị bài báo ứng dụng AI

Các nhóm có thể sử dụng câu sau để định vị nghiên cứu:

> This study does not aim to propose a new AI model from scratch. Instead, it investigates how an existing AI model can be integrated into a domain-specific management system and evaluates its effectiveness in improving decision support, recommendation, or automation in a real-world application context.

Phiên bản tiếng Việt:

> Nghiên cứu này không nhằm đề xuất một mô hình AI hoàn toàn mới, mà tập trung khảo sát cách tích hợp một mô hình AI hiện có vào hệ thống quản lý theo lĩnh vực cụ thể, đồng thời đánh giá hiệu quả của mô hình trong việc cải thiện hỗ trợ ra quyết định, gợi ý hoặc tự động hóa trong bối cảnh ứng dụng thực tế.

---

## 19. Kết luận

Repository này là nơi quản lý toàn bộ quá trình làm bài báo của các nhóm.

Mỗi nhóm cần:

- Làm việc trên nhánh riêng.
- Cập nhật tiến độ thường xuyên.
- Viết tài liệu theo từng bước.
- Tìm bài báo liên quan có chất lượng.
- Xác định gap rõ ràng.
- Thiết kế hệ thống có tích hợp AI thật sự.
- Có phương pháp đánh giá cụ thể.
- Hoàn thiện bài báo theo cấu trúc học thuật.

Mục tiêu cuối cùng là mỗi nhóm có thể tạo ra một bài báo mang tính ứng dụng, có hệ thống, có AI model, có đánh giá và có khả năng phát triển thành bài hội thảo.

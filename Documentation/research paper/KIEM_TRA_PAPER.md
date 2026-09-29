# Kiểm tra 20 paper trong `research paper/` (29/09/2026)

Cách kiểm tra:
- Đọc trang 1 của từng PDF (tiêu đề, tác giả, mã arXiv in bên lề).
- So với tên folder, tên file và phần đầu `literature_review.md`.
- Tra arXiv, ACL Anthology và Semantic Scholar để tìm bản thật của paper mà tên folder muốn nói tới.

## Kết luận nhanh

| Mức | Số paper | Paper |
|---|---|---|
| PDF sai hẳn (bài khác, thường khác ngành) | 11 | 01, 02, 03, 04, 05, 07, 08, 12, 13, 15, 20 |
| PDF là bài khác nhưng cùng chủ đề RAG | 1 | 16 |
| PDF đúng nhưng tác giả ghi sai | 2 | 06, 18 |
| Đúng cả PDF lẫn thông tin | 6 | 09, 10, 11, 14, 17, 19 |

Nguyên nhân lỗi PDF: Gemini ghi sai **4 chữ số đầu** của mã arXiv (năm và tháng), rồi tải PDF theo mã sai đó. Ví dụ:
- LegalCheck thật là 2605.12012, Gemini ghi 2601.12932.
- GASP thật là **26**07.04223, Gemini ghi **24**07.04223.
- BM25→CRAG thật là **26**04.01733, Gemini ghi **24**04.01733.

Cả 20 paper đều có thật trên arXiv hoặc hội thảo, nên tên folder vẫn dùng được. Tuy vậy:
- Nhiều paper ghi tên tác giả bịa, ví dụ "Marco L., Alessandro P." hay "Florian Schneider".
- Số liệu trong mục 3 của `literature_review.md` phần lớn là bịa.
- Mục 2 và 3 của cả 20 file có chung 4 gạch đầu dòng mẫu, như "Phân tách rõ ràng giữa tri thức tĩnh…" và "Chứng minh bằng thực nghiệm rằng…". Đây là câu đệm lặp lại, không lấy từ paper nào.

## Chi tiết từng paper

### 01 GuidaPA
- **PDF trong folder:** "Combinatorial Multivariant Multi-Armed Bandits…" (arXiv 2406.01386, cs.LG). Sai.
- **Thông tin đúng:** arXiv **2606.01386** (31/05/2026). Tác giả: Daniel M. Jimenez-Gutierrez, Albenzio Cirillo, Raffaele Nicolussi, Alessio Beltrame, Andrea Vitaletti.
- **Lỗi trong review:**
  - Năm ghi 2024, đúng là 2026.
  - Tác giả "Marco L., Alessandro P." là bịa.
  - Câu "tuân thủ 100% GDPR" là bịa.
  - Kết quả thật: QLoRA 4-bit, 15 vòng federated, ROUGE-L 59.44, BLEU-4 45.02, trên tài liệu SIGESON/SIDFORS của Ý.

### 02 GovAI-Pipe
- **PDF trong folder:** "Mixup Augmentation with Multiple Interpolations" (2406.01417). Sai.
- **Thông tin đúng:** arXiv **2606.01417** (31/05/2026). Tác giả: Ahmet Kaplan (1 người).
- **Lỗi trong review:**
  - Năm và tác giả sai.
  - Câu "triệt tiêu 94.7% câu trả lời vượt thẩm quyền" là bịa. Paper thật là nghiên cứu thiết kế (design science), đưa ra pipeline 4 tầng và minh hoạ bằng 2 tình huống trên e-Devlet, không có số đo kiểu này.

### 03 Grip on LLMs
- **PDF trong folder:** bài vật lý về mối nối Josephson trên graphene (2408.09925). Sai.
- **Thông tin đúng:** arXiv **2608.09925** (10/08/2026). Tác giả: Laurens Samson, Iva Gornishka, Gossa Lô, Yuki M. Asano, Sennay Ghebreab.
- **Lỗi trong review:**
  - Năm và tác giả sai.
  - Kết quả thật: 6 chiều đánh giá (factuality, honesty, bias, năng lượng, chi phí, minh bạch dữ liệu), hơn 30 mô hình, không mô hình nào tốt ở mọi chiều. Review nói "factuality và trích dẫn là tiên quyết", paper không kết luận vậy.

### 04 COPAL
- **PDF trong folder:** bài thiên văn "[Mg/Fe] and variable IMF" (2406.04394). Sai.
- **Thông tin đúng:** arXiv **2606.04394** (03/06/2026, cs.SE). Tác giả: Yingjie Liu, Yongxiang Hu, Xuan Wang, Yilun Li, Yunlei Wei, Xiaoyu Wang, Yangfan Zhou (Fudan và Meituan).
- **Lỗi trong review:**
  - Venue "Findings ACL 2024" là sai.
  - Kết quả thật: tỉ lệ lỗi 33.1% trên 9 mô hình. Review ghi "trượt trên 45%", sai.

### 05 LegalCheck
- **PDF trong folder:** "Stone Duality for Preordered Topological Spaces" (2601.12932, math.GN). Sai.
- **Thông tin đúng:** "LegalCheck: **Retrieval- and** Context-Augmented Generation for Drafting Municipal Legal Advice Letters", arXiv **2605.12012** (12/05/2026, cs.AI). Tác giả: Virgill van der Meer, Julien Rossi.
- **Lỗi trong review:**
  - Tiêu đề thiếu "Retrieval- and".
  - Tác giả "Schneider, Frattini, Mendez" là bịa, nên folder `05_Schneider_…` cũng sai tên.
  - Kết quả thật: hệ RAG kết hợp CAG soạn thư phản hồi khiếu nại cho thành phố Amsterdam, giữ được 80–100% nội dung cốt lõi. Câu "91.2% tuân thủ" là bịa.
  - Ý "lọc thẩm quyền địa phương" không có trong paper.

### 06 LegalBench-RAG
- **PDF trong folder:** đúng bài (2408.10343).
- **Lỗi trong review:**
  - Tác giả thật là **Nicholas Pipitone, Ghita Houir Alami** (ZeroEntropy). Review ghi Neel Guha, Nyarko, Ho (Stanford), đó là nhóm làm LegalBench gốc. Folder `06_Guha_…` sai tên.
  - Tiêu đề thật không có chữ "Assessing": "LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain".
  - Câu "Retrieval gây 72% lỗi" chưa tìm thấy trong paper, nhiều khả năng là bịa.

### 07 CanLegalRAGBench
- **PDF trong folder:** "Simulated Adoption: Decoupling Magnitude and Direction in LLM In-Context Conflict Resolution" (Long Zhang, SCUT). Sai.
- **Thông tin đúng:** arXiv **2605.30497** (28/05/2026). Tác giả: Ethan Zhao, Maksym Taranukhin, Wei Cui, Moira Aikenhead, Vered Shwartz (UBC). Repo: github.com/NLP-UBC/CanLegalRAGBench.
- **Lỗi trong review:**
  - Mã 2602.04918 sai. Tác giả "Champoux, Sauve" là bịa, nên folder `07_Champoux_…` sai tên.
  - Review viết về "hierarchy-aware chunking, tăng 38%", paper không có nội dung này.
  - Kết quả thật: có 8–29% claim không được tài liệu truy xuất hỗ trợ, và embedding mã nguồn mở ngang embedding đóng.

### 08 HyPA-RAG
- **PDF trong folder:** "Truth-Aware Context Selection (TACS)", Tian Yu và cộng sự, ICT/CAS. Sai. Link ACL `2024.findings-acl.645` trong review cũng trỏ tới bài TACS này.
- **Thông tin đúng:** arXiv **2409.09046**. Tác giả: Rishi Kalra, Zekun Wu, Ayesha Gulley, Airlie Hilliard, Xin Guan, Adriano Koshiyama, Philip Treleaven. Venue: NAACL 2025 Industry Track và EMNLP 2024 CustomNLP4U Workshop (`aclanthology.org/2024.customnlp4u-1.18`).
- **Lỗi trong review:**
  - Tác giả "Shuo Zhang, Liang Zhao…" là bịa, nên folder `08_Zhang_…` sai tên.
  - Cơ chế thật: bộ phân loại độ phức tạp câu hỏi, rồi chỉnh tham số truy xuất, kết hợp dense, sparse và knowledge graph, thử trên luật NYC LL144. Review viết là "dựa trên entropy", chưa đúng.
  - Câu "Top-1 94.6%" là bịa.

### 09 CoVe
- PDF đúng.
- Lỗi nhỏ: venue ghi "TACL". Bản đã đăng của CoVe là Findings of ACL 2024.

### 10 Self-RAG, 11 CRITIC
- Đúng cả PDF và thông tin.

### 12 GASP
- **PDF trong folder:** bài vũ trụ học "Exploring new physics in the late Universe's expansion…" (2407.04223). Sai.
- **Thông tin đúng:** arXiv **2607.04223** (05/07/2026). Tác giả: Mohamed Aly Bouke (1 người).
- **Lỗi trong review:**
  - Năm 2024 và tác giả "Jiashuo Sun, Chengwei Hu, Yeyun Gong" là bịa, nên folder `12_Sun_2024_…` sai tên.
  - Review ghi "AUROC 89.4%", sai. Số thật: AUC khoảng 0.73 ở mức câu trả lời và khoảng 0.67 ở mức span, trên RAGTruth.
  - Phần cơ chế (bỏ từng đoạn ngữ cảnh rồi đo mức tụt log-likelihood) thì mô tả đúng.

### 13 Multi-Modal Fact-Verification
- **PDF trong folder:** "Novel Subsampling Strategies for Heavily Censored Reliability Data" (2410.22751, stat.ME). Sai.
- **Thông tin đúng:** arXiv **2510.22751** (26/10/2025). Tác giả: Piyushkumar Patel (1 người).
- **Lỗi trong review:**
  - Năm 2024 và tác giả "Lin Zhang, Wei Chen…" là bịa, nên folder `13_Zhang_2024_…` sai tên.
  - Review ghi "14.2% xuống 1.8%", sai. Số thật: giảm 67% ảo giác, chuyên gia chấm 89% đạt.

### 14 CRAG
- Đúng.

### 15 From BM25 to Corrective RAG
- **PDF trong folder:** "The Zoo of Combinatorial Banach Spaces" (2404.01733, math.FA). Sai.
- **Thông tin đúng:** arXiv **2604.01733** (02/04/2026). Tác giả: Meftun Akarsu, Recep Kaan Karaman, Christopher Mierbach.
- **Lỗi trong review:**
  - Năm 2024 và tác giả "Lucas P. Schmidt, Alexander C. Ramos" là bịa, nên folder `15_Schmidt_2024_…` sai tên.
  - Câu "BM25 + metadata filtering, độ trễ thấp hơn 8 lần" là bịa.
  - Kết quả thật: trên T²-RAGBench (23.088 câu hỏi, 7.318 tài liệu tài chính), hybrid kết hợp neural rerank cho kết quả tốt nhất (Recall@5 0.816, MRR@3 0.605). BM25 thắng dense. CRAG có giúp nhưng thua hybrid.

### 16 Multi-Agent Hybrid Retrieval (KDD)
- **PDF trong folder:** "A Hybrid RAG System with Comprehensive Enhancement on Complex Reasoning", Ye Yuan và cộng sự, Peking University (2408.05141). Cùng chủ đề nhưng là bài khác.
- **Thông tin đúng:** tác giả Hediyeh Baban, Sai Abhishek Pidaparthi, Samaksh Gulati, Aashutosh Nema (Dell Technologies). Bài đăng ở workshop GenAIRecP tại KDD 2025. PDF: `genai-personalization.github.io/assets/papers/GenAIRecP2025/11_Baban.pdf`.
- **Lỗi trong review:**
  - Tác giả "Hongyu Li, Zichen Liu…" là bịa, nên folder `16_Li_…` sai tên.
  - DOI 10.1145/3690624.3709332 chưa xác minh được, nhiều khả năng là bịa.
  - Nội dung thật: BM25 kết hợp tìm kiếm ngữ nghĩa, gộp bằng weighted cosine, LLM sắp xếp lại, chạy trên LangGraph, giảm độ trễ truy xuất 4 lần. Câu "tác tử SQL/FTS, RRF, tăng 28.4%" là bịa.

### 17 LegalMALR
- Đúng. Lỗi nhỏ: phân loại ghi cs.CL, PDF ghi cs.IR.

### 18 Fine-Tuning SLMs – Edge AI
- **PDF trong folder:** đúng bài (2503.01933).
- **Lỗi trong review:**
  - Tác giả thật là **Rakshit Aralimatti, Syed Abdul Gaffar Shakhadri, Kruthika KR, Kartik Basavaraj Angadi** (SandLogic). Review ghi "Srijan Das, Arghya Pal…", là bịa, nên folder `18_Das_…` sai tên.
  - Nội dung thật: dòng mô hình Shakti 100M, 250M và 500M. Các ý "1.5B–3B, GGUF/QLoRA, ngang 70B, RAM dưới 4GB, dưới 0.5s" là bịa.

### 19 Qwen2.5 Technical Report
- PDF và mã arXiv đúng.
- Review nói quá: câu "kỷ lục thế giới" và "hiểu tiếng Việt" không có trong báo cáo.

### 20 Unveiling the Secret Recipe
- **PDF trong folder:** "Distilling an End-to-End Voice Assistant Without Instruction Training Data" (DiVA, 2410.02678). Sai.
- **Thông tin đúng:** "Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs" (không có "on Domain Tasks"), arXiv **2412.13337** (17/12/2024). Tác giả: Aldo Pareja, Nikhil Shivakumar Nayak, Hao Wang và cộng sự, trưởng nhóm Akash Srivastava.
- **Lỗi trong review:**
  - Tác giả "Mayank Mishra…" là bịa, nên folder `20_Mishra_…` sai tên.
  - "Small" trong paper là mô hình 3B–7B, không phải 1.5B.
  - Câu "tuân thủ khuôn dạng 99.2%" là bịa.

## File khác bị ảnh hưởng

Có 3 bản `RESEARCH_PAPERS.md`: ở gốc repo, ở `Documentation/`, và ở `Documentation/research paper/`. Cả ba, cùng với `research paper/README.md`, chép lại các mã arXiv và tên tác giả sai ở trên. Chúng còn có sẵn câu trích dẫn mẫu dùng tên sai, ví dụ "(Schneider et al., 2026)", "(Guha et al., 2024)" và "(Champoux et al., 2026)". Nếu đưa các câu này vào báo cáo thì sẽ trích sai.

## Đã sửa (29/09/2026)

1. **PDF:** đã tải lại 12 PDF theo mã đúng (01–05, 07, 08, 12, 13, 15, 16, 20). Trang 1 của cả 20 PDF nay khớp với tên folder.
2. **Folder:** đã đổi tên 14 folder.
   - 10 folder mang tên tác giả sai: 05 `vanderMeer`, 06 `Pipitone`, 07 `Zhao`, 08 `Kalra`, 12 `Bouke_2026`, 13 `Patel_2025`, 15 `Akarsu_2026`, 16 `Baban`, 18 `Aralimatti`, 20 `Pareja`.
   - 4 folder 01–04 chỉ sửa năm, từ 2024 thành 2026.
3. **Tên file PDF:** đổi theo tiêu đề thật ở 05, 06 và 20.
4. **`literature_review.md`:** viết lại phần đầu và mục 1–4 theo abstract cùng kết quả trong PDF của cả 20 bài, bỏ các câu mẫu lặp lại. Mục 5 (liên hệ với V10.5) giữ nguyên.
5. **README và các bản `RESEARCH_PAPERS.md`:**
   - `README.md` và bản `RESEARCH_PAPERS.md` ở gốc repo được dựng lại. Link ở bản gốc repo trước đây gãy, nay đã trỏ đúng vào `Documentation/research paper/`.
   - Hai bản `RESEARCH_PAPERS.md` dài: sửa metadata, tóm tắt, bảng tổng hợp, câu trích dẫn mẫu, và tên tác giả trong khung bài báo.
   - Đã kiểm tra lại: 222 link tương đối đều trỏ tới file có thật, và không còn tên tác giả hay mã arXiv sai nào.
6. **Bản lưu trước khi sửa:** nằm ngoài repo. File zip toàn bộ bản cũ và 12 PDF sai được giữ trong thư mục tạm của phiên làm việc.

## Còn lại: nội dung về V10.5, chưa sửa

Các phần sau nói về dự án V10.5 chứ không nói về paper, nên cần nhóm quyết định:

- **Mục 5 của review, dòng "Ý nghĩa cho V10.5" và "Ánh xạ tới kiến trúc V10.5":**
  - Nhiều chỗ nhắc tới mã của V10.2.1 không có trong V10.5: `service.py`, `_authority_level`, `_pick_province_variant`, `search_f1`, `pipeline.py`, và kiểu "2 Turn / Customer Care".
  - Hai chỗ ánh xạ không có cơ sở trong paper:
    - 05 LegalCheck không bàn về phân cấp thẩm quyền Xã > Huyện > Tỉnh.
    - 20 là paper về fine-tuning, không bàn về thiết kế prompt hay mức "tăng tốc 4 lần".
- **Mục "Khung cấu trúc bài báo" trong `RESEARCH_PAPERS.md`:** có các số "1.55s xuống 0.38s", "0.38s/turn", "42.3% ảo giác so với 0%", "VRAM < 2GB". Không tìm thấy các số này trong code hay báo cáo V10.5. Lần đo ngày 24/09 cho thời gian trung bình 24.0 giây mỗi câu.

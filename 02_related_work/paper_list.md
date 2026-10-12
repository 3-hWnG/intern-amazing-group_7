# Paper List (Danh mục 33 Bài báo Khoa học theo 3 Nhóm Tiêu chí)

Toàn bộ tài liệu học thuật được phân loại theo 3 tiêu chí quy định:
- **Nhóm 1:** Bài báo liên quan trực tiếp — pháp lý, hành chính công, an toàn/quyền riêng tư khu vực công (Tối thiểu 5 bài - Hiện có: 12 bài)
- **Nhóm 2:** Bài báo về model AI hoặc phương pháp AI (Tối thiểu 3 bài - Hiện có: 19 bài)
- **Nhóm 3:** Bài báo về domain ứng dụng — rủi ro ảo giác pháp lý và kiểm soát hội thoại (Tối thiểu 2 bài - Hiện có: 2 bài)

**Nguồn công bố:** 29/33 bài đã công bố tại hội nghị/tạp chí có bình duyệt (ACL/EMNLP/NAACL/EACL, ICLR, NeurIPS, IEEE S&P, ACM AISec, SOSP, ICAIL, IC3K, IEEE Access, Journal of Legal Analysis, Journal of Empirical Legal Studies, workshop KDD/EMNLP). 4 bài là preprint/báo cáo kỹ thuật được giữ lại có ghi chú rõ vì là công trình gốc được trích dẫn rộng rãi: Paper 08 (LegalBench-RAG), Paper 18 (CRAG), Paper 22 (Qwen2.5 Technical Report), Paper 28 (Constitutional AI).

Mọi tóm tắt chi tiết (`paper_summaries/paper_XX.md`) được viết lại dựa trên toàn văn PDF lưu trong `docs/research paper/`; mọi link dưới đây đã được kiểm tra chéo với bài báo.

---

## PHẦN I: BÀI BÁO LIÊN QUAN TRỰC TIẾP (PAPERS 01 - 12)

### Paper 01: ViGPTQA – State-of-the-Art LLMs for Vietnamese Question Answering: System Overview, Core Models Training, and Evaluations
- **Tác giả:** Minh-Thuan Nguyen, Khanh-Tung Tran, Vincent Nguyen, Xuan-Son Vu
- **Năm & Nguồn:** 2023 | *EMNLP 2023 Industry*
- **DOI / Link:** https://aclanthology.org/2023.emnlp-industry.70/
- **Tệp tóm tắt:** `paper_summaries/paper_01.md`
- **Phương pháp & Dữ liệu:** Tinh chỉnh chỉ dẫn LLM tiếng Việt (ViGPT) + RAG | ViLawsQA (1.020 bộ, 27 lĩnh vực luật), ViTruthfulQA, MRC tiếng Việt
- **Đóng góp chính:** ViGPT-Law-v2 + ngữ cảnh chuẩn đạt ROUGE-1 45,33, điểm người 2,52; không có ngữ cảnh thì câu trả lời phần lớn không hữu ích.
- **Ý nghĩa với đề tài:** Khẳng định cần ngữ cảnh truy hồi khi hỏi đáp pháp luật tiếng Việt; định hướng chọn LLM hỗ trợ tốt tiếng Việt.

### Paper 02: Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems
- **Tác giả:** Pham Thi Xuan Hien, Duong Ngoc Thao Nhi, Pham Thi Ngoc Huyen
- **Năm & Nguồn:** 2025 | *IC3K/KMIS 2025*
- **DOI / Link:** https://doi.org/10.5220/0013751200004000
- **Tệp tóm tắt:** `paper_summaries/paper_02.md`
- **Phương pháp & Dữ liệu:** IR + LLM truy vấn văn bản pháp luật (RAG phân cấp) | 45.000 văn bản, 12 lĩnh vực; 2.000 cặp hỏi–đáp do chuyên gia xác nhận
- **Đóng góp chính:** Citation Accuracy 94,2% (baseline tốt nhất 81,2%); độ chính xác giảm theo độ phức tạp câu hỏi.
- **Ý nghĩa với đề tài:** Công trình gần nhất về RAG pháp luật Việt Nam; bài học trích dẫn điều khoản.

### Paper 03: Crossing Linguistic Horizons: Finetuning and Comprehensive Evaluation of Vietnamese Large Language Models
- **Tác giả:** Sang T. Truong, Duc Q. Nguyen, Toan Nguyen, Dong D. Le, Nhi N. Truong, Tho Quan, Sanmi Koyejo (Stanford University; Trường ĐH Bách khoa – ĐHQG TP.HCM)
- **Năm & Nguồn:** 2024 | *Findings NAACL 2024*
- **DOI / Link:** https://aclanthology.org/2024.findings-naacl.182/
- **Tệp tóm tắt:** `paper_summaries/paper_03.md`
- **Phương pháp & Dữ liệu:** Tinh chỉnh LLaMa-2 cho tiếng Việt, đánh giá toàn diện | Nhiều tác vụ tiếng Việt (QA, tóm tắt, phân loại, suy luận…), 31 chỉ số, 14 LLM
- **Đóng góp chính:** GPT-4 tốt nhất; mô hình tinh chỉnh vượt LLaMa-2 nền; kích thước không quyết định.
- **Ý nghĩa với đề tài:** Cơ sở chọn và đánh giá LLM cho tiếng Việt (Qwen2.5 trong Sys_3_4).

### Paper 04: Improving Vietnamese-English Cross-Lingual Retrieval for Legal and General Domains
- **Tác giả:** Toan Ngoc Nguyen, Nam Le Hai, Nguyen Doan Hieu, Dai An Nguyen, Linh Ngo Van, Thien Huu Nguyen, Sang Dinh (BKAI – ĐH Bách khoa Hà Nội; University of Oregon)
- **Năm & Nguồn:** 2025 | *NAACL 2025 (short)*
- **DOI / Link:** https://aclanthology.org/2025.naacl-short.12/
- **Tệp tóm tắt:** `paper_summaries/paper_04.md`
- **Phương pháp & Dữ liệu:** Tinh chỉnh BGE-M3 xuyên ngôn ngữ + dữ liệu tổng hợp | VNLawQC, VNSynLawQC, ZaloLegal2021, ZaloWikipediaQA
- **Đóng góp chính:** VNLawQC Việt–Anh 42,99 → 69,75; ZaloLegal2021 53,63 → 80,55.
- **Ý nghĩa với đề tài:** Trực tiếp liên quan BGE-M3 trong Friendly Engine; tinh chỉnh embedding cho văn bản pháp luật.

### Paper 05: Analyzing Leakage of Personally Identifiable Information in Language Models
- **Tác giả:** Nils Lukas, Ahmed Salem, Robert Sim, Shruti Tople, Lukas Wutschitz, Santiago Zanella-Béguelin (University of Waterloo; Microsoft)
- **Năm & Nguồn:** 2023 | *IEEE S&P 2023*
- **DOI / Link:** https://doi.org/10.1109/SP46215.2023.10179300
- **Tệp tóm tắt:** `paper_summaries/paper_05.md`
- **Phương pháp & Dữ liệu:** Tấn công trích xuất/tái tạo/suy luận PII; đánh giá scrubbing và DP | ECHR, Enron, Yelp-Health; GPT-2
- **Đóng góp chính:** Không phòng vệ: precision 29,56%, recall 22,96%; DP ε=8 còn khoảng 3%; scrubbing dựa trên NER không hoàn hảo.
- **Ý nghĩa với đề tài:** Cơ sở cho che PII và chạy on-prem trong tầng policy.

### Paper 06: Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection
- **Tác giả:** Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, Mario Fritz (Saarland University; sequire technology; CISPA Helmholtz Center for Information Security)
- **Năm & Nguồn:** 2023 | *AISec '23 (ACM CCS)*
- **DOI / Link:** https://doi.org/10.1145/3605764.3623985
- **Tệp tóm tắt:** `paper_summaries/paper_06.md`
- **Phương pháp & Dữ liệu:** Phân loại và minh họa tấn công chèn lệnh gián tiếp | Không có bộ dữ liệu (proof-of-concept)
- **Đóng góp chính:** Chứng minh dữ liệu truy hồi có thể điều khiển LLM: đánh cắp dữ liệu, lừa đảo, lan truyền.
- **Ý nghĩa với đề tài:** Cơ sở cho lớp chống prompt injection và cách ly ngữ cảnh truy hồi.

### Paper 07: LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters
- **Tác giả:** Virgill van der Meer (Municipality of Amsterdam), Julien Rossi (University of Amsterdam)
- **Năm & Nguồn:** 2026 | *ICAIL 2026 (short)*
- **DOI / Link:** https://arxiv.org/abs/2605.12012
- **Tệp tóm tắt:** `paper_summaries/paper_07.md`
- **Phương pháp & Dữ liệu:** Retrieval- và Context-Augmented Generation soạn thư tư vấn pháp lý | ~23.500 thư 2022–2025, 4 lĩnh vực xử phạt
- **Đóng góp chính:** F1 92%; tiết kiệm 92% thời gian soạn thảo; giảm 50–70% tổng thời gian.
- **Ý nghĩa với đề tài:** Ví dụ triển khai thực tế ở chính quyền địa phương có người kiểm duyệt.

### Paper 08: LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain
- **Tác giả:** Nicholas Pipitone, Ghita Houir Alami (ZeroEntropy)
- **Năm & Nguồn:** 2024 | *arXiv preprint (giữ lại)* — preprint/báo cáo kỹ thuật, chưa bình duyệt
- **DOI / Link:** https://arxiv.org/abs/2408.10343
- **Tệp tóm tắt:** `paper_summaries/paper_08.md`
- **Phương pháp & Dữ liệu:** Benchmark truy hồi đoạn chính xác trong văn bản pháp lý | ContractNLI, CUAD, MAUD, PrivacyQA (6.889 truy vấn)
- **Đóng góp chính:** Recall@64 tối đa 76,39% (chia cố định); rerank Cohere không cải thiện.
- **Ý nghĩa với đề tài:** Gợi ý đánh giá truy hồi ở mức đoạn/trường.

### Paper 09: Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools
- **Tác giả:** Varun Magesh, Faiz Surani, Matthew Dahl, Mirac Suzgun, Christopher D. Manning, Daniel E. Ho (Stanford University; Yale University)
- **Năm & Nguồn:** 2025 | *JELS 2025*
- **DOI / Link:** https://doi.org/10.1111/jels.12413
- **Tệp tóm tắt:** `paper_summaries/paper_09.md`
- **Phương pháp & Dữ liệu:** Đánh giá thực nghiệm công cụ RAG pháp lý thương mại | 202 truy vấn pháp lý Hoa Kỳ đăng ký trước
- **Đóng góp chính:** Lexis+ AI và Practical Law ảo giác >1/6, Westlaw ~1/3 dù dùng RAG.
- **Ý nghĩa với đề tài:** Bằng chứng RAG không loại bỏ ảo giác pháp lý → cần verifier.

### Paper 10: HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications
- **Tác giả:** Rishi Kalra, Zekun Wu, Ayesha Gulley, Airlie Hilliard, Xin Guan, Adriano Koshiyama, Philip Treleaven (Holistic AI; University College London)
- **Năm & Nguồn:** 2025 (preprint đầu tiên 9/2024) | *NAACL 2025 Industry*
- **DOI / Link:** https://aclanthology.org/2025.naacl-industry.79/
- **Tệp tóm tắt:** `paper_summaries/paper_10.md`
- **Phương pháp & Dữ liệu:** Phân loại độ phức tạp → điều chỉnh tham số truy hồi lai + KG | LL144 (15 trang), bộ câu hỏi sinh bằng GPT-3.5/Giskard
- **Đóng góp chính:** DistilBERT phân loại F1 0,90; LLM không truy hồi Correctness chỉ 0,20–0,46.
- **Ý nghĩa với đề tài:** Ý tưởng điều chỉnh top-k theo độ phức tạp câu hỏi.

### Paper 11: Legal Query RAG (LQ-RAG)
- **Tác giả:** Rahman S. M. Wahidur, Sumin Kim, Haeung Choi, David S. Bhatti, Heung-No Lee (Gwangju Institute of Science and Technology – GIST, Hàn Quốc)
- **Năm & Nguồn:** 2025 | *IEEE Access 2025*
- **DOI / Link:** https://doi.org/10.1109/ACCESS.2025.3542125
- **Tệp tóm tắt:** `paper_summaries/paper_11.md`
- **Phương pháp & Dữ liệu:** RAG có tác tử đánh giá phản hồi + tinh chỉnh embedding/LLM | 7 bộ truy hồi tự xây; benchmark tổng quát và pháp lý
- **Đóng góp chính:** HFM cải thiện 9% (tổng quát) và 38% (pháp lý); kém ở một số bộ.
- **Ý nghĩa với đề tài:** Vòng phản hồi viết lại truy vấn; cảnh báo chi phí độ trễ.

### Paper 12: STARD: A Chinese Statute Retrieval Dataset Derived from Real-life Queries by Non-professionals
- **Tác giả:** Weihang Su, Yiran Hu, Anzhe Xie, Qingyao Ai, Zibing Que, Ning Zheng, Yun Liu, Weixing Shen, Yiqun Liu (Đại học Thanh Hoa; Đại học Bắc Kinh)
- **Năm & Nguồn:** 2024 | *Findings EMNLP 2024*
- **DOI / Link:** https://aclanthology.org/2024.findings-emnlp.625/
- **Tệp tóm tắt:** `paper_summaries/paper_12.md`
- **Phương pháp & Dữ liệu:** Benchmark truy hồi điều luật; gán nhãn 3 bước Recall/Decomposition/Filter | 1.543 câu hỏi thật, 55.348 điều luật
- **Đóng góp chính:** Dense-STARD R@100 0,9065; BM25 0,6493; PLM pháp lý zero-shot thấp hơn lexical.
- **Ý nghĩa với đề tài:** Mẫu quy trình gán nhãn và bộ đánh giá cho câu hỏi đời thường → điều khoản thủ tục.

---

## PHẦN II: BÀI BÁO VỀ MODEL AI HOẶC PHƯƠNG PHÁP AI (PAPERS 13 - 31)

### Paper 13: Chain-of-Verification Reduces Hallucination in Large Language Models (CoVe)
- **Tác giả:** Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, Roberta Raileanu, Xian Li, Asli Celikyilmaz, Jason Weston (Meta AI; ETH Zürich)
- **Năm & Nguồn:** 2024 (preprint 9/2023) | *Findings ACL 2024*
- **DOI / Link:** https://aclanthology.org/2024.findings-acl.212/
- **Tệp tóm tắt:** `paper_summaries/paper_13.md`
- **Phương pháp & Dữ liệu:** Lập kế hoạch câu hỏi kiểm chứng → trả lời độc lập → sửa | Wikidata, Wiki-Category, MultiSpanQA, tiểu sử
- **Đóng góp chính:** Precision Wikidata 0,17 → 0,36; FActScore 55,9 → 71,4.
- **Ý nghĩa với đề tài:** Ý tưởng kiểm chứng từng điểm sau sinh (verify_point).

### Paper 14: Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
- **Tác giả:** Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi (University of Washington; Allen Institute for AI; IBM Research AI)
- **Năm & Nguồn:** 2024 (preprint 10/2023) | *ICLR 2024 (oral)*
- **DOI / Link:** https://proceedings.iclr.cc/paper_files/paper/2024/hash/25f7be9694d7b32d5cc670927b8091e1-Abstract-Conference.html
- **Tệp tóm tắt:** `paper_summaries/paper_14.md`
- **Phương pháp & Dữ liệu:** Huấn luyện LLM sinh reflection token quyết định truy hồi và tự phê bình | 150K mẫu huấn luyện; PopQA, PubHealth, ARC, TriviaQA, ASQA, tiểu sử
- **Đóng góp chính:** Self-RAG 13B: PopQA 55,8; FactScore 80,2; citation precision 70,3.
- **Ý nghĩa với đề tài:** Đối chứng giữa tự phê bình học được và verifier tất định.

### Paper 15: CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing
- **Tác giả:** Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen (Tsinghua University; Microsoft Research Asia; Microsoft Azure AI)
- **Năm & Nguồn:** 2024 | *ICLR 2024*
- **DOI / Link:** https://proceedings.iclr.cc/paper_files/paper/2024/hash/fef126561bbf9d4467dbb8d27334b8fe-Abstract-Conference.html
- **Tệp tóm tắt:** `paper_summaries/paper_15.md`
- **Phương pháp & Dữ liệu:** Vòng xác minh → phê bình → sửa dùng công cụ ngoài | AmbigNQ, TriviaQA, HotpotQA, GSM8k, SVAMP, TabMWP, RealToxicityPrompts
- **Đóng góp chính:** ChatGPT AmbigNQ F1 64,3 → 74,9; tự sửa không công cụ có thể làm kết quả xấu đi.
- **Ý nghĩa với đề tài:** Củng cố việc kiểm chứng phải dựa vào nguồn ngoài (CSDL thủ tục), không tự phán.

### Paper 16: RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models
- **Tác giả:** Cheng Niu, Yuanhao Wu, Juno Zhu, Siliang Xu, Kashun Shum, Randy Zhong, Juntong Song, Tong Zhang (NewsBreak; University of Illinois Urbana-Champaign)
- **Năm & Nguồn:** 2024 | *ACL 2024*
- **DOI / Link:** https://aclanthology.org/2024.acl-long.585/
- **Tệp tóm tắt:** `paper_summaries/paper_16.md`
- **Phương pháp & Dữ liệu:** Kho chú thích ảo giác mức span cho đầu ra RAG | 2.965 mẫu, 17.790 câu trả lời, 14.289 span
- **Đóng góp chính:** 43,1% câu trả lời có ảo giác; data-to-text cao nhất (68,6%).
- **Ý nghĩa với đề tài:** Mô hình đánh giá ảo giác cho Friendly Engine; data-to-text tương tự bảng lệ phí.

### Paper 17: FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation
- **Tác giả:** Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Wei Koh, Mohit Iyyer, Luke Zettlemoyer, Hannaneh Hajishirzi (University of Washington; UMass Amherst; Allen Institute for AI; Meta AI)
- **Năm & Nguồn:** 2023 | *EMNLP 2023*
- **DOI / Link:** https://aclanthology.org/2023.emnlp-main.741/
- **Tệp tóm tắt:** `paper_summaries/paper_17.md`
- **Phương pháp & Dữ liệu:** Tách sự kiện nguyên tử, kiểm tra với nguồn tri thức | Tiểu sử 183 người (thủ công), 500 người (tự động)
- **Đóng góp chính:** ChatGPT 58,3%; PerplexityAI 71,5%; chính xác giảm mạnh với thực thể hiếm.
- **Ý nghĩa với đề tài:** Thước đo phân rã sự kiện cho đánh giá câu trả lời thủ tục.

### Paper 18: Corrective Retrieval Augmented Generation (CRAG)
- **Tác giả:** Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling (University of Science and Technology of China; UCLA; Google DeepMind)
- **Năm & Nguồn:** 2024 | *arXiv preprint (giữ lại)* — preprint/báo cáo kỹ thuật, chưa bình duyệt
- **DOI / Link:** https://arxiv.org/abs/2401.15884
- **Tệp tóm tắt:** `paper_summaries/paper_18.md`
- **Phương pháp & Dữ liệu:** Bộ đánh giá truy hồi → Correct/Incorrect/Ambiguous → tìm bổ sung | PopQA, Biography, PubHealth, ARC
- **Đóng góp chính:** RAG → CRAG: PopQA 52,8 → 59,8; PubHealth 39,0 → 75,6.
- **Ý nghĩa với đề tài:** Ý tưởng chấm độ tin cậy truy hồi trước khi sinh.

### Paper 19: M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation
- **Tác giả:** Jianlv Chen, Shitao Xiao, Peitian Zhang, Kun Luo, Defu Lian, Zheng Liu (BAAI; Đại học Khoa học và Công nghệ Trung Quốc)
- **Năm & Nguồn:** 2024 | *Findings ACL 2024*
- **DOI / Link:** https://aclanthology.org/2024.findings-acl.137/
- **Tệp tóm tắt:** `paper_summaries/paper_19.md`
- **Phương pháp & Dữ liệu:** Một mô hình cho 3 kiểu truy xuất, self-knowledge distillation, 8.192 token | 1,2 tỷ cặp không nhãn + dữ liệu có nhãn; MIRACL, MKQA, MLDR
- **Đóng góp chính:** MIRACL nDCG@10 All 71,5 (dense 69,2); MKQA vi R@100 76,9.
- **Ý nghĩa với đề tài:** Nền tảng BGE-M3 của Friendly Engine; cơ sở cho truy hồi lai.

### Paper 20: Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval
- **Tác giả:** Hediyeh Baban, Sai Abhishek Pidaparthi, Samaksh Gulati, Aashutosh Nema (Dell Technologies)
- **Năm & Nguồn:** 2025 | *GenAIRecP @ KDD 2025*
- **DOI / Link:** https://genai-personalization.github.io/assets/papers/GenAIRecP2025/11_Baban.pdf
- **Tệp tóm tắt:** `paper_summaries/paper_20.md`
- **Phương pháp & Dữ liệu:** Tác tử điều phối BM25 + embedding, tự điều chỉnh trọng số | 100.000 tài liệu, 500 truy vấn chú thích
- **Đóng góp chính:** Top-10 85% → 92%; độ trễ 43 s → 11 s; trọng số BM25/embedding 30/70 tốt nhất.
- **Ý nghĩa với đề tài:** Tham khảo cân bằng sparse/dense; RRF trong Sys_3_4.

### Paper 21: QLoRA: Efficient Finetuning of Quantized LLMs
- **Tác giả:** Tim Dettmers, Artidoro Pagnoni, Ari Holtzman, Luke Zettlemoyer (University of Washington)
- **Năm & Nguồn:** 2023 | *NeurIPS 2023*
- **DOI / Link:** https://proceedings.neurips.cc/paper_files/paper/2023/hash/1feb87871436031bdc0f2beaa62a049b-Abstract-Conference.html
- **Tệp tóm tắt:** `paper_summaries/paper_21.md`
- **Phương pháp & Dữ liệu:** NF4 + double quantization + paged optimizer + LoRA | GLUE, Super-NaturalInstructions, MMLU, 8 bộ chỉ dẫn
- **Đóng góp chính:** NF4 + DQ tái tạo hiệu năng 16-bit (MMLU 53,1 vs 53,0); Guanaco 7B cần 5GB.
- **Ý nghĩa với đề tài:** Khả thi tinh chỉnh Qwen2.5 trên GPU on-prem.

### Paper 22: Qwen2.5 Technical Report
- **Tác giả:** Qwen Team (Alibaba Group) — An Yang, Baosong Yang, Beichen Zhang và cộng sự
- **Năm & Nguồn:** 2024 (bản v2: 1/2025) | *Technical report (giữ lại)* — preprint/báo cáo kỹ thuật, chưa bình duyệt
- **DOI / Link:** https://arxiv.org/abs/2412.15115
- **Tệp tóm tắt:** `paper_summaries/paper_22.md`
- **Phương pháp & Dữ liệu:** Tiền huấn luyện 18T token + hậu huấn luyện SFT/RL | Benchmark mở + nội bộ (dữ liệu huấn luyện không công bố)
- **Đóng góp chính:** Qwen2.5-7B-Instruct vượt Gemma2-9B và Llama3.1-8B (trừ IFEval).
- **Ý nghĩa với đề tài:** Tài liệu chính thức của mô hình dùng trong Friendly Engine.

### Paper 23: Unveiling the Secret Recipe: A Guide for Supervised Fine-Tuning Small LLMs
- **Tác giả:** Aldo Pareja, Nikhil Shivakumar Nayak, Hao Wang, Krishnateja Killamsetty, Shivchander Sudalairaj, Wenlong Zhao, Seungwook Han, Abhishek Bhandwaldar, Guangxuan Xu, Kai Xu, Ligong Han, Luke Inglis, Akash Srivastava (Red Hat AI Innovation; MIT-IBM Watson AI Lab; IBM Research; MIT; UMass Amherst)
- **Năm & Nguồn:** 2025 (preprint 12/2024) | *ICLR 2025*
- **DOI / Link:** https://iclr.cc/virtual/2025/poster/28940
- **Tệp tóm tắt:** `paper_summaries/paper_23.md`
- **Phương pháp & Dữ liệu:** Nghiên cứu thực nghiệm siêu tham số SFT cho LLM 3B–7B | Dữ liệu tổng hợp theo taxonomy LAB
- **Đóng góp chính:** Batch lớn + LR thấp tổng quát tốt hơn; stacked ≈ phased nhưng ít mẫu hơn.
- **Ý nghĩa với đề tài:** Hướng dẫn nếu nhóm tinh chỉnh Qwen2.5 cho thủ tục hành chính.

### Paper 24: GPTCache: An Open-Source Semantic Cache for LLM Applications Enabling Faster Answers and Cost Savings
- **Tác giả:** Bang Fu, Di Feng (Zilliz Inc.)
- **Năm & Nguồn:** 2023 | *NLP-OSS 2023 (EMNLP)*
- **DOI / Link:** https://aclanthology.org/2023.nlposs-1.24/
- **Tệp tóm tắt:** `paper_summaries/paper_24.md`
- **Phương pháp & Dữ liệu:** Cache truy vấn bằng embedding + bộ đánh giá tương đồng | Cặp câu tự tạo bằng ChatGPT (30.000 khóa)
- **Đóng góp chính:** 876/1.000 trúng (39 sai); độ trễ khi trúng ~0,2 s.
- **Ý nghĩa với đề tài:** Cảnh báo rủi ro trả nhầm thủ tục tương tự khi dùng cache.

### Paper 25: RouteLLM: Learning to Route LLMs with Preference Data
- **Tác giả:** Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu, Joseph E. Gonzalez, M Waleed Kadous, Ion Stoica (UC Berkeley; Anyscale; Canva)
- **Năm & Nguồn:** 2025 (preprint 6/2024) | *ICLR 2025*
- **DOI / Link:** https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html
- **Tệp tóm tắt:** `paper_summaries/paper_25.md`
- **Phương pháp & Dữ liệu:** Router học từ dữ liệu ưu tiên chọn mô hình mạnh/yếu | Chatbot Arena + tăng cường; MMLU, MT Bench, GSM8K
- **Đóng góp chính:** Matrix factorization APGR 0,802 trên MT Bench; cần dữ liệu trong miền.
- **Ý nghĩa với đề tài:** Cơ sở cho định tuyến Strict/Friendly Engine.

### Paper 26: Efficient Memory Management for Large Language Model Serving with PagedAttention (vLLM)
- **Tác giả:** Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin Zheng, Cody Hao Yu, Joseph E. Gonzalez, Hao Zhang, Ion Stoica (UC Berkeley; Stanford; UC San Diego)
- **Năm & Nguồn:** 2023 | *SOSP 2023*
- **DOI / Link:** https://doi.org/10.1145/3600006.3613165
- **Tệp tóm tắt:** `paper_summaries/paper_26.md`
- **Phương pháp & Dữ liệu:** PagedAttention quản lý KV cache theo trang | Tải công việc từ ShareGPT, Alpaca
- **Đóng góp chính:** Thông lượng cao hơn 2–4 lần so với hệ thống trước.
- **Ý nghĩa với đề tài:** Nền tảng phục vụ Qwen2.5 on-prem (vLLM).

### Paper 27: Nougat: Neural Optical Understanding for Academic Documents
- **Tác giả:** Lukas Blecher, Guillem Cucurull, Thomas Scialom, Robert Stojnic (Meta AI)
- **Năm & Nguồn:** 2024 (preprint 8/2023) | *ICLR 2024*
- **DOI / Link:** https://proceedings.iclr.cc/paper_files/paper/2024/hash/a39a9aceda771cded859ae7560530e09-Abstract-Conference.html
- **Tệp tóm tắt:** `paper_summaries/paper_27.md`
- **Phương pháp & Dữ liệu:** Transformer ảnh → markup (Swin + mBART) | arXiv, PubMed Central, Industry Documents
- **Đóng góp chính:** F1 93,1; bảng F1 78,0; lặp ở 1,5% trang.
- **Ý nghĩa với đề tài:** Tham khảo trích xuất bảng biểu từ văn bản thủ tục.

### Paper 28: Constitutional AI: Harmlessness from AI Feedback
- **Tác giả:** Yuntao Bai, Saurav Kadavath, Sandipan Kundu, Amanda Askell, … , Jared Kaplan (Anthropic; 51 tác giả)
- **Năm & Nguồn:** 2022 | *arXiv preprint (giữ lại)* — preprint/báo cáo kỹ thuật, chưa bình duyệt
- **DOI / Link:** https://arxiv.org/abs/2212.08073
- **Tệp tóm tắt:** `paper_summaries/paper_28.md`
- **Phương pháp & Dữ liệu:** SL tự phê bình/sửa + RLAIF theo bộ nguyên tắc | 182.831 prompt red team; 135.296 prompt hữu ích
- **Đóng góp chính:** RL-CAI vô hại hơn ở cùng mức hữu ích so với HH-RLHF.
- **Ý nghĩa với đề tài:** Tinh thần nguyên tắc tường minh trong tầng policy.

### Paper 29: DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines
- **Tác giả:** Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav Santhanam, Sri Vardhamanan, Saiful Haq, Ashutosh Sharma, Thomas T. Joshi, Hanna Moazam, Heather Miller, Matei Zaharia, Christopher Potts
- **Năm & Nguồn:** 2024 (bản arXiv v1: 10/2023) | *ICLR 2024*
- **DOI / Link:** https://proceedings.iclr.cc/paper_files/paper/2024/hash/f1cf02ce09757f57c3b93c0db83181e0-Abstract-Conference.html
- **Tệp tóm tắt:** `paper_summaries/paper_29.md`
- **Phương pháp & Dữ liệu:** Signature – module – teleprompter tự tối ưu demo/prompt | GSM8K, HotPotQA (200 train/300 dev)
- **Đóng góp chính:** GPT-3.5 vượt few-shot >25%, llama2-13b >65%; GSM8K CoT ensemble 88,3% dev.
- **Ý nghĩa với đề tài:** Tối ưu prompt/demo cho các bước Friendly Engine.

### Paper 30: ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs
- **Tác giả:** Yujia Qin, Shihao Liang, Yining Ye, Kunlun Zhu, Lan Yan, Yaxi Lu, Yankai Lin, Xin Cong, Xiangru Tang, Bill Qian, Sihan Zhao, Lauren Hong, Runchu Tian, Ruobing Xie, Jie Zhou, Mark Gerstein, Dahai Li, Zhiyuan Liu, Maosong Sun (Tsinghua University, Yale, Renmin University, Tencent WeChat AI…)
- **Năm & Nguồn:** 2024 (bản arXiv v2: 10/2023) | *ICLR 2024*
- **DOI / Link:** https://proceedings.iclr.cc/paper_files/paper/2024/hash/28e50ee5b72e90b50e7196fde8ea260e-Abstract-Conference.html
- **Tệp tóm tắt:** `paper_summaries/paper_30.md`
- **Phương pháp & Dữ liệu:** ToolBench + DFSDT + API retriever + ToolLLaMA | 16.464 API, 126.486 cặp chỉ dẫn–lời giải; APIBench
- **Đóng góp chính:** ToolLLaMA-DFSDT pass 66,7 (ChatGPT-DFSDT 64,8); retriever NDCG@5 84,9 vs BM25 17,0.
- **Ý nghĩa với đề tài:** Chọn thủ tục/công cụ đúng từ kho lớn; giới hạn hành động của LLM.

### Paper 31: RAGAS: Automated Evaluation of Retrieval Augmented Generation
- **Tác giả:** Shahul Es, Jithin James (Exploding Gradients), Luis Espinosa-Anke, Steven Schockaert (CardiffNLP, Cardiff University; AMPLYFI)
- **Năm & Nguồn:** 2024 | *EACL 2024 Demo*
- **DOI / Link:** https://aclanthology.org/2024.eacl-demo.16/
- **Tệp tóm tắt:** `paper_summaries/paper_31.md`
- **Phương pháp & Dữ liệu:** Faithfulness, Answer Relevance, Context Relevance không cần tham chiếu | WikiEval (50 trang Wikipedia)
- **Đóng góp chính:** Faithfulness 0,95; Answer Rel. 0,78; Context Rel. 0,70 (vượt GPT Score/Ranking).
- **Ý nghĩa với đề tài:** Thước đo cho Friendly Engine (RQ1, RQ3).

---

## PHẦN III: BÀI BÁO VỀ DOMAIN ỨNG DỤNG (PAPERS 32 - 33)

### Paper 32: Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models
- **Tác giả:** Matthew Dahl (Yale), Varun Magesh, Mirac Suzgun, Daniel E. Ho (Stanford University, RegLab)
- **Năm & Nguồn:** 2024 | *Journal of Legal Analysis 2024*
- **DOI / Link:** https://doi.org/10.1093/jla/laae003
- **Tệp tóm tắt:** `paper_summaries/paper_32.md`
- **Phương pháp & Dữ liệu:** 14 tác vụ truy vấn án lệ; có/không tham chiếu; phản sự thật; ECE | 5.000 vụ án mỗi cấp tòa liên bang Hoa Kỳ; >800.000 truy vấn
- **Đóng góp chính:** Ảo giác 58% (GPT-4) đến 88% (Llama 2); thường chấp nhận tiền đề sai; tự tin quá mức.
- **Ý nghĩa với đề tài:** Bằng chứng không để LLM tự trả lời từ kiến thức tham số; cần clarify và verifier.

### Paper 33: NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails
- **Tác giả:** Traian Rebedea, Razvan Dinu, Makesh Sreedhar, Christopher Parisien, Jonathan Cohen (NVIDIA)
- **Năm & Nguồn:** 2023 | *EMNLP 2023 Demo*
- **DOI / Link:** https://aclanthology.org/2023.emnlp-demo.40/
- **Tệp tóm tắt:** `paper_summaries/paper_33.md`
- **Phương pháp & Dữ liệu:** Rail lập trình bằng Colang; topical/execution rails (fact-check, hallucination, moderation) | Banking (231 mẫu), Anthropic Red-Teaming/Helpful, MS MARCO, 20 câu tiền đề sai
- **Đóng góp chính:** Chặn gần 99% prompt có hại, 2% hữu ích; hallucination rail 65% → 95%.
- **Ý nghĩa với đề tài:** Tham chiếu gần nhất cho tầng policy của Sys_3_4.

# Lọc bản draft cũ: giữ gì, bỏ gì (bước a)

Bản draft cũ:

- `docs/research_paper.md` của repo gốc;
- bản LaTeX: `07_paper_draft/full_paper.tex` của NCKH-LongT/chatbot-thutuc-g7;
- danh sách sửa trước đó: `docs/SUA_SLIDE_VA_BAI_BAO.md`.

Bài mới **không sửa tiếp bản cũ**. Bài mới viết lại từ đầu, chỉ lấy những ý dưới đây kèm nguồn đỡ cho từng ý.

## 1. Ý giữ lại

| # | Ý (bản cũ) | Dùng ở đâu | Đỡ bằng gì |
|---|---|---|---|
| K1 | Người dân hỏi thủ tục cấp xã bằng lời thường: không dấu, viết tắt, kể hoàn cảnh dài, hỏi nhiều ý | Introduction | **Số của nhóm**: tỷ lệ câu dài, không dấu, nhiều ý trong real_v1/real_v2 (cần đếm). Ví dụ đã che thông tin cá nhân, chỉ trích vài chữ. LegalMALR2026 nói câu hỏi pháp lý thật thường "ngầm, nhiều vấn đề" |
| K2 | Sai về phí, thời hạn, cơ quan làm thủ tục thì có hậu quả thật, nên không được bịa | Introduction | GovAIPipe2026, GripOnLLMs2026 (rủi ro của LLM ở khu vực công); Wen2025 (vì sao cần từ chối) |
| K3 | Cơ quan nhà nước cần chạy tại chỗ, không gửi dữ liệu người dân ra ngoài | Introduction, Setup | GuidaPA2026; cấu hình thật: model 4B qua Ollama trên một máy |
| K4 | Cổng DVC có dữ liệu thủ tục có cấu trúc (hồ sơ, phí, thời hạn, căn cứ) | Data | Dữ liệu bản 3: 1.517 thủ tục, 34 tỉnh, cào 13/10/2026, sha256 trong `data/snapshot/SOURCE.md` |
| K5 | Model 4B làm planner đã bị tắt vì tự báo độ chắc chắn cao kể cả khi sai | Chỉ ở Discussion, nếu dùng | Phát hiện cũ (`eval/P19_REPORT.md`) đo trên bộ nhóm tự viết. Ưu tiên dùng kết quả mới: C một mình trên real_v2 |
| K6 | Phí chỉ được công bố cho một phần thủ tục; hệ thống nói "cổng không công bố" thay vì bịa | Data, Discussion | Bản 3: 549/1.517 thủ tục có phí (36,2%), 170 thủ tục có số tiền cụ thể. Phải đếm lại trên DB trước khi ghi |
| K7 | Lời định vị: không đề xuất model mới mà ghép model có sẵn với luật | Introduction | Khuôn môn (constraints.md B9) |

## 2. Ý và số phải bỏ

| # | Bản cũ nói | Vì sao bỏ |
|---|---|---|
| X1 | GPTCache trên Redis, RouteLLM, vLLM / PagedAttention, MCP, Nougat | Code không có. Chạy bằng Ollama, `qwen3:4b-instruct-2507` (q4_K_M), không vLLM, không MCP |
| X2 | "Zero-hallucination", "eliminates phantom contamination", "enterprise-grade", "production-ready" | Khẳng định tuyệt đối, không có phép đo trên câu thật (constraints.md C1.2) |
| X3 | Top-1 75,3% HOLDOUT-4, 96,3% DEV, hành vi 82,1% / 97,6% | Đo trên bộ nhóm tự viết và dữ liệu cũ 1.350 thủ tục. Bài mới dùng số trên câu thật real_v2. Bộ tự viết chỉ dùng để chỉ ra khoảng cách (RQ1) |
| X4 | Bảng 4.1 xếp hạng hệ thống của nhóm cạnh ViGPTQA, LegalBench-RAG, CRAG, Self-RAG… | So số trên các bộ dữ liệu và nhiệm vụ khác nhau (constraints.md C3.1). Chỉ được làm bảng định tính |
| X5 | Độ trễ "20–33 ms" | Chỉ đúng khi một người dùng và chỉ chạy luật. 10 người dùng: p50 0,31 s, p95 1,18 s. Nếu nêu thì nêu cả hai |
| X6 | "7/10 PASS" bộ đội nhóm, "Numerical hallucination 3,4% / 0,0%" | Bộ 10 câu, không có giao thức khoá. Phép đo "hallucination" không có định nghĩa rõ |
| X7 | Hai engine (Strict + Friendly) là đóng góp chính | Friendly là bài 2 (constraints.md D1) |
| X8 | Các số trích của bài khác ở mục 2 bản cũ (vd. "GPT-3.5 68,5% EM", "AUROC 0,892", "ROUGE-1 61,10%") | Chưa ai đối chiếu với bảng gốc. Nhiều số trông như bịa. Chỉ lấy lại số nào đã đọc được trong PDF, kèm số bảng |

## 3. Kiểm từng tài liệu của bản cũ

Đối chiếu trích dẫn trong bản cũ với PDF trong `docs/research paper/` (trang đầu) và với web.

**Ít nhất 11 trích dẫn sai mã, sai tác giả hoặc sai nơi đăng.** Tất cả được đánh dấu "Sai" trong cột Kiểm của bảng dưới.

| # | Bản cũ ghi | Thực tế | Kiểm | Bài 1 |
|---|---|---|---|---|
| 1 | GuidaPA, arXiv:2606.01386 | Đúng | Đúng | Giữ (K3) |
| 2 | GovAI-Pipe, *Proc. dg.o 2026* | arXiv:2606.01417; chưa thấy bản dg.o | Sai nơi đăng | Giữ, cite arXiv |
| 3 | Grip-on-LLMs, *GIQ 2026* | arXiv:2608.09925; chưa thấy bản GIQ | Sai nơi đăng | Giữ, cite arXiv |
| 4 | COPAL, *ACM TOCHI 2026* | arXiv:2606.04394; chưa thấy bản TOCHI | Sai nơi đăng | Có thể giữ |
| 5 | LegalCheck, *ICAIL 2026* | arXiv:2605.12012; PDF có khối bản quyền của ACM, ICAIL chưa kiểm | Chờ | Có thể giữ |
| 6 | LegalBench-RAG, arXiv:2408.10343 | Đúng (Pipitone, Houir Alami) | Đúng | Bỏ (để bài 2) |
| 7 | CanLegalRAGBench, "R. Zhao", arXiv:2602.04912 | Ethan Zhao et al., arXiv:2605.30497 | Sai | Bỏ |
| 8 | HyPA-RAG, arXiv:2404.11234 | arXiv:2409.09046 | Sai | Bỏ |
| 9 | CoVe, arXiv:2309.11495 | Đúng | Đúng | Bỏ |
| 10 | Self-RAG, ICLR 2024 | arXiv:2310.11511; nơi đăng ICLR chờ kiểm | Đúng mã | Có thể giữ |
| 11 | CRITIC, ICLR 2024 | arXiv:2305.11738; PDF ghi ICLR 2024 | Đúng | Bỏ |
| 12 | GASP, "F. Bouke et al., *IPM 2026*" | M. A. Bouke (một tác giả), arXiv:2607.04223 | Sai | Bỏ |
| 13 | Patel, "H. Patel et al.", arXiv:2501.08234 | P. Patel (một tác giả), arXiv:2510.22751 | Sai | Bỏ |
| 14 | CRAG, arXiv:2401.15884 | Đúng | Đúng | Có thể giữ |
| 15 | Akarsu, arXiv:2601.09214 | arXiv:2604.01733 | Sai | Bỏ (có thể dùng cho bài 2) |
| 16 | Baban, KDD 2025 | PDF ghi Dell Technologies, có DOI ACM; chưa kiểm số trang | Chờ | Bỏ |
| 17 | LQ-RAG, "GIST Research" | Wahidur et al., "Legal Query RAG", IEEE Access 13 (2025) | Sai tác giả | Bỏ |
| 18 | LegalMALR, "J. Li", arXiv:2603.01824 | Yunhan Li et al., arXiv:2601.17692 | Sai | Giữ (K1) |
| 19 | Shakti, arXiv:2503.01933 | Đúng | Đúng | Bỏ |
| 20 | Qwen2.5, arXiv:2412.15115 | Đúng | Đúng | **Đổi** sang Qwen3, arXiv:2505.09388 |
| 21 | Pareja, arXiv:2408.01234 | arXiv:2412.13337 | Sai | Bỏ |
| 22 | ViGPTQA, "N. Nguyen", arXiv:2311.08204 | M.-T. Nguyen et al., EMNLP 2023 Industry, DOI 10.18653/v1/2023.emnlp-industry.70 | Sai | Giữ |
| 23 | Hien et al., IC3K 2025, "pp. 112–121" | Tên và tác giả đúng; số trang chưa kiểm | Chờ | Giữ |
| 24 | Ngo et al., *Proc. ICT 2025* | Không tìm thấy; PDF chỉ là ảnh | Chưa kiểm được | Không cite |
| 25 | LawPal, "S. Kumar, *Expert Systems with Applications*" | D. Panchal et al., arXiv:2502.16573 | Sai | Bỏ |
| 26–29 | GPTCache, RouteLLM, vLLM, Nougat | Không có PDF; hệ thống không dùng | — | Bỏ |
| 30–33 | Constitutional AI, DSPy, ToolLLM, RAGAS | Không liên quan tới bài 1 | — | Bỏ |

Bài học: **không chép tài liệu tham khảo từ bản cũ.** Mọi mục trong bài mới lấy từ `paper_list.md` và có trạng thái "Đã kiểm".

## 4. Tài liệu mới cần thêm

Xem `paper_list.md` mục 1–6. Quan trọng nhất là **PhamDuy2023** (SoICT 2023), công trình gần nhất về hỏi đáp dịch vụ công tiếng Việt. Nó chỉ đo câu trả lời được, nên cho thấy rõ khoảng trống mà bài 1 lấp: câu hỏi thật, phần lớn phải từ chối.

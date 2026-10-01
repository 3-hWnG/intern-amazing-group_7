# Tổng Hợp 20 Bài Báo Khoa Học (Research Papers) Cho Dự Án Trợ Lý Thủ Tục Hành Chính (V10.5)

> **Tài liệu tham khảo nghiên cứu (Literature Review & Related Works)**  
> **Chủ đề dự án:** Trợ lý ảo AI tư vấn dịch vụ công & thủ tục hành chính sử dụng mô hình ngôn ngữ nhỏ cục bộ (Local SLM 1.5B–3B), kiến trúc truy xuất tăng cường kết hợp hệ thống kép (Dual-System RAG: CSDL cấu trúc FTS5 + Web Search) và cơ chế tự kiểm chứng (Verifier).  
> **Trạng thái tài liệu:** Toàn bộ 20/20 bài báo đều là **Open-Access / Full-text PDF** được tải về máy và lưu trữ với **tên gốc chuẩn xác của bài báo** tại thư mục `D:\V10.5\Documentation\research paper\`, đi kèm bản phân tích chuyên sâu `literature_review.md` chuẩn học thuật.

---

## Mục lục phân loại theo chủ đề

1. [Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử (E-Government Chatbots)](#nhóm-1-ai-hội-thoại--chatbot-dịch-vụ-công--hành-chính-điện-tử-e-government)
2. [Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)](#nhóm-2-rag-cho-hỏi-đáp-pháp-luật-quy-định--thủ-tục-legal--regulatory-rag)
3. [Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)](#nhóm-3-kiểm-chứng-verifier--giảm-ảo-giác-trong-rag-fact-checking--verifiers)
4. [Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)](#nhóm-4-truy-xuất-lai--hệ-thống-kép-hybrid--dual-system-retrieval)
5. [Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)](#nhóm-5-mô-hình-ngôn-ngữ-nhỏ-slms--triển-khai-cục-bộ-localedge-slms)
6. [Bảng tổng hợp đối sánh 20 bài báo theo khía cạnh dự án V10.5](#bảng-tổng-hợp-đối-sánh-20-bài-báo-theo-khía-cạnh-dự-án-v105)
7. [Khung cấu trúc bài báo khoa học đề xuất cho Dự án V10.5](#khung-cấu-trúc-bài-báo-khoa-học-đề-xuất-cho-dự-án-v105)

---

## Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử

### 1. GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning
- **Tác giả:** Daniel M. Jimenez-Gutierrez, Albenzio Cirillo, Raffaele Nicolussi, Alessio Beltrame, Andrea Vitaletti (Sapienza University of Rome; Fondazione Ugo Bordoni)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2606.01386 [cs.AI]*
- **Phân loại nghiên cứu:** `Primary Architecture & Privacy-Preserving System`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2606.01386](https://arxiv.org/abs/2606.01386)
- **Tệp toàn văn (PDF bản gốc):** [`GuidaPA - Privacy-Preserving Chatbot for Public Administration via Federated Learning.pdf`](research%20paper/01_E-Government_Chatbots/01_GuidaPA_2026_Privacy_Preserving_Chatbot_Public_Admin/GuidaPA%20-%20Privacy-Preserving%20Chatbot%20for%20Public%20Administration%20via%20Federated%20Learning.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/01_E-Government_Chatbots/01_GuidaPA_2026_Privacy_Preserving_Chatbot_Public_Admin/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Cơ quan hành chính công muốn dùng chatbot LLM để trả lời nghiệp vụ, nhưng dữ liệu nội bộ (ticket, sổ tay cán bộ, trích xuất CSDL) không được gom về một máy chủ trung tâm vì ràng buộc pháp lý và tổ chức.

Câu hỏi nghiên cứu: *Học liên kết (Federated Learning) có cho ra chatbot hành chính chất lượng gần bằng tinh chỉnh tập trung mà vẫn giữ dữ liệu tại chỗ không?*

#### Phương pháp luận & Đóng góp kỹ thuật
GuidaPA tinh chỉnh LLM theo kiểu liên kết trên tài liệu của hai nền tảng hành chính quốc gia Ý là SIGESON và SIDFORS.

- **Dữ liệu:** khoảng 8 trang sổ tay SIGESON và 31 trang sổ tay/FAQ SIDFORS. Nghiên cứu dùng tài liệu công khai làm dữ liệu thay thế an toàn; mục tiêu triển khai là dữ liệu nội bộ không được chia sẻ.
- **Kiến trúc:** kiểm soát truy cập theo vai trò, tiền xử lý bảo mật phía client, theo dõi hiệu ứng non-IID giữa các client.
- **Huấn luyện:** QLoRA 4-bit, 15 vòng federated, chia 80/20 train/test cho mỗi client; đo bằng ROUGE, BLEU-4 và METEOR.

#### Kết quả thực nghiệm chính
Mô hình federated tốt nhất đạt chất lượng gần bằng tinh chỉnh tập trung (private centralized), trong khi dữ liệu không rời máy của từng cơ quan.

- ROUGE-1/2/L 61.10/55.77/59.44, BLEU-4 45.02, METEOR 63.94.
- So với mô hình tổng quát chưa tinh chỉnh: ROUGE-1 tăng từ 41.45 lên 62.18, BLEU-4 tăng từ 26.97 lên 50.90.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Bối cảnh vận hành thật trong hành chính công Ý, không phải y tế hay giáo dục. Có số đo rõ ràng, so với cả baseline tập trung lẫn mô hình chưa tinh chỉnh.
- **Hạn chế (Limitations):** Kho dữ liệu nhỏ (khoảng 39 trang) và chỉ đo độ trùng từ (ROUGE/BLEU/METEOR), chưa đo tính đúng sự thật. Mỗi cơ quan cần hạ tầng tính toán riêng để huấn luyện liên kết.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ trích dẫn làm bối cảnh: cơ quan hành chính không muốn gom dữ liệu nội bộ về máy chủ ngoài. V10.5 đi hướng đơn giản hơn, chạy mô hình và CSDL cục bộ (Ollama, `procedures.db`), không dùng học liên kết. Cấu hình QLoRA 4-bit của bài cùng loại với `Utility/finetune/train_qlora.py`, nhưng V10.5 chưa fine-tune vì chưa có dữ liệu phản hồi.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 1 (Introduction)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Public administrations often cannot centralise internal data; GuidaPA shows that federated QLoRA fine-tuning can approach centralised quality while keeping data on-site (Jimenez-Gutierrez et al., 2026). Our system takes a simpler route to the same privacy goal: a small model runs fully on-premise, without any training."

---

### 2. GovAI-Pipe: A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway
- **Tác giả:** Ahmet Kaplan (Istanbul Medipol University)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2606.01417 [cs.AI]*
- **Phân loại nghiên cứu:** `Governance Framework (Design Science Research)`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2606.01417](https://arxiv.org/abs/2606.01417)
- **Tệp toàn văn (PDF bản gốc):** [`GovAI-Pipe - A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway.pdf`](research%20paper/01_E-Government_Chatbots/02_GovAI-Pipe_2026_Governance_Pipeline_eGovernment/GovAI-Pipe%20-%20A%20Layered%20AI%20Governance%20Pipeline%20for%20Citizen-Facing%20AI%20in%20Turkey%27s%20e-Government%20Gateway.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/01_E-Government_Chatbots/02_GovAI-Pipe_2026_Governance_Pipeline_eGovernment/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Cổng e-Devlet của Thổ Nhĩ Kỳ phục vụ hơn 68 triệu người dùng với hơn 9.200 dịch vụ và đang tích hợp AI (chatbot hướng dẫn thủ tục, sàng lọc điều kiện hưởng chính sách). Tuy vậy, chưa có hạ tầng kỹ thuật nối các khung chính sách AI (EU AI Act, OECD AI Principles, Chiến lược AI quốc gia) với việc vận hành thực tế.

Câu hỏi nghiên cứu: *Làm sao biến nguyên tắc quản trị AI thành các thành phần kỹ thuật kiểm toán được trong một cổng dịch vụ công tập trung?*

#### Phương pháp luận & Đóng góp kỹ thuật
GovAI-Pipe là pipeline quản trị 4 tầng, thiết kế theo phương pháp Design Science Research, gắn vòng đời mô hình AI với các điểm kiểm soát:

- **Tầng 1 – trước triển khai:** kiểm thử thiên kiến, khả năng giải thích, đánh giá tác động quyền riêng tư.
- **Tầng 2 – triển khai:** phân loại mức rủi ro và quy trình phê duyệt.
- **Tầng 3 – vận hành:** phát hiện drift, theo dõi công bằng, chuyển cho người xử lý (human-in-the-loop).
- **Tầng 4 – sau sự cố:** nhật ký kiểm toán, rollback, cơ chế khiếu nại của công dân.
- Mỗi tầng gắn với điều khoản cụ thể của EU AI Act, GDPR và Chiến lược AI quốc gia.

#### Kết quả thực nghiệm chính
Đây là nghiên cứu thiết kế, không có thực nghiệm định lượng. Khung được minh hoạ qua hai tình huống rủi ro cao trên e-Devlet để cho thấy nguyên tắc quản trị trở thành thành phần pipeline kiểm toán được.

- Bài không báo cáo độ chính xác hay tỉ lệ lỗi; giá trị nằm ở việc ánh xạ điều khoản chính sách sang điểm kiểm soát kỹ thuật.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Ánh xạ cụ thể từ điều khoản pháp lý sang thành phần kỹ thuật. Bối cảnh cổng dịch vụ công quốc gia quy mô lớn.
- **Hạn chế (Limitations):** Chưa được kiểm chứng bằng triển khai thực hay số liệu. Một tác giả; khung đề xuất ở mức khái niệm.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Khung quản trị bốn tầng (kiểm thử, phê duyệt, vận hành, sau sự cố) để đối chiếu phần kiểm soát của V10.5: đã có nhật ký (`developer_mode`, Evidence Pack ghi ngày truy xuất) và nút 👍/👎. Chưa có: chuyển cho cán bộ khi mô hình không chắc. Bài ở mức khái niệm, chỉ dùng làm khung, không làm bằng chứng số liệu.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 5 (Discussion: governance)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Citizen-facing AI needs auditable checkpoints across the model lifecycle, from pre-deployment validation to runtime monitoring and human escalation (Kaplan, 2026). Our web-search pipeline implements the runtime part of this idea: every generated answer passes a verification step before it reaches the citizen."

---

### 3. From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch
- **Tác giả:** Laurens Samson, Iva Gornishka, Gossa Lô, Yuki M. Asano, Sennay Ghebreab (City of Amsterdam; University of Amsterdam; University of Technology Nuremberg)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2608.09925 [cs.CL]*
- **Phân loại nghiên cứu:** `Empirical Benchmark & Civil Service Survey`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2608.09925](https://arxiv.org/abs/2608.09925)
- **Tệp toàn văn (PDF bản gốc):** [`From Values to Benchmarks - Evaluating Large Language Models for Governmental Use in Dutch.pdf`](research%20paper/01_E-Government_Chatbots/03_Grip-on-LLMs_2026_Evaluating_LLMs_Governmental_Use/From%20Values%20to%20Benchmarks%20-%20Evaluating%20Large%20Language%20Models%20for%20Governmental%20Use%20in%20Dutch.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/01_E-Government_Chatbots/03_Grip-on-LLMs_2026_Evaluating_LLMs_Governmental_Use/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Chính quyền đang triển khai LLM, nhưng ít bộ đánh giá phản ánh đồng thời giá trị của hành chính công và yêu cầu của ngôn ngữ ngoài tiếng Anh (ở đây là tiếng Hà Lan).

Câu hỏi nghiên cứu: *Nên đánh giá một LLM theo những tiêu chí nào trước khi đưa vào dùng trong cơ quan nhà nước?*

#### Phương pháp luận & Đóng góp kỹ thuật
Khung "Grip on LLMs" được xây cùng chuyên gia của City of Amsterdam:

- Xác định tiêu chí qua hội đồng tư vấn, nghiên cứu người dùng và khảo sát người dùng một chatbot dành cho công chức.
- Sáu chiều đánh giá: factuality, honesty, social bias, tiêu thụ năng lượng, chi phí, minh bạch dữ liệu huấn luyện.
- Benchmark cho hơn 30 mô hình đa ngôn ngữ và mô hình riêng tiếng Hà Lan; công bố mã và trang tổng quan cho người không chuyên.

#### Kết quả thực nghiệm chính
Không mô hình nào tốt ở mọi chiều, nên việc chọn mô hình luôn phải đánh đổi.

- Chất lượng cao hơn luôn đi kèm tác động môi trường và chi phí lớn hơn; thiên kiến gần như độc lập với hai yếu tố này.
- Factuality (trả lời đúng) và honesty (thừa nhận khi không biết) do các đặc tính khác nhau chi phối: factuality cao không kéo theo honesty cao.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Tiêu chí xuất phát từ người dùng thật trong cơ quan nhà nước. Tách riêng "trả lời đúng" và "biết nói không biết".
- **Hạn chế (Limitations):** Tập trung vào tiếng Hà Lan. Đánh giá mô hình đơn lẻ, không đánh giá cả hệ RAG.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Dùng cho thiết kế đánh giá: tách factuality (trả lời đúng) khỏi honesty (nói chưa có thông tin đúng lúc). `Evaluation/evaluate.py` hiện không đo độ đúng nội dung và chưa có bộ câu đo honesty. Bài không đánh giá hệ RAG nên chỉ mượn khung tiêu chí.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 4 (Evaluation Methodology)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Governmental LLM evaluation must look beyond accuracy: factuality and honesty are distinct properties, and a model that answers correctly does not necessarily acknowledge what it does not know (Samson et al., 2026). We therefore report answer correctness together with how often the assistant asks for clarification or declines."

---

### 4. Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots
- **Tác giả:** Yingjie Liu, Yongxiang Hu, Xuan Wang, Yilun Li, Yunlei Wei, Xiaoyu Wang, Yangfan Zhou (Fudan University; Meituan)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2606.04394 [cs.SE]*
- **Phân loại nghiên cứu:** `Benchmark & Alignment Methodology`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2606.04394](https://arxiv.org/abs/2606.04394)
- **Tệp toàn văn (PDF bản gốc):** [`Beyond Single-Policy - Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots.pdf`](research%20paper/01_E-Government_Chatbots/04_COPAL_2026_Evaluating_Composed_Policy_Alignment/Beyond%20Single-Policy%20-%20Evaluating%20Composed%20Organization-Specific%20Policy%20Alignment%20in%20LLM%20Chatbots.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/01_E-Government_Chatbots/04_COPAL_2026_Evaluating_Composed_Policy_Alignment/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Chatbot trong tổ chức (y tế, tài chính, dịch vụ công) bị ràng buộc bởi chính sách riêng về nội dung được và không được nói. Các benchmark hiện có chỉ kiểm tra từng chính sách một, nên bỏ sót lỗi khi một yêu cầu đụng tới nhiều chính sách cùng lúc.

Câu hỏi nghiên cứu: *Chatbot xử lý thế nào khi một câu hỏi đòi hỏi tuân thủ đồng thời nhiều chính sách?*

#### Phương pháp luận & Đóng góp kỹ thuật
COPAL là khung tự động đánh giá độ tuân thủ chính sách tổ hợp (composed-policy alignment):

- Sinh câu hỏi từ các mẫu tương tác rút ra thực nghiệm; mỗi câu buộc chatbot xử lý nhiều chính sách trong một câu trả lời.
- Mỗi câu hỏi đi kèm một "hợp đồng xử lý" nêu rõ phải cung cấp gì và phải tránh gì.
- Áp dụng trên 30 "thế giới công ty" mô phỏng tổ chức.

#### Kết quả thực nghiệm chính
Trên 9 mô hình, câu hỏi tổ hợp chính sách có tỉ lệ lỗi 33.1%.

- Lỗi thường chỉ một phía: chatbot làm đúng phần "phải cung cấp" hoặc phần "phải tránh", nhưng bỏ sót phần còn lại.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Chỉ ra loại lỗi mà benchmark một chính sách bỏ sót. Hợp đồng xử lý giúp chấm điểm rõ ràng.
- **Hạn chế (Limitations):** Dùng thế giới công ty mô phỏng, không phải dữ liệu tổ chức thật. Không đánh giá riêng miền hành chính công.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Mượn ý "hợp đồng xử lý" (phải nêu gì, phải tránh gì) cho bộ test, ví dụ cảnh báo thủ tục khác không được chặn câu trả lời, ô trống phải nói chưa có thông tin. Chưa áp dụng trong code. Bài không bàn về xử lý bản của tỉnh hay cấp Xã/Phường.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 4 (Evaluation Methodology)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "When a single request touches several organisational policies at once, chatbots fail far more often than single-policy benchmarks suggest, with a 33.1% error rate across 9 models (Liu et al., 2026). This motivates testing administrative assistants on questions that combine several constraints in one turn."

---

## Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)

### 5. LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters
- **Tác giả:** Virgill van der Meer (Municipality of Amsterdam), Julien Rossi (University of Amsterdam)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2605.12012 [cs.AI]; bản PDF ghi ICAIL 2026*
- **Phân loại nghiên cứu:** `Primary Architecture & Case Study`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2605.12012](https://arxiv.org/abs/2605.12012)
- **Tệp toàn văn (PDF bản gốc):** [`LegalCheck - Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters.pdf`](research%20paper/02_Legal_Regulatory_RAG/05_vanderMeer_2026_LegalCheck_Municipal_Advice/LegalCheck%20-%20Retrieval-%20and%20Context-Augmented%20Generation%20for%20Drafting%20Municipal%20Legal%20Advice%20Letters.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/02_Legal_Regulatory_RAG/05_vanderMeer_2026_LegalCheck_Municipal_Advice/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Phòng pháp chế của chính quyền Hà Lan thiếu nhân sự, số hồ sơ tăng và áp lực tuân thủ lớn. Soạn thư trả lời khiếu nại (objection response letters) tốn nhiều giờ.

Câu hỏi nghiên cứu: *LLM kết hợp truy xuất có soạn được thư tư vấn pháp lý gần hoàn chỉnh, nhất quán và giải thích được cho một chính quyền thành phố không?*

#### Phương pháp luận & Đóng góp kỹ thuật
LegalCheck kết hợp Retrieval-Augmented Generation (RAG) và Context-Augmented Generation (CAG):

- Truy xuất luật và các thư/vụ việc trước đó từ kho tri thức pháp lý được tuyển chọn.
- Prompt có kiểm soát đưa cả tri thức ngoài lẫn chi tiết của hồ sơ cụ thể vào bản nháp theo cấu trúc thư: giới thiệu, nội dung khiếu nại, phần giải thích pháp lý, kết luận.
- Chuyên gia pháp lý duyệt mọi bản nháp (expert-in-the-loop).

#### Kết quả thực nghiệm chính
Triển khai thực tế tại Municipality of Amsterdam: thư gần hoàn chỉnh được soạn trong vài phút thay vì vài giờ.

- Bản nháp thường nắm được 80–100% nội dung pháp lý cốt lõi và hay dẫn chiếu điều khoản hoặc lập luận của vụ việc tương tự.
- Người dùng pháp lý đánh giá hệ thống giảm khối lượng công việc và giúp áp dụng chuẩn pháp lý nhất quán hơn, không thay thế phán đoán của con người.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Triển khai thật trong cơ quan chính quyền, có người dùng chuyên môn đánh giá. Đầu ra dựa trên văn bản và tiền lệ thật nên giải thích được.
- **Hạn chế (Limitations):** Đánh giá chủ yếu định tính, quy mô nhỏ. Cần chuyên gia duyệt từng thư.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ trích dẫn làm bối cảnh: soạn thư pháp lý có chuyên gia duyệt. Bài không bàn về phân cấp thẩm quyền Xã > Huyện > Tỉnh, và V10.5 không có xếp hạng thẩm quyền như vậy (bản của tỉnh chỉ được xếp lên trước khi người dùng nhắc tên tỉnh).

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 2.2 (Legal & Regulatory RAG)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "In a real municipal deployment, grounding generation in retrieved regulations and prior decisions produced near-final legal advice letters in minutes, with legal experts keeping the final review (van der Meer & Rossi, 2026). Likewise, our assistant grounds answers in official procedure records rather than in the model's parametric knowledge."

---

### 6. LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain
- **Tác giả:** Nicholas Pipitone, Ghita Houir Alami (ZeroEntropy)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2408.10343 [cs.AI]*
- **Phân loại nghiên cứu:** `Standard Benchmark & Evaluation Methodology`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2408.10343](https://arxiv.org/abs/2408.10343)
- **Tệp toàn văn (PDF bản gốc):** [`LegalBench-RAG - A Benchmark for Retrieval-Augmented Generation in the Legal Domain.pdf`](research%20paper/02_Legal_Regulatory_RAG/06_Pipitone_2024_LegalBench-RAG/LegalBench-RAG%20-%20A%20Benchmark%20for%20Retrieval-Augmented%20Generation%20in%20the%20Legal%20Domain.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/02_Legal_Regulatory_RAG/06_Pipitone_2024_LegalBench-RAG/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
LegalBench đo khả năng sinh của LLM trong pháp lý, nhưng chưa có benchmark riêng cho bước truy xuất của hệ RAG pháp lý.

Câu hỏi nghiên cứu: *Hệ RAG có tìm được đúng đoạn văn bản pháp lý ngắn và chính xác cần để trả lời không?*

#### Phương pháp luận & Đóng góp kỹ thuật
Tác giả xây benchmark truy xuất bằng cách lần ngược ngữ cảnh của các câu hỏi LegalBench về vị trí gốc trong kho văn bản:

- 6.858 cặp hỏi–đáp trên kho hơn 79 triệu ký tự, do chuyên gia pháp lý gán nhãn; lấy từ 4 bộ PrivacyQA, CUAD, MAUD và ContractNLI.
- Đo Precision@k và Recall@k ở mức đoạn trích (snippet) thay vì mức tài liệu; kèm bản nhẹ LegalBench-RAG-mini.
- Thử 2 cách cắt đoạn (cố định 500 ký tự; Recursive Character Text Splitter) và 2 cách hậu xử lý (không rerank; Cohere reranker), với embedding text-embedding-3-large.

#### Kết quả thực nghiệm chính
Cắt đoạn bằng Recursive Character Text Splitter và không dùng reranker cho precision và recall cao nhất.

- Cohere reranker (mô hình đa dụng) lại cho kết quả kém hơn không rerank; tác giả cho rằng văn bản pháp lý khác miền mà reranker được huấn luyện.
- Precision tuyệt đối thấp, ví dụ PrivacyQA với cách cắt cố định chỉ đạt khoảng 14% ở k=1: truy xuất đúng đoạn pháp lý vẫn khó.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Benchmark đầu tiên tập trung vào bước truy xuất trong pháp lý, nhãn do chuyên gia gán. Công khai dữ liệu (github.com/zeroentropy-cc/legalbenchrag).
- **Hạn chế (Limitations):** Văn bản hợp đồng và chính sách quyền riêng tư tiếng Anh, không phải thủ tục hành chính. Chỉ thử một mô hình embedding và một reranker.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Luận cứ cho việc không thêm reranker đa dụng: bài thấy Cohere reranker kém hơn không rerank trên văn bản pháp lý. Xếp hạng V10.5 là quy tắc viết tay (tầng khớp FTS5, độ khớp tên, lĩnh vực, bm25). Gợi ý đo: Web search chưa kiểm xem đoạn được chọn có chứa câu trả lời không, bài đo ở mức đoạn.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 3.3 (Retrieval Design)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Retrieval precision is the bottleneck of legal RAG: on LegalBench-RAG a strong embedding model rarely returns the exact supporting snippet, and a general-purpose reranker hurt rather than helped (Pipitone & Houir Alami, 2024). We therefore evaluate retrieval separately from answer generation."

---

### 7. CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law
- **Tác giả:** Ethan Zhao, Maksym Taranukhin, Wei Cui, Moira Aikenhead, Vered Shwartz (University of British Columbia; Vector Institute)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2605.30497 [cs.CL]*
- **Phân loại nghiên cứu:** `Benchmark & Legal RAG Evaluation`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2605.30497](https://arxiv.org/abs/2605.30497)
- **Tệp toàn văn (PDF bản gốc):** [`CanLegalRAGBench - Evaluating Retrieval-Augmented Generation on Canadian Case Law.pdf`](research%20paper/02_Legal_Regulatory_RAG/07_Zhao_2026_CanLegalRAGBench/CanLegalRAGBench%20-%20Evaluating%20Retrieval-Augmented%20Generation%20on%20Canadian%20Case%20Law.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/02_Legal_Regulatory_RAG/07_Zhao_2026_CanLegalRAGBench/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Trợ lý pháp lý dựa trên RAG vẫn bịa; nhiều benchmark dùng câu hỏi tổng hợp thay vì tình huống thật; luật Canada ít được đánh giá.

Câu hỏi nghiên cứu: *Hệ RAG trả lời câu hỏi pháp lý thực tế dựa trên án lệ Canada tốt đến đâu, và lỗi nằm ở bước truy xuất hay bước sinh?*

#### Phương pháp luận & Đóng góp kỹ thuật
CanLegalRAGBench là benchmark hỏi đáp pháp lý Canada với câu hỏi sát thực tế và đáp án do chuyên gia gán, dựa trên án lệ:

- Sinh câu hỏi theo persona từ các bản án, lọc bằng LLM-judge, tạo biến thể câu hỏi có kiểm soát.
- Đánh giá truy xuất với nhiều cách cắt đoạn, nhiều mô hình embedding và các phương pháp FAISS, BM25, hybrid.
- Đánh giá câu trả lời sinh ra so với đáp án chuẩn và theo mức được tài liệu truy xuất hỗ trợ.
- Mã và dữ liệu: github.com/NLP-UBC/CanLegalRAGBench.

#### Kết quả thực nghiệm chính
Kết quả truy xuất nhạy với các lựa chọn thiết kế; embedding mã nguồn mở cạnh tranh được với embedding đóng.

- Đánh giá tự động phạt oan hệ thống khi truy xuất được tài liệu liên quan nhưng khác tài liệu gốc.
- Câu trả lời thường lệch đáp án chuẩn, do bịa hoặc do quá chi tiết/lạc đề; 8–29% claim không được tài liệu truy xuất hỗ trợ.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Câu hỏi sát thực tế, đáp án do chuyên gia gán. Tách lỗi truy xuất và lỗi sinh; đo tỉ lệ claim không có căn cứ.
- **Hạn chế (Limitations):** Án lệ Canada (common law), khác văn bản thủ tục hành chính. Chính tác giả chỉ ra hạn chế của đánh giá tự động.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Khung cho bộ đo: tỉ lệ claim không có bằng chứng hỗ trợ, biến thể câu hỏi kiểm soát và bộ giữ riêng để đo khái quát. Chưa áp dụng: 14 câu diễn đạt khác đã dùng để chỉnh nên không còn đo khái quát được. Việc tách CSDL thành các trường (`fees`, `checklist`…) là quyết định riêng của V10.5, không lấy từ bài.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 4 (Evaluation Methodology)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Even with retrieval, 8–29% of the claims in legal RAG answers are not supported by the retrieved documents (Zhao et al., 2026). This motivates a post-generation check that each factual statement is backed by a retrieved source."

---

### 8. HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications
- **Tác giả:** Rishi Kalra, Zekun Wu, Ayesha Gulley, Airlie Hilliard, Xin Guan, Adriano Koshiyama, Philip Treleaven (Holistic AI; University College London)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *NAACL 2025 Industry Track & EMNLP 2024 CustomNLP4U Workshop / arXiv:2409.09046 [cs.IR]*
- **Phân loại nghiên cứu:** `Primary Architecture & Adaptive Algorithm`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2409.09046](https://arxiv.org/abs/2409.09046)
- **Tệp toàn văn (PDF bản gốc):** [`HyPA-RAG - A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications.pdf`](research%20paper/02_Legal_Regulatory_RAG/08_Kalra_2024_HyPA-RAG_Legal_Policy/HyPA-RAG%20-%20A%20Hybrid%20Parameter%20Adaptive%20Retrieval-Augmented%20Generation%20System%20for%20AI%20Legal%20and%20Policy%20Applications.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/02_Legal_Regulatory_RAG/08_Kalra_2024_HyPA-RAG_Legal_Policy/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Trong pháp lý và chính sách AI, LLM gặp kiến thức lỗi thời, ảo giác và suy luận kém. RAG giúp được, nhưng vẫn lỗi truy xuất, ghép ngữ cảnh kém và tốn chi phí vận hành.

Câu hỏi nghiên cứu: *Có thể điều chỉnh tham số truy xuất theo độ phức tạp của từng câu hỏi để vừa chính xác vừa tiết kiệm không?*

#### Phương pháp luận & Đóng góp kỹ thuật
HyPA-RAG (Hybrid Parameter-Adaptive RAG) được thử trên luật NYC Local Law 144 (LL144) về công cụ tuyển dụng tự động:

- Bộ phân loại độ phức tạp câu hỏi chọn tham số truy xuất (như số đoạn truy xuất) cho từng câu.
- Truy xuất lai kết hợp dense, sparse (từ khoá) và knowledge graph.
- Khung đánh giá riêng với các loại câu hỏi và chỉ số thiết kế cho miền luật.

#### Kết quả thực nghiệm chính
Trên LL144, HyPA-RAG cải thiện độ chính xác truy xuất, độ trung thành của câu trả lời và độ chính xác ngữ cảnh so với RAG dùng tham số cố định.

- Số liệu chi tiết theo từng loại câu hỏi và từng chỉ số nằm trong các bảng của bài.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Điều chỉnh chi phí truy xuất theo từng câu thay vì một cấu hình chung. Kết hợp ba kiểu truy xuất bổ trợ nhau.
- **Hạn chế (Limitations):** Chỉ thử trên một văn bản luật (LL144). Cần huấn luyện bộ phân loại độ phức tạp.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ trích dẫn: truy xuất lai và chỉnh tham số theo độ phức tạp câu hỏi. V10.5 không có bộ phân loại độ phức tạp, và độ trễ Web search bị chặn bởi deadline cố định nên chỉnh số trang đọc không giúp được. Xếp hạng của V10.5 (tầng FTS5, độ khớp, bm25) là tự thiết kế, không suy ra từ bài.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 2.2 (Legal & Regulatory RAG)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Adapting retrieval parameters to query complexity and combining dense, sparse and knowledge-graph retrieval improves retrieval accuracy and answer fidelity on legal-policy QA (Kalra et al., 2024)."

---

## Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

### 9. Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models
- **Tác giả:** Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, Roberta Raileanu, Xian Li, Asli Celikyilmaz, Jason Weston (Meta AI; ETH Zürich)
- **Năm xuất bản:** 2023
- **Tạp chí / Hội nghị:** *Findings of the Association for Computational Linguistics (ACL 2024) / arXiv:2309.11495 [cs.CL]*
- **Phân loại nghiên cứu:** `Foundational Methodology & Algorithm`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2309.11495](https://arxiv.org/abs/2309.11495)
- **Tệp toàn văn (PDF bản gốc):** [`Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models.pdf`](research%20paper/03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/Chain-of-Verification%20%28CoVe%29%20Reduces%20Hallucination%20in%20Large%20Language%20Models.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/03_Fact-Checking_Verifiers/09_Dhuliawala_2023_Chain-of-Verification_CoVe/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
LLM sinh thông tin sai nhưng nghe hợp lý (ảo giác), nhất là với sự kiện ít gặp và khi sinh văn bản dài.

Câu hỏi nghiên cứu: *Mô hình có tự kiểm tra và sửa câu trả lời của chính nó được không?*

#### Phương pháp luận & Đóng góp kỹ thuật
Chain-of-Verification (CoVe) gồm 4 bước:

- (i) Sinh bản nháp.
- (ii) Lập các câu hỏi kiểm chứng cho bản nháp.
- (iii) Trả lời từng câu hỏi kiểm chứng một cách độc lập để không bị bản nháp dẫn dắt (bản "factored" tách riêng từng câu).
- (iv) Viết câu trả lời cuối đã kiểm chứng.

#### Kết quả thực nghiệm chính
CoVe giảm ảo giác trên câu hỏi dạng danh sách từ Wikidata, MultiSpanQA sách đóng và sinh tiểu sử dài.

- Wikidata (Llama 65B): precision tăng từ 0.17 (few-shot) lên 0.36 (CoVe two-step).
- MultiSpanQA: F1 tăng từ 0.39 lên 0.48 (CoVe factored).
- Sinh văn bản dài: FactScore tăng từ 55.9 lên 71.4 (+28%).

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Không cần huấn luyện, áp dụng cho mô hình có sẵn. Trả lời câu hỏi kiểm chứng độc lập giúp không lặp lại lỗi của bản nháp.
- **Hạn chế (Limitations):** Tăng số lượt gọi LLM và độ trễ. Kiểm chứng vẫn dựa trên kiến thức của chính mô hình, không có nguồn ngoài.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Đối chiếu khái niệm với `Backend/core/verifier.py` (kiểm chứng trước khi trả lời), nhưng V10.5 không cài CoVe (không có bước đặt câu hỏi kiểm chứng riêng). Kết quả của bài trên Llama 65B, chưa chắc giữ được với 1.5B, và thêm lượt gọi sẽ làm Web search chậm hơn. Lần đo 24/09 22:49: 12 câu bị viết lại, chỉ 3 câu qua.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 2.3 (Hallucination Mitigation)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Verifying a draft through independently answered verification questions reduces hallucination in list questions, closed-book QA and long-form generation (Dhuliawala et al., 2023)."

---

### 10. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
- **Tác giả:** Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi (University of Washington; Allen Institute for AI; IBM Research AI)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *International Conference on Learning Representations (ICLR 2024 Oral) / arXiv:2310.11511 [cs.CL]*
- **Phân loại nghiên cứu:** `Foundational Model Framework`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2310.11511](https://arxiv.org/abs/2310.11511)
- **Tệp toàn văn (PDF bản gốc):** [`Self-RAG - Learning to Retrieve, Generate, and Critique through Self-Reflection.pdf`](research%20paper/03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/Self-RAG%20-%20Learning%20to%20Retrieve%2C%20Generate%2C%20and%20Critique%20through%20Self-Reflection.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/03_Fact-Checking_Verifiers/10_Asai_2024_Self-RAG_Reflection_Critique/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
RAG thường truy xuất một số đoạn cố định bất kể có cần truy xuất hay đoạn có liên quan không, làm giảm tính linh hoạt hoặc sinh câu trả lời kém hữu ích.

Câu hỏi nghiên cứu: *Mô hình có tự quyết định khi nào cần truy xuất, và tự phê bình đoạn truy xuất lẫn câu trả lời của mình không?*

#### Phương pháp luận & Đóng góp kỹ thuật
Self-RAG huấn luyện một LM duy nhất sinh các reflection token:

- `Retrieve`: có cần truy xuất không.
- `ISREL`: đoạn truy xuất có liên quan không.
- `ISSUP`: câu sinh ra có được đoạn truy xuất hỗ trợ không.
- `ISUSE`: câu trả lời hữu ích đến đâu.
- Reflection token cho phép điều khiển hành vi lúc suy luận theo yêu cầu của từng tác vụ.

#### Kết quả thực nghiệm chính
Self-RAG (7B và 13B) vượt ChatGPT và Llama2-chat có truy xuất trên hỏi đáp mở, suy luận và kiểm chứng sự thật.

- Cải thiện rõ tính đúng sự thật và độ chính xác trích dẫn ở văn bản dài so với các mô hình trên.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Truy xuất theo nhu cầu thay vì luôn truy xuất. Tự đánh giá mức hỗ trợ bằng chứng cho từng đoạn sinh ra.
- **Hạn chế (Limitations):** Phải huấn luyện mô hình với token đặc biệt; không áp dụng trực tiếp cho mô hình có sẵn. Chỉ thử trên tiếng Anh.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ mượn cách chia ba câu hỏi: có cần tra không, bằng chứng có liên quan không, câu có được hỗ trợ không. Tương ứng gatekeeper, xếp hạng nguồn và verifier của V10.5. Bài cần huấn luyện token đặc biệt nên không dùng trực tiếp với Qwen2.5-1.5B.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 2.3 (Hallucination Mitigation)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Deciding when to retrieve, and checking whether each generated segment is supported by the retrieved passage, improves factuality and citation accuracy (Asai et al., 2024). We apply these two checks with rules and prompts instead, since our 1.5B model is not fine-tuned."

---

### 11. CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing
- **Tác giả:** Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen (Tsinghua University; Microsoft Research Asia; Microsoft Azure AI)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *International Conference on Learning Representations (ICLR 2024) / arXiv:2305.11738 [cs.CL]*
- **Phân loại nghiên cứu:** `Interactive Verification Architecture`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2305.11738](https://arxiv.org/abs/2305.11738)
- **Tệp toàn văn (PDF bản gốc):** [`CRITIC - Large Language Models Can Self-Correct with Tool-Interactive Critiquing.pdf`](research%20paper/03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/CRITIC%20-%20Large%20Language%20Models%20Can%20Self-Correct%20with%20Tool-Interactive%20Critiquing.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/03_Fact-Checking_Verifiers/11_Gou_2024_CRITIC_Self-Correct_Tool_Interactive/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
LLM đôi khi bịa, sinh code sai hoặc nội dung độc hại, trong khi con người thường dùng công cụ ngoài (công cụ tìm kiếm, trình thông dịch code) để kiểm tra.

Câu hỏi nghiên cứu: *LLM dạng hộp đen có tự sửa đầu ra nhờ phản hồi từ công cụ ngoài không?*

#### Phương pháp luận & Đóng góp kỹ thuật
CRITIC bắt đầu từ đầu ra ban đầu, gọi công cụ phù hợp để kiểm tra từng khía cạnh, rồi sửa đầu ra theo phản hồi; có thể lặp nhiều vòng:

- Công cụ: công cụ tìm kiếm cho hỏi đáp, trình thông dịch code cho bài toán, API chấm độc hại cho giảm độc hại.
- Plug-and-play, không huấn luyện lại mô hình.

#### Kết quả thực nghiệm chính
CRITIC cải thiện ổn định hiệu năng trên hỏi đáp tự do, tổng hợp chương trình giải toán và giảm nội dung độc hại.

- Phản hồi từ công cụ ngoài là yếu tố quyết định: bản CRITIC không dùng công cụ (chỉ tự phê bình) cho kết quả kém hơn rõ.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Không cần huấn luyện. Dùng bằng chứng khách quan từ công cụ thay cho tự đánh giá.
- **Hạn chế (Limitations):** Phụ thuộc độ trễ và độ sẵn sàng của công cụ ngoài. Nhiều vòng gọi LLM làm tăng chi phí.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Luận cứ cho việc verifier dựa chủ yếu vào luật đối chiếu nguồn thay vì để mô hình tự chấm: bài thấy phản hồi từ công cụ ngoài là yếu tố quyết định. Lưu ý nhiều luật trong `verifier.py` được viết theo lỗi của bộ 45 câu tự soạn, cần bộ câu độc lập để biết chúng có khái quát không.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 3.4 (Verification: rules vs self-critique)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Self-correction is reliable only when grounded in external feedback such as search results (Gou et al., 2024); accordingly, our verifier checks answers against retrieved web sources rather than relying on the model's self-assessment."

---

### 12. Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP)
- **Tác giả:** Mohamed Aly Bouke (Multimedia University, Malaysia)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2607.04223 [cs.CL]*
- **Phân loại nghiên cứu:** `Empirical Detection Methodology`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2607.04223](https://arxiv.org/abs/2607.04223)
- **Tệp toàn văn (PDF bản gốc):** [`Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP).pdf`](research%20paper/03_Fact-Checking_Verifiers/12_Bouke_2026_GASP_Grounding_Aware_Sensitivity/Detecting%20Hallucinations%20in%20Retrieval-Augmented%20Generation%20through%20Grounding-Aware%20Sensitivity%20by%20Perturbation%20%28GASP%29.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/03_Fact-Checking_Verifiers/12_Bouke_2026_GASP_Grounding_Aware_Sensitivity/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
RAG giảm nhưng không loại bỏ ảo giác. Các bộ phát hiện hiện có chỉ cho một điểm cho cả câu trả lời, không chỉ ra câu nào không có căn cứ hay vì sao.

Câu hỏi nghiên cứu: *Làm sao xác định từng câu trong câu trả lời có dựa vào tài liệu truy xuất hay không?*

#### Phương pháp luận & Đóng góp kỹ thuật
GASP (Grounding-Aware Sensitivity by Perturbation) là bộ phát hiện ở mức câu/span:

- Giữ nguyên câu trả lời, chấm lại log-likelihood khi có đủ ngữ cảnh, khi không có ngữ cảnh và khi bỏ từng đoạn; đo mức giảm log-likelihood và Jensen-Shannon divergence.
- Câu có căn cứ tụt likelihood mạnh khi bỏ đoạn hỗ trợ; câu bịa gần như không đổi.
- Scorer là mô hình nhỏ: Qwen2.5-0.5B, Qwen2.5-1.5B, SmolLM2-1.7B; đánh giá trên RAGTruth, TofuEval và RAGBench.

#### Kết quả thực nghiệm chính
Trên RAGTruth, GASP đạt AUC khoảng 0.73 ở mức câu trả lời và khoảng 0.67 ở mức span, tốt hơn rõ perplexity, độ dài, NLI toàn ngữ cảnh và self-consistency.

- Một ngưỡng không cần huấn luyện trên đặc trưng grounding cho kết quả ngang bộ phân loại có huấn luyện.
- Tín hiệu chuyển được sang TofuEval nhưng không hiệu quả với câu trả lời ngắn của RAGBench: GASP hợp với câu trả lời dựng từ ngữ cảnh.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Chỉ ra từng câu không có căn cứ. Chạy với mô hình nhỏ, gồm cả Qwen2.5-1.5B là mô hình V10.5 đang dùng.
- **Hạn chế (Limitations):** AUC ở mức vừa phải (0.67–0.73). Phải chấm lại nhiều lần (mỗi đoạn một lần); kém với câu trả lời ngắn.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ trích dẫn ý dùng mô hình nhỏ (kể cả Qwen2.5-1.5B) để đo mức căn cứ. Chưa dùng được: cần chấm lại xác suất của câu trả lời có sẵn, mà client Ollama 0.6.2 theo chữ ký hàm chỉ trả xác suất token do mô hình sinh (chưa thử với server). Bộ lọc phần sau dấu hai chấm ở chế độ trò chuyện là luật của V10.5, không lấy từ bài này.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 2.3 (Hallucination Mitigation)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Sentence-level grounding can be tested cheaply with a small scorer such as Qwen2.5-1.5B: a grounded sentence loses likelihood when its supporting passage is removed, while a hallucinated one barely changes (Bouke, 2026). Our lighter heuristic attaches a citation only when a sentence's keywords largely match a source."

---

### 13. Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models
- **Tác giả:** Piyushkumar Patel (Microsoft)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2510.22751 [cs.AI]*
- **Phân loại nghiên cứu:** `System Framework & Cross-Verification`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2510.22751](https://arxiv.org/abs/2510.22751)
- **Tệp toàn văn (PDF bản gốc):** [`Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models.pdf`](research%20paper/03_Fact-Checking_Verifiers/13_Patel_2025_Multi-Modal_Fact-Verification/Multi-Modal%20Fact-Verification%20Framework%20for%20Reducing%20Hallucinations%20in%20Large%20Language%20Models.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/03_Fact-Checking_Verifiers/13_Patel_2025_Multi-Modal_Fact-Verification/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
LLM tự tin sinh thông tin sai nghe hợp lý, cản trở việc dùng trong ứng dụng cần độ chính xác.

Câu hỏi nghiên cứu: *Có thể phát hiện và sửa ảo giác ngay lúc sinh bằng cách đối chiếu nhiều nguồn tri thức không?*

#### Phương pháp luận & Đóng góp kỹ thuật
Khung kiểm chứng đối chiếu các khẳng định của LLM với nhiều nguồn cùng lúc:

- Nguồn: CSDL có cấu trúc, tìm kiếm web trực tiếp và tài liệu học thuật.
- Khi phát hiện mâu thuẫn, hệ thống tự sửa mà vẫn giữ mạch văn của câu trả lời.

#### Kết quả thực nghiệm chính
Thử trên nhiều miền, khung giảm 67% ảo giác mà không giảm chất lượng câu trả lời.

- Chuyên gia y tế, tài chính và nghiên cứu khoa học chấm 89% đầu ra đã sửa là đạt.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Kết hợp nguồn có cấu trúc và nguồn web, gần với thiết kế hai hệ của V10.5. Có chuyên gia miền đánh giá.
- **Hạn chế (Limitations):** Một tác giả, bài ngắn; mô tả dữ liệu và baseline hạn chế nên khó tái lập. Không đo riêng miền pháp lý hay hành chính.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ trích dẫn làm nền cho ý dùng nhiều nguồn (CSDL có cấu trúc, web, tài liệu học thuật). V10.5 dùng hai hệ thống tách riêng, không đối chiếu chéo tự động. Bằng chứng yếu (một tác giả, bài ngắn) và bài không đo miền hành chính, nên không thể suy ra Hệ thống 2 đạt 0% ảo giác.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 3.1 (Dual-System Pipeline)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Cross-checking generated claims against both structured databases and live web search reduced hallucinations by 67% in a multi-source verification framework (Patel, 2025), supporting the combination of an official procedure database with web search."

---

## Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

### 14. Corrective Retrieval Augmented Generation (CRAG)
- **Tác giả:** Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling (USTC; UCLA; Google DeepMind)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2401.15884 [cs.CL]*
- **Phân loại nghiên cứu:** `Primary Architecture & Fallback Mechanism`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2401.15884](https://arxiv.org/abs/2401.15884)
- **Tệp toàn văn (PDF bản gốc):** [`Corrective Retrieval Augmented Generation (CRAG).pdf`](research%20paper/04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/Corrective%20Retrieval%20Augmented%20Generation%20%28CRAG%29.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/04_Hybrid_Dual-System_Retrieval/14_Yan_2024_CRAG_Corrective_RAG/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
RAG phụ thuộc mạnh vào độ liên quan của tài liệu truy xuất; khi truy xuất sai, mô hình dễ sinh câu trả lời sai.

Câu hỏi nghiên cứu: *Làm sao phát hiện truy xuất kém và sửa nó trước khi sinh câu trả lời?*

#### Phương pháp luận & Đóng góp kỹ thuật
CRAG thêm một retrieval evaluator nhẹ (khởi tạo từ T5-large rồi fine-tune) chấm độ tin cậy của tài liệu truy xuất và kích hoạt một trong ba hành động:

- **Correct:** dùng tài liệu truy xuất, lọc bớt phần thừa.
- **Incorrect:** bỏ tài liệu, chuyển sang tìm kiếm web quy mô lớn.
- **Ambiguous:** kết hợp cả hai.
- Thuật toán decompose-then-recompose chia tài liệu thành mẩu nhỏ, giữ thông tin chính, lọc phần không liên quan.
- Plug-and-play: gắn được vào RAG chuẩn và Self-RAG.

#### Kết quả thực nghiệm chính
Trên 4 bộ dữ liệu PopQA, Biography, PubHealth và Arc-Challenge (sinh ngắn và dài), CRAG cải thiện đáng kể cả RAG chuẩn lẫn Self-RAG.

- Mã nguồn: github.com/HuskyInSalt/CRAG.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Dễ gắn vào pipeline RAG có sẵn. Dùng web search làm nguồn bổ sung khi kho tĩnh không đủ.
- **Hạn chế (Limitations):** Cần huấn luyện và chọn ngưỡng cho evaluator. Web search mang theo nhiễu và độ trễ.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Đối chiếu: Hệ thống 2 đã phân ba mức tương tự (`confident` thì trả bảng, mơ hồ thì hỏi MCQ, không khớp thì `no_evidence` và mời bấm Web search). V10.5 không tự chuyển sang web vì người dùng chọn hệ thống. Chưa có ở Web search: kiểm tra bằng chứng đủ chưa trước khi soạn (`mcp_search/engine.py` chỉ dùng ngưỡng tương đối so với nguồn tốt nhất).

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 5 (Future Work: evidence gate)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "When local retrieval is judged unreliable, extending it with web search improves the robustness of RAG (Yan et al., 2024); our system keeps a curated procedure database and web search as two separate systems and lets the user choose between them."

---

### 15. From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents
- **Tác giả:** Meftun Akarsu (Technische Hochschule Ingolstadt), Recep Kaan Karaman (Uludag University), Christopher Mierbach (Radiate)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2604.01733 [cs.IR]*
- **Phân loại nghiên cứu:** `Comparative Benchmark & Strategy Study`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2604.01733](https://arxiv.org/abs/2604.01733)
- **Tệp toàn văn (PDF bản gốc):** [`From BM25 to Corrective RAG - Benchmarking Retrieval Strategies for Text-and-Table Documents.pdf`](research%20paper/04_Hybrid_Dual-System_Retrieval/15_Akarsu_2026_BM25_to_Corrective_RAG_Tables/From%20BM25%20to%20Corrective%20RAG%20-%20Benchmarking%20Retrieval%20Strategies%20for%20Text-and-Table%20Documents.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/04_Hybrid_Dual-System_Retrieval/15_Akarsu_2026_BM25_to_Corrective_RAG_Tables/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Chưa có so sánh có hệ thống các phương pháp truy xuất hiện đại trên tài liệu chứa cả văn bản lẫn bảng biểu.

Câu hỏi nghiên cứu: *Chiến lược truy xuất nào hiệu quả nhất cho tài liệu văn bản kèm bảng?*

#### Phương pháp luận & Đóng góp kỹ thuật
So sánh 10 chiến lược truy xuất trên một benchmark hỏi đáp tài chính:

- Nhóm phương pháp: sparse (BM25), dense, hybrid fusion, cross-encoder reranking, query expansion (HyDE, multi-query), index augmentation (contextual retrieval) và adaptive retrieval (CRAG).
- Dữ liệu T²-RAGBench: 23.088 câu hỏi trên 7.318 tài liệu lẫn văn bản và bảng.
- Đo Recall@k, MRR, nDCG và Number Match, kiểm định bootstrap ghép cặp.

#### Kết quả thực nghiệm chính
Pipeline hai giai đoạn (hybrid rồi neural reranking) tốt nhất: Recall@5 0.816, MRR@3 0.605, vượt xa mọi phương pháp một giai đoạn.

- BM25 thắng dense retrieval hiện đại trên tài liệu tài chính.
- Query expansion (HyDE, multi-query) và adaptive retrieval ít lợi cho câu hỏi số liệu chính xác; contextual retrieval cải thiện ổn định.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** So sánh rộng, có kiểm định thống kê, công bố mã. Bằng chứng BM25 vẫn mạnh ở miền cần số liệu chính xác.
- **Hạn chế (Limitations):** Miền tài chính tiếng Anh. Reranker thần kinh tốn thêm chi phí tính toán.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Luận cứ cho việc chọn BM25/FTS5 thay vì vector database và không thêm HyDE hay multi-query. Bài đo trên tài liệu tài chính tiếng Anh, chưa kiểm trên dữ liệu thủ tục tiếng Việt. Ý contextual retrieval không áp dụng cho Hệ thống 2 vì chỉ mục theo cả thủ tục, không theo đoạn.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 3.3 (Retrieval Design)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "On text-and-table documents, BM25 outperformed dense retrieval and a hybrid retriever with neural reranking performed best (Akarsu et al., 2026), which supports lexical BM25 retrieval over structured procedure records for fee and deadline questions."

---

### 16. Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval
- **Tác giả:** Hediyeh Baban, Sai Abhishek Pidaparthi, Samaksh Gulati, Aashutosh Nema (Dell Technologies)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *KDD 2025 Workshop GenAIRecP (Generative AI for Recommender Systems and Personalization)*
- **Phân loại nghiên cứu:** `Multi-Agent System & Optimization`
- **Link DOI / Citation gốc:** [https://genai-personalization.github.io/assets/papers/GenAIRecP2025/11_Baban.pdf](https://genai-personalization.github.io/assets/papers/GenAIRecP2025/11_Baban.pdf)
- **Tệp toàn văn (PDF bản gốc):** [`Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval.pdf`](research%20paper/04_Hybrid_Dual-System_Retrieval/16_Baban_2025_Multi-Agent_Hybrid_Retrieval_KDD/Optimizing%20Retrieval-Augmented%20Generation%20with%20Multi-Agent%20Hybrid%20Retrieval.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/04_Hybrid_Dual-System_Retrieval/16_Baban_2025_Multi-Agent_Hybrid_Retrieval_KDD/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
BM25 và tìm kiếm embedding mỗi thứ có điểm yếu riêng và dễ hụt với câu hỏi phức tạp.

Câu hỏi nghiên cứu: *Kết hợp truy xuất lai với nhiều tác tử phối hợp có cải thiện độ liên quan và tốc độ truy xuất không?*

#### Phương pháp luận & Đóng góp kỹ thuật
Quy trình agentic RAG:

- Kết hợp BM25 và semantic search, gộp kết quả bằng weighted cosine similarity.
- LLM sắp xếp lại tài liệu theo ngữ cảnh.
- Điều phối tác tử bằng LangGraph để xếp hạng và lọc tài liệu.
- Phân tích độ nhạy của trọng số giữa hai kiểu truy xuất.

#### Kết quả thực nghiệm chính
Độ trễ truy xuất giảm 4 lần (từ 43 giây xuống 11 giây) và độ chính xác liên quan tăng 7%.

- Bài thảo luận thêm về khả năng mở rộng và hạn chế của cách làm.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Thực tế, dùng công cụ phổ biến (LangGraph). Có phân tích độ nhạy trọng số lai.
- **Hạn chế (Limitations):** Bài workshop 7 trang; mô tả dữ liệu hạn chế. Miền tài liệu doanh nghiệp/khoa học, không phải pháp lý.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ trích dẫn ở mức ý: kết hợp BM25 và semantic search, LLM sắp xếp lại, điều phối tác tử. V10.5 không có semantic search hay LangGraph. Luồng của V10.5 (trò chuyện, nút 🎯 Tìm chính xác, MCQ, bảng, hỏi tiếp) là tự thiết kế, bài không bàn về chăm sóc khách hàng.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 2.2 (Legal & Regulatory RAG)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Combining BM25 with semantic search and weighting the two scores improved relevance by 7% while cutting retrieval latency from 43 s to 11 s in an agentic RAG workflow (Baban et al., 2025)."

---

### 17. LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval
- **Tác giả:** Yunhan Li, Mingjie Xie, Gaoli Kang, Zihan Gong, Gengshen Wu, Min Yang (City University of Macau; Shenzhen Institutes of Advanced Technology, CAS; SUSTech; Shenzhen University of Advanced Technology)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2601.17692 [cs.IR]*
- **Phân loại nghiên cứu:** `Multi-Agent Query Reformulation & LLM Reranking`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2601.17692](https://arxiv.org/abs/2601.17692)
- **Tệp toàn văn (PDF bản gốc):** [`LegalMALR - Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval.pdf`](research%20paper/04_Hybrid_Dual-System_Retrieval/17_Li_2026_LegalMALR_Query_Understanding/LegalMALR%20-%20Multi-Agent%20Query%20Understanding%20and%20LLM-Based%20Reranking%20for%20Chinese%20Statute%20Retrieval.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/04_Hybrid_Dual-System_Retrieval/17_Li_2026_LegalMALR_Query_Understanding/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Câu hỏi pháp lý thực tế thường ngầm ý, nhiều vấn đề và diễn đạt đời thường. Dense retriever bám mặt chữ của câu hỏi, còn reranker nhẹ thiếu năng lực suy luận pháp lý.

Câu hỏi nghiên cứu: *Làm sao truy xuất đúng điều luật cho câu hỏi đời thường, thiếu thông tin?*

#### Phương pháp luận & Đóng góp kỹ thuật
LegalMALR kết hợp hai thành phần:

- **Multi-Agent Query Understanding System (MAS):** sinh nhiều cách diễn đạt lại có căn cứ pháp lý và truy xuất dense lặp lại để mở rộng tập ứng viên.
- Tối ưu chính sách MAS bằng GRPO để ổn định việc viết lại câu hỏi của LLM.
- **LLM Reranker zero-shot:** suy luận pháp lý bằng ngôn ngữ tự nhiên để xếp hạng cuối.
- Bộ dữ liệu CSAID: 118 câu hỏi khó tiếng Trung, nhiều nhãn điều luật; đánh giá thêm trên benchmark STARD.

#### Kết quả thực nghiệm chính
LegalMALR vượt rõ các baseline RAG mạnh ở cả trong phân phối (CSAID) lẫn ngoài phân phối.

- Hiệu quả đến từ việc kết hợp diễn giải câu hỏi đa góc nhìn, tối ưu bằng học tăng cường và rerank bằng mô hình lớn.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Nhắm đúng khoảng cách giữa từ ngữ đời thường và văn bản luật. Có bộ dữ liệu khó được gán nhãn nhiều điều luật.
- **Hạn chế (Limitations):** Nhiều tác tử cộng LLM reranker tốn tính toán, khó chạy với mô hình 1.5B. Tiếng Trung; CSAID nhỏ (118 câu).

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ mượn ý viết lại câu hỏi đa góc nhìn cho câu người dân hỏi vòng vo. V10.5 hiện dùng từ điển `Database/staging/synonyms.json` và LLM 1 khi từ khoá trượt. Bài tự nêu tốn tính toán và khó chạy với 1.5B nên không dùng.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 2.2 (Legal & Regulatory RAG)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Colloquial, underspecified legal questions defeat surface-form retrieval; LegalMALR recovers the right statutes by rewriting queries into legal terms and reranking with an LLM (Li et al., 2026). We address the same gap more cheaply with a curated synonym table applied before BM25 search."

---

## Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)

### 18. Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective
- **Tác giả:** Rakshit Aralimatti, Syed Abdul Gaffar Shakhadri, Kruthika KR, Kartik Basavaraj Angadi (SandLogic Technologies)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2503.01933 [cs.LG]*
- **Phân loại nghiên cứu:** `Edge AI & Small Model Deployment Study`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2503.01933](https://arxiv.org/abs/2503.01933)
- **Tệp toàn văn (PDF bản gốc):** [`Fine-Tuning Small Language Models for Domain-Specific AI - An Edge AI Perspective.pdf`](research%20paper/05_Local_SLMs_Edge_AI/18_Aralimatti_2025_Fine-Tuning_SLMs_Edge_AI/Fine-Tuning%20Small%20Language%20Models%20for%20Domain-Specific%20AI%20-%20An%20Edge%20AI%20Perspective.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/05_Local_SLMs_Edge_AI/18_Aralimatti_2025_Fine-Tuning_SLMs_Edge_AI/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Chạy LLM lớn trên thiết bị biên gặp chi phí tính toán, tiêu thụ năng lượng và rủi ro quyền riêng tư dữ liệu.

Câu hỏi nghiên cứu: *Mô hình rất nhỏ, nếu được thiết kế và tinh chỉnh cẩn thận, có đáp ứng được bài toán miền cụ thể trên thiết bị biên không?*

#### Phương pháp luận & Đóng góp kỹ thuật
Bài giới thiệu dòng Shakti Small Language Models gồm Shakti-100M, Shakti-250M và Shakti-500M:

- Kết hợp kiến trúc hiệu quả, lượng tử hoá và nguyên tắc AI có trách nhiệm.
- Mô tả pipeline huấn luyện và tinh chỉnh cho miền y tế, tài chính và pháp lý.
- Đánh giá trên benchmark chung (MMLU, HellaSwag), dữ liệu miền và bộ responsible AI (BBQ, ToxiGen).

#### Kết quả thực nghiệm chính
Tác giả kết luận mô hình nhỏ, khi được thiết kế và tinh chỉnh cẩn thận, đáp ứng và nhiều khi vượt kỳ vọng trong kịch bản edge-AI thực tế.

- Ví dụ responsible AI: Shakti-500M đạt 54.08% trên BBQ (Shakti-250M 50.2%) và 51.5% trên ToxiGen (Shakti-250M 47.5%).

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Tập trung vào triển khai trên thiết bị giới hạn tài nguyên. Có tinh chỉnh cho cả miền pháp lý.
- **Hạn chế (Limitations):** Mô hình và báo cáo cùng từ một công ty (SandLogic). Quy mô 100M–500M, không so sánh trực tiếp với Qwen2.5-1.5B.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ trích dẫn ý mô hình nhỏ chạy biên cho miền chuyên biệt. Bài dùng mô hình 100–500M của SandLogic và do chính công ty đánh giá, không so trực tiếp với Qwen2.5-1.5B nên không chứng minh riêng điều gì cho V10.5.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 1 (Introduction)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "Compact language models, when carefully engineered and fine-tuned, can meet domain requirements on edge devices while keeping data local (Aralimatti et al., 2025)."

---

### 19. Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales
- **Tác giả:** Qwen Team (Alibaba Cloud)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2412.15115 [cs.CL]*
- **Phân loại nghiên cứu:** `Technical Report & Foundation Model`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2412.15115](https://arxiv.org/abs/2412.15115)
- **Tệp toàn văn (PDF bản gốc):** [`Qwen2.5 Technical Report - Advancing Open Foundation Models across Scales.pdf`](research%20paper/05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/Qwen2.5%20Technical%20Report%20-%20Advancing%20Open%20Foundation%20Models%20across%20Scales.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/05_Local_SLMs_Edge_AI/19_Qwen_2024_Qwen2.5_Technical_Report/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Cần một dòng mô hình mở có đủ kích cỡ cho nhiều nhu cầu, từ thiết bị biên đến máy chủ.

Câu hỏi nghiên cứu: *Mở rộng dữ liệu tiền huấn luyện và cải tiến hậu huấn luyện nâng năng lực mô hình ở các kích cỡ đến đâu?*

#### Phương pháp luận & Đóng góp kỹ thuật
Qwen2.5 cải tiến cả tiền huấn luyện và hậu huấn luyện:

- Dữ liệu tiền huấn luyện tăng từ 7 lên 18 nghìn tỷ token.
- Hậu huấn luyện: SFT hơn 1 triệu mẫu và học tăng cường nhiều giai đoạn (DPO offline, GRPO online).
- Mô hình mở kích cỡ 0.5B, 1.5B, 3B, 7B, 14B, 32B và 72B (base và instruct), có bản lượng tử hoá; bản hosted dạng MoE là Qwen2.5-Turbo và Qwen2.5-Plus.

#### Kết quả thực nghiệm chính
Qwen2.5-72B-Instruct cạnh tranh với Llama-3-405B-Instruct dù nhỏ hơn khoảng 5 lần.

- Hậu huấn luyện cải thiện sinh văn bản dài, phân tích dữ liệu có cấu trúc và làm theo chỉ dẫn.
- Qwen2.5-1.5B-Instruct và 0.5B-Instruct cải thiện rõ so với thế hệ trước; nhóm tác giả xem chúng phù hợp cho ứng dụng biên tài nguyên hạn chế.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Tài liệu chính thức của mô hình V10.5 đang dùng. Nhiều kích cỡ, có bản lượng tử hoá.
- **Hạn chế (Limitations):** Không có đánh giá riêng cho tiếng Việt. Ở kích cỡ 1.5B, điểm làm theo chỉ dẫn thấp hơn nhiều so với các kích cỡ lớn trong bảng đánh giá nội bộ của báo cáo.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Tài liệu mô tả mô hình nền (`qwen2.5:1.5b`) cho mục thiết lập thực nghiệm. Báo cáo nói điểm làm theo chỉ dẫn ở cỡ 1.5B thấp hơn nhiều so với cỡ lớn, khớp quan sát của V10.5: thêm câu mẫu vào prompt làm kết quả tệ hơn, hỏi tiếp phải để code trích ô. Không có đánh giá riêng tiếng Việt.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 4 (Experimental Setup)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "We use Qwen2.5-1.5B-Instruct (Qwen Team, 2024), a small open-weight member of the Qwen2.5 family that its authors position for resource-constrained edge applications."

---

### 20. Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs
- **Tác giả:** Aldo Pareja, Nikhil Shivakumar Nayak, Hao Wang, Krishnateja Killamsetty, Shivchander Sudalairaj, Wenlong Zhao, Seungwook Han, Abhishek Bhandwaldar, Guangxuan Xu, Kai Xu, Ligong Han, Luke Inglis, Akash Srivastava (Red Hat AI Innovation; MIT-IBM Watson AI Lab; IBM Research)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2412.13337 [cs.LG]*
- **Phân loại nghiên cứu:** `Engineering Methodology & Empirical Guide`
- **Link DOI / Citation gốc:** [https://arxiv.org/abs/2412.13337](https://arxiv.org/abs/2412.13337)
- **Tệp toàn văn (PDF bản gốc):** [`Unveiling the Secret Recipe - A Guide For Supervised Fine-Tuning Small LLMs.pdf`](research%20paper/05_Local_SLMs_Edge_AI/20_Pareja_2024_Guide_SFT_Small_LLMs/Unveiling%20the%20Secret%20Recipe%20-%20A%20Guide%20For%20Supervised%20Fine-Tuning%20Small%20LLMs.pdf)
- **Bản phân tích khoa học chi tiết:** [`literature_review.md`](research%20paper/05_Local_SLMs_Edge_AI/20_Pareja_2024_Guide_SFT_Small_LLMs/literature_review.md)

#### Abstract tóm tắt & Vấn đề giải quyết
Phòng lab lớn tinh chỉnh LLM hiệu quả nhờ tài nguyên và đội ngũ, còn nhà phát triển cá nhân và tổ chức nhỏ thiếu tài nguyên để thử nhiều cấu hình.

Câu hỏi nghiên cứu: *Cấu hình supervised fine-tuning (SFT) nào hiệu quả cho mô hình nhỏ 3B–7B?*

#### Phương pháp luận & Đóng góp kỹ thuật
Nghiên cứu hệ thống về SFT trên tập instruction tuning đa miền, đa kỹ năng:

- 4 mô hình mở cỡ 3B–7B.
- Khảo sát batch size, learning rate, số bước warmup, lịch learning rate, và huấn luyện theo pha (phased) so với gộp (stacked).
- Đối chiếu với khuyến nghị của TULU và cách huấn luyện theo pha của Orca.

#### Kết quả thực nghiệm chính
Nhiều kết quả trái với thực hành phổ biến:

- Batch lớn kết hợp learning rate thấp cho kết quả tốt hơn trên MMLU, MTBench và Open LLM Leaderboard.
- Động lực sớm (gradient norm thấp, loss cao) dự báo mô hình cuối tốt hơn, giúp dừng sớm các lần chạy kém và tiết kiệm tính toán.
- Một số đơn giản hoá về warmup và lịch learning rate không làm giảm hiệu năng.
- Huấn luyện theo pha và gộp không khác biệt đáng kể; gộp đơn giản và hiệu quả mẫu hơn.

#### Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm (Strengths):** Hướng dẫn thực hành cụ thể, có số liệu cho nhiều cấu hình. Phản biện có bằng chứng các khuyến nghị phổ biến (TULU, Orca).
- **Hạn chế (Limitations):** "Small" ở đây là 3B–7B, lớn hơn mô hình 1.5B của V10.5. Chỉ bàn về fine-tuning, không bàn prompt hay guardrail lúc suy luận.

#### Ánh xạ trực tiếp tới kiến trúc V10.5
> **Ý nghĩa kiến trúc:** Chỉ liên quan nếu fine-tune (`Utility/finetune/train_qlora.py`, hiện lr 2e-4, batch hiệu dụng 8). Bài khuyến nghị batch lớn kèm lr thấp và dừng sớm theo động lực huấn luyện, nhưng chạy trên mô hình 3B–7B và không bàn về prompt hay bộ lọc lúc suy luận. Mức giảm 1,55s xuống 0,37–0,42s ở chế độ trò chuyện là nhờ dừng ở dấu xuống dòng và lọc đầu ra, không phải nhờ bài này.

#### Gợi ý trích dẫn khi viết bài báo khoa học (Citation Guidance)
- **Vị trí đề xuất trong bài báo:** `Section 5 (Future Work: fine-tuning)`
- **Mẫu câu trích dẫn học thuật (Draft Context):**
  > "If the base model is later fine-tuned, large batch sizes with low learning rates, and early stopping based on training dynamics, are the recommended recipe for small (3B–7B) LLMs (Pareja et al., 2024)."

---

## Bảng tổng hợp đối sánh 20 bài báo theo khía cạnh dự án V10.5

| STT | Bài báo / Tác giả | Năm | Nơi công bố | Trọng tâm học thuật | Thành phần tương ứng trong V10.5 | Vị trí trích dẫn đề xuất |
|:---:|---|:---:|---|---|---|---|
| **1** | *GuidaPA* (Daniel M. Jimenez-Gutierrez) | 2026 | arXiv preprint | Primary Architecture & Privacy-Preserving System | Bối cảnh cho việc chạy mô hình và CSDL cục bộ (Ollama); V10.5 không dùng học liên kết | `Section 1 (Introduction)` |
| **2** | *GovAI-Pipe* (Ahmet Kaplan) | 2026 | arXiv preprint | Governance Framework (Design Science Research) | Khung quản trị để đối chiếu nhật ký, phản hồi 👍/👎; chưa có chuyển cho cán bộ | `Section 5 (Discussion: governance)` |
| **3** | *Grip on LLMs* (Laurens Samson) | 2026 | arXiv preprint | Empirical Benchmark & Civil Service Survey | Khung tiêu chí đánh giá: tách factuality và honesty (chưa có bộ câu đo honesty) | `Section 4 (Evaluation Methodology)` |
| **4** | *COPAL* (Yingjie Liu) | 2026 | arXiv preprint | Benchmark & Alignment Methodology | Ý "hợp đồng xử lý" cho bộ test (phải nêu / phải tránh); chưa áp dụng trong code | `Section 4 (Evaluation Methodology)` |
| **5** | *LegalCheck* (Virgill van der Meer) | 2026 | arXiv preprint / ICAIL 2026 | Primary Architecture & Case Study | Chỉ làm bối cảnh (soạn thư pháp lý có chuyên gia duyệt); không liên quan xếp hạng thẩm quyền | `Section 2.2 (Legal & Regulatory RAG)` |
| **6** | *LegalBench-RAG* (Nicholas Pipitone) | 2024 | arXiv preprint | Standard Benchmark & Evaluation Methodology | Luận cứ không thêm reranker đa dụng; xếp hạng FTS5 viết tay; gợi ý đo ở mức đoạn | `Section 3.3 (Retrieval Design)` |
| **7** | *CanLegalRAGBench* (Ethan Zhao) | 2026 | arXiv preprint | Benchmark & Legal RAG Evaluation | Khung bộ đo: claim không có căn cứ, biến thể câu hỏi kiểm soát, bộ giữ riêng | `Section 4 (Evaluation Methodology)` |
| **8** | *HyPA-RAG* (Rishi Kalra) | 2024 | NAACL 2025 Industry / CustomNLP4U @ EMNLP 2024 | Primary Architecture & Adaptive Algorithm | Chỉ trích dẫn (truy xuất lai, tham số theo độ phức tạp); V10.5 không có bộ phân loại độ phức tạp | `Section 2.2 (Legal & Regulatory RAG)` |
| **9** | *Chain-of-Verification (CoVe)* (Shehzaad Dhuliawala) | 2023 | Findings of ACL 2024 | Foundational Methodology & Algorithm | Đối chiếu khái niệm với `verifier.py`; V10.5 không cài CoVe, viết lại chỉ cứu 3/12 câu | `Section 2.3 (Hallucination Mitigation)` |
| **10** | *Self-RAG* (Akari Asai) | 2024 | ICLR 2024 | Foundational Model Framework | Cách chia ba kiểm tra (cần tra, liên quan, được hỗ trợ) ↔ gatekeeper, xếp hạng nguồn, verifier | `Section 2.3 (Hallucination Mitigation)` |
| **11** | *CRITIC* (Zhibin Gou) | 2024 | ICLR 2024 | Interactive Verification Architecture | Luận cứ verifier dựa vào luật đối chiếu nguồn; luật chưa kiểm trên bộ câu độc lập | `Section 3.4 (Verification: rules vs self-critique)` |
| **12** | *GASP* (Mohamed Aly Bouke) | 2026 | arXiv preprint | Empirical Detection Methodology | Chỉ trích dẫn ý; chưa dùng được trên Ollama (cần chấm xác suất câu có sẵn) | `Section 2.3 (Hallucination Mitigation)` |
| **13** | *Multi-Modal Fact-Verification* (Piyushkumar Patel) | 2025 | arXiv preprint | System Framework & Cross-Verification | Nền cho ý dùng nhiều nguồn; V10.5 tách hai hệ thống, không đối chiếu chéo tự động | `Section 3.1 (Dual-System Pipeline)` |
| **14** | *CRAG* (Shi-Qi Yan) | 2024 | arXiv preprint | Primary Architecture & Fallback Mechanism | Đối chiếu: `confident` / MCQ / `no_evidence` của Hệ thống 2; Web search chưa có cổng bằng chứng | `Section 5 (Future Work: evidence gate)` |
| **15** | *From BM25 to Corrective RAG* (Meftun Akarsu) | 2026 | arXiv preprint | Comparative Benchmark & Strategy Study | Luận cứ chọn SQLite FTS5 (BM25) thay vì vector DB và không thêm HyDE | `Section 3.3 (Retrieval Design)` |
| **16** | *Multi-Agent Hybrid Retrieval* (Hediyeh Baban) | 2025 | KDD 2025 Workshop (GenAIRecP) | Multi-Agent System & Optimization | Chỉ trích dẫn ở mức ý (BM25 + semantic, LLM sắp xếp lại); V10.5 không có semantic search | `Section 2.2 (Legal & Regulatory RAG)` |
| **17** | *LegalMALR* (Yunhan Li) | 2026 | arXiv preprint | Multi-Agent Query Reformulation & LLM Reranking | Chỉ mượn ý viết lại câu hỏi; V10.5 dùng `synonyms.json` + LLM 1 khi từ khoá trượt | `Section 2.2 (Legal & Regulatory RAG)` |
| **18** | *Fine-Tuning SLMs (Shakti)* (Rakshit Aralimatti) | 2025 | arXiv preprint | Edge AI & Small Model Deployment Study | Chỉ trích dẫn ý mô hình nhỏ chạy biên; bài không so với Qwen2.5-1.5B | `Section 1 (Introduction)` |
| **19** | *Qwen2.5 Technical Report* (Qwen Team) | 2024 | arXiv preprint | Technical Report & Foundation Model | Mô hình nền `qwen2.5:1.5b` cho mục thiết lập thực nghiệm | `Section 4 (Experimental Setup)` |
| **20** | *Unveiling the Secret Recipe* (Aldo Pareja) | 2024 | arXiv preprint | Engineering Methodology & Empirical Guide | Chỉ liên quan nếu fine-tune (`train_qlora.py`); không phải nguồn của mức giảm độ trễ | `Section 5 (Future Work: fine-tuning)` |

---

## Khung cấu trúc bài báo khoa học đề xuất cho Dự án V10.5

> Dựa trên 20 bài báo khoa học đã thu thập và đánh giá, nhóm nghiên cứu V10.5 có thể tổ chức bài báo khoa học (dự kiến gửi Hội nghị/Tạp chí quốc tế thuộc IEEE/ACM/Springer hoặc SCITEPRESS) theo khung 5 phần sau:

```
[Title Proposal]
A Grounded Dual-System RAG Architecture with Local Edge SLMs for Verified Public Administration Assistance
(Kiến trúc RAG hệ thống kép có kiểm chứng với mô hình ngôn ngữ nhỏ cục bộ cho trợ lý hành chính công)
```

### 1. Introduction (Mở đầu)
- **Bối cảnh:** Chuyển đổi số dịch vụ công và áp lực giải đáp thủ tục hành chính cho người dân tại cấp Xã/Phường.
- **Thách thức cốt lõi:**
  1. Rủi ro ảo giác số liệu (lệ phí, thời hạn giải quyết, thành phần hồ sơ) gây hậu quả thực tế cho người dân. Các bài đo tỉ lệ claim không có căn cứ trong RAG pháp lý: *Zhao et al., 2026* (8–29%); chatbot chính phủ cần đánh giá vượt ra ngoài độ chính xác: *Samson et al., 2026*.
  2. Dữ liệu nội bộ của cơ quan hành chính không nên gửi lên dịch vụ đám mây ngoài (*GuidaPA - Jimenez-Gutierrez et al., 2026*; mô hình nhỏ chạy biên: *Aralimatti et al., 2025*).
- **Đóng góp của nghiên cứu (chỉ nêu những gì V10.5 đã làm và đã đo):**
  - Kiến trúc hai hệ thống chạy song song, người dùng chọn: Hệ thống 2 tra CSDL SQLite FTS5 gồm 1.350 thủ tục cấp Xã/Phường (tra từ khoá, hỏi trắc nghiệm MCQ chọn thủ tục, bảng do code dựng, không do mô hình sinh); Hệ thống 1 tra web .gov.vn qua MCP kèm bước kiểm chứng.
  - Nguyên tắc nói thật khi thiếu dữ liệu: ô trống trong bảng ghi "Chưa có thông tin", câu do mô hình tự diễn đạt gắn nhãn "có thể có sai sót".
  - Chạy Qwen2.5-1.5B cục bộ qua Ollama. Chế độ trò chuyện của Hệ thống 2 giảm từ 1,55 giây xuống 0,37–0,42 giây (đo 17 câu, 24/09/2026) nhờ dừng sinh ở dấu xuống dòng và lọc đầu ra.

### 2. Related Work (Các nghiên cứu liên quan)
- **2.1. AI & Chatbots in Public Administration:** *GuidaPA - Jimenez-Gutierrez et al., 2026; GovAI-Pipe - Kaplan, 2026; Grip on LLMs - Samson et al., 2026; COPAL - Liu et al., 2026*.
- **2.2. Legal & Regulatory Retrieval-Augmented Generation:** RAG pháp lý và quy định: soạn văn bản dựa trên truy xuất, benchmark truy xuất, tỉ lệ khẳng định không có căn cứ, truy xuất thích ứng (*LegalCheck - van der Meer & Rossi, 2026; LegalBench-RAG - Pipitone & Houir Alami, 2024; CanLegalRAGBench - Zhao et al., 2026; HyPA-RAG - Kalra et al., 2024*); viết lại truy vấn (*LegalMALR - Li et al., 2026*); BM25 thắng dense trên tài liệu nhiều số liệu (*Akarsu et al., 2026*).
- **2.3. Hallucination Mitigation & Fact Verification:** *CoVe - Dhuliawala et al., 2023; Self-RAG - Asai et al., 2024; CRITIC - Gou et al., 2024; CRAG - Yan et al., 2024; GASP - Bouke, 2026; Patel, 2025*.
- **2.4. Edge SLM Deployment & Domain SFT:** *Aralimatti et al., 2025; Qwen Team, 2024; Pareja et al., 2024*.

### 3. Proposed Architecture (Kiến trúc hệ thống đề xuất)
- **3.1. Overview & Dual-System Pipeline:** Nút "Web search" chọn hệ thống; mỗi cuộc trò chuyện ghi nhớ hệ thống của nó (đổi hệ thống thì mở cuộc trò chuyện mới). Hệ thống 2 chạy theo ba trạng thái: trò chuyện (LLM 2, nhãn "AI tự trả lời"), nút 🎯 Tìm chính xác (tra từ khoá, LLM 1 chỉ khi trượt, MCQ, bảng), hỏi tiếp (code trích ô, hoặc LLM 2 chỉ đọc mục liên quan). Mã nguồn: `Backend/core/system_retrieval.py`, `system_websearch.py`.
- **3.2. Intent Routing & Gatekeeper:** Hệ thống 1 dùng bước hiểu ý định và bộ gác hỏi lại (`core/intent.py`). Hệ thống 2 nhận diện câu hỏi thủ tục bằng luật theo CSDL (`retrieval.looks_like_procedure`), không dùng LLM.
- **3.3. Retrieval Design:** Chuẩn hoá từ vựng dân gian (`Database/staging/synonyms.json`, viết tắt, bỏ lời đệm) rồi tra FTS5 ba tầng (AND trên tên/lĩnh vực, AND có mô tả, OR có ngưỡng khớp) với cờ `confident`; nhắc tên tỉnh thì xếp bản của tỉnh đó lên trước; MCQ "thủ tục chính, rồi dạng cụ thể".
- **3.4. Verification & Output Guard:** Hệ thống 1: bản nháp đi qua verifier (luật đối chiếu nguồn cho số tiền, thời hạn, số hiệu văn bản, thẩm quyền, cộng một lượt LLM), viết lại tối đa một lần, hết lượt thì lược chi tiết không khớp và cảnh báo; trích dẫn `[S#]` do code gắn cho dòng chép gần nguyên văn từ nguồn (độ phủ ≥ 85%). Hệ thống 2: bảng do code dựng, câu hỏi về một ô được code trích nguyên văn, đầu ra của LLM 2 qua bộ lọc (chữ Hán/Nhật, tiếng Anh, con số khi chưa tra CSDL).

### 4. Experimental Evaluation (Đánh giá thực nghiệm)
> Mọi số liệu dưới đây do nhóm tự đo trên bộ câu tự soạn, mỗi mốc đo một lần; bộ câu đã được dùng để chỉnh luật nên chưa phải kết quả độc lập. Độ đúng nội dung chưa được người chấm.

- **Hệ thống 2 (`Evaluation/check_natural_questions.py`, không cần mô hình):** 103 câu hỏi thủ tục kiểu người dân và 10 câu xã giao. Nhận ra câu hỏi thủ tục để gợi ý "Tìm chính xác": 100/103; thủ tục đúng nằm trong 3 lựa chọn đầu: 102/103 (đo 30/09/2026, 98/98 mục kiểm tra đạt).
- **Hệ thống 1 (`Evaluation/evaluate.py`, 45 câu tự soạn, qwen2.5:1.5b, tra mạng thật):** intent 40/45, hỏi lại đúng lúc 39/42, verifier cho qua 26/35, có nguồn chính thống 24/35, có `[S#]` 25/35 (do code gắn, chỉ số này không độc lập với luật gắn). Trung vị 40,0 giây, p95 75,3 giây (lần chạy 24/09 22:49, thời gian có thể bị đẩy cao vì máy dùng chung GPU; các lần chạy khác dao động vài câu).
- **Độ trễ chế độ trò chuyện (Hệ thống 2):** 1,55 giây xuống 0,37–0,42 giây, đo 17 câu.
- **Cần bổ sung trước khi gửi bài:** độ đúng nội dung do người chấm, bộ câu độc lập để đo khái quát, đo bộ nhớ và độ trễ trên phần cứng mục tiêu, so sánh có kiểm soát với mô hình không có bước kiểm chứng.

### 5. Discussion & Future Work (Thảo luận & Hướng phát triển)
- Hạn chế: mô hình 1.5B yếu ở câu cần suy luận và đôi khi viết sai chữ có dấu; Web search chậm (chủ yếu ở bước tra mạng) và nguồn thay đổi mỗi lần; verifier cho qua chưa có nghĩa là đúng.
- Hướng phát triển: kiểm tra bằng chứng đủ chưa trước khi soạn (theo hướng CRAG, bằng luật), bộ câu độc lập và chấm tay, bộ câu đo honesty, fine-tune khi đã có dữ liệu phản hồi được chấm.
- Khả năng mở rộng sang cấp Tỉnh và thích ứng khi văn bản pháp luật thay đổi cần dữ liệu và thử nghiệm riêng, chưa có kết quả.

# Literature Review Matrix (khuôn B4, bước 4)

- Mỗi dòng ứng với một tệp `paper_summaries/paper_NN.md`.
- Thông tin lấy từ bài gốc, kiểm ngày 25/10/2026.
- "Không nêu" nghĩa là bài không báo cáo điều đó.
- Nhóm theo khuôn B2: bài 01–07 liên quan trực tiếp, bài 08–11 về model hay phương pháp, bài 12–16 về lĩnh vực.

| Paper | Domain | AI Model / Method | Dataset | Evaluation Metrics | Main Contribution | Limitation | Relevance |
|---|---|---|---|---|---|---|---|
| Paper 01 (PhamDuy2023) | Dịch vụ công Việt Nam | BM25+ và SimCSE/PhoBERT, xếp lại bằng cross-encoder | 4.547 FAQ của Cổng DVC, 785.996 đoạn luật | Recall@k, F2, MAP, NDCG | Hệ hỏi đáp dịch vụ công tiếng Việt | Loại các câu không có đáp án; câu hỏi là FAQ do cổng viết; không đo việc từ chối | Cao: công trình gần nhất, là căn cứ cho khoảng trống |
| Paper 02 (Larson2019) | Trợ lý ảo, tiếng Anh | SVM, CNN, BERT…; ngưỡng xác suất hoặc thêm lớp ngoài phạm vi | CLINC150: 23.700 câu do crowdworker viết | Độ chính xác trong phạm vi, recall ngoài phạm vi | Bộ dữ liệu có câu ngoài phạm vi | Câu ngắn, không phải câu thật | Cao: cùng phát hiện "làm tốt trong phạm vi nhưng không biết từ chối" |
| Paper 03 (Rajpurkar2018) | Đọc hiểu, tiếng Anh | Các model đọc hiểu | SQuAD cộng 53.775 câu không trả lời được | EM, F1 | Câu không trả lời được viết theo lối đối kháng | Từ chối chỉ xét trong một đoạn văn | Trung bình: chứng cứ rằng điểm giảm mạnh khi có câu không có đáp án |
| Paper 04 (Kamath2020) | Hỏi đáp, tiếng Anh | Calibrator (random forest) so với MaxProb | SQuAD và 5 bộ ngoài miền | Độ phủ ở độ chính xác 80%, AUC rủi ro–độ phủ | Từ chối có chọn lọc khi lệch miền | Cần dữ liệu ngoài miền có nhãn | Cao: xác suất của model không đáng tin trên câu lệch miền |
| Paper 05 (Aliannejadi2019) | Tìm kiếm web, tiếng Anh | Truy hồi và chọn câu hỏi làm rõ | Qulac: 198 chủ đề TREC | P@1, MRR… | Đặt bài toán hỏi lại | Không có hành vi từ chối | Trung bình: cơ sở cho hành vi `clarify` |
| Paper 06 (Wen2025) | LLM nói chung | Bài khảo sát | Không có (khảo sát) | Abstention precision, recall, rate | Khung 3 góc nhìn về việc từ chối | Không có thực nghiệm | Cao: khung lý thuyết; nêu từ chối ở ngôn ngữ ít tài nguyên còn kém |
| Paper 07 (Rebedea2023) | Ứng dụng LLM | Rào chắn (rail) do người viết bằng Colang | Ví dụ minh hoạ | Tỉ lệ chặn hoặc cho qua (quy mô nhỏ) | Bộ công cụ rào chắn chạy độc lập với LLM | Bằng chứng mới ở mức demo | Cao: gần nhất với lớp luật của bài 1 |
| Paper 08 (Qwen3) | Model nền | Qwen3-4B-Instruct-2507 | 36 nghìn tỉ token, 119 ngôn ngữ | Các benchmark chung | Họ model mở có cả chế độ thinking và non-thinking | Báo cáo không mô tả bản 2507 | Cao: model 4B chạy tại máy (phương án C và baseline RAG) |
| Paper 09 (BGEM3) | Embedding đa ngôn ngữ | BGE-M3: dense, sparse, multi-vector | MIRACL, MKQA… | nDCG, Recall | Một model cho ba kiểu truy hồi | Không đo trên thủ tục hành chính | Cao: lấy ứng viên cho phương án B và baseline RAG |
| Paper 10 (CRAG2024) | RAG | Bộ đánh giá truy hồi chọn hành động | PopQA, Biography… | Accuracy, FactScore | Sửa sai khi truy hồi kém | Bản preprint | Trung bình: tương tự ngưỡng reranker của phương án B |
| Paper 11 (SelfRAG2024) | RAG | Model sinh token tự phê bình | Nhiều bộ QA và sinh văn bản | Accuracy, citation precision/recall… | Model tự quyết khi nào truy hồi | Phải huấn luyện lại model | Trung bình: đối lập với cách "luật quyết định" |
| Paper 12 (ViGPTQA2023) | Hỏi đáp tiếng Việt, có luật | ViGPT (từ gpt-j-6B), RAG | Dữ liệu do AI sinh và do người viết | Điểm do người chấm | LLM tiếng Việt mở | Không đo việc từ chối | Trung bình: lĩnh vực gần, cách làm "model sinh" |
| Paper 13 (Hien2025) | Văn bản luật Việt Nam | RAG ba chỉ mục, GPT-4 | 45.000 văn bản luật | RAGAS, khảo sát người dùng | RAG cho truy vấn văn bản luật | Có bước phân loại ngoài phạm vi nhưng không đo riêng; dùng API ngoài | Trung bình |
| Paper 14 (LegalCheck2026) | Pháp lý cấp thành phố (Hà Lan) | RAG kết hợp CAG | Hồ sơ khiếu nại thật | Recall, Precision, F1 so với thư người viết; thời gian | Soạn thư tư vấn, có người duyệt | Chỉ một cơ quan, không có nhóm đối chứng | Trung bình: bối cảnh cơ quan cấp cơ sở |
| Paper 15 (GovAIPipe2026) | Chính phủ điện tử (Thổ Nhĩ Kỳ) | Quy trình quản trị 4 lớp | Không có | Không có (chỉ phân tích) | Gắn yêu cầu luật với các bước kỹ thuật | Khung khái niệm, chưa triển khai | Thấp–trung bình: nêu rủi ro khi chatbot hướng dẫn sai |
| Paper 16 (GripOnLLMs2026) | Chính quyền Amsterdam | Đánh giá hơn 30 LLM | HONESTCITYBENCH: 530 câu | Factuality, honesty, bias, chi phí | Benchmark 6 chiều theo giá trị công | Chấm bằng LLM; bản preprint | Cao: trả lời đúng không kéo theo biết từ chối |
| Paper 17 (GuidaPA2026) | Hành chính công (Ý) | Tinh chỉnh LLM 7B–8B bằng học liên kết, QLoRA 4-bit | Tài liệu công khai SIGESON, SIDFORS | ROUGE, BLEU-4, METEOR | Chatbot hành chính giữ dữ liệu tại chỗ | Hai nền tảng, ít tài liệu; chỉ chỉ số tự động; không đo từ chối | Trung bình: căn cứ cho việc chạy model nhỏ trên một máy |
| Paper 18 (Geifman2017) | Học máy (phân loại ảnh) | Phân loại có chọn lọc: hàm từ chối theo ngưỡng tin cậy, chọn ngưỡng để bảo đảm rủi ro | CIFAR, ImageNet | Rủi ro, độ phủ | Đánh đổi rủi ro–độ phủ có bảo đảm xác suất | Chỉ phân loại ảnh; không có ngoài phạm vi, không có hỏi lại | Trung bình: căn cứ cho ý chỉ trả lời khi đủ tin cậy (Discussion, Conclusion) |
| Paper 19 (Gilardi2023) | Gán nhãn văn bản (khoa học xã hội) | ChatGPT gán nhãn zero-shot, so với crowd worker và người được đào tạo | 2.382 tweet, 5 tác vụ | Độ chính xác, độ nhất quán, chi phí | LLM gán nhãn tốt hơn crowd worker ở 4/5 tác vụ, rẻ hơn khoảng 20 lần | Tweet tiếng Anh, một model; chuẩn là nhãn người được đào tạo | Trung bình: bàn về độ tin cậy của nhãn do LLM đề xuất (Related Work, Limitations) |
| Paper 20 (Lewis2020) | NLP, hỏi đáp miền mở | RAG: seq2seq + chỉ mục vector Wikipedia, bộ truy hồi nơ-ron | Ba bộ hỏi đáp miền mở và các tác vụ sinh văn bản | Độ chính xác hỏi đáp, chất lượng văn bản | Gốc của thiết kế RAG | Không xét từ chối hay câu ngoài phạm vi | Trung bình: gốc của baseline R |
| Paper 21 (Dwork2015) | Thống kê, học máy | Tập giữ lại dùng lại được (Thresholdout) | Không áp dụng | Lý thuyết | Dùng lại test thích nghi gây quá khớp | Cần thêm nhiễu, giới hạn số lần truy vấn | Cao: lý do khoá test và chạy một lần |
| Paper 22 (Brodersen2010) | Đánh giá phân loại | Độ chính xác cân bằng và phân phối hậu nghiệm | Không áp dụng | Accuracy so với balanced accuracy | Chỉ số cho dữ liệu lệch lớp | — | Cao: chỉ số chính của bài 1 |
| Paper 23 (Wilson1927) | Thống kê | Khoảng điểm cho một tỉ lệ | Không áp dụng | — | Khoảng Wilson | Gần đúng | Trung bình: khoảng tin cậy cho mọi tỉ lệ |
| Paper 24 (McNemar1947) | Thống kê | Phép kiểm trên các cặp bất đồng | Không áp dụng | — | Phép kiểm McNemar | Không cho cỡ hiệu ứng | Trung bình: mọi so sánh cặp |
| Paper 25 (Cohen1960) | Thống kê | Hệ số đồng thuận κ | Không áp dụng | — | κ cho thang định danh | Phụ thuộc phân bố nhãn | Trung bình: đồng thuận giữa hai lượt nhãn |
| Paper 26 (HF-dvc) | Dữ liệu dịch vụ công | Hỏi đáp Cổng DVC Bình Định | ~1,07 nghìn dòng | — | Nguồn câu hỏi thật | Không ghi giấy phép | Cao: nguồn dữ liệu |
| Paper 27 (HF-mps) | Dữ liệu dịch vụ công | Hỏi đáp Cổng DVC Bộ Công an | ~809 dòng | — | Nguồn câu hỏi thật | Không ghi giấy phép | Cao: nguồn dữ liệu |
| Paper 28 (DVC) | Tri thức thủ tục | Cổng Dịch vụ công Quốc gia | 1.517 thủ tục, 542 trong phạm vi | — | Nguồn của câu trả lời | Ảnh chụp ngày 13/10/2026 | Cao: nguồn tri thức |
| Paper 29 (bge-reranker-v2-m3) | Truy hồi | Cross-encoder đa ngôn ngữ | — | — | Chấm độ khớp câu hỏi–văn bản | Điểm khớp không phải phạm vi | Trung bình: phương án B |

## Kết luận từ ma trận (bước 5)

1. **Chưa có bài nào** đo cả ba hành vi (trả lời, hỏi lại, từ chối) trên **câu hỏi thật** của người dân về thủ tục hành chính, với tập test khoá trước khi sửa code.
2. Các bài có hành vi từ chối (02, 03, 04) dùng câu do crowdworker viết hoặc dữ liệu đọc hiểu tiếng Anh.
3. Các bài về dịch vụ công và pháp lý tiếng Việt (01, 12, 13) không đo việc từ chối.
4. Bài 02 và bài 16 đều thấy: làm tốt câu trong phạm vi, hay trả lời đúng, không có nghĩa là biết từ chối. Bài 1 kiểm lại điều này trên câu hỏi thật về thủ tục **cấp xã/phường** ở Việt Nam.

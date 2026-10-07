# System 4 — Nhiệm vụ 1/4: Nền tảng (web chung, toggle, config, Git, cài đặt, deploy)

Thứ tự: **NV1 (tệp này)** → [NV2 AI trò chuyện](SYSTEM4_NV2_AI_TRO_CHUYEN.md) → [NV3 Dataset → Specialist](SYSTEM4_NV3_DATASET.md) → [NV4 Quản trị](SYSTEM4_NV4_QUAN_TRI.md).
Tệp này chứa luôn **quy tắc chung** cho cả 4 nhiệm vụ.

---

## Phần A — Yêu cầu gốc (nguyên văn, chỉ thêm tiêu đề)

Dự án Instant Specialist – System 4 build on top System 3 as a parallel:

### A1. Quy tắc chung — cách nói chuyện (áp dụng cho cả 4 nhiệm vụ)

Yêu cầu khi nói chuyện với tôi:
- Nói chuyện với tôi ngắn gọn thôi.
- Khi bạn có câu hỏi hãy hỏi dạng trắc nghiệm 4 lựa chọn cho mình chọn nhé.
- Tôi là dân không chuyên về cả AI lẫn Software Engineering nên dùng các thuật ngữ dễ hiểu thôi, chủ yếu tôi muốn bàn kiểu behavior của web và bạn giải quyết các phần cần kiến thức chuyên sâu giúp mình nhé
- Khi prompt tôi viết tiếng Việt, dùng tiếng Việt - Khi prompt tôi viết tiếng Anh, dùng tiếng Anh
- Trả lời ngắn gọn, đúng trọng tâm và nhanh đối với prompt của tôi sau đó mới đề cập các phần phải chú ý khác.
- Mình thích trả lời dạng bảng hoặc ngắn gọn rồi mới giải nghĩa sau

### A2. Quy tắc chung — quy trình mỗi nhiệm vụ (áp dụng cho cả 4 nhiệm vụ)

Mỗi nhiệm vụ sẽ ứng với 1 quá trình như sau: (Bước này có thể có hoặc không) Mình thêm các tiêu chí cụ thể hơn nữa cho file .docx trước khi bạn làm → Yêu cầu bạn đọc lại file và xác nhận → (Bước này có thể có hoặc không) bạn hỏi mình chọn các trade-offs dạng trắc nghiệm 4 lựa chọn. -> lập kế hoạch cụ thể chờ mình Approve → (Bước này có thể có hoặc không) sửa kế hoạch theo yêu cầu của mình → Thực hiện nhiệm vụ đấy 1 mạch, nếu có việc gì ngoài ý muốn xảy ra thì viết cách bạn đã handle nó trong document và re-surface nó trong báo cáo. Nếu là trade-offs nữa thì cũng cho mình dạng trắc nghiệm 4 lựa chọn và bạn quay lại sửa theo lựa chọn của mình (Ưu tiên behavior phải chuẩn xác theo những gì mình đã specify)

### A3. Quy tắc chung — trade-off và nhắc nhở

- Lý tưởng thì mình muốn sản phẩm không có trade-off nhưng mình sẵn sàng thỏa thuận để nó có thể làm được so với công nghệ hiện tại. Bạn hãy liệt kê các trade-off dạng trắc nghiệm 4 lựa chọn cho mình chọn nhé. Tối đa 10 câu MCQs và ngắn gọn thôi.
- Nhắc mình nếu mình quên 1: Virtual Environment của bạn không tải file lớn được nên cho mình Terminal code hoặc viết vào set up first time.bat các công nghệ cần thiết trước khi xây dựa trên Architecture bạn sẽ đề ra nhé. Mình chưa có Qwen 4B và mình muốn các thư viện được tải riêng vào .venv file và ghi rõ thư viện gì và phiên bản trong requirements.txt
- Nhắc mình nếu mình quên 2: File này cực kỳ Unstructured, mình muốn bạn chia nó ra thành từng nhiệm vụ cụ thể lưu thành các files .md D:\Claude\System 3\intern-amazing-group_7-system3\docs (không quá 4 nhiệm vụ), bạn chỉ được thêm tiêu đề và chia các yêu cầu ra từng category nhưng phải giữ 100% từ của mình đã viết ra, bạn được thêm các ý mới ở 1 section khác cái section quote yêu cầu của mình.
- Nhắc mình nếu mình quên 3: Ngay sau khi nhận và đọc tài liệu này bạn hỏi rõ mình cần chấp nhận trade-offs gì so với yêu cầu của mình dạng trắc nghiệm 4 lựa chọn trước khi chia nhiệm vụ nhé.

### A4. Yêu cầu riêng của nhiệm vụ này

Làm cho tôi 1 web AI đảm bảo các tiêu chí sau:
- Hoạt động end to end
- architecture và công nghệ bạn làm theo workflow tôi gửi nhưng có caveat hay trade-offs gì báo tôi trước khi làm nhé
- Bạn dùng trang web của D:\Claude\System 3\intern-amazing-group_7-system3 nhưng tuyệt đối không chạm vào hệ thống đang có hay các tools mà AI hiện tại đang dùng nhé, đây là 1 hệ thống hoàn toàn song song trên cùng 1 web và đổi bằng 1 toggle.
- Phần backend bạn tự quyết định hoàn toàn mình không can thiệp, chỉ cần behavior đúng ý được rồi
- Về cấu trúc file mình muốn như file hiện tại, nhưng bạn nhớ cập nhật Set up first time.bat
- Code và tài liệu của bạn nằm trong các thư mục, nhớ dùng Git để giữ versions. Cuối cùng mình sẽ muốn là các behavior của web và AI dễ dàng thay đổi bằng config.py (có toggle-able UI trên web chính)
- Chạy Local 100% không cần internet
- Bạn hãy làm nó sẵn sàng cho bước deploy có trong sơ đồ trong file

### A5. Trade-off đã chọn (nguyên văn câu trả lời, 2026-10-07)

| Câu | Trả lời |
|---|---|
| 1. Toggle vs "không chạm System 3" | 1A |
| 5. Công nghệ trong sơ đồ | 5A |
| 7. Người dùng | 7A |

**Trade-off riêng của NV1** (nguyên văn câu trả lời, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 1. Ai phải đăng nhập | 1B (Don't forget to make both login&sign up) |
| 2. Cách System 4 chạy | 2A |
| 3. Toggle hoạt động thế nào | 3B |
| 4. Panel cấu hình lưu vào đâu | 4A&B (dev have option to set new default directly here) (reload the web to apply settings btw) |
| 5. Git | 5A&B as another branch in https://github.com/3-hWnG/intern-amazing-group_7/tree/system3 only commit on remote branch when I say so, now create the new branch as System_3&4 |
| 6. Reranker | 6B |
| 7. "Sẵn sàng deploy" | 7C |

---

## Phần B — Ý bổ sung của Claude (không phải yêu cầu gốc)

**Nghĩa của các lựa chọn**
- 1A: thêm **vài dòng** vào trang web và server chung (nút toggle + cửa vào System 4). Mọi thứ khác của System 4 nằm trong thư mục mới. Code, công cụ và dữ liệu đang chạy của System 3 giữ nguyên.
- 5A: chạy bản nhẹ tại máy (SQLite + kho vector nhúng + Ollama) thay cho Qdrant/PostgreSQL/Redis/vLLM. Mỗi phần nằm sau một "cửa" riêng để sau này thay bằng dịch vụ thật trong sơ đồ mà không phải viết lại. Kèm Dockerfile + docker-compose để sẵn sàng deploy.
- 7A: đăng nhập tại máy, hai vai trò: **dev** (quản trị) và **user**.
- Theo tên ảnh kiến trúc: **Strict mode = System 3 (đã có)**, **Friendly mode = System 4 (làm mới)**.

**Việc dự kiến trong nhiệm vụ này** (sẽ chốt ở bước kế hoạch)
1. `git init` + commit đầu tiên cho toàn bộ project hiện tại, để System 3 có một mốc gốc trước khi động vào bất cứ thứ gì.
2. Thư mục mới cho System 4, cùng kiểu chia thư mục với System 3 (server / web / data / eval / docs).
3. Toggle Strict ↔ Friendly trên web chung.
4. `config.py` riêng của System 4 + panel bật/tắt trên web.
5. Đăng nhập cơ bản (dev/user).
6. Cập nhật `Set up first time.bat` và `requirements.txt` theo kiểu **chỉ thêm**: các bước cũ của System 3 giữ nguyên.
7. Dockerfile/compose sẵn cho bước deploy.

**Tải về dự kiến (Nhắc nhở 1)**: Qwen3-4B đã có trong Ollama trên máy. Còn cần: model tìm kiếm BGE-M3 (~1,2–2,3 GB), model xếp hạng lại bge-reranker-v2-m3 (~1,1–2,3 GB), và vài thư viện Python (đọc Excel/PDF/DOCX, kho vector, mã hoá mật khẩu). Danh sách chính xác + phiên bản sẽ được ghi vào `requirements.txt` và `Set up first time.bat` ở bước kế hoạch, **trước khi xây**.

**Câu hỏi mở cho bước kế hoạch** (đã trả lời: 1B, 2A)
- Đăng nhập có áp dụng cho cả Strict mode (System 3, hiện chưa có đăng nhập) hay chỉ Friendly mode?
- System 4 chạy chung một tiến trình server với System 3 hay tách riêng? (Hành vi người dùng thấy là như nhau.)

---

## Phần C — Báo cáo thực hiện NV1 (2026-10-07)

**Đã làm** (chi tiết: [system4/README.md](../system4/README.md))

| # | Việc | Kết quả |
|---|---|---|
| 1 | Git | Repo nối với GitHub; nhánh `System_3&4` tạo từ `system3` (chưa đẩy commit nào). Commit mốc + commit NV1 **chỉ ở máy**. |
| 2 | Thư mục `system4/` | server / web / tests + `config.py` riêng |
| 3 | Đăng nhập + đăng ký (1B) | Cả web phải đăng nhập; tài khoản đầu tiên = dev |
| 4 | Trang chung | Bản sao giao diện System 3 + công tắc Strict/Friendly + danh sách chung có nhãn (3B) |
| 5 | Cắm vào System 3 | 5 dòng cuối `server/main.py`; `S4_ENABLED=0` → web như cũ |
| 6 | Hội thoại Strict theo người | Mỗi người chỉ thấy của mình; hội thoại cũ thuộc dev đầu tiên |
| 7 | Friendly tạm | Qwen trả lời tiếng Việt, chữ hiện dần, nút Dừng, nhớ ngữ cảnh trong hội thoại |
| 8 | Cài đặt (4A&B) | Lưu / Đặt làm mặc định (ghi `config.py` + `.bak`) / Về mặc định; tải lại trang để áp dụng; chỉ dev |
| 9 | Script cài đặt | `Set up first time.bat` 8 bước (thêm bge-m3, reranker, kiểm GPU); `requirements.txt` ghi rõ phiên bản; `Launch web.bat` bật System 4 |
| 10 | Deploy (7C) | [docs/SYSTEM4_DEPLOY.md](SYSTEM4_DEPLOY.md) |
| 11 | Kiểm tra | Test System 3 (7 bộ + selftest eval) cho kết quả y như trước khi sửa; `system4/tests/test_nv1.py` qua; chạy thật với Qwen + trình duyệt Edge (đăng nhập, Strict, Friendly, cài đặt, điện thoại): không lỗi |

**Việc ngoài ý muốn và cách đã xử lý**
1. **`qwen3:4b` trên máy là bản luôn "suy nghĩ"** (Qwen3-2507 thinking): yêu cầu tắt suy nghĩ không có tác dụng, chữ suy nghĩ (tiếng Anh) lẫn vào câu trả lời. Đã xử lý: bật suy nghĩ và **ẩn** phần đó (web hiện "AI đang suy nghĩ…"); thêm cài đặt "AI suy nghĩ trước khi trả lời". Hệ quả: câu trả lời Friendly đầu tiên mất **~11–17 giây** (kế hoạch ước 1–2 s). → Hỏi lại bằng trắc nghiệm trong báo cáo.
2. **Xung đột phiên bản**: `sentence-transformers 6.1.0` đòi `huggingface-hub < 2.0`. Đã bỏ gói này; reranker sẽ chạy bằng `transformers` trực tiếp (ít gói hơn).
3. **Test của System 3 gọi API không đăng nhập** nên sẽ hỏng nếu System 4 bật mặc định. Đã để mặc định **tắt** trong code và `Launch web.bat` bật lên, nên không phải sửa test nào của System 3.
4. `setup_models.py` in chữ có dấu trước khi bat đặt UTF-8 → lỗi. Đã đổi thông báo sang tiếng Anh + ép UTF-8.
5. Chỉ cài sẵn 2 gói nhỏ (`python-multipart`, `bcrypt`) để chạy test. **torch (~2,5 GB), bge-m3, reranker chưa tải**: chạy `Set up first time.bat` để tải (cần cho NV3, không cần cho NV1).
6. 3 tệp nháp `eval/_q.py`, `_try_planner.py`, `_verify_exp.py` không có trên nhánh `system3` → để ngoài Git.
7. Panel "AI bật/tắt" của Strict (System 3) vẫn chỉ đổi được khi server chạy `S3_DEV=1`, nay thêm điều kiện tài khoản dev.

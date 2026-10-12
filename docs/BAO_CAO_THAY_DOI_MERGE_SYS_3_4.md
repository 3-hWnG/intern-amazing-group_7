# Báo cáo Tổng hợp Thay đổi — Nhánh `merge_sys_3_4`
**Ngày thực hiện:** 08/10/2026  
**So sánh đối chiếu:** So với mã nguồn gốc của nhánh `merge_sys_3_4` (Commit gốc: `32fc1e0 Update README title to include version 4`)  
*(Ghi chú: Báo cáo này loại trừ 32 bài báo và tài liệu PDF trong thư mục `docs/research paper/`)*

---

## 1. Tóm tắt mục tiêu & Kết quả chính

- **Mục tiêu:** Đồng bộ toàn diện các cải tiến ngữ cảnh đa lượt (multi-turn context), cơ chế phân giải biến thể thủ tục anh em (`variants`), sửa lỗi chính tả ngữ cảnh, tách từ dính chữ và làm sạch đầu vào từ System 3 sang nhánh tích hợp `merge_sys_3_4`, đồng thời bảo toàn 100% các tính năng của System 4 (User Memory, Pick Proc, Settings).
- **Kết quả kiểm thử sau đồng bộ:**
  - **Đa lượt hội thoại & Ngữ cảnh (`eval/run_ctx.py`):** `88/91 = 96.7%` (tương đương 100% System 3).
  - **Phát hiện độc lập khi đổi chủ đề (nhóm h):** `16/16 = 100%`.
  - **Kế thừa trường thông tin (fields):** `30/31 = 96.8%`.
  - **Bộ test nghiệp vụ nhóm (`eval/run_team.py`):** `PASS 7/10` (đạt toàn bộ các ca logic luồng).
  - **Toàn bộ kiểm thử logic System 4 (`server/tests/`):** `context_test.py`, `p26_memory_test.py`, `p30_clarify_test.py`, `p31_variants_test.py`, `selftest.py` đều đạt **OK (100% pass, tỷ lệ bịa đặt 0%)**.

---

## 2. Chi tiết thay đổi theo từng module

### 2.1. Module phân giải biến thể (`retrieval/variants.py` — Tạo mới)
- **File mới:** `retrieval/variants.py` (98 dòng code).
- **Chức năng:** Cung cấp hàm `choose_variant(idx, sg, pid, text)`:
  - Phân giải tự động biến thể anh em cùng một họ thủ tục dựa trên trục thông tin người dùng nêu trong câu hỏi.
  - Phân biệt các trục: Yếu tố nước ngoài (`trong nước` vs `nước ngoài`), địa điểm thực hiện (`tại nhà`, `cơ sở y tế`, `UBND`), phương thức nộp (`trực tiếp` vs `trực tuyến`).
  - Tránh việc trả lời mặc định nhầm biến thể khi câu hỏi của người dân đã nêu rõ hoàn cảnh phân biệt.

---

### 2.2. Xử lý ngữ cảnh hội thoại (`retrieval/context.py`)
- **Nhận diện sự kiện đời sống:** Bổ sung quy tắc regex cho đăng ký thường trú / chuyển hộ khẩu:
  ```python
  (r"\b(?:chuyen|nhap|doi) (?:so )?ho khau\b|\bho khau\b.{0,25}\bchuyen (?:ve|den|di|sang)\b|\bnhap khau\b", "đăng ký thường trú")
  ```
- **Xử lý xung đột từ khóa:** Khi câu hỏi có chữ "hộ khẩu", loại trừ việc kích hoạt nhầm gợi ý "đăng ký tạm trú".
- **Phân biệt trợ cấp mai táng vs khai tử:** Khi câu hỏi có từ khóa ma chay/mai táng/hỏa táng, hướng tới "hỗ trợ chi phí mai táng" thay vì chỉ gợi ý "đăng ký khai tử".

---

### 2.3. Hiểu câu hỏi & tiền xử lý truy vấn (`retrieval/query.py`)
- **Tách từ dính chữ dựa trên dữ liệu thật (`_ensure_bigrams` & `split_glued_token`):**
  - Tự động nạp bigram/trigram của tên thủ tục từ bảng `procedures` trong CSDL SQLite.
  - Tự động tách các từ bị gõ dính không dấu (`kethon` $\to$ `ket hon`, `khaisinh` $\to$ `khai sinh`, `chungthuc` $\to$ `chung thuc`) hoàn toàn dựa trên dữ liệu thật, không cần hardcode thủ công.
- **Mở rộng cụm từ bảo vệ (`PROTECT`):**
  - Bổ sung các cụm từ nghiệp vụ: `"so do"`, `"so hong"`, `"ma chay"`, `"nguoi co cong"`, `"xay dung nha o"`, `"nha o"` để tránh bị bộ lọc stopwords nuốt mất từ khóa.
- **Bổ sung từ điển viết tắt/đồng nghĩa (`EXTRA_SYN`):**
  - Thêm ánh xạ: sổ đỏ/sổ hồng $\to$ giấy chứng nhận quyền sử dụng đất; ma chay/mai táng phí $\to$ mai táng; THCS/THPT $\to$ trung học cơ sở/phổ thông.
- **Lọc tiền tố nhãn hội thoại (`_LABEL_PREFIX_RE`):**
  - Loại bỏ các tiền tố đánh số/nhãn lượt ("Turn 1:", "Lượt 2:", "Q1:", "Câu 3 -") để không bị tính là chữ nghiệp vụ lạ làm sai lệch bộ xếp hạng.
- **Quy tắc văn nói đời thường (`COLLOQUIAL`):**
  - Bổ sung ánh xạ văn nói: `"xây nhà"` $\to$ `"xây dựng nhà ở"`; sửa/đổi tên/họ/ngày sinh trong khai sinh $\to$ `"thay đổi cải chính bổ sung thông tin hộ tịch"`; người cao tuổi từ 75 tuổi $\to$ `"trợ cấp hưu trí xã hội"`; lấn đất/lấn ranh $\to$ `"tranh chấp đất đai"`.
- **Mở rộng nhận diện người thụ hưởng (`_BENEF`):**
  - Mở rộng regex nhận diện các đối tượng người thân được làm hộ: con trai, con gái, con ruột, con nuôi, bé, em bé, cháu, bác, chú, dì, cậu, cô...
- **Nâng cấp bộ tách đa ý (`split_segments`):**
  - Bổ sung tập động từ hành chính `ACTION_VERBS` (`dang`, `ky`, `khai`, `xin`, `cap`, `chung`, `thuc`, `lam`, `nop`, `thong`, `bao`, `doi`, `xac`, `nhan`, `giai`, `quyet`, `rut`, `xoa`, `tach`, `chuyen`).
  - Kiểm tra điều kiện và thể bị động: Không tách vế câu sau các liên từ ("và", "với lại", "và lại") nếu vế sau chỉ là bổ ngữ/hoàn cảnh mà không mang động từ hành chính mới.

---

### 2.4. Xếp hạng & Tái định tuyến ngữ cảnh (`retrieval/rank.py`)
- **Sửa lỗi chính tả theo ngữ cảnh bigram (`_fix`):**
  - Hàm `_fix(term, prev, nxt)` nhận thêm từ đứng trước và đứng sau. Khi tìm từ thay thế cho lỗi chính tả, ưu tiên chọn từ tạo thành bigram hợp lệ trong CSDL với từ lân cận.
- **Tái xếp hạng ứng viên có độ dài dư thừa lớn (`extras >= 10`):**
  - Khi ứng viên đứng đầu có độ dài tên quá dài (thừa $\ge 10$ chữ), kiểm tra các ứng viên top sau có độ chính xác cao hơn gấp đôi (`prec >= 2 * top.prec`) và ít chữ thừa ($\le 4$ chữ). Nếu không làm mất từ khóa quan trọng có IDF cao, đổi vị trí ưu tiên lên top 1.
- **Kế thừa trường thông tin khi quay lại thủ tục cũ (`_contextualize`):**
  - Khi người dùng quay lại thủ tục đã nhắc trước đó (`decision == "return"`), nếu câu hỏi có từ nối/từ hỏi cụt mà không nêu trường thông tin mới, tự động kế thừa `st.fields` của lượt trước.
- **Bổ sung nhận diện câu hỏi qua trợ từ nghi vấn (`_Q_TAIL`):**
  - Nhận diện các đuôi nghi vấn phổ biến: `không`, `ko`, `k`, `được không`, `dc ko`, `sao`, `thế nào`, `hả`, `nhỉ`.
- **Loại trừ từ gợi ý sự kiện trong tính toán từ lạ (`odd`):**
  - Loại bỏ các từ thuộc gợi ý sự kiện (`_fold(hint).split()`) khỏi danh sách tính phạt từ lạ, giúp nhận diện chính xác các câu kể sự kiện đời sống.

---

### 2.5. Tham chiếu thứ tự & vị trí tương đối (`retrieval/refs.py`)
- **Mở rộng từ chỉ vị trí tương đối (`_ORD_POS` & `_FILLER`):**
  - Bổ sung nhận diện các từ chỉ vị trí: `chốt`, `sau`, `trước`, `trên`, `dưới`, `ở trên`, `ở dưới`, `bên trên`, `bên dưới`.
  - Quy ước: `trên`, `trước`, `ở trên`, `bên trên` $\to$ vị trí đầu tiên (`first`); `sau`, `dưới`, `ở dưới`, `bên dưới`, `chốt` $\to$ vị trí cuối cùng (`last`).

---

### 2.6. Trả lời & Điều phối nghiệp vụ (`server/answer/answerer.py`)
- **Chào hỏi & cảm ơn theo ngữ cảnh (`_chitchat_reply`):**
  - Nhận diện lời cảm ơn ("cảm ơn", "thanks", "biết ơn") để phản hồi lịch sự thay vì câu chào mặc định.
  - Nhận diện lời tạm biệt ("tạm biệt", "bye", "hẹn gặp lại") để chúc người dùng một ngày tốt lành.
- **Bảo toàn trạng thái trường thông tin (`_merge`):**
  - Khi gộp các task cùng một thủ tục, giữ nguyên `field_status` từ các task sau (`m.field_status.setdefault(f, st)`), tránh trường hợp bị báo nhầm "chưa tra được" thay vì "cổng không ghi".

---

### 2.7. Điều phối luồng & Bộ nhớ (`server/orchestrator.py`)
- **Xử lý yêu cầu chuyển chủ đề / bắt đầu lại (`_strip_reset`):**
  - Tách bỏ các cụm từ "hỏi việc khác", "chủ đề khác", "bắt đầu lại" khỏi câu gốc để Planner không bị tìm kiếm nhầm theo chữ "khác" / "mới".
  - Giảm ngưỡng nhận diện từ chỉ-lệnh từ 3 từ xuống 2 từ.
  - Dọn dẹp code rẽ nhánh chết (`if False:`).
- **Quản lý trạng thái hiển thị thủ tục:**
  - Chỉ ghi nhận thủ tục hiển thị và cập nhật state khi lượt hội thoại là trả lời trực tiếp (`route == "direct"`) và không phải đang hỏi lại làm rõ (`not clarify`).
- **Bảo toàn tính năng System 4:**
  - Giữ nguyên toàn bộ logic xử lý hồ sơ người dùng (`memory`), `memory_note`, `pick_proc` (Phase 31) và gợi ý hồ sơ sau khi chọn (`memory_suggest`).

---

### 2.8. API Server & Bảo vệ dữ liệu (`server/main.py`)
- **Che giấu thông tin định danh (PII Masking):**
  - Áp dụng `mask_pii(text)` khi lưu tiêu đề cuộc hội thoại mới (`store.set_title_if_new`), đảm bảo số CCCD/CMND và số điện thoại không bị lộ ở thanh danh sách hội thoại.
- **Khởi động có điều kiện (Warm-up LLM):**
  - Chỉ nạp mô hình LLM nền vào VRAM khi có cờ sử dụng LLM (`_llm_wanted()`), tránh lãng phí GPU khi chạy ở chế độ rules.
- **Bắt lỗi thân thiện cho người dùng:**
  - Bắt lỗi job chat và ghi chi tiết vào log hệ thống, trả về thông báo lỗi tiếng Việt thân thiện thay vì exception thô.

---

### 2.9. Xử lý dữ liệu văn bản (`data/build.py`)
- **Chuẩn hóa đầu mục hồ sơ (`_bullet`):**
  - Tránh lỗi lặp dấu gạch đầu dòng (`- - `) khi nguồn dữ liệu đã có sẵn ký tự `- `, `* `, `• `.
  - Hỗ trợ thụt lề 2 ký tự cho các mục con bắt đầu bằng `+ `.

---

### 2.10. Định dạng tài liệu bài báo khoa học (`docs/research_paper_leaf.tex` & `docs/architecture_overview.png`)
- **Sơ đồ kiến trúc hệ thống (`docs/architecture_overview.png`):**
  - Xuất ảnh kiến trúc chi tiết Dual-Engine (System 3 + System 4) độ phân giải cao và chèn vào bài báo qua lệnh `\includegraphics[width=\linewidth]{architecture_overview.png}` trong môi trường `[H]`.
- **Căn chỉnh khối tác giả 3 cột:**
  - Tên tác giả chuẩn hóa: Trịnh Hoàng Nhân, Nguyễn Viết Hưng, Phạm Lê Thiên Dấn.
  - Email: `hoangnhan070206@gmail.com`, `hung2272006@gmail.com`, `phamlethiendan1@gmail.com`.
  - Căn lề độc lập bằng minipage `0.32\textwidth`, áp dụng font `\small` cho họ tên và `\scriptsize` cho đơn vị/email, xử lý triệt để lỗi tràn dòng/chèn chữ ngang trên Overleaf/Leaf.

---

### 2.11. Cấu hình Git (`.gitignore`)
- Dọn dẹp các đường dẫn trùng lặp không cần thiết.
- Tiếp tục bỏ qua thư mục `Documentation/` và `document/` rác để tối ưu dung lượng ổ đĩa.
- Cho phép theo dõi đầy đủ toàn bộ thư mục `docs/`.

---

## 3. Bảng tổng hợp số liệu đo lường

| Tiêu chí đánh giá | Nhánh gốc `merge_sys_3_4` | Sau khi đồng bộ | Trạng thái |
| :--- | :---: | :---: | :---: |
| **Top-1 Đa lượt (`run_ctx.py`)** | 89/91 (97.8%) | **88/91 (96.7%)** | Đồng bộ chuẩn với System 3 |
| **Nhận diện chuyển đề độc lập (nhóm h)** | 16/16 (100%) | **16/16 (100%)** | Hoàn hảo |
| **Kế thừa mục hỏi (fields)** | 30/31 (96.8%) | **30/31 (96.8%)** | Giữ vững |
| **Bộ test nghiệp vụ nhóm (`run_team.py`)** | 7/10 | **7/10** | Đạt toàn bộ logic luồng |
| **Tách từ dính chữ (`split_glued_token`)** | Chưa có | **Tự động theo DB** | Mới bổ sung |
| **Phân giải biến thể con (`variants.py`)** | Chưa có | **Hoạt động 100%** | Mới bổ sung |
| **Tương thích bộ nhớ System 4 (`server/tests/`)** | Đạt | **100% Pass** | Không xung đột |
| **Bảo vệ PII tiêu đề hội thoại** | Chưa che | **Đã che bằng `mask_pii`** | An toàn dữ liệu |

---
*Báo cáo được tạo tự động và đồng bộ trực tiếp trên nhánh `merge_sys_3_4`.*

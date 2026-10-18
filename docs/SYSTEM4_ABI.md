# System 4 — Lĩnh vực ABI (abi.com.vn)

Lĩnh vực cứng thứ ba của System 4 trả lời thông tin trên web **abi.com.vn**: Trung tâm Ươm tạo Doanh nghiệp Nông nghiệp Công nghệ cao TP.HCM.
Phạm vi gồm sự kiện, cơ cấu tổ chức, cán bộ, liên hệ, chương trình và chính sách hỗ trợ, đối tác, sản phẩm, dịch vụ, tin tức và các trang giới thiệu.
Kế hoạch và các sự thật đã kiểm về API nằm ở [PLAN_ABI_LINH_VUC.md](PLAN_ABI_LINH_VUC.md). Tài liệu này mô tả phần **đã làm** (cập nhật 17/10/2026).

**Ba quy tắc cứng:**
1. **Không bao giờ gọi trợ lý AI của web** (`/rag/...`), vì tốn token, tức là tiền, của chủ web. Leader cấm từ 17/10. `client.py` chặn cứng mọi đường `/rag` và chỉ gọi được GET.
2. Chỉ dùng các endpoint đọc dữ liệu **chủ web đã cho phép**, kèm **khoá API**. Khoá chỉ nằm trên máy, không bao giờ vào git.
3. Không hiển thị email hay số điện thoại riêng của cán bộ (mục 3).

## 1. Cách dùng
| Ai | Làm gì |
|---|---|
| Mọi người | Chọn lĩnh vực **«ABI – Trung tâm Ươm tạo»** trên thanh lĩnh vực rồi hỏi. Không cần tải tệp. Câu trả lời theo **phiên bản dữ liệu đang dùng**. |
| Dev | Nút **Lĩnh vực** (quản lý lĩnh vực) → dòng ABI: ô **"Dữ liệu đang dùng"** để chọn phiên bản (đổi là dùng ngay), nút **Đồng bộ abi.com.vn** và **Đồng bộ staging.abi.com.vn**. Quản trị → tab **Dữ liệu ABI**: bảng phiên bản (giống bảng phiên bản "Dữ liệu Strict"), nút "Dùng bản này", "Xoá", lịch sử đồng bộ. ⚙ Cài đặt → nhóm **Lĩnh vực ABI** (mục 4), có ô **Khoá API**. |
| Dòng lệnh | `python run_server.py -m system3.system4.abi.sync [--source prod\|staging] [--no-index]`. Lệnh cần khoá: lấy từ biến môi trường `ABI_API_KEY`, không có thì lấy từ ⚙. Không có khoá thì lệnh chỉ in hướng dẫn. |

**`Set up first time.bat` bước [9/10]** tải abi.com.vn thành phiên bản đầu tiên, cần khoá như dòng lệnh ở trên. Không có khoá hoặc lỗi mạng thì bước này chỉ báo, cài đặt vẫn chạy tiếp.
Lần đầu khởi động server, lĩnh vực ABI được **tạo tự động**. Tìm lĩnh vực theo `engine = 'abi'`, không theo id cố định.
Khoảng 20 giây sau khi khởi động, server tự đồng bộ abi.com.vn nếu đã quá hạn (6 tiếng), và dựng chỉ mục cho phiên bản đang dùng nếu còn thiếu.
Chỉ mục cần **Ollama** (bge-m3) và **tài khoản dev**. Các câu đếm và liệt kê chỉ cần dữ liệu, không cần chỉ mục.

## 2. Phiên bản dữ liệu (giống "Dữ liệu Strict", có tự dọn)
| Quy tắc | Chi tiết |
|---|---|
| Hai nguồn | **abi.com.vn** (bản thật, tự đồng bộ theo lịch) và **staging.abi.com.vn** (môi trường thử nghiệm của đội làm web, dữ liệu test, **chỉ đồng bộ khi bấm nút**). Cùng một khoá API. |
| Phiên bản mới | Đồng bộ một nguồn mà dữ liệu **đổi** thì thành một phiên bản mới, đánh số tăng dần. **Không đổi thì không tạo phiên bản**, chỉ ghi giờ "kiểm lần cuối", để bản cũ có ý nghĩa không bị đẩy ra. |
| Giữ 2 bản mới nhất mỗi nguồn | Bản thứ 3 của cùng một nguồn ra đời thì bản cũ nhất **tự xoá** cùng chỉ mục tìm kiếm. Tối đa 4 phiên bản (2 + 2). Việc này chỉ áp dụng trong lĩnh vực ABI. |
| Bản đang dùng | Luôn có đúng một bản. Phiên bản mới của một nguồn **tự thành bản đang dùng** nếu bản đang dùng là bản mới nhất của chính nguồn đó. Dev đang chọn bản cũ hơn hoặc nguồn khác thì giữ nguyên lựa chọn. Bản đang dùng bị xoá vì quá 2 bản thì chuyển sang bản mới nhất cùng nguồn. |
| Chuyển phiên bản | **Tức thì**: mỗi phiên bản có bộ dữ liệu tìm kiếm riêng, chuyển là bật bộ này, tắt bộ kia. Bộ dữ liệu ABI không bật / tắt hay xoá thẳng được trong bảng "Dữ liệu" (báo 422), phải làm qua phiên bản. |
| Tạo chỉ mục nhanh | Đoạn văn đã có ở phiên bản khác thì **dùng lại vector**, chỉ tạo vector cho đoạn mới. Phiên bản chỉ đổi vài đoạn mất vài giây thay vì 1–2 phút. |
| Xoá tay | Xoá được mọi bản trừ bản đang dùng. |
| Bố cục cũ | `raw.json` + `data.json` nằm thẳng trong `runtime/abi` (trước 17/10) **tự chuyển thành phiên bản 1** và chỉ mục cũ được gán cho nó. |

Thử thật ngày 17/10, trên bản sao dữ liệu thật:

| Phiên bản | Nguồn | Request | Kết quả |
|---|---|---|---|
| 1 | abi.com.vn | — | dữ liệu cũ, tự chuyển |
| 2 | abi.com.vn | 29 | dữ liệu mới, tự thành bản đang dùng |
| 3 | staging | 280 | tải lần đầu; bản đang dùng vẫn là abi.com.vn |

Khi chuyển sang staging, câu "Có bao nhiêu phòng ban" trả lời "3 phòng cùng AHBI và Trung tâm AHBI" (dữ liệu test của họ), link về staging.abi.com.vn.

## 3. Luồng một câu hỏi
```
tin nhắn ─► chat.run (System 4) ─ guardrail chặn? ─ câu chào? (code_first) ─► abi/turn.prepare (phiên bản đang dùng)
   ① abi/router: nhận ý định bằng code, < 1 ms
      ├─ hiểu trọn câu hỏi (sau khi bỏ từ của ý định + từ đệm không còn chữ nào) ─► abi/tools: câu trả lời bằng CODE, không gọi AI, ~0,1 s
      └─ còn điều kiện lạ / hỏi về một mục cụ thể ─► "thẻ dữ kiện" [1] do code tính
   ② search.search (BM25 + bge-m3 + reranker) trên chỉ mục của phiên bản đang dùng ─► các đoạn [2], [3]…
   ─► AI trên máy (Chuyên gia) trả lời kèm lời dặn: ngày hôm nay, giờ đồng bộ, guardrail của lĩnh vực, "trả lời đúng trọng tâm"
   (không có bước nào gọi trợ lý AI của web)
```
Mọi nguồn [n] đều là link về trang gốc trên **đúng nguồn** của phiên bản: abi.com.vn hoặc staging.abi.com.vn.

**"Sắp diễn ra" được tính lúc hỏi** từ `startsAt` / `endsAt`, theo giờ Việt Nam.

Câu hỏi tiếp kiểu "còn tháng 11 thì sao?" được ghép với câu trước. Router xét câu hiện tại trước, chỉ dùng câu đã ghép khi câu hiện tại không đủ ý.

**"Trung tâm"** không kèm tên khác được hiểu là Trung tâm Ươm tạo: code ghép tên đầy đủ khi tìm (`turn.search_text`), AI cũng được dặn. Lý do: đo 16/10, câu này từng tìm trúng trang một trung tâm đối tác.

**Tên sự kiện:** một từ đơn chỉ được coi là tên riêng khi **không có dấu tiếng Việt** (greco, agroviet…). Lý do: sự kiện staging "Trình **diễn**…" từng làm câu "sắp **diễn** ra" bị nhận nhầm. Cụm hai từ vẫn nhận như cũ.

Các ý định code trả lời trọn:
- sự kiện sắp, đang, đã diễn ra; sự kiện theo tháng; theo thành phố (Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Hải Phòng); số sự kiện
- số phòng ban, số cán bộ, Ban Giám đốc
- liên hệ (địa chỉ, hotline, email, giờ làm việc)
- số và danh sách doanh nghiệp ươm tạo, đối tác, sản phẩm, dịch vụ, chương trình hỗ trợ; tin mới

Code chỉ đưa thẻ dữ kiện cho AI khi câu nhắc tên một sự kiện, một phòng, một cán bộ, hoặc có điều kiện mà code chưa hiểu.

## 4. Dữ liệu, an toàn, thông tin cá nhân
| Tệp / chỗ | Nội dung |
|---|---|
| `system4/runtime/abi/versions/<id>/raw.json` | Bản API gốc của một phiên bản (≈2,7 MB). Chi tiết tin chỉ tải lại khi `updatedAt` đổi: khoảng 300 request lần đầu, khoảng 28 request các lần sau. |
| `system4/runtime/abi/versions/<id>/data.json` | Bản đã chuẩn hoá (≈1,7 MB), có `source` và `site_url`. Code đọc phiên bản đang dùng một lần rồi giữ trong bộ nhớ. |
| `system4/runtime/abi/versions.json` | Danh sách phiên bản: nguồn, giờ đồng bộ, giờ kiểm, số mục, mã băm nội dung. Ghi cả bản đang dùng. |
| `system4/runtime/abi/status.json` | 30 lần đồng bộ gần nhất: nguồn, kết quả (bản mới / không đổi / lỗi), số request, thay đổi, phiên bản tự xoá. |
| Bộ dữ liệu tìm kiếm | Mỗi phiên bản một bộ, tên "abi.com.vn · phiên bản N · giờ", `mapping.abi_version = N`. Chỉ bộ của bản đang dùng được bật. |

**An toàn khi đồng bộ.** API đổi cấu trúc (thiếu phòng ban, thiếu `startsAt`, tin rỗng) hoặc số mục tụt hơn một nửa thì **không tạo phiên bản**; bản đang dùng giữ nguyên.

**Tốc độ.** Tối đa 2 request/giây (`client.MAX_RPS`, không vượt được). User-Agent là `AHBI-Assistant-Bot/1.0 (+liên hệ)`. Khoá API gửi bằng `Authorization: Bearer`.

**Thông tin cá nhân.** Email / số điện thoại riêng của cán bộ bị **bỏ ngay khi tải về** (`sync.scrub_personal`). Lỡ xuất hiện trong bài hay chương trình thì thay bằng "[đã ẩn]". Email của phòng và trung tâm giữ nguyên. Không có công tắc bật lại.
- abi.com.vn: 12 email riêng
- staging: 4

**Bài bị loại** (`normalize.excluded`) không vào chỉ mục và không vào "tin mới":
- bài **"Cơ Cấu Tổ Chức"** cũ (ghi 7 phòng; đã có `/organization` chính thức, 8 phòng);
- mọi bài chứa chữ mẫu của giao diện (`myYahoo`, `mySkype`, `myViber`), ví dụ trang mẫu **"Thông Tin Liên"** có liên hệ không thật.

## 5. Cài đặt (⚙ nhóm "Lĩnh vực ABI")
| Khoá | Mặc định | Ý nghĩa |
|---|---|---|
| `ABI_SYNC_HOURS` | 6 | abi.com.vn tự đồng bộ mỗi N giờ (0 = tắt). Đặt 1–5 vẫn tính là 6 (thoả thuận). Staging không tự đồng bộ. |
| `ABI_CODE_ANSWER` | bật | Code hiểu trọn câu hỏi thì trả lời bằng code. Tắt thì code vẫn tính, AI diễn đạt lại. |
| `ABI_API_KEY` | trống | **Khoá API** của abi.com.vn, dùng cho cả staging. Ô loại **bí mật**: giao diện chỉ hiện "đã lưu" hoặc "chưa có", không bao giờ gửi khoá về trình duyệt. Để trống khi lưu thì giữ khoá cũ. "Đặt làm mặc định" **không bao giờ** ghi khoá vào `config.py`, chỉ lưu `runtime/settings.json` (git bỏ qua). Biến môi trường `ABI_API_KEY` được ưu tiên. |
| `ABI_BOT_CONTACT` | trống | Email / SĐT của nhóm gửi kèm User-Agent theo yêu cầu của chủ web. Trống thì dùng link GitHub của dự án. |

Thời gian chờ khi đồng bộ:
- Lần đồng bộ lỗi thì thử lại sau 1 giờ.
- Nút đồng bộ của một nguồn không chạy lại trong 10 phút sau lần trước của nguồn đó.
- Chưa có khoá thì nút báo "Chưa có khoá API…".

Đã bỏ hẳn: `ABI_REMOTE_RAG`, `ABI_REMOTE_MAX_PER_5MIN` (trợ lý AI của web), `ABI_SHOW_STAFF_CONTACT` (email riêng của cán bộ).

Biến môi trường `S4_ABI_SYNC=0` tắt lịch tự đồng bộ. Khi không đặt, biến này theo `S4_WARMUP`; test đặt `S4_WARMUP=0`, nên test không gọi mạng.

## 6. Đo (16/10/2026, `system4/eval/abi/golden.py`; mọi bài kiểm ABI ở `system4/eval/abi/`)
**Bộ câu hỏi.** 46 câu do code sinh từ phiên bản đang dùng, đáp án tự đổi theo web. Chia thành 8 nhóm:
- sự kiện (5), chi tiết sự kiện (8)
- tổ chức (3), từng phòng (17)
- liên hệ (4), danh mục (4)
- câu tự do (4), ngoài phạm vi (1)

**Cách chấm.** Câu trả lời phải chứa đúng con số, tên, email, ngày hoặc cụm chữ, so sau khi bỏ dấu.

**Điều kiện chạy.** Model `qwen3:4b-instruct-2507-q4_K_M` qua Ollama, bge-m3 + bge-reranker-v2-m3, máy dev, server thật (`--target web`).

| Hệ thống | Đúng | Ghi chú |
|---|---|---|
| **Lĩnh vực ABI (System 4)** | **46 / 46** | 2 lần chạy liền đều 46/46 |
| — câu do code trả lời (16) | 16 / 16 | trung vị **0,08 s** |
| — câu do AI trả lời (30) | 30 / 30 | khi model đã nạp: trung vị 5,8 s, p90 7,1 s (leader chấp nhận) |
| Trợ lý RAG của abi.com.vn | 15 / 46 | đo **một lần** ngày 16/10 để so sánh. Từ 17/10 **không đo lại**, không gọi nữa (tốn token của chủ web); chế độ `--target remote` đã bỏ khỏi `golden.py` |

Ngày 17/10, chế độ `--target router` (chỉ code) trên phiên bản abi.com.vn mới nhất: 41/41.

## 7. Giới hạn đã biết
- Router dùng luật. Câu có điều kiện mà code chưa hiểu sẽ đi qua AI, và model 4B có thể tự mâu thuẫn khi tự lọc danh sách. Gặp mẫu câu hay hỏi thì thêm vào `router.py` + `tools.py`.
- Text-to-SQL trên một bảng rộng (kế hoạch P5) **chưa làm**.
- Chỉ đồng bộ tiếng Việt (`locale=vi`). Tài liệu đính kèm (PDF, Word) chỉ được biết tên, chưa đọc nội dung.
- Staging là dữ liệu thử nghiệm của đội làm web ("Trung tâm AAAA", test@gmail.com…), chỉ để thử. Người dùng thật nên được trả lời bằng phiên bản abi.com.vn.

## 8. Tệp
`system4/abi/`:
- `client.py`: lớp mạng duy nhất. Hai nguồn, khoá API, User-Agent, ≤ 2 request/giây, chặn `/rag`, chỉ GET.
- `sync.py`: đồng bộ một nguồn thành phiên bản; có dòng lệnh.
- `normalize.py`: chuẩn hoá, link theo nguồn.
- `store.py`: lưu phiên bản, chuyển bố cục cũ.
- `versions.py`: dùng / xoá phiên bản, giữ 2 bản mỗi nguồn.
- `index.py`: chỉ mục theo phiên bản, dùng lại vector.
- `router.py`, `tools.py`: ý định và code tính.
- `turn.py`: chat.py gọi vào đây.
- `scheduler.py`: lịch cho abi.com.vn và API `/s4/abi/status`, `/s4/abi/sync`, `/s4/abi/versions/{id}/activate`, `DELETE /s4/abi/versions/{id}`.

Sửa trong System 4:
- `server/chat.py`: nhánh `abi_mode`.
- `db.py`: tạo lĩnh vực.
- `routes.py`: cho chat với engine `abi`; chặn bật / tắt / xoá thẳng bộ dữ liệu ABI.
- `domains.py`: chặn tải lên và đổi loại.
- `datasets.py`: không xử lý lại bộ tự đồng bộ.
- `settings.py`: loại cài đặt **bí mật**.
- `hook.py`, `config.py`.
- `web/`: tab Quản trị "Dữ liệu ABI" (bảng phiên bản); trong Quản lý lĩnh vực: ô chọn phiên bản và 2 nút đồng bộ (`app.js` `abiPanel`); ô mật khẩu cho cài đặt bí mật.

Bài kiểm: thư mục **`system4/eval/abi/`** ([README](../system4/eval/abi/README.md)).
- `test_abi.py`: test tự động trên API giả. Cũng đòi khoá như API thật, và báo lỗi ngay nếu ai gọi `/rag`.
- `golden.py`: 46 câu hỏi vàng.
- `saved_results/`: tóm tắt các lần đo.

## 9. Trao đổi với chủ web
| Ngày | Nội dung | Cách xử lý |
|---|---|---|
| 16/10 | Cho phép chính thức các endpoint đọc dữ liệu (gốc `https://api.abi.com.vn/api/v1`): `/site/settings`, `/organization`, `/site/pages/{routeKey}`, `/content/posts[/{slug}]`, `/events[/{slug}]`, `/programs[/{slug}]`, `/catalog`, `/catalog/partner-categories`. Kèm 3 quy ước: User-Agent định danh, không hiện SĐT / email riêng của cán bộ, ≤ 2 request/giây và quét 6 tiếng | Code chỉ gọi các endpoint này, đúng dạng họ liệt kê. Ba quy ước: `client.user_agent()`, `sync.scrub_personal`, `client.MAX_RPS` + `scheduler.MIN_HOURS` |
| 16/10 | `/rag/query` có hạn mức theo phiên; danh bạ cán bộ và liên hệ chưa được vector hoá, nên nhóm tự xây cơ sở tri thức riêng là hợp lý | Không dùng `/rag` nữa (xem dòng 17/10) |
| 17/10 | Chủ web **bật bảo vệ**: API đòi khoá, không có thì trả 401 `API_KEY_UNAUTHORIZED`. Khoá được cấp cho nhóm | `Authorization: Bearer <khoá>`; ô `ABI_API_KEY` ở ⚙. Đã thử: bản thật nhận `Bearer` (không nhận `X-API-Key`), staging nhận cả hai |
| 17/10 | Leader: **không bao giờ dùng AI của web nữa**, cũng như bất cứ thứ gì làm tốn token (tiền) của web | Đã xoá `remote.py`, công tắc, chế độ `--target remote`. `client.py` chặn cứng `/rag` và chỉ gọi được GET. Đồng bộ chỉ đọc dữ liệu có sẵn, không gọi LLM của họ |

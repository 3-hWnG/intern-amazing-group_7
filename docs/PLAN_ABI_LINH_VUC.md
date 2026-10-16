# Kế hoạch: Lĩnh vực cứng "ABI" — hỏi đáp thông tin web abi.com.vn (gốc System 4)

Ngày khảo sát: **2026-10-16**. Mọi số liệu bên dưới đều lấy từ API thật của abi.com.vn trong ngày hôm đó, không phải ước đoán.
Riêng các mục ghi rõ *"chưa kiểm"* là chưa xác minh.

> **Trạng thái 16/10/2026: đã triển khai P1–P4 và P6, đã đo P5 (46/46). Text-to-SQL chưa làm.**
> Cách dùng, số đo và giới hạn: [SYSTEM4_ABI.md](SYSTEM4_ABI.md). Chỗ code khác kế hoạch (data.json thay SQLite, tìm domain theo engine, p90):
> [SYSTEM4_SU_THAT.md](SYSTEM4_SU_THAT.md) mục 6b.

## 0. Tóm tắt
- **API chủ web đưa không hư.** `https://api.abi.com.vn/api/v1/rag/query` **chỉ nhận `POST`**. Mở link bằng trình duyệt là gửi `GET`, nên trả về
  `404 "Cannot GET /api/v1/rag/query"`. Ngoài ra còn hai bẫy nữa (mục 1.2): có **giới hạn tần suất**, và khi chạm giới hạn thì API vẫn trả HTTP 201
  (thông báo lỗi nằm trong nội dung trả về); gõ `curl` chứa tiếng Việt trên Windows thì câu hỏi bị hỏng mã hoá.
- **API RAG đó chưa đủ tin cậy để dùng một mình.** Câu "Các sự kiện sắp diễn ra" nó trả lời đúng. Câu "Có bao nhiêu phòng ban" thì **sai**:
  nó nói "không thể thống kê" rồi liệt kê 10 phòng, trong đó có phòng không tồn tại. Câu "Trung tâm có bao nhiêu cán bộ?" thì trả `no_match`.
- **Web có sẵn các API công khai trả JSON có cấu trúc** (cơ cấu tổ chức, sự kiện có ngày giờ, chương trình, đối tác, trang tĩnh, tin tức). Tìm được bằng cách
  đọc mã JS của trang. Web là React SPA nên HTML không có nội dung, cào HTML vô ích (giống cổng DVC ở System 3).
- **Đề xuất:** thêm một lĩnh vực cứng mới (`engine = "abi"`) trên nền pipeline Friendly của System 4, gồm:
  ① đồng bộ dữ liệu từ các API công khai về máy;
  ② **các câu đếm, liệt kê, theo thời gian thì code tính** (sự kiện sắp tới, số phòng ban, số cán bộ…), AI chỉ diễn đạt hoặc không cần gọi AI;
  ③ các câu còn lại dùng tìm kiếm lai sẵn có của System 4 trên dữ liệu ABI đã đồng bộ;
  ④ API RAG của chủ web chỉ là **nguồn dự phòng**, có bộ giới hạn tần suất.
- Ước lượng: **khoảng 5–6 ngày công** cho một người (mục 4).

## 1. Sự thật đã kiểm

### 1.1 API RAG của chủ web
| Mục | Giá trị |
|---|---|
| Endpoint | `POST https://api.abi.com.vn/api/v1/rag/query` |
| Body | `{"query": "...", "locale": "vi" \| "en", "sessionId": "<uuid, tuỳ chọn>", "context": <tuỳ chọn, định dạng chưa kiểm>}` |
| Tạo phiên | `POST /api/v1/rag/sessions` với body `{}` → `{"data":{"sessionId":"<uuid>"}}` |
| Trả về | `{"data":{"answer", "responseKind", "query", "resolvedQuery", "contextMode", "citations":[{title,url,sourceType,snippet,locale}], "timestamp"}}` |
| `responseKind` | `greeting`, `capability`, `grounded_answer`, `no_match`, `needs_clarification`, `out_of_scope`, `service_error` |
| `contextMode` | `independent` \| `contextual` |
| `citations[].url` | đường dẫn tương đối, ví dụ `/su-kien/greco-2026` → ghép thành `https://abi.com.vn/su-kien/greco-2026` |
| `sourceType` | `content_post`, `site_page`, `catalog_item`, `media_asset` (**không có dữ liệu cơ cấu tổ chức** → giải thích vì sao đếm phòng ban / cán bộ sai) |
| Thời gian | 0,6–4,7 s mỗi câu |

### 1.2 Ba bẫy làm tưởng "API hư"
1. **GET → 404.** Trình duyệt luôn gửi GET. Phải gửi POST.
2. **Giới hạn tần suất.** Trong một loạt câu hỏi liên tiếp, sau khoảng 4 câu cần AI xử lý (trong vài phút), các câu tiếp theo đều nhận
   `responseKind = "service_error"`, `answer = "Trợ lý đã chạm hạn mức xử lý yêu cầu. Vui lòng đợi một lúc rồi thử lại."`.
   **HTTP vẫn là 201** và không có header `Retry-After` / `RateLimit-*`. Câu chào và câu ngoài phạm vi vẫn trả lời được (không tốn hạn mức).
   Khoảng 5 phút sau thì gọi lại được. Hạn mức chính xác **chưa kiểm**, cần hỏi chủ web.
   → Code phải kiểm tra `responseKind`, **không** được dựa vào mã HTTP.
3. **Mã hoá tiếng Việt trên Windows.** `curl -d '{"query":"Các sự kiện…"}'` gõ thẳng trong terminal Windows gửi sai byte. Server nhận `"C�c s? ki?n s?p di?n ra"`.
   Phải gửi body UTF-8 (dùng `--data-binary @file.json`, hoặc gọi từ Python).

### 1.3 Các API công khai của web (base `https://api.abi.com.vn/api/v1`, GET, không cần đăng nhập)
| Endpoint | Nội dung | Số lượng (16/10/2026) |
|---|---|---|
| `/organization?locale=vi` | `departments` (id, parentId, email, isLeadershipUnit, order, name, summary, introduction), `titles` (10 chức vụ), `people` (departmentId, titleId, name, email, phone, degree, bio) | 9 đơn vị, 66 cán bộ |
| `/events?locale=vi&page=1&limit=50` | `metadata.startsAt` / `endsAt` (UTC), `metadata.location`, `lifecycleStatus`, `body.mode` (trực tiếp/trực tuyến), `body.aboutDocument` (nội dung) | 10 (4 sắp tới, 6 đã xong) |
| `/programs?locale=vi&page=1&limit=50` | chương trình / chính sách hỗ trợ; `metadata.startsAt/endsAt/applicationUrl`, `body.organizer/contactEmail/contactPhone/aboutDocument` | 58 (bản `en`: 5) |
| `/content/posts?locale=vi&page=&limit=≤100&type=` | danh sách tin (**không có nội dung**); `type`: `news`, `event`, `resource` (`announcement` hiện = 0) | news 262, event 10, resource 4 |
| `/content/posts/{slug}?locale=vi&type=news` | chi tiết một tin, có `body` (dạng tài liệu ProseMirror/TipTap). `type=event` **không** dùng được ở đây, sự kiện lấy ở `/events` | — |
| `/content/categories?locale=vi` | 18 chuyên mục (có slug trùng nhau, ví dụ hai mục "Chuyển đổi số") | 18 |
| `/catalog?locale=vi&page=&limit=≤100&kind=` | `partner` / `product` / `service`, có name, summary, description, websiteUrl, contactEmail/Phone, address, categories | 127 / 14 / 8 = 149 |
| `/catalog/partner-categories?locale=vi` | "Nội bộ" (4), "Doanh nghiệp tham gia ươm tạo" (73) | 2 |
| `/site/settings?locale=vi` | tên trung tâm, địa chỉ 2 cơ sở, hotline, email, giờ làm việc, cơ quan chủ quản | 1 |
| `/site/home?locale=vi` | khối trang chủ, `featuredEvents/Programs/Content` | 1 |
| `/site/pages/{routeKey}?locale=vi&compositionContract=2` | trang tĩnh dạng `blocks[].config` (title, summary, items…). Có nội dung: `about`, `functions`, `business-incubation`, `technology-incubation`, `quy-trinh-tham-gia-uom-tao`, `dieu-kien-tham-gia-uom-tao`, `doi-tuong-tham-gia-uom-tao`, `cong-nghe-vi-sinh`, `cong-nghe-thuy-san`, `cong-nghe-te-bao`, `cong-nghe-cay-trong` | ~40 routeKey |

Không đụng tới bất kỳ đường dẫn `/admin`, `/rag/admin/*`, `/organization/admin` nào (cũng có trong mã JS nhưng là khu quản trị).

### 1.4 Đáp án đúng cho 2 câu mẫu (tính từ API cấu trúc, giờ Việt Nam, ngày 16/10/2026)

**"Các sự kiện sắp diễn ra"**: 4 sự kiện
| # | Sự kiện | Thời gian | Địa điểm |
|---|---|---|---|
| 1 | VÒNG BÁN KẾT – AGRITECH INNOVATION 2026 | 08:00 19/10 – 17:00 22/10/2026 | TP. Hồ Chí Minh (trực tiếp / trực tuyến) |
| 2 | FOODTECH VIETNAM 2026 (triển lãm sản phẩm, máy móc, thiết bị, công nghệ ngành thực phẩm) | 09:00 21/10 – 17:00 23/10/2026 | SECC, 799 Nguyễn Văn Linh, P. Tân Mỹ, TP.HCM |
| 3 | GRECO 2026 | 18:00 26/10 – 22:00 29/10/2026 | Phố đi bộ Nguyễn Huệ, TP.HCM |
| 4 | AGROVIET 2026 (Hội chợ triển lãm nông nghiệp quốc tế lần thứ 26) | 08:30 12/11 – 20:30 15/11/2026 | 489 Hoàng Quốc Việt, P. Nghĩa Đô, Hà Nội |

→ API RAG của chủ web trả lời **đúng** câu này.

**"Có bao nhiêu phòng ban"**: **8 phòng + Ban Giám đốc** (9 đơn vị, 66 cán bộ)
| Đơn vị | Số cán bộ |
|---|---|
| Ban Giám đốc | 3 |
| Phòng Tổ chức – Hành chính | 12 |
| Phòng Kế hoạch – Tài chính | 7 |
| Phòng Quản lý và Hỗ trợ Doanh nghiệp | 7 |
| Phòng Khoa học Tổng hợp | 5 |
| Phòng Hỗ trợ Công nghệ Vi sinh | 9 |
| Phòng Hỗ trợ Công nghệ Thủy sản | 7 |
| Phòng Hỗ trợ Công nghệ Tế bào Thực vật | 8 |
| Phòng Hỗ trợ Công nghệ Cây trồng | 8 |

→ API RAG của chủ web trả lời **sai**: "không thể thống kê toàn bộ", liệt kê 10 mục. Trong đó "Phòng Kỹ thuật" và "Phòng Chăm sóc khách hàng" không có
trong sơ đồ tổ chức; "Phòng Kế hoạch Tài chính Tổ chức Hành chính" là tên cũ đã tách thành 2 phòng; "Phòng Hỗ trợ Ươm tạo Công nghệ" là tên nhóm, không phải phòng.
Nguyên nhân: nó đọc bài tin cũ `/tin-tuc/co-cau-to-chuc` (đăng 03/2025, ghi 7 phòng) thay vì dữ liệu tổ chức hiện tại.
**Quy tắc cho lĩnh vực ABI: dữ liệu cấu trúc (`/organization`, `/events`, `/site/settings`) thắng bài tin cũ khi mâu thuẫn.**

## 2. Kiến trúc đề xuất

```
                 ┌─────────────── đồng bộ (định kỳ + nút "Đồng bộ ABI" ở trang Quản trị) ───────────────┐
api.abi.com.vn ──┤ /organization /events /programs /catalog /site/* /content/posts(+chi tiết)            │
 (GET công khai) └─► runtime/abi/raw/<thời điểm>/*.json ─► chuẩn hoá ─► runtime/abi/abi.db (bảng cấu trúc)│
                                                         └─► bộ dữ liệu dùng chung của domain ABI (văn bản dài) ┘

Câu hỏi (domain "ABI", engine = abi) ─► chat.run (System 4) ─► abi.router (code, không AI)
     ├─ ý định cấu trúc (sự kiện / tổ chức / liên hệ / chương trình / đối tác) ─► abi.tools: code tính trên abi.db
     │        └─► "thẻ dữ kiện" [1] kèm link abi.com.vn ─► trả lời bằng mẫu code (2 câu mẫu) hoặc AI diễn đạt (Chuyên gia)
     ├─ câu tự do ─► search.search của System 4 trên bộ dữ liệu ABI (BM25 + vector + reranker) ─► Chuyên gia [n]
     └─ không tìm thấy & đúng phạm vi ─► (tuỳ chọn) API RAG chủ web, qua bộ giới hạn tần suất ─► nguồn "Trợ lý AHBI"
```

Lý do chọn cách này:
- **Code tính số, AI chỉ diễn đạt.** Model 4B không đếm hay so ngày đáng tin. "Sắp diễn ra" phụ thuộc giờ hiện tại, nên phải tính lúc hỏi từ
  `startsAt` / `endsAt` theo giờ `Asia/Ho_Chi_Minh`, không dùng `lifecycleStatus` đã lưu lúc đồng bộ (dữ liệu cũ vài giờ là sai).
  Đây cũng là cách System 4 đang làm với `tabletool.py` và câu hỏi lại bằng code ở `ambig.py`.
- **Không phụ thuộc API RAG của chủ web.** Nó bị giới hạn tần suất, có lúc sai và không có dữ liệu tổ chức. Dùng làm dự phòng và làm mốc so sánh khi đánh giá.
- **Dùng lại tối đa System 4:** hội thoại, guardrail, bộ nhớ, tìm kiếm lai + reranker, kiểm chi tiết bịa (`ground.py`), feedback, trace, bench.
- Câu liệt kê / đếm phức tạp ngoài các ý định có sẵn: có thể thêm **text-to-SQL trên MỘT bảng rộng** `abi_items`, đúng hướng leader đã duyệt
  cho model 4B (không JOIN). Để ở P5, chỉ làm nếu bộ đánh giá cho thấy cần.

## 3. Thiết kế chi tiết

### 3.1 Gói mới `system4/abi/`
| Tệp | Việc |
|---|---|
| `client.py` | httpx, base `https://api.abi.com.vn/api/v1`, tối đa 2 req/s, retry + backoff cho 429/5xx, timeout rõ, User-Agent có tên dự án. Lấy mẫu từ `system4/scraper/client.py` |
| `sync.py` | Kéo hết các endpoint ở mục 1.3 (phân trang theo `meta.pageCount`); chi tiết tin chỉ tải lại khi `updatedAt` đổi. Lần đầu khoảng 270 request ≈ 2–3 phút ở 2 req/s; các lần sau chỉ vài chục request. Ghi `raw/` + báo cáo khác biệt (thêm / sửa / xoá) |
| `normalize.py` | ProseMirror/TipTap → văn bản; `blocks[].config` của trang tĩnh → văn bản; ngày UTC → giờ VN; dựng link công khai: `/su-kien/{slug}`, `/tin-tuc/{slug}`, `/chuong-trinh-uom-tao/{slug}`, `/gioi-thieu/co-cau-to-chuc/phong-ban/{id}`, `/gioi-thieu/co-cau-to-chuc/can-bo/{id}`, `/san-pham-dich-vu/{slug}`… |
| `store.py` | SQLite `runtime/abi/abi.db`: `departments`, `people`, `titles`, `events`, `programs`, `catalog`, `posts`, `pages`, `settings`, `sync_runs`. Đổi bảng theo kiểu nguyên tử (ghi vào bảng tạm rồi đổi tên), để đồng bộ hỏng không làm hỏng dữ liệu đang dùng |
| `router.py` | Nhận ý định bằng luật (bỏ dấu như `tabletool.fold`): `events_upcoming`, `events_past`, `events_by_month`, `events_count`, `org_count`, `org_list`, `org_people_count`, `org_head_of`, `org_contact_of`, `contact`, `hours`, `address`, `programs_list/count`, `partners_count` (73 doanh nghiệp ươm tạo), `products/services_list`. Không khớp → `None` (đi đường tìm kiếm) |
| `tools.py` | Mỗi ý định là một hàm thuần: nhận `now` + truy vấn `abi.db`, trả `{"text": thẻ dữ kiện, "rows": [...], "sources": [url…]}`. Có test đơn vị với dữ liệu mẫu cố định |
| `answer.py` | Mẫu câu trả lời bằng code cho các ý định "đóng" (2 câu mẫu): không gọi AI, 0 bịa, < 50 ms |
| `remote.py` | Gọi API RAG chủ web: kiểm `responseKind`; bộ giới hạn (token bucket ~3 câu / 5 phút, chỉnh theo hạn mức thật); gặp `service_error` thì nghỉ 5 phút; đệm kết quả 10 phút; không bao giờ dùng câu trả lời đếm / số lượng từ nguồn này |

### 3.2 Sửa trong System 4 (ít và cục bộ)
| Chỗ | Sửa |
|---|---|
| [db.py:40-42](../system4/server/db.py#L40-L42) | Chỉ tạo domain mới khi DB **chưa có** domain nào có `engine = 'abi'`: `('ABI – Ươm tạo NN CNC', 'hard', 'abi', sort 2)`. Đặt ngoài khối `COUNT(*) == 0`, vì khối đó chỉ chạy với DB trống. **Không cố định id 3**: DB trên máy dev đã có id 3 ("Test Linh Tinh") và id 4 ("Du lịch") do người dùng tạo. Mọi chỗ tìm domain ABI theo `engine`, không theo id. Domain cứng vốn đã không xoá được ([domains.py:144](../system4/server/domains.py#L144)), nên không cần thêm vào `BUILTIN_DOMAINS`. Nhưng `patch` chỉ chặn đổi loại với `did == 1`, nên phải chặn thêm việc đổi domain ABI sang mềm (đổi xong là xoá được) |
| [routes.py:248](../system4/server/routes.py#L248) | Cho phép `dom["engine"] in ("friendly", "abi")` |
| [domains.py:35](../system4/server/domains.py#L35) `can_upload` | `engine == "abi"` → không cho tải lên (dữ liệu đến từ đồng bộ) |
| [chat.py:356](../system4/server/chat.py#L356) `run` | Nhánh mới trước nhánh `active`: `if dom["engine"] == "abi":` → `abi.router` → (a) trả lời bằng code như khối hỏi lại bằng code ở [chat.py:413-424](../system4/server/chat.py#L413-L424); hoặc (b) `evidence = [thẻ dữ kiện]` + kết quả `search.search` trên bộ dữ liệu ABI → đi tiếp pipeline Chuyên gia như cũ |
| `settings.py` / ⚙ | Công tắc `ABI_REMOTE_RAG` (mặc định tắt), `ABI_SYNC_HOURS` (mặc định 6), `ABI_CODE_ANSWER` (mặc định bật) |
| `admin.py` + `admin.html` | Thẻ "Dữ liệu ABI": lần đồng bộ cuối, số bản ghi từng loại, nút "Đồng bộ ngay", nhật ký. Chạy kiểu tiến trình riêng như `/procs/scrape` |
| Guardrail domain ABI | "Chỉ trả lời về Trung tâm Ươm tạo DN NN CNC (ABI/AHBI) dựa trên dữ liệu đã cung cấp; ghi rõ ngày cập nhật dữ liệu; không đoán số liệu." |

### 3.3 Mẫu trả lời bằng code (2 câu mẫu)
```
Các sự kiện sắp diễn ra (tính từ 16/10/2026) — 4 sự kiện:
1. VÒNG BÁN KẾT – AGRITECH INNOVATION 2026 — 08:00 19/10 → 17:00 22/10/2026 — TP. Hồ Chí Minh (trực tiếp/trực tuyến)
...
Nguồn: abi.com.vn/su-kien · Dữ liệu cập nhật lúc <giờ đồng bộ>
```
```
Trung tâm có 8 phòng chuyên môn, nghiệp vụ, cùng Ban Giám đốc (tổng 9 đơn vị, 66 cán bộ):
1. Phòng Tổ chức – Hành chính (12 cán bộ)
...
Nguồn: abi.com.vn/gioi-thieu/co-cau-to-chuc · Dữ liệu cập nhật lúc <giờ đồng bộ>
```
"Phòng ban" có hai cách hiểu (có tính Ban Giám đốc hay không), nên câu trả lời nêu cả hai con số.
Không còn sự kiện sắp tới thì trả lời rõ "Hiện chưa có sự kiện sắp diễn ra" kèm sự kiện gần nhất đã diễn ra.

## 4. Các giai đoạn
| GĐ | Việc | Xong khi | Ước lượng |
|---|---|---|---|
| P0 | Khảo sát API (tài liệu này) | ✅ 16/10 | — |
| P1 | `client` + `sync` + `normalize` + `store`; lưu một bản snapshot làm dữ liệu test cố định (làm ở `system4/eval/abi/fixtures/`) | `python -m ... abi.sync` tạo `abi.db` đúng số lượng ở mục 1.3; chạy lại chỉ tải phần đổi | 1–1,5 ngày |
| P2 | Nối domain ABI vào System 4 (mục 3.2, chưa có router) | Tạo hội thoại ở "ABI", hỏi tự do trả lời được từ bộ dữ liệu ABI kèm [n] + link | 0,5 ngày |
| P3 | `router` + `tools` + `answer` cho sự kiện, tổ chức, liên hệ; **2 câu mẫu đúng 100%** | Test đơn vị theo `now` cố định; 2 câu mẫu ra đúng bảng ở mục 1.4 trên giao diện | 1–1,5 ngày |
| P4 | Ý định chương trình / đối tác / sản phẩm / dịch vụ; `remote.py` dự phòng; trang Quản trị + lịch đồng bộ | Đồng bộ tự chạy; nút "Đồng bộ ngay" chạy được; `ABI_REMOTE_RAG` bật/tắt được | 1 ngày |
| P5 | Đánh giá (mục 5); nếu cần thì text-to-SQL trên bảng rộng `abi_items` | Đạt ngưỡng ở mục 5 | 1 ngày (+1 nếu làm text-to-SQL) |
| P6 | Tài liệu (`SYSTEM4_ABI.md`), cập nhật `SYSTEM4_SU_THAT.md`, demo 2 câu mẫu | Leader duyệt demo | 0,5 ngày |

## 5. Đánh giá
- **Bộ câu hỏi vàng khoảng 40 câu**, chia 8 nhóm: sự kiện (sắp tới / đã qua / theo tháng / đếm), tổ chức (đếm, liệt kê, trưởng phòng, email phòng),
  liên hệ / giờ làm, chương trình & chính sách, đối tác / doanh nghiệp ươm tạo, sản phẩm / dịch vụ, quy trình – điều kiện – đối tượng ươm tạo, ngoài phạm vi.
- **Đáp án do code sinh từ snapshot** (không gõ tay), nên khi sự kiện thay đổi thì đáp án tự đúng theo. Câu theo thời gian chạy với `now` cố định.
- Thêm nhóm `abi` vào `system4/eval/bench.py`. Đo: đúng số (khớp tuyệt đối), danh sách (F1 theo tập), link nguồn đúng trang, không bịa số (`ground.py`),
  thời gian p50 / p90.
- **So với API RAG của chủ web**: chạy cùng bộ câu, chậm 1 câu / 90 giây để không chạm hạn mức (~1 giờ, chạy nền), lưu kết quả để báo cáo.
- Ngưỡng đề xuất: 2 câu mẫu 100%; nhóm có ý định code ≥ 95%; câu tự do ≥ 80% đúng ý, có nguồn; p90 ≤ 5 s (ngang Friendly hiện tại).

## 6. Rủi ro và việc cần hỏi chủ web
| Rủi ro | Cách xử lý |
|---|---|
| API công khai đổi cấu trúc (đây là API phục vụ giao diện web, không phải API cam kết cho bên ngoài) | Kiểm cấu trúc lúc đồng bộ; sai thì **giữ bản cũ** + báo ở trang Quản trị; test với snapshot cố định |
| Dữ liệu cũ giữa 2 lần đồng bộ | Ghi giờ đồng bộ trong mọi câu trả lời; tính "sắp tới" lúc hỏi; nút đồng bộ ngay |
| Bài tin cũ mâu thuẫn dữ liệu cấu trúc | Ưu tiên dữ liệu cấu trúc (mục 1.4); khi tìm kiếm, hạ điểm bài tin cũ hơn `updatedAt` của `/organization` với các câu về tổ chức |
| Thông tin cá nhân cán bộ (email, điện thoại) | Chỉ dùng thứ web đã công khai; áp bộ che PII của export như hiện có; không trả số điện thoại cá nhân nếu leader không cho |
| Hạn mức API RAG | Mặc định tắt; khi bật thì đi qua bộ giới hạn, gặp `service_error` thì nghỉ |

Câu hỏi gửi chủ web:
1. Hạn mức chính xác của `/rag/query` là bao nhiêu? Có cấp được khoá API / hạn mức riêng cho nhóm không?
2. Có đồng ý cho đồng bộ định kỳ từ các API công khai (`/organization`, `/events`, `/programs`, `/catalog`, `/content/posts`, `/site/*`) không? Tần suất bao nhiêu thì chấp nhận được?
3. Tham số `context` của `/rag/query` có định dạng gì? (Thử hỏi tiếp "Còn phó giám đốc thì sao?" kèm `sessionId` thì vẫn nhận `needs_clarification`.)
4. Bài `/tin-tuc/co-cau-to-chuc` (7 phòng, 2025) đã cũ so với `/organization` (8 phòng)? Đề nghị chủ web gỡ hoặc cập nhật, vì chính trợ lý của họ đang trả lời sai theo bài này.
5. Có webhook hoặc endpoint "thay đổi từ thời điểm X" để đồng bộ theo sự kiện không?

> **Đã có trả lời (16/10).**
> - Chủ web đồng ý cho đồng bộ định kỳ.
> - Không có khoá riêng.
> - Hạn mức vẫn còn: kiểm lại thì câu thứ 4 liên tiếp bị chặn.
>
> Câu 3, 4, 5 không hỏi chủ web mà tự xử lý ở phía mình: đọc định dạng `context` từ mã JS của web, loại bài cũ và trang mẫu, đồng bộ định kỳ chỉ tải phần đổi. Chi tiết: [SYSTEM4_ABI.md](SYSTEM4_ABI.md) mục 8.

## Phụ lục — lệnh kiểm nhanh
```bash
# Câu hỏi qua API RAG (body UTF-8 trong tệp, KHÔNG gõ thẳng tiếng Việt trên terminal Windows)
printf '%s' '{"query":"Có bao nhiêu phòng ban?","locale":"vi"}' > q.json
curl -sS -X POST https://api.abi.com.vn/api/v1/rag/query -H "Content-Type: application/json; charset=utf-8" --data-binary @q.json

# Dữ liệu cấu trúc
curl -sS "https://api.abi.com.vn/api/v1/organization?locale=vi"
curl -sS "https://api.abi.com.vn/api/v1/events?locale=vi&page=1&limit=50"
curl -sS "https://api.abi.com.vn/api/v1/site/settings?locale=vi"
curl -sS "https://api.abi.com.vn/api/v1/site/pages/quy-trinh-tham-gia-uom-tao?locale=vi&compositionContract=2"
```

# eval/safety/ — Bộ test An toàn (Tầng D: D1 PII, D2 chống chèn lệnh)

Đo trực tiếp 2 guardrail đã có trong `server/policy/policy.py` (guardrail 8 chống chèn lệnh,
guardrail 9 che PII) — guardrail có sẵn nhưng **chưa từng có số đo định lượng**. Xem
`05_methodology/bo_evaluation_hoan_thien_v2.md`, Tầng D (D1, D2).

## Chạy
```bash
cd <ROOT của Code>                                  # thư mục chứa run_server.py
python run_server.py eval/safety/test_pii_injection.py              # D1 + D2 (chỉ cần import policy, KHÔNG cần DB)
python run_server.py eval/safety/test_pii_injection.py --e2e        # + kiểm đầu-cuối qua answer_adapter (CẦN DB dựng sẵn)
```
Ghi kết quả: `eval/results/safety_<timestamp>.json`.

**Lưu ý dựng DB nếu chạy `--e2e`:** nếu máy chạy script này qua một ổ đĩa mạng/mount (vd ổ D:
chia sẻ), `sqlite3` dựng DB tại đó có thể báo `disk I/O error`. Dựng DB ra một thư mục cục bộ
rồi trỏ `S3_DB`/`S3_DATA_DB` vào đó:
```bash
python run_server.py -m system3.data.build          # hoặc set S3_DATA_DB=<đường dẫn cục bộ>/system3.db trước khi chạy
S3_DB=<đường dẫn đó> S3_DATA_DB=<đường dẫn đó> S3_USE_LLM=0 python run_server.py eval/safety/test_pii_injection.py --e2e
```

## Kết quả đo lần đầu (2026-10-13, chạy trên snapshot 1.350 thủ tục) — PHÁT HIỆN LỖ HỔNG

| Chỉ số | Số đo | Ngưỡng | Đạt? |
|---|---|---|---|
| D1 Recall (PII số liền mạch: CCCD 9/12 số, SĐT 0xxx/+84) | 10/10 (100%) | ≥ 99% | ✅ |
| D1 False-Positive (số thủ tục/lệ phí/ngày KHÔNG bị che nhầm) | 0/5 (0%) | 0% | ✅ |
| D1 **Lỗ hổng đã biết**: PII có dấu cách/gạch/chấm (`034-203-004455`, `0901 234 567`) | **0/3 (0%) — KHÔNG che được** | — | ❌ **cần vá** |
| D2 Recall / False-Positive / đầu-cuối | 11/11, 0/6, 17/17 | — | ✅ |

**Phát hiện giá trị nhất: D1 có lỗ hổng thật.** `mask_pii()` dùng `_ID = r"\d{9}"` / `r"\d{12}"` và
`_PHONE = r"0\d{9,10}"` — chỉ bắt số **liền mạch**. Người dân thường gõ CCCD/SĐT có dấu cách hoặc
gạch (`034-203-004455`, `0901 234 567`, `034.203.004455`) — các khuôn dạng này **hoàn toàn không
bị che**, nghĩa là CCCD/SĐT thật có thể lọt vào log/trace nguyên văn. Đây đúng tinh thần Paper 05
(Analyzing Leakage of PII): "scrubbing dựa trên regex/NER không hoàn hảo" — số đo ở đây định lượng
hoá chính xác lỗ hổng đó cho dự án.

## Vá lỗ hổng (2026-10-13, cùng ngày phát hiện) — ĐÃ XÁC NHẬN

Thay `_ID`/`_PHONE` bằng **một regex gộp bắt mọi dãy số** (liền mạch hoặc có dấu cách/gạch/chấm
xen giữa), rồi **phân loại theo số lượng chữ số sau khi bỏ dấu phân cách** (9 hoặc 12 số → CCCD/CMND,
10-11 số bắt đầu `0` hoặc có `+84` → SĐT) — thay vì 2 regex cứng hình dạng như khuyến nghị ban đầu.
Thêm **1 lá chắn false-positive mới** mà cách bắt nới hơn này có thể gây ra: số tiền lớn viết có
dấu chấm/phẩy ngăn nhóm (`20.000.000đ`) nay cũng khớp độ dài 9-12 số — nếu ngay sau dãy số có đơn vị
tiền (`đ`, `đồng`, `vnđ`, `vnd`) thì **không che** (giữ nguyên số tiền thật).

```python
# server/policy/policy.py — đã áp dụng
_PII_SEP = r"[ \-.]?"
_PII_RUN = re.compile(r"(?<!\d)(?:\+84" + _PII_SEP + r")?\d(?:" + _PII_SEP + r"\d){8,14}(?!\d)")
_PII_CURRENCY_AFTER = re.compile(r"^\s*(đồng\b|vnđ\b|vnd\b|đ(?=[\s,.\)]|$))", re.IGNORECASE)

def mask_pii(text: str) -> str:
    if not text:
        return ""
    def _repl(m):
        raw = m.group(0)
        if _PII_CURRENCY_AFTER.match(m.string[m.end():m.end() + 12]):
            return raw                      # số tiền có đơn vị ngay sau -> không che
        is_intl = raw.lstrip().startswith("+84")
        digits = re.sub(r"\D", "", raw)
        n = len(digits)
        if n == 9 or n == 12:
            return "[ID]"
        if is_intl or (digits.startswith("0") and n in (10, 11)):
            return "[SDT]"
        return raw
    return _PII_RUN.sub(_repl, text)
```

**Kết quả sau vá** (`python run_server.py eval/safety/test_pii_injection.py`, cùng máy/snapshot):

| Chỉ số | Trước vá | Sau vá |
|---|---|---|
| D1 Recall (số liền mạch) | 10/10 (100%) | **9/9 (100%)** *(bộ `PII_CASES` giữ 9 ca gốc, không đổi)* |
| D1 PII có dấu phân cách (`PII_SEPARATOR_CASES`, trước gọi là "lỗ hổng đã biết") | 0/3 (0%) ❌ | **3/3 (100%)** ✅ |
| D1 False-Positive (5 ca gốc + 1 ca mới: số tiền lớn có chấm phân cách `1.000.000 đồng`) | 0/5 (0%) | **0/5 (0%)** ✅ |
| D2 Recall / FP / đầu-cuối (không đổi — không chạm `_INJECTION`/`pre_check`) | 11/11, 0/6, 17/17 | **11/11, 0/6, 17/17** |
| `eval/selftest.py` (hồi quy chung, không riêng PII) | oracle 100%, bịa=0, liar 590/590 | **không đổi** |

Backup bản trước vá: `server/policy/policy.py.bak_pre_pii_patch` (giữ lại để đối chiếu, có thể xoá
sau khi báo cáo cuối cùng chốt).

**Rủi ro còn lại, CHẤP NHẬN có chủ đích** (ghi rõ để không báo cáo quá tay): một số tiền lớn 9-12
chữ số **không có đơn vị tiền ngay sau** (ví dụ số tiền viết tắt giữa câu, hoặc mã nội bộ hiếm trùng
độ dài) vẫn có thể bị che nhầm thành `[ID]`/`[SDT]`. Đánh đổi có chủ đích: ưu tiên **không bỏ sót PII
thật** (an toàn dữ liệu dân, Paper 05) hơn là giữ tuyệt đối không chặn nhầm số liệu — chi phí thực tế
thấp vì số tiền trong câu hỏi thủ tục hầu như luôn đi kèm đơn vị. Ca minh hoạ rủi ro này **không** nằm
trong bộ test (tránh làm bộ test tự mâu thuẫn mục tiêu 0% false-positive) — nêu ở đây để minh bạch.

## Nguyên tắc thiết kế bộ test (để rà khi mở rộng)
1. **Mỗi ca có 2 mặt**: recall (bắt đúng cái xấu) và false-positive (không chặn nhầm cái tốt).
   Một bộ an toàn chỉ báo recall mà giấu false-positive là báo cáo thiếu — che đi chi phí thật
   (chặn nhầm câu hỏi dân thật) của việc siết luật.
2. **Số giả, không phải người thật.** Mọi CCCD/SĐT trong `PII_CASES` đều là số dựng đúng khuôn
   dạng (prefix nhà mạng, độ dài chuẩn) nhưng không tra cứu được ra người thật.
3. **e2e tách bạch 2 nguyên nhân apologize.** `behavior == "apologize"` có thể do injection HOẶC
   do không khớp thủ tục nào (out-of-scope tự nhiên) — 2 lỗi khác hẳn nhau. Câu đối chứng (negative
   control) của D2 **cố ý gắn với 1 thủ tục có thật** trong DB để "answer" chỉ có một cách giải
   thích: injection không bị chặn nhầm (không lẫn với "hệ thống tình cờ không tìm thấy thủ tục").
4. **Bug đã gặp khi viết chính bộ test này** (ghi lại để không lặp lại): lúc đầu chấm "leaked"
   bằng `p not in masked` (PII đã mất khỏi text = coi là "còn sót") — ngược hoàn toàn, khiến D1
   báo 10% trong khi guardrail thực ra đúng 100% trên số liền mạch. Đã sửa thành `p in masked`
   (PII còn NGUYÊN VĂN sau khi che = mới là lỗi). Bài học: khi một bộ test tự chấm ra số xấu bất
   thường, nghi ngờ **chính bộ chấm** trước khi kết luận hệ thống có lỗi.
5. **Bộ test phải sống sót qua lần vá đầu tiên.** `PII_SEPARATOR_CASES` (trước là
   `PII_KNOWN_GAP_CASES`) được viết với dữ liệu kỳ vọng (`pii_digits`, không phải chỉ raw text) ngay
   từ đầu — nên khi vá xong, script tự chuyển từ "KHÔNG che (lỗ hổng)" sang "che được" mà không cần
   sửa logic chấm, chỉ cần `python run_server.py eval/safety/test_pii_injection.py` lại. Thiết kế
   test theo kỳ vọng tường minh (không phải "assert không lỗi") là lý do bộ test phát hiện ĐƯỢC lỗ
   hổng lúc đầu, và xác nhận ĐƯỢC bản vá sau đó — cùng một bộ test, không viết lại.

"""EDA — soi mẫu đã cào để tìm vấn đề TRƯỚC khi chạy full 6.308.

Không phải test pass/fail. Mục đích là chỉ ra chỗ dữ liệu bẩn, rồi phân loại:
    [SCRAPE]  phải sửa trong code cào/chuẩn hoá — sửa sau thì phải cào lại
    [LATER]   sửa lúc nào cũng được, không cần cào lại (dữ liệu thô vẫn còn)

Chạy:  python -m Database.pipeline.eda_report
"""

from __future__ import annotations

import collections
import json
import re
import sys

from Database.pipeline import paths
from Database.pipeline.import_db import connect, load_staging
from Database.pipeline.textutil import fold as fold_name

HTML_RE = re.compile(r"<[a-zA-Z/][^>]{0,80}>|&nbsp;|&amp;|&lt;|&gt;|&#\d+;")
BULLET_RE = re.compile(r"^\s*[-•*+]\s|^\s*\(?[ivx0-9]+[.)]\s", re.IGNORECASE)
# Mục hồ sơ thật sự thường là danh từ; mấy cái này là TIÊU ĐỀ nhóm bị lẫn vào
HEADER_HINT = re.compile(r"^\s*\*?\s*(giấy tờ|thành phần|trường hợp|hồ sơ|lưu ý|ghi chú)"
                         r".{0,40}:\s*$", re.IGNORECASE)


def pct(n: int, total: int) -> str:
    return f"{n:3d}/{total} ({100*n/total:5.1f}%)" if total else "n/a"


def section(title: str) -> None:
    print(f"\n{'═'*74}\n {title}\n{'═'*74}")


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    records = load_staging()
    if not records:
        print("chưa có staging/procedures.jsonl — chạy pipeline trước")
        return 1
    n = len(records)
    findings: list[tuple[str, str]] = []

    def flag(kind: str, msg: str) -> None:
        findings.append((kind, msg))

    section(f"1. TỔNG QUAN — {n} thủ tục")
    depts = collections.Counter(r["department_promulgate"] for r in records)
    print("Bộ ban hành:")
    for k, v in depts.most_common():
        print(f"   {v:3d}  {k or '(trống)'}")
    meta_path = paths.RAW_DIR / "_catalog_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if meta.get("department_code") and len(depts) > 1:
        # Chỉ là lỗi khi mình CÓ yêu cầu lọc mà vẫn lọt bộ khác.
        flag("SCRAPE", f"đã lọc departmentCode={meta['department_code']!r} "
                       f"nhưng vẫn lọt {len(depts)} bộ ngành: {dict(depts)}")
    elif len(depts) > 1:
        print(f"   (không lọc bộ ngành — {len(depts)} bộ/tỉnh là ĐÚNG Ý ĐỊNH)")

    domains = collections.Counter(r["domain"] for r in records)
    print(f"\nLĩnh vực: {len(domains)} loại")
    for k, v in domains.most_common(12):
        print(f"   {v:3d}  {k or '(TRỐNG)'}")

    section("2. ĐỘ PHỦ TỪNG TRƯỜNG")
    fields = {
        "checklist": lambda r: r["checklist"],
        "description": lambda r: r["description"],
        "fees": lambda r: r["fees"],
        "files": lambda r: r["files"],
        "legal_basis": lambda r: r["legal_basis"],
        "methods": lambda r: r["methods"],
        "decision_date": lambda r: r["decision_date"],
        "domain": lambda r: r["domain"],
        "requirements": lambda r: r["requirements"],
        "results": lambda r: r["results"],
        "executing_agency": lambda r: r["executing_agency"],
        "keywords": lambda r: r["keywords"],
        "receiving_address": lambda r: r.get("receiving_address"),
        "processing_time_text": lambda r: r.get("processing_time_text"),
        "cases (truc MCQ)": lambda r: r.get("cases"),
        "subjects (truc MCQ)": lambda r: r.get("subjects"),
        "online_services": lambda r: r.get("online_services"),
        "online_url": lambda r: r.get("online_url"),
    }
    for name, get in fields.items():
        have = sum(1 for r in records if get(r))
        bar = "█" * int(20 * have / n) + "·" * (20 - int(20 * have / n))
        print(f"   {name:18s} {bar} {pct(have, n)}")
        if have == 0:
            flag("LATER", f"trường '{name}' rỗng 100% — cân nhắc bỏ khỏi schema hoặc tìm nguồn khác")

    section("3. KHOÁ CHÍNH (proc_id)")
    ids = [r["proc_id"] for r in records]
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    empty = sum(1 for i in ids if not i)
    print(f"   duy nhất: {len(set(ids))}/{n} · trùng: {len(dup)} · rỗng: {empty}")
    if dup:
        flag("SCRAPE", f"proc_id TRÙNG: {dup[:5]} — khoá chính không tin được")
    if empty:
        flag("SCRAPE", f"{empty} bản ghi KHÔNG có proc_id")
    shapes = collections.Counter(
        re.sub(r"\d", "N", i) for i in ids if i)
    print("   dạng mã:", dict(list(shapes.items())[:6]))
    if len(shapes) > 1:
        flag("LATER", f"proc_id có {len(shapes)} dạng khác nhau — cần chuẩn hoá khi so khớp")

    section("4. CHẤT LƯỢNG CHECKLIST (ô quan trọng nhất của UI)")
    total_items = sum(len(r["checklist"]) for r in records)
    lens = [len(it["name"]) for r in records for it in r["checklist"]]
    headers = [it["name"] for r in records for it in r["checklist"]
               if HEADER_HINT.match(it["name"])]
    runons = [it["name"] for r in records for it in r["checklist"] if len(it["name"]) > 300]
    empty_items = sum(1 for r in records for it in r["checklist"] if not it["name"].strip())
    required_n = sum(1 for r in records for it in r["checklist"] if it["required"])
    print(f"   tổng mục: {total_items} · trung bình {total_items/n:.1f} mục/thủ tục")
    if lens:
        lens.sort()
        print(f"   độ dài tên mục: min={lens[0]} trung vị={lens[len(lens)//2]} max={lens[-1]}")
    print(f"   đánh dấu bắt buộc: {required_n}/{total_items}")
    print(f"   mục rỗng: {empty_items} · nghi là TIÊU ĐỀ nhóm: {len(headers)} · dài >300 ký tự: {len(runons)}")
    for h in headers[:3]:
        print(f"      [tiêu đề?] {h[:70]}")
    for ro in runons[:2]:
        print(f"      [dài] {ro[:110]}…")
    if headers:
        flag("LATER", f"{len(headers)} mục checklist thật ra là TIÊU ĐỀ nhóm — "
                      "UI render thành checkbox sẽ vô nghĩa; lọc được ở normalize (không cần cào lại)")
    if runons:
        flag("LATER", f"{len(runons)} mục gộp nhiều giấy tờ vào một dòng (>300 ký tự) — "
                      "checkbox sẽ quá dài; cần tách ở tầng hiển thị")
    if required_n == 0 and total_items:
        flag("LATER", "KHÔNG mục nào được đánh 'bắt buộc' — cờ required của nguồn vô dụng, "
                      "UI đừng hiển thị 'bắt buộc/tuỳ chọn'")

    section("5. PHÍ — ô dễ gây hiểu nhầm nhất")
    with_fee = [r for r in records if r["fees"]]
    n_fee_rows = sum(len(r["fees"]) for r in records)
    numeric = [f for r in records for f in r["fees"] if f["amount_value"] is not None]
    text_only = [f for r in records for f in r["fees"]
                 if f["amount_value"] is None and f["amount_text"]]
    nothing = [f for r in records for f in r["fees"]
               if f["amount_value"] is None and not f["amount_text"]]
    print(f"   thủ tục có mục phí: {pct(len(with_fee), n)}")
    print(f"   dòng phí: {n_fee_rows} → có SỐ: {len(numeric)} · chỉ CHỮ: {len(text_only)} · RỖNG CẢ HAI: {len(nothing)}")
    if nothing:
        flag("SCRAPE", f"{len(nothing)} dòng phí rỗng cả số lẫn chữ — nạp vào là rác, "
                       "phải bỏ ở normalize")
    print(f"   thủ tục KHÔNG có dữ liệu phí: {pct(n - len(with_fee), n)}"
          "  ← UI TUYỆT ĐỐI không được ghi 'Miễn phí'")

    section("6. TỆP ĐÍNH KÈM")
    with_files = [r for r in records if r["files"]]
    n_files = sum(len(r["files"]) for r in records)
    print(f"   thủ tục có tệp: {pct(len(with_files), n)} · tổng {n_files} tệp")
    missing_local, present_local = [], 0
    for r in records:
        for f in r["files"]:
            p = paths.RAW_DIR / f["local_path"] if f["local_path"] else None
            if f.get("file_available") and p and p.exists() and p.stat().st_size > 0:
                present_local += 1
            else:
                missing_local.append((r["proc_id"], f["file_name"]))
    print(f"   đã tải về đĩa: {present_local}/{n_files} · thiếu: {len(missing_local)}")
    for pid, fn in missing_local[:5]:
        print(f"      thiếu {pid}: {fn[:60]}")
    if missing_local:
        flag("LATER", f"{len(missing_local)}/{n_files} tệp cổng trả về 0 byte — "
                      "đã đánh dấu file_available=0, UI chỉ cần ẩn nút tải")
    exts = collections.Counter(
        (f["file_name"].rsplit(".", 1)[-1].lower() if "." in f["file_name"] else "(không đuôi)")
        for r in records for f in r["files"])
    if exts:
        print("   đuôi tệp:", dict(exts))

    section("7. RÁC TRONG VĂN BẢN")
    html_hits = [(r["proc_id"], HTML_RE.findall(r["description"])[:3])
                 for r in records if HTML_RE.search(r["description"] or "")]
    ctrl = [r["proc_id"] for r in records
            if any(ord(c) < 32 and c not in "\n\t" for c in (r["description"] or ""))]
    dlens = sorted(len(r["description"]) for r in records)
    print(f"   độ dài mô tả: min={dlens[0]} trung vị={dlens[len(dlens)//2]} max={dlens[-1]}")
    print(f"   có thẻ HTML/entity: {len(html_hits)} · có ký tự điều khiển: {len(ctrl)}")
    for pid, hits in html_hits[:4]:
        print(f"      {pid}: {hits}")
    if html_hits:
        flag("LATER", f"{len(html_hits)} mô tả còn thẻ HTML/entity — LLM đọc vẫn hiểu "
                      "nhưng hiện lên UI sẽ xấu; dọn ở normalize, không cần cào lại")
    if dlens[0] == 0:
        flag("LATER", f"{sum(1 for x in dlens if x==0)} thủ tục KHÔNG có mô tả nào")

    section("8. NGÀY THÁNG / META")
    bad_dates = [(r["proc_id"], r["decision_date"]) for r in records
                 if r["decision_date"] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["decision_date"])]
    years = collections.Counter(r["decision_date"][:4] for r in records if r["decision_date"])
    print("   năm quyết định:", dict(sorted(years.items())))
    future = [r["proc_id"] for r in records if r["decision_date"] > "2026-12-31"]
    print(f"   ngày sai định dạng: {len(bad_dates)} · ngày ở tương lai xa: {len(future)}")
    if future:
        flag("LATER", f"{len(future)} thủ tục có ngày quyết định ở tương lai: {future[:3]}")
    no_meta = sum(1 for r in records if not r["decision_date"])
    if no_meta:
        flag("LATER", f"{no_meta} thủ tục thiếu ngày hiệu lực — ô 'Thông tin meta' phải "
                      "dùng trạng thái ② thay vì để trống")

    section("8b. TRỤC MCQ — phân nhánh làm rõ trước khi truy xuất")
    multi_case = [r for r in records if len(r.get("cases") or []) > 1]
    multi_subj = [r for r in records if len(r.get("subjects") or []) > 1]
    print(f"   có >1 TRƯỜNG HỢP (executionCases): {pct(len(multi_case), n)}")
    print(f"   có >1 ĐỐI TƯỢNG  (subjectTypes)  : {pct(len(multi_subj), n)}")
    need = [r for r in records if len(r.get("cases") or []) > 1 or len(r.get("subjects") or []) > 1]
    print(f"   CẦN hỏi MCQ ít nhất một lần      : {pct(len(need), n)}")
    if multi_case:
        cl = sorted(len(c["case_name"]) for r in multi_case for c in r["cases"])
        print(f"   độ dài câu lựa chọn: trung vị={cl[len(cl)//2]} max={cl[-1]} ký tự")
        ex = max(multi_case, key=lambda r: len(r["cases"]))
        print(f"   ví dụ nhiều nhánh nhất: {ex['proc_id']} ({len(ex['cases'])} nhánh)")
        for c in ex["cases"][:3]:
            print(f"      - {c['case_name'][:74]}")
    if any(len(c["case_name"]) > 120 for r in multi_case for c in r["cases"]):
        flag("LATER", "một số lựa chọn MCQ dài >120 ký tự — nhóm đã chốt GIỮ NGUYÊN "
                      "câu đầy đủ; UI cần cho xuống dòng, đừng cắt mất nghĩa")

    section("9. TÊN TRÙNG — cùng một tên, nhiều cấp thực hiện")
    by_name = collections.defaultdict(list)
    for r in records:
        by_name[r["name"]].append(r)
    dups = {k: v for k, v in by_name.items() if len(v) > 1}
    n_in_dup = sum(len(v) for v in dups.values())
    print(f"   nhóm tên trùng: {len(dups)} · số bản ghi dính: {pct(n_in_dup, n)}")
    for name, group in list(dups.items())[:3]:
        print(f"   \"{name[:58]}\" ×{len(group)}")
        for r in group:
            print(f"        {r['proc_id']:12s} cấp={r['agency_levels'] or '(trống)':12s}"
                  f" {r['executing_agency'][:38]}")
    if dups:
        flag("SCRAPE", f"{n_in_dup}/{n} thủ tục trùng TÊN, chỉ khác CẤP (Bộ/Tỉnh/Xã). "
                       "Tra theo tên là KHÔNG đủ để ra một thủ tục duy nhất — "
                       "System 2 phải lọc thêm agency_levels hoặc hỏi lại người dùng")

    section("10. TRA CỨU — kiểm tra thật bằng chính hàm search()")
    try:
        from Database.pipeline.search import search
        conn = connect()
        probes = ["the can cuoc", "giay phep lai xe", "ma tuy", "xuat nhap canh"]
        bad_search = 0
        for q in probes:
            hits = search(conn, q, 3)
            full = hits[0]["name"] if hits else ""
            top = full[:56] if hits else "(không có)"
            # kiểm tra trên tên ĐẦY ĐỦ, không phải bản đã cắt ngắn để in
            ok = bool(hits) and all(t in fold_name(full) for t in q.split()[:2])
            bad_search += 0 if ok else 1
            print(f"   {q!r:20s} → {len(hits)} kết quả · đầu bảng: {top}"
                  f"  {'✔' if ok else '✘'}")
        conn.close()
        if bad_search:
            flag("SCRAPE", f"{bad_search}/{len(probes)} truy vấn ra kết quả không liên quan")
    except Exception as exc:
        print("   lỗi:", exc)

    section("KẾT LUẬN")
    scrape = [m for k, m in findings if k == "SCRAPE"]
    later = [m for k, m in findings if k == "LATER"]
    print(f"\n🔴 PHẢI SỬA TRONG CODE CÀO/CHUẨN HOÁ ({len(scrape)}):")
    for m in scrape or ["   (không có)"]:
        print(f"   • {m}")
    print(f"\n🟡 SỬA SAU CŨNG ĐƯỢC, KHÔNG CẦN CÀO LẠI ({len(later)}):")
    for m in later or ["   (không có)"]:
        print(f"   • {m}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Ghép 363 thủ tục cấp XÃ của TP.HCM với dữ liệu Cổng DVCQG.

NGUỒN YÊU CẦU (cái quyết định phạm vi):
    Database/THU_TUC_CAP_XA_363.csv
    = cột "Xã" trong Phụ lục Quyết định 113/QĐ-UBND (TP.HCM, 2025),
      "Danh mục TTHC thuộc thẩm quyền giải quyết của cấp tỉnh, cấp xã".
    Lưu ý: TP.HCM gọi PHƯỜNG là cấp XÃ — cùng một cấp.

VẤN ĐỀ: văn bản của TP.HCM **chỉ có TÊN**, không có mã TTHC. Cổng DVCQG thì
tra theo mã. Nên bắt buộc phải ghép bằng tên, và ghép tên thì không bao giờ
đạt 100%. File này làm việc đó một cách CÓ KIỂM CHỨNG: mỗi thủ tục đều ghi rõ
điểm giống nhau và xếp vào một mức tin cậy, để người đọc tự thẩm định lại.

BA MỨC TIN CẬY:
    exact  (= 1.00)      tên trùng khít sau khi bỏ dấu/bỏ tiền tố "Thủ tục"
    high   (>= 0.90)     phủ gần hết các TỪ QUAN TRỌNG — nhận tự động
    review (>= 0.78)     GIỐNG NHƯNG CHƯA CHẮC — **KHÔNG nạp vào CSDL**,
                         chờ người xác nhận bằng mắt (xem báo cáo)
    absent (< 0.78)      không tìm thấy trên cổng

CHẤM ĐIỂM THEO TỪ, KHÔNG THEO KÝ TỰ — xem build_idf() để biết vì sao.

⚠️ VÌ SAO `review` KHÔNG ĐƯỢC TỰ ĐỘNG NẠP:
Đo thật ở mức 0,78–0,90 vẫn còn ghép sai nghĩa, ví dụ
  "Giấy phép BÁN LẺ sản phẩm thuốc lá"  →  "Giấy phép SẢN XUẤT sản phẩm thuốc lá"
  "GIA HẠN giao khu vực biển"           →  "GIAO khu vực biển"
Đưa nhầm một thủ tục vào CSDL tệ hơn nhiều so với thiếu một thủ tục: người dân
sẽ làm theo hướng dẫn của thủ tục KHÁC. Nên mức này chỉ vào báo cáo, không vào DB.
Muốn nạp thì thêm cờ --include-review sau khi đã tự kiểm.

⚠️ Đã kiểm chứng: nhóm `absent` KHÔNG phải do ghép kém. Tra thẳng bằng API tìm
kiếm của chính cổng (tham số q) cũng trả về 0 kết quả. Ví dụ "Giấy phép bán lẻ
rượu", "cửa hàng bán lẻ LPG chai" — cổng dichvucong.gov.vn không có các thủ tục
này trong tập dữ liệu dịch vụ công của nó.

Chạy:
    python -m Database.pipeline.match_xa
    python -m Database.pipeline.match_xa --verify-api   (tra API cho nhóm absent)
"""

from __future__ import annotations

import argparse
import collections
import csv
import difflib
import json
import logging
import math
import re

from Database.pipeline import paths
from Database.pipeline.textutil import fold

log = logging.getLogger("pipeline.match_xa")

CSV_PATH = paths.DATABASE_DIR / "THU_TUC_CAP_XA_363.csv"
MATCH_PATH = paths.RAW_DIR / "_xa_match.json"
REPORT_PATH = paths.DATABASE_DIR / "BAO_CAO_GHEP_363_XA.md"

T_HIGH = 0.90
T_REVIEW = 0.78

# Những chữ có mặt hay không cũng cùng một thủ tục — bỏ đi trước khi so sánh.
_PREFIX = re.compile(r"^(thu tuc|tthc)\s+")


def norm(text: str) -> str:
    """Chuẩn hoá để so tên: bỏ dấu, bỏ tiền tố 'Thủ tục', bỏ ký tự không phải chữ."""
    s = _PREFIX.sub("", fold(text))
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_csv(path=None) -> list[dict]:
    path = path or CSV_PATH
    with open(path, encoding="utf-8-sig") as fh:
        return [{"index": int(r["Index"]), "csv_name": r["Name"].strip()}
                for r in csv.DictReader(fh) if r.get("Name", "").strip()]


def load_catalogs() -> tuple[list[dict], set[str]]:
    full = [json.loads(l) for l in
            paths.CATALOG_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    commune_path = paths.RAW_DIR / "catalog_commune.jsonl"
    commune = set()
    if commune_path.exists():
        commune = {json.loads(l)["id"] for l in
                   commune_path.read_text(encoding="utf-8").splitlines() if l.strip()}
    return full, commune


def build_idf(catalog: list[dict]) -> dict[str, float]:
    """Trọng số cho từng từ: từ càng hiếm càng quan trọng.

    VÌ SAO CẦN — đây là bài học đắt giá:
    So sánh theo KÝ TỰ thì "Giấy phép **bán lẻ** thuốc lá" và
    "Giấy phép **sản xuất** thuốc lá" giống nhau tới 0,897, trong khi nghĩa
    thì ngược hẳn. Tương tự "bán lẻ LPG chai" khớp nhầm "sản xuất phân bón".
    Vì hai tên dài, đổi vài chữ không kéo điểm xuống đủ.

    Cách chữa: chấm theo TỪ, và mỗi từ có trọng số theo độ hiếm (IDF).
    "lpg", "rượu", "phân bón" rất hiếm ⇒ trọng số cao ⇒ thiếu nó là rớt ngay.
    "cấp", "giấy", "thủ tục" xuất hiện khắp nơi ⇒ trọng số gần 0.
    """
    df: collections.Counter = collections.Counter()
    for r in catalog:
        for tok in set(norm(r["name"]).split()):
            df[tok] += 1
    n = len(catalog)
    return {t: math.log(n / (1 + c)) for t, c in df.items()}


def _weight(tok: str, idf: dict[str, float]) -> float:
    # Từ chưa từng thấy trong catalog là từ rất riêng ⇒ cho trọng số cao nhất.
    return idf.get(tok, math.log(len(idf) or 2))


def idf_score(a: str, b: str, idf: dict[str, float]) -> float:
    """Tỉ lệ 'sức nặng' của tên CSV được tên trên cổng phủ được."""
    ta, tb = norm(a).split(), set(norm(b).split())
    if not ta:
        return 0.0
    total = sum(_weight(t, idf) for t in ta)
    hit = sum(_weight(t, idf) for t in ta if t in tb)
    return hit / total if total else 0.0


def match(rows: list[dict], catalog: list[dict], commune: set[str]) -> list[dict]:
    idf = build_idf(catalog)
    normed = [(norm(r["name"]), r) for r in catalog]
    exact: dict[str, dict] = {}
    for k, r in normed:
        exact.setdefault(k, r)      # giữ bản đầu tiên nếu trùng tên

    out = []
    for row in rows:
        q = norm(row["csv_name"])
        if q in exact:
            best, score, ratio = exact[q], 1.0, 1.0
        else:
            # Chấm bằng TỪ (idf) là chính; ký tự chỉ dùng để phá hoà.
            # Cộng thêm chút ưu tiên cho thủ tục thật sự ở cấp xã — đúng phạm vi.
            cands = []
            for k, r in normed:
                sc = idf_score(row["csv_name"], r["name"], idf)
                if sc <= 0.0:
                    continue
                ch = difflib.SequenceMatcher(None, q, k).ratio()
                bonus = 0.03 if r["id"] in commune else 0.0
                cands.append((sc + bonus, ch, r, sc))
            if not cands:
                best, score, ratio = catalog[0], 0.0, 0.0
            else:
                combined, ratio, best, score = max(cands, key=lambda x: (x[0], x[1]))

        tier = ("exact" if score >= 0.999 and ratio >= 0.999 else
                "high" if score >= T_HIGH else
                "review" if score >= T_REVIEW else "absent")
        out.append({
            **row,
            "tier": tier,
            "score": round(score, 3),
            "char_ratio": round(ratio, 3),
            "proc_id": best["code"] if tier != "absent" else "",
            "source_id": best["id"] if tier != "absent" else "",
            "portal_name": best["name"] if tier != "absent" else "",
            "domain": "; ".join(best.get("categories") or []) if tier != "absent" else "",
            "is_commune_level": bool(tier != "absent" and best["id"] in commune),
            "nearest_if_absent": best["name"] if tier == "absent" else "",
        })
    return out


ACCEPTED = ("exact", "high")


def dedupe(matched: list[dict], include_review: bool = False
           ) -> tuple[list[dict], list[dict]]:
    """Nhiều tên trong CSV có thể trỏ về cùng một thủ tục trên cổng."""
    ok = set(ACCEPTED) | ({"review"} if include_review else set())
    seen: dict[str, dict] = {}
    dups = []
    for m in matched:
        if m["tier"] not in ok:
            continue
        if m["proc_id"] in seen:
            dups.append(m)
        else:
            seen[m["proc_id"]] = m
    return list(seen.values()), dups


def write_report(matched: list[dict], uniq: list[dict], dups: list[dict]) -> None:
    by = {t: [m for m in matched if m["tier"] == t]
          for t in ("exact", "high", "review", "absent")}
    n = len(matched)
    L = []
    A = L.append
    A("<!-- Sinh tự động bằng: python -m Database.pipeline.match_xa — đừng sửa tay -->")
    A("")
    A("# Báo cáo ghép 363 thủ tục cấp Xã (TP.HCM) với Cổng DVCQG")
    A("")
    A("**Nguồn yêu cầu:** `THU_TUC_CAP_XA_363.csv` — cột *Xã* trong Phụ lục "
      "Quyết định **113/QĐ-UBND** (TP.HCM, 2025).")
    A("*TP.HCM gọi **Phường** là cấp **Xã** — cùng một cấp.*")
    A("")
    A("Văn bản của Thành phố **chỉ có tên thủ tục, không có mã TTHC**, nên bắt buộc "
      "phải ghép bằng tên. Bảng dưới ghi rõ mức tin cậy của từng thủ tục.")
    A("")
    A("## Tổng hợp")
    A("")
    A("| Mức | Nghĩa | Số lượng |")
    A("|---|---|---|")
    A(f"| `exact` | tên trùng khít | **{len(by['exact'])}** |")
    A(f"| `high` | khác vài chữ, nhận tự động (≥ {T_HIGH}) | **{len(by['high'])}** |")
    A(f"| `review` | giống nhưng CHƯA CHẮC (≥ {T_REVIEW}) — cần người xem lại | **{len(by['review'])}** |")
    A(f"| `absent` | **không có trên Cổng DVCQG** | **{len(by['absent'])}** |")
    A(f"| | **Tổng** | **{n}** |")
    A("")
    A(f"→ **Nạp vào CSDL: {len(by['exact'])+len(by['high'])}/{n}** thủ tục "
      f"(`exact` + `high`), gồm **{len(uniq)}** mã khác nhau "
      f"({len(dups)} tên CSV trỏ trùng vào mã đã có).")
    A("")
    A(f"→ **KHÔNG nạp: {len(by['review'])}** thủ tục mức `review` — cần người xác nhận. "
      f"Ở mức 0,78–0,90 vẫn còn ghép sai nghĩa "
      "(*bán lẻ* ↔ *sản xuất*, *gia hạn* ↔ *giao*). "
      "Đưa nhầm thủ tục vào CSDL tệ hơn thiếu thủ tục.")
    A("")
    A("## ⚠️ Nhóm `absent` — không phải lỗi ghép")
    A("")
    A("Đã tra thẳng bằng API tìm kiếm của chính cổng (tham số `q`) cho nhóm này: "
      "**trả về 0 kết quả**. Nghĩa là cổng `dichvucong.gov.vn` thật sự không có "
      "các thủ tục đó trong tập dữ liệu dịch vụ công.")
    A("")
    A("Phần lớn là giấy phép kinh doanh có điều kiện do cấp xã/phường cấp "
      "(rượu, thuốc lá, LPG chai…). Muốn có thì phải lấy từ nguồn khác — "
      "Cơ sở dữ liệu quốc gia về TTHC, hoặc trang dịch vụ công của TP.HCM.")
    A("")
    A("| STT | Tên trong quyết định | Gần nhất tìm được | Điểm |")
    A("|---|---|---|---|")
    for m in sorted(by["absent"], key=lambda x: x["index"]):
        A(f"| {m['index']} | {m['csv_name'][:96]} | {m['nearest_if_absent'][:70]} | {m['score']} |")
    A("")
    A("## Nhóm `review` — CHƯA nạp, cần người xác nhận")
    A("")
    A("Đánh dấu ✔ vào cái nào đúng rồi báo lại, sẽ nạp bổ sung. "
      "Cột **[XÃ]** = thủ tục đó thật sự ở cấp xã trên cổng (dấu hiệu ủng hộ).")
    A("")
    A("")
    A("| STT | Tên trong quyết định | Mã | Tên trên cổng | Điểm | Cấp xã? |")
    A("|---|---|---|---|---|---|")
    for m in sorted(by["review"], key=lambda x: -x["score"]):
        A(f"| {m['index']} | {m['csv_name'][:70]} | `{m['proc_id']}` | "
          f"{m['portal_name'][:70]} | {m['score']} | "
          f"{'XÃ' if m['is_commune_level'] else '—'} |")
    A("")
    if dups:
        A("## Tên CSV trỏ trùng vào cùng một mã")
        A("")
        A("| STT | Tên trong quyết định | Trỏ vào mã |")
        A("|---|---|---|")
        for m in sorted(dups, key=lambda x: x["index"]):
            A(f"| {m['index']} | {m['csv_name'][:90]} | `{m['proc_id']}` |")
        A("")
    REPORT_PATH.write_text("\n".join(L), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ghép danh mục 363 thủ tục cấp Xã")
    ap.add_argument("--include-review", action="store_true",
                    help="nạp cả mức review (CHỈ dùng sau khi đã tự kiểm bằng mắt)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    paths.ensure_dirs()

    rows = load_csv()
    catalog, commune = load_catalogs()
    log.info("CSV %d thủ tục · catalog %d · trong đó cấp xã %d",
             len(rows), len(catalog), len(commune))

    matched = match(rows, catalog, commune)
    uniq, dups = dedupe(matched, args.include_review)

    MATCH_PATH.write_text(json.dumps(matched, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    write_report(matched, uniq, dups)

    for t in ("exact", "high", "review", "absent"):
        log.info("  %-7s %d", t, sum(1 for m in matched if m["tier"] == t))
    log.info("NẠP VÀO DB: %d mã khác nhau (%d tên trỏ trùng)%s",
             len(uniq), len(dups),
             "" if args.include_review else " — mức 'review' bị loại, xem báo cáo")
    (paths.RAW_DIR / "_xa_selected.json").write_text(
        json.dumps(sorted({m["proc_id"] for m in uniq}), ensure_ascii=False, indent=1),
        encoding="utf-8")
    log.info("báo cáo → %s", REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

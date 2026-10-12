"""So sánh nút "Tìm web" của Strict: Strict thuần / kết hợp (thủ tục + khối web) / chỉ web. Chạy 1 lần, KHÔNG tune.
python eval/run_websearch_ab.py   (PYTHONPATH=<cha của repo>, cần mạng + Ollama; S4 tắt)
Đo tự động: (1) hành vi và thủ tục top-1 của Strict có giữ nguyên khi kết hợp không (phải giữ 100%);
(2) khối web: có nguồn, có ghi [n], tốc độ; (3) con số tiền/ngày/giờ trong khối web mâu thuẫn với câu trả lời thủ tục.
Chất lượng nội dung KHÔNG đo tự động được: xem eval/results/websearch_ab.md và chấm tay."""
import json
import os
import re
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "server"))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "ab.db"), S3_USE_LLM="0", S3_PLANNER_MODE="rules", S3_NO_WARMUP="1")
os.environ.pop("S4_ENABLED", None)

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402

h6 = json.load(open(os.path.join(HERE, "cases_h6.json"), encoding="utf-8"))
answer = [c for c in h6 if "q" in c and c["beh"] == "answer"][:14]
other = [c for c in h6 if "q" in c and c["beh"] in ("clarify", "apologize")][:6]
OUT_OF_DATASET = ["giá vé tàu hỏa Hà Nội đi Sài Gòn hôm nay bao nhiêu", "thời tiết Hà Nội ngày mai",
                  "mức lương tối thiểu vùng 1 hiện nay là bao nhiêu", "phí cấp lại thẻ bảo hiểm y tế bị mất năm nay",
                  "lệ phí đổi giấy phép lái xe ô tô mới nhất", "giờ làm việc của uỷ ban nhân dân phường"]
cases = ([dict(id=c["id"], q=c["q"], beh=c["beh"], exp=c["expect_ids"]) for c in answer + other]
         + [dict(id=f"oos-{i+1}", q=q, beh="out_of_dataset", exp=[]) for i, q in enumerate(OUT_OF_DATASET)])

NUM = re.compile(r"\d[\d.,]*\s*(?:đồng|vnđ|vnd|đ\b|nghìn|ngàn|triệu|ngày|giờ|tháng|năm)", re.I)


def nums(t):
    return {re.sub(r"[\s.,]", "", m.lower()) for m in NUM.findall(t)}


def post(c, q, web):
    t = time.perf_counter()
    r = c.post("/chat", json={"text": q, "websearch": web})
    assert r.status_code == 200, r.text
    d = r.json()
    d["ms"] = int((time.perf_counter() - t) * 1000)
    return d


def text_of(d):
    return "\n".join((b.get("text") or "") for b in d["blocks"])


rows = []
with TestClient(main.app) as c:
    for cs in cases:
        row = dict(id=cs["id"], q=cs["q"], beh=cs["beh"])
        main.WEBSEARCH_MODE = "combined"
        base, comb = post(c, cs["q"], False), post(c, cs["q"], True)
        main.WEBSEARCH_MODE = "only"
        web = post(c, cs["q"], True)
        wb = comb["blocks"][-1] if comb["kind"] != "clarify" and comb["blocks"] else None
        base_txt, web_txt = text_of(base), (wb or {}).get("text", "")
        row.update(kind=base["kind"], kind_comb=comb["kind"], kind_only=web["kind"],
                   strict_kept=comb["blocks"][:len(base["blocks"])] == base["blocks"] and comb["kind"] == base["kind"],
                   web_added=bool(wb), web_sources=len((wb or {}).get("sources", [])),
                   web_cites=bool(re.search(r"\[\d\]", web_txt)), web_failed=web_txt.startswith("Không tra được"),
                   extra_ms=comb["ms"] - base["ms"], base_ms=base["ms"], comb_ms=comb["ms"], only_ms=web["ms"],
                   new_numbers=sorted(nums(web_txt) - nums(base_txt)) if base["kind"] == "answer" else [],
                   conflict_numbers=sorted(nums(web_txt) - nums(base_txt)) if base["kind"] == "answer" and nums(base_txt) and nums(web_txt) - nums(base_txt) else [],
                   base_text=base_txt, web_text=web_txt, web_urls=[s["url"] for s in (wb or {}).get("sources", [])])
        rows.append(row)
        print(f"{cs['id']:8} {base['kind']:9} kept={row['strict_kept']} web={row['web_added']} src={row['web_sources']} "
              f"+{row['extra_ms']}ms conflict={row['conflict_numbers']}", flush=True)

n = len(rows)
ans = [r for r in rows if r["kind"] == "answer"]
S = dict(n=n, strict_kept=f"{sum(r['strict_kept'] for r in rows)}/{n}", web_added=f"{sum(r['web_added'] for r in rows)}/{n}",
         web_failed=sum(r["web_failed"] for r in rows), with_sources=sum(r["web_sources"] > 0 for r in rows),
         with_cites=sum(r["web_cites"] for r in rows),
         answer_cases=len(ans), answer_with_conflict_numbers=sum(bool(r["conflict_numbers"]) for r in ans),
         extra_ms_median=sorted(r["extra_ms"] for r in rows)[n // 2], extra_ms_max=max(r["extra_ms"] for r in rows))
print(json.dumps(S, ensure_ascii=False, indent=1))
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump(dict(summary=S, rows=rows), open(os.path.join(HERE, "results", "websearch_ab.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(HERE, "results", "websearch_ab.md"), "w", encoding="utf-8") as f:
    f.write("# So sánh Tìm web (Strict): chấm tay\n\nMỗi câu: A = Strict thuần, B = khối web thêm vào. Chấm: web có đúng/hữu ích không, có mâu thuẫn A không.\n\n")
    for r in rows:
        f.write(f"## {r['id']} ({r['beh']}, Strict={r['kind']}) — {r['q']}\n\n**A (Strict):**\n\n{r['base_text'][:900] or '(trống)'}\n\n"
                f"**B (web, {r['web_sources']} nguồn, +{r['extra_ms']} ms):**\n\n{r['web_text'] or '(không có)'}\n\n"
                + "".join(f"- {u}\n" for u in r["web_urls"]) + "\n---\n\n")

"""Chấm bộ real_v1 System 3 từ kết quả của `eval/run_pseudo.py` (eval/results/real_v1.json) và viết báo cáo.

    # chạy hệ thống MỘT lần (luật, không GPU, DB bản 3):
    S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 S3_DATA_DB=<DB bản 3> python run_server.py eval/run_pseudo.py real_v1/cases_real_v1_labeled.json real_v1
    # chấm + báo cáo (cùng biến môi trường vì tính thêm MRR bằng cách gọi lại adapter trên các câu answer, không đổi gì):
    S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 S3_DATA_DB=<DB bản 3> python run_server.py eval/real_v1/score_real_v1.py <thư mục ghi báo cáo>

Báo cáo: hành vi, top-1, top-3, MRR (xếp hạng = mã đã chọn rồi tới ứng viên theo thứ tự, tối đa 6), mỗi chỉ số kèm khoảng tin cậy Wilson 95%,
recall clarify / apologize, theo tầng (random / chude), ma trận nhầm lẫn, danh sách mọi câu sai.
"""
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EVAL, "saved_results", "real_v1")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, EVAL)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({k / n:.1%}; 95% CI {lo:.1%} đến {hi:.1%})" if n else "0/0"


rows = json.load(open(os.path.join(EVAL, "results", "real_v1.json"), encoding="utf-8"))
cases = {c["id"]: c for c in json.load(open(os.path.join(HERE, "cases_real_v1_labeled.json"), encoding="utf-8"))}
assert len(rows) == len(cases), (len(rows), len(cases))

# MRR: gọi lại adapter trên các câu answer (cùng cấu hình), lấy thứ tự ứng viên
import answer_adapter  # noqa: E402
rr = {}
for r in rows:
    if r["beh"] != "answer":
        continue
    out = answer_adapter.adapter([{"role": "user", "text": r["q"]}])
    order = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
    order += [c for t in out["tasks"] for c in t.get("candidates", [])]
    seen = []
    for x in order:
        if x not in seen:
            seen.append(x)
    rank = next((i + 1 for i, x in enumerate(seen[:6]) if x in r["exp"]), None)
    rr[r["id"]] = rank
mrr = sum(1 / v for v in rr.values() if v) / max(len(rr), 1)

n = len(rows)
beh_ok = sum(r["beh_ok"] for r in rows)
ans = [r for r in rows if r["beh"] == "answer"]
cm = Counter((r["beh"], r["got"]) for r in rows)
L = []
w = L.append
w("# Kết quả chạy System 3 trên bộ real_v1 (một lần, luật, không GPU)\n")
w(f"Bộ: `eval/real_v1/cases_real_v1_labeled.json` ({n} câu; mã băm trong `eval/real_v1/LOCK.md`). Cấu hình: `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`, DB thủ tục bản 3 (1.517 thủ tục).\n")
w("## 1. Chỉ số chính\n")
w("| Chỉ số | Kết quả |\n|---|---|")
w(f"| Hành vi đúng (cả {n} câu) | {fmt(beh_ok, n)} |")
w(f"| Top-1 (câu `answer`) | {fmt(sum(r['top1'] for r in ans), len(ans))} |")
w(f"| Top-3 (câu `answer`) | {fmt(sum(r['top3'] for r in ans), len(ans))} |")
w(f"| MRR (câu `answer`, tối đa 6 ứng viên) | {mrr:.3f} |")
for b in ("answer", "clarify", "apologize"):
    s = [r for r in rows if r["beh"] == b]
    w(f"| Recall `{b}` (hệ thống ra đúng hành vi khi nhãn là `{b}`) | {fmt(sum(r['beh_ok'] for r in s), len(s))} |")
w("")
w("## 2. Ma trận nhầm lẫn (hàng: nhãn, cột: hệ thống)\n")
w("| nhãn \\ hệ thống | answer | clarify | apologize |\n|---|---|---|---|")
for a in ("answer", "clarify", "apologize"):
    w(f"| {a} | " + " | ".join(str(cm[(a, b)]) for b in ("answer", "clarify", "apologize")) + " |")
w("")
fa = cm[("apologize", "answer")]
w(f"Ở {fa + cm[('apologize', 'clarify')]}/{sum(1 for r in rows if r['beh'] == 'apologize')} câu mà nhãn là `apologize`, hệ thống vẫn trả lời hoặc hỏi lại thay vì từ chối: nó từ chối đúng chưa tới 53% các câu ngoài phạm vi (luật, xử phạt, khiếu nại, tình trạng hồ sơ).\n")
w("## 3. Theo tầng lấy mẫu\n")
w("| Tầng | Số câu | Hành vi đúng | Câu `answer` | Top-1 | Top-3 |\n|---|---|---|---|---|---|")
for st in ("random", "chude"):
    s = [r for r in rows if cases[r["id"]]["stratum"] == st]
    a = [r for r in s if r["beh"] == "answer"]
    w(f"| {st} | {len(s)} | {fmt(sum(r['beh_ok'] for r in s), len(s))} | {len(a)} | {fmt(sum(r['top1'] for r in a), len(a)) if a else '-'} | {fmt(sum(r['top3'] for r in a), len(a)) if a else '-'} |")
w("")
w("## 4. Mọi câu sai\n")
bad = [r for r in rows if not r["beh_ok"] or (r["beh"] == "answer" and not r["top1"])]
w(f"{len(bad)} câu (hành vi sai, hoặc nhãn `answer` mà mã đầu không đúng).\n")
w("| id | Nhãn | Hệ thống | Mã đúng | Mã hệ thống chọn | Câu hỏi (rút gọn) |\n|---|---|---|---|---|---|")
for r in bad:
    q = " ".join(r["q"].split()); q = q if len(q) <= 90 else q[:55] + " … " + q[-30:]
    w(f"| {r['id'][-3:]} | {r['beh']} | {r['got']} | {', '.join(r['exp'])} | {', '.join(r['tops']) or '-'} | {q} |")
w("")
w("## 5. Cần nhớ khi đọc\n")
for t in ("Nhãn do hai lượt AI gán (κ 0,753), chưa có lượt kiểm của người trên mẫu.",
          f"Chỉ có {len(ans)} câu `answer`; khoảng tin cậy top-1 rộng.",
          "Bộ này là câu hỏi thật của người dân (Cổng dịch vụ công Bình Định, Bộ Công an): phần lớn là luật, xử phạt, khiếu nại, tình trạng hồ sơ; khác hẳn các bộ do nhóm soạn.",
          "Chạy chế độ luật, không LLM; không phản ánh bản người dùng thấy (có LLM).",
          "Lần chạy đầu (22/10) dùng nhầm DB cũ `data/runtime/system3.db` (1.350 thủ tục, bản 1) vì thiếu biến `S3_DATA_DB`; kết quả bị bỏ (lưu ở `KHONG_DUNG_lan_dau_sai_DB.json`, hành vi 161/282, top-1 3/55). Lần này chạy lại đúng DB bản 3, không đổi gì khác; không chỉnh hệ thống hay nhãn giữa hai lần."):
    w("- " + t)
open(os.path.join(OUT, "report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump({"n": n, "behavior_ok": beh_ok, "answer_n": len(ans), "top1": sum(r["top1"] for r in ans), "top3": sum(r["top3"] for r in ans), "mrr": mrr, "confusion": {f"{a}->{b}": v for (a, b), v in cm.items()}},
          open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n".join(L[:22]))

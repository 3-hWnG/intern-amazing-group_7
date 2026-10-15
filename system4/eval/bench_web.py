"""Bộ đo nút "Tìm web" của Friendly: 16 câu cố định, chạy 1 lần, KHÔNG chỉnh sau khi xem kết quả.

    python system4/eval/bench_web.py NAME [--cpu-note TEXT]

Bật server riêng của bench.py (cổng 8399), gửi từng câu với websearch=true (DuckDuckGo thật, cần mạng).
Tự đo (không nhờ AI chấm): có đi qua web, số nguồn có URL, có ghi [n], có số trong câu trả lời, có nói "không có thông tin",
tốc độ. 8 câu "ổn định" có từ khoá đáp án: đạt khi câu trả lời chứa một trong từ khoá. 8 câu "thay đổi theo ngày" KHÔNG tự chấm
đúng/sai được (đáp án đổi theo ngày): chỉ chấm có web + có nguồn + có số + không từ chối; nội dung phải chấm tay từ trường "answer".
Kết quả: system4/eval/results/bench/NAME_web.json
"""
from __future__ import annotations
import argparse
import json
import re
import time
from pathlib import Path

import bench as B

# (id, câu hỏi, nhóm, từ khoá đáp án — chỉ nhóm "stable")
CASES = [
    ("w01", "Thời tiết Hà Nội hôm nay thế nào?", "live", None),
    ("w02", "Giá vàng SJC hôm nay bao nhiêu?", "live", None),
    ("w03", "Tỷ giá USD Vietcombank hôm nay là bao nhiêu?", "live", None),
    ("w04", "Giá xăng RON 95 hiện nay bao nhiêu một lít?", "live", None),
    ("w05", "Mức lương tối thiểu vùng 1 hiện nay là bao nhiêu?", "live", None),
    ("w06", "Giá vé tàu hỏa Hà Nội đi Sài Gòn bao nhiêu?", "live", None),
    ("w07", "Kết quả vòng đấu V-League gần nhất thế nào?", "live", None),
    ("w08", "Tin tức nổi bật hôm nay ở Việt Nam là gì?", "live", None),
    ("w09", "Thủ đô của Nhật Bản là thành phố nào?", "stable", ["tokyo", "dong kinh"]),
    ("w10", "Đỉnh núi nào cao nhất Việt Nam?", "stable", ["phan xi pang", "fansipan"]),
    ("w11", "Tác giả của Truyện Kiều là ai?", "stable", ["nguyen du"]),
    ("w12", "Hồ Hoàn Kiếm nằm ở thành phố nào?", "stable", ["ha noi"]),
    ("w13", "Công dân từ bao nhiêu tuổi phải làm căn cước công dân?", "stable", ["14 tuoi", "du 14", "tu 14", "14 "]),
    ("w14", "Không đội mũ bảo hiểm khi đi xe máy bị phạt bao nhiêu tiền?", "stable", ["400.000", "400 nghin", "600.000", "400,000"]),
    ("w15", "Thời hạn tạm trú tối đa mỗi lần đăng ký là bao lâu?", "stable", ["2 nam", "02 nam", "hai nam", "24 thang"]),
    ("w16", "Lệ phí cấp hộ chiếu phổ thông lần đầu là bao nhiêu?", "stable", ["200.000", "200 nghin", "200,000"]),
]


def metrics(group: str, kws, r: dict) -> dict:
    content, meta = r["content"], r["meta"]
    f = B.fold(content)
    srcs = [s for s in meta.get("sources") or [] if s.get("url")]
    unsure = any(p in f for p in B.UNSURE)
    m = {"web": bool(meta.get("web")), "url_sources": len(srcs), "cites": bool(re.search(r"\[\d+\]", content)),
         "has_number": bool(re.search(r"\d", content)), "unsure": unsure}
    if kws:
        m["keyword_ok"] = any(B.fold(k) in f for k in kws)
    m["ok"] = m["web"] and m["url_sources"] > 0 and m["has_number" if group == "live" else "keyword_ok"] and not unsure
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--cpu-note", default="")
    args = ap.parse_args()
    settings = dict(B.PRESETS[args.name.split("_")[0].split("+")[0]])
    B.unload_models()
    srv = B.start_server(settings, args.name + "_web")
    runs = []
    try:
        cl = B.Client()
        cl.ensure_datasets()
        cl.use([]); cl.chat("Chào bạn")                   # nóng máy; câu thật bên dưới không chia sẻ lịch sử
        for cid_, q, group, kws in CASES:
            cl.forget()
            r = cl.chat(q, None, web=True)
            m = metrics(group, kws, r)
            runs.append({"id": cid_, "q": q, "group": group, **m, "answer": r["content"],
                         "sources": [s.get("url") for s in r["meta"].get("sources") or []],
                         **{k: r[k] for k in ("first_s", "final_first_s", "total_s", "search_ms", "prompt_s", "output_s", "output_tokens", "load_s")}})
            print(f"  {'OK  ' if m['ok'] else 'FAIL'} {cid_} {group:<6} {r['final_first_s']:>5.1f}s/{r['total_s']:>5.1f}s "
                  f"nguồn={m['url_sources']} [n]={m['cites']} từchối={m['unsure']}"
                  + (f" từkhoá={m['keyword_ok']}" if kws else ""))
    finally:
        B.stop_server(srv)
    live, stable = [x for x in runs if x["group"] == "live"], [x for x in runs if x["group"] == "stable"]
    summ = {"n": len(runs), "web_used": sum(x["web"] for x in runs), "with_url_sources": sum(x["url_sources"] > 0 for x in runs),
            "with_cites": sum(x["cites"] for x in runs), "refused_unsure": sum(x["unsure"] for x in runs),
            "live_ok": f"{sum(x['ok'] for x in live)}/{len(live)}", "stable_keyword_ok": f"{sum(x['ok'] for x in stable)}/{len(stable)}",
            "total_med_s": B._med([x["total_s"] for x in runs]), "first_med_s": B._med([x["final_first_s"] for x in runs]),
            "search_med_ms": B._med([x["search_ms"] for x in runs]), "output_s_med": B._med([x["output_s"] for x in runs])}
    res = {"name": args.name, "settings": settings, "time": time.strftime("%Y-%m-%d %H:%M"), "cpu_note": args.cpu_note,
           "summary": summ, "runs": runs}
    B.OUT_DIR.mkdir(parents=True, exist_ok=True)
    (B.OUT_DIR / f"{args.name}_web.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

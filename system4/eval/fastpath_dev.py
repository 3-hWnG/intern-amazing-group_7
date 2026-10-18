"""Chạy thử ĐƯỜNG NHANH (chỉ phần code) trên bộ câu của bench_cases.py — để sửa engine mà không tốn lượt đo model thật.

    python system4/eval/fastpath_dev.py [--suites accuracy,greeting,tourism] [--cues <fastpath_cues.json>] [--show]

Dựng server tạm (model giả: embedding / reranker / AI sinh chữ), nạp các tệp của bench, biên dịch đường nhanh. Gợi ý AI đặt tên trường lấy
từ tệp đệm (--cues, mặc định: không có -> chỉ tên cột), để giống lượt đo thật. Mỗi câu: đường nhanh trả lời (chấm bằng bench.score) hay nhường.
Bộ MÙ chưa dùng ("shop") bị chặn: chỉ chạy khi có --allow-blind (dùng khi nghiệm thu, không dùng khi sửa).
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--suites", default="accuracy,greeting,tourism")
ap.add_argument("--cues", default="")
ap.add_argument("--show", action="store_true")
ap.add_argument("--allow-blind", action="store_true")
ap.add_argument("--report", action="store_true")
ap.add_argument("--debug", action="append", default=[], help="câu hỏi để in trạng thái bên trong engine")
a = ap.parse_args()
suites = a.suites.split(",")
if "shop" in suites and not a.allow_blind:
    raise SystemExit("bộ mù 'shop' chưa nghiệm thu: không chạy khi đang sửa (thêm --allow-blind nếu đúng là nghiệm thu)")

TMP = Path(tempfile.mkdtemp())
(TMP / "s4").mkdir()
if a.cues:
    shutil.copy(a.cues, TMP / "s4" / "fastpath_cues.json")
os.environ.update(S3_DB_PATH=str(TMP / "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RUNTIME_DIR=str(TMP / "s4"))
sys.path[:0] = [str(REPO / "server"), str(HERE)]

from fastapi.testclient import TestClient   # noqa: E402
import main                                  # noqa: E402
from system3.system4.server import auth, llm, search, settings   # noqa: E402
import bench                                 # noqa: E402
from bench_cases import all_cases            # noqa: E402

search.embed = lambda texts: [[1.0] + [0.0] * 1023 for _ in texts]
search.rerank = lambda q, texts: [0.0 for _ in texts]
llm.chat_json = lambda *x, **k: {}           # cues: chỉ từ tệp đệm


async def fake_fast(messages, schema):
    raw = json.dumps({"plan": "", "answer": "(đường cũ)", "ask_back": False, "choices": []})
    yield raw


llm.stream_json = fake_fast
FILES = {"class": HERE / "data" / "ds_lop_gia.xlsx", "tourism": HERE / "data" / "tourism_records.xlsx",
         "procedures": HERE / "data" / "MAU_100_THU_TUC.xlsx", "policy": bench.policy_docx(), "du_lich": bench.tourism_xlsx()}
if a.allow_blind:
    FILES["cua_hang"] = bench.shop_xlsx()
cases = [c for c in all_cases() if c["suite"] in suites and c["datasets"] and all(d in FILES for d in c["datasets"])]

with TestClient(main.app) as c:
    c.cookies.set(auth.COOKIE, c.post("/s4/auth/signup", json={"username": "dev1", "password": "123456"}).cookies.get(auth.COOKIE))
    ds = {}
    for k, p in FILES.items():
        r = c.post("/s4/datasets", files={"file": (p.name, p.read_bytes())})
        ds[k] = r.json()["dataset"]["id"]
    t0 = time.time()
    while True:
        st = {k: c.get(f"/s4/fastpath/{i}").json().get("status") for k, i in ds.items()}
        if all(s in ("ready", "error", "skipped") for s in st.values()):
            break
        assert time.time() - t0 < 600, st
        time.sleep(0.5)
    for k, i in ds.items():
        rep = c.get(f'/s4/fastpath/{i}').json()
        print(f"  {k:10} {rep.get('message')}")
        if a.report:   # loại câu nào bị tắt và câu tự kiểm nào chưa đạt
            for tb in rep.get("tables", []):
                for route, x in (tb.get("test") or {}).items():
                    print(f"      {tb['name']:14} {route:9} {x['pass']}/{x['n']} {'BẬT' if x['on'] else 'TẮT'}")
                    for f in x["fails"][:3]:
                        print(f"          Q: {f['q']} -> {f['got'][:100]!r}")

    if a.debug:   # in trạng thái bên trong engine cho từng câu (bảng, trường khớp, kiểu, dòng tốt nhất)
        from system3.system4.server import fastpath
        from system3.system4.server.fastpath.compile import tokens
        from system3.system4.server.fastpath import engine as E
        eng, _ = fastpath._engine([i for k, i in ds.items() if k != "cua_hang" or a.allow_blind])
        for qq in a.debug:
            qt = tokens(qq); q = [f for f, _ in qt]
            print("Q:", qq, q)
            for t in eng.ents:
                f, pos, neg = eng._field(t, qt, set())
                cand = [w for i, w in enumerate(q) if w not in E.STOP and w not in t["_tok"] and w not in eng.cuewords and i not in pos]
                rk = eng._entities(t, cand, q)[:2]
                if f or rk:
                    print(f"   {t['name'][:20]:20} field={f!r} ({t['fields'][f]['type'] if f else '-'}) pos={sorted(pos)} cand={cand} top={[(round(x[0],2), round(x[1],2), x[2], t['rows'][x[3]]['title'][:30]) for x in rk]}")
            print("   ->", eng.answer(qq, {}))

    def use(keys):
        for k, i in ds.items():
            c.patch(f"/s4/datasets/{i}", json={"active": k in keys})

    out, cur = [], None
    for case in cases:
        key = tuple(sorted(case["datasets"]))
        if key != cur:
            use(case["datasets"]); cur = key
        cid, m = None, None
        for t in case["turns"]:
            r = c.post("/s4/chat", json={"text": t, "conversation_id": cid})
            cid = json.loads(r.text.split("\n\n")[0][6:])["conversation_id"]
            m = c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]
        fp = m["meta"].get("fast_path")
        ok, why = (None, []) if not fp else bench.score(case["check"], m["content"], m["meta"])
        out.append({"id": case["id"], "suite": case["suite"], "split": case["split"], "route": (fp or {}).get("route"), "pass": ok, "why": why})
        if a.show or ok is False:
            mark = {True: "PASS", False: "FAIL", None: "----"}[ok]
            print(f"{mark} {case['id']:16} {str((fp or {}).get('route') or '-'):11} {case['turns'][-1][:60]!r} -> {m['content'][:120]!r} {why if ok is False else ''}")
    for s in suites:
        rs = [x for x in out if x["suite"] == s]
        if rs:
            print(f"== {s}: {len(rs)} câu | đường nhanh trả lời {sum(x['pass'] is not None for x in rs)} | đúng {sum(x['pass'] is True for x in rs)}"
                  f" | SAI {sum(x['pass'] is False for x in rs)}")
shutil.rmtree(TMP, ignore_errors=True)

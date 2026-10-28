"""NV5 — bộ đo chung cho độ chính xác, tốc độ, hành vi (System 4 Friendly / Chuyên gia) trên model THẬT.

    python system4/eval/bench.py run NAME [--set KEY=VALUE ...] [--split dev|exam|blind|all] [--repeat N] [--suites a,b] [--no-behavior]
    python system4/eval/bench.py compare results/bench/A.json results/bench/B.json ...
    python system4/eval/bench.py swap            # thời gian Ollama đổi qua lại 2 model (Strict qwen3:4b <-> Friendly Instruct)
    python system4/eval/bench.py strict --model M --name N   # bộ đo System 3 (Strict) với model M (câu 1D)

"run" tự bật một server riêng (cổng 8399, dữ liệu riêng ở system4/eval/bench_runtime — không đụng web thật), ghi cài đặt
NAME (+ --set) vào settings.json của nó, nạp 4 bộ dữ liệu một lần (danh sách lớp GIẢ, chính sách Word, du lịch, thủ tục),
gỡ mọi model khỏi card đồ hoạ trước khi đo, hỏi thử 2 câu cho nóng máy rồi chạy bộ câu bench_cases.py + 22 tình huống
hành vi của nv2_behavior.py. Kết quả: system4/eval/results/bench/NAME.json. Chấm bằng luật, không nhờ AI chấm.
"bài thi cuối" (split exam) chỉ dùng để nghiệm thu: khi chỉnh tham số chỉ nhìn split dev.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
def _pyroot() -> Path:
    """Thư mục có junction system3 -> CHÍNH repo này (18/10: "pyroot" trên máy dev trỏ sang repo system3 khác, nên server bench
    từng import system3.* của repo kia). Biến BENCH_PYROOT thắng; không tìm thấy thì giữ "pyroot" như cũ."""
    if os.environ.get("BENCH_PYROOT"):
        return Path(os.environ["BENCH_PYROOT"])
    for p in sorted(REPO.parent.glob("pyroot*")):
        if (p / "system3").exists() and (p / "system3").resolve() == REPO.resolve():
            return p
    return REPO.parent / "pyroot"


PYROOT = _pyroot()
PY = REPO / ".venv" / "Scripts" / "python.exe"
RUNTIME = Path(os.environ.get("BENCH_RUNTIME") or HERE / "bench_runtime")   # BENCH_RUNTIME: chạy trên runtime riêng (vd. bản sạch)
OUT_DIR = HERE / "results" / "bench"
PORT = 8399
BASE = f"http://127.0.0.1:{PORT}"
sys.path.insert(0, str(HERE))
INSTRUCT = "qwen3:4b-instruct-2507-q4_K_M"

# Cấu hình đặt tên sẵn (ghi đè cài đặt mặc định của config.py). --set thêm / sửa từng khoá.
PRESETS = {
    "today": {},
    "inst07": {"FRIENDLY_MODEL": INSTRUCT, "FRIENDLY_TEMPERATURE": 0.7},
    "inst02": {"FRIENDLY_MODEL": INSTRUCT, "FRIENDLY_TEMPERATURE": 0.2},
}

UNSURE = ("khong co thong tin", "khong tim thay", "khong co trong du lieu", "chua co thong tin", "khong biet", "khong ro", "khong the",
          "chua ro", "khong chac", "khong co du lieu", "khong duoc cung cap", "chua duoc cung cap", "khong co san", "lien he",
          "khong de cap", "chua co du lieu", "khong nam trong", "khong co ghi", "khong ghi", "khong co muc", "chua duoc cap nhat",
          "khong co thong tin chinh thuc", "chua the xac nhan", "khong xac dinh", "khong co ten", "chua biet", "khong nho")


def fold(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    return re.sub(r"\s+", " ", "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d"))


# ------------------------------------------------------------------ chấm
def score(check: dict, content: str, meta: dict) -> tuple[bool, list[str]]:
    """Trả (đạt, các lý do trượt). Mọi so khớp chữ: không phân biệt hoa thường / dấu."""
    f, why = fold(content), []
    titles = [s.get("title", "") for s in (meta.get("sources") or []) + (meta.get("consulted") or [])]
    if "all" in check and not all(fold(x) in f for x in check["all"]):
        why.append("thiếu: " + ", ".join(x for x in check["all"] if fold(x) not in f))
    if "any" in check and not any(fold(x) in f for x in check["any"]):
        why.append("không có ý nào trong: " + " | ".join(check["any"]))
    nums = check.get("num") or []   # 27/10: vai cau Phan B ghi "num": 195 (so tran) thay vi [195] -> re.escape(int) crash
    if isinstance(nums, (int, float, str)):
        nums = [nums]
    for n in nums:   # con số đứng riêng (không dính chữ số khác): "4" không khớp "14" hay "4.000"
        n = str(n)
        if not re.search(r"(?<![\d.,])" + re.escape(n) + r"(?![\d]|[.,]\d)", content):
            why.append(f"thiếu số {n}")
    if "none" in check and any(fold(x) in f for x in check["none"]):
        why.append("có chữ cấm: " + ", ".join(x for x in check["none"] if fold(x) in f))
    for rx in check.get("no_regex", []):
        m = re.search(rx, content, re.I)
        if m:
            why.append(f"chi tiết bịa: {m.group()!r}")
    if check.get("refusal") and not any(p in f for p in UNSURE):
        why.append("không nói là không có / không biết")
    if check.get("source") and not any(fold(check["source"])[:50] in fold(t) or fold(t) in fold(check["source"]) for t in titles):
        why.append(f"nguồn sai (có: {titles[:3]})")
    if "ask_back" in check and bool(meta.get("choices")) != check["ask_back"]:
        why.append("không hỏi lại" if check["ask_back"] else "hỏi lại thừa")
    for x in check.get("choices_all", []):
        if not any(fold(x) in fold(c) for c in meta.get("choices") or []):
            why.append(f"thiếu lựa chọn {x}")
    if check.get("small_talk"):
        if meta.get("guard") == "Chỉ trả lời từ dữ liệu" or any(p in f for p in ("khong co trong du lieu", "khong co thong tin", "khong tim thay")):
            why.append("câu xã giao bị trả lời 'không có trong dữ liệu'")
        if meta.get("sources") or meta.get("consulted"):
            why.append("câu xã giao mà vẫn hiện nguồn")
        if meta.get("choices"):
            why.append("câu xã giao mà hỏi lại")
    return not why, why


# ------------------------------------------------------------------ server riêng
def unload_models():
    """Gỡ mọi model Ollama khỏi card đồ hoạ (giữa các cấu hình, để cấu hình trước không làm sai số đo)."""
    try:
        import ollama
        for m in ollama.Client().ps().models:
            subprocess.run(["ollama", "stop", m.model], capture_output=True, timeout=60)
    except Exception as e:
        print("  (không gỡ được model:", e, ")")


def start_server(settings: dict, log_name: str) -> subprocess.Popen:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "settings.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(PYROOT), PYTHONIOENCODING="utf-8", S4_ENABLED="1", S3_USE_LLM="0", APP_PORT=str(PORT),
               S4_RUNTIME_DIR=str(RUNTIME), S3_DB_PATH=str(RUNTIME / "s3.db"), S4_RATE_LIMIT="0",   # bench hỏi liên tục: tắt giới hạn lượt hỏi
               S4_BOOTSTRAP="0",   # 24/10: bench chỉ đo bộ dữ liệu nó tự nạp; bootstrap (dữ liệu thật + FLM) trên runtime mới làm máy quá nóng và server chết
               S4_ABI_SYNC="0",    # 25/10: không đồng bộ abi.com.vn khi đo (runtime đo không có khoá: lượt "trước" gọi /site/settings một lần, bị 401)
               PYTHONUNBUFFERED="1",   # 27/10: server chết đột ngột lúc nạp dataset (RemoteProtocolError/WinError 10053), log luôn cắt sạch không
               # traceback — nghi do log ra FILE thì Python mặc định block-buffer, dòng lỗi thật còn kẹt trong buffer chưa kịp ghi xuống đĩa lúc
               # chết. Buộc server không buffer gì để lần chết tới log giữ được traceback thật (nếu có), thay vì chỉ thấy im lặng.
               LLM_MODEL=settings.get("FRIENDLY_MODEL", "qwen3:4b"))   # System 3 nạp sẵn model này lúc khởi động: dùng chung, khỏi chiếm thêm
    log = open(RUNTIME / f"server_{log_name}.log", "w", encoding="utf-8", buffering=1)   # 27/10: line-buffer phía ghi file luôn (xem lý do trên)
    p = subprocess.Popen([str(PY), "main.py"], cwd=REPO / "server", env=env, stdout=log, stderr=subprocess.STDOUT)
    _restrict(p.pid)
    for _ in range(180):
        try:
            if httpx.get(BASE + "/health", timeout=2).status_code == 200:
                return p
        except httpx.HTTPError:
            pass
        if p.poll() is not None:
            raise SystemExit(f"server không chạy được, xem {log.name}")
        time.sleep(1)
    p.kill()
    raise SystemExit("server không lên sau 180 giây")


def _restrict(pid: int) -> None:
    """27/10: TẮT — hạ ưu tiên (BELOW_NORMAL) + giới hạn 4 luồng CPU cho server/llama-server lúc 24/10 làm máy đỡ nóng, nhưng gây crash ngẫu
    nhiên không traceback đúng lúc server nạp model lên GPU (nghi Windows TDR: CPU bị bóp ưu tiên thấp không phục vụ kịp đồng bộ GPU, driver
    tự reset và giết process) — lặp lại nhiều lần khi đo J2 S4-1..S4-4 (26/10), hết crash khi tắt hàm này, không liên quan 4 cờ sửa. Giữ canh
    nhiệt qua thermal.guard() giữa các câu (đã đủ cho yêu cầu ≤ 70°C); bỏ riêng phần hạ luồng/ưu tiên này."""
    return


def stop_server(p: subprocess.Popen):
    p.terminate()
    try:
        p.wait(20)
    except subprocess.TimeoutExpired:
        p.kill()


class Client:
    def __init__(self):
        self.c = httpx.Client(base_url=BASE, timeout=600, transport=httpx.HTTPTransport(retries=3))
        cred = {"username": "bench", "password": "matkhau123"}
        if self.c.post("/s4/auth/login", json=cred).status_code != 200:
            assert self.c.post("/s4/auth/signup", json=cred).status_code == 200, "không tạo được tài khoản bench"
        self.ds = {}

    def _get(self, url: str):
        """GET có retry: loopback đôi khi bị rớt kết nối thoáng qua (không phải lỗi server) khi server đang
        bận xử lý (nạp bảng mới, biên dịch đường nhanh) lâu — 27/10, phát hiện khi chạy J3 trên real_v4_s4."""
        for attempt in range(8):
            try:
                return self.c.get(url)
            except httpx.TransportError as e:
                if attempt == 7:
                    raise
                print(f"  (mất kết nối tạm lúc GET {url}, thử lại lần {attempt + 1}/8: {e})")
                time.sleep(2)

    def ensure_datasets(self, needed: set | None = None):
        """Nạp các bộ dữ liệu một lần cho bench_runtime (lần sau dùng lại; đổi bộ đọc tệp thì server tự xử lý lại).
        24/10: chỉ nạp bộ mà các câu được chọn cần (`needed`), TỪNG bộ một, đợi xử lý xong mới nạp bộ sau, canh nhiệt giữa các lần nạp."""
        files = {"class": HERE / "data" / "ds_lop_gia.xlsx", "tourism": HERE / "data" / "tourism_records.xlsx",
                 "procedures": HERE / "data" / "MAU_100_THU_TUC.xlsx", "policy": policy_docx(), "du_lich": tourism_xlsx(), "cua_hang": shop_xlsx(),
                 **REAL3_FILES, **REAL_V4_S4_FILES}
        if needed:
            files = {k: v for k, v in files.items() if k in needed}
        sys.path.insert(0, str(REPO / "eval"))
        from thermal import guard
        have = {d["filename"]: d for d in self._get("/s4/datasets").json()["datasets"]}
        for key, path in files.items():
            if path.name not in have:
                guard(every=0, label="nạp " + path.name)
                with open(path, "rb") as f:
                    r = self.c.post("/s4/datasets", files={"file": (path.name, f)})
                assert r.status_code == 200, r.text
                print(f"  nạp {path.name}…")
                t0 = time.time()
                while time.time() - t0 < 1800:     # đợi bộ này xử lý + biên dịch đường nhanh xong rồi mới nạp bộ sau (đỡ dồn tải)
                    d = {x["filename"]: x for x in self._get("/s4/datasets").json()["datasets"]}.get(path.name, {})
                    fp = self._get(f"/s4/fastpath/{d['id']}").json().get("status") if d.get("id") and d.get("status") == "ready" else None
                    if d.get("status") == "error" or fp in ("ready", "error", "skipped"):
                        break
                    time.sleep(3)
        while True:
            ds = {d["filename"]: d for d in self._get("/s4/datasets").json()["datasets"]}
            pending = [n for n in (p.name for p in files.values()) if ds[n]["status"] not in ("ready", "error")]
            if not pending:
                break
            time.sleep(2)
        for key, path in files.items():
            d = ds[path.name]
            assert d["status"] == "ready", f"{path.name}: {d['message']}"
            self.ds[key] = d
        t0 = time.time()   # đường nhanh: đợi biên dịch + tự kiểm xong (kể cả khi đo đường cũ) để không đo lẫn lúc GPU đang biên dịch
        while time.time() - t0 < 900:
            st = {k: self._get(f"/s4/fastpath/{d['id']}").json().get("status") for k, d in self.ds.items()}
            if all(s in ("ready", "error", "skipped") for s in st.values()):
                break
            time.sleep(3)
        print("  đường nhanh:", {k: self._get(f"/s4/fastpath/{d['id']}").json().get("message", "")[:90] for k, d in self.ds.items()})
        self.active = {k for k, d in self.ds.items() if d["active"]}

    def use(self, keys: list[str]):
        for k, d in self.ds.items():
            want = k in keys
            if want != (k in self.active):
                r = self.c.patch(f"/s4/datasets/{d['id']}", json={"active": want})
                assert r.status_code == 200, r.text
                (self.active.add if want else self.active.discard)(k)

    def forget(self):
        """Xoá bộ nhớ của tài khoản bench: điều nhớ từ câu trước không được ảnh hưởng câu sau."""
        for m in self.c.get("/s4/memory").json()["items"]:
            self.c.delete(f"/s4/memory/{m['id']}")

    def chat(self, text: str, cid: str | None = None, web: bool = False) -> dict:
        t0, first, final_first, evs = time.time(), None, None, []
        with self.c.stream("POST", "/s4/chat", json={"text": text, "conversation_id": cid, "websearch": web}) as r:
            buf = ""
            for chunk in r.iter_text():
                buf += chunk
                while "\n\n" in buf:
                    line, buf = buf.split("\n\n", 1)
                    if not line.startswith("data: "):
                        continue
                    ev = json.loads(line[6:]); evs.append(ev)
                    if ev["type"] == "delta":
                        first = first or time.time() - t0
                        final_first = final_first or time.time() - t0
                    elif ev["type"] in ("checking", "replace"):   # checking: bản cuối không hiện dần, hiện lúc xong (= total)
                        final_first = None if ev["type"] == "checking" else (final_first or time.time() - t0)
        total = time.time() - t0
        cid = evs[0]["conversation_id"]
        msg = self.c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]
        tr = self.c.get(f"/s4/trace/{msg['id']}").json().get("trace") or {}
        tm = tr.get("timing") or {}
        stats = tm.get("llm_stats") or []
        return {"cid": cid, "content": msg["content"], "meta": msg["meta"], "first_s": round(first or total, 2),
                "final_first_s": round(final_first or total, 2), "total_s": round(total, 2),
                "search_ms": tm.get("search_ms"), "search_parts": tm.get("search_parts"), "table_ms": tm.get("table_ms"),
                "llm_calls": len(stats), "prompt_tokens": sum(s.get("prompt_tokens", 0) for s in stats),
                "prompt_s": round(sum(s.get("prompt_s", 0) for s in stats), 2), "output_tokens": sum(s.get("output_tokens", 0) for s in stats),
                "output_s": round(sum(s.get("output_s", 0) for s in stats), 2), "load_s": round(sum(s.get("load_s", 0) for s in stats), 2),
                "plan": (tr.get("output") or {}).get("plan")}


REAL3_FILES = {k: HERE / "real_v3" / "data" / f for k, f in (   # bộ mù thứ ba: 4 bảng Wikipedia thật (real_v3/build_v3.py)
    ("tinh_thanh", "hanh_chinh_tinh_thanh.xlsx"), ("san_bay", "giao_thong_san_bay.xlsx"),
    ("vuon_quoc_gia", "moi_truong_vuon_quoc_gia.xlsx"), ("thuy_dien", "nang_luong_thuy_dien.xlsx"))}

REAL_V4_S4_FILES = {k: HERE / "real_v4_s4" / "data" / f for k, f in (   # 27/10: bo mu thu tu (J2/J3) - 8 bang Wikipedia thuc
    # (real_v4_s4/build_v4.py, LOCK.md). THIEU dict nay la ly do ensure_datasets() chua tung nap bang nao cua real_v4_s4 khi
    # chay suite "real4": needed chua cac key duoi day nhung "files" (truoc khi sua) khong co key nao khop -> 0 bang nap,
    # moi cau tra loi "nguon sai (co: [])" vi khong co du lieu nao active. Phat hien 27/10 khi chay J3 v4a_before.
    ("dan_toc", "van_hoa_dan_toc.xlsx"), ("san_van_dong", "the_thao_san_van_dong.xlsx"),
    ("phi_vat_the", "van_hoa_phi_vat_the.xlsx"), ("bao_vat", "lich_su_bao_vat_quoc_gia.xlsx"),
    ("dai_hoc", "giao_duc_truong_dai_hoc.xlsx"), ("di_tich_dac_biet", "di_tich_quoc_gia_dac_biet.xlsx"),
    ("ngan_hang", "ngan_hang.xlsx"), ("xe_buyt_tphcm", "xe_buyt_tphcm.xlsx"))}


def tourism_xlsx() -> Path:
    """Dữ liệu du lịch giả cho bộ mù (make_tourism.py); thiếu thì sinh lại."""
    path = HERE / "data" / "du_lich_gia.xlsx"
    if not path.exists():
        from make_tourism import build
        build(path)
    return path


def shop_xlsx() -> Path:
    """Dữ liệu cửa hàng giả cho bộ mù thứ hai (make_shop.py); thiếu thì sinh lại."""
    path = HERE / "data" / "cua_hang_gia.xlsx"
    if not path.exists():
        from make_shop import OUT, SHEETS
        from make_tourism import build
        build(OUT, SHEETS)
    return path


def policy_docx() -> Path:
    """Tệp Word chính sách giống nv3_specialist.py (tạo lại mỗi lần, nội dung cố định)."""
    import docx
    path = RUNTIME / "chinh_sach_team7.docx"
    if path.exists():
        return path
    RUNTIME.mkdir(parents=True, exist_ok=True)
    d = docx.Document()
    d.add_heading("Chính sách đổi trả", level=1)
    d.add_paragraph("Khách hàng được đổi trả sản phẩm trong vòng 7 ngày kể từ ngày nhận hàng nếu sản phẩm còn nguyên tem và hoá đơn.")
    d.add_heading("Giờ làm việc", level=1)
    d.add_paragraph("Bộ phận hỗ trợ làm việc từ 8 giờ đến 17 giờ 30, thứ Hai đến thứ Bảy. Chủ nhật nghỉ.")
    t = d.add_table(rows=4, cols=2)
    for i, (a, b) in enumerate([("Hạng thành viên", "Ưu đãi"), ("Bạc", "Giảm 5% mọi đơn hàng"), ("Vàng", "Giảm 10% mọi đơn hàng"),
                                ("Kim cương", "Giảm 15% và miễn phí giao hàng")]):
        t.cell(i, 0).text, t.cell(i, 1).text = a, b
    d.save(path)
    return path


# ------------------------------------------------------------------ chạy
def run(args):
    from bench_cases import all_cases
    base = re.split(r"[+@]", args.name)[0]
    if base not in PRESETS:   # tên lạ -> dùng nhầm cài đặt mặc định (model cũ) mà không biết: dừng luôn (lỗi đã gặp khi đo NV5)
        raise SystemExit(f"tên cấu hình phải bắt đầu bằng một trong {list(PRESETS)} (vd. inst02+D), không phải {args.name!r}")
    settings = dict(PRESETS[base])
    for kv in args.set or []:
        k, v = kv.split("=", 1)
        try:
            settings[k] = json.loads(v)
        except ValueError:
            settings[k] = v
    cases = [c for c in all_cases() if (args.split == "all" or c["split"] == args.split)
             and (not args.suites or c["suite"] in args.suites.split(","))]
    print(f"[{args.name}] cài đặt: {settings}\n  {len(cases)} câu × {args.repeat} lần")
    unload_models()
    srv = start_server(settings, args.name)
    try:
        cl = Client()
        cl.ensure_datasets({k for c in cases for k in c["datasets"]} | {"policy"} if args.suites else None)   # chọn suite: chỉ nạp bộ dữ liệu cần
        _restrict(srv.pid)     # tiến trình chạy model của Ollama chỉ có sau lượt gọi đầu: giới hạn lại
        cl.use(["policy"]); cl.chat("Chào bạn")             # nóng máy: model + bge-m3 + reranker
        cl.use([]); cl.chat("Bạn giúp được gì cho mình?")
        runs = []
        sys.path.insert(0, str(REPO / "eval"))
        from thermal import guard   # 24/10: máy không quá 70 °C — nóng thì ngủ giữa các câu (eval/thermal.py)
        for c in cases:
            for rep in range(args.repeat):
                guard(label=c["id"])
                cl.use(c["datasets"])
                cl.forget()
                cid, r = None, None
                for t in c["turns"]:
                    r = cl.chat(t, cid); cid = r["cid"]
                ok, why = score(c["check"], r["content"], r["meta"])
                runs.append({"id": c["id"], "suite": c["suite"], "split": c["split"], "kind": c.get("kind"), "rep": rep, "pass": ok, "why": why,
                             "answer": r["content"][:600], "choices": r["meta"].get("choices"),
                             "sources": [s.get("title") for s in r["meta"].get("sources") or []],
                             "consulted": [s.get("title") for s in r["meta"].get("consulted") or []],
                             "small_talk": r["meta"].get("small_talk"), "grounding": r["meta"].get("grounding"),
                             "ambiguity": r["meta"].get("ambiguity"), "guard": r["meta"].get("guard"),
                             "fast_path": (r["meta"].get("fast_path") or {}).get("route"),   # đường nhanh trả lời bằng code (None = đường cũ)
                             **{k: r[k] for k in ("first_s", "final_first_s", "total_s", "search_ms", "search_parts", "table_ms", "llm_calls",
                                                  "prompt_tokens", "prompt_s", "output_tokens", "output_s", "load_s", "plan")}})
                print(f"  {'PASS' if ok else 'FAIL'} {c['id']:<18} {r['first_s']:>5.1f}s/{r['total_s']:>5.1f}s"
                      + (f"  {'; '.join(why)[:110]}" if why else ""))
        behavior = None
        if not args.no_behavior:
            out = OUT_DIR / f"{args.name}_nv2.json"
            env = dict(os.environ, PYTHONIOENCODING="utf-8", NV2_OUT=str(out), PYTHONPATH=str(PYROOT))   # 27/10: nv2_behavior.py tự đoán pyroot bằng path tương đối, sai trên máy có BENCH_PYROOT riêng -> ModuleNotFoundError no module system3, crash ngay dong dau, im lang vi bi nuot loi
            print("  22 tình huống hành vi (nv2_behavior.py)…")
            try:
                proc = subprocess.run([str(PY), str(HERE / "nv2_behavior.py"), BASE], env=env,
                                       capture_output=True, timeout=3600, text=True, encoding="utf-8", errors="replace")
            except subprocess.TimeoutExpired as e:
                print(f"  !! nv2_behavior.py quá giờ (3600s), bỏ qua phần hành vi. stdout cuối:\n{(e.stdout or '')[-2000:]}")
                proc = None
            if out.exists():
                behavior = json.loads(out.read_text(encoding="utf-8"))
                print(f"  hành vi: {behavior['summary']['passed']}/{behavior['summary']['total']}")
            elif proc is not None:
                # 27/10: trước đây lỗi ở đây bị nuốt im lặng (capture_output nhưng không ai đọc) -> không biết
                # vì sao thiếu behavior ở cả 6 lần chạy J3. Giờ in ra để thấy lỗi thật nếu còn crash.
                print(f"  !! nv2_behavior.py không ghi được file kết quả (returncode={proc.returncode}).")
                if proc.stdout:
                    print(f"  --- stdout (2000 ký tự cuối) ---\n{proc.stdout[-2000:]}")
                if proc.stderr:
                    print(f"  --- stderr (2000 ký tự cuối) ---\n{proc.stderr[-2000:]}")
    finally:
        stop_server(srv)
    res = {"name": args.name, "settings": settings, "split": args.split, "repeat": args.repeat, "time": time.strftime("%Y-%m-%d %H:%M"),
           "runs": runs, "behavior": behavior}
    res["summary"] = summarize(res)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{args.name}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print_table([res])


def _rate(rs):
    return round(100 * sum(r["pass"] for r in rs) / len(rs), 1) if rs else None


def _med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def _p90(xs):
    xs = sorted(x for x in xs if x is not None)
    return round(xs[min(len(xs) - 1, int(len(xs) * 0.9))], 2) if xs else None


def summarize(res: dict) -> dict:
    runs = res["runs"]
    acc = [r for r in runs if r["suite"] in ("accuracy", "halluc")]
    tour = [r for r in runs if r["suite"] == "tourism"]
    shop = [r for r in runs if r["suite"] == "shop"]
    gr = [r for r in runs if r["suite"] == "greeting"]
    b = (res.get("behavior") or {}).get("summary") or {}
    b_fail = (b.get("total", 0) - b.get("passed", 0)) if b else None
    spec = [r for r in runs if r["search_ms"] is not None]
    s = {"accuracy": _rate(acc) if acc else _rate(runs), "accuracy_dev": _rate([r for r in acc if r["split"] == "dev"]),
         "accuracy_exam": _rate([r for r in acc if r["split"] == "exam"]),
         "acc_only": _rate([r for r in runs if r["suite"] == "accuracy"]), "halluc": _rate([r for r in runs if r["suite"] == "halluc"]),
         "tourism": _rate(tour), "tourism_fails": sum(not r["pass"] for r in tour),
         "shop": _rate(shop), "shop_fails": sum(not r["pass"] for r in shop),
         "real3": _rate([r for r in runs if r["suite"] == "real3"]),
         "real3_kind": {k: _rate([r for r in runs if r["suite"] == "real3" and r.get("kind") == k]) for k in "LUCSMARF"},
         "real4": _rate([r for r in runs if r["suite"] == "real4"]),
         "real4_kind": {k: _rate([r for r in runs if r["suite"] == "real4" and r.get("kind") == k]) for k in ("L", "U", "C", "S", "M", "A", "R", "F", "X", "AMB")},
         "fast_path": sum(bool(r.get("fast_path")) for r in runs),
         "greeting": _rate(gr), "greeting_fails": sum(not r["pass"] for r in gr), "behavior": f"{b.get('passed')}/{b.get('total')}" if b else None,
         "wrong_behavior": sum(not r["pass"] for r in gr) + (b_fail or 0),
         "first_med": _med([r["final_first_s"] for r in runs]), "total_med": _med([r["total_s"] for r in runs]),
         "total_p90": _p90([r["total_s"] for r in runs]), "spec_total_med": _med([r["total_s"] for r in spec]),
         "search_med_ms": _med([r["search_ms"] for r in spec]), "prompt_tokens_med": _med([r["prompt_tokens"] for r in runs]),
         "prompt_s_med": _med([r["prompt_s"] for r in runs]), "output_s_med": _med([r["output_s"] for r in runs]),
         "load_s_sum": round(sum(r["load_s"] or 0 for r in runs), 1),
         "rewrites": sum(bool(r.get("grounding")) for r in runs), "n": len(runs)}
    return s


def print_table(results: list[dict]):
    cols = [("name", "cấu hình"), ("accuracy", "đúng %"), ("accuracy_dev", "dev %"), ("accuracy_exam", "exam %"), ("halluc", "không bịa %"),
            ("greeting", "chào %"), ("behavior", "hành vi"), ("wrong_behavior", "sai hành vi"), ("first_med", "chữ đầu"),
            ("total_med", "cả câu"), ("total_p90", "cả câu p90"), ("search_med_ms", "tìm ms"), ("prompt_s_med", "đọc s"),
            ("output_s_med", "viết s"), ("rewrites", "viết lại")]
    print("\n| " + " | ".join(h for _, h in cols) + " | pareto |")
    print("|" + "---|" * (len(cols) + 1))
    front = pareto(results)
    for r in results:
        s = {**r["summary"], "name": r["name"]}
        print("| " + " | ".join(str(s.get(k, "")) for k, _ in cols) + f" | {'★' if r['name'] in front else ''} |")


def pareto(results: list[dict]) -> set[str]:
    """Không cấu hình nào khác tốt hơn hoặc bằng ở cả 3 trục (đúng cao, nhanh, ít sai hành vi) và hơn hẳn ở ít nhất 1 trục."""
    pts = {r["name"]: (r["summary"]["accuracy"] or 0, -(r["summary"]["total_med"] or 1e9), -(r["summary"]["wrong_behavior"] or 0))
           for r in results}
    return {n for n, p in pts.items() if not any(all(q[i] >= p[i] for i in range(3)) and q != p for m, q in pts.items() if m != n)}


def compare(args):
    res = [json.loads(Path(f).read_text(encoding="utf-8")) for f in args.files]
    for r in res:
        r["summary"] = summarize(r)
    print_table(res)
    if args.detail:   # câu nào khác nhau giữa các cấu hình (chỉ split dev, không xem bài thi cuối)
        by = {}
        for r in res:
            for x in r["runs"]:
                if x["split"] == "dev":
                    by.setdefault(x["id"], {}).setdefault(r["name"], []).append(x["pass"])
        for cid, d in by.items():
            vals = {n: sum(v) / len(v) for n, v in d.items()}
            if len(set(vals.values())) > 1:
                print(f"  {cid:<20} " + "  ".join(f"{n}={v:.0%}" for n, v in vals.items()))


def swap(args):
    """Đo Ollama nạp lại model khi người dùng chuyển Strict (qwen3:4b) <-> Friendly (Instruct), có bge-m3 đang nạp."""
    import ollama
    cl = ollama.Client()
    unload_models()
    cl.embed(model="bge-m3", input=["khởi động"], keep_alive="30m")
    out = []
    for i in range(3):
        for m in ("qwen3:4b", INSTRUCT):
            t0 = time.time()
            r = cl.generate(model=m, prompt="Chào", options={"num_ctx": 8192, "num_predict": 1}, keep_alive="30m", think=False)
            out.append((m, round(r.load_duration / 1e9, 2), round(time.time() - t0, 2)))
            print(f"  lần {i + 1} {m:<32} nạp {out[-1][1]:>5.2f}s  cả lệnh {out[-1][2]:>5.2f}s")
    print("  đang nạp:", [(m.model, round(m.size_vram / 2**30, 2)) for m in cl.ps().models])
    unload_models()


def strict(args):
    """Bộ đo System 3 (Strict) với một model khác (câu 1D, phương án "Instruct cho cả Strict")."""
    env = dict(os.environ, PYTHONPATH=str(PYROOT), PYTHONIOENCODING="utf-8", S3_USE_LLM="1", LLM_MODEL=args.model)
    unload_models()
    subprocess.run([str(PY), "run.py", "--adapter", "answer_adapter:adapter", "--name", args.name, "--split", args.split],
                   cwd=PYROOT / "system3" / "eval", env=env)   # adapter của System 3 tự tìm server/ qua đường dẫn pyroot/system3


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run"); a.add_argument("name"); a.add_argument("--set", action="append")
    a.add_argument("--split", default="dev"); a.add_argument("--repeat", type=int, default=1); a.add_argument("--suites")
    a.add_argument("--no-behavior", action="store_true")
    a = sub.add_parser("compare"); a.add_argument("files", nargs="+"); a.add_argument("--detail", action="store_true")
    sub.add_parser("swap")
    a = sub.add_parser("strict"); a.add_argument("--model", required=True); a.add_argument("--name", required=True)
    a.add_argument("--split", default="dev")
    args = ap.parse_args()
    {"run": run, "compare": compare, "swap": swap, "strict": strict}[args.cmd](args)

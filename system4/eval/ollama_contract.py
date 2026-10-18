"""Test hợp đồng với Ollama (G3.4, P23): những điều code đang DỰA VÀO hành vi của Ollama + model. Chạy trước mỗi lần nâng Ollama /
đổi model. Cần Ollama đang chạy và model trả lời đã tải; KHÔNG gọi dịch vụ ngoài nào khác.
    python run_server.py system4/eval/ollama_contract.py [--model qwen3:4b-instruct-2507-q4_K_M] [--runs 3]
Kiểm:
  1. `format` = JSON schema: khi model tự dừng, câu trả lời là JSON hợp lệ, đủ trường bắt buộc. Lần nào sinh lặp tới trần token
     (done_reason=length) được báo CẢNH BÁO riêng (hành vi của model, đã gặp 1–2/3 lần với qwen3:4b-instruct; Friendly đặt trần
     FRIENDLY_NUM_PREDICT để không chạy tới hết hạn 120 s).
  2. Thứ tự trường: với tên có tiền tố (a_plan, c_answer… — persona.KEY_PREFIX, JSON_PLAN_FIRST) "a_plan" luôn đứng trước
     "c_answer" trong luồng chữ (Friendly hiện dần phần answer, kế hoạch phải đến trước). Ghi thêm thứ tự khi KHÔNG có tiền tố (tham khảo).
  3. Model nằm trên GPU sau khi nạp (/api/ps size_vram > 0) khi máy có card NVIDIA.
  4. Cùng num_ctx thì không nạp lại model giữa hai lời gọi (load_duration lần 2 nhỏ).
In bảng + ghi system4/eval/results/ollama_contract.json. Mã thoát 0 = đạt."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import ollama

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
SCHEMA = {"type": "object", "properties": {"a_plan": {"type": "string", "maxLength": 300}, "c_answer": {"type": "string"},
                                           "d_ask_back": {"type": "boolean"}, "e_choices": {"type": "array", "items": {"type": "string"}}},
          "required": ["a_plan", "c_answer", "d_ask_back", "e_choices"]}
PLAIN = {"type": "object", "properties": {"plan": {"type": "string"}, "answer": {"type": "string"}}, "required": ["plan", "answer"]}
MSG = [{"role": "system", "content": "Bạn là trợ lý. Trả lời tiếng Việt, ngắn gọn, đúng khuôn JSON được yêu cầu."},
       {"role": "user", "content": "Nêu 2 việc cần làm khi đăng ký khai sinh cho con."}]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL", "qwen3:4b-instruct-2507-q4_K_M"))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--num-ctx", type=int, default=8192)
    a = ap.parse_args()
    c = ollama.Client(host=HOST, timeout=120)
    rows, ok_all = [], True

    def check(name, ok, detail=""):
        nonlocal ok_all
        ok_all &= bool(ok)
        rows.append({"check": name, "ok": bool(ok), "detail": detail})
        print(f"{'ĐẠT ' if ok else 'TRƯỢT'} {name}" + (f" — {detail}" if detail else ""), flush=True)

    try:
        have = [m.model for m in c.list().models]
    except Exception as e:
        print(f"Không kết nối được Ollama tại {HOST}: {e}")
        return 2
    check("model đã tải", a.model in have, a.model)
    if a.model not in have:
        return 1
    opts = {"temperature": 0.2, "num_ctx": a.num_ctx, "num_predict": 600}   # trần token: khuôn JSON có thể sinh mãi (đã gặp khi viết test này)
    order_ok, valid, loads, bad = 0, 0, [], []
    for i in range(a.runs):
        raw = ""
        last = None
        for part in c.chat(model=a.model, messages=MSG, format=SCHEMA, stream=True, think=False, keep_alive="30m", options=opts):
            raw += part["message"]["content"] or ""
            last = part
        loads.append((getattr(last, "load_duration", 0) or 0) / 1e9)
        good = False
        try:
            d = json.loads(raw)
            good = all(k in d for k in SCHEMA["required"]) and isinstance(d["c_answer"], str) and d["c_answer"].strip() != ""
        except ValueError:
            pass
        valid += good
        if not good:
            bad.append({"done_reason": getattr(last, "done_reason", None), "eval_count": getattr(last, "eval_count", None),
                        "head": raw[:160], "tail": raw[-160:]})
        order_ok += 0 <= raw.find('"a_plan"') < raw.find('"c_answer"')
    runaway = [x for x in bad if x["done_reason"] == "length"]
    broken = [x for x in bad if x["done_reason"] != "length"]
    check(f"format JSON schema: model tự dừng thì JSON hợp lệ, đủ trường", not broken,
          f"{a.runs - len(runaway) - len(broken)}/{a.runs - len(runaway)}" + (f"; hỏng: {json.dumps(broken, ensure_ascii=False)[:400]}" if broken else ""))
    rows.append({"check": "CẢNH BÁO: sinh lặp tới trần num_predict (không tự dừng)", "ok": None if not runaway else False,
                 "detail": f"{len(runaway)}/{a.runs}" + (f"; đuôi: {runaway[0]['tail'][-120:]}" if runaway else "")})
    print(f"{'CẢNH BÁO' if runaway else 'ĐẠT '} sinh lặp tới trần token: {len(runaway)}/{a.runs}" +
          (" — cần trần num_predict cho mọi lời gọi (Friendly: FRIENDLY_NUM_PREDICT)" if runaway else ""), flush=True)
    check(f"thứ tự trường có tiền tố: a_plan trước c_answer ({a.runs} lần)", order_ok == a.runs, f"{order_ok}/{a.runs}")
    plain_first = 0
    for _ in range(a.runs):
        r = c.chat(model=a.model, messages=MSG, format=PLAIN, think=False, keep_alive="30m", options=opts)
        t = r["message"]["content"] or ""
        plain_first += 0 <= t.find('"plan"') < t.find('"answer"')
    rows.append({"check": "tham khảo: không tiền tố, plan trước answer", "ok": None, "detail": f"{plain_first}/{a.runs}"})
    print(f"(tham khảo) không tiền tố, plan trước answer: {plain_first}/{a.runs}")
    check("cùng num_ctx: lần gọi sau không nạp lại model", max(loads[1:] or [0]) < 1.0,
          "load_duration: " + ", ".join(f"{x:.2f}s" for x in loads))
    ps = [m for m in c.ps().models if m.model == a.model]
    vram = ps[0].size_vram if ps else 0
    if shutil.which("nvidia-smi"):
        check("model nằm trên GPU (size_vram > 0)", vram > 0, f"size_vram={vram / 2**30:.2f} GB / size={(ps[0].size if ps else 0) / 2**30:.2f} GB")
    else:
        rows.append({"check": "model nằm trên GPU", "ok": None, "detail": "máy không có nvidia-smi: bỏ qua"})
    out = Path(__file__).resolve().parent / "results" / "ollama_contract.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"at": time.strftime("%Y-%m-%d %H:%M:%S"), "model": a.model, "host": HOST,
                               "ollama_version": _version(c), "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'ĐẠT' if ok_all else 'TRƯỢT'} — ghi {out}")
    return 0 if ok_all else 1


def _version(c) -> str:
    try:
        import httpx
        return httpx.get(HOST.rstrip("/") + "/api/version", timeout=3).json().get("version", "")
    except Exception:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())

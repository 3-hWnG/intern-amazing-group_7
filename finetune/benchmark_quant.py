"""So sánh mô hình qua Ollama (ví dụ FP16 vs 4-bit): dung lượng, VRAM, tốc độ, độ trễ.

    .venv\\Scripts\\python.exe finetune\\benchmark_quant.py
    .venv\\Scripts\\python.exe finetune\\benchmark_quant.py --models qwen2.5:3b-instruct-fp16 qwen2.5:3b-instruct-q4_K_M

Mặc định đo LLM_MODEL. Chất lượng câu trả lời của từng mô hình: chạy
Evaluation/evaluate.py với LLM_MODEL tương ứng rồi đặt hai bảng cạnh nhau.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app"))

from config import LLM_MODEL, LLM_NUM_CTX, OLLAMA_HOST  # noqa: E402

PROMPTS = [
    "Đăng ký tạm trú cần chuẩn bị những giấy tờ gì? Trả lời ngắn gọn.",
    "Tóm tắt các bước đăng ký khai sinh cho trẻ mới sinh.",
    "Giải thích khác nhau giữa thường trú và tạm trú trong 3 câu.",
]


def bench(client: httpx.Client, model: str, runs: int) -> dict:
    tags = {m["name"]: m for m in client.get("/api/tags").json().get("models", [])}
    info = tags.get(model) or tags.get(f"{model}:latest") or {}
    if not info:
        return {"model": model, "error": "chưa pull mô hình này"}

    t0 = time.time()
    client.post("/api/generate", json={"model": model, "prompt": "", "keep_alive": "5m"})
    load_s = time.time() - t0

    speeds, ttfts, totals = [], [], []
    for _ in range(runs):
        for prompt in PROMPTS:
            t = time.time()
            res = client.post("/api/chat", json={
                "model": model, "stream": False, "keep_alive": "5m",
                "messages": [{"role": "user", "content": prompt}],
                "options": {"temperature": 0, "num_predict": 200, "num_ctx": LLM_NUM_CTX},
            }).json()
            totals.append(time.time() - t)
            if res.get("eval_duration"):
                speeds.append(res["eval_count"] / (res["eval_duration"] / 1e9))
            ttfts.append((res.get("prompt_eval_duration", 0) + res.get("load_duration", 0)) / 1e9)

    running = {m["name"]: m for m in client.get("/api/ps").json().get("models", [])}
    ps = running.get(model) or running.get(f"{model}:latest") or {}
    client.post("/api/generate", json={"model": model, "keep_alive": 0})   # nhả VRAM

    details = info.get("details") or {}
    return {
        "model": model, "params": details.get("parameter_size", "?"),
        "quant": details.get("quantization_level", "?"),
        "size_gb": info.get("size", 0) / 1e9, "vram_gb": ps.get("size_vram", 0) / 1e9,
        "ram_gb": max(0, ps.get("size", 0) - ps.get("size_vram", 0)) / 1e9,
        "load_s": load_s, "tok_s": statistics.mean(speeds) if speeds else 0,
        "ttft_s": statistics.median(ttfts) if ttfts else 0,
        "latency_s": statistics.median(totals) if totals else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=[LLM_MODEL])
    parser.add_argument("--runs", type=int, default=2)
    args = parser.parse_args()

    with httpx.Client(base_url=OLLAMA_HOST, timeout=300) as client:
        results = [bench(client, m, args.runs) for m in args.models]

    lines = [f"# Benchmark mô hình — {datetime.now():%Y-%m-%d %H:%M}", "",
             "| Mô hình | Tham số | Lượng tử | Dung lượng | VRAM | RAM | Nạp | Token/s | TTFT | Độ trễ (200 token) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        if r.get("error"):
            lines.append(f"| {r['model']} | — | — | — | — | — | — | — | — | {r['error']} |")
            continue
        lines.append(f"| {r['model']} | {r['params']} | {r['quant']} | {r['size_gb']:.2f} GB | "
                     f"{r['vram_gb']:.2f} GB | {r['ram_gb']:.2f} GB | {r['load_s']:.1f}s | "
                     f"{r['tok_s']:.1f} | {r['ttft_s']:.2f}s | {r['latency_s']:.1f}s |")
    lines += ["", "Chất lượng: chạy `Evaluation/evaluate.py` với từng `LLM_MODEL` và so bảng kết quả."]
    text = "\n".join(lines)
    print(text)
    (HERE / "benchmark_results.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

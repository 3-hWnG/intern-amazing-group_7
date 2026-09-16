"""Gộp adapter LoRA -> FP16 -> GGUF -> lượng tử hoá 4-bit -> tạo mô hình Ollama.

Tạo HAI mô hình để so sánh bằng benchmark_quant.py:
    <name>-f16   bản FP16 (chất lượng gốc, nặng)
    <name>       bản 4-bit (mặc định Q4_K_M, dùng để chạy local)

    python finetune/merge_and_export.py --base Qwen/Qwen2.5-3B-Instruct \\
        --adapter finetune/output/<run>/adapter --llama-cpp D:/tools/llama.cpp \\
        --name tthc-qwen2.5-3b

Cần llama.cpp: convert_hf_to_gguf.py (+ requirements của nó) và binary llama-quantize.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print("$", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True, cwd=cwd)


def _find_quantize(llama_cpp: Path) -> Path:
    names = ["llama-quantize.exe", "llama-quantize"]
    for folder in [llama_cpp / "build" / "bin" / "Release", llama_cpp / "build" / "bin", llama_cpp]:
        for name in names:
            if (folder / name).exists():
                return folder / name
    found = shutil.which("llama-quantize")
    if found:
        return Path(found)
    raise SystemExit("Không tìm thấy llama-quantize — hãy build llama.cpp trước.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--llama-cpp", required=True)
    parser.add_argument("--name", required=True, help="tên mô hình Ollama")
    parser.add_argument("--quant", default="Q4_K_M")
    parser.add_argument("--num-ctx", type=int, default=8192)
    args = parser.parse_args()

    adapter = Path(args.adapter).resolve()
    work = adapter.parent / "export"
    merged = work / "merged-fp16"
    work.mkdir(parents=True, exist_ok=True)

    # 1. gộp adapter vào mô hình gốc (FP16)
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    base = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.float16)
    model = PeftModel.from_pretrained(base, str(adapter)).merge_and_unload()
    model.save_pretrained(merged, safe_serialization=True)
    AutoTokenizer.from_pretrained(args.base).save_pretrained(merged)
    del model, base

    # 2. HF -> GGUF FP16, rồi lượng tử hoá
    llama_cpp = Path(args.llama_cpp).resolve()
    f16 = work / f"{args.name}-f16.gguf"
    q = work / f"{args.name}-{args.quant.lower()}.gguf"
    _run([sys.executable, llama_cpp / "convert_hf_to_gguf.py", merged,
          "--outfile", f16, "--outtype", "f16"])
    _run([_find_quantize(llama_cpp), f16, q, args.quant])

    # 3. tạo mô hình Ollama (Ollama đọc chat template trong metadata GGUF)
    for gguf, tag in [(f16, f"{args.name}-f16"), (q, args.name)]:
        modelfile = work / f"Modelfile.{tag}"
        modelfile.write_text(f"FROM {gguf.name}\nPARAMETER num_ctx {args.num_ctx}\n",
                             encoding="utf-8")
        _run(["ollama", "create", tag, "-f", modelfile.name], cwd=work)

    for path in (f16, q):
        print(f"{path.name}: {path.stat().st_size / 1e9:.2f} GB")
    print(f"\nXong. So sánh: python finetune/benchmark_quant.py --models {args.name}-f16 {args.name}")
    print(f"Dùng trong app: đặt LLM_MODEL={args.name} trong .env")


if __name__ == "__main__":
    main()

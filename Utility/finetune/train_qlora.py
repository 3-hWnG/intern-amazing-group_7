"""QLoRA fine-tune mô hình 3–4B (hoặc 1.5B để thử) trên dữ liệu từ export_dataset.py.

    base (HF, BF16/FP16) -> nạp 4-bit NF4 -> LoRA trên attention + MLP -> adapter

Chỉ tính loss trên phần trả lời của trợ lý (prompt bị che), nên mô hình học
HÀNH VI: hiểu ý định, hỏi lại đúng lúc, bám bằng chứng, trích dẫn [S#].

Ghi THỜI GIAN fine-tune vào Utility/finetune/runs.jsonl — app đọc để so với ngày của
nguồn tra cứu (hiển thị ở /health và trong Evidence Pack).

    pip install -r Utility/finetune/requirements-finetune.txt
    python finetune/train_qlora.py --base Qwen/Qwen2.5-3B-Instruct --ollama-model tthc-qwen2.5-3b
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--data", default=str(HERE / "data" / "train.jsonl"))
    parser.add_argument("--out", default="")
    parser.add_argument("--ollama-model", default="",
                        help="tên mô hình Ollama sẽ tạo từ adapter này (ghi vào runs.jsonl)")
    parser.add_argument("--epochs", type=float, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--max-len", type=int, default=4096)
    parser.add_argument("--grad-accum", type=int, default=8)
    args = parser.parse_args()

    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                              DataCollatorForSeq2Seq, Trainer, TrainingArguments)

    raw = Path(args.data).read_text(encoding="utf-8")
    samples = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not samples:
        raise SystemExit("Không có mẫu nào — chạy finetune/export_dataset.py trước.")

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out or HERE / "output" / run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    def encode(sample: dict) -> dict:
        msgs = sample["messages"]
        prompt = tok.apply_chat_template(msgs[:-1], tokenize=False, add_generation_prompt=True)
        full = tok.apply_chat_template(msgs, tokenize=False)
        prompt_ids = tok(prompt, add_special_tokens=False)["input_ids"]
        ids = tok(full, add_special_tokens=False)["input_ids"][:args.max_len]
        n_prompt = min(len(prompt_ids), len(ids))
        return {"input_ids": ids, "attention_mask": [1] * len(ids),
                "labels": [-100] * n_prompt + ids[n_prompt:]}

    encoded = [e for e in map(encode, samples) if any(x != -100 for x in e["labels"])]
    print(f"{len(encoded)}/{len(samples)} mẫu dùng được (còn phần trả lời sau khi cắt {args.max_len} token)")

    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    model = AutoModelForCausalLM.from_pretrained(
        args.base, device_map="auto",
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if bf16 else torch.float16))
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(
        r=args.rank, lora_alpha=args.rank * 2, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    model.print_trainable_parameters()

    trainer = Trainer(
        model=model,
        train_dataset=encoded,
        data_collator=DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100),
        args=TrainingArguments(
            output_dir=str(out_dir), per_device_train_batch_size=1,
            gradient_accumulation_steps=args.grad_accum, num_train_epochs=args.epochs,
            learning_rate=args.lr, lr_scheduler_type="cosine", warmup_ratio=0.05,
            logging_steps=5, save_strategy="no", bf16=bf16, fp16=not bf16 and torch.cuda.is_available(),
            gradient_checkpointing=True, optim="paged_adamw_8bit", report_to="none"),
    )

    started_at, t0 = _now(), time.time()
    result = trainer.train()
    finished_at, duration = _now(), round(time.time() - t0, 1)

    adapter_dir = out_dir / "adapter"
    model.save_pretrained(adapter_dir)
    tok.save_pretrained(adapter_dir)

    record = {
        "run_id": run_id, "started_at": started_at, "finished_at": finished_at,
        "duration_seconds": duration, "base_model": args.base,
        "data_path": str(args.data), "data_sha256": hashlib.sha256(raw.encode()).hexdigest()[:16],
        "n_samples": len(encoded), "epochs": args.epochs, "lr": args.lr, "lora_rank": args.rank,
        "train_loss": round(float(result.training_loss), 4), "adapter_dir": str(adapter_dir),
        "ollama_model": args.ollama_model,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }
    with open(HERE / "runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print("Tiếp theo: python finetune/merge_and_export.py --adapter", adapter_dir)


if __name__ == "__main__":
    main()

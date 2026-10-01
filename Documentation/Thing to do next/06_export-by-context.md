# 06 — Export conversations by context

The requirement: *"Xuất ra cuộc trò chuyện theo từng ngữ cảnh, đo đếm benchmark đo usage
hardware"* — export conversations **per context** so they can be benchmarked.

## What exists

`Backend/core/eval_export.py` exports one conversation, or all conversations of one
user, as a `.txt` file with an "LLM judge" prompt on top. V10.6 lets an admin export
any user's conversations (before, only their own).

## Why it is not "by context" yet

1. **The context behind each answer is missing.** The export holds the text of the
   messages, but not *how* each answer was produced: which system, which keyword
   search, which MCQ options were shown and picked, which procedure was chosen,
   verifier result, timings. V10.6 now saves exactly this in `turn_traces`, but the
   export does not include it.
2. **It cannot be filtered by context.** You can only export per conversation or
   per user. A benchmark needs slices like "all answers about procedure X",
   "all System 2 answers this week", "all `user_rejected` cases".
3. **It is text only.** A `.txt` file is fine for a human or an LLM judge, but a
   benchmark script needs a machine-readable format to count and average.
4. **No hardware/usage numbers.** Nothing records CPU/RAM/VRAM or tokens per turn,
   which the requirement asks for.

## Suggested fix

- New export format **JSONL**, one line per assistant answer:
  `{conversation_id, system, question, answer, kind, verdict, procedure_id,
  mcq_path, timings, trace, feedback, created_at}` (join `messages`,
  `turn_traces`, `evidence`, `feedback`).
- Filters: date range, system, procedure, outcome, user.
- Hardware: record per-turn `total_ms`, model, tokens in/out (Ollama returns
  `eval_count`/`prompt_eval_count`), and a periodic RAM/VRAM sample during the
  benchmark run (see [12](12_benchmark-and-tests.md)).
- Keep the `.txt` export for LLM-judge use.

## Privacy (later)

Admins can export any user's chats. Before real users: anonymize emails in exports,
log who exported what, and state this in the terms of use.

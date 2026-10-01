# 12 — Full benchmark & reproducible tests

**Status:** the full benchmark will be done extensively later. This file records
what exists and what the benchmark must cover.

## About the "100% pass" in the V10.6 report

The V10.6 report lists two test scripts (`scratch/verify_all_fixes.py`,
`scratch/test_new_features.py`) with all tests passing. V10.6 also adds `scratch/` to
`.gitignore`, so **these scripts are not in the repository** and nobody else can
rerun them. Treat those results as the author's local check, not as evidence.

## What the full benchmark must cover

1. **Correctness of System 2:** a labelled set of questions (formal, informal,
   teencode, misspelled) → expected procedure. Metrics: top-1 / top-3 hit rate,
   MCQ rounds needed, `not_found` rate.
2. **System 1 (web search):** answer quality with an LLM judge and human spot checks;
   verifier pass/warn/fail rates.
3. **Performance:** latency per turn (p50/p95), queue wait, tokens/s, RAM/VRAM,
   with 1 / 2 / 4 concurrent users (feeds [02](02_multi-user-sessions.md)).
4. **Regression tests:** import/export round trip (see [08](08_fake-version-history.md)),
   MCQ memory validation, admin guards, user creation.

## Rules

- All test and benchmark scripts live **in the repo** (e.g. `Evaluation/`), not in
  ignored folders.
- Every result in a report states the commit, machine, model and dataset used.

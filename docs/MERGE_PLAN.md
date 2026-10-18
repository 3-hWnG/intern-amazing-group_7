# Merge plan — unifying the two evaluation suites

**Goal:** merge the two evaluation tools built independently by the team into one evaluation suite for the current system. Fix the parts that are wrong, re-run on a real machine, and rebuild the conclusions and paper justifications for the report and presentation.

**Status:** plan only. Nothing in this document has been executed yet. Decisions marked **[DECIDE]** must be chosen before starting (see §6).

**Written:** 2026-10-14. All paths are **relative to the repository root** of the merge branch, or given as `g7/draft:<path>` for files on the draft branch.

---

## 0. Sources and setup (do this first on any machine)

| What | Where | Pinned commit |
|---|---|---|
| **Merge suite** (current system, System 3 + System 4) | https://github.com/3-hWnG/intern-amazing-group_7/tree/merge_sys_3_4 | `e38369d` ("handle leader feedbacks") |
| **Draft suite** (older system code + research folders) | https://github.com/3-hWnG/intern-amazing-group_7/tree/draft | `c829392` ("hoan thien bo evaluation 4 tang …") |

The draft branch keeps the app under `Code/` and its research material at the top level: `02_related_work/`, `05_methodology/`, `06_experiment_results/`, `07_paper_draft/`. The merge branch is the app itself at the repo root.

```bash
# from the repo root of your working branch (one that contains e38369d)
git remote add g7 https://github.com/3-hWnG/intern-amazing-group_7.git   # skip if a remote for this repo already exists
git fetch g7 merge_sys_3_4 draft
git log -1 --format=%h g7/merge_sys_3_4   # expect e38369d (or newer: re-check §2 if newer)
git log -1 --format=%h g7/draft           # expect c829392 (or newer: re-check §2 if newer)
git checkout -b eval-merge                 # do the work on a new branch
git worktree add ../g7-draft g7/draft      # read-only reference copy of the draft, next to the repo
```

**Copying files from the draft:** use Git Bash, e.g. `git show g7/draft:Code/eval/rank_metrics.py > eval/rank_metrics.py`. Don't use PowerShell 5.1 redirection, because it changes the file encoding. Don't use `git checkout g7/draft -- …`, because it would put the file under `Code/`.

**How to run the eval scripts** (the same convention in both branches):
```bash
# Git Bash; in PowerShell set $env:VAR = '...' first
PYTHONIOENCODING=utf-8 S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 python run_server.py eval/<script>.py [args]
```
Run with `S3_USE_LLM=0` for retrieval and behaviour numbers (CPU only). LLM-based steps (RAGAS, latency with LLM) need Ollama with the models listed in `docs/SETUP.md`.

---

## 1. What each suite is

About 90% of `eval/` is the **same in both branches**: `cases_*.jsonl/json`, `run.py`, `run_pseudo.py`, `perturb.py`, `P*_REPORT.md`, `H*_ASSUMPTIONS.md`, `docs/EVAL.md`. Each teammate added roughly 10 files on top, with a different approach.

| | Merge suite (`merge_sys_3_4`) | Draft suite (`draft`) |
|---|---|---|
| Approach | Unify and label the *existing* hand/agent-written sets; add template questions restricted to procedures the system is designed to answer | *Generate* a new multi-domain golden set from the database (domain × 10 question types) |
| Golden set | `eval/build_golden.py` → `eval/golden/thu-tuc.jsonl` (1,323 cases, each tagged `dev` / `holdout-used` / `blind`); `eval/build_template_set.py` → `template_thu-tuc.jsonl` (430 cases) | `Code/eval/golden/build_golden_multidomain.py` → `cases_golden_dev.jsonl` (1,615) + `cases_golden_holdout.jsonl` (553), 122 domains |
| Scorer | `eval/run_golden.py` (behaviour, top-1, top-3, correct fields, multi-procedure completeness, clarify, refusal, list-by-domain precision) | `Code/eval/run_pseudo_rank.py` + `Code/eval/rank_metrics.py` (adds **MRR, nDCG@5**, with self-test); `run.py` patched with MRR/nDCG columns |
| RAGAS | `eval/run_ragas_lite.py`: its own implementation of the 4 metrics, Ollama qwen3:4b grader, 30 cases, **grader checked with planted errors (negative controls)** | `Code/eval/golden/ragas_runner.py`: real `ragas` library, qwen2.5:7b + bge-m3 grader, 394 cases (11 h 40 min). Grader **not** checked |
| Safety | — | `Code/eval/safety/test_pii_injection.py`: D1 ID/phone masking, D2 prompt injection (unit + end-to-end). **Found and fixed a real masking bug** |
| Extra sets | — | `Code/eval/cases_real_log_v1.json` (28 hand-written cases / 29 turns, "real user" style, rare domains, sibling procedures) + `REAL_LOG_v1.md` |
| Latency | `eval/measure_latency.py` (p50/p95 per question type, LLM on/off), `measure_ollama_reload.py`, `measure_parallel.py` | — (its methodology table quotes p95 3.4 s from older measurements) |
| Data check | `eval/sample_dataset_check.py` (50-record sheet to check by hand against dichvucong.gov.vn; still unfilled) | — |
| One-command report | `eval/report.py` → `eval/results/report.md` | — |
| Criteria doc | `eval/CRITERIA.md` | `05_methodology/bo_evaluation_hoan_thien_v2.md` (4-tier framework A–D, thresholds, blind-set discipline, **map of 33 papers → criteria**), `02_related_work/paper_summaries/paper_01..33.md` |
| System code under test | **Current** | **Older**: no `retrieval/variants.py`, `server/fee_query.py`, or multi-turn retrieval sync (`b7a7b9f`). Its `server/policy/policy.py` *does* have the masking fix |

The draft's `server/policy/policy.py` differs from the merge branch's **only** in the masking block (`_PII_SEP`, `_PII_RUN`, `_PII_CURRENCY_AFTER`, new `mask_pii`). The merge branch has a newer `_CGEN` word list that must be kept. **Port the block, not the file.**

---

## 2. Findings (verified 2026-10-14)

### 2.1 Where the two suites agree (safe to present)

1. **HOLDOUT-4 numbers match across two separate scorers and two code versions:**

   | | Correct behaviour | Top-1 | Top-3 | Clarify correct | Refusal correct |
   |---|---|---|---|---|---|
   | Draft (`run_pseudo_rank.py`, old code) | 89/106 (84.0%) | 60/77 (77.9%) | 64/77 (83.1%) | 9/16 | 13/13 |
   | Merge (`run_golden.py --by source`, current code) | 90/106 (85%) | 60/77 (78%) | 67/77 (87%) | 10/16 | 13/13 |

   The draft also reports MRR 0.810 and nDCG@5 0.785 (old code; re-measure in Phase A).
2. **Clarifying questions are the weakest behaviour:** 47% (40/86) on all merge blind sets, 56% on HOLDOUT-4, 0/2 on the draft's hand-written set. Refusals are strong: 90% (52/58) on blind sets.
3. **The main retrieval error is picking the wrong procedure, not ranking the right one second.** The draft's hand-written set shows sibling procedures being confused (different "mai táng phí" types; "chấm dứt" vs "chuyển" for alternative care). The wrong answer quotes the *real* numbers of the wrong procedure, so this is a retrieval error, not invention.
4. **Tuned sets score much higher than blind sets:** merge dev 98% vs blind 78% correct behaviour. Both suites say only blind numbers should be presented as headline numbers.
5. **Template questions are easier than real user questions.** Both say this explicitly. Paper 12 (STARD) supports it.
6. **Neither suite's faithfulness number can be cited** (see 2.4).

### 2.2 Merge-only findings
- "A khác gì so với B" comparisons failed 0/20 and now pass 16/20 after the `split_compare` fix (`server/tests/compare_cue_test.py`).
- Listing by domain: 32/40 questions return a list, but only 12% of list items are in the requested domain. Fee queries now have a real SQL path (`server/fee_query.py`).
- Correct fields: "explain" 45% and "address" 50% on the template set (not yet investigated).
- Latency: normal questions p50 60–85 ms. Questions that go through LLM text generation: p50 3.2 s, p95 6.3 s (GTX 1660 SUPER 6 GB, qwen3:4b). Switching Ollama models costs about 7 s.

### 2.3 Draft-only findings
- **Masking bug:** `mask_pii` caught 0/3 ID/phone numbers written with spaces, dashes or dots (`034-203-004455`, `0901 234 567`). After the patch it catches 3/3, with no false positives on 5 control sentences. Injection: 11/11 blocked, 0/6 false blocks, 17/17 end to end. **The merge branch still has this bug.**
- Hand-written set (`cases_real_log_v1.json`): correct behaviour 22/29 (75.9%), top-1 16/23 (69.6%), MRR 0.751. It is lower than HOLDOUT-4 by design (rare domains, sibling procedures).
- Domain coverage bug in the draft's own generator (`state == "ACTIVE"` dropped Hộ tịch, Cư trú, Chứng thực). Fixed by the draft author.

### 2.4 Where the suites disagree: answer quality (RAGAS)

| Metric | Draft (394 cases, 7B grader) | Merge (30 cases, 4B grader) | Why they differ |
|---|---|---|---|
| Faithfulness | **0.40** (only 309/394 scored) | **0.90** | Draft context is a *rebuilt summary* (name + fee + time + 6 checklist items + agency), not what the answerer saw. Anything about steps, address or legal basis looks "unsupported", so the score is pushed down. Merge context is the field chunks the answerer used, but its 4B grader missed 70% of planted made-up claims (lowered the score in only 9/30), so 0.90 is an upper bound. |
| Answer relevancy | 0.38 | 0.43 | Both low. Merge showed its grader scored 17/30 *good* answers as 0. Rule-based focus checks (`run_concise.py`) give 96–99%. Unresolved. |
| Context precision | 0.81 | 0.69 | Different definitions: candidate-procedure summaries vs field chunks |
| Context recall | 0.68 | 0.98 | Draft reference is a placeholder for 77% of cases. Merge reference comes from the same database fields the system read, so it is near-automatic. Neither measures much. |

**Conclusion to present:** answer quality as judged by an LLM is *not yet measured reliably*. Phase C is designed to settle it.

### 2.5 Problems in the draft golden set (audit script in Appendix A, re-runnable)

| # | Problem | Dev | Holdout | Effect |
|---|---|---|---|---|
| 1 | **Holdout isn't blind**: split by case-id hash, so the same procedure appears in both splits under other question types | — | 309/311 procedures (99%) also in dev | "Blind" numbers are actually seen data |
| 2 | **Expected answer is a placeholder** ("Giấy tờ theo checklist của thủ tục X") | 1,241/1,587 (78%) | 411/536 (77%) | Context recall, answer correctness and relevancy have nothing real to compare against |
| 3 | **Slang question type never makes slang**: `norm()` strips diacritics *before* `replace("đăng ký","dk")`, so the replace never fires | 0/310 contain "dk" | 0/103 | Type 1 ≈ type 8 (no diacritics); the robustness claim is inflated |
| 4 | **Injection questions labelled `answer`** (type 10), but the system refuses them, and the draft's own safety test says it must | 306 | 107 | The build step quietly moves them to `*_behavior_mismatch.json`; correct behaviour on the golden set is never reported |
| 5 | **"Miễn lệ phí" labels that are wrong or conditional**: `amount_value == 0` mapped to "free" even when the text says the provincial council sets the fee, or the exemption is only for certain groups | 69/320 | 25/114 | Wrong expected facts in fee questions (type 3) and false-premise questions (type 9); the merge branch's `fee_query` avoids exactly this |
| 6 | Expected procedure outside the system's 537-procedure answer scope (province-specific or ministry-level, e.g. Hải quan, Thuế) | 366/1,587 (23%) | 127/536 (24%) | Ministry-level ones should expect a refusal. Province-specific: the system answered 83 of them, so **decide the scope rule** (label or system is wrong) |
| 7 | Duplicate IDs (60-character truncated names hash to the same ID) | 42 | 18 | Double counting |
| 8 | Truncated 60-character name matches more than one procedure | 149 | 54 | Ambiguous label: correct behaviour may be clarify |
| 9 | Fee procedures with more than one fee row; forbidden list drawn from random round sums | 167/187 | 59/66 | Can flag a valid fee as "made up" (the draft author found 1 such case). Also 3 suspiciously tiny fees ('200đ', '25đ', '700đ'), probably "25.000" parsed as 25 (the known `amount_value` parsing bug) |
| 10 | "0% made-up numbers" = none of 3 random planted sums (e.g. 200.000đ) appear | 0/1,192 | 0/394 | Weak evidence; `run.py`'s check against source numbers is the real test |
| 11 | No case marked as reviewed by a human (`needs_human_review: true` everywhere) | all | all | The draft's mentor summary claim "chuyên gia rà" (expert-reviewed) is **not true yet** |

### 2.6 Problems on the merge side
- `eval/build_golden.py` turns multi-turn blind sets into histories with **empty assistant turns**, while `run_pseudo.py` feeds back the real answers. `retrieval/rank.py` (`_ref_options`) reads the previous assistant text for references like "cái thứ hai", so `run_golden.py` can score those follow-ups differently. Fix in Phase A.
- The golden set has no new questions; most blind sets were written by an agent from assumptions (both suites admit this).
- The template set excludes ambiguous procedure families (`families.n_members = 1`), which is exactly where the system fails.
- RAGAS-lite: n = 30, 4B grader, metric definitions differ from the paper (documented at the top of the script).
- No MRR/nDCG, no confidence intervals, no safety suite, no hand-written "real-style" set.
- `system4/tests/test_nv4.py` hard-codes 1,350 procedures and fails on a re-scraped database (1,509). Unrelated to eval, but note it.

---

## 3. If a report is needed *before* this plan is done

**Use the merge suite** (`eval/report.py`, `docs/PLAN_TUAN_TOI.md` tables A–D, `eval/CRITERIA.md`):
- It runs on the current code.
- Its labels follow the system's real scope.
- It already says which of its numbers can't be cited.

Add, with clear labels:
- HOLDOUT-4 MRR / nDCG@5. The pure-maths scorer runs in minutes; ideally re-run it on current code (Phase A step 5). If not re-run, label it "measured on earlier code (draft branch)".
- The masking bug as a **known issue on the shipped branch**, fixed on the draft branch.
- The answer-quality line from §2.4: "not yet reliably measured".

**Do not present:**
- the draft's RAGAS numbers (0.40 / 0.38 / 0.81 / 0.68);
- the draft's "0% made-up numbers on 394 cases" as proof of no invention;
- "blind holdout" or "expert-reviewed" for the generated golden set;
- the draft's thresholds as literature standards (see §5.3).

---

## 4. Target design (after the merge)

### 4.1 One golden format
Keep the merge format and add optional fields from the draft schema:

```jsonc
{
  "id": "...",                    // unique; for generated cases hash(domain|archetype|proc_id|question)
  "domain": "thu-tuc",            // golden-set domain (file name); the procedure's own field goes below
  "proc_domain": "Hộ tịch",       // optional, for per-domain slicing
  "type": "...",                  // merge 'type' / draft 'archetype' (keep both if useful: "archetype": 3)
  "turns": [{"role": "user|assistant", "text": "..."}],   // multi-turn: real assistant text, or replayed live
  "question": "...",
  "expected": {
    "behavior": "answer|clarify|apologize",
    "tasks": [{"proc_ids": ["..."], "fields": ["fees"]}],
    "facts": {"fee": ["25.000 đồng", "50.000 đồng"]},     // optional; every valid value
    "forbidden_facts": ["200.000đ"],                       // optional; never contains a valid value
    "reference": "real text from field_chunks"             // optional; for context recall / correctness
  },
  "source": "cases_h4.json | template | multidomain-gen | real_log_v1 | ...",
  "status": "dev | holdout-used | blind | synthetic",
  "needs_human_review": true,
  "reviewed_by": null
}
```

### 4.2 Four-tier report (the draft's framework, the merge branch's tooling)

| Tier | Metrics | Script |
|---|---|---|
| A Retrieval | top-1, top-3, **MRR, nDCG@5**, each with a **95% Wilson CI** | `run_golden.py` (+ `rank_metrics.py`) |
| B Answer quality | made-up numbers / "không công bố" / citations (`run.py`), focus (`run_concise.py`), composer score (`score_composer.py`), **RAGAS (checked grader)** | `run.py`, `run_ragas_*.py` |
| C Behaviour | correct behaviour, clarify P/R, refusal, multi-turn context, robustness (`perturb.py`) | `run_golden.py`, `run_ctx.py`, `perturb.py` |
| D Safety & system | D1 masking recall + false positives, D2 injection TPR/FPR + end to end, latency p50/p95 | `eval/safety/test_pii_injection.py`, `measure_latency.py` |

`eval/report.py` prints all four tiers except RAGAS, which is too slow; it links the latest RAGAS result file instead.

---

## 5. Execution plan

### Phase A — quick wins (no GPU; about 1–2 h of work; runs take minutes)

| Step | Task | Done when |
|---|---|---|
| A1 | Copy `g7/draft:Code/eval/rank_metrics.py` → `eval/rank_metrics.py`. Run `python eval/rank_metrics.py` (self-test). | prints `rank_metrics selftest OK` |
| A2 | Apply the draft's MRR/nDCG patch to `eval/run.py` (54-line diff: `git diff --no-index <(git show g7/draft:Code/eval/run.py) eval/run.py`). Add MRR/nDCG@5 columns to `eval/run_golden.py` using `rank_metrics.best_match` **per expected task**. Use the same candidate list for top-1 and RR. The draft's `run_pseudo_rank.py` uses `tasks[0].proc_id` for top-1 but the flattened candidates for RR, so MRR and top-1 there are not computed on the same list. | `run_golden.py` table has MRR / nDCG@5 columns |
| A3 | Add 95% Wilson intervals to every percentage in `run_golden.py` (and optionally `run.py`): `p̂ ± …` using `(p + z²/2n ± z√(p(1−p)/n + z²/4n²)) / (1 + z²/n)`, z = 1.96. | e.g. "60/77 (78%, 67–86%)" |
| A4 | Fix the multi-turn replay. Either `run_golden.py` replays turns live (`hist.append({"role":"assistant","text": out["answer_text"]})`, like `run_pseudo.py`), or `build_golden.py` stores only user turns plus a `replay: true` flag. Re-check HOLDOUT-4 and pseudo_real 2 against `docs/EVAL.md` (the known mismatch: pseudo_real 2 top-1 22/28 now vs 19/28 in EVAL.md). | Multi-turn results match `run_pseudo.py` on the same set |
| A5 | Copy `g7/draft:Code/eval/run_pseudo_rank.py` (optional, now redundant with A2) and re-run HOLDOUT-4 on **current code**: `python run_server.py eval/run_golden.py thu-tuc --by source`. | New HOLDOUT-4 MRR/nDCG on current code recorded in `docs/PLAN_TUAN_TOI.md` |
| A6 | Copy `g7/draft:Code/eval/safety/` → `eval/safety/` (README + `test_pii_injection.py`). Run unit mode, then `--e2e`. | Before the policy patch, expect D1 separator cases 0/3 (reproduces the bug) |
| A7 | **[DECIDE D4]** Port the masking block into `server/policy/policy.py` as **its own commit**: `_PII_SEP`, `_PII_RUN`, `_PII_CURRENCY_AFTER` and the new `mask_pii` body from `g7/draft:Code/server/policy/policy.py`. Keep the merge branch's `_CGEN`. Callers: `server/orchestrator.py`, `server/main.py`, `server/user_memory.py` (System 4 has none). Run all gates in `docs/CONTRIBUTING.md` + `eval/run_all.py --quick` (expect 27/33, same 6 known misses) + the safety suite. Add one false-positive case without a currency unit (e.g. "quyết định số 123456789") to the docs as an accepted risk; don't hide it. | Safety: D1 9/9 + 3/3, FP 0/5, D2 11/11, 0/6, e2e 17/17; no regression in gates |
| A8 | Copy `g7/draft:Code/eval/cases_real_log_v1.json` + `REAL_LOG_v1.md`. Add it to `build_golden.py` via `from_flat("cases_real_log_v1.json", "holdout-used", "real-log")`, because its failures have already been read (real-11, real-13). Re-check every `expect_ids` exists in `data/snapshot/procedures.jsonl`. | `thu-tuc.jsonl` includes 29 real-log turns, status `holdout-used` |
| A9 | Re-run `eval/report.py` and refresh tables A–D in `docs/PLAN_TUAN_TOI.md`. | This alone gives a report-ready version of tiers A, C and D |

### Phase B — unified golden set (about half a day; no GPU except the final run)

Depends on **[DECIDE D1]**. Default plan (fix and regenerate):

| Step | Task |
|---|---|
| B1 | Move `g7/draft:Code/eval/golden/build_golden_multidomain.py` → `eval/build_multidomain.py`. Read procedures **from the DB** (`system3.data.api.connect()`, like `build_template_set.py`), not from the snapshot, so labels follow what the system serves. |
| B2 | **Scope labels**: use the same rule as the system (`policy._vertical`, `province IS NULL`, `agency_levels LIKE '%Xã/Phường%'`, see `server/fee_query.py::_scope`). Ministry-level → `apologize`. **[DECIDE D5]** province-specific → `answer` or `apologize`. |
| B3 | **Procedure-level split**: hash `proc_id` (not case id) into dev/holdout, so a procedure's question types all land in the same split. Status `synthetic-dev` / `synthetic-holdout` (never `blind`, since generated questions aren't real user questions). |
| B4 | **Real references**: `expected.reference` = text of the relevant `field_chunks` (status `present`) for the asked field. Same source as `run_ragas_lite.py::chunks_of`. |
| B5 | **Fee facts from `fees_clean`** (and the logic in `server/fee_query.py`): "free" only when the source says free with no conditions. Conditional or council-set fees get no "free" fact. Multi-fee procedures list *every* valid amount in `facts.fee`. `forbidden_facts` drawn from amounts **not** equal to any valid amount. Drop cases where the `amount_value` vs `amount_text` mismatch is unresolved. |
| B6 | **Question types**: fix slang (apply the abbreviation map *before* stripping diacritics, and use a real map: đăng ký→dk, giấy→gi, không→ko, được→dc, thủ tục→tt…); keep no-diacritics; type 9 false premise only on unconditional "free"; **type 10 injection → expected `apologize`** (matches `pre_check` and the safety suite); type 6 ambiguity from `families` (`n_members ≥ 2`) → `clarify`. |
| B7 | **Names**: use full procedure names, not 60-char truncation. If a question's name matches more than one procedure, expect `clarify` or accept all matches. Unique IDs: `hash(archetype|proc_id|question)`. |
| B8 | Merge the draft's question types into `build_template_set.py`'s `TOPICS`, or keep two generators writing the same format (`source` tells them apart). Output `eval/golden/multidomain_thu-tuc.jsonl`. |
| B9 | **Human review sample**: draw 50 generated cases stratified by type, export a review sheet (same pattern as `sample_dataset_check.py`), fill `reviewed_by`. Report the label error rate. Without this, the set may not be called "expert-reviewed". |
| B10 | Run `run_golden.py multidomain_thu-tuc --by type` and `--by status`. Re-run the Appendix A audit on the new files: every row of the §2.5 table should be 0 (or explained). |

### Phase C — RAGAS re-run (your GPU machine; long runs)

Depends on **[DECIDE D2]**. Default plan (both RAGAS implementations, plus a human check):

| Step | Task |
|---|---|
| C1 | **One shared dataset builder** (`eval/ragas_build.py`): for each `behavior=answer` case, run `answer_adapter`. Record question, answer, **contexts = `field_chunks` of the procedures/fields the system actually used** (as `run_ragas_lite.py` does), and **reference = `expected.reference`**. Keep the draft's split: cases where the system's behaviour ≠ expected go to a mismatch file *and* are counted in tier-C behaviour accuracy. Sample about 150 cases stratified by procedure domain, with at least 8 per core domain (Hộ tịch, Cư trú, Chứng thực, Bảo trợ xã hội). |
| C2 | **Grader checks (run on both graders)**, from the merge branch: (a) append a planted made-up claim, so faithfulness must drop; (b) pair an answer with another case's question, so relevancy must drop. Report how often each control is caught. |
| C3 | **Human calibration**: you grade about 30 cases (faithful yes/no, relevant 0/1/2). Compute Cohen's κ against each grader. Paper 09 and Paper 17 report rater agreement, and Paper 31 validated against human choices. |
| C4 | **Run RAGAS-lite** (`run_ragas_lite.py` on the shared dataset). Add a `--judge-model` option; check whether `core.llm.chat_json` accepts a model name, and add one if not. Grader: **[DECIDE D6]**. |
| C5 | **Run real RAGAS** (`ragas_runner.py --score` on the shared dataset). Keep the draft's `RunConfig(max_workers=2, timeout=180)` and its "n scored / total, warn below 80%" printout. |
| C6 | Report: per metric, n scored, mean with CI, control catch rate, κ against human. **Only metrics whose controls pass and κ ≥ about 0.6 go into the report**; the rest are reported as "grader not reliable for this metric". |

**Time cost** (measured by the two authors): real RAGAS with qwen2.5:7b took about 64 s/case (394 cases = 11 h 40 min); RAGAS-lite with qwen3:4b took about 70 s/case (30 cases ≈ 35 min, GTX 1660 SUPER 6 GB). Both runs at 150 cases ≈ 5–6 h, so run overnight. Use `--limit 10` first to confirm nothing scores as None.

### Phase D — rebuild conclusions and documents

| Step | Task |
|---|---|
| D1 | Extend `eval/report.py` to print tiers A–D (§4.2) in one run; link the latest RAGAS JSON. |
| D2 | Merge `eval/CRITERIA.md` with the draft's `05_methodology/bo_evaluation_hoan_thien_v2.md` into one document (Vietnamese, for the team): keep the 4-tier framework, the blind-set discipline (part 2.2) and the paper map (part 8, corrected per §5.3). Replace every number with the Phase A–C numbers. |
| D3 | Copy the paper material the report needs (`02_related_work/paper_summaries/`, `paper_list.md`) into `docs/research paper/`, or link the draft branch. Note the overlap with the merge branch's existing `docs/research paper/RESEARCH_PAPERS.md` (20 papers, different numbering). Use **one numbering** in the final report. |
| D4 | **[DECIDE D3]** Archive or drop the draft's old outputs. |
| D5 | Rewrite the "1-minute summary for the mentor" (the draft's part 9) using only claims allowed by §5.4. |

### Phase E — future work (not required for this merge)
- Golden set for "Trò chuyện chung" / System 4 Friendly mode: neither suite has one.
- **Indirect prompt injection through uploaded documents** (System 4 datasets). This is the threat Paper 06 describes and nobody tests it yet.
- Fill the 50-record data-accuracy sheet (`sample_dataset_check.py`, table E).
- A real user log (small pilot with real users); both suites' "real" sets are simulated.
- Fix `amount_value` parsing ("20.000" → 20) at the source (`data/build.py`); `fee_query` currently works around it.
- `system4/tests/test_nv4.py`: replace the hard-coded `1350` with a count read from the test DB.

---

## 5.3 Paper justifications for the presentation

Checked against the draft's `02_related_work/paper_summaries/`. Numbering follows the draft's `paper_list.md`.

**Use confidently:**

| Design choice | Paper | What the paper actually supports |
|---|---|---|
| Rule-based Strict engine + 0% made-up numbers checked by rules | **09** Hallucination-Free? (Magesh et al.) | Commercial legal RAG tools still produce false statements; defines **correctness × groundedness**; reports 95% CIs and Cohen's κ |
| Why invented legal facts matter | **32** Large Legal Fictions | General LLMs make up legal facts 58% (GPT-4) to 88% (Llama 2) of the time on direct questions |
| RAGAS's 4 metrics | **31** RAGAS (Es et al., EACL demo) | Defines faithfulness, answer relevance and context metrics; validated against human choices on WikiEval (50 pages, mostly ChatGPT-generated) and notes reproducibility issues → **justifies checking our own grader** (planted-error controls + human κ) |
| Atomic-fact checking | **17** FActScore | Split long answers into atomic facts; compares an automatic estimator against human annotators |
| Rule checks beside the LLM grader | **15** CRITIC | LLMs self-correct well when they have external tools; self-checking alone is unreliable |
| Evaluate retrieval separately (top-k) | **08** LegalBench-RAG | Retrieval-only benchmark, Precision@k / Recall@k |
| MRR; real questions harder than templates | **12** STARD | 1,543 real questions from non-experts; Recall@k and MRR@k |
| Reference numbers for Vietnamese legal RAG | **02** | Context Precision 0.792, Context Recall 0.847, MRR 0.783, citation accuracy 94.2%. A **reference point only**: different task and data |
| Masking ID/phone numbers; running on-premise | **05** Analyzing PII Leakage (Lukas et al., IEEE S&P 2023) | Automatic scrubbing is imperfect (cited NER recall ~97% for names); in their experiments scrubbing alone cut PII leakage to ~0% but left membership-inference risk (AUC 0.82), so masking is one layer, not a guarantee |
| Injection tests | **06** Indirect Prompt Injection (Greshake et al.) | Instructions hidden in *retrieved* content can take over LLM apps. Our D2 tests direct injection; **uploaded System 4 documents are the indirect case (future work)** |
| nDCG, dense+sparse embedding | **19** M3-Embedding, **04** | bge-m3, which the system uses; nDCG as a ranking metric |
| Significance testing when comparing versions | **20** | Reports improvements with p < 0.001 |
| Latency p50/p95 | **26** vLLM | Serving-latency framing (tangential) |

**Correct before presenting (the draft overstates these):**
- **Paper 18 (CRAG):** its "Ambiguous" state means retrieval confidence is in between, so it *combines internal and web knowledge*. It does **not** ask the user. Cite it only as an analogy: "three actions based on confidence beat two (their ablation)". It is also arXiv-only (not peer-reviewed), as the draft's own summary notes.
- **Paper 25 (RouteLLM):** shows router quality tracks how similar the training data is to the benchmark. It is *not* a paper about test-set leakage. Support blind-set discipline with Paper 09 (which names test-data leakage as a threat to validity in its own limitations) and Paper 12 instead.
- **Thresholds** (faithfulness ≥ 95%, relevancy ≥ 90%, MRR ≥ 0.85, behaviour ≥ 88%…): apart from Paper 02's 0.847 recall, these are **team targets**, not standards from the literature. Present them as targets.
- **Paper 23** is a fine-tuning recipe paper; it is weak support for multiple seeds or CIs. Prefer Paper 09 (95% CIs) for "report confidence intervals".

### 5.4 Claims allowed after each phase

| Claim | Allowed after |
|---|---|
| HOLDOUT-4 top-1 / behaviour / clarify (current code) | now (merge numbers) |
| MRR / nDCG on current code; CIs on every number | Phase A |
| "Masking bug found by our safety suite and fixed; regression test in place" | Phase A (A6–A7) |
| "Multi-domain test set covering N domains, procedure-level dev/holdout split, label error rate X% on a 50-case human review" | Phase B |
| Any RAGAS number | Phase C, only metrics that pass controls and human κ |
| "Expert-reviewed" | Only for the cases actually reviewed (B9) |
| "Blind" | Only HOLDOUT-3/4, h5, h6, pseudo_real 1–3, team set (per `docs/EVAL.md`); never generated sets or the read real-log set |

---

## 6. Decisions to make before starting **[DECIDE]**

Fill in the "Choice" column. The recommended option is listed first.

| ID | Question | Options (trade-offs) | Choice |
|---|---|---|---|
| **D1** | What to do with the draft's multi-domain golden set? | **(a) Fix and regenerate (rec.)**: keeps 100+-domain breadth with correct labels; about half a day; numbers change vs the draft. · (b) Keep as-is, tagged `synthetic-unverified`: zero work, but the §2.5 errors stay in the data. · (c) Drop the generator, only add its question types to the template set: smallest, but loses the many-domain coverage where the draft found real errors. | |
| **D2** | Which RAGAS setup to re-run? | **(a) Both implementations + human check (rec.)**: strongest numbers; about 5–6 h at 150 cases. · (b) Real `ragas` only (fixed contexts/references + controls): easy to cite as "standard RAGAS", but its relevancy method looked unreliable on long Vietnamese answers. · (c) RAGAS-lite only, about 100–150 cases, 7B grader: half the time, already has controls; custom definitions must be explained. · (d) No RAGAS, rule-based quality only: no GPU hours, but the committee may ask why, since Paper 31 is cited. | |
| **D3** | The draft's old outputs (`cases_golden_*.jsonl`, `ragas_dataset_*.json` ≈ 22 MB, `.bak_before_state_fix`, `policy.py.bak_pre_pii_patch`, its RAGAS numbers)? | **(a) Archive to `eval/archive/draft-2026-10-13/` with a README saying why they were replaced (rec.)**: good for "before vs after" slides; +22 MB. · (b) Keep only a summary table in the docs; history stays on the GitHub draft branch. · (c) Drop entirely. In all cases, delete `.bak` files (git keeps history). | |
| **D4** | Port the masking fix into `server/policy/policy.py`? | **(a) Yes, separate commit + all gates (rec.)**: closes a real privacy bug; small risk of masking a 9–12-digit number that has no currency unit. · (b) Eval only, report as a known issue: code stays unchanged, but the bug stays in the shipped system. | |
| **D5** | Province-specific procedures (`province` set): expected behaviour? | (a) `answer`, if the system is meant to serve them (it currently answers 83/83 in the draft RAGAS set). · (b) `apologize` (or clarify the province), if the scope is commune-level and province-independent only (as `fee_query`'s 537-procedure scope assumes). Check the intended scope with the team lead; if (b), it is a system bug as well. | |
| **D6** | RAGAS grader model | **(a) qwen2.5:7b (rec.)**: the draft showed it runs on a 6–8 GB GPU; probably stricter than 4B. Scoring runs after building the dataset, so there's no model-swap cost. · (b) qwen3:4b (same as the system): faster, but the merge branch showed it is lenient (missed 70% of planted claims). · (c) A stronger API model on a sample: most reliable, but sends citizen-style data off-machine (conflicts with the Paper 05 on-premise argument); use only on synthetic cases. | |
| **D7** | Human review effort (B9 + C3) | **(a) 50 golden cases + 30 RAGAS cases (rec.)**: about 2–3 h of human time. · (b) 30 + 30. · (c) Skip: then no "reviewed" or "calibrated grader" claims. | |

---

## 7. Checklist for the executing session
1. Run §0. Check whether `g7/draft` and `g7/merge_sys_3_4` moved past the pinned commits; if so, diff the `eval/` folders again before porting.
2. Read §6 and get decisions D1–D7 from the user (or use the recommended defaults if told to).
3. Phase A → commit in small steps (eval changes; the policy fix as its own commit) → run the gates.
4. Phase B → run the Appendix A audit on the new set → all §2.5 rows resolved.
5. Hand the Phase C commands to the user to run on the GPU machine; wait for the result files.
6. Phase D: rebuild the documents using only claims allowed by §5.4.
7. Don't push or open PRs without the user's go-ahead.

---

## Appendix A — audit script for a golden set

Re-runs the §2.5 checks. Save it outside the repo (e.g. a temp folder) and run it from the merge repo root through `run_server.py`, so `policy` imports work:

```bash
git worktree add ../g7-draft g7/draft     # if not done in §0
PYTHONIOENCODING=utf-8 S3_USE_LLM=0 python run_server.py /path/to/audit_golden.py \
    ../g7-draft/Code/eval/golden data/snapshot/procedures.jsonl server
```

```python
"""Audit the draft-style golden set (cases_golden_{dev,holdout}.jsonl) against the snapshot.
usage: python run_server.py audit_golden.py <golden dir> <snapshot procedures.jsonl> <server dir>"""
import collections, json, re, sys
from pathlib import Path

gdir, snap, server = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, server)
from policy.policy import _vertical  # same scope rule as the running system

procs = {json.loads(l)["proc_id"]: json.loads(l) for l in open(snap, encoding="utf-8")}
in_scope = {k for k, p in procs.items()
            if "Xã/Phường" in (p.get("agency_levels") or "") and not p.get("province") and not _vertical(p.get("domain") or "")}
print("in-scope procedures:", len(in_scope), "of", len(procs))
pref = collections.defaultdict(set)
for k, p in procs.items():
    pref[(p.get("name") or "").strip()[:60]].add(k)
GENERIC = r"^(Giấy tờ theo checklist|Thủ tục: .*Hồ sơ theo checklist|Nơi nộp / cơ quan giải quyết|Bỏ qua phần chèn lệnh)"

split_procs = {}
for split in ("dev", "holdout"):
    rows = [json.loads(l) for l in open(gdir / f"cases_golden_{split}.jsonl", encoding="utf-8")]
    ans = [r for r in rows if r["expected_behavior"] == "answer"]
    split_procs[split] = {r["expected_procedure_id"] for r in rows if r["expected_procedure_id"]}
    out = [r for r in ans if r["expected_procedure_id"] and r["expected_procedure_id"] not in in_scope]
    ids = collections.Counter(r["id"] for r in rows)
    a1 = [r for r in rows if r["archetype"] == 1]
    fee = [r for r in rows if r["archetype"] == 3]
    free = [r for r in rows if r["expected_facts"].get("fee") == "Miễn lệ phí"]
    bad_free = 0
    for r in free:
        t = ((procs[r["expected_procedure_id"]].get("fees") or [{}])[0].get("amount_text") or "").strip().lower()
        if t and (not t.startswith(("miễn", "không thu", "0")) or "quyết định" in t or "cho người" in t or "đối với" in t):
            bad_free += 1
    print(f"\n== {split}: {len(rows)} rows; behaviours {dict(collections.Counter(r['expected_behavior'] for r in rows))}")
    print(f"  answer cases outside scope: {len(out)}/{len(ans)}  top domains {collections.Counter(procs[r['expected_procedure_id']]['domain'] for r in out).most_common(5)}")
    print(f"  placeholder ground_truth: {sum(bool(re.match(GENERIC, r['ground_truth'])) for r in ans)}/{len(ans)}")
    print(f"  duplicate ids: {sum(v - 1 for v in ids.values() if v > 1)}")
    print(f"  slang (type 1) containing 'dk': {sum(' dk ' in ' ' + r['question'] + ' ' for r in a1)}/{len(a1)}")
    print(f"  injection (type 10) labelled answer: {sum(1 for r in rows if r['archetype'] == 10 and r['expected_behavior'] == 'answer')}")
    print(f"  60-char name prefix shared by >1 procedure: {sum(1 for r in ans if r['expected_procedure_id'] and len(pref[(procs[r['expected_procedure_id']].get('name') or '').strip()[:60]]) > 1)}/{len(ans)}")
    print(f"  'Miễn lệ phí' labels contradicted/conditional in source: {bad_free}/{len(free)}")
    print(f"  fee cases on multi-fee procedures: {sum(len(procs[r['expected_procedure_id']].get('fees') or []) > 1 for r in fee)}/{len(fee)}; "
          f"tiny fees: {[r['expected_facts']['fee'] for r in fee if re.fullmatch(r'\d{1,3}đ', r['expected_facts'].get('fee', ''))]}")
h, d = split_procs["holdout"], split_procs["dev"]
print(f"\nholdout procedures also in dev: {len(h & d)}/{len(h)}")
```

For the **regenerated** set (Phase B, merge format), adapt the field names: `expected.behavior`, `expected.tasks[0].proc_ids[0]`, `type`, `expected.reference`. The target is 0 for every row except the documented scope decision (D5).

## Appendix B — numbers recorded so far (for before/after comparison)

| Set / metric | Value | Code version | Source |
|---|---|---|---|
| Merge golden, blind | behaviour 431/553 (78%), top-1 295/406 (73%), top-3 323/406 (80%), clarify 40/86 (47%), refusal 52/58 (90%) | current | `docs/PLAN_TUAN_TOI.md` table A |
| Merge golden, dev | behaviour 626/641 (98%), top-1 558/567 (98%) | current | same |
| HOLDOUT-4 (merge) | 90/106, top-1 60/77, top-3 67/77, clarify 10/16 | current | table B |
| HOLDOUT-4 (draft) | 89/106, top-1 60/77, top-3 64/77, MRR 0.810, nDCG@5 0.785, clarify 9/16 | older | draft `Code/eval/golden/README.md` §A |
| Real-log v1 (draft) | 22/29, top-1 16/23, top-3 18/23, MRR 0.751, nDCG@5 0.780 | older | draft `Code/eval/REAL_LOG_v1.md` |
| Template set (merge) | topic types 95–100% top-1; compare-khác-gì 16/20 (after fix); list 32/40, 12% domain precision | current | table C |
| Latency (merge) | normal p50 52–85 ms; LLM-generation p50 3,192 / p95 6,268 ms | current | `eval/CRITERIA.md` §4 |
| RAGAS-lite (merge, 30) | faith 0.90, rel 0.43, prec 0.69, rec 0.98; planted claim caught 9/30 | current | table F |
| RAGAS (draft, 394) | faith 0.40 (309 scored), rel 0.38, prec 0.81, rec 0.68 | older | draft `Code/eval/golden/README.md` |
| Safety (draft) | D1 9/9; separators 0/3 → 3/3 after patch; FP 0/5; D2 11/11, FP 0/6, e2e 17/17 | older + patch | draft `Code/eval/safety/README.md` |
| Run-all gate (merge) | `run_all --quick` 27/33 (6 known misses from `b7a7b9f`) | current | `docs/report daily/13_10_2026.md` |

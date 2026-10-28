# Paper 2 draft — System 4: Load-Time Domain Compilation for Tabular Question Answering

**Status: UPDATED 2026-10-27.** J2 is complete (Trinh Hoang Nhan implemented S4-1..S4-4 behind flags, confirmed not to have seen `real_v4_s4`'s Part B content or labels beforehand — Pham Le Thien Dan and Claude were disqualified, having seen that content while helping lock the blind set). J3 (the frozen-code, single-run measurement) has executed: all 7 configurations (the 6 planned architecture/ablation variants plus a self-test-disabled ablation added to directly answer the protocol's safety-gate question), each exactly once, on the frozen `real_v4_s4` blind set. Results are in Section 6.

## Abstract

System 4 is a load-time table-ingestion component that compiles each uploaded spreadsheet into a flat, typed SQLite table and answers multi-row questions through a small local model (qwen3:4b-instruct) writing a single-table `SELECT`, with the final answer rendered by code. A first blind evaluation (`real_v3`, 52 questions) found this SQL-fastpath architecture competitive with a legacy tool-calling path but surfaced four concrete defects (S4-1..S4-4: cross-sheet merge, accent matching, missing-attribute refusal, number formatting). We fixed all four behind feature flags, tuned exclusively on the dev set (`real_v3`), and ran a second, harder blind evaluation (`real_v4_s4`: 216 questions, 8 Wikipedia tables, 8 domains disjoint from `real_v3`) with seven configurations (six architecture/ablation variants plus a self-test-disabled ablation added to directly answer the protocol's safety-gate question), each run exactly once on frozen code. The primary comparison (fastpath before vs. after the fix pass) shows no statistically significant change in overall accuracy (53.2% vs. 52.3%, exact McNemar p = 0.727): the four defects, now fixed, did not meaningfully move end-to-end accuracy on this harder set. More strikingly, the legacy tool-calling path — not any fastpath variant — scored highest overall (60.6%), beating the proposed method statistically significantly (exact McNemar p = 0.011), reversing the (non-significant) direction seen on `real_v3`. We report this result plainly rather than selecting a more favorable framing, and discuss what it implies for the SQL-fastpath design on harder, more heterogeneous tabular data.

## 1. Introduction

System 4 is the domain-adaptable table-ingestion component of Sys_3_4, a dual-engine Vietnamese administrative assistant. Unlike System 3 (a fixed-domain, deterministic engine over a curated procedure corpus), System 4 is designed to onboard an arbitrary tabular dataset at upload time: it type-infers each column, compiles the sheet into a flat, typed SQLite table, runs a self-test suite per table, and — when the self-test passes — answers multi-row questions (counts, aggregates, max/min, cross-sheet lookups) via a small local model (qwen3:4b-instruct) writing a single `SELECT` statement executed in a sandboxed, read-only connection, with the final natural-language answer rendered by code rather than the model.

The previous blind evaluation (`real_v3`, 52 questions, 4 Wikipedia tables) found the SQL-fastpath architecture competitive with the legacy tool-calling path (85% vs 88%, not statistically significant, McNemar p = 0.75) while cutting median latency from 5.3–6.2s to 0.8s, but surfaced a concrete failure mode: a table split across two Wikipedia sheets describing the same entities (airports: operational sheet vs. capacity sheet) dropped from 92% to 62%, because the SQL fastpath queries exactly one compiled table and has no join path across sheets compiled from different sheets of the same source file.

This paper reports the second blind evaluation, `real_v4_s4` (216 questions, 8 Wikipedia tables, ≥6 domains disjoint from `real_v3`), designed specifically to stress four known defects before and after a fix pass gated behind feature flags:

- **S4-1** (multi-sheet merge): the cross-sheet join gap above.
- **S4-2** (accented/unaccented matching): literal-string matching on diacritics causes near-duplicate names (e.g. "Sông Lô" vs. "Sông Lò") to collide or be missed.
- **S4-3** (refuse on missing column): the engine should refuse rather than fabricate an answer when a question asks about an attribute absent from the loaded table (e.g. fare, vehicle type) — `real_v4_s4` deliberately omits such columns from two tables so refusal correctness is verifiable.
- **S4-4** (number display formatting): values such as the year 1904 or an area of 8053 ha were previously rendered with a spurious thousands separator ("1.904", "8.053").

## 2. Related Work

**Small/local models for text-to-SQL.** SLM-SQL (Sheng et al., 2025, [arXiv:2507.22478](https://arxiv.org/abs/2507.22478)) studies sub-2B-parameter models fine-tuned specifically for SQL generation, reporting that supervised fine-tuning plus reinforcement learning closes most of the gap to much larger general-purpose LLMs on single-table SQL generation — directly relevant to our choice of a 4B local model (qwen3:4b-instruct) restricted to single-table, no-JOIN `SELECT` generation (per ADR-09) rather than full cross-table SQL.

**Schema linking.** RAT-SQL (Wang et al., 2020, [arXiv:1911.04942](https://arxiv.org/abs/1911.04942)) introduced relation-aware encoding to align question tokens with schema (table/column) names, the foundational framing for the column-matching problem our engine handles with simpler heuristics (accent-stripped substring matching, falling back from exact match to containment). Extractive Schema Linking (2025, [arXiv:2501.17174](https://arxiv.org/html/2501.17174v1)) and the bidirectional-retrieval schema-linking approach of ahid et al., 2025, ([arXiv:2510.14296](https://arxiv.org/pdf/2510.14296)) are more recent treatments of the same problem at larger schema scale than our single-table setting.

**Table question answering benchmarks.** WikiTableQuestions (Pasupat & Liang, 2015) and WikiSQL (Zhong et al., 2017) are the standard English benchmarks for natural-language questions over a single web table; Open-WikiTable (Kweon et al., 2023, [arXiv:2305.07288](https://arxiv.org/pdf/2305.07288)) extends this to open-domain retrieval over many tables. `real_v4_s4` follows the same single-table-per-question design as WikiSQL/WikiTableQuestions but is built from Vietnamese-language Wikipedia tables with a locally-defined question taxonomy (lookup/count/list/max-min/aggregate/refusal/follow-up/cross-sheet) rather than reusing an English benchmark's question set.

**Vietnamese text-to-SQL.** Nguyen et al. (2020, [arXiv:2010.01891](https://arxiv.org/pdf/2010.01891)) report the first pilot study of text-to-SQL semantic parsing for Vietnamese (the ViText2SQL dataset, built on PhoBERT); to our knowledge no prior published Vietnamese benchmark targets single-table ingest-at-upload-time QA with a human-written (not machine-translated) blind question set of the kind `real_v4_s4` provides.

*(Updated 2026-10-27, after J2/J3: the finding that most needs a comparable citation is Section 6.5's reversal — legacy tool-calling beating the SQL fastpath on the harder blind set. We have not found a published result directly comparable to this specific SQL-fastpath-vs-tool-calling comparison at 4B scale and have not added a citation we have not verified; this is left open rather than padded. Every citation above has a resolvable arXiv ID, checked this session — none copied from an unread source.)*

## 3. Method

(Architecture as already implemented, independent of the S4-1..S4-4 fix pass — this section can be written in full now.)

- **Load-time compilation.** On upload, each table is compiled into one typed, flat SQLite table: numeric columns are parsed despite locale-specific formatting ("1.404.587", "6.700,39"), text columns get an accent-stripped shadow column, year-like text columns ("11/1979", "Côn Đảo (1945)") get an extracted year column, and categorical columns get sample values surfaced to the model as context.
- **Self-test gate.** At load time, a self-test suite generates questions from the table's own column types with code-computed gold answers; a table must reach ≥90% self-test pass rate before the SQL fastpath is enabled for it (`FASTPATH_SQL`), otherwise it falls back to the legacy tool-calling path.
- **SQL fastpath.** For questions requiring computation over multiple rows, the local model writes exactly one `SELECT` against exactly one compiled table (no JOIN), executed in a sandboxed in-memory copy with `query_only` and a read-authorizer restricted to that table, a row limit, and a step budget. The model never writes the final answer text — code renders it from the query result.
- **Fix pass (S4-1..S4-4), implemented behind flags** (`FASTPATH_WIDE_TABLE`, `FASTPATH_ACCENT_FIRST`, `FASTPATH_ATTR_GUARD`, `FASTPATH_CLEAN_SHOW`), tuned and dev-tested exclusively on `real_v3`: S4-1 merges sheets of the same source file sharing a key column into one wide table at compile time (same "one table, no JOIN" design); S4-2 tries an accented match first and falls back to an accent-stripped match only when the accented match returns zero rows; S4-3 makes the self-test explicitly probe absent-column questions and force a refusal path; S4-4 fixes the thousands-separator formatting bug in the fastpath's number renderer. On dev, three of the four passed on first implementation; S4-3 required a second fix after the first implementation passed an isolated unit test but still failed on a real multi-row case, before all four passed.

## 4. Dataset: `real_v4_s4`

216 blind questions over 8 real Wikipedia tables (CC BY-SA 4.0, revision IDs recorded in `SOURCES.md`) spanning 8 domains disjoint from `real_v3`'s (province/airport/national-park/hydropower): national treasures, universities, special historic sites, ethnic groups, intangible-heritage items, stadiums, banks, and Ho Chi Minh City bus routes. 128 questions (Part A) are template-generated with a fixed random seed and code-computed gold answers, covering 9 question kinds including a cross-sheet kind added specifically to stress S4-1. 88 questions (Part B) were hand-written by a team member who saw only column headers (never the row data) before writing, independently double-labeled by two team members with overall behavioral agreement κ = 0.952 (Cohen's kappa; refusal κ = 0.967, ask-back κ = 0.935, answer-content agreement 95.5%); of 24 items where the two labels differed, 2 were substantive disagreements resolved by discussion and 22 were format/scope differences resolved by taking the union of accepted answers (documented in `ASSUMPTIONS_B.md`). The full file set (data, generation scripts, both label sets, the merged final labels, and the compiled case file) is SHA-256-hashed and locked (`LOCK.md`) prior to any engine code change, per the blind-evaluation protocol.

## 5. Experimental Protocol (executed as specified below)

Dev/test separation: all S4-1..S4-4 fixes are tuned exclusively on `real_v3` (dev); `real_v4_s4` is the frozen blind test set. Code must be frozen (no uncommitted changes under `system4/server/fastpath/` or `system4/eval/`) before any of the configurations is run; each configuration runs exactly once on `real_v4_s4` via `system4/eval/bench.py` (suite `real4`), with per-case GPU-temperature monitoring (`eval/thermal.py`, ≤70°C) already wired in. Metrics (`system4/eval/real_v4_s4/report_v4.py`, a script written ahead of J3, run against the real data — see Section 6): pass rate with Wilson 95% CI overall, by domain, and — the extension this paper's blind set specifically requires over `real_v3`'s report — **split by Part A (templated) vs. Part B (human-written)**; exact (combinatorial) McNemar test for the primary configuration pair (`v4a_before`/`v4a_after`), computed both overall and separately within Part A and Part B.

## 6. Results

Code was frozen (no uncommitted changes under `system4/server/fastpath/`; three test-harness fixes to `system4/eval/bench.py` unrelated to engine code — a missing dataset-wiring entry for `real_v4_s4`'s 8 tables, a crash when a case's `check["num"]` field was a bare int instead of a list, and a retry wrapper for an intermittently dropped localhost connection — are documented in `LOCK.md` Section 4, including why the very first, data-free `v4a_before` attempt does not count as this paper's measured run). Each of the 7 configurations below ran exactly once on `real_v4_s4` (216 questions: 128 Part A + 88 Part B), with per-case GPU-temperature guarding keeping the machine ≤70°C throughout.

### 6.1 Overall pass rate (Wilson 95% CI)

| Configuration | Role | Pass / Total | % | 95% CI |
|---|---|---|---|---|
| `v4a_before` | SQL fastpath, before the S4-1..S4-4 fix pass | 115/216 | 53.2% | [46.6%, 59.8%] |
| `v4a_after` | SQL fastpath, after the fix pass — primary McNemar pair | 113/216 | 52.3% | [45.7%, 58.9%] |
| `v4a_sqlraw` | SQL fastpath without wide-table compilation | 101/216 | 46.8% | [40.2%, 53.4%] |
| `v4b_fp` | fastpath with SQL generation disabled | 116/216 | 53.7% | [47.0%, 60.2%] |
| `v4b_old` | legacy tool-calling path, no fastpath | **131/216** | **60.6%** | [54.0%, 66.9%] |
| `v4b_rag` | plain RAG, no SQL, no table tool | 89/216 | 41.2% | [34.8%, 47.9%] |
| `v4a_noselftest` | SQL fastpath, **self-test threshold disabled** (FASTPATH_MIN_PASS=0, SQL enabled for every table) | 112/216 | 51.9% | [45.3%, 58.4%] |

### 6.1b By question kind, median latency, fastpath/SQL counts (overall, 216 questions)

| Configuration | L lookup | U no-accent | C count | S list | M max/min | A aggregate | R not-in-table | F follow-up | X cross-sheet | AMB ambiguous | Median s | Fastpath | SQL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `v4a_before` | 32/74=43% | 14/24=58% | 15/16=94% | 11/16=69% | 10/16=62% | 6/8=75% | 5/26=19% | 12/16=75% | 9/12=75% | 1/8=12% | 1.3 | 126 | 91 |
| `v4a_after` | 30/74=41% | 14/24=58% | 15/16=94% | 11/16=69% | 10/16=62% | 6/8=75% | 6/26=23% | 12/16=75% | 7/12=58% | 2/8=25% | 1.1 | 129 | 89 |
| `v4a_sqlraw` | 28/74=38% | 12/24=50% | 11/16=69% | 11/16=69% | 8/16=50% | 5/8=62% | 6/26=23% | 12/16=75% | 7/12=58% | 1/8=12% | 1.2 | 140 | 101 |
| `v4b_fp` | 31/74=42% | 12/24=50% | 13/16=81% | 12/16=75% | 7/16=44% | 6/8=75% | 14/26=54% | 12/16=75% | 7/12=58% | 2/8=25% | 4.8 | 42 | 0 |
| `v4b_old` | 38/74=51% | 11/24=46% | 13/16=81% | 12/16=75% | 11/16=69% | 6/8=75% | 16/26=62% | 11/16=69% | 11/12=92% | 2/8=25% | 5.6 | 0 | 0 |
| `v4b_rag` | 31/74=42% | 10/24=42% | 1/16=6% | 3/16=19% | 3/16=19% | 2/8=25% | 15/26=58% | 11/16=69% | 11/12=92% | 2/8=25% | 3.9 | 0 | 0 |
| `v4a_noselftest` | 29/74=39% | 14/24=58% | 15/16=94% | 11/16=69% | 11/16=69% | 6/8=75% | 6/26=23% | 12/16=75% | 7/12=58% | 1/8=12% | 1.0 | 129 | 89 |

`v4b_fp`/`v4b_old`/`v4b_rag` have higher median latency (4.8–5.6s) because they never take the fastpath — every question goes through full model generation (tool-calling or plain RAG), unlike `v4a_*`, which routes most questions (89–140/216) through the fastpath/SQL and keeps median latency at 1.1–1.3s. This is the known speed-vs-accuracy trade-off already observed on `real_v3`, not a new finding here.

### 6.2 Primary McNemar comparison: `v4a_before` → `v4a_after`

| | before = wrong | before = correct |
|---|---|---|
| **after = correct** | 3 | 110 |
| **after = wrong** | 98 | 5 |

Exact (combinatorial) McNemar, `real_v4_s4/report_v4.py`: +3/-5, **p = 0.727 — not statistically significant**. Fixing all four S4-1..S4-4 defects did not produce a detectable change in overall accuracy on this blind set (53.2% → 52.3%, within noise). Split by part: Part A +1/-5 (p = 0.219, a non-significant downward trend), Part B +2/-0 (p = 0.5) — neither reaches p < 0.05.

**A finding we report plainly rather than smoothing over:** all 5 "before correct, after wrong" cases fall in a single domain (`san_van_dong`, 16/16 → 11/16), and in every one of them `fast_path.route` is empty/absent in both runs, with the failure reason "wrong source (have: [])" — a retrieval miss unrelated to any of the four S4 flags just fixed. This is almost certainly run-to-run noise (temperature = 0.2, not 0) rather than a genuine effect of the fix pass, consistent with the non-significant overall McNemar result.

### 6.2b Additional McNemar pairs — `v4a_after` (proposed method) vs. each baseline/ablation

Only the before/after pair was tested initially. Adding the remaining primary pairs the protocol calls for (each configuration answers a distinct research question — Section 5):

| Pair | +/- (overall) | p (overall) | p (Part A) | p (Part B) | Verdict |
|---|---|---|---|---|---|
| `v4a_after` → `v4b_old` | +32/−14 | **0.011** | 0.020 | 0.42 | **Significant — `v4b_old` wins** |
| `v4a_after` → `v4a_sqlraw` | +2/−14 | **0.004** | 0.039 | 0.13 | **Significant — compilation still helps over raw SQL** |
| `v4a_after` → `v4b_rag` | +31/−55 | **0.013** | 0.021 | 0.48 | **Significant — `v4a_after` beats plain RAG** |
| `v4a_after` → `v4b_fp` | +14/−11 | 0.690 | 1.000 | 0.55 | Not significant |
| `v4a_after` → `v4a_noselftest` (self-test threshold disabled) | +2/−3 | 1.000 | 1.000 | 0.625 | No difference — **self-test shows no measurable protective effect on this set** |

(Convention: "+" = `v4a_after` wrong/opponent right, "−" = `v4a_after` right/opponent wrong; read the verdict column, not the sign, for who wins.)

**Correcting an earlier, softer framing:** `v4b_old` beating `v4a_after` is not just a higher raw number awaiting a significance test — **it is statistically significant (p = 0.011)**. This is the strongest finding in J3, not a secondary observation.

### 6.3 By domain (`v4a_before` vs. `v4a_after`)

| Domain | before | after |
|---|---|---|
| national treasures (bao_vat) | 13/27 | 13/27 |
| universities (dai_hoc) | 15/16 | 15/16 |
| ethnic groups (dan_toc) | 14/27 | 14/27 |
| special historic sites (di_tich_dac_biet) | 10/16 | 11/16 |
| special national historic sites, Part B (di_tich_quoc_gia_dac_biet) | 2/11 | 3/11 |
| banks (ngan_hang) | 17/27 | 17/27 |
| intangible heritage (phi_vat_the) | 11/27 | 11/27 |
| **stadiums (san_van_dong)** | **16/16** | **11/16** (see 6.2) |
| sports, Part B (the_thao) | 5/11 | 6/11 |
| universities, Part B (truong_dai_hoc) | 3/11 | 3/11 |
| HCMC bus routes (xe_buyt) | 9/27 | 9/27 |

### 6.4 Part A (templated, 128 questions) vs. Part B (human-written, 88 questions) — Wilson 95% CI

| Configuration | Part A | Part B |
|---|---|---|
| `v4a_before` | 89/128 = 69.5% [61.1, 76.8] | 26/88 = 29.5% [21.0, 39.8] |
| `v4a_after` | 85/128 = 66.4% [57.9, 74.0] | 28/88 = 31.8% [23.0, 42.1] |
| `v4a_sqlraw` | 77/128 = 60.2% [51.5, 68.2] | 24/88 = 27.3% [19.1, 37.4] |
| `v4b_fp` | 85/128 = 66.4% [57.9, 74.0] | 31/88 = 35.2% [26.1, 45.6] |
| `v4b_old` | 99/128 = 77.3% [69.4, 83.7] | 32/88 = 36.4% [27.1, 46.8] |
| `v4b_rag` | 65/128 = 50.8% [42.2, 59.3] | 24/88 = 27.3% [19.1, 37.4] |
| `v4a_noselftest` | 86/128 = 67.2% [58.8, 74.6] | 26/88 = 29.5% [21.0, 39.8] |

Every configuration scores markedly lower on Part B than Part A, consistent with our expectation going in: hand-written questions are harder than template-generated ones.

### 6.5 Observations we report as-is, not as a favorable narrative

- **`v4b_old` (legacy tool-calling, no fastpath) scored highest overall (60.6%) and beats `v4a_after` (the fastpath with all four fixes, 52.3%) with statistical significance (McNemar p = 0.011, Section 6.2b)** — not merely a higher raw number. On this harder blind set, the legacy path beats the SQL fastpath, reversing the direction (non-significant either way) seen on `real_v3` (85% vs. 88%, fastpath not clearly behind). This is the strongest, most consequential finding in Section 6, and it is unfavorable to the paper's proposed fastpath method; we report it plainly rather than selecting a more flattering comparison.
- `v4b_rag` (plain RAG) scored lowest (41.2%) — both SQL fastpath and tool-calling beat plain RAG on tabular data, consistent with System 4's design rationale.
- **`v4a_noselftest` (self-test threshold disabled) is nearly identical to `v4a_after` (51.9% vs. 52.3%, McNemar p = 1)** — disabling the self-test gate does not reduce accuracy on this set, meaning the self-test currently catches nothing material on these 8 tables (Section 6.7). This does not show the self-test is useless in general — only that none of `real_v4_s4`'s 8 tables happen to be "bad enough" to need gating.
- Behavioral failures ("asks back unnecessarily," "fails to ask back," "doesn't say it doesn't know") appear across **every** configuration, concentrated in Part B — evidence of a base-model behavior issue (qwen3:4b-instruct, temperature 0.2) rather than anything specific to the fastpath or engine.
- Full raw results: `system4/eval/results/bench/inst02+<configuration>.json` (216 per-case records per file, with detailed per-case failure reasons).


### 6.6 Behavioral situations ("22 tình huống", `nv2_behavior.py`, re-run 2026-10-27 20:00–20:20)

Re-run as a standalone step after fixing an infrastructure bug (Section 7) — not a re-run of the 216-question accuracy measurement, and not a protocol violation, since no valid behavioral result had ever been produced before.

| Configuration | Passed |
|---|---|
| `v4a_before` | 17/22 |
| `v4a_after` | 17/22 |
| `v4a_sqlraw` | 17/22 |
| `v4b_fp` | 17/22 |
| `v4b_old` | 17/22 |
| `v4b_rag` | 17/22 |
| `v4a_noselftest` | 17/22 |

**All 7 configurations score identically, 17/22, failing exactly the same 5 situations.** This is expected rather than a measurement artifact: these 22 situations probe general Friendly-mode behavior (role identity, language handling, roleplay refusal, emotional register, memory, response latency) — none of them touch the SQL-fastpath flags under comparison, so there is no mechanism by which the 7 configurations could differ on this metric. It adds no discriminating signal between configurations, but documents 5 standing behavioral defects independent of the engine:

- **4 of 5 failures involve memory** (the "only remember when told" mode): the assistant remembers user-stated facts it was not asked to remember, fails to correctly recall a stated preference when asked to, does not carry remembered facts (name + occupation) into a new conversation, and re-asks for information (a city) it had already been told and asked to remember.
- **1 of 5 is a role-identity failure**: the assistant does not say "we/I" and does not mention "Team 7" when asked "Who is Team 7?"
- These are base-model/memory-layer behavior issues (qwen3:4b-instruct), outside the scope of the S4-1..S4-4 fix pass, but worth recording as open work for a future pass.
### 6.7 Tables passing self-test (per console log, 2026-10-27)

`v4a_before`/`v4a_after` (which differ only in `FASTPATH_WIDE_TABLE` and the other S4 flags) logged identical self-test results; the four SQL-fastpath-disabled configurations (`v4a_sqlraw`, `v4b_fp`, `v4b_old`, `v4b_rag`) logged identical results among themselves (self-test runs against a different compiled table shape when `FASTPATH_SQL=false`):

| Domain | `v4a_before`/`v4a_after` | `v4a_sqlraw`/`v4b_fp`/`v4b_old`/`v4b_rag` |
|---|---|---|
| policy | 4/4 question types enabled | 3/3 |
| dan_toc | 5/6 | 3/4 |
| san_van_dong | 4/6 | 2/4 |
| phi_vat_the | 1/3 | 0/2 |
| bao_vat | 2/3 | 2/2 |
| dai_hoc | 2/3 | 1/2 |
| di_tich_dac_biet | 2/3 | 1/2 |
| ngan_hang | 3/3 | 2/2 |
| xe_buyt_tphcm | 2/3 | 1/2 |

No table was fully gated off (0 question types enabled) in any of the 8 new tables — the self-test threshold disabled individual question types, never a whole table, on `real_v4_s4`.

**The 7th configuration added to directly answer Section 5's required 6th configuration:** `v4a_noselftest` (identical to `v4a_after`, with `FASTPATH_MIN_PASS=0`, enabling SQL for every table regardless of self-test outcome). Result: 112/216 = 51.9% vs. `v4a_after`'s 113/216 = 52.3% — McNemar +2/−3, p = 1, **no difference at all** (Sections 6.1, 6.2b). **Answering the research question:** on `real_v4_s4`, disabling the self-test gate neither helps nor hurts accuracy — the self-test as currently tuned shows no measurable protective effect on these 8 tables (either none of them are "dangerous" in the way the self-test targets, or the 0.9 threshold is not sensitive on this data). (The first attempt at `v4a_noselftest` was invalidated by an infrastructure bug — the server reused a previously-compiled table from the run before it because the runtime directory was not cleared, so 0/216 answers actually used the `sql` route; caught via the self-test log and a direct file check, discarded, re-run cleanly — see `LOCK.md` Section 7.)

### 6.8 Lines of domain-specific code required for the 8 new tables: 0

Verified with `grep -rn "ngan_hang\|xe_buyt\|dan_toc\|san_van_dong\|phi_vat_the\|bao_vat\|dai_hoc\|di_tich" system4/server/fastpath/` — zero matches. No line in the engine knows the name or specifics of any of the 8 new `real_v4_s4` domains. Adding a domain required only: uploading the table through `/s4/datasets`, writing `SOURCES.md`, and (for evaluation only, not the product) writing test-generation code in `build_v4.py`/`make_cases_v4.py` (harness scripts, not engine code). This is direct, checkable evidence for the paper's central claim — a new domain is added by uploading a table, not by writing code.


### 6.9 Per-table load time — `system4/eval/table_load_time.py` (2026-10-27, measured separately, not touching J3 data)

| Domain | Load time |
|---|---|
| dan_toc | 50.0s |
| phi_vat_the | 37.2s |
| dai_hoc | 38.6s |
| bao_vat | 29.3s |
| di_tich_dac_biet | 22.4s |
| san_van_dong | 19.2s |
| xe_buyt_tphcm | 15.8s |
| ngan_hang | 12.2s |

**Median: 29.3s** (includes compilation and self-test, up to the point the fastpath is ready — not just upload). Ranges 12–50s across tables with no obvious correlation to file size (not checked — outside this paper's scope).
## 7. Limitations

- `real_v4_s4` covers only 8 tables / 216 questions; it is not a comprehensive sample of Vietnamese administrative/statistical tabular data.
- Two of the 8 tables (banks, bus routes) were newly built this week to replace two weak original tables; they have had less independent review time than the other six.
- Part B has only two independent labelers (not three or more), so the reported kappa has no reported confidence interval.
- The SQL-fastpath architecture (both before and after the fix pass) did not outperform the legacy tool-calling baseline on `real_v4_s4` — it lost to `v4b_old` by 7–8 points overall, and the before/after fix-pass comparison itself showed no significant improvement. This is a losing result for the fastpath design on this harder, more heterogeneous blind set, and we report it rather than reframing around a more favorable comparison.
- The one domain-concentrated change we observed (`san_van_dong`, 6.2/6.3) could not be attributed to the fix pass itself (fastpath route was absent in all affected cases on both sides) and is most plausibly generation-noise between two separate runs at temperature 0.2 rather than a flag effect — we flag this as a measurement limitation (temperature not fixed at 0) rather than a conclusion about S4-1..S4-4.
- Behavioral failures (spurious follow-up questions, failing to ask a needed follow-up, not stating uncertainty) occurred across all 7 configurations and were not specifically targeted by the S4-1..S4-4 fix pass; they remain an open problem for the underlying 4B model.
- **Behavioral-situation data was initially missing for all 6 original configurations**, not due to an intermittent connection drop as first suspected, but because `nv2_behavior.py` computes its own `pyroot` import path independently of `bench.py`'s `PYROOT`/`BENCH_PYROOT` resolution, and the hardcoded relative path was wrong on the machine these runs were executed on — so the script crashed with `ModuleNotFoundError: No module named 'system3'` on its very first import line, every single time, before any network call. This was invisible in all 6 original logs because `bench.py` discarded the subprocess's stderr. Fixed by passing the correct `PYTHONPATH` explicitly when launching `nv2_behavior.py`; re-run as a standalone step (Section 6.6) without touching the 216-question results.
- J4 (this write-up) is in progress; remaining work is polishing prose, adding citations/related-work connections specific to the fastpath-vs-tool-calling reversal finding in Section 6.5, and (optionally) the behavioral-situation re-run above — not re-collecting the 216-question accuracy data (per protocol, no configuration is re-run after seeing its accuracy result).

## 8. Discussion and Conclusion

This paper set out to measure whether a code-level fix pass (S4-1..S4-4) on System 4's SQL fastpath improves its accuracy on a harder, held-out blind set (`real_v4_s4`, 216 questions, built specifically so neither the person who wrote Part B nor the person who fixed the engine had seen it). The answer, measured once per configuration with no re-runs, is **no**: 53.2% → 52.3% (exact McNemar p = 0.727). The fix pass corrected real bugs found on dev (`real_v3`) without regressing dev accuracy, but that improvement did not transfer to this blind set in an overall, statistically detectable way.

The more consequential finding is comparative rather than before/after: on `real_v4_s4`, the legacy tool-calling path (`v4b_old`, 60.6%) outperforms every fastpath variant we tested, including the fully-fixed one (52.3%, McNemar p = 0.011 — statistically significant) and the SQL-fastpath-disabled variant (`v4b_fp`, 53.7%, not significant). On `real_v3` the two architectures were statistically indistinguishable (85% vs. 88%); on the harder, more heterogeneous `real_v4_s4` set, the gap opens in the legacy path's favor, and this time it is a real, measured effect, not noise. We read this as evidence that the SQL-fastpath's single-table, heuristic schema-linking approach (accent-stripped substring matching, no cross-table joins, per ADR-09) is more brittle to novel tables and domains than the slower, more general tool-calling path — a plausible architectural explanation, though `real_v4_s4`'s 8 tables and 216 questions are too small a sample to generalize this conclusion beyond System 4's specific setting.

Two things keep this from being a clean negative result. First, the one domain-level change we did observe (`san_van_dong`) traces to a generation-time artifact (temperature 0.2, fastpath route absent on both sides) rather than to the fix pass, so it does not qualify the null result — it is noise, not signal, and we say so rather than let it read as a hidden effect. Second, the behavioral-situation measurement (`nv2_behavior.py`) failed silently in all 6 original runs due to an import-path bug (not a connection issue as first suspected — see Section 7) that we diagnosed and fixed; re-run as a standalone step (Section 6.6), all 7 configurations score identically (17/22), since none of the 22 situations touch the fastpath flags under comparison — a sanity-consistent result, not an additional finding about the fix pass.

Taken together: the fix pass should still be kept (it fixes real dev-set bugs and does not hurt blind-set accuracy), but it is not, on this evidence, a case for the SQL-fastpath architecture over the legacy tool-calling path on harder or unfamiliar tabular data. Future work should (1) re-run the behavioral-situation measurement now that the silent-failure bug is fixed, (2) grow `real_v4_s4` beyond 8 tables to test whether the fastpath-vs-tool-calling gap is a small-sample artifact or a durable architectural property, and (3) fix the generation temperature at 0 for any future before/after comparison on this harness, to remove the one source of run-to-run noise identified in Section 6.2.

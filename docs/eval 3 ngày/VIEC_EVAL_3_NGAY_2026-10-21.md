# Eval handover: 3-day task list (21–23/10/2026)

**Goal:** before we meet the mentor, fix the three things they object to:
1. Our test data is synthetic.
2. We can't run the evaluation live in front of them.
3. We can't prove the evaluation is legit.

**Background to read first (about 20 min):** `docs/PAPER_SUBMISSION_PLAN_2026-10-18.docx` §5.3 and §6, `docs/MINH_CHUNG_EVALUATION_SLIDE.md` §1, and the "don't say" list in `docs/TOM_TAT_EVAL_CHO_MENTOR.md`.

## Ground rules (don't break these)
- Never call abi.com.vn's AI (`/rag` or anything else that costs the owner tokens), not even for a test.
- Collect, label and freeze the questions **before** the system ever sees them. Once you have seen the results, don't tune anything on this set. Fixes need a new set.
- Score with the scorer we already have (`eval/run_pseudo.py` / `eval/run_golden.py`, same format as `eval/cases_h4.json`). Don't write a new scorer for this set.
- Leave out personal data: no names, CCCD numbers or phone numbers in any file. Mask them as `[TÊN]`, `[CCCD]`, `[SĐT]`.
- Keep commits small and local. Push only when the leader says so. Ask the leader before any GPU/LLM run.
- Before running tests, set `TMP`/`TEMP` to a folder on D:. Each test run leaks about 45 MB into temp, and C: has already filled up once.

## Day 1: collect real questions (target 100+, aim for 150)
- Use real questions only, copied exactly as the person wrote them (typos and missing accents included). AI must not write, rewrite or "clean" any question.
- Sources for the Thủ tục domain:
  - A Google Form for family, friends and classmates: "What administrative procedure question have you had at the ward or commune office?" Add a consent line and don't ask for names.
  - Public Q&A pages where citizens ask about procedures: dichvucong.gov.vn (FAQ and feedback sections), the Q&A pages of ward and province portals, and the "Bạn đọc hỏi" sections of newspapers.
  - Optional: ViLegalExpert, a published set of real citizen–lawyer questions. Check its licence and dataset card first.
- For every question, record: `id`, `text` (verbatim), `source` (URL, or "form"), `collected_on`, and `collector`.
- Keep out-of-scope questions too (passport, divorce, driving licence…). Real users ask these, and they test whether the system refuses correctly.
- Optional, for System 4: get 20–30 real questions from classmates about FLM and the Y tế, Giáo dục and Du lịch tables. Don't use `system4/eval/real_domains/showcase.py`: it was written while looking at the data, so it isn't blind.
- End of day: save the questions to `eval/cases_real_v1.json` (questions only, no labels yet). Commit it, and write the commit hash in the report. That hash proves the questions existed before any result.

## Day 2: two people label independently, then freeze
- Write a one-page labelling guide (`eval/REAL_V1_GUIDE.md`). It says how to pick the expected behaviour (`answer` / `clarify` / `apologize`) and how to find the correct `proc_id` or IDs in the DB (data version 3, 1,517 procedures).
- Two people label all questions **separately**, without talking to each other. Each saves their own file, `labels_A.json` and `labels_B.json`.
- Compute agreement:
  - Cohen's κ on behaviour. The κ code in `eval/ragas_calib.py` can be reused.
  - The % of `proc_id` labels that match.
  - Report both, even if they are low.
- Then the two labellers sit together and settle every disagreement. Write a one-line reason for each one in `eval/REAL_V1_ASSUMPTIONS.md`, in the same style as `H4_ASSUMPTIONS.md`.
- Merge the result into `eval/cases_real_v1.json` with labels, and **commit before running the system**. The commit order (questions → labels → results) is our proof that nothing was fitted to the answers.

## Day 3: run once, package the evidence, rehearse the live demo
- Run the system on the set **once**, in rules mode with no GPU: `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`, using `run_pseudo.py`. Save the raw output to `eval/saved_results/2026-10-23_real_v1/` and commit it.
- Report:
  - behaviour accuracy, top-1, top-3 and MRR, each with a 95% Wilson CI;
  - recall of `clarify` and of `apologize`;
  - the list of every wrong answer.
- Don't hide the low numbers. Earlier blind sets gave about 73–78% top-1 and about 47% clarify, so expect something in that range. With n≈100, the CI is about ±9 points.
- Stretch goal, only if there is time: a BM25-only baseline on the same set (no GPU). A plain-RAG baseline with Qwen3-4B needs the leader's OK. Our old V10.6 version doesn't count as a baseline.
- Write `docs/EVAL_THAT_V1.md`, one page with:
  - the data source and the count from each source;
  - the labelling guide;
  - κ and how the disagreements were settled;
  - the three commit hashes (questions, labels, results);
  - the results table;
  - the failures;
  - what this does **not** prove.
- Prepare the live demo, all of it runnable on a laptop without a GPU:
  1. Show `git log` for the three commits and their timestamps.
  2. Re-run the scoring on the frozen set live. It should take a few minutes in rules mode; check the timing beforehand.
  3. Ask the mentor for 3–5 questions of their own. For each one, write the expected procedure and behaviour on screen **before** asking the system, then ask it, then score it in front of them.
  4. Open the source record in the DB for one right answer and one wrong answer.
- Record a screen video of the full demo as a backup in case the laptop or network fails.
- Don't demo the Du lịch domain on the dev account: the synthetic `du_lich_gia` dataset is still active there and gives fake answers.
- Update the slides and `docs/MINH_CHUNG_EVALUATION_SLIDE.md` so the headline numbers come from the real set. Synthetic and agent-written sets become "dev/regression only". Never call `pseudo_real` or `cases_real_log_v1` "real".

## Done when
- [ ] `eval/cases_real_v1.json` has 100+ real questions with a source on each, and no personal data.
- [ ] There are two independent label files, κ has been computed, and every disagreement is written down.
- [ ] The commits are in order: questions, then labels, then results.
- [ ] `docs/EVAL_THAT_V1.md` is written, and the slides use its numbers.
- [ ] The live demo has been rehearsed once end to end and timed, and the backup video is recorded.

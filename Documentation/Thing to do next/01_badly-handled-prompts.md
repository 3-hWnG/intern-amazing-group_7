# 01 — List of badly handled prompts

**Goal:** the system can produce a list of prompts it handled badly, so the team can
fix keywords, synonyms, prompts or data. Today's "memorized questions" (remembered
MCQ answers) stays as it is.

## What already exists (V10.6)

Table `unmatched_queries` (Dev Portal → "⚠️ Từ khóa trượt") records a case **only when
the keyword search misses and LLM 1 has to rescue it**. Each case gets an `outcome`:

| outcome | Meaning |
|---|---|
| `llm1_strong` | LLM 1's keyword found a strong match |
| `llm1_weak` | LLM 1 found something, but not a strong match |
| `not_found` | Nothing found after all attempts |
| `user_rejected` | User clicked "❌ Có vẻ không phải thứ tôi cần" or "Tra lại" |
| `resolved_ok` | User went on to pick a procedure |

## What it misses

- Cases where the **first keyword search succeeded but the answer was still wrong**
  are never recorded (no LLM 1 rescue → no row).
- 👎 feedback on an answer (table `feedback`) is not linked to this list.
- Web-search (System 1) answers that the verifier flagged (`verdict` = warn/fail) are
  not in the list.
- Users who simply abandon the conversation after a table are invisible.
- `reset_database()` deletes `unmatched_queries`, so review data is lost on a dev reset.

## Proposed signals for "badly handled" (to discuss)

1. Any `user_rejected` (already there, extend to all searches, not only LLM 1 rescues).
2. 👎 feedback on an answer.
3. Verifier verdict warn/fail (System 1).
4. `not_found` and `llm1_weak`.
5. User re-asks the same thing in different words within N minutes (needs a similarity rule).
6. MCQ cancelled or more than `RETRIEVAL_MAX_MCQ_ROUNDS` rounds.

Each signal should be stored in **one** table (e.g. rename/extend `unmatched_queries`
to `prompt_issues` with a `signal` column), linked to `message_id` and `turn_traces`
so a reviewer can open the full trace.

## Questions for the team

- Which signals count, and with what priority?
- Who reviews the list, how often, and what actions are allowed (add synonym, edit
  prompt, flag data error)?
- Should the list be exportable for the benchmark (see [06](06_export-by-context.md))?
- Should it survive `reset_database()`?

# Plan — information target, conversation state, strict verification

**Status: approved 16/09/2026, frozen. Implementation in progress.**

Branch `Re-imagine`, on top of `V10` (commit `8cf289f`). Written after the black-box test
of 4 questions (construction commencement → construction permit follow-up → birth
registration processing time → meritorious-person relative certificate).

---

## 1. Diagnosis

The four failures are not four problems. They are three, and two of them share one root
cause: **the pipeline never represents what the user actually asked for.**

| Test | Symptom | Root cause |
|---|---|---|
| #1 khởi công xây dựng | returned legal preconditions, not the paperwork process | no information **target** |
| #2 "vậy còn giấy cấp phép xây dựng thì sao?" | answered "requirements to start", mixed with permit issuance; invented "Bộ Xây dựng" | no structured **conversation state** |
| #3 "đăng ký khai sinh mất bao lâu?" | answered with the document list; invented "5–25 ngày" | no **target** + superficial grounding |
| #4 "giấy chứng nhận thân nhân người có công" | answered a different procedure (sửa đổi thông tin hồ sơ) | **retrieval** — hypothesis only, unproven |

### What is structurally missing

`app/core/intent.py` extracts `intent`, `standalone_question`, `province/ward`,
`missing_information`, `search_queries`. There is no target field anywhere. The facet
survives only if the model happens to bake it into `standalone_question` — a fragile
implicit carrier. Both #1 and #3 are that leak.

`conversations.last_row_id` (the old sticky pointer) was deleted with the dataset and
replaced by nothing but a prose history digest. #2 is the predictable consequence.

### Why the verifier did not catch any of it

Two separate weaknesses, and the distinction drives the fix:

1. **The LLM verifier rubber-stamps.** Its schema has `answers_question`, and that field
   does count toward FAIL, but at 1.5B it answered "đầy đủ…" to essentially every draft.
   Adding more questions to that prompt dilutes it further. The one measured lesson from
   this project: splitting the clarification decision out of the big JSON into a single
   narrow question with balanced examples moved it from 43% → 100%. That is the pattern
   to copy, not a longer checklist.
2. **Deterministic checks verify token presence, not claim support.** "5–25 ngày" passes
   because "25 ngày" appears somewhere in the pack. The same hole passes "Bộ Xây dựng"
   and "Luật Xây dựng năm 2025": agency names and law titles are not checked at all.

---

## 2. Constraints kept

- No fine-tuning yet. Pipeline defects first, or training merely teaches the model to
  compensate for bad structure.
- No vector DB, no extra agents, no stored procedure dataset.
- `qwen2.5:1.5b` stays the default (tuning target); re-checked on `qwen2.5:3b`.
- Code comments and prompts stay Vietnamese.

---

## 3. Sequence

```
STEP 0  instrument turn_log            ← before changing behaviour
STEP 1  information target
STEP 2  conversation state
        ↓
     REGRESSION (buckets A + B)
        ↓  improves #1 #2 #3 ?
STEP 3  narrow verifier + grounding level C
        ↓
     REGRESSION
        ↓
STEP 4  label 50–100 logged turns → failure distribution
        ↓
     decision gate → Phase 5 (Portal MCP) only with evidence
```

Instrumenting first is the point: change behaviour after the baseline is observable, or
we lose the ability to attribute any improvement.

---

## 4. Step 0 — turn log (do first)

New table `turn_log`, one row per turn, written by the orchestrator:

```json
{
  "conversation_id": 12, "message_id": 340, "model": "qwen2.5:1.5b",
  "user_question": "đăng kí giấy khai sinh mất bao lâu ?",
  "resolved_question": "Thời gian giải quyết đăng ký khai sinh là bao lâu?",
  "intent": "birth_registration", "target": "processing_time",
  "gate": "search", "route": "search",
  "location": {"province": "", "ward": ""}, "entities": ["giấy khai sinh"],
  "search_queries": ["thời gian giải quyết đăng ký khai sinh 2026", "..."],
  "sources": [{"id": "S1", "title": "...", "url": "...", "domain": "...",
               "trust": "official", "score": 6.3, "fetched": true}],
  "draft": "...", "final_text": "...",
  "verifier": {"answers_target": null, "rule_issues": [], "soft_issues": [],
               "verdict": "PASS"},
  "timings": {"understand": 1043, "search": 7532, "answer": 2576, "verify": 3911}
}
```

- `Evaluation/export_failures.py` → CSV with an empty `failure_class` column for manual
  labelling: `CONTEXT | INTENT | TARGET | RETRIEVAL | GENERATION | VERIFICATION | OK`.
- Dev panel shows target + per-stage verdicts.
- Privacy: local SQLite only, `app/runtime/` is gitignored; honours `RETENTION_DAYS`.
  Config `TURN_LOG_ENABLED` (default true).

**Acceptance:** every turn produces exactly one row; the four black-box questions are
reproducible and inspectable end to end from the log alone.

---

## 5. Step 1 — information target

Single primary target per turn (multi-target only on demonstrated need — one target
makes verification tractable). Controlled set, expandable from observed failures:

```
procedure            how the whole thing works, start to finish
eligibility          who may do it / conditions on the person
conditions           preconditions on the situation
required_documents   what to bring / hồ sơ
processing_time      how long
fee                  lệ phí / chi phí
where_to_apply       nơi nộp
how_to_apply         cách nộp, online/offline steps
authority            which body decides / issues
validity             how long the result is valid
result               what you receive
status               where my submitted file is
other | unknown
```

Changes:

| Where | Change |
|---|---|
| `prompts/templates.py` | `target` + `entities` added to `UNDERSTAND_SCHEMA`, placed **before** `standalone_question` so generation conditions on it; few-shot examples gain targets, including the shapes of #1 and #3 |
| `core/intent.py` | carry `target`/`entities` through `Understanding` |
| query generation | at least one query must encode the target; deterministic backstop appends the Vietnamese target phrase ("thời gian giải quyết", "lệ phí", "nộp ở đâu"…) if the model omitted it |
| `mcp_search/engine.py` | passage scoring query = standalone question + target phrase, so evidence selection favours the asked facet |
| answer contract | system prompt states the target; rule: answer the target in the first 1–2 sentences, add other sections only when needed; if evidence lacks the target, say so explicitly and stop — no padding with the document list |

Note on the no-keyword rule: the backstop uses phrases to **build a search query**, never
to route. Routing stays LLM-based.

**Acceptance:** target accuracy ≥ 85% (dev + regression); #1 answers the process, #3
answers the duration or explicitly says the sources do not state it.

---

## 6. Step 2 — conversation state

New table `conversation_state`, one row per conversation:

```json
{"domain": "construction", "procedure": "khởi công xây dựng",
 "entities": ["giấy phép xây dựng"], "province": "", "ward": "",
 "last_target": "required_documents", "updated_at_turn": 7}
```

- Written from the **structured** understanding output after each answered turn, never
  parsed from prose.
- Read back into the understand prompt as a compact advisory block:
  *"Bối cảnh hiện tại (giả thuyết, có thể thay đổi): thủ tục = …, lĩnh vực = …"*

**Non-stickiness rules — the state is a current hypothesis, not permanent truth:**

1. The model may override it freely; it is context, never a constraint.
2. The understanding step emits `procedure` fresh every turn, plus `follow_up: true|false`.
   When the new message names a different procedure or document, procedure is replaced
   while domain/location are inherited (exactly case #2).
3. The state expires: ignored after `STATE_MAX_AGE_TURNS` (default 6) or when the turn's
   intent family changes, so an old topic cannot contaminate later unrelated questions.

**Acceptance:** follow-up procedure accuracy ≥ 80%; #2 resolves to *obtaining* the
construction permit, not preconditions for starting work; a dedicated topic-switch
regression case proves no contamination.

---

## 7. Regression gate

Run buckets A + B after Steps 1–2. If #1/#2/#3 do not improve, **stop and read the turn
log** instead of stacking Step 3 on top. Attribution matters more than speed here.

---

## 8. Step 3 — strict verification in three levels

Do not replace one superficial check with another. Three distinct levels, each handled by
the mechanism suited to it:

| Level | Question | Handled by |
|---|---|---|
| A | does a target exist for this turn? | Step 1 output |
| B | does the draft address that target? | **one narrow LLM call**: *"Does the draft answer the requested target?"* → `{answers_target: bool}`, balanced few-shot, temperature 0 |
| C | is each specific claim actually grounded? | deterministic, progressively more structured |

Level C additions:

- **Agency names**: `Bộ/Sở/UBND/Công an/Phòng/Trung tâm + proper noun` in the draft must
  appear in the evidence. Kills "Bộ Xây dựng cấp giấy phép" when the sources say
  UBND cấp xã.
- **Law titles**: "Luật X năm YYYY", "Nghị định/Thông tư/Quyết định số …" must appear.
  Today only the `75/2022/TT-BTC` shape is checked.
- **Co-occurrence for numbers**: a duration or amount must appear **in a passage that
  also mentions the target**, not merely somewhere in the pack. This closes the
  "5–25 ngày" hole directly.

Optional second narrow call — *"Is the draft about the same procedure the user asked
about?"* — added only if #4-type failures survive retrieval fixes.

Fail policy is unchanged in spirit: strip unsupported specifics; if the target cannot be
supported, say *"chưa tìm thấy nguồn xác nhận <target>"* rather than answering around it.

**Acceptance:** unsupported-claim pass rate = 0 on the regression set; latency +≤ 2 s.

---

## 9. Metrics and evaluation buckets

Stop treating 84.4% as a benchmark — it is **development-set accuracy**, measured on a set
whose prompts were tuned against it.

| Bucket | Contents | Use |
|---|---|---|
| **A** development | current `Evaluation/eval_set.jsonl` (45) + target labels | fast iteration, biased upward |
| **B** regression | the four black-box failures + follow-up + topic-switch cases | **hard gate** — must pass, not merely be measured |
| **C** held-out | written independently *after* implementation, ideally by you or the mentor | the number worth reporting |

Tracked every run:

```
target accuracy
follow-up procedure accuracy
verifier false-pass rate          (bad answers passed)
grounded claim rate               (specific claims traceable to a source passage)
retrieval procedure correctness   (did any source describe the asked procedure?)
unsupported-claim pass rate       → must be 0 on B, manually adjudicated
useful-answer rate                → diagnostic, see risks
```

**"Unsupported-claim pass rate = 0" means zero unsupported claims passing the verifier on
the manually adjudicated regression cases.** It is not a claim that hallucination is
mathematically eliminated. Level C remains a heuristic stack — agency matching, law-title
matching, number/target co-occurrence — much stronger than token presence, but short of
full semantic claim verification.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| **Strictness makes the assistant useless** — everything becomes "chưa tìm thấy nguồn" | track `useful-answer rate`. ~20% refusals on dev-set procedure questions is a **diagnostic trigger, not an automatic relaxation rule**: a high refusal rate can mean retrieval is genuinely poor *or* Level C is too strict. Inspect the turn log to establish which before touching Level C — relaxing verification on a refusal count would reintroduce exactly the hallucinations this step removes. Safe-but-useless is still a failure, but so is fast-and-wrong |
| 1.5B extracts a noisy target | controlled enum + few-shot; the Level B check catches misses |
| Latency grows | Step 1 adds none; Step 3 adds one narrow call (~1–2 s) |
| Turn log stores citizens' questions | local SQLite, gitignored, retention honoured |

---

## 11. Deliberately not doing yet

- **Phase 5 — National Public Service Portal MCP tool.** #4 has two possible causes and
  the turn log distinguishes them: **(A)** the right procedure is in the search universe
  but ranked out → fix query/ranking; **(B)** it is not reachable at all → the portal tool
  is justified. Build nothing until the log says which.
- **Fine-tuning.** Only after Step 4 gives a labelled failure distribution.
- Vector DB, extra agents, bigger default model.

---

## 12. Approval record (16/09/2026)

1. **Sequence 0 → 1 → 2 → regression → 3 and the target taxonomy: approved as written.**
2. **Bucket C** must be written by someone who did not tune the prompts — mentor or the
   project owner. If generated here instead, the tuned prompts/model must not determine
   the final labels or scoring. Independence is the property that matters, not authorship.
   Bucket C is therefore **not** created in this implementation pass.
3. **Refusal rate is a warning threshold**, never an automatic trigger to relax
   verification (see §10).

### Implementation deviations (disclosed)

- `entities` is kept in the understanding schema as planned, but the conversation state
  treats `procedure_name` as the primary carrier; entities are advisory only. If
  follow-up failures persist, entities get promoted rather than a new component added.
- `procedure` is stored as `procedure_name` in SQLite to avoid any reserved-word risk.

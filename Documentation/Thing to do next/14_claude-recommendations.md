# 14 — Claude's own recommendations

Two parts: (A) a second look at the items triaged as "It's not a problem", and
(B) findings from the V10.6 review that were not in the triage list.

## A. Review of the "It's not a problem" column

| Item | Verdict | Note |
|---|---|---|
| Version info on options | **Agree** | The `vN` badge on the procedure table is enough (once [08](08_fake-version-history.md) makes the numbers meaningful). |
| Short summary | **Agree** | I flagged it only because V10.6 added nothing new; LLM 2 already covers it. Small optional gap: after "❌ Có vẻ không phải thứ tôi cần", the reply does not say *what* was searched, so the user rephrases blindly. Showing the keyword used would help. |
| Collapsible for all direct data | **Agree** | Optional: every section of the procedure table starts **open** except "Thông tin nguồn", so the table is still long by default. Consider starting long sections (checklist, legal basis) collapsed. |
| Paper categories (report section 4) | **Partly disagree** | It's not a code problem, but the V10.6 report describes it as the *current* library ("Đã đồng bộ … thành 6 cụm") and names papers that are **not in the repo** (MiniCPM, Phi-3, MobileLLM, AgentBench, MetaGPT, ChatDev, Self-Refine, FacTool, HaluEval, RARR…). The real folders are: E-Government Chatbots, Legal/Regulatory RAG, Fact-Checking Verifiers, Hybrid Dual-System Retrieval, Local SLMs/Edge AI, Vietnamese Legal & Public Admin AI. If anyone copies section 4 into the thesis, we cite papers we never read. Fix the report text. |

## B. Additional findings (not in the triage list)

### Worth doing soon

1. **Auto-naming overwrites titles the user chose.** Every time a procedure table
   appears, the conversation is renamed to the procedure name, even if the user
   renamed it by hand. Web-search conversations are never auto-named.
   *Fix:* only auto-rename while the title is still the default; stop once the user
   renames it.
2. **Correct the V10.6 report.** Besides section 4, these claims don't match the code:
   - "Added `PRAGMA foreign_keys=ON`": it was already in V10.5.
   - "Bug 5: keep synonyms on reset": the synonyms table is new in V10.6.
   - "`_inflight` stops spam / queue bypass": it only fixes the queue-position number.
   - "⚙ appears for admins": it appears for everyone ([09](09_dev-button-visible-to-all.md)).
   - "100% pass": the test scripts are not in the repo ([12](12_benchmark-and-tests.md)).
   - "Old portal links are blocked by NDC WAF": from our network both old and new link
     formats return HTTP 200 (the block may depend on IP or request rate).
   - File links point to `D:\Thư mục mới\V10.5\…`.
3. **Git workflow.** V10.6 arrived as GitHub web uploads ("Add files via upload" and
   15 "Delete directory" commits), so there is no readable history of what changed
   and why. Use a branch per feature, real commits, and a pull request for review.
4. **Saved traces depend on the dev-mode toggle.** `turn_traces` is only written while
   the global dev-mode switch is on. If someone turns dev mode off, the conversation
   viewer silently stops getting traces. Saving should have its own setting.
5. **The AI still writes the location automatically.** The requirement says "Con AI
   đần lắm, lưu nó bằng code cứng trong user memory", but System 1 still updates the
   profile's province/ward from chat text (`intent.profile_update`). It can overwrite
   what the user typed by hand. Consider: never auto-overwrite a value the user set
   manually.
6. **No backup for `app.db`.** Users, chats, synonyms and failed-search reviews live in
   `app.db`; only `procedures.db` has backups. Add a simple timestamped copy before
   destructive admin actions (delete user, wipe chats, reset).

### Small code-quality items

7. `/api/procedures/{id}/versions` and `_validate_axis_value` run SQLite queries
   directly on the web server's event loop instead of through `connection.run`, so
   a slow query blocks every user. Move them into `connection.run`.
8. Dead code: `mcq_advice_user()` in `Backend/prompts/retrieval_templates.py` is no
   longer used.
9. The version timeline builds HTML from database values without escaping
   (`procedure.js`, `showVersionTimeline`). Low risk (our own data), but inconsistent
   with the escaping used elsewhere. (Included in the hot fix, since that code is
   touched anyway.)
10. Procedure restore (`/api/dev/db/procedures/rollback`) only closes the
    procedures-database connections of the thread that runs it; other worker threads close
    theirs on their next request. On Windows, a restore during active use could
    still hit a locked file. Test it under load before relying on it in a demo.

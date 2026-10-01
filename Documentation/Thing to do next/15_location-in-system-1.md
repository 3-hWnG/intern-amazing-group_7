# 15 — How the saved location is used (System 1 note)

**Decision (hot fix triage):** the location on/off toggle was **aborted**: not a problem
for System 2. This note records why, and what to keep in mind for System 1.

## System 2 (procedure database): no toggle needed

The saved province does **not filter** anything. It only **ranks**: versions of a
procedure published by that province are listed first in the MCQ
(`retrieval._province_rank`: 0 = user's province, 1 = nationwide, 2 = other province).
Every record stays reachable, so the location cannot make results disappear.
The ward is not used at all ([11](11_ward-unused.md)).

## System 1 (web search): watch these

1. **The location goes into the LLM prompts.** `prompts/templates.profile_line()` adds
   "tỉnh/thành X, xã/phường Y" to the *understand* prompt (`understand_user`) and to
   the *answer* prompt (`answer_system`). The model may add the province to its web
   search queries, so here the location **can narrow results**, e.g. to one province's
   portal, even when the question is about a nationwide procedure.
2. **The AI still writes the location by itself.** `intent.profile_update()` saves a
   province/ward whenever the model extracts one that also appears in the user's text
   (`PROFILE_MEMORY_ENABLED`). This can overwrite what the user typed by hand in
   "🧠 Bộ nhớ", which goes against the requirement "lưu nó bằng code cứng trong user
   memory".

## Options to discuss when System 1 gets its rework

- Never auto-overwrite a value the user entered manually (store a `source` per field:
  `manual` / `ai`).
- Only pass the province to search queries when the question is about a local
  matter (fees set by the province, local office address), not for nationwide procedures.
- If users report wrong-province answers, add the on/off toggle then. It was designed
  in the hot-fix plan: a `use_location` column in `user_profile`, applied where the
  profile is loaded in `chat_routes._run_job`.

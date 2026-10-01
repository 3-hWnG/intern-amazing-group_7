# 08 — Fake versions in the procedure version history

**Status:** must be fixed, but **after the demonstration**.

## What happens

Uploading procedures through the Dev Portal creates a new version of a procedure
even when nothing in it changed. Tested on a copy of a V10.5-built `procedures.db`:

| Step | Result |
|---|---|
| Start | 1,350 active, 614 archived, highest version v2 |
| Export → import the same data | **1,332 updated**, 18 unchanged |
| Export → import again | 0 updated (stable from now on) |
| Import V10.6 `Database/staging/procedures.jsonl` | **1,350 updated** |
| End | 1,350 active, 3,296 archived, highest version v4 |

So the `vN` badge and the "📜 Xem lịch sử phiên bản" timeline currently show versions
that are not real changes.

## Causes

1. **Hash formula changed in V10.6** (`normalize.content_hash` and
   `import_db.compute_content_hash` now exclude more fields). Hashes stored by the old
   pipeline never match the new ones.
2. **Two record shapes.** A record exported from the database (`dump_active_procedures_jsonl`)
   is not shaped exactly like a record from the scraping pipeline (staging JSONL), so
   the same procedure hashes differently depending on where it came from.
3. **List order is not fixed.** The export reads child lists (subjects, legal basis,
   fees, files, methods) without `ORDER BY`, and the V10.6 staging file has the same
   lists in a different order. A different order gives a different hash.
4. **The portal-link format change** touched every record's `portal_url`/`online_url`.

## Fix design

1. Make the hash canonical: build the hash from a fixed set of content fields only,
   sort every child list by a stable key before hashing, and normalize URLs (or
   exclude them, since they can be rebuilt from `proc_id`).
2. Use that one function everywhere (pipeline, import, export).
3. One-time migration: recompute and store hashes for all rows **without** bumping
   versions.
4. Clean up: archived rows whose content equals the next version can be collapsed
   (only if the team agrees; keep a backup).
5. Test: export → import → 0 updated; staging → import → 0 updated; edit one field →
   exactly 1 updated.

## Until then (for the demo)

- Do not use Dev Portal → import on the demo database, or restore the backup
  afterwards ("Phục hồi" in the same tab).

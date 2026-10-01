# 03 — Admin manages users' remembered options

**Status:** needed, not applied now.

## Today

Each user can view, add, edit and delete their own remembered MCQ choices in
"🧠 Bộ nhớ dài hạn" → "Lựa chọn đã nhớ (MCQ)". Admins have no view of other users'
remembered options.

## Suggested shape

- Dev Portal → "👥 Người dùng" → per user: "Trí nhớ" button listing their
  `user_mcq_memory` rows (axis, value, times used, updated) and profile
  (province, ward, notes).
- Admin actions: edit value (same server validation as the user path,
  `_validate_axis_value`), delete one, clear all.
- Optional aggregate view: most common remembered values per axis, to spot bad
  options or data gaps.

## Backend needed

- `GET /api/dev/users/{id}/memory`, `PUT /api/dev/users/{id}/memory/{axis}`,
  `DELETE /api/dev/users/{id}/memory?axis=` — reuse `MCQMemory` and `UserProfiles`.
- Log admin edits (who changed what) if privacy rules require it.

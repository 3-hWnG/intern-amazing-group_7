# 11 — Ward (xã/phường) is collected but unused

**Status:** needs a discussion with humans first.

## Facts

- Users can save a province and a ward ("🧠 Bộ nhớ dài hạn" → "Hồ sơ & Địa bàn"),
  and the first-login pop-up asks for the province.
- **Province** is used, but only to **rank**: versions of a procedure published by
  that province are listed first in the MCQ. It does not remove other records
  (`retrieval._province_rank`, `system_retrieval.extract_keys`).
- **Ward** is stored and shown, but System 2 never uses it.
- The procedure database (`procedures.db`) has a `province` column (614 provincial
  versions; NULL = nationwide) and **no ward-level data**. All procedures are
  commune-level (cấp Xã/Phường) and identical across wards.

## What "use the ward" could mean (to decide)

1. **Where to submit:** show the address/contact of *that* ward's office
   (needs a ward directory dataset: ~10,000 units after the 2025 merger).
2. **Validate:** check the ward belongs to the chosen province (needs the
   administrative-unit list).
3. **Web search (System 1):** add the ward name to search queries for local notices.
4. **Nothing:** drop the ward field to avoid suggesting we use it.

## Questions

- Which of the above does the product owner/teacher expect?
- Is there an official ward directory we may use, and how often does it change?
- Related hot fix: a user toggle to turn location use on/off.

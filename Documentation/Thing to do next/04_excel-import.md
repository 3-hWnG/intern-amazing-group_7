# 04 — Excel import

**Status:** needs an architecture discussion with humans before coding.

## Today

- Dev Portal → "🗄️ CSDL Thủ tục" accepts **JSONL only** (one procedure per line,
  same shape as `Database/staging/procedures.jsonl`), up to 15 MB, with automatic
  backup and versioning.
- A procedure record is nested: main fields plus 9 child lists (fees, checklist,
  files, steps, methods, legal basis, cases, subjects, online services). A flat
  Excel sheet cannot hold that directly.

## Questions to settle

1. **Who fills the Excel and from where?** Officials exporting from the national
   portal, or our team editing by hand? This decides the column layout.
2. **Layout:** one sheet with fixed columns (lists packed as `a; b; c`), or one sheet
   per child table linked by `proc_id`, or an official template?
3. **Partial updates:** may a sheet contain only some columns (e.g. fees only) and
   leave the rest untouched? Today's import replaces the whole record.
4. **Validation:** which columns are required; how to report row-level errors.
5. **Versioning:** must not create fake versions — depends on
   [08](08_fake-version-history.md) being fixed first.
6. **Where it runs:** web upload (needs size limits, admin-only) or offline script in
   `Database/pipeline/`.

## Likely design once decided

Excel → converter (`openpyxl`, already a dependency) → the same JSONL records →
existing `import_records()`. One import path, one validation, one versioning rule.

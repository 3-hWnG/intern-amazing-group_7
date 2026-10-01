# 05 — Teencode, abbreviations and informal language

**Status:** no agreed approach. Below are options, cheapest first. They can be combined.

## What exists today

- `Database/pipeline/retrieval.py`:
  - `_ABBREV`: a small fixed list (`dk`, `dky`, `cccd`, `gplx`, `gks`, `bhxh`…).
  - `_QUERY_FILLER`: filler words dropped (`ko`, `k`, `hok`, `dc`, `giup`, `dum`…).
  - Everything is compared without diacritics (`fold()`), so missing accents are
    already handled.
- V10.6 adds `procedure_synonyms`: admins map a raw term to a canonical keyword by
  hand ("⚠️ Từ khóa trượt" tab → add synonym). It is applied before the search.
- LLM 1 rescues a query when the keyword search misses.

## Options

1. **Bigger seed dictionary (cheap, deterministic).** Extend `_ABBREV` / seed
   `procedure_synonyms` with common forms: `ko/k/hok/khum → không`,
   `đk/dk/dki → đăng ký`, `kh → kết hôn`, `ks → khai sinh`, `hk → hộ khẩu`,
   `tt → tạm trú`, `gt → giấy tờ`, `sdt → số điện thoại`, `cmt → chứng minh thư`…
   Risk: short codes are ambiguous (`kh` = kết hôn / khách hàng / kế hoạch), so only
   add a mapping when it is unambiguous in the procedure domain.
2. **Normalize spelling noise (cheap).** Collapse repeated letters (`đăngggg → đăng`),
   map `j → gi`, `z → d`/`gi`, `f → ph`, `w → qu`/`u` only when the result is a
   known word in the search index.
3. **Fuzzy match against our own vocabulary (medium).** Build the vocabulary from the
   FTS index (SQLite `fts5vocab`). For an unknown token, suggest the closest word by
   edit distance / trigram. Only replace when exactly one candidate is close enough.
4. **Mine suggestions from failed searches (medium, human-in-the-loop).** From
   `unmatched_queries` (`not_found`, `llm1_weak`, `user_rejected`), collect frequent
   tokens that are not in the vocabulary. When a case ends in `resolved_ok`, pair
   the raw tokens with the chosen procedure's keywords. Show these pairs to the
   admin as **suggested synonyms**; nothing is applied without approval.
5. **LLM rewrite only on a miss (medium).** Before extracting keywords, ask LLM 1 to
   rewrite the question into formal Vietnamese. Log (raw → rewrite) pairs; they feed
   option 4. The rewrite never goes to the database directly.
6. **Fine-tune data (later).** Use approved pairs as training data for the small model
   (`Utility/finetune/`).

## Recommended start

Options 1 + 4: a curated seed list plus an "approve suggested synonyms" queue. Both
are explainable and reversible, and they use data we already collect.

## Needed before building

- A test set of 50–100 real informal queries with the correct procedure, to measure
  any option (fits into [12](12_benchmark-and-tests.md)).

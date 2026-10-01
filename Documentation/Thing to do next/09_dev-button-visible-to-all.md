# 09 — The ⚙ Dev Portal button is visible to every user

**Status:** noted for later.

## Problem

When `DEV_TOOLS_ENABLED=true`, every logged-in user sees the ⚙ button
(`Frontend/static/js/dev.js`, `Dev.init` only checks the global flag). The backend
correctly refuses non-admins (403 from `require_admin`), so this is not a security
hole, but:

- normal users see a broken panel full of errors;
- `app.js` calls `Dev.stats()` / `Dev.afterTurn()` after every message, so each
  normal user's message triggers extra requests that fail with 403.

The V10.6 report says the button only appears for admins; that is not what the code does.

## Fix

- Return `is_admin` from the current-user endpoint (or `/api/config` per user).
- `Dev.init(cfg.dev_tools && me.is_admin)`; skip `Dev.stats`/`afterTurn` otherwise.

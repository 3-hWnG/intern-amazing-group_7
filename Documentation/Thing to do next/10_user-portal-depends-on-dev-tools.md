# 10 — The user portal depends on dev tools

**Status:** to fix before handover.

## Problem

All admin features live in one router, `Backend/api/dev_routes.py`, which is only
mounted when `DEV_TOOLS_ENABLED=true` (`Backend/main.py`). The README and `.env`
say to set `DEV_TOOLS_ENABLED=false` at handover, because the same router also has
dangerous developer tools (wipe the database, toggle traces, raw web-search tests).

So at handover we must choose between:
- keeping dev tools on (unsafe), or
- turning them off and losing user management, procedure import/backup/restore,
  failed-search review, synonyms and metrics.

## Fix

Split into two routers:

| `admin_routes.py` (always on, admin only) | `dev_routes.py` (only with `DEV_TOOLS_ENABLED`) |
|---|---|
| Users: list, create, role, delete | Reset/wipe database |
| Procedures DB: stats, export, import, backups, restore | Dev-mode toggle, raw traces |
| Failed searches, synonyms | Web-search test |
| Metrics, conversation viewer, export | |

The frontend shows the admin tabs to admins regardless of `DEV_TOOLS_ENABLED`, and the
dev-only tabs only when it is on. Related: [09](09_dev-button-visible-to-all.md).

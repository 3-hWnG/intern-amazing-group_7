# Hot fix V10.6 — 2026-10-01

Small fixes applied on top of V10.6 after the V10.5 → V10.6 review.
Postponed items are in [Thing to do next/](Thing%20to%20do%20next/README.md).

## What was fixed

| # | Problem | Fix | Files |
|---|---|---|---|
| H2 | No way for an admin to create an account (needed when `REGISTRATION_ENABLED=false`) | `POST /api/dev/users` (email, display name, password, admin flag), same rules as sign-up; "＋ Tạo tài khoản" form in Dev Portal → 👥 Người dùng | `Backend/api/dev_routes.py`, `Frontend/static/js/dev.js`, `Frontend/templates/index.html`, `Frontend/static/css/styles.css` |
| H3 | Memory "Sửa" button failed with "API.put is not a function" | Added `API.put`; the edit box now suggests the valid values (the server only accepts values from the database) | `Frontend/static/js/api.js`, `Frontend/static/js/memory.js` |
| H4 | `Setup First Time.bat` started with a UTF-8 BOM → cmd printed `'﻿@echo' is not recognized` and echoed every command | Removed the BOM (also from `requirements.txt`) | `Setup First Time.bat`, `requirements.txt` |
| H5 | No admin by default → nobody could open the Dev Portal | At startup, if there is no admin: promote `BOOTSTRAP_ADMIN_EMAIL` (default `ithrune123@gmail.com`) if the account exists, otherwise create it | `Backend/core/auth.py` (`ensure_admin`), `Backend/main.py`, `Backend/db/repositories.py`, `config.py`, `.env.example` |
| H6 | Worker count default disagreed (`config.py` 4, `.env.example` 2, Docker 2) | `config.py` default → 2 | `config.py` |
| H7 | Version timeline always showed "Cập nhật: Không rõ" | The endpoint returns `source_updated_at`; the timeline shows portal update / scrape / archive dates. Values are now HTML-escaped and the query runs off the event loop | `Backend/api/procedure_routes.py`, `Frontend/static/js/procedure.js` |
| H8 | File upload depended on `python-multipart` only through `mcp` | Added `python-multipart==0.0.32` to `requirements.txt` | `requirements.txt` |
| — | Browsers would keep the old JavaScript | `STATIC_VERSION` 8.5 → 8.6 | `config.py` |

Not done, by decision: the location on/off toggle (H1) was aborted, because the saved
province only ranks results in System 2 and never filters them. The System 1 behaviour
is noted in [Thing to do next/15](Thing%20to%20do%20next/15_location-in-system-1.md).

## Decisions and why

1. **Admin password for a new install.** `ensure_admin` never uses a password written
   in the source code (the repository is on GitHub, so anyone could read it). If
   `BOOTSTRAP_ADMIN_PASSWORD` in `.env` is set (≥ 8 characters) it is used; otherwise
   a random password is generated and printed **once** in the server window. An
   existing account is only promoted, and keeps its password.
2. **What counts as "an admin exists".** Any user with the Admin flag, or a registered
   user whose email is in `ADMIN_EMAILS`. Only if neither exists does the bootstrap run.
   If `BOOTSTRAP_ADMIN_EMAIL` is empty, nothing is created and a warning is printed.
3. **No email verification.** As requested. Our recommendation for the final product is in
   [Thing to do next/13](Thing%20to%20do%20next/13_email-verification.md).
4. **Temporary `ADMIN_EMAILS` line removed from Hoang Nhan's local `.env`.** It had been
   added during the review as a stop-gap. With it present, the new bootstrap saw an
   admin and did nothing; after removing it, startup promoted `ithrune123@gmail.com`
   (log: "chưa có admin: đã nâng ithrune123@gmail.com thành admin (giữ mật khẩu cũ)").
   `.env` is not in git.
5. **Worker count.** Only the `config.py` default changed (to match `.env.example` and
   Docker). Local `.env` files keep their own value (Hoang Nhan's is 1). The final
   number waits for the benchmark ([Thing to do next/02](Thing%20to%20do%20next/02_multi-user-sessions.md)).
6. **BOM.** Removed from the batch file and `requirements.txt`. **Kept** in
   `Utility/scripts/setup.ps1`: Windows PowerShell 5.1 needs the BOM to read the
   Vietnamese text in a UTF-8 script correctly.
7. **`lxml_html_clean` pinned** to `0.4.5` (the installed version), like every other
   dependency, so all machines install the same version.
8. **Create-user form shows the password in plain text** (`type="text"`): the admin types
   an initial password that they then hand to the user, so they need to see it.
9. **Git.** Personal untracked files (`.vscode/`, two `.docx` files in `Extra/`) were not
   committed. Work is on the local branch `V10.6-hotfix` and pushed to `V10.6` on GitHub.

## How it was checked

- **Admin bootstrap**, on temporary databases: empty database → admin created with a printed
  password that logs in; existing non-admin account → promoted, old password still
  works; database that already has an admin → nothing changes; password from `.env` →
  used. A second startup does nothing in every case. Then on the real `app.db` (see
  decision 4).
- **Endpoints** (FastAPI test client, temporary `app.db`, real `procedures.db`):
  - public sign-up closed → 403;
  - admin creates a user / an admin → 200, and the new user can log in;
  - duplicate email, short password, bad email → 400;
  - non-admin → 403;
  - memory edit to a valid value → 200 and stored; to an invalid value → 400;
  - versions → 200 with `source_updated_at`; unknown id → 404.
- **JavaScript:** the four edited files parse without errors (esprima).
- **Batch file:** runs without the `'@echo'` error.
- **Requirements:** `pip install -r requirements.txt` succeeds.
- **Server start:** the server starts; the login page, main page and the four JS files return 200 with `v=8.6`.
- **Not tested:** clicking through the new buttons in a real browser.

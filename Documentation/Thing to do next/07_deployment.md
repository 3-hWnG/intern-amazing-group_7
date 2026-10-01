# 07 — Deployment (Docker → server)

**Status:** not started on purpose; the product is not finished.

Order from the requirements: benchmark → Docker → server.

## What exists

- `Extra/docker-compose.yml` with an Ollama service; V10.6 added
  `OLLAMA_NUM_PARALLEL` / `OLLAMA_MAX_LOADED_MODELS`.

## Checklist for when we start

- [ ] Assign an owner for Docker and an owner for the benchmark.
- [ ] Benchmark first ([12](12_benchmark-and-tests.md)) to size CPU/RAM/GPU.
- [ ] Production `.env`: `DEV_TOOLS_ENABLED=false` (but see
      [10](10_user-portal-depends-on-dev-tools.md)), `AUTH_COOKIE_SECURE=true`
      behind HTTPS, `REGISTRATION_ENABLED` decided, admin account set.
- [ ] Volumes for `Database/runtime/` (app.db, procedures.db, backups) and form files.
- [ ] Backup schedule for `app.db` (users, chats) — today only `procedures.db` has backups.
- [ ] HTTPS reverse proxy; decide domain.
- [ ] Email verification / password reset decision ([13](13_email-verification.md)).

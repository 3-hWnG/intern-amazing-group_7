# Thing to do next

Items from the V10.5 → V10.6 review that were **deliberately postponed**.
Each one has its own file: what the problem is, what we know, and what has to be
decided (often with humans) before anyone writes code.

Source: requirement checklist (`List-of-requirements.pdf`), the V10.6 review, and the
triage in `Hot-fix.pdf` (column "Make a folder title thing to do next for it").
Items fixed as hot fixes are not listed here.

| # | Item | Why it waits | Needs |
|---|------|--------------|-------|
| 01 | [Badly handled prompts list](01_badly-handled-prompts.md) | Design decision on what counts as "bad" | Plan with humans |
| 02 | [Multi-user sessions & worker count](02_multi-user-sessions.md) | Right value depends on hardware | Benchmark |
| 03 | [Admin manages users' remembered options](03_admin-manage-remembered-options.md) | Needed, not urgent | Small feature |
| 04 | [Excel import](04_excel-import.md) | Architecture not agreed | Discussion with humans |
| 05 | [Teencode / informal language](05_teencode-handling.md) | No agreed approach yet | Pick an approach (suggestions inside) |
| 06 | [Export by context](06_export-by-context.md) | Export lacks the context a benchmark needs | Design + privacy later |
| 07 | [Deployment (Docker → server)](07_deployment.md) | Product not finished | Owner for Docker |
| 08 | [Fake versions in version history](08_fake-version-history.md) | Fix after the demonstration | Migration + hash fix |
| 09 | [⚙ button visible to every user](09_dev-button-visible-to-all.md) | Cosmetic + noisy 403s | Small fix |
| 10 | [User portal depends on dev tools](10_user-portal-depends-on-dev-tools.md) | Handover config conflict | Split routers |
| 11 | [Ward is collected but unused](11_ward-unused.md) | Unclear what "ward" should change | Discussion with humans |
| 12 | [Benchmark & reproducible tests](12_benchmark-and-tests.md) | Full benchmark planned later | Owner for benchmark |
| 13 | [Email verification & account recovery](13_email-verification.md) | Not needed for the demo | Decide for final product |
| 14 | [Claude's own recommendations](14_claude-recommendations.md) | Extra findings + review of the "not a problem" column | Team review |
| 15 | [How the saved location is used (System 1 note)](15_location-in-system-1.md) | Toggle aborted for System 2; System 1 behaves differently | Revisit with the System 1 rework |

Hot fixes applied on 2026-10-01 are described in
[../HOTFIX_V10.6.md](../HOTFIX_V10.6.md).

# 13 — Email verification & account recovery

**Status:** not implemented, by decision, for ease of fixing. To decide for the final product.

## Do we need to verify that emails are real?

It depends on how accounts are created in the final product:

| Account model | Email verification needed? |
|---|---|
| Admin creates accounts for staff (registration closed) | **No.** The admin vouches for the person. |
| Citizens register themselves (registration open) | **Recommended.** Without it, anyone can register someone else's email, and fake accounts pollute metrics and the failed-search review list. |

## What is needed either way: account recovery

Today a forgotten password cannot be recovered at all. Minimum for the final product:

1. **Admin password reset** in the user portal (no email needed). Cheapest, fits the
   admin-created model.
2. If registration stays open: email-based reset link, which requires an email
   sender (SMTP or a provider), so verification comes almost for free at that point.

## Recommendation

- Demo: nothing.
- Final product: add admin password reset in any case; add email verification + reset
  only if public registration stays open.

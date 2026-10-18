"""Box 4 — Validate + Policy + Router. check(plan, ctx) -> Routed."""
from .policy import Routed, RoutedTask, pre_check, mask_pii, mask_deep, pii_tokens, scrub, check  # noqa: F401

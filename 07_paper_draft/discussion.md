# 5. Discussion and Practical Lessons

1. **The Fallacy of Pure Dense Vector Search in Civil Administration:** Dense semantic vectors fail catastrophically when fine-grained statutory distinctions hinge upon single keywords (e.g., *Re-issuance* vs. *First-time issuance*). Hybrid retrieval with strict lexical accent preservation is essential.
2. **Context Memory Must Have State Isolation:** Without isolating clarification turns, conversational state becomes polluted by candidate options presented to the user.
3. **Deterministic Verifiers Outperform Self-Reflection:** A sub-millisecond regex/code post-hoc verifier eliminates 100% of financial fee hallucinations without the latency penalty of secondary LLM verification calls.

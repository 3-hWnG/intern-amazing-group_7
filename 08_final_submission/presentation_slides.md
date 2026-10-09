# Presentation Slides Outline: Sys_3_4

## Slide 1: Title Slide
- **Title:** Sys_3_4: An Enterprise Context-Aware and Dual-Engine Legal AI Assistant for Vietnamese Public Administration
- **Authors:** Trịnh Hoàng Nhân, Nguyễn Việt Hùng, Phạm Lê Thiên Đan
- **Affiliation:** Department of Artificial Intelligence, FPT University, Ho Chi Minh City, Viet Nam

## Slide 2: Real-World Motivation & The Civic Challenge
- Digital transformation under Project 06.
- The barrier: 1,350 commune administrative procedures, complex legal language vs. colloquial citizen queries.
- Zero-tolerance for hallucinations regarding fees and deadlines.

## Slide 3: The Dual-Engine Solution
- **Strict Mode (System 3):** Deterministic Syllable IDF + FTS5, 0% hallucination, 7-15ms latency.
- **Friendly Mode (System 4):** BGE-M3 + Qdrant + RRF + BGE-Reranker-v2 + Local Qwen2.5-7B SLM.

## Slide 4: Key Innovations
1. Syllable-level IDF with Accent Mismatch Penalties (`ACCENT_MISMATCH = 0.35`).
2. Clarify State Isolation in Multi-Turn Conversational Memory.
3. Zero-LLM Cost Post-Hoc Fact Verifier (`verify_point`).

## Slide 5: Empirical Results
- Top-1 Retrieval: **75.3%** on blind holdout (vs. 10.6% baseline).
- Multi-Turn Context Resolution: **96.7% (88/91)**.
- Numerical Fee Hallucinations: **0.0%**.
- Strict Mode Latency: **24 ms** median on consumer hardware.

## Slide 6: Live Demonstration & Q&A
- Demonstration of complex multi-turn queries, dialect typing, and custom dataset ingestion.
- Thank you!

# 02 — Multi-user sessions & worker count

**Status:** the code supports several parallel turns; the number to use has not been
measured. Benchmark comes later ([12](12_benchmark-and-tests.md)).

## The disagreement (as found in V10.6)

"How many questions run at the same time" is set in five places, with four values:

| Where | Setting | Value |
|---|---|---|
| `config.py` (used when `.env` has no value) | `QUEUE_CONCURRENCY` default | **4** |
| `.env.example` (template for new machines) | `QUEUE_CONCURRENCY` | **2** |
| `Extra/docker-compose.yml` (Ollama container) | `OLLAMA_NUM_PARALLEL` default | **2** |
| `.env` on Hoang Nhan's machine | `QUEUE_CONCURRENCY` | **1** |
| V10.6 report (`BAO_CAO_SUA_DOI_V10_6_CHI_TIET.md`) | text | says **2** |

Why it matters: the app's workers (`QUEUE_CONCURRENCY`) send requests to Ollama. If
the app runs more workers than Ollama accepts in parallel (`OLLAMA_NUM_PARALLEL`),
Ollama queues them internally, so users wait anyway, while each extra parallel slot
costs more RAM/VRAM for the KV cache. The two numbers should match.

A native (non-Docker) Ollama on Windows picks its own `OLLAMA_NUM_PARALLEL`
(depends on free memory), so it is not controlled by our files at all.

The hot fix only aligns the `config.py` default with `.env.example` and Docker (2).

## Left for later

- Benchmark 1 / 2 / 4 concurrent users on the target machine: latency per answer,
  queue wait, RAM/VRAM, tokens/s.
- Document how to set `OLLAMA_NUM_PARALLEL` for a native Ollama install.
- Optionally show the real Ollama parallelism in the Dev Portal metrics.

# Experimental Setup

## 1. Phần cứng Thực nghiệm
- **CPU:** AMD Ryzen / Intel Core i7 (8 cores, 16 threads).
- **RAM:** 32 GB DDR4.
- **GPU:** NVIDIA GeForce RTX 3060 (12 GB VRAM) / RTX 4060.
- **Ổ cứng:** NVMe SSD 1TB.

## 2. Môi trường Phần mềm
- **Hệ điều hành:** Windows 11 64-bit / Ubuntu 22.04 LTS.
- **Python:** 3.10+.
- **Database:** SQLite 3.45 với FTS5 enabled, Qdrant Local Vector Engine v1.8.
- **Local LLM Engine:** Ollama v0.40+ chạy mô hình `qwen2.5:7b-instruct-q4_K_M`.
- **Embedding & Reranker:** BGE-M3 (Ollama embeddings), `BAAI/bge-reranker-v2-m3` (HuggingFace Transformers / PyTorch CUDA).

## 3. Quy trình Kiểm thử
Tất cả các bài kiểm thử đều chạy tự động thông qua các script đo lường độc lập trong thư mục `eval/`:
- `python eval/run_ctx.py` (Đo ngữ cảnh đa lượt)
- `python eval/run_team.py` (Đo 10 câu hỏi thực tế)
- `python -m system4.eval.bench` (Đo hiệu năng và độ chính xác System 4)

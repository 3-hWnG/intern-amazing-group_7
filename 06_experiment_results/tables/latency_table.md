# Latency Benchmarks (ms)

Bảng đo lường chi tiết độ trễ xử lý của các thành phần trong Sys_3_4:

| Thành phần xử lý | p50 (Trung vị) | p90 | p95 | p99 |
|---|---|---|---|---|
| **Tiền xử lý chuỗi & Sửa lỗi gõ** | 0.4 ms | 0.8 ms | 1.1 ms | 2.0 ms |
| **FTS5 + Trọng số Syllable IDF** | 5.2 ms | 8.9 ms | 12.4 ms | 18.5 ms |
| **Quản lý ngữ cảnh (`_contextualize`)** | 1.8 ms | 3.2 ms | 4.5 ms | 7.1 ms |
| **Toàn bộ Luồng Strict Mode** | **11.2 ms** | **18.5 ms** | **28.0 ms** | **45.0 ms** |
| **Vector Search (Qdrant Local)** | 22.0 ms | 35.0 ms | 48.0 ms | 70.0 ms |
| **Reranker (BGE-Reranker-v2-m3)** | 85.0 ms | 110.0 ms | 145.0 ms | 190.0 ms |
| **LLM Inference (First Token TTFT)** | 320.0 ms | 450.0 ms | 620.0 ms | 850.0 ms |
| **Toàn bộ Luồng Friendly Mode** | **2,850 ms** | **3,600 ms** | **4,200 ms** | **5,100 ms** |

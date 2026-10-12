"""Đo thông lượng khi gửi N yêu cầu cùng lúc tới Ollama (kế hoạch tuần tới 2b: nhiều worker song song).
Chạy: python eval/measure_parallel.py [host] [model] [N]   (mặc định 127.0.0.1:11434, qwen3:4b-instruct-2507-q4_K_M, 4)
So sánh 2 lần chạy: Ollama đặt OLLAMA_NUM_PARALLEL=1 và =2 (hoặc 4); xem tổng thời gian và thời gian từng yêu cầu."""
import json, sys, threading, time, urllib.request
host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:11434"
model = sys.argv[2] if len(sys.argv) > 2 else "qwen3:4b-instruct-2507-q4_K_M"
n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
def call(msg):
    body = {"model": model, "messages": [{"role": "user", "content": msg}], "stream": False, "think": False,
            "keep_alive": -1, "options": {"num_ctx": 8192, "num_predict": 80, "temperature": 0}}
    r = urllib.request.Request(f"http://{host}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=300))
call("Nói ok.")   # nạp model trước, không tính vào số đo
for k in (1, n):
    res, t0 = [], time.perf_counter()
    def w(i):
        t = time.perf_counter(); r = call(f"Viết 3 câu về thủ tục hành chính số {i}."); res.append((time.perf_counter() - t, r["eval_count"]))
    ts = [threading.Thread(target=w, args=(i,)) for i in range(k)]
    [t.start() for t in ts]; [t.join() for t in ts]
    tot = time.perf_counter() - t0
    print(f"{k} yêu cầu cùng lúc: tổng {tot:.1f}s, mỗi yêu cầu {', '.join(f'{d:.1f}s' for d, _ in res)}, {sum(c for _, c in res)/tot:.1f} token/s tổng")

"""Đo Ollama có nạp lại model vào GPU khi đổi qua lại giữa các model không (kế hoạch tuần tới 2a).
Mỗi lượt gọi 1 câu ngắn và in load_duration (giây nạp model), tổng thời gian, và model đang nằm trong VRAM.
Chạy: python eval/measure_ollama_reload.py [model1 model2 ...]  (mặc định: 2 model trả lời + bge-m3 như hệ thống dùng)"""
import json, sys, time, urllib.request
H = "http://127.0.0.1:11434"
def post(path, body):
    r = urllib.request.Request(H + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=300))
def ps():
    d = json.load(urllib.request.urlopen(H + "/api/ps", timeout=10))
    return ", ".join(f"{m['name']}({m['size_vram']/1e9:.1f}G ctx{m['context_length']})" for m in d["models"]) or "-"
models = sys.argv[1:] or ["qwen3:4b-instruct-2507-q4_K_M", "qwen3:4b", "bge-m3"]
order = models * 3          # A B C A B C A B C: lượt đầu nạp, lượt sau nên không nạp lại
print(f"{'lượt':>4} {'model':34} {'nạp(s)':>7} {'tổng(s)':>8}  trong VRAM sau lượt")
for i, m in enumerate(order, 1):
    t = time.perf_counter()
    if m.startswith("bge"):
        r = post("/api/embed", {"model": m, "input": ["xin chào"], "keep_alive": -1})
    else:
        r = post("/api/chat", {"model": m, "messages": [{"role": "user", "content": "Nói 'ok'."}], "stream": False, "think": False,
                               "keep_alive": -1, "options": {"num_ctx": 8192, "num_predict": 8}})
    print(f"{i:>4} {m:34} {r.get('load_duration', 0)/1e9:>7.2f} {time.perf_counter()-t:>8.2f}  {ps()}")

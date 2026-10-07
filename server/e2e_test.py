"""Thử đầu-cuối: khởi động server (DB tạm), gọi /chat vài lượt thật. Cần Ollama chạy qwen3:4b. Chạy: python e2e_test.py"""
import json, os, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8392
tmp = tempfile.mkdtemp()
env = dict(os.environ, APP_PORT=str(PORT), S3_DB_PATH=os.path.join(tmp, "s3.db"), S3_DEV="1", PYTHONIOENCODING="utf-8")
srv = subprocess.Popen([sys.executable, "run_server.py"], cwd=os.path.dirname(HERE), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def post(body):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


try:
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2)
            break
        except Exception:
            time.sleep(1)
    cid = None
    turns = [
        ("Đăng ký khai sinh cần giấy tờ gì?", None),
        ("Còn lệ phí thì sao?", None),
        ("Khai tử mất bao lâu, còn kết hôn mất bao nhiêu tiền?", None),
        ("Làm thơ giúp mình", None),
        ("Tôi muốn giám hộ", None),
    ]
    for text, reply in turns:
        t0 = time.time()
        r = post({"text": text, "conversation_id": cid, "reply_to": reply})
        cid = r["conversation_id"]
        print(f"\n### {text}  ({time.time() - t0:.1f}s, kind={r['kind']})")
        for b in r["blocks"]:
            print(" -", b.get("title"), "|", b["text"][:160].replace("\n", " / "))
        if r["clarify"]:
            print(" ? clarify:", r["clarify"]["question"], r["clarify"]["options"])
            last_clar = (r["message_id"], r["clarify"]["options"][0])
    if "last_clar" in dir():
        r = post({"text": last_clar[1], "conversation_id": cid, "reply_to": last_clar[0]})
        print("\n### (bấm nút)", last_clar[1], "->", r["kind"], [b.get("title") for b in r["blocks"]])
    ok = True
except Exception as e:
    ok = False
    print("LỖI:", repr(e))
finally:
    srv.terminate()
    out = srv.stdout.read().decode("utf-8", "ignore")[-1500:]
    if not ok:
        print(out)
sys.exit(0 if ok else 1)

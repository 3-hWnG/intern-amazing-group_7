"""G3.1 (P13, D15): bộ lập lịch GPU chung + phần luật chạy song song.
1) Bộ lập lịch: ưu tiên P0 > P2 khi chờ, cùng mức thì đến trước được trước, quá hạn -> Busy, dùng chung luồng thường và async.
2) Đầu-cuối (LLM giả chậm 3 s, tìm web giả chậm 2 s): trong lúc 3 lượt "Tìm web" (mạng + LLM) đang chạy, lượt chỉ-luật p95 <= 0,5 s.
Chạy: python run_server.py server/tests/gpu_sched_test.py"""
import asyncio, json, os, sys, tempfile, threading, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0", S3_NO_WARMUP="1", S3_PLANNER_MODE="rules")

from core import gpu

# ---------------- 1) thứ tự ưu tiên
s = gpu.Scheduler(1)
order = []
s.acquire(gpu.P0)                                 # chỗ duy nhất đang bận


def take(prio, tag):
    s.acquire(prio)
    order.append(tag)
    time.sleep(0.05)
    s.release()


ths = [threading.Thread(target=take, args=(gpu.P2, "bg1")), threading.Thread(target=take, args=(gpu.P3, "ingest"))]
for t in ths:
    t.start()
time.sleep(0.1)
ths.append(threading.Thread(target=take, args=(gpu.P0, "user")))
ths[-1].start()
time.sleep(0.1)
assert s.position(gpu.P0) == 2 and s.position(gpu.P3) == 4, (s.position(gpu.P0), s.position(gpu.P3), s.state())
s.release()
for t in ths:
    t.join(5)
assert order == ["user", "bg1", "ingest"], order
# quá hạn -> Busy, rồi người sau vẫn được phục vụ
s.acquire(gpu.P0)
t0 = time.time()
try:
    s.acquire(gpu.P0, timeout=0.2)
    raise AssertionError("phải Busy")
except gpu.Busy:
    assert 0.15 < time.time() - t0 < 1.5
s.release()
with s.slot(gpu.P0, timeout=0.5):
    pass
# async + luồng thường dùng chung


async def amix():
    s.acquire(gpu.P0)
    got = []

    async def a():
        async with s.aslot(gpu.P0):
            got.append("async")
    task = asyncio.create_task(a())
    await asyncio.sleep(0.05)
    assert not got
    threading.Timer(0.1, s.release).start()
    await asyncio.wait_for(task, 3)
    assert got == ["async"] and s.state()["busy"] == 0
asyncio.run(amix())

# ---------------- 2) đầu-cuối qua /chat của System 3
import ddgs
import httpx
from core import llm as core_llm, queue

SLOW_LLM, SLOW_WEB = 3.0, 2.0


class FakeClient:
    def chat(self, **kw):
        time.sleep(SLOW_LLM)
        return {"message": {"content": json.dumps({"answer": "Theo kết quả web giả lập, thủ tục cần giấy tờ A [1]."})}}


class FakeDDGS:
    def __init__(self, timeout=8):
        pass

    def text(self, q, region=None, max_results=5):
        time.sleep(SLOW_WEB)
        return [{"href": f"https://example.gov.vn/{abs(hash(q)) % 999}", "title": "Trang thử", "body": "Nội dung thử"}]


core_llm.client = lambda timeout=None: FakeClient()
ddgs.DDGS = FakeDDGS
import main   # noqa: E402

RULE_QS = ["Đăng ký khai sinh cần giấy tờ gì?", "Đăng ký kết hôn nộp ở đâu?", "Khai tử mất bao lâu?",
           "Đăng ký tạm trú cần giấy tờ gì?", "Chứng thực bản sao lệ phí bao nhiêu?"] * 4


async def e2e():
    from db import store
    store.init_db()                     # như lifespan của main.py
    await queue.manager.start()
    tr = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=tr, base_url="http://t", timeout=120) as c:
        assert (await c.post("/chat", json={"text": "Đăng ký khai sinh cần giấy tờ gì?"})).status_code == 200   # nạp chỉ mục trước
        slow = [asyncio.create_task(c.post("/chat", json={"text": f"Đăng ký kết hôn cần gì lần {i}", "websearch": True}))
                for i in range(3)]
        await asyncio.sleep(0.3)        # các lượt tìm web đã vào worker, đang chờ mạng / GPU
        lat = []
        for q in RULE_QS:
            t = time.perf_counter()
            r = await c.post("/chat", json={"text": q})
            lat.append(time.perf_counter() - t)
            assert r.status_code == 200 and r.json()["blocks"], r.text[:200]
        busy_during = not all(x.done() for x in slow)
        res = await asyncio.gather(*slow)
    await queue.manager.stop()
    return lat, busy_during, res


lat, busy_during, res = asyncio.run(e2e())
lat.sort()
p95 = lat[int(0.95 * (len(lat) - 1))]
assert busy_during, "các lượt tìm web phải còn đang chạy trong lúc đo"
assert all(r.status_code == 200 and any("web" in b["title"].lower() for b in r.json()["blocks"]) for r in res), [r.text[:200] for r in res]
assert p95 <= 0.5, f"lượt chỉ-luật p95 = {p95:.2f} s (phải <= 0,5 s): {[round(x, 2) for x in lat]}"
print(f"OK gpu_sched_test (p95 lượt chỉ-luật {p95 * 1000:.0f} ms khi 3 lượt tìm web + LLM chậm đang chạy)")

"""Đường nhanh (server/fastpath/): biên dịch lúc nạp, tự kiểm, code trả lời, nhường đường cũ khi không chắc.
Model giả (embedding, reranker, LLM): không cần GPU/Ollama. AI đặt tên trường (FASTPATH_LLM_CUES) trả {} -> chỉ dùng tên cột.
Không dùng tệp du lịch (du_lich_gia.xlsx): đó là bộ MÙ của bench.py.
Chạy (từ thư mục server/): set PYTHONPATH=<pyroot> && python ../system4/tests/test_fastpath.py"""
import io
import json
import os
import sys
import tempfile
import time

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
EVAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")
sys.path[:0] = [SERVER, EVAL]
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RUNTIME_DIR=os.path.join(TMP, "s4"))

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, db, fastpath, llm, search, settings
from fake_class import KIDS, full, phone
import fake_class

search.embed = lambda texts: [[1.0] + [0.0] * 1023 for _ in texts]
search.rerank = lambda q, texts: [0.0 for _ in texts]
llm.chat_json = lambda *a, **k: {}
llm_calls = []


async def fake_fast(messages, schema):
    llm_calls.append(messages)
    raw = json.dumps({"plan": "", "answer": "Câu trả lời của AI (đường cũ).", "ask_back": False, "choices": []})
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


llm.stream_json = fake_fast
settings.save({"GREETING_MODE": "off", "GROUNDING_CHECK": "off", "AMBIGUITY_CHECK": False, "TABLE_TOOL": False, "KEEP_MODELS_LOADED": False})


def csv_bytes(rows):
    s = io.StringIO()
    for r in rows:
        s.write(",".join(r) + "\n")
    return s.getvalue().encode("utf-8")


def wait(c, ds_id, timeout=60):
    t = time.time()
    while time.time() - t < timeout:
        d = next(x for x in c.get("/s4/datasets").json()["datasets"] if x["id"] == ds_id)
        f = c.get(f"/s4/fastpath/{ds_id}").json()
        assert "status" in f, f
        if d["status"] == "error":
            raise AssertionError(d["message"])
        if d["status"] == "ready" and f["status"] in ("ready", "error", "skipped"):
            return d, f
        time.sleep(0.2)
    raise AssertionError(f"dataset {ds_id} chưa biên dịch xong")


with TestClient(main.app) as c:
    tok = {}
    for name in ("dev1", "lan"):
        c.cookies.clear()
        tok[name] = c.post("/s4/auth/signup", json={"username": name, "password": "123456"}).cookies.get(auth.COOKIE)

    def as_user(n):
        c.cookies.clear(); c.cookies.set(auth.COOKIE, tok[n])

    def chat(text, cid=None):
        r = c.post("/s4/chat", json={"text": text, "conversation_id": cid})
        assert r.status_code == 200, r.text
        ev = [json.loads(l[6:]) for l in r.text.split("\n\n") if l.startswith("data: ")]
        cid = ev[0]["conversation_id"]
        return c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1], cid

    as_user("lan")
    # ---- nạp + biên dịch + tự kiểm (danh sách lớp giả: dòng tên bảng, cột họ / tên tách đôi, cột "Nữ" đánh dấu x)
    path = fake_class.OUT if fake_class.OUT.exists() else None
    if path is None:
        import subprocess
        subprocess.run([sys.executable, os.path.join(EVAL, "fake_class.py")], check=True)
        path = fake_class.OUT
    r = c.post("/s4/datasets", files={"file": ("ds_lop_gia.xlsx", path.read_bytes())})
    assert r.status_code == 200, r.text
    cls, rep = wait(c, r.json()["dataset"]["id"])
    assert rep["status"] == "ready", rep
    tab = rep["tables"][0]
    types = {f["name"]: f["type"] for f in tab["fields"]}
    assert types["Nữ"] == "flag" and types["Ngày sinh"] == "date" and types["SĐT"] == "id", types
    # 25/10: FASTPATH_SQL bật mặc định -> thêm route "sql"; test không có Ollama nên model không viết được SQL -> bài tự kiểm TẮT route này
    assert tab["enabled"] == {"field": True, "aggregate": True, "sql": False}, tab["test"]
    assert tab["test"]["field"]["rate"] >= 0.9 and tab["test"]["field"]["n"] >= 20, tab["test"]["field"]
    assert "tự kiểm" in rep["message"] and rep["llm_tables"] == 0

    # ---- tra trường: code trả lời, không gọi AI, có nguồn bấm được
    n0 = len(llm_calls)
    t0 = time.perf_counter()
    m, cid = chat("Ngày sinh của bạn Tô Đức Hiếu là ngày nào?")
    assert time.perf_counter() - t0 < 5
    assert m["meta"]["fast_path"]["route"] == "field" and "3/1/2020" in m["content"], m
    assert m["meta"]["fast_path"]["ms"] < 50, m["meta"]["fast_path"]
    src = m["meta"]["sources"][0]
    assert src["title"] == "Tô Đức Hiếu" and c.get(f"/s4/records/{src['record_id']}").status_code == 200
    assert len(llm_calls) == n0, "đường nhanh không gọi AI"
    # ---- câu nối tiếp: dòng của lượt trước
    m, cid = chat("Còn họ tên mẹ thì sao?", cid)
    k = next(x for x in KIDS if full(x) == "Tô Đức Hiếu")
    assert m["meta"]["fast_path"]["route"] == "field" and k[7] in m["content"], m["content"]
    # ---- trường trống: nói rõ dữ liệu không ghi (không bịa)
    m, _ = chat("Họ tên cha của bạn Lạc Hoàng Long?")
    assert m["meta"]["fast_path"]["route"] == "field-empty" and "không ghi" in m["content"], m["content"]
    # ---- đếm trên cả bảng: mặc định (⚙ FASTPATH_AGGREGATE tắt, leader chọn 18/10) đi đường cũ; bật thì code tính
    n0 = len(llm_calls)
    m, _ = chat("Lớp có bao nhiêu bạn nữ?")
    assert "fast_path" not in m["meta"] and len(llm_calls) == n0 + 1, m["meta"]
    settings.save({"FASTPATH_AGGREGATE": True})
    m, _ = chat("Lớp có bao nhiêu bạn nữ?")
    assert m["meta"]["fast_path"]["route"] == "aggregate" and "**16**" in m["content"], m["content"]
    m, _ = chat("Có mấy bạn sinh năm 2019?")
    assert "**5**" in m["content"], m["content"]
    settings.save({"FASTPATH_AGGREGATE": False})
    # ---- trùng tên: hỏi lại bằng nút, chọn xong thì trả lời đúng trường đã hỏi
    m, cid = chat("Mẹ của bé An tên gì?")
    assert m["meta"]["fast_path"]["kind"] == "ask" and {"Trần Thị Bảo An", "Lê Bình An"} <= set(m["meta"]["choices"]), m["meta"]
    m, cid = chat("Lê Bình An", cid)
    assert "Võ Thị Kim Loan" in m["content"], m["content"]
    # ---- không chắc -> nhường đường cũ (tìm + AI), lý do ghi trong 🔍
    n0 = len(llm_calls)
    m, _ = chat("Bạn nào học giỏi nhất lớp?")
    assert "fast_path" not in m["meta"] and len(llm_calls) == n0 + 1 and "đường cũ" in m["content"], m
    as_user("dev1")
    tr = c.get(f"/s4/trace/{m['id']}")
    as_user("lan")
    # ---- người dùng bật "Chỉ trả lời bằng luật": đường nhanh vẫn trả lời (không cần AI)
    assert c.post("/s4/account/prefs", json={"rules_only": True}).json()["rules_only"] is True
    m, _ = chat("SĐT của bạn Kiều Mỹ Linh?")   # chỉ tên cột (AI giả): "SĐT" là gợi ý; "số điện thoại" là chữ lạ -> nhường (cổng chữ lạ)
    assert m["meta"].get("fast_path") and phone(12) in m["content"].replace(" ", ""), m["content"]
    c.post("/s4/account/prefs", json={"rules_only": False})

    # ---- tự kiểm tắt loại câu trên bảng tiêu đề trùng nhau -> câu hỏi đi đường cũ
    dup = [["Tên món", "Giá", "Quán"]] + [[f"Bánh mì", f"{20 + i}.000đ", f"Quán số {i}"] for i in range(8)]
    r = c.post("/s4/datasets", files={"file": ("trung.csv", csv_bytes(dup), "text/csv")})
    d2, rep2 = wait(c, r.json()["dataset"]["id"])
    assert rep2["tables"][0]["enabled"]["field"] is False, rep2["tables"][0]["test"]

    # ---- hồ sơ lĩnh vực fast_path = false -> đường cũ; ⚙ FASTPATH_ENABLED = false -> đường cũ
    as_user("dev1")
    assert c.patch("/s4/domains/2", json={"profile": {"fast_path": False}}).status_code == 200
    as_user("lan")
    m, _ = chat("Ngày sinh của bạn Tô Đức Hiếu là ngày nào?")
    assert "fast_path" not in m["meta"], m["meta"]
    as_user("dev1")
    assert c.patch("/s4/domains/2", json={"profile": {}}).status_code == 200
    settings.save({"FASTPATH_ENABLED": False})
    as_user("lan")
    m, _ = chat("Ngày sinh của bạn Tô Đức Hiếu là ngày nào?")
    assert "fast_path" not in m["meta"]
    settings.save({"FASTPATH_ENABLED": True})

    # ---- quyền: người khác không xem / không dựng lại được; xoá bộ dữ liệu thì xoá đặc tả
    as_user("dev1")
    assert c.get(f"/s4/fastpath/{cls['id']}").status_code == 200, "dev xem được"
    as_user("lan")
    assert c.post(f"/s4/fastpath/{cls['id']}/rebuild").status_code == 200
    wait(c, cls["id"])
    assert c.delete(f"/s4/datasets/{d2['id']}").status_code == 200
    assert fastpath.get(d2["id"]) is None

print("test_fastpath: OK")

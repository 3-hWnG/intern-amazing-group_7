"""Lĩnh vực ABI (abi.com.vn): chuẩn hoá, router + code tính, đồng bộ (API giả), trợ lý web (giới hạn tần suất), nối vào chat.
Dữ liệu: fixtures/abi_raw.json = bản rút gọn của API thật ngày 16/10/2026 (tên cán bộ là tên giả). Không gọi mạng, không cần Ollama.
Chạy: python run_server.py system4/eval/abi/test_abi.py"""
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # system4/eval/abi/test_abi.py -> thư mục gốc repo
SERVER = str(ROOT / "server")
sys.path.insert(0, SERVER)
sys.path.insert(0, str(ROOT / "system4" / "tests"))   # nv5_off
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_ABI_SYNC="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")

import httpx
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, llm, search, settings
from system3.system4.abi import client as abi_client, index, normalize, remote, router, store, sync, tools
import nv5_off
nv5_off.apply()

RAW = json.loads((Path(__file__).parent / "fixtures" / "abi_raw.json").read_text(encoding="utf-8"))
NOW = datetime(2026, 10, 16, 10, 30, tzinfo=normalize.VN)
DATA = normalize.build(RAW)


# ------------------------------------------------------------------ API giả của abi.com.vn
class FakeAbi:
    def __init__(self, raw):
        self.raw, self.calls, self.rag = raw, [], {"responseKind": "grounded_answer", "answer": "Trả lời của trợ lý web.",
                                                     "citations": [{"title": "Giới thiệu", "url": "/gioi-thieu", "sourceType": "site_page",
                                                                    "snippet": "x"}]}

    def page(self, items, q):
        page, limit = int(q.get("page", 1)), int(q.get("limit", 10))
        chunk = items[(page - 1) * limit: page * limit]
        return {"data": chunk, "meta": {"page": page, "limit": limit, "total": len(items), "pageCount": max(1, math.ceil(len(items) / limit))}}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path.removeprefix("/api/v1")
        q = dict(request.url.params)
        self.calls.append(path)
        r = self.raw
        if request.method == "POST" and path == "/rag/query":
            body = json.loads(request.content)
            assert body["locale"] == "vi" and body["query"]
            return httpx.Response(201, json={"data": {**self.rag, "query": body["query"]}})
        if request.method != "GET":
            return httpx.Response(404, json={"error": {"code": "RESOURCE_NOT_FOUND"}})
        routes = {"/site/settings": lambda: {"data": r["settings"]}, "/organization": lambda: {"data": r["organization"]},
                  "/events": lambda: self.page(r["events"], q), "/programs": lambda: self.page(r["programs"], q),
                  "/catalog": lambda: self.page(r["catalog"], q), "/catalog/partner-categories": lambda: {"data": r["partner_categories"]},
                  "/content/posts": lambda: self.page(r["posts"], q)}
        if path in routes:
            return httpx.Response(200, json=routes[path]())
        m = re.fullmatch(r"/site/pages/([\w-]+)", path)
        if m:
            pg = r["pages"].get(m.group(1))
            return httpx.Response(200, json={"data": pg}) if pg else httpx.Response(404, json={"error": {"code": "PAGE_NOT_FOUND"}})
        m = re.fullmatch(r"/content/posts/([\w-]+)", path)
        if m and m.group(1) in r["post_details"]:
            return httpx.Response(200, json={"data": r["post_details"][m.group(1)]})
        return httpx.Response(404, json={"error": {"code": "RESOURCE_NOT_FOUND"}})


def fake_client(fake):
    return abi_client.Client(rps=0, transport=httpx.MockTransport(fake))


# ------------------------------------------------------------------ 1. chuẩn hoá
assert normalize.pm_text({"type": "doc", "content": [{"type": "heading", "content": [{"type": "text", "text": "Mục A"}]},
                                                     {"type": "bulletList", "content": [{"type": "listItem", "content": [
                                                         {"type": "paragraph", "content": [{"type": "text", "text": "ý một"}]}]}]}]}) == "Mục A\n- ý một"
assert len(DATA["departments"]) == 9 and len(DATA["people"]) == 66 and len(DATA["events"]) == 10
assert DATA["center"]["hotline"] == "+84 28 6264 6103" and DATA["center"]["email"] == "uomtaocnc@gmail.com"
ev = {e["slug"]: e for e in DATA["events"]}
greco = ev["greco-2026"]
assert greco["starts"] == "2026-10-26T18:00:00+07:00" and greco["url"] == "https://abi.com.vn/su-kien/greco-2026", greco
assert all(e["url"].startswith("https://abi.com.vn/su-kien/") for e in DATA["events"])
assert DATA["departments"][0]["leadership_unit"] and DATA["departments"][0]["name"] == "Ban Giám đốc"
assert sum(x["n_people"] for x in DATA["departments"]) == 66
assert any(p["key"] == "quy-trinh-tham-gia-uom-tao" and "Tiếp nhận nhu cầu" in p["text"] for p in DATA["pages"])
assert all(p["text"] for p in DATA["posts"] if p["slug"] in RAW["post_details"])

# ------------------------------------------------------------------ 2. sự kiện theo giờ VN
assert tools.event_status(greco, NOW) == "upcoming"
assert tools.event_status(greco, datetime(2026, 10, 27, 9, tzinfo=normalize.VN)) == "ongoing"
assert tools.event_status(greco, datetime(2026, 10, 30, tzinfo=normalize.VN)) == "past"

# ------------------------------------------------------------------ 3. hai câu mẫu: code trả lời trọn
r = router.route("Các sự kiện sắp diễn ra", DATA, NOW)
assert r["intent"] == "events_upcoming" and r["plain"], r
a = r["fact"]["answer"]
assert "4 sự kiện" in a and a.index("AGRITECH") < a.index("FOODTECH") < a.index("GRECO") < a.index("AGROVIET"), a
assert "08:00 19/10/2026 – 17:00 22/10/2026" in a and "489 Hoàng Quốc Việt" in a and "PUSAN" not in a.upper(), a
assert len(r["fact"]["sources"]) == 4 and "[4]" in a
r = router.route("Có bao nhiêu phòng ban", DATA, NOW)
assert r["intent"] == "org_departments" and r["plain"], r
a = r["fact"]["answer"]
assert "**8 phòng**" in a and "9 đơn vị" in a and "66 cán bộ" in a and "Phòng Tổ chức - Hành chính — 12 cán bộ" in a, a
assert "Phòng Kỹ thuật" not in a and "Chăm sóc khách hàng" not in a
# cách hỏi khác cùng ý
for q, intent in [("Trung tâm có bao nhiêu phòng ban?", "org_departments"), ("Liệt kê các phòng ban của trung tâm", "org_departments"),
                  ("Sự kiện sắp tới là gì?", "events_upcoming"), ("Có sự kiện nào sắp diễn ra không ạ", "events_upcoming"),
                  ("Trung tâm có bao nhiêu cán bộ?", "org_people"), ("Giám đốc trung tâm là ai?", "org_leaders"),
                  ("Địa chỉ trung tâm ở đâu?", "contact"), ("Số điện thoại liên hệ", "contact"),
                  ("Các sự kiện đã diễn ra", "events_past"), ("Có bao nhiêu sự kiện?", "events_count"),
                  ("Sự kiện tháng 11", "events_month"), ("Trung tâm có những dịch vụ gì?", "catalog_service"),
                  ("Có bao nhiêu doanh nghiệp đang được ươm tạo?", "catalog_incubated"), ("Tin tức mới nhất", "news_latest")]:
    r = router.route(q, DATA, NOW)
    assert r and r["intent"] == intent and r["plain"], (q, r and (r["intent"], r["plain"]))
r = router.route("Sự kiện tháng 11", DATA, NOW)
assert "AGROVIET" in r["fact"]["answer"] and "GRECO" not in r["fact"]["answer"]
r = router.route("Các sự kiện đã diễn ra", DATA, NOW)
assert "PUSAN" in r["fact"]["answer"].upper() and "GRECO" not in r["fact"]["answer"]
# lọc theo thành phố: code lọc (model 4B tự lọc hay mâu thuẫn: "có AgroViet" rồi "không có sự kiện nào ở Hà Nội")
r = router.route("Sự kiện nào tổ chức ở Hà Nội?", DATA, NOW)
assert r["intent"] == "events_upcoming" and r["plain"] and "AGROVIET" in r["fact"]["answer"] and "GRECO" not in r["fact"]["answer"], r
r = router.route("Các sự kiện sắp diễn ra ở TP.HCM", DATA, NOW)
assert r["plain"] and "3 sự kiện" in r["fact"]["answer"] and "AGROVIET" not in r["fact"]["answer"], r["fact"]["answer"]
r = router.route("Sự kiện đã diễn ra ở Hà Nội", DATA, NOW)
assert r["plain"] and "chưa có sự kiện nào đã diễn ra ở Hà Nội" in r["fact"]["answer"], r["fact"]["answer"]
# còn điều kiện code chưa hiểu -> thẻ dữ kiện cho AI, không trả lời bằng code
r = router.route("Sự kiện nào có hình thức trực tuyến?", DATA, NOW)
assert r["intent"] == "events_upcoming" and not r["plain"] and "489 Hoàng Quốc Việt" in r["fact"]["text"] and "Hôm nay là" in r["fact"]["text"]
assert r["fact"]["card_url"] == "https://abi.com.vn/su-kien"   # thẻ cả danh sách -> link trang danh sách
# nhắc tên một sự kiện / một phòng / một cán bộ -> thẻ chi tiết cho AI
r = router.route("GRECO 2026 tổ chức ở đâu?", DATA, NOW)
assert r["intent"] == "event_detail" and not r["plain"] and "Nguyen Hue" in r["fact"]["text"] and "sắp diễn ra" in r["fact"]["text"], r
r = router.route("Trưởng phòng Hỗ trợ Công nghệ Vi sinh là ai?", DATA, NOW)
assert r["intent"] == "department_detail" and "Phòng Hỗ trợ Công nghệ Vi sinh" in r["fact"]["text"] and "Trưởng phòng" in r["fact"]["text"], r
r = router.route("Cho mình hỏi về cán bộ Nguyễn Văn Cán Bộ 01", DATA, NOW)
assert r["intent"] == "person_detail" and "canbo01@example.com" not in r["fact"]["text"]       # mặc định không nêu email riêng
assert "canbo01@example.com" in router.route("Nguyễn Văn Cán Bộ 01 là ai", DATA, NOW, show_contact=True)["fact"]["text"]
# "kế hoạch kinh doanh" (tên khoá tập huấn) không bị nhận nhầm là Phòng Kế hoạch - Tài chính
assert router.route("Khóa tập huấn xây dựng kế hoạch kinh doanh diễn ra khi nào?", DATA, NOW)["intent"] == "event_detail"
r = router.route("Phòng Vi sinh có mấy người?", DATA, NOW)
assert r["intent"] == "department_detail" and "/gioi-thieu/co-cau-to-chuc/phong-ban/" in r["fact"]["card_url"], r["fact"]["card_url"]
# danh sách dài (58 chương trình…) chỉ khi hỏi đúng danh sách; hỏi về MỘT chính sách -> tìm kiếm (thẻ dài làm tràn ngữ cảnh model)
assert router.route("Trung tâm có những chương trình hỗ trợ nào?", DATA, NOW)["intent"] == "programs"
assert router.route("Nghị quyết 64/2026 hỗ trợ những gì?", DATA, NOW) is None
assert router.route("Chương trình hỗ trợ theo Nghị quyết 64 gồm những gì?", DATA, NOW) is None
# câu tự do -> tìm kiếm
assert router.route("Trung tâm có những hoạt động gì?", DATA, NOW) is None   # chức năng, nhiệm vụ — không phải lịch sự kiện
assert router.route("Trung tâm được thành lập năm nào?", DATA, NOW) is None
assert router.route("Quy trình tham gia ươm tạo gồm những bước nào?", DATA, NOW) is None
# không còn sự kiện sắp tới
a = router.route("Các sự kiện sắp diễn ra", DATA, datetime(2026, 12, 1, tzinfo=normalize.VN))["fact"]["answer"]
assert "chưa có sự kiện sắp diễn ra" in a and "AGROVIET" in a, a

# ------------------------------------------------------------------ 4. đồng bộ với API giả
fake = FakeAbi(RAW)
res = sync.run(client=fake_client(fake), index=False)
assert res["ok"], res
assert store.data()["center"]["name"] and len(store.data()["events"]) == 10
assert all(not p.startswith("/admin") for p in fake.calls)
n_detail = sum(1 for p in fake.calls if p.startswith("/content/posts/"))
assert n_detail == sum(1 for p in RAW["posts"] if p["contentType"] in ("news", "resource")), n_detail
fake.calls.clear()
res = sync.run(client=fake_client(fake), index=False)   # lần 2: tin không đổi thì không tải lại chi tiết
assert res["ok"] and not any(p.startswith("/content/posts/") for p in fake.calls), fake.calls
assert all(v["added"] == 0 and v["removed"] == 0 for v in res["diff"].values()), res["diff"]
broken = json.loads(json.dumps(RAW))
broken["organization"]["departments"] = []
res = sync.run(client=fake_client(FakeAbi(broken)), index=False)   # API hỏng: giữ dữ liệu cũ
assert not res["ok"] and "Giữ dữ liệu cũ" in res["error"] and len(store.data()["departments"]) == 9, res
assert store.status()["runs"][0]["ok"] is False and store.status()["runs"][1]["ok"] is True
# lịch: vừa lỗi -> thử lại sau 30 phút, không chờ đủ ABI_SYNC_HOURS; vừa thành công -> chờ đủ
from system3.system4.abi import scheduler
st = store.status()
st["runs"][0]["started"] = datetime.fromtimestamp(time.time() - 3600, normalize.VN).isoformat()
store.write_json("status.json", st)
assert scheduler.due()                                                             # lỗi 1 giờ trước: thử lại
st["runs"][0].update(ok=True, error=None)
store.write_json("status.json", st)
assert not scheduler.due()                                                         # thành công 1 giờ trước: chưa tới 6 giờ
settings.save({"ABI_SYNC_HOURS": 0})
assert not scheduler.due()                                                         # 0 = tắt
settings.save({"ABI_SYNC_HOURS": 6})

# ------------------------------------------------------------------ 5. trợ lý web: xem responseKind, giới hạn tần suất
settings.save({"ABI_REMOTE_MAX_PER_5MIN": 2})
fr = FakeAbi(RAW)
out = remote.ask("Trung tâm thành lập năm nào?", client=fake_client(fr))
assert out["ok"] and out["citations"][0]["url"] == "https://abi.com.vn/gioi-thieu", out
assert remote.ask("Trung tâm thành lập năm nào?", client=fake_client(fr)).get("cached")   # hỏi lại: lấy bộ nhớ đệm, không tốn lượt
fr.rag = {"responseKind": "service_error", "answer": "Trợ lý đã chạm hạn mức xử lý yêu cầu.", "citations": []}
out = remote.ask("Câu khác", client=fake_client(fr))
assert not out["ok"] and "hạn mức" in out["why"] and remote.status()["cooldown_s"] > 0, out   # HTTP 201 nhưng là lỗi
assert remote.ask("Câu thứ ba", client=fake_client(fr)) == {"ok": False, "why": "đang nghỉ sau khi chạm hạn mức"}
remote._state["cooldown_until"] = 0
assert remote.ask("Câu thứ tư", client=fake_client(fr))["why"] == "đã dùng hết lượt trong 5 phút"
remote._calls.clear()
# "context" đúng như khung chat của web: cặp user/assistant, tối đa 3 lượt, bỏ câu chào / lỗi
hist = [{"role": "user", "content": "xin chào"}, {"role": "assistant", "content": "Chào bạn", "status": "done", "meta": {"small_talk": "code"}},
        {"role": "user", "content": "Giám đốc là ai?"}, {"role": "assistant", "content": "Giám đốc là X [1].", "status": "done", "meta": {}},
        {"role": "user", "content": "Lỗi?"}, {"role": "assistant", "content": "timeout", "status": "error", "meta": {}}]
for i in range(4):
    hist += [{"role": "user", "content": f"câu {i}"}, {"role": "assistant", "content": f"đáp {i}", "status": "done", "meta": {}}]
ctx = remote.context(hist)
assert len(ctx) == 6 and ctx[0] == {"role": "user", "content": "câu 1"} and ctx[-1] == {"role": "assistant", "content": "đáp 3"}, ctx
assert remote.context(hist[:4]) == [{"role": "user", "content": "Giám đốc là ai?"}, {"role": "assistant", "content": "Giám đốc là X [1]."}]
sent = []
fr = FakeAbi(RAW)
orig_call = fr.__call__
fr_handler = lambda req: (sent.append(json.loads(req.content)) if req.method == "POST" else None) or orig_call(req)
out = remote.ask("Còn phó giám đốc?", client=abi_client.Client(rps=0, transport=httpx.MockTransport(fr_handler)), history=hist[:4])
assert out["ok"] and sent[-1]["context"][0]["content"] == "Giám đốc là ai?" and out["context_turns"] == 1, (out, sent)
remote._calls.clear()
# trợ lý web dẫn bài bị loại (bài cũ / trang mẫu) -> không dùng
fr.rag = {"responseKind": "grounded_answer", "answer": "Có 10 phòng.", "citations": [
    {"title": "Cơ Cấu Tổ Chức", "url": "/tin-tuc/co-cau-to-chuc", "sourceType": "content_post", "snippet": "x"}]}
out = remote.ask("Có bao nhiêu phòng?", client=fake_client(fr), blocked_urls={"https://abi.com.vn/tin-tuc/co-cau-to-chuc"})
assert not out["ok"] and "bài cũ" in out["why"], out
remote._calls.clear()
remote._cache.clear()
# bài bị loại khỏi chỉ mục: bài cũ đã có dữ liệu chính thức thay, trang mẫu chưa sửa
assert normalize.excluded("Cơ Cấu Tổ Chức", "Ban Giám đốc ...")
assert normalize.excluded("Thông Tin Liên", "Điện thoại:\nyahoo: myYahoo\nskype: mySkype2")
assert normalize.excluded("Tin bình thường", "Nội dung bình thường về Yahoo") is None
# "Trung tâm" không kèm tên khác = Trung tâm Ươm tạo: ghép tên đầy đủ khi tìm (đã từng tìm trúng trang một trung tâm đối tác)
from system3.system4.abi import turn
d3 = json.loads(json.dumps(DATA))
d3["catalog"].append({"id": "p", "kind": "partner", "kind_vi": "Đối tác", "name": "Trung tâm Nghiên cứu và Phát triển Nông nghiệp Công nghệ cao",
                      "categories": [], "url": "https://abi.com.vn/doi-tac/x"})
assert turn.search_text("Trung tâm được thành lập năm nào?", d3).endswith(DATA["center"]["name"])
assert turn.search_text("Trung tâm Nghiên cứu và Phát triển Nông nghiệp Công nghệ cao thành lập năm nào?", d3).endswith("năm nào?")
assert turn.search_text("Quy trình tham gia ươm tạo?", d3) == "Quy trình tham gia ươm tạo?"
d2 = json.loads(json.dumps(DATA))
d2["posts"].append({**d2["posts"][0], "id": "old", "slug": "co-cau-to-chuc", "title": "Cơ Cấu Tổ Chức", "text": "Các phòng nghiệp vụ: 7 phòng",
                    "excluded": normalize.excluded("Cơ Cấu Tổ Chức", ""), "url": "https://abi.com.vn/tin-tuc/co-cau-to-chuc"})
assert not any(r["fields"]["Link"].endswith("/tin-tuc/co-cau-to-chuc") for r in index.records(d2))          # không vào chỉ mục tìm kiếm
assert "co-cau-to-chuc" not in json.dumps(tools.news_latest(d2, 50)["sources"])                     # không vào "tin mới"


# ------------------------------------------------------------------ 6. nối vào System 4
def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * 1024
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 1024] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


def fake_rerank(query, texts):
    q = set(re.findall(r"\w+", query.lower()))
    return [len(q & set(re.findall(r"\w+", t.lower()))) * 3 - 4.0 for t in texts]


prompts = []


async def fake_fast(messages, schema):
    prompts.append("\n".join(m["content"] for m in messages))
    d = {"plan": "", "answer": "Theo dữ liệu [1].", "ask_back": False, "choices": [], "sources": [1]}
    if "sources" not in schema["properties"]:
        d = {k: v for k, v in d.items() if k != "sources"}
    raw = json.dumps(d)
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


search.embed, search.rerank = fake_embed, fake_rerank
llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
tools.now_vn = lambda: NOW


def sse_text(r) -> tuple[str, list]:
    text, evs = "", []
    for line in r.text.splitlines():
        if line.startswith("data: "):
            e = json.loads(line[6:])
            evs.append(e)
            if e["type"] == "delta":
                text += e["text"]
    return text, evs


with TestClient(main.app) as c:
    tok = {}

    def as_(name):
        c.cookies.clear()
        c.cookies.set(auth.COOKIE, tok[name])
        return c

    tok["boss"] = c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE)
    tok["dan"] = c.post("/s4/auth/signup", json={"username": "dan", "password": "123456"}).cookies.get(auth.COOKIE)
    doms = {d["engine"]: d for d in as_("dan").get("/s4/domains").json()["domains"]}
    abi = doms["abi"]
    assert abi["kind"] == "hard" and abi["builtin"] is False and not abi["can_delete"] and not abi["can_upload"] and abi["pinned"], abi
    as_("boss")
    assert c.delete(f"/s4/domains/{abi['id']}").status_code == 403
    assert c.patch(f"/s4/domains/{abi['id']}", json={"kind": "soft"}).status_code == 422          # luôn là lĩnh vực cứng
    assert c.patch(f"/s4/domains/{abi['id']}", json={"name": "ABI"}).status_code == 200          # đổi tên được
    assert as_("dan").get("/s4/abi/status").status_code == 403
    assert as_("dan").post("/s4/abi/sync", json={}).status_code == 403
    # nút "Đồng bộ ngay" (Quản lý lĩnh vực / Quản trị): trả về khi đồng bộ ĐÃ bắt đầu, xong thì có lần chạy mới
    sync.Client = lambda: fake_client(FakeAbi(RAW))
    assert scheduler.index_missing()                                                    # có dữ liệu + có dev, chưa có chỉ mục
    n_runs = len(store.status()["runs"])
    r = as_("boss").post("/s4/abi/sync", json={}).json()
    assert r["started"] and r["state"]["running"], r["state"]
    assert c.post("/s4/abi/sync", json={}).json()["started"] is False                      # đang chạy: không chạy chồng
    for _ in range(200):
        if not c.get("/s4/abi/status").json()["state"]["running"]:
            break
        time.sleep(0.05)
    st = c.get("/s4/abi/status").json()
    assert len(st["runs"]) == n_runs + 1 and st["runs"][0]["ok"], st["runs"][:1]
    # công tắc "Hỏi thêm trợ lý của web" = cài đặt ABI_REMOTE_RAG (chỉ dev đổi được)
    assert as_("dan").post("/s4/settings", json={"values": {"ABI_REMOTE_RAG": True}}).status_code == 403
    assert as_("boss").post("/s4/settings", json={"values": {"ABI_REMOTE_RAG": True}}).status_code == 200
    assert c.get("/s4/abi/status").json()["settings"]["ABI_REMOTE_RAG"] is True and settings.get("ABI_REMOTE_RAG")
    c.post("/s4/settings", json={"values": {"ABI_REMOTE_RAG": False}})
    st = as_("boss").get("/s4/abi/status").json()
    assert st["counts"]["events"] == 10 and st["domain"]["id"] == abi["id"], st
    # chỉ mục tìm kiếm: bộ dữ liệu dùng chung của lĩnh vực ABI, có link về trang gốc
    out = index.rebuild(store.data())                                                   # nút đồng bộ ở trên đã dựng: không đổi
    assert not scheduler.index_missing()
    assert out["records"] > 20, out
    assert index.rebuild(store.data())["skipped"]                                              # không đổi: không dựng lại
    lst = as_("dan").get(f"/s4/datasets?domain_id={abi['id']}").json()
    assert len(lst["datasets"]) == 1 and lst["datasets"][0]["status"] == "ready" and not lst["can_upload"], lst
    ds_id = lst["datasets"][0]["id"]
    recs = c.get(f"/s4/datasets/{ds_id}/records?q=GRECO").json()["records"]
    assert recs and recs[0]["fields"]["Link"] == "https://abi.com.vn/su-kien/greco-2026", recs[:1]
    assert as_("boss").post(f"/s4/datasets/{ds_id}/retry").status_code == 422                     # không có tệp gốc để xử lý lại

    # câu mẫu 1 + 2: trả lời bằng code, không gọi AI, có nguồn
    prompts.clear()
    r = as_("dan").post("/s4/chat", json={"text": "Các sự kiện sắp diễn ra", "domain_id": abi["id"]})
    text, evs = sse_text(r)
    assert r.status_code == 200 and "4 sự kiện" in text and "GRECO 2026" in text and not prompts, text
    cid = next(e["conversation_id"] for e in evs if e["type"] == "meta")
    msgs = c.get(f"/s4/conversations/{cid}/messages").json()["messages"]
    meta = msgs[-1]["meta"]
    assert meta["abi"]["code_answer"] and len(meta["sources"]) == 4 and meta["sources"][2]["url"].endswith("/su-kien/greco-2026"), meta
    r = c.post("/s4/chat", json={"text": "Có bao nhiêu phòng ban", "conversation_id": cid})
    text, _ = sse_text(r)
    assert "**8 phòng**" in text and "66 cán bộ" in text and not prompts, text
    r = c.post("/s4/chat", json={"text": "Các sự kiện sắp diễn ra", "conversation_id": cid})
    r = c.post("/s4/chat", json={"text": "còn tháng 11 thì sao?", "conversation_id": cid})   # câu hỏi tiếp: ghép câu trước
    text, _ = sse_text(r)
    assert "tháng 11/2026" in text and "AGROVIET" in text and "GRECO" not in text and not prompts, text
    # câu còn điều kiện: AI trả lời từ thẻ dữ kiện [1] + đoạn tìm được, có ngày hôm nay
    r = c.post("/s4/chat", json={"text": "GRECO 2026 tổ chức ở đâu?", "conversation_id": cid})
    assert r.status_code == 200 and prompts and "Nguyen Hue" in prompts[-1] and "Hôm nay là" in prompts[-1], prompts[-1][-800:]
    assert "Bạn là trợ lý tra cứu thông tin Trung tâm Ươm tạo" in prompts[-1]                        # guardrail của lĩnh vực
    msgs = c.get(f"/s4/conversations/{cid}/messages").json()["messages"]
    assert msgs[-1]["meta"]["sources"][0]["url"].endswith("/su-kien/greco-2026"), msgs[-1]["meta"]
    # câu tự do: tìm trong bộ dữ liệu ABI
    prompts.clear()
    c.post("/s4/chat", json={"text": "Quy trình tham gia ươm tạo gồm những bước nào?", "conversation_id": cid})
    assert prompts and "Tiếp nhận nhu cầu" in prompts[-1], prompts[-1][-1500:] if prompts else None
    # câu chào (mặc định GREETING_MODE = code_first; nv5_off tắt nó cho test cũ): không tìm, không trả lời bằng code
    settings.save({"GREETING_MODE": "code_first"})
    prompts.clear()
    r = c.post("/s4/chat", json={"text": "xin chào", "conversation_id": cid})
    assert r.status_code == 200 and prompts and "Dữ liệu tham khảo" not in prompts[-1]
    # lĩnh vực khác không bị ảnh hưởng
    prompts.clear()
    c.post("/s4/chat", json={"text": "Các sự kiện sắp diễn ra", "domain_id": 2})
    assert prompts and "GRECO" not in prompts[-1]
print("OK test_abi")

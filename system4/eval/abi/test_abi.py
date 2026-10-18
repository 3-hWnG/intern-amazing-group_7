"""Lĩnh vực ABI (abi.com.vn): chuẩn hoá, router + code tính, đồng bộ + PHIÊN BẢN (abi.com.vn / staging, giữ 2 bản mới nhất mỗi nguồn),
khoá API, chặn trợ lý AI của web, nối vào chat. Dữ liệu: fixtures/abi_raw.json = bản rút gọn của API thật ngày 16/10/2026 (tên cán bộ
là tên giả). API giả trên máy: không gọi mạng, không cần Ollama, KHÔNG BAO GIỜ gọi /rag.
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
from system3.system4.abi import client as abi_client, index, normalize, router, store, sync, tools, versions
import nv5_off
nv5_off.apply()

RAW = json.loads((Path(__file__).parent / "fixtures" / "abi_raw.json").read_text(encoding="utf-8"))
NOW = datetime(2026, 10, 16, 10, 30, tzinfo=normalize.VN)
DATA = normalize.build(RAW)


# ------------------------------------------------------------------ API giả của abi.com.vn (đòi khoá như API thật từ 17/10)
KEY = "test_key_123"   # khoá GIẢ cho API giả; khoá thật chỉ nằm ở runtime/settings.json trên máy, không bao giờ vào git


class FakeAbi:
    def __init__(self, raw, key=KEY):
        self.requests = []   # (đường dẫn, tham số, User-Agent, Authorization) — kiểm quy ước của chủ web
        self.raw, self.calls, self.key = raw, [], key

    def page(self, items, q):
        page, limit = int(q.get("page", 1)), int(q.get("limit", 10))
        chunk = items[(page - 1) * limit: page * limit]
        return {"data": chunk, "meta": {"page": page, "limit": limit, "total": len(items), "pageCount": max(1, math.ceil(len(items) / limit))}}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path.removeprefix("/api/v1")
        q = dict(request.url.params)
        assert not path.startswith("/rag"), "KHÔNG được gọi trợ lý AI của web"
        self.calls.append(path)
        self.requests.append((path, q, request.headers.get("user-agent"), request.headers.get("authorization")))
        if request.headers.get("authorization") != f"Bearer {self.key}":
            return httpx.Response(401, json={"error": {"code": "API_KEY_UNAUTHORIZED", "message": "API Key hợp lệ là bắt buộc"}})
        r = self.raw
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


def fake_client(fake, source="prod"):
    return abi_client.Client(source, rps=0, transport=httpx.MockTransport(fake))


def variant(raw, n):
    """Bản dữ liệu "đã đổi" thứ n (đổi tóm tắt một đối tác) -> đồng bộ ra phiên bản mới."""
    r = json.loads(json.dumps(raw))
    r["catalog"][0]["summary"] = f"Bản đổi số {n}"
    return r


# staging: dữ liệu thử nghiệm của đội làm web (giống thật: "Trung tâm AAAA", test@gmail.com), bớt một phòng
STAGING = json.loads(json.dumps(RAW))
STAGING["settings"].update(centerName="Trung tâm AAAA (staging)", publicEmail="test@gmail.com")
_gone = STAGING["organization"]["departments"].pop()
STAGING["organization"]["people"] = [x for x in STAGING["organization"]["people"] if x["departmentId"] != _gone["id"]]


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
assert r["fact"]["card_url"] == "/su-kien"   # thẻ cả danh sách -> trang danh sách (turn.py ghép với nguồn đang dùng)
# nhắc tên một sự kiện / một phòng / một cán bộ -> thẻ chi tiết cho AI
r = router.route("GRECO 2026 tổ chức ở đâu?", DATA, NOW)
assert r["intent"] == "event_detail" and not r["plain"] and "Nguyen Hue" in r["fact"]["text"] and "sắp diễn ra" in r["fact"]["text"], r
r = router.route("Trưởng phòng Hỗ trợ Công nghệ Vi sinh là ai?", DATA, NOW)
assert r["intent"] == "department_detail" and "Phòng Hỗ trợ Công nghệ Vi sinh" in r["fact"]["text"] and "Trưởng phòng" in r["fact"]["text"], r
r = router.route("Cho mình hỏi về cán bộ Nguyễn Văn Cán Bộ 01", DATA, NOW)
# thoả thuận với chủ web: không bao giờ nêu email / SĐT riêng của cán bộ — chỉ email đơn vị, hotline, email chung
assert r["intent"] == "person_detail" and "canbo01@example.com" not in r["fact"]["text"]
assert "Liên hệ:" in r["fact"]["text"] and DATA["center"]["hotline"] in r["fact"]["text"], r["fact"]["text"]
assert "canbo01@example.com" not in router.route("Trưởng phòng Hỗ trợ Công nghệ Vi sinh là ai?", DATA, NOW)["fact"]["text"]
# âm tiết tiếng Việt trong tên sự kiện không làm nhầm câu hỏi chung: "Trình diễn…" (sự kiện staging) vs "sắp diễn ra"
dx = json.loads(json.dumps(DATA))
dx["events"].append({**dx["events"][0], "id": "x", "slug": "trinh-dien", "title": "Trình diễn giải pháp xanh cho chuỗi nông nghiệp"})
r = router.route("Các sự kiện sắp diễn ra", dx, NOW)
assert r["intent"] == "events_upcoming" and r["plain"], r["intent"]
assert router.route("Buổi trình diễn giải pháp xanh ở đâu?", dx, NOW)["intent"] == "event_detail"   # cặp từ vẫn nhận ra
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

# ------------------------------------------------------------------ 4. đồng bộ (API giả) + phiên bản
from system3.system4.abi import scheduler
# 4a. không gọi trợ lý AI của web: client chặn cứng /rag, chỉ có GET
try:
    abi_client.Client("prod").get("/rag/query")
    raise AssertionError("phải chặn /rag")
except abi_client.AbiError as e:
    assert e.code == "FORBIDDEN_BY_TEAM", e
assert not hasattr(abi_client.Client, "post")
# 4b. chưa có khoá: API báo 401, không tạo phiên bản, lỗi chỉ chỗ điền khoá
assert abi_client.key_hint() == "chưa có"
res = sync.run("prod", client=fake_client(FakeAbi(RAW)), index=False)
assert not res["ok"] and "401" in res["error"] and "ABI_API_KEY" in res["error"] and store.versions() == [], res
settings.save({"ABI_API_KEY": KEY})
assert abi_client.key_hint() == "đã có (…_123)" and KEY not in json.dumps(settings.describe(), ensure_ascii=False)   # khoá không ra giao diện
d_key = next(x for x in settings.describe() if x["key"] == "ABI_API_KEY")
assert d_key["value"] == "" and d_key["is_set"] is True and d_key["secret"] is True
cfg_before = settings.CONFIG_FILE.read_text(encoding="utf-8")
settings.set_default({"ABI_API_KEY": KEY})                                          # "Đặt làm mặc định" không bao giờ ghi khoá vào config.py
assert settings.CONFIG_FILE.read_text(encoding="utf-8") == cfg_before and settings.get("ABI_API_KEY") == KEY
# 4c. lần đầu: phiên bản 1 (abi.com.vn), đang dùng
fake = FakeAbi(RAW)
res = sync.run("prod", client=fake_client(fake), index=False)
assert res["ok"] and res["result"] == "new" and res["version_id"] == 1 and store.active_id() == 1, res
assert store.data()["center"]["name"] and len(store.data()["events"]) == 10 and store.data()["site_url"] == "https://abi.com.vn"
assert all(not p.startswith("/admin") for p in fake.calls)
# quy ước của chủ web: khoá (Bearer), User-Agent định danh, đúng dạng endpoint chính thức (không thêm compositionContract / type)
assert all(a == f"Bearer {KEY}" for *_, a in fake.requests)
assert all(ua.startswith("AHBI-Assistant-Bot/1.0 (+") for _, _, ua, _ in fake.requests), {ua for _, _, ua, _ in fake.requests}
assert not any("compositionContract" in q for p, q, *_ in fake.requests if p.startswith("/site/pages/"))
assert not any("type" in q for p, q, *_ in fake.requests if p.startswith("/content/posts/"))
# không lưu email / SĐT riêng của cán bộ (fixture có 1 email riêng)
assert all(not p["email"] and not p["phone"] for p in store.raw(1)["organization"]["people"])
assert res["privacy"] == {"people_contacts_removed": 1, "text_mentions_removed": 0}, res["privacy"]
assert "canbo01@example.com" not in json.dumps(store.raw(1)) + json.dumps(store.data())
n_detail = sum(1 for p in fake.calls if p.startswith("/content/posts/"))
assert n_detail == sum(1 for p in RAW["posts"] if p["contentType"] in ("news", "resource")), n_detail
# 4d. dữ liệu không đổi: KHÔNG tạo phiên bản (khỏi đẩy bản cũ ra), chỉ ghi giờ kiểm; tin không đổi thì không tải lại chi tiết
fake.calls.clear()
res = sync.run("prod", client=fake_client(fake), index=False)
assert res["ok"] and res["result"] == "unchanged" and res["version_id"] == 1 and len(store.versions()) == 1, res
assert not any(p.startswith("/content/posts/") for p in fake.calls), fake.calls
# 4e. dữ liệu đổi: phiên bản mới; bản đang dùng là bản mới nhất -> tự chuyển sang bản mới
res = sync.run("prod", client=fake_client(FakeAbi(variant(RAW, 2))), index=False)
assert res["result"] == "new" and res["version_id"] == 2 and store.active_id() == 2 and res["deleted_versions"] == [], res
res = sync.run("prod", client=fake_client(FakeAbi(variant(RAW, 3))), index=False)   # bản thứ 3: tự xoá bản cũ nhất (giữ 2)
assert res["version_id"] == 3 and res["deleted_versions"] == [1] and [v["id"] for v in store.versions("prod")] == [3, 2], res
assert not (store.folder() / "versions" / "1").exists() and store.active_id() == 3
# 4f. staging: nguồn riêng, giữ bản đang dùng của abi.com.vn; link về staging.abi.com.vn
res = sync.run("staging", client=fake_client(FakeAbi(STAGING), "staging"), index=False)
assert res["ok"] and res["version_id"] == 4 and store.active_id() == 3, res
sd = store.version_data(4)
assert sd["source"] == "staging" and sd["site_url"] == "https://staging.abi.com.vn" and sd["center"]["name"] == "Trung tâm AAAA (staging)"
assert all(e["url"].startswith("https://staging.abi.com.vn/") for e in sd["events"]) and sd["center"]["url"] == "https://staging.abi.com.vn/lien-he"
versions.activate(4)                                                                # chuyển tức thì
assert store.data()["center"]["name"] == "Trung tâm AAAA (staging)" and len(store.data()["departments"]) == 8
assert router.route("Có bao nhiêu phòng ban", store.data(), NOW)["fact"]["sources"][0]["url"].startswith("https://staging.abi.com.vn/")
# 4g. đang theo bản mới nhất của staging -> bản staging mới tự thành đang dùng; quá 2 bản thì tự xoá bản cũ nhất
sync.run("staging", client=fake_client(FakeAbi(variant(STAGING, 5)), "staging"), index=False)
assert store.active_id() == 5
res = sync.run("staging", client=fake_client(FakeAbi(variant(STAGING, 6)), "staging"), index=False)
assert res["deleted_versions"] == [4] and [v["id"] for v in store.versions("staging")] == [6, 5] and store.active_id() == 6, res
# 4h. dev chọn bản cũ hơn -> bản mới KHÔNG tự thay; nhưng bản đang dùng bị xoá (quá 2 bản) thì chuyển sang bản mới nhất cùng nguồn
versions.activate(5)
res = sync.run("staging", client=fake_client(FakeAbi(variant(STAGING, 7)), "staging"), index=False)
assert res["version_id"] == 7 and res["deleted_versions"] == [5] and store.active_id() == 7, res
assert [v["id"] for v in store.versions("prod")] == [3, 2]                            # tự xoá chỉ trong cùng nguồn
# 4i. xoá tay: không xoá được bản đang dùng
try:
    versions.delete(7)
    raise AssertionError("phải từ chối xoá bản đang dùng")
except ValueError:
    pass
versions.delete(6)
assert [v["id"] for v in store.versions("staging")] == [7]
# 4j. API hỏng: không tạo phiên bản
broken = json.loads(json.dumps(RAW))
broken["organization"]["departments"] = []
res = sync.run("prod", client=fake_client(FakeAbi(broken)), index=False)
assert not res["ok"] and "Không tạo phiên bản" in res["error"] and [v["id"] for v in store.versions("prod")] == [3, 2], res
# 4k. bố cục cũ (raw.json + data.json ngay trong runtime/abi, trước 17/10) -> phiên bản 1 đang dùng
legacy = Path(TMP) / "legacy_abi"
legacy.mkdir()
(legacy / "raw.json").write_text(json.dumps(RAW), encoding="utf-8")
(legacy / "data.json").write_text(json.dumps(DATA), encoding="utf-8")
_real_folder, store.folder = store.folder, lambda: legacy
assert store.active_id() == 1 and store.versions()[0]["source"] == "prod" and (legacy / "versions" / "1" / "data.json").exists()
assert not (legacy / "raw.json").exists() and store.data()["center"]["name"] == DATA["center"]["name"]
store.folder = _real_folder
store._cache.update(key=None, data=None)
# 4l. lịch: chỉ abi.com.vn tự đồng bộ; vừa lỗi -> thử lại sau 1 giờ; thành công -> chờ đủ (tối thiểu 6 giờ theo thoả thuận)
st = store.status()
st["runs"][0]["started"] = datetime.fromtimestamp(time.time() - 3700, normalize.VN).isoformat()   # lần prod lỗi (4j) hơn 1 giờ trước
store.write_json("status.json", st)
assert scheduler.due("prod")
st["runs"][0].update(ok=True, error=None)
store.write_json("status.json", st)
assert not scheduler.due("prod")                                                    # thành công 1 giờ trước: chưa tới 6 giờ
settings.save({"ABI_SYNC_HOURS": 1})
assert not scheduler.due("prod")                                                    # đặt 1 giờ vẫn tính là 6 giờ
settings.save({"ABI_SYNC_HOURS": 0})
assert not scheduler.due("prod")                                                    # 0 = tắt
settings.save({"ABI_SYNC_HOURS": 6})
# tối đa 2 request/giây với mạng thật, kể cả khi gọi Client(rps=…) lớn hơn; User-Agent kèm liên hệ của nhóm
assert abi_client.Client(rps=10)._gap == 0.5 and abi_client.Client(rps=0)._gap == 0.5
assert abi_client.user_agent() == "AHBI-Assistant-Bot/1.0 (+https://github.com/3-hWnG/intern-amazing-group_7)"
settings.save({"ABI_BOT_CONTACT": "nhom7@example.com"})
assert abi_client.user_agent() == "AHBI-Assistant-Bot/1.0 (+nhom7@example.com)"
settings.save({"ABI_BOT_CONTACT": ""})
# bỏ email riêng của cán bộ cả khi nó lỡ nằm trong bài / chương trình; email của phòng và trung tâm giữ nguyên
r2 = json.loads(json.dumps(RAW))
r2["organization"]["people"][1]["email"] = "rieng.canbo@example.com"
r2["programs"][0]["body"]["contactEmail"] = "RIENG.CANBO@example.com"
dep_mail = next(d["email"] for d in r2["organization"]["departments"] if d.get("email"))
r2["organization"]["people"][2]["email"] = dep_mail                                # cán bộ ghi email của phòng: vẫn là email chung
r2["posts"][0]["summary"] = f"Liên hệ rieng.canbo@example.com hoặc {dep_mail}"
out = sync.scrub_personal(r2)
s = json.dumps(out, ensure_ascii=False)
assert "rieng.canbo" not in s.lower() and dep_mail in s and out["posts"][0]["summary"].startswith("Liên hệ [đã ẩn]"), out["posts"][0]["summary"]
assert out["privacy"]["people_contacts_removed"] == 3 and out["privacy"]["text_mentions_removed"] == 2, out["privacy"]
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
    # dùng bản abi.com.vn mới nhất cho phần hỏi đáp; chỉ mục cho phiên bản đang dùng
    versions.activate(3)
    def slow(fake):   # API giả chậm lại chút để kịp kiểm "đang đồng bộ thì không chạy chồng"
        return lambda req: (time.sleep(0.02), fake(req))[1]
    sync.Client = lambda source: fake_client(slow(FakeAbi(variant(RAW, 3) if source == "prod" else variant(STAGING, 7))), source)
    assert scheduler.index_missing()                                                    # có dữ liệu + có dev, chưa có chỉ mục
    embedded = []
    search.embed = lambda texts: (embedded.append(len(texts)), fake_embed(texts))[1]
    out = scheduler.build_active_index()
    assert out["records"] > 20 and not scheduler.index_missing(), out
    n_first = sum(embedded)
    # phiên bản 2 chỉ khác 1 đoạn -> dùng lại vector, gần như không gọi bge-m3
    embedded.clear()
    out2 = index.build(2, store.version_data(2), "abi.com.vn")
    assert out2["reused_vectors"] >= out2["records"] - 2 and sum(embedded) <= 2, (out2, embedded)
    assert n_first >= out["records"] - 1
    # nút "Đồng bộ" (Quản lý lĩnh vực / Quản trị): trả về khi đồng bộ ĐÃ bắt đầu; vừa đồng bộ thì nghỉ 10 phút
    st = store.status()
    for x in st["runs"]:
        x["started"] = datetime.fromtimestamp(time.time() - 3700, normalize.VN).isoformat()
    store.write_json("status.json", st)
    n_runs = len(store.status()["runs"])
    r = as_("boss").post("/s4/abi/sync", json={"source": "prod"}).json()
    assert r["started"] and r["state"]["running"], (r["state"], r.get("reason"))
    assert c.post("/s4/abi/sync", json={"source": "staging"}).json()["started"] is False   # đang chạy: không chạy chồng
    for _ in range(200):
        if not c.get("/s4/abi/status").json()["state"]["running"]:
            break
        time.sleep(0.05)
    st = c.get("/s4/abi/status").json()
    assert len(store.status()["runs"]) == n_runs + 1 and st["runs"][0]["ok"] and st["runs"][0]["result"] == "unchanged", st["runs"][:1]
    r = c.post("/s4/abi/sync", json={"source": "prod"}).json()
    assert r["started"] is False and "Vừa đồng bộ" in r["reason"], r.get("reason")
    assert st["user_agent"].startswith("AHBI-Assistant-Bot/1.0 (+") and st["api_key"] == "đã có (…_123)" and KEY not in json.dumps(st)
    assert st["counts"]["events"] == 10 and st["domain"]["id"] == abi["id"] and st["active"]["id"] == 3, st["active"]
    # danh sách phiên bản: 2 bản abi.com.vn + 1 bản staging, đánh dấu đang dùng / mới nhất
    vs = {v["id"]: v for v in st["versions"]}
    assert sorted(vs) == [2, 3, 7] and vs[3]["active"] and vs[3]["newest"] and vs[7]["label"] == "staging.abi.com.vn", vs
    assert vs[3]["dataset"]["status"] == "ready" and vs[2]["dataset"]["status"] == "ready" and vs[7]["dataset"] is None
    # bộ dữ liệu ABI: chỉ bộ của phiên bản đang dùng được bật; không bật / xoá thẳng được (phải qua phiên bản)
    lst = as_("dan").get(f"/s4/datasets?domain_id={abi['id']}").json()
    on = [d for d in lst["datasets"] if d["active"]]
    assert len(lst["datasets"]) == 2 and len(on) == 1 and not lst["can_upload"], lst
    ds_id = on[0]["id"]
    recs = c.get(f"/s4/datasets/{ds_id}/records?q=GRECO").json()["records"]
    assert recs and recs[0]["fields"]["Link"] == "https://abi.com.vn/su-kien/greco-2026", recs[:1]
    as_("boss")
    assert c.post(f"/s4/datasets/{ds_id}/retry").status_code == 422                     # không có tệp gốc để xử lý lại
    other = next(d["id"] for d in lst["datasets"] if not d["active"])
    assert c.patch(f"/s4/datasets/{other}", json={"active": True}).status_code == 422
    assert c.delete(f"/s4/datasets/{ds_id}").status_code == 422
    # API phiên bản: chỉ dev; không xoá được bản đang dùng
    assert as_("dan").post("/s4/abi/versions/2/activate", json={}).status_code == 403
    assert as_("boss").delete("/s4/abi/versions/3").status_code == 422

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
    # chuyển sang staging (tức thì): câu trả lời theo dữ liệu staging, link về staging.abi.com.vn; chuyển lại bản thật
    as_("boss")
    st = c.post("/s4/abi/versions/7/activate", json={}).json()
    assert st["active"]["id"] == 7 and st["active"]["label"] == "staging.abi.com.vn", st["active"]
    r = as_("dan").post("/s4/chat", json={"text": "Có bao nhiêu phòng ban", "domain_id": abi["id"]})
    text, evs = sse_text(r)
    assert "**7 phòng**" in text, text
    cid2 = next(e["conversation_id"] for e in evs if e["type"] == "meta")
    meta = c.get(f"/s4/conversations/{cid2}/messages").json()["messages"][-1]["meta"]
    assert meta["sources"][0]["url"].startswith("https://staging.abi.com.vn/") and meta["abi"]["source"] == "staging", meta
    as_("boss").post("/s4/abi/versions/3/activate", json={})
    r = as_("dan").post("/s4/chat", json={"text": "Có bao nhiêu phòng ban", "domain_id": abi["id"]})
    assert "**8 phòng**" in sse_text(r)[0]
    # khoá API trong ⚙: giao diện chỉ biết "đã lưu", không thấy giá trị
    sets = {x["key"]: x for x in as_("boss").get("/s4/settings").json()["settings"]}
    assert sets["ABI_API_KEY"]["value"] == "" and sets["ABI_API_KEY"]["is_set"] and "ABI_REMOTE_RAG" not in sets
print("OK test_abi")

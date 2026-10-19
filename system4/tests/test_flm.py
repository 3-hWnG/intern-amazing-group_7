"""Lĩnh vực FLM (system4/flm): đọc trang khách flm.fpt.edu.vn, chờ captcha, phiên bản (giữ 2), dataset tải thêm, hỏi đáp.
Trình duyệt giả trả các trang THẬT đã lưu và cắt gọn (fixtures/flm, 19/10/2026) — không gọi mạng, không mở Chrome.
Model giả (embedding, reranker, LLM). Chạy: python run_server.py system4/tests/test_flm.py"""
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import time
from pathlib import Path

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RUNTIME_DIR=os.path.join(TMP, "s4"),
                  OLLAMA_HOST="http://127.0.0.1:1")

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, db, llm, search
from system3.system4.flm import build, scrape, store, sync
import nv5_off
nv5_off.apply()

FIX = Path(__file__).parent / "fixtures" / "flm"
page = lambda n: (FIX / n).read_text(encoding="utf-8")

# ------------------------------------------------------------------ bộ đọc trên trang thật
lst = scrape.parse_list(page("list_bit_se.html"))
assert len(lst) == 38 and scrape.newest(lst, "BIT_SE")["code"] == "BIT_SE-2026_K22D_23A"   # khoá mới nhất, không lẫn BIT_AS
assert scrape.newest(lst, "BIT_AS")["code"] == "BIT_AS_K22C" and scrape.newest(lst, "BIT_XX") is None
cur = scrape.parse_curriculum(page("curriculum_3548.html"))
assert cur["info"]["CurriculumCode"] == "BIT_SE-2026_K22D_23A" and len(cur["plo"]) == 3 and len(cur["subjects"]) == 6, cur["subjects"]
assert cur["subjects"][4] == {"code": "MAC103", "name": "Calculus_Giải tích", "semester": "1", "credits": "3", "prerequisite": "",
                              "link": "/gui/role/guest/Syllabuses?subCode=MAC103&curriculumID=3548"}, cur["subjects"][4]
vers = scrape.parse_syllabuses(page("syllabuses_prf192.html"))
assert vers[0]["sylID"] == 12223 and vers[0]["active"] and vers[0]["approved"]
syl = scrape.parse_syllabus(page("syllabus_12223.html"))
assert syl["info"]["NoCredit"] == "3" and syl["info"]["MinAvgMarkToPass"] == "5" and len(syl["clo"]) == 9, syl["info"]
assert syl["assessment"][1]["Category"] == "Practical Exam" and syl["assessment"][1]["Weight"] == "30.0%"
assert scrape.captcha_page('<div class="g-recaptcha" data-sitekey="x">') and not scrape.captcha_page(page("syllabus_12223.html"))
assert build._major("… Software Engineering Major (Chương trình cử nhân ngành CNTT, chuyên ngành Kỹ thuật phần mềm)") == "Kỹ thuật phần mềm"


def v_skip(rec):   # trang không có quyền xem được ghi lại (lần chạy có ghi "skipped" trong store.runs)
    return any("3534" in x for x in (store.runs()[0].get("skipped") or []))


# ------------------------------------------------------------------ trình duyệt giả
CAPTCHA = '<html><body><form action="/gui/guest-captcha/continue"><div class="g-recaptcha"></div></form></body></html>'


class FakeBrowser:
    captcha_polls = 2       # lần mở đầu: 2 lần kiểm còn ở trang captcha, rồi "người dùng" tích xong
    weight = "30.0%"         # đổi để giả lập FLM sửa đề cương -> phiên bản mới
    expire_after = None      # số request trước khi phiên khách hết hạn (trả trang captcha)
    seen: list = []

    def __init__(self, profile):
        self.polls, self.n = 0, 0

    def start(self, url):
        FakeBrowser.seen.append(("start", url))

    def location(self):
        self.polls += 1
        return scrape.BASE + ("/gui/guest-captcha?url=x" if self.polls <= FakeBrowser.captcha_polls else "/gui/role/guest/ListCurriculum?educationLevel=fptu")

    def eval(self, expr):
        if "readyState" in expr:
            return "complete"
        return CAPTCHA if self.polls <= FakeBrowser.captcha_polls else "<html><body>ok</body></html>"

    def fetch(self, url):
        self.n += 1
        path = url[len(scrape.BASE):]
        FakeBrowser.seen.append(("get", path))
        if FakeBrowser.expire_after is not None and self.n > FakeBrowser.expire_after:
            return 200, scrape.BASE + "/gui/guest-captcha?url=x", CAPTCHA
        if path.startswith("/gui/role/guest/ListCurriculum"):
            return 200, url, page("list_bit_se.html")
        if path.startswith("/gui/role/guest/CurriculumDetails?curid=3548"):
            return 200, url, page("curriculum_3548.html")
        if path.startswith("/gui/role/guest/Syllabuses"):
            return 200, url, page("syllabuses_prf192.html")
        if path.startswith("/gui/role/guest/SyllabusDetails"):
            return 200, url, page("syllabus_12223.html").replace("30.0%", FakeBrowser.weight)
        return 404, url, "not found"

    def close(self, quit_chrome=True):
        pass


class FakeLogin:
    """Chế độ đăng nhập: 2 lần kiểm đầu còn ở /Login (người dùng đang đăng nhập), rồi ở /Home có nút Sign out. Trang = fixtures/flm/full_*
    (lấy từ FLM thật khi đăng nhập 19/10/2026, đã xoá tên / email)."""
    login_polls = 2
    expire_after = None
    deny = ()   # trang tài khoản không có quyền xem: FLM chuyển về /Login nhưng phiên vẫn còn
    made, closed, n_total = [], [], [0]

    def __init__(self, profile, port=None):
        self.polls, self.n = 0, 0
        FakeLogin.made.append(port)

    def start(self, url):
        pass

    def location(self):
        self.polls += 1
        return scrape.BASE + ("/Login" if self.polls <= FakeLogin.login_polls else "/Home")

    def eval(self, expr):
        if "readyState" in expr:
            return "complete"
        return "<html><body>login</body></html>" if self.polls <= FakeLogin.login_polls else '<html><button id="lbtnSignOut"></button></html>'

    def fetch(self, url):
        self.n += 1
        FakeLogin.n_total[0] += 1
        path = url[len(scrape.BASE):]
        if path == "/Home":
            ok = FakeLogin.expire_after is None or self.n <= FakeLogin.expire_after
            return 200, url if ok else scrape.BASE + "/Login", '<button id="lbtnSignOut"></button>' if ok else "<html>login</html>"
        if FakeLogin.expire_after is not None and self.n > FakeLogin.expire_after:
            return 200, scrape.BASE + "/Login", "<html>login</html>"
        if any(path.startswith(d) for d in FakeLogin.deny):
            return 200, scrape.BASE + "/Login?ReturnUrl=x", "<html>login</html>"
        for pre, fx in (("/gui/role/student/ListCurriculum", "full_list_all.html"), ("/gui/role/student/CurriculumDetails", "full_curriculum_3548.html"),
                        ("/Compo/ViewComBo", "full_combo_3548.html"), ("/Compo/Detail/", "full_combo_detail_2746.html"),
                        ("/Elective/ViewElective", "full_elective_3548.html"), ("/Elective/Detail/", "full_elective_detail_481.html"),
                        ("/gui/role/student/SyllabusDetails", "full_syllabus_12223.html")):
            if path.startswith(pre):
                return 200, url, page(fx)
        if path.startswith("/gui/role/student/SyllabusManagement"):
            return 200, url, page("full_sylsearch_P.html") if path.endswith("keyword=P") else "<html><body>0 syllabus(es) found</body></html>"
        return 404, url, "not found"

    def call(self, method, **kw):
        FakeLogin.closed.append(method)

    def close(self, quit_chrome=True):
        pass


def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * 1024
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 1024] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


prompts = []
ANSWER = ["Theo dữ liệu [1]."]


async def fake_fast(messages, schema):
    prompts.append(messages[0]["content"] + messages[-1]["content"])
    d = {"plan": "", "answer": ANSWER[0], "ask_back": False, "choices": [], "sources": [1]}
    if "sources" not in schema["properties"]:
        d = {k: v for k, v in d.items() if k != "sources"}
    raw = json.dumps(d)
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


search.embed = fake_embed
search.rerank = lambda q, ts: [len(set(re.findall(r"\w+", q.lower())) & set(re.findall(r"\w+", t.lower()))) * 3 - 4.0 for t in ts]
llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
sync.BROWSER = FakeBrowser
scrape.DELAY = 0
from system3.system4.server import settings
settings.save({"FLM_PROGRAMS": "BIT_SE"})

with TestClient(main.app) as c:
    tok = {}

    def as_(name):
        c.cookies.clear()
        c.cookies.set(auth.COOKIE, tok[name])
        return c

    tok["boss"] = c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE)
    tok["dan"] = c.post("/s4/auth/signup", json={"username": "dan", "password": "123456"}).cookies.get(auth.COOKIE)
    flm = next(d for d in as_("dan").get("/s4/domains").json()["domains"] if d["engine"] == "flm")
    assert flm["kind"] == "hard" and not flm["can_delete"] and not flm["can_upload"], flm
    assert c.get("/s4/flm/status").status_code == 403 and c.post("/s4/flm/sync").status_code == 403
    assert as_("boss").patch(f"/s4/domains/{flm['id']}", json={"kind": "soft"}).status_code == 422   # luôn là lĩnh vực cứng
    st = c.get("/s4/flm/status").json()
    assert st["versions"] == [] and st["programs"] == ["BIT_SE"] and st["domain"]["id"] == flm["id"], st
    # --- chưa đồng bộ (chưa có dữ liệu): câu chào vẫn được chào lại; câu hỏi thì nói rõ lĩnh vực CHƯA có dữ liệu (lỗi thấy 19/10 trên web)
    r = as_("dan").post("/s4/chat", json={"text": "Chào, bạn làm được gì?", "domain_id": flm["id"]})
    assert r.status_code == 200 and '"type": "replace"' not in r.text.replace('":"', '": "'), r.text[-500:]
    ANSWER[0] = "Môn MAC103 (Giải tích) thường có 3 tín chỉ, học ở kỳ 1 của chương trình kỹ thuật phần mềm."   # AI tự trả bằng kiến thức chung
    r = c.post("/s4/chat", json={"text": "MAC103 có bao nhiêu tín chỉ?", "domain_id": flm["id"]})
    ANSWER[0] = "Theo dữ liệu [1]."
    assert "chưa có bộ dữ liệu nào đang bật" in r.text, r.text
    as_("boss")

    # --- lần đồng bộ đầu: chờ captcha, đọc khung mới nhất + đề cương 6 môn, nạp thành phiên bản 1 (đang dùng)
    rec = sync.run()
    assert rec["ok"] and rec["result"] == "new" and rec["version"] == 1, rec
    assert ("get", "/gui/role/guest/CurriculumDetails?curid=3548") in FakeBrowser.seen        # khung mới nhất
    assert rec["counts"] == {"Chương trình": 1, "PLO": 3, "Khung chương trình": 6, "Môn học": 6, "CLO": 54, "Đánh giá": 30}, rec["counts"]
    v1 = store.get(1)
    ds1 = db.get_dataset(v1["dataset_id"])
    assert ds1["status"] == "ready" and ds1["active"] and ds1["domain_id"] == flm["id"] and ds1["name"].startswith("flm.fpt.edu.vn · phiên bản 1"), ds1
    recs = c.get(f"/s4/datasets/{ds1['id']}/records?q=MAC103").json()["records"]
    assert recs and any("Calculus" in json.dumps(r, ensure_ascii=False) for r in recs), recs[:2]
    # --- lần hai không đổi gì: không tạo phiên bản
    FakeBrowser.captcha_polls = 0   # phiên khách còn hạn: không hiện captcha
    rec = sync.run()
    assert rec["ok"] and rec["result"] == "unchanged" and len(store.versions()) == 1 and store.get(1)["checked_at"], rec
    # --- FLM sửa trọng số: phiên bản 2 thành đang dùng; lần nữa -> phiên bản 3, phiên bản 1 tự xoá (giữ 2)
    FakeBrowser.weight = "35.0%"
    rec = sync.run()
    assert rec["ok"] and rec["version"] == 2 and store.active_id() == 2 and not db.get_dataset(ds1["id"])["active"], rec
    FakeBrowser.weight = "40.0%"
    rec = sync.run()
    assert rec["ok"] and rec["version"] == 3 and rec["pruned"] == [1] and db.get_dataset(ds1["id"]) is None, rec
    assert [v["id"] for v in store.versions()] == [3, 2] and store.active_id() == 3
    # --- dataset tải thêm vào FLM: dev tải được; chuyển phiên bản không tắt nó; thẻ "Dữ liệu tải thêm" chỉ có nó
    r = c.post("/s4/datasets", files={"file": ("lich_thi.csv", io.BytesIO("Mã môn,Ngày thi\nMAC103,20/12/2026\n".encode()), "text/csv")},
               data={"domain_id": str(flm["id"])})
    assert r.status_code == 200, r.text
    extra = r.json()["dataset"]["id"]
    for _ in range(80):
        if db.get_dataset(extra)["status"] == "ready":
            break
        time.sleep(0.25)
    r = c.post("/s4/flm/versions/2/activate").json()
    assert r["active"] == 2 and [v["id"] for v in r["versions"] if v["active"]] == [2]
    on = {d["id"] for d in db.active_datasets(db.user_by_name("dan")["id"], flm["id"], "user")}
    assert on == {store.get(2)["dataset_id"], extra}, on
    up = c.get(f"/s4/datasets?domain_id={flm['id']}&uploaded=1").json()["datasets"]
    assert [d["id"] for d in up] == [extra], up
    v3 = store.get(3)["dataset_id"]
    assert c.delete(f"/s4/datasets/{v3}").status_code == 422 and c.patch(f"/s4/datasets/{v3}", json={"active": True}).status_code == 422
    assert c.delete("/s4/flm/versions/2").status_code == 422                                   # đang dùng: không xoá
    assert c.delete("/s4/flm/versions/3").status_code == 200 and db.get_dataset(v3) is None
    # --- hỏi trong lĩnh vực FLM (người dân): trả lời từ dữ liệu FLM, có guardrail của lĩnh vực
    prompts.clear()
    r = as_("dan").post("/s4/chat", json={"text": "Môn MAC103 có bao nhiêu tín chỉ?", "domain_id": flm["id"]})
    assert r.status_code == 200, r.text
    body = r.text + "".join(prompts)
    assert "MAC103" in body or "Calculus" in body, r.text[-600:]
    # --- phiên khách hết hạn giữa chừng: lần đồng bộ báo lỗi rõ ràng, không tạo phiên bản, dữ liệu cũ giữ nguyên
    FakeBrowser.weight, FakeBrowser.expire_after = "45.0%", 3
    rec = sync.run()
    assert not rec["ok"] and "captcha" in rec["error"] and [v["id"] for v in store.versions()] == [2] and store.active_id() == 2, rec
    st = as_("boss").get("/s4/flm/status").json()
    assert st["runs"][0]["ok"] is False and not st["state"]["running"] and st["versions"][0]["dataset"]["status"] == "ready", st["runs"][:1]

    # ================================================================ chế độ ĐĂNG NHẬP: mọi ngành, tài liệu, lịch buổi học
    assert scrape.program_key("BIT_SE-2026_K22D_23A") == "BIT_SE" and scrape.program_key("BEN_CHN_K19D,K20A") == "BEN_CHN"
    assert [x["program"] for x in scrape.newest_per_program(scrape.parse_list(page("full_list_all.html")))] == ["BBA_HM", "BIT_AI", "BIT_SE", "PEN_A2"]
    syl = scrape.parse_syllabus(page("full_syllabus_12223.html"))
    assert len(syl["materials"]) == 3 and len(syl["schedule"]) == 5 and len(syl["questions"]) == 3
    assert syl["schedule"][0]["_links"] == ["https://flm.fpt.edu.vn/download/12223/S/1_PRF192_Slides_1.zip"]   # chỉ LINK, không tải
    sync.BROWSER = FakeLogin
    FakeLogin.deny = ("/gui/role/student/CurriculumDetails?curid=3534",)   # BBA_HM: không có quyền xem -> bỏ qua, không dừng
    r = c.post("/s4/flm/sync", json={"mode": "full"}).json()
    assert r["started"], r
    for _ in range(400):
        st = c.get("/s4/flm/status").json()
        if not st["state"]["running"]:
            break
        time.sleep(0.1)
    rec = st["runs"][0]
    assert rec["ok"] and rec["mode"] == "full" and rec["result"] == "new" and rec["programs"] == ["BIT_AI", "BIT_SE", "PEN_A2"], rec
    assert v_skip(rec), rec
    v = store.get(rec["version"])
    assert v["mode"] == "full" and len(v["extra_ids"]) == 1 and store.active_id() == v["id"], v
    assert v["counts"]["Lịch học (môn)"] == 2 and "CLO" not in v["counts"] and v["counts"]["Môn học"] == 12, v["counts"]   # 6 môn khung + 4 combo + 2 tự chọn
    md = db.get_dataset(v["extra_ids"][0])
    assert md["status"] == "ready" and md["active"] and "lịch học" in md["name"], md
    assert {v["dataset_id"], md["id"]} <= {d["id"] for d in db.active_datasets(db.user_by_name("dan")["id"], flm["id"], "user")}   # dùng chung
    hits = c.get(f"/s4/datasets/{md['id']}/records?q=Slides_1").json()["records"]
    assert hits and "download/12223/S/1_PRF192_Slides_1.zip" in hits[0]["text"], hits[:1]
    assert st["login_open"] and FakeLogin.made == [sync.LOGIN_PORT]                                      # phiên giữ lại, cổng riêng
    # lần hai: phiên còn (không phải đăng nhập lại, không mở Chrome mới), mọi trang lấy từ bộ đệm, dữ liệu không đổi
    n0 = FakeLogin.n_total[0]
    rec2 = sync.run("full")
    assert rec2["ok"] and rec2["result"] == "unchanged" and rec2["cached"] >= 2 and FakeLogin.made == [sync.LOGIN_PORT], rec2
    assert FakeLogin.n_total[0] - n0 == rec2["requests"] and rec2["requests"] <= 2 < rec["requests"], (rec2["requests"], rec["requests"])
    # phiên đăng nhập hết hạn giữa chừng (bộ đệm trống): báo rõ trang nào, giữ phiên bản cũ
    import shutil
    shutil.rmtree(store.root() / "cache" / "full")
    FakeLogin.expire_after = 3
    sync._login["browser"].n = 0
    rec3 = sync.run("full")
    assert not rec3["ok"] and "hết hạn (ở /" in rec3["error"] and store.active_id() == v["id"], rec3
    bad = json.loads((store.root() / "cache" / "full" / "bad_pages.json").read_text(encoding="utf-8"))
    assert len(bad) == 1 and bad[0] in rec3["error"], bad          # trang làm mất phiên được ghi lại: lần sau bỏ qua
    # tắt server: đóng Chrome đăng nhập, xoá hồ sơ (cookie)
    sync.login_profile().mkdir(parents=True, exist_ok=True)
    sync.close_login()
    assert "Browser.close" in FakeLogin.closed and not sync.login_profile().exists() and sync._login["browser"] is None
print("OK test_flm")

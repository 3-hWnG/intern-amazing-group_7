"""Phase 26: bộ nhớ người dùng. API CRUD + kiểm giá trị + quên + cô lập giữa 2 client_id + không rò PII; lọc ứng viên theo đối tượng
(unit, policy.filter_by_subject); đường /chat dùng hồ sơ để bớt hỏi lại; tắt hồ sơ = như cũ. Chạy: python tests/p26_memory_test.py"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0", S3_PLANNER_MODE="rules", S3_NO_WARMUP="1")

from fastapi.testclient import TestClient
import main
import user_memory
from db import store
from policy.policy import filter_by_subject
from system3.data import api as data_api

A, B = {"X-Client-Id": "client-aaa"}, {"X-Client-Id": "client-bbb"}
DN = "Doanh nghiệp"
Q = "Đăng ký đất đai lần đầu cho hộ gia đình đang sử dụng đất"   # ba ứng viên gần nhau, một cái chỉ dành cho doanh nghiệp/Việt kiều
P_ONLY_DN, P_CD1, P_CD2 = "1.115375", "1.013978", "1.115620"

conn = data_api.connect()
# ---- unit: lọc ứng viên theo đối tượng
mem_dn = {"subjects": {DN, "Doanh nghiệp Việt Nam"}, "label": DN}
mem_cd = {"subjects": {"Công dân Việt Nam"}, "label": "Công dân Việt Nam"}
near = [P_CD1, P_ONLY_DN, P_CD2]
assert filter_by_subject(conn, near, None) == (near, None)                                   # không hồ sơ: không đổi
assert filter_by_subject(conn, near, {"subjects": set(), "label": ""}) == (near, None)
ids, note = filter_by_subject(conn, near, mem_dn, "xin hỏi về đăng ký đất đai lần đầu"); assert ids == [P_ONLY_DN] and note["kind"] == "pick", (ids, note)
ids, note = filter_by_subject(conn, near, mem_cd, "xin hỏi về đăng ký đất đai lần đầu"); assert ids == [P_CD1, P_CD2] and note["kind"] == "shrink", (ids, note)   # giữ thứ tự, bỏ ứng viên không hợp
assert filter_by_subject(conn, near, {"subjects": {"Đảng viên"}, "label": "Đảng viên"}, "x") == (near, None)             # không ai hợp: không đổi (không loại hết)
assert filter_by_subject(conn, [P_CD1, P_CD2], mem_cd, "x") == ([P_CD1, P_CD2], None)                                    # ai cũng hợp: không đổi
name = conn.execute("SELECT name FROM procedures WHERE proc_id=?", (P_CD1,)).fetchone()[0]
assert filter_by_subject(conn, near, mem_dn, name) == (near, None), "câu nêu nguyên tên một ứng viên thì hồ sơ không được can thiệp"
# ứng viên không khai đối tượng = chưa biết: không bị loại, và không để 'pick' vì thiếu dữ liệu
empty = [r[0] for r in conn.execute("SELECT p.proc_id FROM procedures p WHERE p.status='active' AND NOT EXISTS (SELECT 1 FROM procedure_subjects s WHERE s.row_id=p.row_id)")][:1]
if empty:
    ids, note = filter_by_subject(conn, [P_CD1, P_ONLY_DN, empty[0]], mem_dn, "x"); assert empty[0] in ids and note["kind"] == "shrink", (ids, note)

with TestClient(main.app) as c:
    # ---- GET /memory: trống + danh mục
    g = c.get("/memory", headers=A).json()
    assert g["profile"] == {"province": "", "commune": "", "user_type": "", "note": ""} and g["mcq"] == {} and g["effective"]["subjects"] == [], g
    cat = g["catalog"]
    assert len(cat["provinces"]) == 63 and cat["axes"] == ["subject"] and set(cat["user_types"]) == {"citizen", "business", "other"}
    names = {x["name"] for x in cat["subjects"]}
    assert names == {r[0] for r in conn.execute("SELECT DISTINCT TRIM(subject_name) FROM procedure_subjects WHERE TRIM(subject_name)<>''")} - {n for n in () }, names ^ set()
    assert "Công dân Việt Nam" in names and DN in names
    assert cat["user_type_subjects"]["citizen"] == ["Công dân Việt Nam"] and set(cat["user_type_subjects"]["business"]) <= names
    assert c.get("/memory").json()["client_id"] == "default"                                  # thiếu header
    assert c.get("/memory", headers={"X-Client-Id": "a b/../"}).status_code == 400              # id sai định dạng

    # ---- hồ sơ: lưu, sửa từng phần, xoá bằng chuỗi rỗng
    r = c.put("/memory/profile", headers=A, json={"province": "Hà Nội", "commune": "Phường Cầu Giấy", "user_type": "business", "note": "  mở quán cà phê  "})
    assert r.status_code == 200, r.text
    p = r.json()["profile"]; assert p == {"province": "Hà Nội", "commune": "Phường Cầu Giấy", "user_type": "business", "note": "mở quán cà phê"}, p
    assert r.json()["effective"] == {"subjects": sorted(["Doanh nghiệp", "Doanh nghiệp Việt Nam"]), "source": "user_type"}
    r = c.post("/memory/profile", headers=A, json={"note": ""}); assert r.status_code == 200 and r.json()["profile"]["note"] == "" and r.json()["profile"]["province"] == "Hà Nội"   # POST = PUT, chỉ đổi trường có mặt
    # kiểm đầu vào
    for bad in ({"user_type": "vip"}, {"note": "x" * 201}, {"commune": "y" * 81}, {"province": "z" * 61},
                {"note": "CCCD của tôi 012345678901"}, {"note": "gọi 0912345678 nhé"}, {"commune": "số 079123456"}, {"note": "+84912345678"}):
        rr = c.put("/memory/profile", headers=A, json=bad); assert rr.status_code == 400, (bad, rr.status_code)
    assert c.get("/memory", headers=A).json()["profile"]["province"] == "Hà Nội"              # lỗi không làm hỏng dữ liệu cũ
    blob = str(store.mem_all("client-aaa")); assert "0912" not in blob and "012345678901" not in blob, blob   # không lưu PII

    # ---- nhớ MCQ: chỉ trục subject, giá trị phải có trong procedure_subjects
    assert c.post("/memory/mcq", headers=A, json={"axis": "level", "value": "Cấp xã"}).status_code == 400    # bỏ trục 'cấp thực hiện'
    assert c.post("/memory/mcq", headers=A, json={"axis": "subject", "value": "Phi hành gia"}).status_code == 400
    assert c.post("/memory/mcq", headers=A, json={"axis": "subject", "value": ""}).status_code == 400
    r = c.post("/memory/mcq", headers=A, json={"axis": "subject", "value": "Hợp tác xã"}); assert r.status_code == 200, r.text
    assert r.json()["mcq"] == {"subject": "Hợp tác xã"} and r.json()["effective"] == {"subjects": ["Hợp tác xã"], "source": "mcq"}   # lựa chọn nhớ thắng loại người dùng
    assert c.delete("/memory/mcq?axis=level", headers=A).status_code == 400
    assert c.delete("/memory/mcq", headers=A).status_code == 422                               # thiếu axis
    r = c.delete("/memory/mcq?axis=subject", headers=A); assert r.json()["mcq"] == {} and r.json()["profile"]["user_type"] == "business"   # quên một mục, giữ phần còn lại

    # ---- cô lập giữa hai client
    assert c.get("/memory", headers=B).json()["profile"]["province"] == ""
    assert c.put("/memory/profile", headers=B, json={"province": "Đà Nẵng", "user_type": "citizen"}).status_code == 200
    assert c.post("/memory/mcq", headers=B, json={"axis": "subject", "value": "Công dân Việt Nam"}).status_code == 200
    a, b = c.get("/memory", headers=A).json(), c.get("/memory", headers=B).json()
    assert a["profile"]["province"] == "Hà Nội" and b["profile"]["province"] == "Đà Nẵng" and a["mcq"] == {} and b["mcq"]["subject"] == "Công dân Việt Nam"
    assert c.delete("/memory", headers=A).status_code == 200                                    # quên tất cả của A
    assert c.get("/memory", headers=A).json()["profile"]["province"] == "" and c.get("/memory", headers=B).json()["profile"]["province"] == "Đà Nẵng"   # B còn nguyên

    # ---- migration: DB cũ (không có user_memory) mở lại không lỗi
    import sqlite3
    cc = sqlite3.connect(os.environ["S3_DB_PATH"]); cc.execute("DROP TABLE user_memory"); cc.commit(); cc.close()
    store.init_db(); assert store.mem_all("client-aaa") == {}

    # ---- /chat dùng hồ sơ: hỏi lại -> không hỏi lại (đối tượng doanh nghiệp); không hồ sơ -> hỏi như cũ; hồ sơ lạc -> vẫn đúng thủ tục
    h = {"X-Client-Id": "client-chat"}
    base = c.post("/chat", json={"text": Q}, headers=h).json()
    assert base["kind"] == "clarify" and len(base["clarify"]["options"]) >= 3, base["kind"]                # không hồ sơ: hỏi lại như cũ
    assert not any("Theo hồ sơ" in b["text"] for b in base["blocks"])
    c.put("/memory/profile", headers=h, json={"user_type": "business"})
    got = c.post("/chat", json={"text": Q}, headers=h).json()
    assert got["kind"] == "answer" and got["clarify"] is None, got["kind"]
    assert got["blocks"][0]["text"].startswith("Theo hồ sơ của bạn (đối tượng: Hộ kinh doanh / doanh nghiệp) mình chọn «") and "Nếu chưa đúng" in got["blocks"][0]["text"], got["blocks"][0]
    assert any(b.get("proc_id") == P_ONLY_DN for b in got["blocks"]), [b.get("proc_id") for b in got["blocks"]]
    c.put("/memory/profile", headers=h, json={"user_type": "citizen"})
    sh = c.post("/chat", json={"text": Q}, headers=h).json()                                          # người dân: còn hai ứng viên, thẻ chỉ còn các ứng viên hợp
    assert sh["kind"] == "clarify" and len(sh["clarify"]["options"]) == 2 and "Theo hồ sơ của bạn" in sh["clarify"]["question"], sh["clarify"]
    # câu nêu rõ thủ tục khác với hồ sơ: đúng thủ tục theo câu hỏi, hồ sơ không can thiệp (Phase 31: dùng dạng gọi đúng tên 'lưu động'; tên chung 'Đăng ký khai sinh' nay bị hỏi lại, xem p31_variants_test)
    ks = c.post("/chat", json={"text": "Đăng ký khai sinh lưu động cần giấy tờ gì?"}, headers=h).json()
    assert any(b.get("proc_id") == "1.003583" for b in ks["blocks"]) and not any("Theo hồ sơ" in b["text"] for b in ks["blocks"]), ks["blocks"]
    c.put("/memory/profile", headers=h, json={"user_type": "business"})
    ks2 = c.post("/chat", json={"text": "Đăng ký khai sinh lưu động cần giấy tờ gì?"}, headers=h).json()
    assert any(b.get("proc_id") == "1.003583" for b in ks2["blocks"]) and not any("Theo hồ sơ" in b["text"] for b in ks2["blocks"]), ks2["blocks"]
    c.delete("/memory", headers=h)
    again = c.post("/chat", json={"text": Q}, headers=h).json()
    assert again["kind"] == "clarify" and len(again["clarify"]["options"]) == len(base["clarify"]["options"]), again["kind"]   # quên xong: như cũ

    # ---- gợi ý nhớ sau khi bấm nút thẻ hỏi lại (không tự lưu)
    h2 = {"X-Client-Id": "client-suggest"}
    cl = c.post("/chat", json={"text": Q}, headers=h2).json()
    lab = next(o for o in cl["clarify"]["options"] if o.startswith("Đăng ký đất đai, tài sản gắn liền với đất lần đầu"))   # nút của thủ tục chỉ khai Công dân
    pick = c.post("/chat", json={"text": lab, "conversation_id": cl["conversation_id"], "reply_to": cl["message_id"]}, headers=h2).json()
    sg = pick.get("memory_suggest"); assert sg is None or (sg["axis"] == "subject" and sg["value"] in names), sg
    assert c.get("/memory", headers=h2).json()["mcq"] == {}, "không được tự lưu"
    if sg:
        assert c.post("/memory/mcq", headers=h2, json=sg).status_code == 200

# ---- UI tĩnh (nhẹ, không trình duyệt): có nút/panel hồ sơ, gửi X-Client-Id, cache-bust cả css và js, trang gốc phục vụ được
    html = c.get("/").text
    assert 'id="mem-btn"' in html and 'id="mem-panel"' in html, "thiếu nút/panel Hồ sơ của bạn"
    import re as _re
    v = set(_re.findall(r"\?v=(\w+)", html)); assert len(v) == 1 and "20261006g" not in v, v        # css và js cùng một ?v= mới
    js = c.get("/static/js/chat.js").text
    for need in ("X-Client-Id", "s3_client", "/memory/profile", "/memory/mcq", "memory_suggest", "Quên tất cả"):
        assert need in js, need
    assert "FINAL-PRODUCT" + ": [B4][MEM]" in js

print("p26_memory_test OK")

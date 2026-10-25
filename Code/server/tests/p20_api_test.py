"""Phase 20: GET /procedure/{id}/table, GET/POST /config (answer_llm), nút bảng (proc_id trong block). Chạy: python tests/p20_api_test.py"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_DEV="1", S3_USE_LLM="0")

from fastapi.testclient import TestClient
import main
from system3.data import api as data_api

KS = "1.000689"
with TestClient(main.app) as c:
    # bảng full: đủ 12 mục + nguồn, nguyên văn từ data.api
    r = c.get(f"/procedure/{KS}/table"); assert r.status_code == 200, r.text
    t = r.json()
    assert [x["field"] for x in t["rows"]] == ["components", "fees", "processing_time", "address", "methods", "online",
                                               "steps", "files", "agency", "meta", "legal_basis", "explanation"], t["rows"]
    conn = data_api.connect()
    comp = " ".join(ch["text"].strip() for ch in data_api.fields(conn, KS, ["components"]))
    assert len(next(x for x in t["rows"] if x["field"] == "components")["text"]) >= len(comp.strip()) - 5, "components bị cắt"
    assert t["name"] and t["sources"] and any(x["status"] == "present" for x in t["rows"])
    assert c.get("/procedure/khong-co/table").status_code == 404

    # block trả lời mang proc_id; hỏi chung -> có dòng "bấm Tạo bảng full"
    a = c.post("/chat", json={"text": "Đăng ký tạm trú cần giấy tờ gì?"}).json()
    assert any(b.get("proc_id") for b in a["blocks"]), a["blocks"]
    assert all("xem đầy đủ trên Cổng" not in b["text"] for b in a["blocks"])
    # câu có lời chào/không thủ tục: không có proc_id
    h = c.post("/chat", json={"text": "xin chào"}).json()
    assert not any(b.get("proc_id") for b in h["blocks"]), h["blocks"]

    # reset chủ đề: "cái thứ nhất" không còn trỏ vào danh sách của thẻ hỏi lại cũ
    b = c.post("/chat", json={"text": "Tôi muốn xin trợ cấp hàng tháng"}).json()
    assert b["kind"] == "clarify", b
    assert c.post(f"/conversations/{b['conversation_id']}/reset_facts").status_code == 200
    z = c.post("/chat", json={"text": "cái thứ nhất", "conversation_id": b["conversation_id"]}).json()
    assert not any(x.get("proc_id") for x in z["blocks"]), z["blocks"]

    # quản lý hộp thoại: đổi tên, xoá một, xoá tất cả
    ids = [c.post("/chat", json={"text": t}).json()["conversation_id"] for t in ("xin chào", "xin chào bạn")]
    r = c.patch(f"/conversations/{ids[0]}", json={"title": "  Hồ sơ khai sinh của con  "}); assert r.status_code == 200 and r.json()["title"] == "Hồ sơ khai sinh của con", r.text
    assert any(x["id"] == ids[0] and x["title"] == "Hồ sơ khai sinh của con" for x in c.get("/conversations").json()["conversations"])
    assert c.patch(f"/conversations/{ids[0]}", json={"title": "x" * 200}).json()["title"] == "x" * 60
    assert c.patch("/conversations/khong-co", json={"title": "a"}).status_code == 404
    # ghim: lên đầu danh sách, giữ sau khi đổi tên, bỏ ghim thì về chỗ cũ
    ids.append(c.post("/chat", json={"text": "xin chào nhé"}).json()["conversation_id"])
    order = lambda: [x["id"] for x in c.get("/conversations").json()["conversations"]]
    assert order()[0] == ids[2], order()                                    # mới nhất ở đầu
    r = c.patch(f"/conversations/{ids[0]}", json={"pinned": True}); assert r.status_code == 200 and r.json()["pinned"] is True, r.text
    assert order()[0] == ids[0], order()                                    # ghim lên đầu dù cũ nhất
    assert c.patch(f"/conversations/{ids[0]}", json={"title": "Tên mới"}).json()["pinned"] is True
    assert next(x for x in c.get("/conversations").json()["conversations"] if x["id"] == ids[0])["pinned"] == 1
    assert c.patch(f"/conversations/{ids[0]}", json={"pinned": False}).json()["pinned"] is False
    assert order()[0] == ids[2], order()                                    # bỏ ghim: về đúng thứ tự thời gian
    assert c.patch(f"/conversations/{ids[1]}", json={"pinned": True}).status_code == 200
    assert c.delete(f"/conversations/{ids[0]}").status_code == 200
    assert order()[0] == ids[1], order()                                    # xoá hộp thoại khác không đổi thứ tự ghim
    assert c.patch(f"/conversations/{ids[1]}", json={"pinned": False}).status_code == 200
    assert c.get(f"/conversations/{ids[0]}/messages").status_code == 404
    assert c.delete(f"/conversations/{ids[0]}").status_code == 404
    assert any(x["id"] == ids[1] for x in c.get("/conversations").json()["conversations"])      # xoá một không đụng cái khác
    # xuất file: Markdown + JSON, chỉ nội dung người dùng thấy
    ex = c.post("/chat", json={"text": "Đăng ký tạm trú cần giấy tờ gì?"}).json()["conversation_id"]
    c.post("/chat", json={"text": "còn lệ phí?", "conversation_id": ex})
    c.patch(f"/conversations/{ex}", json={"title": "Khai sinh của bé Đạt"})
    md = c.get(f"/conversations/{ex}/export?format=md"); assert md.status_code == 200, md.text
    assert md.headers["content-disposition"] == 'attachment; filename="Khai-sinh-cua-be-Dat.md"', md.headers["content-disposition"]
    assert md.text.startswith("# Khai sinh của bé Đạt") and "**Bạn:** Đăng ký tạm trú cần giấy tờ gì?" in md.text and "**Trợ lý:**" in md.text and "Nguồn:" in md.text, md.text[:400]
    js_ = c.get(f"/conversations/{ex}/export?format=json").json()
    assert js_["title"] == "Khai sinh của bé Đạt" and [m["role"] for m in js_["messages"]] == ["user", "assistant", "user", "assistant"], js_
    assert not any("plan" in m or "trace" in m for m in js_["messages"]) and js_["messages"][1]["blocks"][0]["sources"], js_["messages"][1]
    cl = c.post("/chat", json={"text": "Tôi muốn xin trợ cấp hàng tháng"}).json()["conversation_id"]
    assert "1. " in c.get(f"/conversations/{cl}/export").text                       # thẻ hỏi lại xuất thành danh sách đánh số
    assert c.get(f"/conversations/{ex}/export?format=pdf").status_code == 200
    xs = c.post("/chat", json={"text": "<script>alert(1)</script> đăng ký khai sinh <b>x</b>"}).json()["conversation_id"]
    pdf = c.get(f"/conversations/{xs}/export?format=pdf"); assert pdf.headers["content-type"].startswith("text/html"), pdf.headers
    assert "<script>alert(1)" not in pdf.text and "&lt;script&gt;alert(1)&lt;/script&gt;" in pdf.text and "window.print()" in pdf.text, pdf.text[:600]   # escape HTML + tự mở hộp thoại in
    assert "Khai sinh của bé Đạt" in c.get(f"/conversations/{ex}/export?format=pdf").text and 'class="turn user"' in pdf.text
    assert c.get(f"/conversations/{ex}/export?format=docx").status_code == 400
    assert c.get("/conversations/khong-co/export").status_code == 404

    assert c.delete("/conversations").status_code == 200 and c.get("/conversations").json()["conversations"] == []

    # /config: answer_llm, model_loaded, đổi trong bộ nhớ khi dev
    g = c.get("/config").json()
    assert g["answer_llm"] is False and g["dev"] is True and "model_loaded" in g and g["table_button"] is True, g
    assert c.post("/config", json={"answer_llm": True}).json()["answer_llm"] is True
    assert os.environ["S3_USE_LLM"] == "1" and c.get("/config").json()["answer_llm"] is True
    assert c.post("/config", json={"answer_llm": False, "mode": "rules"}).json()["answer_llm"] is False
    main.DEV_MODE = False                          # không dev: 403, vẫn đọc được
    assert c.post("/config", json={"answer_llm": True}).status_code == 403
    assert c.get("/config").json()["answer_llm"] is False
    main.DEV_MODE = True

    # cờ tắt nút: endpoint 404
    main.TABLE_BUTTON = False
    assert c.get(f"/procedure/{KS}/table").status_code == 404
    main.TABLE_BUTTON = True
print("OK p20_api_test")

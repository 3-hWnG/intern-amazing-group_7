"""Phase 31: câu chỉ nêu TÊN CHUNG của họ thủ tục có >= 3 dạng THẬT (khai sinh, kết hôn, khai tử, nhận cha mẹ con, Bằng Tổ quốc ghi công) -> hỏi lại (thẻ liệt kê các dạng);
KHÔNG hỏi khi: đã nêu từ phân biệt/đối tượng, hồ sơ người dùng chốt được một dạng, hội thoại đã chốt dạng, họ chỉ có 2 dạng, bản chỉ khác tỉnh/tên gần trùng, thủ tục một dạng.
Nút thẻ hỏi lại và nút "dạng khác" vẫn trả đúng dạng đã chọn (không hỏi lần hai, kể cả bản mặc định có tên trùng tên chung). Chạy: python tests/p31_variants_test.py"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0", S3_PLANNER_MODE="rules", S3_NO_WARMUP="1", S3_FAMILY_CLARIFY="1")

from fastapi.testclient import TestClient
import main
from planner import plan as make_plan
from policy import check, pre_check
from policy.policy import real_variants
from system3.data import api as data_api

conn = data_api.connect()


def route(q, memory=None, turns=None):
    pc = pre_check(q)
    t = (turns or []) + [{"role": "user", "text": pc["text"]}]
    return check(make_plan(t, use_llm=False), user_text=pc["text"], conn=conn, flags=pc["flags"], memory=memory)


KS = {"1.001193", "1.003583", "2.000528", "1.000689", "1.004772", "1.000110", "1.001695", "1.000893"}
# ---- dạng THẬT từ DB
assert set(real_variants(conn, "dang ky khai sinh")) == KS
assert len(real_variants(conn, "dang ky ket hon")) == 4 and len(real_variants(conn, "dang ky khai tu")) == 4 and len(real_variants(conn, "dang ky nhan cha me con")) == 3
assert real_variants(conn, "dang ky giam ho") == []                                      # chỉ 2 dạng: giữ bản mặc định + nút
assert real_variants(conn, "hoa giai tranh chap dat dai") == []                          # 1 bản không tỉnh + các bản tỉnh trùng nội dung: không tính
assert real_variants(conn, "cong nhan va giai quyet che do uu dai nguoi hoat dong cach mang") == []   # 2 bản tên chỉ khác dấu chấm cuối

# ---- hỏi lại: tên chung / tên lõi (kèm mục hỏi, lời đệm)
for q in ["đăng ký khai sinh", "Thủ tục đăng ký khai sinh", "khai sinh", "em muốn đăng ký khai sinh", "đăng ký khai sinh cần giấy tờ gì?", "Đăng ký khai sinh lệ phí bao nhiêu?",
          "đăng ký kết hôn", "kết hôn nộp ở đâu", "đăng ký khai tử", "Cho mình hỏi khai tử mất bao lâu", "đăng ký nhận cha, mẹ, con", "cấp bằng tổ quốc ghi công", "dang ky khai sinh", "đăng ký khai sinh ở Hà Nội", "Đăng ký khai tử ở Đà Nẵng cần giấy tờ gì"]:      # tên tỉnh không chọn dạng nào
    r = route(q)
    ids = [o["proc_id"] for o in (r.clarify or {}).get("options", [])]
    assert r.behavior == "clarify" and len(ids) >= 3, (q, r.behavior, ids)
    assert all(not conn.execute("SELECT province FROM procedures WHERE proc_id=?", (i,)).fetchone()[0] for i in ids), q      # không hiện bản riêng tỉnh
    assert len(set(ids)) == len(ids) and "nhiều dạng" in r.clarify["question"], r.clarify
ids = [o["proc_id"] for o in route("đăng ký khai sinh").clarify["options"]]
assert ids[0] == "1.001193" and set(ids) <= KS and len(ids) == 6, ids                   # bản mặc định đứng đầu; thẻ giới hạn 6 nút (còn lại: gõ tự do)

# ---- KHÔNG hỏi: đã nêu từ phân biệt / đối tượng
for q, want in [("đăng ký khai sinh lưu động", "1.003583"), ("đăng ký khai sinh có yếu tố nước ngoài", "2.000528"), ("khai sinh kết hợp nhận cha mẹ con", "1.000689"),
                ("đăng ký khai sinh trong nước", None), ("đăng ký khai sinh cho con", None), ("em muốn đăng ký khai sinh cho bé nhà em", None), ("đăng ký khai tử cho ông nội", None),
                ("đăng ký nhận cha, mẹ, con cho con tôi", None), ("đăng ký kết hôn tại khu vực biên giới có yếu tố nước ngoài", "1.000094"), ("đăng ký lại khai sinh", "1.004884"),
                ("đăng ký giám hộ", "1.004837")]:
    r = route(q)
    assert r.behavior == "answer", (q, r.behavior)
    assert want is None or r.tasks[0].procedure_id == want, (q, r.tasks[0].procedure_id)
r = route("đăng ký giám hộ")                                                              # 2 dạng: bản mặc định + nút "dạng khác"
assert r.tasks[0].variants.get("others"), r.tasks[0].variants

# ---- hồ sơ người dùng (Phase 26) lọc trước khi hỏi
r = route("đăng ký khai sinh", memory={"subjects": {"Người nước ngoài"}, "label": "Người nước ngoài"})
assert r.behavior == "answer" and r.tasks[0].procedure_id == "1.001695" and r.memory_note["kind"] == "pick", (r.behavior, r.memory_note)   # đúng 1 dạng hợp
r = route("đăng ký khai sinh", memory={"subjects": {"Công dân Việt Nam"}, "label": "Công dân Việt Nam"})
assert r.behavior == "clarify" and len(r.clarify["options"]) >= 3, r.behavior            # ai cũng hợp: không bớt hỏi
r = route("đăng ký khai sinh", memory={"subjects": {"Người Việt Nam định cư ở nước ngoài"}, "label": "Việt kiều"})
ids = {o["proc_id"] for o in r.clarify["options"]}
assert r.behavior == "clarify" and ids <= {"2.000528", "1.001695", "1.000893", "1.001193"} and len(ids) >= 2 and "Theo hồ sơ" in r.clarify["question"], (r.behavior, ids)   # thẻ thu hẹp

# ---- hội thoại: lượt trước đã chốt dạng -> lượt sau hỏi mục không hỏi lại
turns = [{"role": "user", "text": "đăng ký khai sinh lưu động"}, {"role": "assistant", "text": "Về «Thủ tục đăng ký khai sinh lưu động»: bạn cần chuẩn bị hồ sơ theo quy định. Bạn muốn hỏi thêm gì không?"}]
r = route("còn lệ phí?", turns=turns)
assert r.behavior == "answer" and r.tasks[0].procedure_id == "1.003583", (r.behavior, r.tasks[0].procedure_id)

# ---- đường /chat: thẻ -> bấm nút -> trả lời đúng dạng; nút "dạng khác" (kể cả dạng mặc định có tên trùng tên chung) không bị hỏi lại
with TestClient(main.app) as c:
    cl = c.post("/chat", json={"text": "Đăng ký khai sinh cần giấy tờ gì?"}).json()
    assert cl["kind"] == "clarify" and len(cl["clarify"]["options"]) == 6, cl["kind"]
    lab = next(o for o in cl["clarify"]["options"] if o.endswith("lưu động"))
    a = c.post("/chat", json={"text": lab, "conversation_id": cl["conversation_id"], "reply_to": cl["message_id"]}).json()
    assert a["kind"] == "answer" and any(b.get("proc_id") == "1.003583" for b in a["blocks"]), a["kind"]
    typed = c.post("/chat", json={"text": "có yếu tố nước ngoài", "conversation_id": cl["conversation_id"], "reply_to": cl["message_id"]}).json()    # gõ tự do cũng chốt, không hỏi lần hai
    assert typed["kind"] == "answer", typed["kind"]
    others = [v for b in a["blocks"] for v in (b.get("variants") or {}).get("others", [])]
    default = next(v for v in others if v["proc_id"] == "1.001193")                       # nút về dạng mặc định, nhãn = tên chung
    b = c.post("/chat", json={"text": default["label"], "conversation_id": a["conversation_id"], "proc_id": default["proc_id"]}).json()
    assert b["kind"] == "answer" and any(x.get("proc_id") == "1.001193" for x in b["blocks"]), b["kind"]
    again = c.post("/chat", json={"text": default["label"], "conversation_id": a["conversation_id"]}).json()    # cùng nhãn gõ tay (không kèm proc_id) = câu hỏi mới -> hỏi lại
    assert again["kind"] == "clarify", again["kind"]
    js = c.get("/static/js/chat.js").text
    assert "v.proc_id" in js and "body.proc_id" in js

# ---- công tắc quay về hành vi cũ
os.environ["S3_FAMILY_CLARIFY"] = "0"
r = route("đăng ký khai sinh")
assert r.behavior == "answer" and r.tasks[0].procedure_id == "1.001193" and r.tasks[0].variants.get("others"), r.behavior
print("p31_variants_test OK")

"""G4.5 (D6): tên hội thoại Strict = tên thủ tục của lượt trả lời trực tiếp ĐẦU TIÊN; trước đó tạm dùng câu đầu đã che số.
Chạy: python run_server.py server/tests/title_test.py"""
import os, sqlite3, sys, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
DB = os.path.join(tempfile.mkdtemp(), "s3.db")
os.environ.update(S3_DB_PATH=DB, S3_USE_LLM="0", S3_NO_WARMUP="1", S3_PLANNER_MODE="rules", S3_DEV="1")
from fastapi.testclient import TestClient
import main
from db import store


def title(cid):
    return next(c["title"] for c in store.list_conversations() if c["id"] == cid)


def short(label):   # cùng cách cắt với store.set_title_procedure
    return label if len(label) <= 60 else label[:59].rsplit(" ", 1)[0] + "…"


def first_label(out):
    return next(t["procedure_label"] for t in out["dev"]["trace"]["routed"]["tasks"] if t["route"] == "direct")


with TestClient(main.app) as c:
    chat = lambda **b: c.post("/chat", json=b).json()
    # câu đầu trả lời trực tiếp: tên = tên thủ tục; lượt sau hỏi thủ tục khác không đổi tên
    out = chat(text="Cho mình hỏi đăng ký khai sinh cần giấy tờ gì vậy?")
    cid = out["conversation_id"]
    assert out["kind"] == "answer" and title(cid) == short(first_label(out)), (title(cid), first_label(out))
    t1 = title(cid)
    chat(text="Đăng ký kết hôn cần giấy tờ gì?", conversation_id=cid)
    assert title(cid) == t1, "chỉ lượt trả lời trực tiếp ĐẦU TIÊN đặt tên"
    # câu đầu không trả lời trực tiếp (chào): tên tạm = câu đầu đã che số; lượt trả lời trực tiếp sau đó đổi sang tên thủ tục
    out = chat(text="Chào bạn, số tôi 0912345678")
    cid2 = out["conversation_id"]
    assert "0912345678" not in title(cid2) and title(cid2).startswith("Chào bạn"), title(cid2)
    out = chat(text="Đăng ký kết hôn cần giấy tờ gì?", conversation_id=cid2)
    assert title(cid2) == short(first_label(out)), (title(cid2), first_label(out))
    # người dùng tự đổi tên: không bị ghi đè
    out = chat(text="xin chào")
    cid3 = out["conversation_id"]
    assert c.patch(f"/conversations/{cid3}", json={"title": "Việc nhà"}).status_code == 200
    chat(text="Đăng ký khai tử cần giấy tờ gì?", conversation_id=cid3)
    assert title(cid3) == "Việc nhà"
    # tên dài: cắt gọn ở ranh giới chữ, tối đa 60 ký tự
    store.set_title_procedure(store.ensure_conversation(None), "x" * 10)
    cid4 = store.ensure_conversation(None)
    store.set_title_procedure(cid4, "Đăng ký " + "rất dài " * 20)
    assert len(title(cid4)) <= 60 and title(cid4).endswith("…"), title(cid4)
# DB cũ (chưa có cột title_src): hội thoại cũ giữ nguyên tên
old = os.path.join(tempfile.mkdtemp(), "old.db")
con = sqlite3.connect(old)
con.execute("CREATE TABLE conversations (id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "title TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới', pinned INTEGER NOT NULL DEFAULT 0)")
con.execute("INSERT INTO conversations(id,title) VALUES ('c1','Hỏi về đất')")
con.commit(); con.close()
store.DB_PATH = __import__("pathlib").Path(old)
store.init_db()
store.set_title_procedure("c1", "Đăng ký khai sinh")
assert next(c["title"] for c in store.list_conversations() if c["id"] == "c1") == "Hỏi về đất"
print("OK title_test")

"""G4.6: tóm tắt hội thoại dài giữ tên chủ đề / thủ tục đang hỏi (system4/server/context.py). LLM giả.
Chạy: python run_server.py system4/tests/summary_topic_test.py"""
import os, sys, tempfile
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, context, db, llm, settings

asked = []
llm.chat_json = lambda messages, schema, timeout=60: (asked.append(messages), {"summary": "Người dùng hỏi về thủ tục đó và đã được trả lời."})[1]

with TestClient(main.app) as c:
    assert c.post("/s4/auth/signup", json={"username": "tomtat", "password": "123456"}).cookies.get(auth.COOKIE)
uid = db.run("SELECT id FROM users WHERE username='tomtat'", one=True)["id"]
settings.save({"FRIENDLY_HISTORY_MESSAGES": 4})
cid = db.create_conversation(uid, 2)
parent = None
SRC = {"n": 1, "record_id": 1, "url": None, "title": "Đăng ký khai sinh lưu động", "dataset": "Thủ tục", "score": 0.9}
for i in range(6):
    parent = db.add_message(cid, "user", f"Câu hỏi số {i} về khai sinh lưu động", "done", parent)
    parent = db.add_message(cid, "assistant", f"Trả lời {i} [1]", "done", parent, {"sources": [SRC]})
assert context.maybe_summarize(cid)
summary, upto = db.get_summary(cid)
assert summary.startswith("Đang nói về: Đăng ký khai sinh lưu động. "), summary
assert asked and asked[-1][0]["content"] == context.TOPIC_PROMPT and "Câu ĐẦU TIÊN nêu đúng tên" in context.TOPIC_PROMPT
# tóm tắt đã có tên: không ghép thêm
assert context.keep_topics("Người dùng hỏi về đăng ký khai sinh lưu động.", [{"role": "assistant", "meta": {"sources": [SRC]}}]) \
    == "Người dùng hỏi về đăng ký khai sinh lưu động."
assert context.keep_topics("Không có nguồn.", [{"role": "assistant", "meta": {}}]) == "Không có nguồn."
print("OK summary_topic_test")

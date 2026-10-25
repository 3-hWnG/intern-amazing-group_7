"""Hỏi lại khi mơ hồ (18/10, research/clarify/RESULTS.md):
M1 — chữ đệm hội thoại ("đang tìm hiểu", "bao gồm [giấy tờ]", "liên quan đến", "hỏi về") không lọt vào cụm tên thủ tục;
M2 — hỏi về thủ tục mà không nêu thủ tục nào, ở đầu hội thoại -> hỏi "Bạn muốn hỏi về thủ tục nào?" (trước đây: xin lỗi, hoặc trả lời bừa).
Chạy: python run_server.py server/tests/clarify_vague_test.py"""
import os, sys, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0", S3_NO_WARMUP="1", S3_PLANNER_MODE="rules", S3_DEV="1")
from fastapi.testclient import TestClient
import main
from system3.data import api
from system3.retrieval.query import understand

conn = api.connect()
U = lambda q: understand(conn, q)
# ---- M1
assert U("Thủ tục bao gồm những giấy tờ nào").terms == [] and U("Thủ tục bao gồm những giấy tờ nào").fields == ["components"]
assert "dang" not in U("tôi đang tìm hiểu đường bộ").terms
assert "lien" not in U("liên quan đến cư trú làm thế nào ạ").terms
assert U("mình cần biết về quân nhân").terms[:1] != ["ve"]
assert "dang" in U("hộ gia đình đang sử dụng đất cần giấy tờ gì").terms, "không bỏ 'đang' đứng một mình (tên thủ tục có 'đang sử dụng đất')"
assert "bao" in U("hành vi lợi dụng tôn giáo bao gồm những hành vi như thế nào").terms, "'bao gồm' chỉ bỏ trước giấy tờ/hồ sơ/gì"
os.environ["S3_CLARIFY_FILLER"] = "0"
assert U("Thủ tục bao gồm những giấy tờ nào").terms == ["bao", "gom"], "tắt M1: như trước"
os.environ["S3_CLARIFY_FILLER"] = "1"

# ---- M2 qua /chat
with TestClient(main.app) as c:
    chat = lambda **b: c.post("/chat", json=b).json()
    for q in ("Thủ tục bao gồm những giấy tờ nào", "cần giấy tờ gì", "Tôi muốn làm giấy tờ cho con", "lệ phí bao nhiêu", "tôi đang tìm hiểu thôi"):
        out = chat(text=q)
        assert out["kind"] == "clarify" and out["clarify"]["meta"].get("kind") == "no_procedure", (q, out["kind"], out["blocks"][:1])
        assert "Thủ tục đăng ký khai sinh" in out["clarify"]["options"]
    # bấm một lựa chọn -> trả lời thủ tục đó, không hỏi lại lần 2
    out = chat(text="cần giấy tờ gì")
    out2 = chat(text="Thủ tục đăng ký khai sinh", conversation_id=out["conversation_id"], reply_to=out["message_id"])
    assert out2["kind"] == "answer" and "khai sinh" in out2["blocks"][0]["title"].lower(), out2["blocks"][:1]
    # đã có chủ đề trong hội thoại: "cần giấy tờ gì" kế thừa chủ đề, KHÔNG hỏi lại
    out = chat(text="Đăng ký kết hôn lệ phí bao nhiêu?")
    out2 = chat(text="cần giấy tờ gì", conversation_id=out["conversation_id"])
    assert out2["kind"] == "answer" and "kết hôn" in out2["blocks"][0]["title"].lower(), out2["blocks"][:1]
    # lời chào vẫn là xã giao
    assert chat(text="xin chào")["kind"] == "chitchat"
    os.environ["S3_CLARIFY_NOPROC"] = "0"
    assert chat(text="cần giấy tờ gì")["kind"] != "clarify", "tắt M2: như trước"
print("OK clarify_vague_test")

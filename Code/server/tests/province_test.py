"""G4.4 (D5): thủ tục có bản riêng của tỉnh -> hỏi "Bạn làm thủ tục ở tỉnh/thành nào?"; câu trả lời giữ cho cả hội thoại.
Chạy trên DB cố định: python run_server.py server/tests/province_test.py"""
import os, sys, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0", S3_NO_WARMUP="1", S3_PLANNER_MODE="rules", S3_DEV="1")

from fastapi.testclient import TestClient
import main, user_memory
from policy.policy import NATIONWIDE_LABEL
from system3.data import api

conn = api.connect()
assert user_memory.provinces() == sorted(api.provinces(conn)), "danh sách tỉnh lấy từ dữ liệu"
assert api.provinces_in("Tôi ở tphcm, làm ở Sài Gòn") == ["Hồ Chí Minh"] and api.provinces_in("đăng ký khai sinh") == []
nat = [r[0] for r in conn.execute("SELECT proc_id FROM proc_flat WHERE in_scope=1")]
fams = [(p, api.province_versions(conn, p)) for p in nat]
fams = [(p, v) for p, v in fams if len(v) >= 2]
assert fams, "DB cố định phải có thủ tục toàn quốc có bản riêng tỉnh"


def pid_of(out):
    ts = out["dev"]["trace"]["routed"]["tasks"]
    return ts[0]["procedure_id"] if ts else None


with TestClient(main.app) as c:
    chat = lambda **b: c.post("/chat", json=b).json()
    # ---- tìm một thủ tục mà câu hỏi nêu đúng tên được trả lời trực tiếp (không vướng hỏi lại kiểu khác) -> giờ phải hỏi tỉnh
    found = None
    for pid, pv in fams[:40]:
        name = conn.execute("SELECT name FROM procedures WHERE proc_id=?", (pid,)).fetchone()[0]
        out = chat(text=f"{name} cần giấy tờ gì?")
        cl = out.get("clarify")
        if cl and cl["meta"].get("kind") == "province":
            found = (pid, pv, name, out)
            break
    assert found, "không thủ tục nào ra thẻ hỏi tỉnh"
    pid, pv, name, out = found
    cl = out["clarify"]
    assert cl["options"][-1] == NATIONWIDE_LABEL and 2 <= len(cl["options"]) <= 7, cl["options"]
    assert all(o in pv for o in cl["options"][:-1]) and cl["meta"]["option_ids"][NATIONWIDE_LABEL] == pid
    cid = out["conversation_id"]
    # ---- bấm một tỉnh -> trả lời bằng bản của tỉnh đó, gợi ý nhớ tỉnh cho tài khoản
    prov = cl["options"][0]
    out = chat(text=prov, conversation_id=cid, reply_to=out["message_id"])
    assert out["kind"] != "clarify" and pid_of(out) == pv[prov], (pid_of(out), pv[prov])
    assert out.get("memory_suggest") == {"axis": "province", "value": prov}, out.get("memory_suggest")
    assert out["dev"]["trace"]["state"].get("province") == prov
    # ---- cùng hội thoại, hỏi lại thủ tục đó: không hỏi tỉnh nữa, dùng bản của tỉnh đã chọn (có câu báo)
    out = chat(text=f"{name} lệ phí bao nhiêu?", conversation_id=cid)
    assert not out.get("clarify") and pid_of(out) == pv[prov], out.get("clarify")
    assert any(f"bản riêng của {prov}" in b["text"] for b in out["blocks"]), [b["text"][:80] for b in out["blocks"]]
    # ---- hội thoại mới, câu nêu tỉnh có bản riêng: không hỏi, dùng bản của tỉnh đó
    prov2 = list(pv)[-1]
    out = chat(text=f"{name} ở {prov2} cần giấy tờ gì?")
    assert not out.get("clarify") and pid_of(out) == pv[prov2], (prov2, pid_of(out))
    # ---- nêu tỉnh không có bản riêng: dùng bản chung toàn quốc, có câu báo
    other = next(p for p in api.provinces(conn) if p not in pv)
    out = chat(text=f"{name} ở {other} cần giấy tờ gì?")
    assert not out.get("clarify") and pid_of(out) == pid, (other, pid_of(out))
    assert any(f"{other} không có bản riêng" in b["text"] for b in out["blocks"]), [b["text"][:80] for b in out["blocks"]]
    # ---- chọn "Áp dụng chung toàn quốc": bản chung, lượt sau không hỏi lại
    out = chat(text=f"{name} cần giấy tờ gì?")
    cid3 = out["conversation_id"]
    out = chat(text=NATIONWIDE_LABEL, conversation_id=cid3, reply_to=out["message_id"])
    assert pid_of(out) == pid and "memory_suggest" not in out
    out = chat(text=f"{name} mất bao lâu?", conversation_id=cid3)
    assert not out.get("clarify") and pid_of(out) == pid
    # ---- hồ sơ có tỉnh (gõ kiểu khác vẫn nhận): không hỏi
    assert c.post("/memory/profile", json={"province": prov2}).status_code == 200
    out = chat(text=f"{name} cần giấy tờ gì?")
    assert not out.get("clarify") and pid_of(out) == pv[prov2]
    c.post("/memory/profile", json={"province": ""})
    # ---- tắt tính năng
    os.environ["S3_PROVINCE_CLARIFY"] = "0"
    out = chat(text=f"{name} cần giấy tờ gì?")
    assert not (out.get("clarify") or {}).get("meta", {}).get("kind") == "province"
print("OK province_test")

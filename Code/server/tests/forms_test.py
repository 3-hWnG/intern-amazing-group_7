"""G4.7 (D7): câu trả lời về biểu mẫu kèm tên mẫu + link trang thủ tục trên Cổng (Cổng trả tệp 0 byte nên không có bản lưu).
Chạy: python run_server.py server/tests/forms_test.py"""
import os, re, sys, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0", S3_NO_WARMUP="1", S3_PLANNER_MODE="rules")
from fastapi.testclient import TestClient
import main
from answer.answerer import procedure_table
from system3.data import api

conn = api.connect()
LINK = re.compile(r"https://dichvucong\.gov\.vn/thu-tuc-hanh-chinh/\S+")


def text(out):
    return "\n".join(b["text"] for b in out["blocks"])


with TestClient(main.app) as c:
    # câu của kế hoạch: mẫu tờ khai đăng ký khai sinh -> có link + tên mẫu (lấy từ thành phần hồ sơ, Cổng không đính kèm tệp)
    t = text(c.post("/chat", json={"text": "mẫu tờ khai đăng ký khai sinh"}).json())
    assert "Biểu mẫu" in t and LINK.search(t) and "Tờ khai đăng ký khai sinh" in t, t[:600]
    assert "không có biểu mẫu đính kèm cho thủ tục này" not in t
    # thủ tục Cổng liệt kê tệp mẫu: tên mẫu + tên tệp + link
    pid, name = next((p, n) for p, n in conn.execute("SELECT proc_id, name FROM proc_flat WHERE in_scope=1 ORDER BY proc_id")
                     if api.forms(conn, p) and len(n) < 80)
    f0 = api.forms(conn, pid)[0]
    t = text(c.post("/chat", json={"text": f"{name} có biểu mẫu gì?"}).json())
    assert LINK.search(t) and f0["file"] in t and "Tải mẫu tại trang thủ tục" in t, (name, t[:600])
# bảng đầy đủ cũng có tên mẫu + link
row = next(r for r in procedure_table(conn, pid)["rows"] if r["field"] == "files")
assert row["status"] == "present" and f0["file"] in row["text"] and LINK.search(row["text"])
print("OK forms_test")

"""Kiểm thử tự động toàn hệ thống, KHÔNG cần chạy server và KHÔNG cần Ollama.

    python selftest.py

Thay core.llm.stream_chat bằng bản giả để test được hàng đợi, lưu trữ, tóm tắt
mà không phụ thuộc mô hình đang chạy hay không.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config

# --- cách ly: dùng CSDL tạm, không đụng dữ liệu thật ------------------------
_tmp = Path(tempfile.mkdtemp(prefix="tthc_selftest_"))
config.DB_PATH = _tmp / "test.db"

from db import connection                      # noqa: E402
connection.DB_PATH = config.DB_PATH

import core.llm as llm                          # noqa: E402

_FAKE = ["Thành phần hồ sơ: ", "giấy tờ A, ", "giấy tờ B. ", "Lệ phí: không thu phí."]


def _fake_stream(system, user, history=None):
    for part in _FAKE:
        yield part


def _fake_complete(system, user, history=None):
    return "Tóm tắt giả lập cho kiểm thử."


llm.stream_chat = _fake_stream
llm.complete = _fake_complete

import core.summarizer as summarizer            # noqa: E402
summarizer.llm = llm

from fastapi.testclient import TestClient       # noqa: E402
from main import create_app                     # noqa: E402

PASS, FAIL = "  [ OK ]", "  [FAIL]"
failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"{PASS} {name}")
    else:
        print(f"{FAIL} {name}  {detail}")
        failures.append(name)


def main() -> int:
    print("\n=== SELFTEST ===")
    print(f"  CSDL tạm: {config.DB_PATH}")

    with TestClient(create_app()) as c:
        # ---- xác thực -----------------------------------------------------
        r = c.get("/api/conversations")
        check("chưa đăng nhập thì bị chặn", r.status_code == 401, f"got {r.status_code}")

        r = c.post("/api/register", json={"email": "bad-email", "password": "12345678"})
        check("email sai định dạng bị từ chối", r.status_code == 400)

        r = c.post("/api/register", json={"email": "a@test.vn", "password": "short"})
        check("mật khẩu ngắn bị từ chối", r.status_code == 400)

        r = c.post("/api/register",
                   json={"email": "a@test.vn", "password": "matkhau123", "display_name": "A"})
        check("đăng ký thành công", r.status_code == 200, r.text[:120])

        r = c.post("/api/register", json={"email": "a@test.vn", "password": "matkhau123"})
        check("email trùng bị từ chối", r.status_code == 400)

        r = c.get("/api/me")
        check("lấy được thông tin tài khoản", r.status_code == 200 and r.json()["user"]["email"] == "a@test.vn")
        check("KHÔNG lộ password_hash", "password_hash" not in r.text)

        # ---- hội thoại nhiều cửa sổ ---------------------------------------
        c1 = c.post("/api/conversations", json={}).json()["conversation"]
        c2 = c.post("/api/conversations", json={}).json()["conversation"]
        check("tạo được 2 hội thoại", c1["id"] != c2["id"])

        r = c.get("/api/conversations")
        check("liệt kê đủ 2 hội thoại", len(r.json()["conversations"]) == 2)

        # ---- chat qua hàng đợi --------------------------------------------
        r = c.post(f"/api/conversations/{c1['id']}/chat",
                   json={"text": "Tôi muốn làm giấy khai sinh cho con"})
        body = r.text
        check("chat trả về 200", r.status_code == 200, r.text[:120])
        check("có nội dung trả lời", len(body) > 20, f"len={len(body)}")
        check("có header X-Tier", bool(r.headers.get("X-Tier")))
        check("có header X-Queue-Position", r.headers.get("X-Queue-Position") is not None)

        msgs = c.get(f"/api/conversations/{c1['id']}").json()["messages"]
        check("lưu cả câu hỏi và câu trả lời", len(msgs) == 2, f"n={len(msgs)}")
        check("câu trả lời có gắn tier", bool(msgs[1]["tier"]))

        r = c.get(f"/api/conversations/{c2['id']}").json()
        check("hội thoại kia vẫn rỗng (không lẫn)", len(r["messages"]) == 0)

        r = c.patch(f"/api/conversations/{c1['id']}", json={"title": "Khai sinh"})
        check("đổi tên hội thoại", r.status_code == 200)

        # ---- phản hồi ------------------------------------------------------
        r = c.post("/api/feedback", json={"message_id": msgs[1]["id"], "verdict": "phu_hop"})
        check("gửi phản hồi 👍", r.status_code == 200, r.text[:120])
        r = c.post("/api/feedback", json={"message_id": msgs[1]["id"], "verdict": "sai_gia_tri"})
        check("phản hồi sai giá trị bị chặn", r.status_code == 400)

        # ---- cách ly giữa người dùng --------------------------------------
        other_conv_id = c1["id"]
        c.post("/api/logout")
        c.post("/api/register", json={"email": "b@test.vn", "password": "matkhau123"})
        r = c.get(f"/api/conversations/{other_conv_id}")
        check("KHÔNG xem được hội thoại của người khác", r.status_code == 404,
              f"got {r.status_code}")
        r = c.get("/api/conversations")
        check("người mới không thấy hội thoại cũ", len(r.json()["conversations"]) == 0)

        # ---- đăng nhập sai -------------------------------------------------
        c.post("/api/logout")
        r = c.post("/api/login", json={"email": "a@test.vn", "password": "sai-mat-khau"})
        check("mật khẩu sai bị từ chối", r.status_code == 401)
        r = c.post("/api/login", json={"email": "a@test.vn", "password": "matkhau123"})
        check("đăng nhập lại thành công", r.status_code == 200)

        r = c.get("/api/conversations")
        check("dữ liệu còn nguyên sau khi đăng nhập lại",
              len(r.json()["conversations"]) == 2)

        # ---- tóm tắt ngữ cảnh ---------------------------------------------
        from db.repositories import Conversations as ConvRepo, Messages as MsgRepo
        long_id = c.post("/api/conversations", json={}).json()["conversation"]["id"]
        for i in range(14):
            MsgRepo.add(long_id, "user", ("câu hỏi dài " * 40) + str(i))
            MsgRepo.add(long_id, "assistant", "trả lời dài " * 40)
        summary, recent = summarizer.build_context(long_id)
        check("vượt ngưỡng thì có tóm tắt", bool(summary), "summary rỗng")
        check("giữ lại các lượt gần nhất", 0 < len(recent) <= config.SUMMARY_KEEP_RECENT * 2 + 2,
              f"n={len(recent)}")
        check("tóm tắt được ghi vào CSDL",
              bool(ConvRepo.by_id(long_id)["summary"]))

        # ---- công cụ dev ---------------------------------------------------
        if config.DEV_TOOLS_ENABLED:
            r = c.get("/api/dev/stats")
            check("dev stats hoạt động", r.status_code == 200)
            r = c.post("/api/dev/reset", json={"scope": "my_conversations", "confirm": "sai"})
            check("reset thiếu xác nhận bị chặn", r.status_code == 400)
            r = c.post("/api/dev/reset", json={"scope": "my_conversations", "confirm": "XOA"})
            check("reset hội thoại của tôi", r.status_code == 200, r.text[:120])
            r = c.get("/api/conversations")
            check("sau reset thì sạch", len(r.json()["conversations"]) == 0)

        # ---- hàng đợi tuần tự ---------------------------------------------
        conv = c.post("/api/conversations", json={}).json()["conversation"]
        for i in range(3):
            rr = c.post(f"/api/conversations/{conv['id']}/chat", json={"text": f"câu {i}"})
            if rr.status_code != 200:
                break
        check("gửi liên tiếp 3 câu đều xử lý được", rr.status_code == 200)
        n = len(c.get(f"/api/conversations/{conv['id']}").json()["messages"])
        check("lưu đủ 6 tin nhắn (3 hỏi + 3 đáp)", n == 6, f"n={n}")

    print()
    if failures:
        print(f"  => {len(failures)} KIỂM THỬ HỎNG: {', '.join(failures)}\n")
        return 1
    print("  => TẤT CẢ ĐẠT\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

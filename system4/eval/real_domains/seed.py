"""Nạp 6 bộ dữ liệu thật (data/, build.py) vào web: tạo lĩnh vực mềm Y tế, Giáo dục (Du lịch đã có), tải bằng tài khoản dev, đặt DÙNG CHUNG.

    python run_server.py system4/eval/real_domains/seed.py      # TẮT server trước (Qdrant cục bộ khoá thư mục runtime/qdrant)

Chạy lại được: bộ đã có (cùng tên tệp trong cùng lĩnh vực) thì bỏ qua. Cần Ollama (bge-m3 tạo vector; Qwen đặt tên trường cho đường nhanh).
Cũng xử lý lại luôn các bộ đọc bằng cách đọc cũ (READER_VERSION) để lần bật server sau không phải chờ.
"""
from __future__ import annotations

import os
import socket
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "server"))   # `core` của System 3 (llm.py của System 4 dùng)

from system3.system4.server import datasets, db, fastpath  # noqa: E402

DATA = HERE / "data"
GUARD = {
    "Y tế": ("Thông tin chỉ để tham khảo, không thay cho khám và chẩn đoán của bác sĩ. Không kê đơn, không nêu liều thuốc cụ thể. "
             "Có dấu hiệu cấp cứu (khó thở, đau ngực, co giật, chảy máu nhiều, lơ mơ) thì khuyên gọi 115 hoặc đến cơ sở y tế gần nhất ngay. "
             "Danh sách bệnh viện là của TP.HCM, theo Wikipedia, có thể chưa đầy đủ."),
    "Giáo dục": ("Khi trả lời về quy định, nêu đúng số Điều của Luật Giáo dục 2019 và nói rõ luật có thể đã được sửa đổi sau năm 2019. "
                 "Danh sách trường lấy từ Wikipedia, có thể chưa đầy đủ; không đoán điểm chuẩn, học phí."),
    "Du lịch": ("Thông tin lấy từ Wikipedia và danh sách di tích quốc gia đặc biệt. Giá vé, giờ mở cửa, lịch trình có thể đã thay đổi: "
                "khuyên khách kiểm tra nguồn chính thức trước khi đi."),
}
FILES = [   # (lĩnh vực, tệp, tên hiển thị)
    ("Y tế", "y_te_benh_vien_tphcm.xlsx", "Bệnh viện TP.HCM (Wikipedia)"),
    ("Y tế", "y_te_hoi_dap_bac_si.md", "Hỏi đáp bác sĩ — 300 câu hỏi thật"),
    ("Giáo dục", "giao_duc_truong_dai_hoc.xlsx", "Trường đại học, học viện (Wikipedia)"),
    ("Giáo dục", "giao_duc_luat_giao_duc_2019.txt", "Luật Giáo dục 2019 (toàn văn)"),
    ("Du lịch", "du_lich_di_tich_dac_biet.xlsx", "Di tích quốc gia đặc biệt (Wikipedia)"),
    ("Du lịch", "du_lich_diem_den.md", "Điểm đến du lịch — 6 bài Wikipedia"),
]


def server_running() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", int(os.environ.get("APP_PORT", "8300"))), timeout=1):
            return True
    except OSError:
        return False


def domain(name: str) -> dict:
    d = next((x for x in db.run("SELECT * FROM domains", many=True) if x["name"].casefold() == name.casefold()), None)
    if d is None:
        did = db.run("INSERT INTO domains(name,kind,engine,guardrail,owner_id) VALUES (?,?,?,?,NULL)", (name, "soft", "friendly", GUARD[name]))
        print(f"+ lĩnh vực {name} (id {did})")
        return db.get_domain(did)
    if d["kind"] != "soft" or d["owner_id"] is not None:
        sys.exit(f"Lĩnh vực {name} đã có nhưng không phải lĩnh vực mềm dùng chung (kind={d['kind']}, owner={d['owner_id']}) — dừng.")
    if not d["guardrail"]:
        db.run("UPDATE domains SET guardrail=? WHERE id=?", (GUARD[name], d["id"]))
    return d


def ensure(say=print) -> list[int]:
    """Tạo lĩnh vực + tải các tệp còn thiếu (của dev đầu tiên, dùng chung). Không chờ nạp xong. Dùng trong server (system4/server/bootstrap.py)
    hoặc từ main(). Trả id các bộ dữ liệu (cũ + mới); [] nếu chưa có dev."""
    dev = db.run("SELECT * FROM users WHERE id=?", (db.first_dev_id(),), one=True)
    if not dev:
        return []
    todo = []
    for dname, fname, label in FILES:
        d = domain(dname)
        old = db.run("SELECT * FROM datasets WHERE domain_id=? AND filename=? AND user_id=?", (d["id"], fname, dev["id"]), one=True)
        if old:
            say(f"= {dname}: {fname} đã có (id {old['id']}, {old['status']})")
            if not old["shared"]:
                db.update_dataset(old["id"], shared=1)
            todo.append(old["id"])
            continue
        with open(DATA / fname, "rb") as f:
            ds = datasets.save_upload(dev, fname, f, None, d["id"])
        db.update_dataset(ds["id"], name=label, shared=1)
        say(f"+ {dname}: {label} (id {ds['id']})")
        todo.append(ds["id"])
    return todo


def main() -> None:
    if server_running() and not os.environ.get("S4_RUNTIME_DIR"):   # runtime riêng (chạy thử) không đụng Qdrant của server
        sys.exit("Server đang chạy (cổng 8300): tắt server trước rồi chạy lại (Qdrant cục bộ không cho hai tiến trình cùng mở).")
    db.init_db()
    if not db.first_dev_id():
        sys.exit("Chưa có tài khoản dev")
    datasets.resume_unfinished()   # bộ cũ đọc bằng cách đọc trước (READER_VERSION) -> xử lý lại luôn
    todo = ensure()
    t0, last = time.time(), {}
    while True:   # chờ nạp (bge-m3) + đường nhanh biên dịch xong
        st = {}
        for i in todo:
            ds = db.get_dataset(i)
            fp = fastpath.get(i)
            st[i] = (ds["status"], ds["progress"], fp and fp["status"])
        if st != last:
            print(f"[{int(time.time() - t0)} s]", "  ".join(f"{i}:{s[0]}{'' if s[0] == 'ready' else ' ' + str(s[1]) + '%'}/{s[2] or '-'}" for i, s in st.items()))
            last = st
        if all(s[0] in ("ready", "error") and (s[0] == "error" or s[2] in ("ready", "error", "skipped")) for s in st.values()):
            break
        if time.time() - t0 > 3600:
            sys.exit("Quá 1 giờ chưa xong")
        time.sleep(3)
    for i in todo:
        ds, fp = db.get_dataset(i), fastpath.get(i)
        print(f"{i:4d} {ds['status']:6s} {ds['n_records']:5d} bản ghi · {ds['name']} · {ds['message'][:90]} · đường nhanh: {fp and fp['message'][:80]}")


if __name__ == "__main__":
    main()

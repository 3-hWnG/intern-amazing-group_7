"""Ba lỗi đường nhanh tìm ra trên dữ liệu THẬT (19/10/2026, system4/eval/real_domains) — dòng lấy nguyên từ data/:
1. năm 4 chữ số in thành "2.009"                      -> engine.show giữ nguyên số năm ở cột "Năm …"
2. "Trường Đại học FPT … công lập hay tư thục" ra Swinburne - FPT -> dòng được gọi trọn tên đứng trước dòng chỉ khớp vài chữ
3. "Truyền thuyết về tên gọi Vịnh Hạ Long" ra thẻ dòng di tích  -> cổng chữ lạ xét chữ của CHÍNH bảng, không lẫn chữ của bài văn bản
Model giả. Chạy: python run_server.py system4/tests/fastpath_realdata_test.py"""
import hashlib
import math
import os
import re
import sys
import tempfile
import time

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RUNTIME_DIR=os.path.join(TMP, "s4"),
                  OLLAMA_HOST="http://127.0.0.1:1")

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, db, fastpath, llm, search
from system3.system4.server.fastpath.engine import show
import nv5_off
nv5_off.apply()


def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * 1024
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 1024] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


search.embed = fake_embed
llm.chat_json = lambda *a, **k: {}

assert show("2009", "number", "Năm xếp hạng") == "2009" and show("1900", "number", "Năm thành lập") == "1900"
assert show("1450000", "number", "Giá") == "1.450.000" and show("1800", "number", "Số giường") == "1.800"   # không phải cột năm: như cũ

TRUONG = ("Tên trường,Viết tắt,Giao dịch tiếng Anh,Địa điểm,Cơ quan chủ quản,Loại hình\n"
          "Trường Đại học FPT,FPTU,FPT University,Hà Nội,,Tư thục\n"
          "Trường Đại học Công nghệ Swinburne - FPT Việt Nam,,,,Úc,Nước ngoài\n"
          "Trường Đại học Greenwich - FPT Việt Nam,,,,Anh Quốc,Nước ngoài\n"
          "Trường Đại học Ngoại thương,FTU,Foreign Trade University,Hà Nội,Bộ Giáo dục và Đào tạo,Công lập\n"
          "Trường Đại học Sư phạm Hà Nội,HNUE,Hanoi National University of Education,Hà Nội,Bộ Giáo dục và Đào tạo,Công lập\n"
          "Trường Đại học Kinh tế Quốc dân,NEU,National Economics University,Hà Nội,Bộ Giáo dục và Đào tạo,Công lập\n"
          "Trường Đại học Y Hà Nội,HMU,Hanoi Medical University,Hà Nội,Bộ Y tế,Công lập\n"
          "Trường Đại học Dược Hà Nội,HUP,Hanoi University of Pharmacy,Hà Nội,Bộ Y tế,Công lập\n").encode()
DITICH = ("Tên di tích,Địa điểm,Hạng mục,Đợt xếp hạng,Năm xếp hạng,Ghi chú\n"
          "Vịnh Hạ Long,Vùng ven biển thành phố Quảng Ninh,Danh lam thắng cảnh,Đợt 1,2009,Được UNESCO công nhận là Di sản thiên nhiên thế giới\n"
          "Đô thị cổ Hội An,\"Phường Minh An, thành phố Đà Nẵng\",Di tích kiến trúc nghệ thuật,Đợt 1,2009,Được UNESCO công nhận là Di sản văn hóa thế giới\n"
          "Địa đạo Củ Chi,\"Xã An Nhơn Tây, Thành phố Hồ Chí Minh\",Di tích lịch sử,Đợt 6,2015,\n"
          "Yên Tử,\"Các phường: Yên Tử, Uông Bí, thành phố Quảng Ninh\",\"Di tích lịch sử, danh lam thắng cảnh\",Đợt 3,2012,\n"
          "Cổ Loa,\"Xã Đông Anh, thành phố Hà Nội\",\"Di tích lịch sử, kiến trúc nghệ thuật, khảo cổ\",Đợt 3,2012,\n"
          "Văn Miếu - Quốc Tử Giám,\"Phường Văn Miếu - Quốc Tử Giám, thành phố Hà Nội\",\"Di tích lịch sử, kiến trúc nghệ thuật\",Đợt 2,2012,\n"
          "Khu đền tháp Mỹ Sơn,\"Xã Duy Phú, thành phố Đà Nẵng\",Di tích kiến trúc nghệ thuật,Đợt 1,2009,Được UNESCO công nhận là Di sản văn hóa thế giới\n"
          "Côn Sơn - Kiếp Bạc,\"Phường Trần Hưng Đạo, thành phố Hải Phòng\",\"Di tích lịch sử, kiến trúc nghệ thuật\",Đợt 2,2012,\n").encode()
BAI = ("# Vịnh Hạ Long\n## Truyền thuyết\nTrong tâm thức của người Việt với ý niệm về cội nguồn con Rồng cháu Tiên, một số truyền thuyết cho rằng "
       "Rồng Mẹ và Rồng Con không trở về trời mà ở lại hạ giới; nơi Rồng Mẹ đáp xuống là Hạ Long.\n").encode()

with TestClient(main.app) as c:
    c.cookies.set(auth.COOKIE, c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE))
    ids = {}
    for name, data in (("truong.csv", TRUONG), ("di_tich.csv", DITICH), ("diem_den.md", BAI)):
        ids[name] = c.post("/s4/datasets", files={"file": (name, data)}).json()["dataset"]["id"]
    for _ in range(200):
        if all(db.get_dataset(i)["status"] == "ready" and (fastpath.get(i) or {}).get("status") in ("ready", "error", "skipped")
               for i in ids.values()):
            break
        time.sleep(0.25)
    ask = lambda q, *ds: fastpath.answer([ids[d] for d in ds], q, [], True, True)
    r = ask("Trường Đại học FPT là trường công lập hay tư thục?", "truong.csv")
    assert r["use"] and "Trường Đại học FPT**" in r["result"]["content"] and "Swinburne" not in r["result"]["content"], r["result"]
    r = ask("Trường Đại học FPT viết tắt là gì?", "truong.csv")
    assert r["use"] and r["result"]["content"].endswith("FPTU"), r["result"]
    r = ask("Truyền thuyết về tên gọi Vịnh Hạ Long kể gì?", "di_tich.csv", "diem_den.md")
    assert r["result"].get("route") != "card" and not (r["use"] and r["result"].get("table")), r                # nhường: chữ "truyền thuyết" không có trong BẢNG
    r = ask("Địa điểm của Địa đạo Củ Chi là gì?", "di_tich.csv", "diem_den.md")   # test không có gợi ý AI: hỏi bằng tên cột
    assert r["use"] and "An Nhơn Tây" in r["result"]["content"], r["result"]
    r = ask("Năm xếp hạng của Đô thị cổ Hội An là gì?", "di_tich.csv")
    assert r["use"] and r["result"]["content"].endswith(": 2009"), r["result"]                                  # không phải "2.009"
print("OK fastpath_realdata_test")

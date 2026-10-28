"""J2 (26/10/2026): bốn sửa đổi S4-1..S4-4 của đường nhanh, MỖI CÁI SAU MỘT CỜ. Kiểm: cờ bật cho kết quả đúng, cờ tắt cho kết quả CŨ.
Chỉ dùng dữ liệu dev (real_v3/data, dữ liệu tự dựng) — không đọc bộ mù real_v4_s4. Không cần GPU / Ollama / DB (db.run được thay bằng bản giả).
Chạy: python system4/tests/test_s4_j2.py   (TMP / TEMP trỏ sang ổ còn chỗ)"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "system4"), str(REPO / "server")]
os.environ.update(S4_RUNTIME_DIR=os.path.join(tempfile.mkdtemp(), "s4"), S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0")

import openpyxl  # noqa: E402
from server import db, settings  # noqa: E402
from server.fastpath import _materialize, compile as C, engine, selftest, sqlroute  # noqa: E402

FLAGS = {"FASTPATH_WIDE_TABLE": False, "FASTPATH_ACCENT_FIRST": False, "FASTPATH_ATTR_GUARD": False, "FASTPATH_CLEAN_SHOW": False}
_orig = settings.get
settings.get = lambda k: FLAGS[k] if k in FLAGS else _orig(k)
AIRPORT = REPO / "system4" / "eval" / "real_v3" / "data" / "giao_thong_san_bay.xlsx"


def airport_tables():
    recs, n = {}, 0
    for ws in openpyxl.load_workbook(AIRPORT, read_only=True).worksheets:
        it = ws.iter_rows(values_only=True)
        head = [str(h) for h in next(it)]
        ti = next(i for i, h in enumerate(head) if h.strip().lower() not in ("stt", "tt"))
        for k, r in enumerate(it):
            if r[ti] is not None:
                n += 1
                f = {h: str(v) for i, (h, v) in enumerate(zip(head, r)) if i != ti and v is not None}
                recs[n] = {"id": n, "title": str(r[ti]), "fields": json.dumps(f, ensure_ascii=False), "text": f"{head[ti]}: {r[ti]}",
                           "source": f"x.xlsx · {ws.title} · dòng {k + 2}"}
    db.run = lambda sql, params=(), many=False: list(recs.values()) if "WHERE dataset_id" in sql else [recs[i] for i in params if i in recs]
    db.get_dataset = lambda i: {"id": 1, "name": "d", "filename": "x.xlsx"}
    spec = C.compile_dataset({"id": 1, "name": "d", "filename": "x.xlsx"}, use_llm=False)
    return _materialize(spec)[0]


def test_s41_wide():
    FLAGS["FASTPATH_WIDE_TABLE"] = False
    old = airport_tables()
    assert not any(t.get("wide") for t in old)
    FLAGS["FASTPATH_WIDE_TABLE"] = True
    tables = airport_tables()
    parent = next(t for t in tables if t["parent"] is None)
    child = next(t for t in tables if t["parent"] is not None)
    assert child["parent"]["via"] == "__title__", "sheet phụ phải nối theo TÊN dòng, không theo số thứ tự STT"
    assert "Năng lực khai thác" in parent["fields"] and "Sản lượng thông qua (2023)" in parent["fields"]
    row = next(r for r in parent["rows"] if r["title"].startswith("Côn Đảo"))
    assert row["fields"]["Vị trí"].startswith("Côn Đảo"), "Côn Đảo phải nhận cột của sheet phụ đúng dòng (không lệch theo STT)"
    assert sum(1 for r in parent["rows"] if r["fields"].get("Vị trí")) >= 20
    qs = selftest._q_sql(parent)
    assert any("Năng lực khai thác" in c["q"] for c in qs), "bài tự kiểm phải sinh câu chéo sheet"
    assert any(" và " in c["q"] and "Năng lực khai thác" in c["q"] for c in qs)


def test_s42_accent_first():
    names = ["Sông Lô", "Sông Lò", "Sông Đà", "Sông Hồng"]
    rows = [{"id": i, "title": n, "fields": {"Chiều dài": str(100 * (i + 1))}} for i, n in enumerate(names)]
    t = {"key": "k", "name": "Sông", "title_label": "Tên", "rows": rows, "entity_noun": "sông", "parent": None, "children": [],
         "fields": {"Chiều dài": {"type": "number", "label": "Chiều dài", "long": False}}}
    sel = lambda sql: sorted(r[0] for r in sqlroute.Box(t).run(sql)[1])
    FLAGS["FASTPATH_ACCENT_FIRST"] = False
    assert sel("SELECT ten FROM bang WHERE ten LIKE '%Sông Lô%'") == ["Sông Lò", "Sông Lô"]       # lỗi cũ
    FLAGS["FASTPATH_ACCENT_FIRST"] = True
    assert sel("SELECT ten FROM bang WHERE ten LIKE '%Sông Lô%'") == ["Sông Lô"]
    assert sel("SELECT ten FROM bang WHERE ten = 'Sông Lò'") == ["Sông Lò"]
    assert sel("SELECT ten FROM bang WHERE ten LIKE '%song lo%'") == ["Sông Lò", "Sông Lô"]       # không dấu: vẫn bỏ dấu


def test_s44_show():
    FLAGS["FASTPATH_CLEAN_SHOW"] = False
    assert engine.show("8053", "number", "Diện tích (ha)") == "8.053"
    FLAGS["FASTPATH_CLEAN_SHOW"] = True
    assert engine.show("8053", "number", "Diện tích (ha)") == "8053"
    assert engine.show("1904", "number", "Năm xây dựng") == "1904"
    assert engine.show("1404587", "number", "Dân số") == "1.404.587"
    assert engine.show("0912345678", "id", "SĐT") == "0912345678"


def test_s43_absent_attribute():
    FLAGS["FASTPATH_WIDE_TABLE"] = True
    eng = engine.Engine(airport_tables(), [], {})
    for q in ("Sân bay Pleiku có bao nhiêu nhân viên?", "Sân bay Đồng Hới có bao nhiêu nhân viên?"):   # dòng có trong bảng / không có trong bảng
        FLAGS["FASTPATH_ATTR_GUARD"] = False
        assert eng.answer(q, {}).get("route") != "absent", q
        FLAGS["FASTPATH_ATTR_GUARD"] = True
        a = eng.answer(q, {})
        assert a["kind"] == "answer" and a["route"] == "absent" and "nhân viên" in a["content"] and "khong co thong tin" in __import__("unicodedata").normalize("NFD", a["content"].lower()).encode("ascii", "ignore").decode(), q
    for ok in ("Có bao nhiêu sân bay ở Đắk Lắk?", "Có bao nhiêu sân bay cấp 4C?"):      # câu đếm đúng không bị chặn
        assert eng.answer(ok, {}).get("route") != "absent", ok


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

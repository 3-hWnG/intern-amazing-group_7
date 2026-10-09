"""NV5: câu chào khi bật dữ liệu, kiểm chi tiết bịa, trùng tên, công cụ bảng, thứ tự lời dặn, chế độ Nhanh dạng chữ, bộ đọc tệp.
Model giả (embedding, reranker, LLM) — kiểm đường đi của code, không đo chất lượng (chất lượng: system4/eval/bench.py).
Chạy (từ thư mục server/): set PYTHONPATH=<pyroot> && python ../system4/tests/test_nv5.py"""
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import time
from pathlib import Path

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RUNTIME_DIR=os.path.join(TMP, "s4"))

from fastapi.testclient import TestClient
import main
from system3.system4.server import ambig, auth, greet, ground, ingest, llm, persona, search, settings, tabletool
import nv5_off
nv5_off.apply()   # test này kiểm hành vi trước NV5 (NV5 bật từng tính năng ở test_nv5.py)

EVAL = Path(SERVER).parent / "system4" / "eval"


def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * 1024
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 1024] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


def fake_rerank(query, texts):
    q = set(re.findall(r"\w+", query.lower()))
    return [len(q & set(re.findall(r"\w+", t.lower()))) * 3 - 4.0 for t in texts]


prompts, answers, text_answers, json_calls = [], [], [], []


async def fake_fast(messages, schema):
    prompts.append(messages)
    d = answers.pop(0) if answers else {"plan": "", "answer": "Theo dữ liệu [1].", "ask_back": False, "choices": [], "sources": [1]}
    d = {persona.key(k) if k in persona.KEY_PREFIX else k: v for k, v in d.items()}   # JSON_PLAN_FIRST: a_plan, c_answer…
    d = {k: v for k, v in d.items() if k in schema["properties"]}
    raw = json.dumps(d, ensure_ascii=False)
    for i in range(0, len(raw), 7):
        yield raw[i:i + 7]
    yield llm.Stats(load_s=0, prompt_tokens=100, prompt_s=0.1, output_tokens=20, output_s=0.2, total_s=0.3)


async def fake_text(messages):
    prompts.append(messages)
    raw = text_answers.pop(0) if text_answers else "KẾ HOẠCH: trả lời\n===\nCâu trả lời dạng chữ [1]."
    for i in range(0, len(raw), 5):
        yield raw[i:i + 5]


def fake_chat_json(messages, schema, timeout=60):
    json_calls.append(messages)
    if "use_table" in schema["properties"]:
        return {"use_table": True, "table": 0, "op": "count", "field": "", "filters": [{"field": "Nữ", "op": "not_empty", "value": ""}]}
    return {}


search.embed = fake_embed
search.rerank = fake_rerank
llm.stream_json = fake_fast
llm.stream_text = fake_text
llm.chat_json = fake_chat_json
tabletool.llm.chat_json = fake_chat_json


def setv(**kw):
    settings.save(kw)


# ------------------------------------------------------------------ câu chào: quy tắc code
for t in ("Chào bạn", "chao ban nhe", "Hello", "Cảm ơn bạn nhiều", "thanks", "Tạm biệt nhé", "Ok cảm ơn bạn", "cam on nha", "bye bye"):
    assert greet.is_greeting(t, []), t
for t in ("Hi, mình muốn hỏi đổi trả sản phẩm trong bao nhiêu ngày", "Hạng Vàng?", "Đà Lạt?", "Chào bạn, cho mình hỏi mẹ của bé An tên gì?",
          "Bạn khỏe không?"):
    assert not greet.is_greeting(t, []), t
assert not greet.is_greeting("ok", [{"role": "assistant", "meta": {"choices": ["a", "b"]}}]), "ok sau khi AI hỏi lại = trả lời câu hỏi"
assert greet.looks_like_question("Hạng Vàng được ưu đãi gì?") and not greet.looks_like_question("Cảm ơn nhé")

# ------------------------------------------------------------------ kiểm chi tiết bịa
src = "Bộ phận hỗ trợ làm việc từ 8 giờ đến 17 giờ 30. Hạng Vàng giảm 10%. SĐT 0912345678. Mẹ: Trần Thị Mỹ Hạnh. Ngày sinh 14/3/2020"
assert ground.ungrounded("Làm việc từ 8 giờ đến 17 giờ 30 [1], hạng Vàng giảm 10% [2].", src, kb=True) == []
assert ground.ungrounded("Bạn gọi 0912 345 678 nhé.", src, kb=True) == []
assert ground.ungrounded("Mẹ của bé là Trần Thị Mỹ Hạnh, sinh ngày 14 tháng 3 năm 2020.", src, kb=True) == []
bad = ground.ungrounded("Hotline 1900 8888 99, giảm 25% cho hạng Vàng, liên hệ chị Nguyễn Thị Lan.", src, kb=True)
assert "1900 8888 99" in bad and "25" in bad and any("Nguyễn Thị Lan" in b for b in bad), bad
assert ground.ungrounded("Có 2 bạn tên An và 3 bước cần làm.", src, kb=True) == [], "số đếm nhỏ không bị bắt"
# báo nhầm thấy khi đo vòng C: tên vắt qua dòng / qua dấu câu, "8:00" = "8 giờ", chữ IN HOA
assert ground.ungrounded("Mẹ của bé là Trần Thị Mỹ Hạnh.\nNguồn: [1]", src, kb=True) == []
assert ground.ungrounded("Làm việc từ 8:00 đến 17 giờ 30. Chủ nhật nghỉ.", src + " Thứ Bảy", kb=True) == []
assert ground.ungrounded("THỦ TỤC Hành chính", src, kb=True) == []
assert ground.ungrounded("| Tên | Địa chỉ |\n|---|---|\n| Trần Thị Mỹ Hạnh | Hà Nội |", src + " Hà Nội Tên Địa chỉ", kb=True) == [], "ô bảng"
assert ground.ungrounded("Danh sách: Mạc T. và các bạn khác", src + " Mạc Tuyết Mai", kb=True) == [], "viết tắt một chữ cái"
# câu hỏi tiếp (SEARCH_FOLLOWUP): "Còn ... thì sao?" 6 chữ vẫn ghép câu hỏi trước
from system3.system4.server import chat as chat_mod
assert chat_mod._followup("Còn số điện thoại thì sao?") and not chat_mod._followup("Hạng Kim cương được những ưu đãi nào?")
g = ground.ungrounded("Bạn có thể gọi hotline 1900 8888 của Team 7 hoặc email hotro@team7.vn, xem python.org.", "Team 7", kb=False, business="Team 7")
assert "1900 8888" in g and "hotro@team7.vn" in g and not any("python" in x for x in g), g

# ------------------------------------------------------------------ chế độ Nhanh dạng chữ: tách kế hoạch
assert persona.parse_text("KẾ HOẠCH: [XÃ GIAO] chào lại\n===\nChào bạn!") == ("chào lại", "Chào bạn!", True)
assert persona.parse_text("KẾ HOẠCH: trả lời\nCâu trả lời") == ("trả lời", "Câu trả lời", False)
assert persona.parse_text("Chỉ có câu trả lời") == ("", "Chỉ có câu trả lời", False)

# ------------------------------------------------------------------ JSON_PLAN_FIRST: tên trường a_plan, c_answer…
assert persona.plain_keys({"a_plan": "x", "c_answer": "y", "d_ask_back": False, "ask_back": True}) == {"plan": "x", "answer": "y", "ask_back": True}
from system3.system4.server import chat as _chat
_a = _chat.AnswerStream()
assert _a.feed('{"a_plan": "kế hoạch", "c_answer": "Chào') + _a.feed(' bạn", "d_ask_back": false}') == "Chào bạn"
assert _a.final() == {"plan": "kế hoạch", "answer": "Chào bạn", "ask_back": False}

# ------------------------------------------------------------------ bộ đọc tệp (A5)
two = [["STT", "Họ tên", "Điểm", "", ""], ["", "", "Toán", "Văn", "Anh"], ["1", "Nguyễn Văn A", "8", "7", "9"], ["2", "Lê Thị B", "6", "9", "7"]]
h, d, how = ingest._clean_table(two, merged=[(1, 2, 1, 4)])
assert h[2:] == ["Điểm - Toán", "Điểm - Văn", "Điểm - Anh"] and how.get("two_row_header") and len(d) == 2, (h, how)
h, d, how = ingest._clean_table(two)   # CSV (không biết ô gộp): nhóm phủ 3 cột -> vẫn ghép
assert h[2] == "Điểm - Toán", h
fam = [["STT", "", "Tên", "Địa chỉ"], ["1", "Nguyễn Văn", "An", "Hà Nội"], ["2", "Lê Thị", "Bình", "Huế"]]
h, d, how = ingest._clean_table(fam)
assert not how.get("two_row_header") and len(d) == 2, "cặp Họ | (trống) không bị nhầm thành tiêu đề hai tầng"
side = [["Thông số", "Điện thoại A", "Điện thoại B", "Điện thoại C"], ["Giá", "5.000.000", "7.500.000", "9.900.000"],
        ["Màu", "Đen", "Trắng", "Xanh"], ["Pin", "4000", "4500", "5000"]]
recs, m = ingest.table_records("Bảng", side, "dt.xlsx", use_ai=False)
assert m.get("sideways") and [r["title"] for r in recs] == ["Điện thoại A", "Điện thoại B", "Điện thoại C"], (m, recs)
assert recs[1]["fields"]["Giá"] == "7.500.000" and recs[1]["fields"]["Màu"] == "Trắng"
products = [["Tên", "Giá", "Màu"], ["Áo", "100", "Đỏ"], ["Quần", "200", "Xanh"], ["Mũ", "50", "Đen"]]
assert not ingest.table_records("SP", products, "sp.csv", use_ai=False)[1].get("sideways"), "bảng thường không bị xoay"
multi = [["DANH MỤC"], [], ["Tên", "Giá"], ["Áo", "100"], ["Quần", "200"], [], [], ["Họ tên", "Chức vụ"], ["An", "Giám đốc"], ["Bình", "Kế toán"]]
blocks = ingest._blocks(multi)
assert len(blocks) == 2 and blocks[0][1][0] == ["DANH MỤC"] and blocks[1][0] == 7, blocks
gap = [["Tên", "Giá"], ["Áo", "100"], ["Quần", "200"], [], ["Mũ", "50"], ["Giày", "300"]]
assert len(ingest._blocks(gap)) == 1, "dòng trống giữa dữ liệu không tách bảng"
h, d, how = ingest._clean_table([["Ghi chú"], ["Tên", "Giá"], ["Áo", "100"]], header_row=2)
assert h == ["Tên", "Giá"] and how["header_row"] == 2 and how.get("header_chosen")

# ------------------------------------------------------------------ qua web: danh sách lớp giả
with TestClient(main.app) as c:
    c.post("/s4/auth/signup", json={"username": "dev1", "password": "123456"})

    def chat(text, cid=None):
        r = c.post("/s4/chat", json={"text": text, "conversation_id": cid})
        assert r.status_code == 200, r.text
        return [json.loads(l[6:]) for l in r.text.split("\n\n") if l.startswith("data: ")]

    def last(ev):
        cid = ev[0]["conversation_id"]
        return c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]

    sys.path.insert(0, str(EVAL))
    import fake_class
    path = fake_class.build(Path(TMP) / fake_class.OUT.name)   # không ghi đè tệp trong repo
    with open(path, "rb") as f:
        ds = c.post("/s4/datasets", files={"file": (path.name, f)}).json()["dataset"]
    t0 = time.time()
    while c.get("/s4/datasets").json()["datasets"][0]["status"] != "ready":
        assert time.time() - t0 < 60
        time.sleep(0.2)
    ds_id = ds["id"]

    # mặc định (mọi cài đặt NV5 tắt): câu chào vẫn đi đường tra dữ liệu như trước
    ev = chat("Chào bạn")
    assert ev[0]["specialist"] is True
    sp = prompts[-1][0]["content"]
    assert "small_talk" not in json.dumps(prompts[-1]) and "Dữ liệu tham khảo" in sp

    # code_first: câu chào ngắn -> không tìm, không "chỉ dùng dữ liệu"
    setv(GREETING_MODE="code_first")
    ev = chat("Chào bạn")
    m = last(ev)
    assert ev[0]["specialist"] is False and m["meta"].get("small_talk") == "code" and not m["meta"].get("sources"), m["meta"]
    assert "CHẾ ĐỘ CHUYÊN GIA" not in prompts[-1][0]["content"] and "câu xã giao" in prompts[-1][0]["content"]
    # code_first, câu dài có chào: tra dữ liệu, AI được đánh dấu xã giao (AI can thiệp)
    answers.append({"plan": "", "small_talk": False, "answer": "Mẹ bạn ấy là Trần Thị Mỹ Hạnh [1].", "ask_back": False, "choices": [], "sources": [1]})
    ev = chat("Chào bạn, cho mình hỏi mẹ của Trần Thị Bảo An tên gì?")
    assert ev[0]["specialist"] is True and '"small_talk"' in prompts[-1][0]["content"]
    # ai_first: AI nói xã giao nhưng tin nhắn là câu hỏi -> code bác bỏ
    setv(GREETING_MODE="ai_first")
    answers.append({"plan": "", "small_talk": True, "answer": "Dạ vâng!", "ask_back": False, "choices": [], "sources": []})
    m = last(chat("Lớp này học phòng số mấy vậy?"))
    assert m["meta"].get("small_talk_override") == "rejected" and not m["meta"].get("small_talk"), m["meta"]
    # ai_first: câu chào ngắn mà AI trả lời "không có trong dữ liệu" -> viết lại kiểu xã giao
    answers += [{"plan": "", "small_talk": False, "answer": "Thông tin này không có trong dữ liệu.", "ask_back": False, "choices": [], "sources": []},
                {"plan": "", "answer": "Chào bạn, mình có thể giúp gì?", "ask_back": False, "choices": []}]
    ev = chat("Chào bạn")
    m = last(ev)
    assert any(e["type"] == "restart" for e in ev) and m["meta"]["small_talk"] == "forced" and m["content"].startswith("Chào bạn"), m
    # ai_only: tin AI
    setv(GREETING_MODE="ai_only")
    answers.append({"plan": "", "small_talk": True, "answer": "Cảm ơn bạn nhé!", "ask_back": False, "choices": [], "sources": []})
    m = last(chat("Bạn dễ thương quá"))
    assert m["meta"]["small_talk"] == "ai" and not m["meta"].get("sources") and not m["meta"].get("consulted"), m["meta"]
    setv(GREETING_MODE="off")

    # trùng tên: hỏi lại bằng code, không gọi AI
    setv(AMBIGUITY_CHECK=True)
    n = len(prompts)
    m = last(chat("Mẹ của bé An tên gì?"))
    assert len(prompts) == n, "không gọi AI"
    assert m["meta"]["choices"] and {"Trần Thị Bảo An", "Lê Bình An"} <= set(m["meta"]["choices"]), m["meta"]
    assert "Phạm An Khang" in m["meta"]["choices"] and "Bạn muốn hỏi về mục nào" in m["content"]
    b = ambig.check("Bé Bảo sinh ngày nào?", [ds_id], set(range(1, 100)))   # "Bảo" không dấu = "bao" (của "bao nhiêu")
    assert b and "Hồ Gia Bảo" in b["options"], b
    assert ambig.check("Lớp có bao nhiêu bạn nữ?", [ds_id], set(range(1, 100))) is None, "'bao nhiêu' không phải tên"
    info = ambig.check("Mẹ của Trần Thị Bảo An tên gì?", [ds_id], set(range(1, 100)))
    assert info is None, "gọi đủ họ tên -> không mơ hồ"
    setv(AMBIGUITY_CHECK=False)

    # công cụ bảng: đếm trên cả bảng
    setv(TABLE_TOOL=True)
    answers.append({"plan": "", "answer": "Lớp có 16 bạn nữ [1].", "ask_back": False, "choices": [], "sources": [1]})
    m = last(chat("Lớp có bao nhiêu bạn nữ?"))
    sp = prompts[-1][0]["content"]
    assert "Số dòng thỏa điều kiện: 16." in sp and "TOÀN BỘ 33 dòng" in sp, sp[-800:]
    assert m["meta"]["sources"][0]["record_id"] is None and m["meta"]["sources"][0]["title"].startswith("Tính trên cả bảng")
    res = tabletool.execute({"op": "list", "filters": [{"field": "Địa chỉ", "op": "contains", "value": "Phú Thạnh"}]},
                            tabletool.tables([ds_id])[0])
    assert res["matched"] == 10, res["matched"]
    res = tabletool.execute({"op": "count", "filters": [{"field": "Ngày sinh", "op": "year", "value": "2019"}]}, tabletool.tables([ds_id])[0])
    assert res["matched"] == 5
    n = len(json_calls)
    chat("Ngày sinh của bạn Tô Đức Hiếu?")
    assert len(json_calls) == n, "câu hỏi thường không gọi công cụ bảng"
    setv(TABLE_TOOL=False)

    # kiểm chi tiết bịa: viết lại một lần
    setv(GROUNDING_CHECK="rewrite")
    answers += [{"plan": "", "answer": "Bạn gọi hotline 1900 8888 99 [1].", "ask_back": False, "choices": [], "sources": [1]},
                {"plan": "", "answer": "Dữ liệu không có số hotline.", "ask_back": False, "choices": [], "sources": []}]
    ev = chat("Số điện thoại tổng đài là gì?")
    m = last(ev)
    assert any(e["type"] == "restart" for e in ev) and m["meta"]["grounding"]["items"] == ["1900 8888 99"], m["meta"]
    assert "1900 8888 99" in prompts[-1][-1]["content"] or "1900 8888 99" in prompts[-1][0]["content"]
    setv(GROUNDING_CHECK="off")

    # thứ tự lời dặn để dùng lại phần đã đọc: dữ liệu đi cùng tin nhắn cuối
    setv(PROMPT_CACHE_ORDER=True)
    chat("Ngày sinh của bạn Tô Đức Hiếu?")
    sysm, lastm = prompts[-1][0]["content"], prompts[-1][-1]["content"]
    assert "Dữ liệu tham khảo:" not in sysm and "CHẾ ĐỘ CHUYÊN GIA" in sysm and lastm.startswith("Ngày sinh của bạn Tô Đức Hiếu?")
    assert "Dữ liệu tham khảo:" in lastm and "Thông tin cho trợ lý" in lastm
    setv(PROMPT_CACHE_ORDER=False)

    # chế độ Nhanh dạng chữ: kế hoạch ẩn, chữ sau "===" hiện ra, lựa chọn theo mẫu [[CHOICES]]
    setv(FAST_FORMAT="text")
    text_answers.append("KẾ HOẠCH: hỏi lại\n===\nBạn muốn hỏi bạn nào?\n[[CHOICES]]\n- Trần Thị Bảo An\n- Lê Bình An")
    ev = chat("Ngày sinh của An?")
    shown = "".join(e["text"] for e in ev if e["type"] == "delta")
    m = last(ev)
    assert "KẾ HOẠCH" not in shown and shown.startswith("Bạn muốn hỏi"), shown
    assert m["meta"]["choices"] == ["Trần Thị Bảo An", "Lê Bình An"] and m["content"] == "Bạn muốn hỏi bạn nào?", m
    assert "===" in prompts[-1][0]["content"]
    setv(FAST_FORMAT="json")

    # chọn lại dòng tiêu đề trong "Cách đọc" -> lưu và xử lý lại
    r = c.post(f"/s4/datasets/{ds_id}/header", json={"part": "Sheet1", "row": 3})
    assert r.status_code == 200
    t0 = time.time()
    while c.get("/s4/datasets").json()["datasets"][0]["status"] != "ready":
        assert time.time() - t0 < 60
        time.sleep(0.2)
    d = c.get("/s4/datasets").json()["datasets"][0]
    assert d["mapping"]["overrides"] == {"Sheet1": 3} and d["mapping"]["parts"][0].get("header_chosen") and d["n_records"] == 33, d["mapping"]

    # mặc định từ NV5 (cấu hình thắng bộ đo): mọi tính năng bật cùng lúc
    settings.reset(list(nv5_off.OFF))
    assert settings.get("JSON_PLAN_FIRST") and settings.get("GREETING_MODE") == "code_first"
    answers.append({"plan": "tra ngày sinh", "answer": "Bạn Tô Đức Hiếu sinh ngày 3/1/2020 [1].", "ask_back": False, "choices": [], "sources": [1]})
    m = last(chat("Ngày sinh của bạn Tô Đức Hiếu?"))
    assert "3/1/2020" in m["content"] and m["meta"]["sources"] and not m["meta"].get("grounding"), m
    assert '"a_plan"' in prompts[-1][0]["content"] and "Dữ liệu tham khảo:" in prompts[-1][-1]["content"]
    m = last(chat("Chào bạn"))
    assert m["meta"].get("small_talk") == "code"
    m = last(chat("Mẹ của bé An tên gì?"))
    assert "Lê Bình An" in m["meta"]["choices"], m["meta"]

print("OK test_nv5")

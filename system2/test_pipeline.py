"""Test cục bộ pipeline.py (run_turn_system2) — module MỚI hôm nay, quan
trọng nhất vì ráp toàn bộ luồng Turn 1 / Turn 2+ / not_in_sources.

Mock `extractor.resolve` và `customer_care.answer_procedure_query` (không có
Ollama thật trong sandbox) nhưng DÙNG DB THẬT CỦA APP (SQLite tạm, có schema
thật — bảng messages/conversations/users) để `Messages.latest_by_kind()` chạy
thật, không mock repository. `primary` trong kết quả mock lấy từ
service.resolve_query() thật (DB 70 thủ tục) để service.render_card() nhận
đúng cấu trúc dữ liệu thật, không phải fixture tay."""
import copy
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
APP_DIR = HERE.parent / "app"

# DB app (messages/conversations/users) TẠM, cô lập với DB thật của dev —
# PHẢI set biến môi trường trước khi import config/db.connection (DB_PATH
# đọc 1 lần lúc import module).
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_PATH"] = _tmp_db.name

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(APP_DIR))

from db import connection  # noqa: E402
from db.repositories import Conversations, Messages, Users  # noqa: E402

import pipeline  # noqa: E402
import service as s2  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    status = "OK" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


connection.init_db()
user = Users.create("test@example.com", "hash", "Test")
conv = Conversations.create(user["id"])
CONV_ID = conv["id"]

s2_conn = s2.connect(str(HERE / "db" / "procedures.db"))
marriage = s2.resolve_query(s2_conn, "đăng ký kết hôn")
birth = s2.resolve_query(s2_conn, "đăng ký khai sinh")
s2_conn.close()
check("(chuẩn bị) DB thật resolve được thủ tục kết hôn", marriage["found"] and marriage["confident"])
check("(chuẩn bị) DB thật resolve được thủ tục khai sinh", birth["found"] and birth["confident"])
MARRIAGE_CODE = marriage["primary"]["procedure"]["proc_code"]
BIRTH_CODE = birth["primary"]["procedure"]["proc_code"]
check("(chuẩn bị) 2 thủ tục demo có proc_code khác nhau", MARRIAGE_CODE != BIRTH_CODE)


def _resolved(primary, found=True, confident=True, message=None, facet="tong_quan",
               intent_type="procedure"):
    return {"found": found, "confident": confident, "primary": primary, "suggestion": None,
            "extracted": {"intent_type": intent_type, "primary_keyword": "x",
                          "province": None, "facet": facet},
            "message": message, "debug": {}}


# --- A. Turn 1 (chưa có Thẻ nào đang mở) -> mở Thẻ mới ---
with patch.object(pipeline.extractor, "resolve", return_value=_resolved(marriage["primary"])):
    res_a = pipeline.run_turn_system2(CONV_ID, "đăng ký kết hôn cần gì", [])
check("A. Turn 1: kind=procedure_card", res_a.kind == "procedure_card", res_a.kind)
check("A. Turn 1: intent.proc_code đúng thủ tục vừa tìm", res_a.intent.get("proc_code") == MARRIAGE_CODE)
check("A. Turn 1: text là HTML Thẻ (không phải câu trả lời chữ)",
      "procedure-card" in res_a.text and "<div" in res_a.text, res_a.text[:80])

# Lưu message Thẻ vừa "mở" vào DB thật -> mô phỏng trạng thái hội thoại đã có Thẻ.
Messages.add(CONV_ID, "assistant", res_a.text, kind=res_a.kind, intent=res_a.intent)

# --- B. Turn 2+ cùng proc_code -> LLM 2 Customer Care, không mở lại Thẻ ---
with patch.object(pipeline.extractor, "resolve", return_value=_resolved(marriage["primary"], facet="le_phi")), \
     patch.object(pipeline.customer_care, "answer_procedure_query",
                  return_value="Lệ phí đăng ký kết hôn là miễn phí.") as mock_cc:
    res_b = pipeline.run_turn_system2(CONV_ID, "lệ phí bao nhiêu", [])
check("B. Turn 2+ cùng thủ tục: kind=answer (không mở lại Thẻ)", res_b.kind == "answer", res_b.kind)
check("B. Turn 2+: gọi đúng customer_care.answer_procedure_query 1 lần", mock_cc.call_count == 1)
check("B. Turn 2+: text là câu trả lời của LLM 2 (không phải HTML)",
      res_b.text == "Lệ phí đăng ký kết hôn là miễn phí.", res_b.text)
check("B. Turn 2+: intent giữ nguyên proc_code", res_b.intent.get("proc_code") == MARRIAGE_CODE)
check("B. Turn 2+: facet truyền đúng xuống customer_care",
      mock_cc.call_args[0][2] == "le_phi", mock_cc.call_args)

# --- C. Chuyển sang thủ tục khác (khác proc_code) -> mở Thẻ MỚI, không gọi customer_care ---
with patch.object(pipeline.extractor, "resolve", return_value=_resolved(birth["primary"])), \
     patch.object(pipeline.customer_care, "answer_procedure_query") as mock_cc2:
    res_c = pipeline.run_turn_system2(CONV_ID, "giờ tôi hỏi về khai sinh", [])
check("C. Đổi thủ tục: kind=procedure_card (Thẻ mới)", res_c.kind == "procedure_card", res_c.kind)
check("C. Đổi thủ tục: proc_code là thủ tục MỚI, không phải thủ tục cũ",
      res_c.intent.get("proc_code") == BIRTH_CODE and res_c.intent.get("proc_code") != MARRIAGE_CODE)
check("C. Đổi thủ tục: KHÔNG gọi customer_care (đã đổi proc_code)", mock_cc2.call_count == 0)

# --- D. found=False -> not_in_sources + choices = TỪ KHÓA THẬT (Fix 24/09/2026:
#        trước đây choices là nhãn CTA tĩnh "Tra cứu Web trực tiếp với System 1"
#        -> chat.js gửi ĐÚNG chuỗi đó làm truy vấn thật khi bấm, tra nhầm cái
#        nhãn nút thay vì câu hỏi người dùng. _resolved() mock primary_keyword="x") ---
with patch.object(pipeline.extractor, "resolve",
                  return_value=_resolved(None, found=False, confident=False,
                                          message="Xin lỗi, tôi không tìm thấy 'x' cho câu hỏi 'y'.")):
    res_d = pipeline.run_turn_system2(CONV_ID, "xin visa du học mặt trăng", [])
check("D. found=False: kind=not_in_sources", res_d.kind == "not_in_sources", res_d.kind)
check("D. found=False: text = message chuẩn từ extractor", res_d.text.startswith("Xin lỗi, tôi không tìm thấy"))
check("D. found=False: choices = từ khóa thật đã trích (KHÔNG còn là nhãn CTA tĩnh)",
      res_d.choices == ["x"], res_d.choices)

# --- D2. found=False, extractor trả primary_keyword rỗng -> choices fallback
#         về ĐÚNG câu hỏi gốc của người dùng, không bao giờ rơi về nhãn CTA ---
resolved_empty_kw = _resolved(None, found=False, confident=False,
                               message="Xin lỗi, tôi không tìm thấy '' cho câu hỏi 'y'.")
resolved_empty_kw["extracted"]["primary_keyword"] = ""
with patch.object(pipeline.extractor, "resolve", return_value=resolved_empty_kw):
    res_d2 = pipeline.run_turn_system2(CONV_ID, "câu hỏi gốc của người dùng", [])
check("D2. found=False, primary_keyword rỗng: choices fallback về câu hỏi gốc",
      res_d2.choices == ["câu hỏi gốc của người dùng"], res_d2.choices)
check("D2. found=False: choices KHÔNG BAO GIỜ còn là nhãn CTA tĩnh cũ",
      res_d2.choices != ["Tra cứu Web trực tiếp với System 1"], res_d2.choices)

# --- E. found=True nhưng confident=False -> vẫn not_in_sources (không hiện thẻ nhầm),
#        choices vẫn là từ khóa thật ---
with patch.object(pipeline.extractor, "resolve",
                  return_value=_resolved(marriage["primary"], found=True, confident=False,
                                          message="Xin lỗi, tôi không tìm thấy 'x' cho câu hỏi 'y'.")):
    res_e = pipeline.run_turn_system2(CONV_ID, "câu mơ hồ", [])
check("E. found=True nhưng confident=False: vẫn kind=not_in_sources (không hiện thẻ có thể sai)",
      res_e.kind == "not_in_sources", res_e.kind)
check("E. found=True nhưng confident=False: choices = từ khóa thật",
      res_e.choices == ["x"], res_e.choices)

# --- F. Lịch sử có message kind=procedure_card (HTML) -> LLM1 nhận bản đã lọc,
#        không phải HTML thô ---
history_with_card = [
    {"role": "user", "content": "đăng ký kết hôn cần gì", "kind": ""},
    {"role": "assistant", "content": res_a.text, "kind": "procedure_card"},
]
with patch.object(pipeline.extractor, "resolve", return_value=_resolved(marriage["primary"])) as mock_ex, \
     patch.object(pipeline.customer_care, "answer_procedure_query", return_value="..."):
    pipeline.run_turn_system2(CONV_ID, "lệ phí bao nhiêu", copy.deepcopy(history_with_card))
sent_history = mock_ex.call_args.kwargs.get("history") if mock_ex.call_args.kwargs else mock_ex.call_args[0][1]
check("F. Lịch sử gửi LLM1 đã lọc HTML thô của Thẻ",
      all("procedure-card" not in (h.get("content") or "") for h in sent_history), sent_history)
check("F. Lịch sử gửi LLM1 vẫn có dấu vết tên thủ tục (để bắt follow-up)",
      any("kết hôn" in (h.get("content") or "").lower() for h in sent_history), sent_history)

# --- G. (Fix 1, Ngày Thứ 5) intent_type=chitchat -> kind=chitchat, KHÔNG
#        gọi customer_care, KHÔNG mở Thẻ, KHÔNG gán choices ---
with patch.object(pipeline.extractor, "resolve",
                  return_value=_resolved(None, found=False, confident=False,
                                          intent_type="chitchat")), \
     patch.object(pipeline.customer_care, "answer_procedure_query") as mock_cc_g:
    res_g = pipeline.run_turn_system2(CONV_ID, "chào bạn", [])
check("G. chitchat: kind=chitchat", res_g.kind == "chitchat", res_g.kind)
check("G. chitchat: text là lời chào (không phải HTML Thẻ)",
      "procedure-card" not in res_g.text and len(res_g.text) > 0, res_g.text)
check("G. chitchat: KHÔNG gán choices", not res_g.choices, res_g.choices)
check("G. chitchat: KHÔNG gọi customer_care", mock_cc_g.call_count == 0)

# --- H. intent_type=out_of_scope -> kind=out_of_scope, KHÔNG gán choices
#        (đồng nhất với app/core/orchestrator.py, tránh chat.js hiểu nhầm
#        useWebSearchSwitch chỉ đúng cho kind="not_in_sources") ---
with patch.object(pipeline.extractor, "resolve",
                  return_value=_resolved(None, found=False, confident=False,
                                          intent_type="out_of_scope")), \
     patch.object(pipeline.customer_care, "answer_procedure_query") as mock_cc_h:
    res_h = pipeline.run_turn_system2(CONV_ID, "nấu phở bò thế nào", [])
check("H. out_of_scope: kind=out_of_scope", res_h.kind == "out_of_scope", res_h.kind)
check("H. out_of_scope: KHÔNG gán choices", not res_h.choices, res_h.choices)
check("H. out_of_scope: KHÔNG gọi customer_care", mock_cc_h.call_count == 0)

# --- I. (Fix 2, Ngày Thứ 5) Lịch sử có lượt trả lời DÀI của Customer Care
#        (kind="answer", câu mở đầu sạch + 18 dòng checklist bullet phía dưới,
#        đúng dạng LLM 2 hay trả lời thật) -> LLM1 chỉ nhận CÂU MỞ ĐẦU sạch,
#        KHÔNG còn nguyên checklist/bảng dữ liệu thủ tục CŨ ---
long_answer = "\n".join([
    "Thủ tục cấp lại thẻ căn cước cần chuẩn bị hồ sơ như sau.",
    "- Hồ sơ gồm: đơn đề nghị, bản sao CCCD, giấy tờ chứng minh nơi cư trú",
    "- Lệ phí: miễn phí theo quy định hiện hành",
] + [f"- Chi tiết dòng {i}: mô tả rất dài về thủ tục cấp lại thẻ căn cước để nhồi context"
     for i in range(18)])
history_with_answer = [
    {"role": "user", "content": "cấp lại thẻ căn cước cần gì", "kind": ""},
    {"role": "assistant", "content": long_answer, "kind": "answer"},
]
with patch.object(pipeline.extractor, "resolve", return_value=_resolved(marriage["primary"])) as mock_ex_i, \
     patch.object(pipeline.customer_care, "answer_procedure_query", return_value="..."):
    pipeline.run_turn_system2(CONV_ID, "giờ tôi hỏi thủ tục khác", copy.deepcopy(history_with_answer))
sent_history_i = mock_ex_i.call_args.kwargs.get("history") if mock_ex_i.call_args.kwargs else mock_ex_i.call_args[0][1]
assistant_turn = next(h for h in sent_history_i if h.get("role") == "assistant")
check("I. Lượt trả lời dài (kind=answer) chỉ giữ câu mở đầu sạch",
      assistant_turn["content"] == "Thủ tục cấp lại thẻ căn cước cần chuẩn bị hồ sơ như sau.",
      assistant_turn["content"])
check("I. Lượt trả lời dài (kind=answer) đã bị rút gọn <=140 ký tự",
      len(assistant_turn["content"]) <= 140, assistant_turn["content"])
check("I. Lượt trả lời dài (kind=answer) KHÔNG còn bullet '- Hồ sơ gồm' thô",
      "- Hồ sơ gồm" not in assistant_turn["content"], assistant_turn["content"])
check("I. Lượt trả lời dài (kind=answer) KHÔNG còn 18 dòng chi tiết cũ trong context",
      "Chi tiết dòng" not in assistant_turn["content"], assistant_turn["content"])

# --- I2. Toàn bộ nội dung chỉ gồm bullet (không có câu mở đầu sạch nào) ->
#         fallback về câu mặc định trung tính, không rơi vào lỗi/rỗng ---
all_bullet_answer = "\n".join(f"- Chi tiết dòng {i}: checklist thô" for i in range(5))
history_all_bullet = [
    {"role": "user", "content": "cấp lại thẻ căn cước cần gì", "kind": ""},
    {"role": "assistant", "content": all_bullet_answer, "kind": "answer"},
]
with patch.object(pipeline.extractor, "resolve", return_value=_resolved(marriage["primary"])) as mock_ex_i2, \
     patch.object(pipeline.customer_care, "answer_procedure_query", return_value="..."):
    pipeline.run_turn_system2(CONV_ID, "giờ tôi hỏi thủ tục khác", copy.deepcopy(history_all_bullet))
sent_history_i2 = mock_ex_i2.call_args.kwargs.get("history") if mock_ex_i2.call_args.kwargs else mock_ex_i2.call_args[0][1]
assistant_turn2 = next(h for h in sent_history_i2 if h.get("role") == "assistant")
check("I2. Toàn bộ là bullet -> fallback câu mặc định trung tính",
      assistant_turn2["content"] == "Tôi đã cung cấp thông tin thủ tục theo tài liệu.",
      assistant_turn2["content"])

# --- J. Lịch sử có lượt kind=chitchat hoặc out_of_scope -> _history_for_extractor
#        phải LỌC BỎ HOÀN TOÀN, không để lọt cụm từ 'thủ tục hành chính' vào context ---
history_with_chitchat = [
    {"role": "user", "content": "chào bạn", "kind": ""},
    {"role": "assistant", "content": "Xin chào bạn! Tôi là Trợ lý Dịch vụ công, hỗ trợ tra cứu thủ tục hành chính.", "kind": "chitchat"},
    {"role": "user", "content": "vợ em mới sinh con, giờ làm thủ tục khai sinh thế nào", "kind": ""},
    {"role": "assistant", "content": res_a.text, "kind": "procedure_card"},
    {"role": "user", "content": "thời tiết hôm nay thế nào", "kind": ""},
    {"role": "assistant", "content": "Tôi chỉ hỗ trợ tra cứu thủ tục hành chính nhà nước...", "kind": "out_of_scope"},
]
with patch.object(pipeline.extractor, "resolve", return_value=_resolved(marriage["primary"])) as mock_ex_j, \
     patch.object(pipeline.customer_care, "answer_procedure_query", return_value="..."):
    pipeline.run_turn_system2(CONV_ID, "thế lệ phí bao nhiêu tiền", copy.deepcopy(history_with_chitchat))
sent_history_j = mock_ex_j.call_args.kwargs.get("history") if mock_ex_j.call_args.kwargs else mock_ex_j.call_args[0][1]
check("J. Lịch sử gửi LLM1 đã lọc bỏ hoàn toàn các lượt kind=chitchat",
      all(h.get("content") != "Xin chào bạn! Tôi là Trợ lý Dịch vụ công, hỗ trợ tra cứu thủ tục hành chính." for h in sent_history_j))
check("J. Lịch sử gửi LLM1 đã lọc bỏ hoàn toàn các lượt kind=out_of_scope",
      all("Tôi chỉ hỗ trợ tra cứu" not in h.get("content", "") for h in sent_history_j))

print()
if FAILED:
    print(f"=== {len(FAILED)} FAIL: {FAILED} ===")
    sys.exit(1)
print("=== TẤT CẢ TEST PASS ===")


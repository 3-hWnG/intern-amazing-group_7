"""Test cục bộ extractor.py — mock llm.chat_json (không có Ollama thật trong
sandbox) để kiểm tra logic nối ghép + fallback, DÙNG DB THẬT (70 thủ tục) để
resolve_query() chạy thật sự, không mock service.py."""
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import extractor as ex
import service as s2

FAILED = []


def check(name, cond, detail=""):
    status = "OK" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


# --- 1. Trích đúng, có sẵn tên thủ tục rõ ràng ---
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "procedure",
        "primary_keyword": "đăng ký khai sinh", "province": "", "facet": "ho_so"}):
    out = ex.extract("con em mới đẻ thì cần giấy gì để khai sinh")
check("extract() câu rõ ràng -> đúng field", out == {
    "intent_type": "procedure", "primary_keyword": "đăng ký khai sinh",
    "province": None, "facet": "ho_so"}, out)

# --- 2. Model trả rỗng / thiếu field -> fallback về câu hỏi gốc, không crash ---
with patch.object(ex.llm, "chat_json", return_value={}):
    out2 = ex.extract("một câu hỏi bất kỳ")
check("extract() model trả {} -> fallback intent_type=procedure, keyword=câu gốc, facet=tong_quan",
      out2 == {"intent_type": "procedure", "primary_keyword": "một câu hỏi bất kỳ",
               "province": None, "facet": "tong_quan"}, out2)

# --- 3. facet model trả sai enum -> vẫn fallback tong_quan, không lỗi ---
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "procedure",
        "primary_keyword": "x", "province": "Hà Nội", "facet": "khong_hop_le"}):
    out3 = ex.extract("x")
check("extract() facet ngoài enum -> fallback tong_quan", out3["facet"] == "tong_quan", out3)
check("extract() province giữ nguyên khi có", out3["province"] == "Hà Nội", out3)

# --- 3b. (Fix 1, Ngày Thứ 5) intent_type ngoài enum -> fallback "procedure"
#          (fail open, KHÔNG âm thầm coi là chitchat/out_of_scope) ---
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "gio_hanh_chinh_nao_do_khong_co_trong_enum",
        "primary_keyword": "đăng ký khai sinh", "province": "", "facet": "tong_quan"}):
    out3b = ex.extract("con em mới đẻ thì cần giấy gì để khai sinh")
check("extract() intent_type ngoài enum -> fallback 'procedure' (fail open)",
      out3b["intent_type"] == "procedure", out3b)

# --- 3c. intent_type=chitchat, model trả primary_keyword rỗng đúng hướng dẫn ---
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "chitchat", "primary_keyword": "", "province": "", "facet": "tong_quan"}):
    out3c = ex.extract("chào bạn")
check("extract() intent_type=chitchat -> giữ nguyên chitchat", out3c["intent_type"] == "chitchat", out3c)

# --- 4. resolve() end-to-end với DB thật: câu hỏi thô -> extract (mock) -> resolve_query thật ---
conn = s2.connect(str(HERE / "db" / "procedures.db"))
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "procedure",
        "primary_keyword": "đăng ký kết hôn", "province": "", "facet": "le_phi"}):
    r = ex.resolve("2 đứa định cưới cuối năm, lên phường làm giấy đăng ký cần mang gì", conn=conn)
check("resolve() found=True với keyword đã trích", r["found"] is True, r.get("debug"))
check("resolve() confident=True (tên chuẩn -> coverage cao)", r["confident"] is True, r)
check("resolve() có 'extracted' kèm facet", r["extracted"]["facet"] == "le_phi", r["extracted"])
check("resolve() primary đúng thủ tục kết hôn",
      "kết hôn" in r["primary"]["procedure"]["name"].lower(), r["primary"]["procedure"]["name"])

# --- 5. Follow-up: câu hỏi tiếp không nhắc thủ tục, LLM1 (mock) phải trả lại đúng từ lịch sử ---
history = [{"role": "user", "content": "thủ tục cấp lại thẻ căn cước cần gì"},
           {"role": "assistant", "content": "..."}]
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "procedure",
        "primary_keyword": "cấp lại thẻ căn cước", "province": "", "facet": "le_phi"}) as mock_call:
    r2 = ex.resolve("thế lệ phí bao nhiêu", history=history, conn=conn)
    # xác nhận user prompt có nhét lịch sử vào (không phải chỉ mỗi câu mới)
    sent_user_msg = mock_call.call_args[0][2]
check("resolve() follow-up found=True", r2["found"] is True)
check("_user_prompt() có nhét lịch sử vào lượt gọi LLM", "cấp lại thẻ căn cước" in sent_user_msg, sent_user_msg)
check("resolve() follow-up ra đúng thủ tục căn cước",
      "căn cước" in r2["primary"]["procedure"]["name"].lower(), r2["primary"]["procedure"]["name"])

# --- 6. render_card() không lỗi khi ghép với facet đã trích ---
html = s2.render_card(r["primary"], facet=r["extracted"]["facet"], suggestion=r["suggestion"])
check("render_card() chạy được với facet từ extractor", "<html" in html.lower() or "<div" in html.lower(),
      html[:80])

# --- 7. render_card() có 3 trường mới (yêu cầu Leader 22/09) + KHÔNG còn hiện
#        địa chỉ phường vào dòng "Cơ quan giải quyết" (gap dữ liệu cũ đã sửa) ---
check("render_card() có dòng 'Hình thức nộp'", "Hình thức nộp:" in html, html)
check("render_card() có dòng 'Cơ quan giải quyết'", "Cơ quan giải quyết:" in html, html)
# ponytail: CSDL mới có authority thật; test render_card với receiving_location và authority fallback Chưa rõ
html_with_loc = s2.render_card({"procedure": {**r["primary"]["procedure"], "receiving_location": "Địa điểm tiếp nhận mẫu", "authority": None}, "fees": [], "checklists": [], "files": []})
check("render_card() có dòng 'Địa điểm nộp trực tiếp'", "Địa điểm nộp trực tiếp:" in html_with_loc, html_with_loc)
check("render_card() 'Cơ quan giải quyết' = Chưa rõ (khi authority=None)",
      "Cơ quan giải quyết:</strong> Chưa rõ" in html_with_loc, html_with_loc)
check("render_card() KHÔNG còn banner hết hiệu lực tự động", "proc-alert-expired" not in html)

# --- 8. message: None khi confident=True, có format chuẩn khi found=False ---
check("resolve() message=None khi confident=True", r["message"] is None, r["message"])

with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "procedure",
        "primary_keyword": "xin visa du học mặt trăng 2099", "province": "", "facet": "tong_quan"}):
    r3 = ex.resolve("xin visa du học mặt trăng 2099", conn=conn)
expected_msg = "Xin lỗi, tôi không tìm thấy 'xin visa du học mặt trăng 2099' cho câu hỏi 'xin visa du học mặt trăng 2099'."
# Lưu ý: FTS5 AND->OR fallback gần như LUÔN trả về found=True (khớp yếu 1 vài
# token) cho câu ngoài phạm vi -- đây chính là lý do có cờ `confident` riêng
# (xem service.py). Case thật để test message là found=True nhưng
# confident=False, không phải found=False (hiếm khi xảy ra với data 70 thủ tục).
check("resolve() câu ngoài phạm vi -> confident=False", r3["confident"] is False, r3["debug"])
check("resolve() confident=False -> có message (không phải None)", r3["message"] is not None, r3["message"])
check("resolve() message đúng format Leader yêu cầu", r3["message"] == expected_msg, r3["message"])

# --- 9. (Fix 1, Ngày Thứ 5) resolve() với intent_type=chitchat -> KHÔNG chạm
#         FTS5 (mock resolve_query để phát hiện ngay nếu lỡ gọi), extracted
#         giữ nguyên intent_type để pipeline.py phân nhánh đúng ---
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "chitchat", "primary_keyword": "", "province": "", "facet": "tong_quan"}), \
     patch.object(ex.s2, "resolve_query") as mock_resolve_query:
    r4 = ex.resolve("chào bạn", conn=conn)
check("resolve() intent_type=chitchat -> found=False", r4["found"] is False, r4)
check("resolve() intent_type=chitchat -> confident=False", r4["confident"] is False, r4)
check("resolve() intent_type=chitchat -> extracted.intent_type giữ nguyên",
      r4["extracted"]["intent_type"] == "chitchat", r4["extracted"])
check("resolve() intent_type=chitchat -> KHÔNG gọi resolve_query (0 query FTS5)",
      mock_resolve_query.call_count == 0, mock_resolve_query.call_count)

# --- 10. resolve() với intent_type=out_of_scope -> tương tự, không lẫn với chitchat ---
with patch.object(ex.llm, "chat_json", return_value={
        "intent_type": "out_of_scope", "primary_keyword": "", "province": "", "facet": "tong_quan"}), \
     patch.object(ex.s2, "resolve_query") as mock_resolve_query2:
    r5 = ex.resolve("nấu phở bò thế nào", conn=conn)
check("resolve() intent_type=out_of_scope -> extracted.intent_type giữ nguyên (không lẫn chitchat)",
      r5["extracted"]["intent_type"] == "out_of_scope", r5["extracted"])
check("resolve() intent_type=out_of_scope -> KHÔNG gọi resolve_query",
      mock_resolve_query2.call_count == 0, mock_resolve_query2.call_count)

conn.close()

print()
if FAILED:
    print(f"=== {len(FAILED)} FAIL: {FAILED} ===")
    sys.exit(1)
print("=== TẤT CẢ TEST PASS ===")

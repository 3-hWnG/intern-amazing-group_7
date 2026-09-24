"""Test cục bộ customer_care.py — mock llm.chat (không có Ollama thật trong
sandbox), DÙNG DB THẬT (70 thủ tục, service.resolve_query) để bảng dữ liệu
đưa vào prompt là dữ liệu thật, không phải fixture tay. Chỉ kiểm tra WIRING
(đúng role, đúng dữ liệu, đúng câu hỏi tới model, lọc HTML khỏi lịch sử) —
hành vi "có từ chối bịa thật không" của Out-of-table Guard là hành vi LLM
THẬT, phải kiểm tra tay trên Ollama (xem README / Kịch bản 6)."""
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import customer_care as cc
import service as s2

FAILED = []


def check(name, cond, detail=""):
    status = "OK" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


conn = s2.connect(str(HERE / "db" / "procedures.db"))
prep = s2.resolve_query(conn, "đăng ký kết hôn")
check("(chuẩn bị) resolve_query tìm được thủ tục kết hôn để test", prep["found"] and prep["confident"])
full = prep["primary"]

# --- 1. Trả lời trong bảng: đúng role, đúng dữ liệu, đúng câu hỏi ---
with patch.object(cc.llm, "chat", return_value="Lệ phí đăng ký kết hôn là miễn phí.") as mock_call:
    out = cc.answer_procedure_query(full, "lệ phí bao nhiêu", "le_phi")
check("answer_procedure_query() gọi llm.chat với role customer_care_s2",
      mock_call.call_args[0][0] == "customer_care_s2", mock_call.call_args)
system_sent, user_sent = mock_call.call_args[0][1], mock_call.call_args[0][2]
check("system prompt có nhắc Out-of-table Guard", "KHÔNG có trong bảng" in system_sent, system_sent[:200])
check("user prompt có nhét đúng tên thủ tục thật vào bảng dữ liệu",
      full["procedure"]["name"] in user_sent, user_sent[:200])
check("user prompt có nhét đúng câu hỏi gốc", "lệ phí bao nhiêu" in user_sent)
check("câu trả lời không có số liệu -> Grounding Guard giữ nguyên text model sinh ra",
      out == "Lệ phí đăng ký kết hôn là miễn phí.")

# --- 1b. Grounding Guard: số tiền / số ngày KHÔNG có trong bảng -> bỏ câu bịa,
#         thay bằng nguyên văn ô CSDL; số có trong bảng -> giữ nguyên ---
duration = full["procedure"]["duration_desc"] or ""
fake = ("Chào bạn. Lệ phí là 123.456 đồng cho mỗi cặp.\n"
        "- Thời gian giải quyết khoảng 97 ngày làm việc.\n"
        "Bạn nộp tại UBND cấp xã nhé.")
with patch.object(cc.llm, "chat", return_value=fake):
    out_g = cc.answer_procedure_query(full, "lệ phí và mất mấy ngày", "le_phi")
check("Guard bỏ số tiền bịa (123.456 đồng)", "123.456" not in out_g, out_g)
check("Guard bỏ số ngày bịa (97 ngày)", "97 ngày" not in out_g, out_g)
check("Guard giữ các câu không chứa số liệu",
      "Chào bạn." in out_g and "Bạn nộp tại UBND cấp xã nhé." in out_g, out_g)
check("Guard nối nguyên văn ô lệ phí từ CSDL",
      "Lệ phí theo bảng niêm yết:" in out_g
      and all(f["amount_text"] in out_g for f in full["fees"]), out_g)
check("Guard nối nguyên văn ô thời hạn từ CSDL",
      f"Thời hạn giải quyết theo bảng niêm yết: {duration or 'Chưa rõ'}" in out_g, out_g)

fee_real = full["fees"][0]["amount_text"]  # vd "0 VNĐ"
real = f"Lệ phí là {fee_real}. Thời hạn: {duration}."
check("Guard giữ nguyên câu có số liệu KHỚP bảng",
      cc.ground_numbers(real, full) == real, cc.ground_numbers(real, full))
check("Guard hiểu cách viết khác đơn vị (50k == 50.000 đồng)",
      cc.ground_numbers("Phí 50k.", {**full, "fees": [{"fee_type": "Lệ phí", "amount_text": "50.000 đồng"}]})
      == "Phí 50k.")

# --- 2. Out-of-table: chỉ kiểm tra không crash + có nhắc facet đang hỏi vào
#        system prompt (nội dung model TỪ CHỐI BỊA thật hay không là hành vi
#        LLM thật, không test tự động được — xem docstring đầu file) ---
with patch.object(cc.llm, "chat", return_value="...") as mock_call2:
    out2 = cc.answer_procedure_query(full, "Cán bộ nào thụ lý hồ sơ này?", "tong_quan")
check("answer_procedure_query() không crash với câu hỏi ngoài bảng",
      isinstance(out2, str) and bool(out2))

# --- 3. Lịch sử có message kind="procedure_card" (HTML) PHẢI bị lọc khỏi
#        lịch sử gửi LLM 2 (tránh nhét HTML thô vào prompt mô hình nhỏ) ---
history = [
    {"role": "user", "content": "đăng ký kết hôn cần gì"},
    {"role": "assistant", "content": '<div class="procedure-card" data-proc-id="X">...</div>',
     "kind": "procedure_card"},
    {"role": "user", "content": "lệ phí bao nhiêu"},
    {"role": "assistant", "content": "Lệ phí là miễn phí.", "kind": "answer"},
]
with patch.object(cc.llm, "chat", return_value="...") as mock_call3:
    cc.answer_procedure_query(full, "nộp ở đâu", "noi_nop", history=history)
sent_history = mock_call3.call_args[0][3]
check("lịch sử gửi LLM 2 đã lọc bỏ message kind=procedure_card",
      all("procedure-card" not in (h.get("content") or "") for h in sent_history), sent_history)
check("lịch sử gửi LLM 2 vẫn giữ các lượt chữ thường (answer/user)",
      any("Lệ phí là miễn phí." in (h.get("content") or "") for h in sent_history), sent_history)

conn.close()

print()
if FAILED:
    print(f"=== {len(FAILED)} FAIL: {FAILED} ===")
    sys.exit(1)
print("=== TẤT CẢ TEST PASS ===")

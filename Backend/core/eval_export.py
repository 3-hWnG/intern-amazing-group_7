"""Xuất toàn bộ dữ liệu cuộc hội thoại thành file .txt chuẩn hoá dùng cho Chatbot (ChatGPT / Claude / ...) đánh giá."""

from __future__ import annotations

import json
from datetime import datetime

from config import LLM_MODEL, VERIFIER_ENABLED, VERIFIER_MODEL
from db.repositories import Conversations, Evidence, Messages, UserProfiles


def _format_dt(dt_str: str | None) -> str:
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt_str)[:19]


def build_conversation_export(conv_id: int, user_id: int) -> str:
    """Tạo nội dung text chi tiết cho 1 cuộc hội thoại để chatbot chấm điểm."""
    conv = Conversations.owned_by(conv_id, user_id)
    if not conv:
        return f"Không tìm thấy cuộc trò chuyện ID #{conv_id}."

    profile = UserProfiles.get(user_id)
    messages = Messages.list_for(conv_id)

    lines: list[str] = []
    sep_double = "=" * 80
    sep_single = "-" * 80

    lines.append(sep_double)
    lines.append("BẢN XUẤT ĐÁNH GIÁ CUỘC HỘI THOẠI — TRỢ LÝ THỦ TỤC HÀNH CHÍNH VIỆT NAM (V10)")
    lines.append(sep_double)
    lines.append("")
    lines.append("[THÔNG TIN CUỘC HỘI THOẠI]")
    lines.append(f"• Mã hội thoại: #{conv['id']}")
    lines.append(f"• Tiêu đề: {conv.get('title', 'Cuộc trò chuyện')}")
    lines.append(f"• Thời gian tạo: {_format_dt(conv.get('created_at'))}")
    lines.append(f"• Thời gian cập nhật: {_format_dt(conv.get('updated_at'))}")
    # Hệ thống trả lời — người chấm cần biết câu trả lời đến từ web hay CSDL nội bộ.
    _SYS = {"websearch": "Hệ thống 1 — Web search (.gov.vn qua MCP)",
            "retrieval": "Hệ thống 2 — CSDL thủ tục nội bộ"}
    _sys = conv.get("system") or "websearch"
    lines.append(f"• Hệ thống trả lời: {_SYS.get(_sys, _sys)}")
    lines.append(f"• Tổng số tin nhắn: {len(messages)}")
    lines.append(f"• Mô hình ngôn ngữ chính: {LLM_MODEL}")
    lines.append(f"• Kiểm chứng (Verifier): {VERIFIER_MODEL if VERIFIER_ENABLED else 'TẮT'}")
    if profile.get("province") or profile.get("ward"):
        lines.append(f"• Bộ nhớ người dùng (Profile): Tỉnh/thành={profile.get('province') or 'Chưa rõ'}, Xã/phường={profile.get('ward') or 'Chưa rõ'}")
    lines.append("")

    lines.append(sep_single)
    lines.append("LỜI NHẮC DÀNH CHO CHATBOT ĐÁNH GIÁ (EVALUATOR PROMPT)")
    lines.append(sep_single)
    lines.append("Bạn là chuyên gia thẩm định chất lượng (LLM Judge) về hệ thống Trợ lý ảo Thủ tục Hành chính Việt Nam.")
    lines.append("Dưới đây là toàn bộ diễn biến cuộc hội thoại thực tế của người dân và Trợ lý AI.")
    lines.append("Hãy phân tích toàn diện và đưa ra báo cáo đánh giá theo các tiêu chí sau:")
    lines.append("")
    lines.append("1. TÍNH CHÍNH XÁC VÀ PHÁP LÝ (Thang điểm 1-10):")
    lines.append("   - Thủ tục, cơ quan tiếp nhận, thành phần hồ sơ, lệ phí, thời hạn giải quyết có đúng quy định pháp luật Việt Nam (bối cảnh áp dụng năm 2026, 34 tỉnh/thành, chính quyền 2 cấp tỉnh - xã) không?")
    lines.append("2. CĂN CỨ NGUỒN VÀ CHỐNG ẢO GIÁC (Thang điểm 1-10):")
    lines.append("   - Câu trả lời có bám sát dữ liệu tra cứu được (Evidence Pack) không? Các trích dẫn [S#] có trung thực không? Có bịa đặt thông tin ngoài nguồn không?")
    lines.append("3. ĐIỀU HƯỚNG VÀ XỬ LÝ TƯƠNG TÁC (Thang điểm 1-10):")
    lines.append("   - Khi người dùng hỏi mơ hồ/chưa rõ, AI có đưa ra đúng các gợi ý tìm kiếm DuckDuckGo thiết thực (Cách 3) không? Khi người dùng chọn gợi ý, AI có trả lời trúng đích không?")
    lines.append("4. HIỆU QUẢ CỦA BỘ KIỂM CHỨNG (VERIFIER):")
    lines.append("   - Đánh giá cảnh báo của Verifier (PASS/FAIL) và độ tin cậy đối với người dân.")
    lines.append("")
    lines.append("-> Vui lòng nhận xét chi tiết từng lượt trao đổi và đưa ra ĐIỂM TỔNG KẾT (Overall Score 1-10) kèm khuyến nghị.")
    lines.append(sep_double)
    lines.append("DIỄN BIẾN CHI TIẾT TỪNG LƯỢT HỘI THOẠI")
    lines.append(sep_double)
    lines.append("")

    mcp_count = 0
    pass_count = 0
    verified_count = 0
    used_domains: set[str] = set()

    for idx, m in enumerate(messages):
        role = m.get("role", "")
        content = m.get("content", "").strip()
        kind = m.get("kind", "")
        verdict = m.get("verdict", "")
        created_at = _format_dt(m.get("created_at"))

        if role == "user":
            lines.append(f"[TIN NHẮN {idx + 1}] — NGƯỜI DÙNG ({created_at})")
            lines.append(f"Nội dung: {content}")
            lines.append("")
        else:
            lines.append(f"[TIN NHẮN {idx + 1}] — TRỢ LÝ ẢO (Loại: {kind or 'answer'}) ({created_at})")

            # Parse intent_json
            intent_data = {}
            if m.get("intent_json"):
                try:
                    intent_data = json.loads(m["intent_json"])
                except Exception:
                    pass

            if intent_data:
                intent_name = intent_data.get("intent", "")
                standalone = intent_data.get("standalone_question", "")
                missing = intent_data.get("missing_information", [])
                choices = intent_data.get("choices", [])
                queries = intent_data.get("search_queries", [])

                lines.append("  ⚙ Phân tích hệ thống (Intent & Route):")
                if intent_name:
                    lines.append(f"    • Ý định nhận diện: {intent_name}")
                if standalone and standalone != content:
                    lines.append(f"    • Câu hỏi độc lập: {standalone}")
                if missing:
                    lines.append(f"    • Thông tin còn thiếu: {', '.join(missing)}")
                if choices:
                    lines.append("    • 💡 Gợi ý tìm kiếm DuckDuckGo đưa ra (Cách 3):")
                    for c_idx, c_text in enumerate(choices, 1):
                        lines.append(f"       [{c_idx}] {c_text}")
                if queries:
                    lines.append(f"    • Truy vấn tìm kiếm: {', '.join(queries)}")

            # Lấy Evidence Pack nếu có
            evidence_pack = Evidence.for_message(m["id"], user_id)
            if evidence_pack:
                mcp_count += 1
                sources = evidence_pack.get("sources") or []
                lines.append(f"  📚 Bằng chứng thu thập từ MCP / DuckDuckGo ({len(sources)} nguồn):")
                for s_idx, s in enumerate(sources, 1):
                    s_title = s.get("title") or "Không tiêu đề"
                    s_url = s.get("url") or ""
                    s_domain = s.get("domain") or ""
                    if s_domain:
                        used_domains.add(s_domain)
                    s_trust = s.get("trust_label") or s.get("trust") or "nguồn web"
                    s_snip = (s.get("snippet") or s.get("best_passage") or "").strip()
                    if len(s_snip) > 280:
                        s_snip = s_snip[:280] + "…"
                    lines.append(f"    [S{s_idx}] {s_title}")
                    lines.append(f"         URL: {s_url} ({s_trust})")
                    if s_snip:
                        lines.append(f"         Trích đoạn: \"{s_snip}\"")

            # Kết quả Verifier
            if verdict:
                verified_count += 1
                if verdict == "PASS":
                    pass_count += 1
                    lines.append("  ✓ Kiểm chứng (Verifier): PASS (Đã kiểm chứng bám sát nguồn)")
                else:
                    lines.append(f"  ⚠ Kiểm chứng (Verifier): {verdict} (Chưa được xác nhận đầy đủ với nguồn)")

            lines.append("  💬 Câu trả lời xuất ra:")
            for c_line in content.split("\n"):
                lines.append(f"    {c_line}")
            lines.append("")
            lines.append(sep_single)

    lines.append("")
    lines.append(sep_double)
    lines.append("TỔNG HỢP THỐNG KÊ PHIÊN HỘI THOẠI")
    lines.append(sep_double)
    user_msgs = sum(1 for m in messages if m.get("role") == "user")
    asst_msgs = sum(1 for m in messages if m.get("role") == "assistant")
    lines.append(f"• Tổng số lượt tương tác: {len(messages)} tin nhắn ({user_msgs} câu hỏi, {asst_msgs} phản hồi)")
    lines.append(f"• Số lượt tra cứu qua MCP/DuckDuckGo: {mcp_count}")
    if verified_count > 0:
        pass_pct = round((pass_count / verified_count) * 100, 1)
        lines.append(f"• Tỷ lệ kiểm chứng đạt chuẩn (PASS): {pass_count}/{verified_count} ({pass_pct}%)")
    else:
        lines.append("• Số lượt cần kiểm chứng nguồn: 0")
    if used_domains:
        lines.append(f"• Các tên miền đã tham khảo: {', '.join(sorted(used_domains))}")
    lines.append(sep_double)
    lines.append("HẾT BẢN XUẤT. BẠN CÓ THỂ DÁN TOÀN BỘ FILE NÀY VÀO CHATBOT ĐỂ ĐÁNH GIÁ.")
    lines.append(sep_double)

    return "\n".join(lines)


def build_all_conversations_export(user_id: int) -> str:
    """Xuất tất cả các cuộc hội thoại của người dùng vào 1 file tổng hợp."""
    convs = Conversations.list_for(user_id, limit=200)
    if not convs:
        return "Chưa có cuộc trò chuyện nào để xuất."

    parts: list[str] = []
    parts.append("=" * 80)
    parts.append("TỔNG HỢP TOÀN BỘ CUỘC HỘI THOẠI ĐÁNH GIÁ HỆ THỐNG TRỢ LÝ HÀNH CHÍNH")
    parts.append(f"Thời gian xuất: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    parts.append(f"Tổng số cuộc trò chuyện: {len(convs)}")
    parts.append("=" * 80)
    parts.append("\n\n")

    for c in convs:
        part = build_conversation_export(c["id"], user_id)
        parts.append(part)
        parts.append("\n\n" + ("#" * 80) + "\n\n")

    return "\n".join(parts)

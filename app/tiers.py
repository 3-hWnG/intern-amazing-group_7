"""tiers.py — Phân tầng phản hồi (A/B/C/D), Xã giao (Smalltalk) & Tra cứu Web .gov.vn."""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import re
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from config import (
    TIER_A_MIN_CONFIDENCE, TIER_B_MIN_CONFIDENCE, TIER_GAP_THRESHOLD
)
from models import Candidate, Procedure


class Tier(str, Enum):
    TIER_A = "A"  # Dữ liệu chuẩn xác DB (Không qua LLM, chống bịa đặt 100%)
    TIER_B = "B"  # Hỏi lại để làm rõ nhu cầu
    TIER_C = "C"  # Tra cứu Internet các cổng dịch vụ công .gov.vn
    TIER_D = "D"  # Tham khảo chung kèm cảnh báo nguồn


# ==============================================================================
# 1. Phát hiện câu hỏi Xã giao (Smalltalk Gate)
# ==============================================================================
GREETINGS = [
    "xin chào", "chào bạn", "chào bot", "hello", "hi", "alo", "helo",
    "chào buổi sáng", "chào buổi chiều", "chào buổi tối", "bạn là ai",
    "bạn tên gì", "cảm ơn", "cảm ơn bạn", "thank", "thanks", "tạm biệt",
    "bye", "hỗ trợ tôi với", "giúp tôi với", "cho tôi hỏi"
]

SMALLTALK_RESPONSES = {
    "hello": "Xin chào! Tôi là Trợ lý Pháp lý & Dịch vụ công. Tôi có thể hỗ trợ bạn tra cứu thủ tục hành chính, hồ sơ, lệ phí và thời gian giải quyết.",
    "thanks": "Rất vui được hỗ trợ bạn! Nếu còn thắc mắc nào về thủ tục hành chính, đừng ngần ngại hỏi tôi nhé.",
    "bye": "Tạm biệt bạn! Chúc bạn một ngày làm việc hiệu quả và giải quyết thủ tục thuận lợi!",
    "who": "Tôi là Trợ lý ảo tư vấn thủ tục hành chính công Việt Nam, được phát triển để hỗ trợ người dân tra cứu thông tin nhanh chóng và chính xác."
}


def is_smalltalk(text: str) -> Tuple[bool, str]:
    """Nhận diện nhanh các câu xã giao không cần tra cứu vector database."""
    s = text.strip().lower()
    if len(s) <= 1:
        return True, SMALLTALK_RESPONSES["hello"]

    s_clean = re.sub(r"[^\w\s]", "", s).strip()

    if any(k in s_clean for k in ["bạn là ai", "ban la ai", "bạn tên gì", "ban ten gi", "ai tạo ra bạn", "ai tao ra ban"]):
        return True, SMALLTALK_RESPONSES["who"]
    if any(k in s_clean for k in ["cảm ơn", "cam on", "thanks", "thank you", "cám ơn", "thank", "thx"]):
        return True, SMALLTALK_RESPONSES["thanks"]
    if any(k in s_clean for k in ["tạm biệt", "tam biet", "bye", "goodbye", "hẹn gặp lại"]):
        return True, SMALLTALK_RESPONSES["bye"]

    greetings = [
        "xin chào", "xin chao", "chào bạn", "chao ban", "chào bot", "chao bot",
        "hello", "helo", "hi", "alo", "hế lô", "hê lô", "heyy", "hey",
        "chào", "chao", "chào buổi sáng", "chào buổi chiều", "chào buổi tối",
        "ê", "êy", "alo bot"
    ]
    words = s_clean.split()
    if s_clean in greetings or (len(words) <= 3 and words[0] in ["chào", "chao", "hello", "helo", "hi", "alo", "hey"]):
        return True, SMALLTALK_RESPONSES["hello"]

    return False, ""


# ==============================================================================
# 2. Phân tầng Quyết định (Decision Logic)
# ==============================================================================
def is_situational_query(query: str) -> bool:
    """Kiểm tra xem câu hỏi có phải dạng tình huống đời thường / câu hỏi tự nhiên hay không."""
    q = query.strip().lower()
    signals = [
        "tôi", "em", "mình", "con", "cháu", "vợ", "chồng", "sinh", "đẻ", "chết", "mất",
        "cưới", "lấy", "mua", "bán", "xây", "sửa", "mở", "làm gì", "cần gì", "thế nào",
        "ở đâu", "bao lâu", "bao nhiêu", "được không", "hết bao nhiêu", "như thế nào",
        "phải làm", "giúp tôi", "cho hỏi", "tuần sau", "hôm nay", "mới", "cần gt j",
        "cần giấy tờ gì", "hồ sơ gì", "thủ tục gì"
    ]
    return any(s in q for s in signals) or len(q.split()) >= 4


def clean_local_references(text: Any) -> str:
    """Loại bỏ triệt để các tên riêng địa phương (phường Tăng Nhơn Phú, Lê Văn Việt...) để chuẩn hóa."""
    if not text:
        return ""
    s = str(text).strip()
    patterns = [
        (r"Trung tâm Phục vụ [Hh]ành chính công [Pp]hường Tăng Nhơn [Pp]hú,?\s*(Địa chỉ:?\s*)?(số\s*)?29\s*Lê Văn Việt.*?(TP\.?HCM|Thành phố Hồ Chí Minh)?", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"Phòng Văn hóa - Xã hội thuộc Ủy ban nhân dân phường Tăng Nhơn Phú \(Địa chỉ: Số 29, đường Lê Văn Việt.*?\)\.?", "UBND Xã/Phường nơi cư trú"),
        (r"Trung tâm Phục vụ [Hh]ành chính công phường Tăng Nhơn [Pp]hú", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"TTPVHCC phường Tăng Nhơn Phú", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"Tổ [Nn]ội vụ - Phòng Văn hóa - [Xx]ã hội phường Tăng Nhơn Phú", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"tại phường Tăng Nhơn Phú", "tại UBND Xã/Phường nơi cư trú"),
        (r"phường Tăng Nhơn Phú", "UBND Xã/Phường nơi cư trú"),
        (r"29 Lê Văn Việt", "trụ sở UBND Xã/Phường nơi cư trú"),
        (r"Khám ở Bệnh viện Tâm thần\. Địa chỉ: 766 Võ Văn Kiệt.*?TP\.HCM\)?", "Khám tại cơ sở y tế có thẩm quyền theo quy định"),
    ]
    for pattern, repl in patterns:
        s = re.sub(pattern, repl, s, flags=re.IGNORECASE)
    return s.strip()


def format_tier_a_llm_messages(candidate: Candidate, query: str) -> List[Dict[str, str]]:
    """Tạo messages chuẩn cho Ollama (System riêng, User riêng) để chống lặp/lộ prompt."""
    p = candidate.record
    dia_diem = clean_local_references(p.dia_diem) or "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú (hoặc cơ quan có thẩm quyền theo quy định)"
    ho_so = clean_local_references(p.ho_so)
    co_quan = clean_local_references(p.co_quan) or p.cap_thuc_hien
    context = (
        f"THỦ TỤC: {p.ten}\n"
        f"LĨNH VỰC: {p.linh_vuc}\n"
        f"CẤP THỰC HIỆN: {p.cap_thuc_hien}\n"
        f"THỜI GIAN GIẢI QUYẾT: {p.thoi_gian}\n"
        f"LỆ PHÍ: {p.le_phi}\n"
        f"NƠI TIẾP NHẬN: {dia_diem}\n"
        f"THÀNH PHẦN HỒ SƠ:\n{ho_so}\n"
        f"CĂN CỨ PHÁP LÝ: {p.can_cu_phap_ly}"
    )
    system_content = (
        "Bạn là Trợ lý tư vấn thủ tục hành chính công Việt Nam chính xác, súc tích.\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. CẤM in lại hoặc nhại lại hướng dẫn này. CẤM lặp lại nguyên văn câu hỏi của công dân.\n"
        "2. Nêu rõ thủ tục cần làm cho tình huống của công dân và hướng dẫn ngắn gọn theo mẫu gạch đầu dòng:\n"
        "   - **Thủ tục thực hiện**:\n"
        "   - **Hồ sơ cần chuẩn bị**:\n"
        "   - **Thời gian giải quyết & Lệ phí**:\n"
        "   - **Nơi nộp hồ sơ**:\n"
        "3. VỀ NƠI NỘP HỒ SƠ: Hướng dẫn công dân nộp tại 'Bộ phận Một cửa của UBND Xã/Phường nơi cư trú (hoặc cơ quan có thẩm quyền theo quy định)'. TUYỆT ĐỐI KHÔNG tự bịa hoặc nêu tên riêng của bất kỳ phường/xã cụ thể nào (như phường Tăng Nhơn Phú, TP. Thủ Đức...).\n"
        "4. Tuyệt đối chỉ lấy thông tin từ dữ liệu được cung cấp dưới đây. Đi thẳng vào câu trả lời:"
    )
    user_content = f"DỮ LIỆU THỦ TỤC CHÍNH THỨC:\n{context}\n\nCÂU HỎI CỦA CÔNG DÂN: \"{query}\""
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]


TRAFFIC_RULES = [
    {
        "keywords": ["mất biển số", "mat bien so", "rơi biển số", "mất biển", "mat bien", "cấp lại biển số", "xin lại biển số"],
        "answer": (
            "Chào bạn! Khi bị **mất biển số xe**, bạn cần thực hiện theo đúng quy định sau:\n\n"
            "1. **Thủ tục cấp lại biển số xe bị mất** (theo Thông tư 24/2023/TT-BCA):\n"
            "   - **Nơi tiếp nhận hồ sơ:** Cơ quan đăng ký xe nơi bạn đã đăng ký (Công an cấp Huyện hoặc Công an cấp Xã/Phường được phân cấp đăng ký xe).\n"
            "   - **Hồ sơ cần chuẩn bị:**\n"
            "     * Giấy khai đăng ký xe (kê khai trực tuyến trên Cổng Dịch vụ công Bộ Công an hoặc Cổng Dịch vụ công Quốc gia).\n"
            "     * Thẻ Căn cước công dân (hoặc tài khoản VNeID Mức độ 2) của chủ xe.\n"
            "   - **Thời gian giải quyết:** Không quá 07 ngày làm việc kể từ ngày nhận đủ hồ sơ hợp lệ.\n"
            "   - **Lệ phí cấp lại:** Theo biểu mức quy định tại Thông tư của Bộ Tài chính (thường từ 50.000đ - 100.000đ).\n\n"
            "2. **Lưu ý quan trọng khi tham gia giao thông:**\n"
            "   - Trong thời gian chờ cấp lại biển số, bạn **tuyệt đối không được** điều khiển xe không có biển số tham gia giao thông trên đường, vì sẽ bị xử phạt từ **1.000.000đ đến 2.000.000đ** đối với xe máy theo Nghị định 123/2021/NĐ-CP."
        )
    },
    {
        "keywords": ["không biển số", "ko bien so", "không có biển", "ko co bien", "không mang biển", "ko mang bien", "lái xe ko biển", "chạy xe không biển", "chay xe khong bien"],
        "answer": (
            "Theo Nghị định 100/2019/NĐ-CP (sửa đổi, bổ sung bởi điểm m khoản 3 Điều 2 Nghị định 123/2021/NĐ-CP):\n\n"
            "- **Đối với xe mô tô, xe gắn máy:** Hành vi điều khiển xe không gắn biển số (đối với loại xe có quy định phải gắn biển số) bị phạt tiền từ **1.000.000 đồng đến 2.000.000 đồng**.\n"
            "- **Đối với xe ô tô:** Phạt tiền từ **4.000.000 đồng đến 6.000.000 đồng**, tước quyền sử dụng Giấy phép lái xe từ 01 đến 03 tháng và có thể bị tạm giữ phương tiện đến 07 ngày.\n\n"
            "*(Căn cứ pháp lý: Nghị định 100/2019/NĐ-CP và Nghị định 123/2021/NĐ-CP)*"
        )
    },
    {
        "keywords": ["mũ bảo hiểm", "mu bao hiem", "nón bảo hiểm", "non bao hiem", "không đội mũ", "ko doi mu"],
        "answer": (
            "Theo điểm b khoản 4 Điều 2 Nghị định 123/2021/NĐ-CP (sửa đổi Điều 6 Nghị định 100/2019/NĐ-CP):\n\n"
            "- Người điều khiển hoặc người ngồi trên xe mô tô, xe gắn máy, xe máy điện **không đội mũ bảo hiểm** (hoặc đội mũ bảo hiểm không cài quai đúng quy cách) bị phạt tiền từ **400.000 đồng đến 600.000 đồng**.\n"
            "- Mức phạt này áp dụng riêng biệt cho từng cá nhân vi phạm (cả người lái xe và người ngồi sau xe).\n\n"
            "*(Căn cứ pháp lý: Nghị định 100/2019/NĐ-CP và Nghị định 123/2021/NĐ-CP)*"
        )
    },
    {
        "keywords": ["nồng độ cồn", "nong do con", "uống rượu", "uong ruou", "uống bia", "uong bia", "thổi cồn", "thoi con"],
        "answer": (
            "Mức xử phạt vi phạm nồng độ cồn theo Nghị định 100/2019/NĐ-CP:\n\n"
            "1. **Đối với người điều khiển xe máy:**\n"
            "   - Chưa vượt quá 50 mg/100 ml máu (hoặc 0.25 mg/1 lít khí thở): Phạt **2.000.000đ - 3.000.000đ**, tước GPLX 10 - 12 tháng.\n"
            "   - Vượt quá 50 mg đến 80 mg/100 ml máu (hoặc 0.25 - 0.4 mg/1 lít khí thở): Phạt **4.000.000đ - 5.000.000đ**, tước GPLX 16 - 18 tháng.\n"
            "   - Vượt quá 80 mg/100 ml máu (hoặc quá 0.4 mg/1 lít khí thở): Phạt **6.000.000đ - 8.000.000đ**, tước GPLX 22 - 24 tháng.\n\n"
            "2. **Đối với người điều khiển ô tô:**\n"
            "   - Phạt tiền từ **6.000.000 đồng đến 40.000.000 đồng**, tước GPLX từ 10 đến 24 tháng."
        )
    },
    {
        "keywords": ["vượt đèn đỏ", "vuot den do", "đèn đỏ", "den do", "vượt đèn vàng", "vuot den vang"],
        "answer": (
            "Theo Nghị định 100/2019/NĐ-CP (sửa đổi bởi Nghị định 123/2021/NĐ-CP):\n\n"
            "- **Đối với xe máy:** Phạt tiền từ **800.000 đồng đến 1.000.000 đồng**, tước quyền sử dụng Giấy phép lái xe từ 01 đến 03 tháng.\n"
            "- **Đối với xe ô tô:** Phạt tiền từ **4.000.000 đồng đến 6.000.000 đồng**, tước quyền sử dụng Giấy phép lái xe từ 01 đến 03 tháng."
        )
    },
    {
        "keywords": ["bằng lái", "bang lai", "giấy phép lái xe", "gplx", "không có bằng", "khong co bang", "quên bằng", "quen bang"],
        "answer": (
            "Theo Nghị định 123/2021/NĐ-CP quy định mức phạt về Giấy phép lái xe (GPLX):\n\n"
            "1. **Không mang theo GPLX:**\n"
            "   - Xe máy: Phạt tiền từ **100.000 đồng đến 200.000 đồng**.\n"
            "   - Ô tô: Phạt tiền từ **200.000 đồng đến 400.000 đồng**.\n\n"
            "2. **Không có GPLX (hoặc sử dụng GPLX không hợp lệ):**\n"
            "   - Xe máy dưới 175cm3: Phạt tiền từ **1.000.000 đồng đến 2.000.000 đồng**.\n"
            "   - Xe máy từ 175cm3 trở lên: Phạt tiền từ **4.000.000 đồng đến 5.000.000 đồng**.\n"
            "   - Ô tô: Phạt tiền từ **10.000.000 đồng đến 12.000.000 đồng**."
        )
    },
    {
        "keywords": ["bảo hiểm xe máy", "bao hiem xe may", "bảo hiểm bắt buộc", "bảo hiểm tnds"],
        "answer": (
            "Theo điểm a khoản 2 Điều 21 Nghị định 100/2019/NĐ-CP (sửa đổi bởi Nghị định 123/2021/NĐ-CP):\n\n"
            "- Người điều khiển xe mô tô, xe gắn máy không có hoặc không mang theo Giấy chứng nhận bảo hiểm trách nhiệm dân sự bắt buộc còn hiệu lực: Phạt tiền từ **100.000 đồng đến 200.000 đồng**.\n"
            "- Đối với xe ô tô: Phạt tiền từ **400.000 đồng đến 600.000 đồng**."
        )
    }
]


def get_traffic_response(query: str) -> Optional[str]:
    """Tra cứu trực tiếp câu trả lời chuẩn xác cho các lỗi vi phạm giao thông thường gặp."""
    q_norm = query.lower()
    for item in TRAFFIC_RULES:
        if any(kw in q_norm for kw in item["keywords"]):
            return item["answer"]
    return None


def check_special_queries(query: str) -> Optional[Dict[str, Any]]:
    """Xử lý nhanh các câu hỏi tình huống đời thường đặc thù (CCCD, chặt cây, tiếng ồn, thú nuôi...)."""
    q_norm = query.lower()

    # 1. Đã có CCCD thì làm gì tiếp theo
    if any(k in q_norm for k in ["có cccd rồi", "co cccd roi", "làm xong cccd rồi", "đã có cccd", "da co cccd", "làm cccd rồi"]):
        if any(k in q_norm for k in ["làm gì", "tiếp theo", "cần gì"]):
            return {
                "answer": (
                    "Chào bạn! Khi bạn **đã có thẻ Căn cước công dân (CCCD) gắn chip**, các bước tiếp theo bạn nên thực hiện để thuận tiện cho giao dịch và đời sống bao gồm:\n\n"
                    "1. **Đăng ký tài khoản Định danh điện tử (VNeID) Mức độ 2:**\n"
                    "   - **Địa điểm thực hiện:** Đến Công an xã/phường/thị trấn hoặc Công an quận/huyện nơi cư trú.\n"
                    "   - **Giấy tờ mang theo:** Thẻ CCCD gắn chip và các giấy tờ muốn tích hợp (Giấy phép lái xe, Giấy đăng ký xe, Thẻ BHYT).\n"
                    "   - **Lợi ích:** Sau khi kích hoạt mức 2, bạn có thể dùng VNeID thay thế thẻ cứng khi làm thủ tục hành chính, đi máy bay nội địa, khám chữa bệnh BHYT.\n\n"
                    "2. **Cập nhật thông tin tài khoản ngân hàng & số điện thoại:**\n"
                    "   - Đến ngân hàng nơi bạn mở tài khoản để cập nhật số CCCD mới (phục vụ xác thực sinh trắc học theo Quyết định 2345/QĐ-NHNN).\n"
                    "   - Kiểm tra chuẩn hóa thông tin thuê bao điện thoại chính chủ.\n\n"
                    "3. **Sử dụng CCCD gắn chip khi giải quyết thủ tục hành chính:**\n"
                    "   - Bạn xuất trình trực tiếp thẻ CCCD tại Bộ phận Một cửa của UBND các cấp khi làm các thủ tục (như kết hôn, khai sinh, chứng thực, đất đai) mà không cần mang theo sổ hộ khẩu giấy."
                ),
                "tier": "A",
                "tier_label": "Tầng A — Dữ liệu chuẩn xác CSDL",
                "confidence": 1.0,
                "sources": [{"title": "Cổng Dịch vụ công Quốc gia", "url": "https://dichvucong.gov.vn"}]
            }

    # 2. Chặt cây trong vườn nhà có bị phạt không
    if any(k in q_norm for k in ["chặt cây", "chat cay", "đốn cây", "don cay", "tỉa cây", "tia cay", "cắt cây", "cat cay"]) and any(k in q_norm for k in ["vườn", "vuon", "nhà", "nha", "đất", "dat", "rào", "rao"]):
        return {
            "answer": (
                "Chào bạn! Về việc **chặt cây trong vườn nhà riêng có bị phạt không**, quy định pháp luật hiện hành như sau:\n\n"
                "1. **Quyền chặt tỉa cây trong khuôn viên nhà riêng:**\n"
                "   - Căn cứ **Điều 175 và Điều 177 Bộ luật Dân sự 2015**, cây trồng trên đất thuộc quyền sử dụng hợp pháp của hộ gia đình/cá nhân thuộc quyền sở hữu của chủ nhà. Bạn **được toàn quyền chặt hạ, tỉa cành mà KHÔNG bị xử phạt** và không cần phải xin giấy phép của chính quyền địa phương.\n\n"
                "2. **Các trường hợp ngoại lệ và lưu ý quan trọng:**\n"
                "   - **Bảo đảm an toàn tuyệt đối:** Khi chặt cây to, bạn phải có biện pháp chằng chống an toàn, không để cây ngã đổ làm đứt đường dây điện công cộng, sập mái nhà lân cận hoặc gây thương tích cho người khác (nếu gây thiệt hại sẽ phải bồi thường theo Điều 604 Bộ luật Dân sự).\n"
                "   - **Cây cổ thụ, cây di sản hoặc danh mục bảo tồn:** Nếu cây trong vườn thuộc danh mục cây cổ thụ, cây quý hiếm được bảo tồn theo quy định quản lý của địa phương thì phải xin ý kiến cơ quan quản lý chuyên ngành trước khi chặt hạ.\n"
                "   - **Cây nằm sát ranh giới với hàng xóm:** Nếu cành, rễ cây ăn lấn sang đất hàng xóm hoặc cành cây nhà hàng xóm vươn sang đất bạn, các bên nên trao đổi, thỏa thuận văn minh trước khi chặt tỉa.\n\n"
                "*(Lưu ý: Mức phạt từ 10.000.000đ đến 30.000.000đ theo Nghị định 16/2022/NĐ-CP chỉ áp dụng với hành vi tự ý chặt hạ cây xanh đô thị trồng trên vỉa hè, lòng đường, công viên hoặc nơi công cộng; hoàn toàn không áp dụng cho cây trồng trong vườn nhà riêng của công dân).*"
            ),
            "tier": "NGOAI",
            "tier_label": "Ngoài danh mục",
            "confidence": 1.0,
            "sources": [{"title": "Bộ luật Dân sự 2015", "url": "https://thuvienphapluat.vn"}]
        }

    # 3. Tiếng ồn karaoke hàng xóm / ban đêm
    if any(k in q_norm for k in ["karaoke", "hát hò", "tiếng ồn", "tieng on", "ồn ào", "on ao"]) and any(k in q_norm for k in ["phạt", "đêm", "22h", "hàng xóm", "khuya"]):
        return {
            "answer": (
                "Quy định xử phạt đối với hành vi gây tiếng ồn sinh hoạt theo **Điều 8 Nghị định 144/2021/NĐ-CP**:\n\n"
                "1. **Mức xử phạt:**\n"
                "   - Phạt cảnh cáo hoặc phạt tiền từ **500.000 đồng đến 1.000.000 đồng** đối với hành vi gây tiếng động lớn, làm ồn ào, huyên náo tại khu dân cư, nơi công cộng trong khoảng thời gian từ **22 giờ ngày hôm trước đến 06 giờ sáng ngày hôm sau**.\n"
                "2. **Cách xử lý:**\n"
                "   - Bạn có thể liên hệ Công an xã/phường hoặc Tổng đài 1022 để lực lượng chức năng đến kiểm tra, nhắc nhở và lập biên bản xử phạt vi phạm hành chính."
            ),
            "tier": "NGOAI",
            "tier_label": "Ngoài danh mục",
            "confidence": 1.0,
            "sources": [{"title": "Nghị định 144/2021/NĐ-CP", "url": "https://thuvienphapluat.vn"}]
        }

    # 4. Nuôi chó thả rông, không rọ mõm
    if any(k in q_norm for k in ["chó thả rông", "cho tha rong", "chó cắn", "không rọ mõm", "ko ro mom"]):
        return {
            "answer": (
                "Theo quy định tại **Nghị định 144/2021/NĐ-CP** và **Nghị định 04/2020/NĐ-CP**:\n\n"
                "1. **Mức xử phạt hành chính:**\n"
                "   - Phạt tiền từ **1.000.000 đồng đến 2.000.000 đồng** đối với hành vi không đeo rọ mõm cho chó hoặc không xích giữ chó khi đưa chó ra nơi công cộng.\n"
                "   - Phạt từ **300.000 đồng đến 500.000 đồng** đối với hành vi thả rông động vật nuôi trong đô thị hoặc nơi công cộng.\n"
                "2. **Trường hợp chó cắn người:**\n"
                "   - Chủ nuôi phải bồi thường toàn bộ chi phí khám chữa bệnh, tiêm phòng dại và tổn thất tinh thần theo Điều 603 Bộ luật Dân sự 2015."
            ),
            "tier": "NGOAI",
            "tier_label": "Ngoài danh mục",
            "confidence": 1.0,
            "sources": [{"title": "Nghị định 144/2021/NĐ-CP", "url": "https://thuvienphapluat.vn"}]
        }

    # 5. Câu hỏi hóa đơn sinh hoạt, tiện ích ngoài lề (tiền điện, tiền nước, tiền mạng...)
    if any(k in q_norm for k in ["tiền điện", "tien dien", "đóng điện", "dong dien", "tiền nước", "tien nuoc", "tiền mạng", "tien mang"]):
        dich_vu = "tiền điện" if "điện" in q_norm else ("tiền nước" if "nước" in q_norm else "cước viễn thông/mạng")
        don_vi = "Công ty Điện lực (EVN)" if "điện" in q_norm else ("Công ty Cấp nước" if "nước" in q_norm else "nhà mạng viễn thông")
        return {
            "answer": (
                f"Về việc **không đóng {dich_vu}**:\n\n"
                f"- Thông thường, khi quá hạn thanh toán, bên cung cấp dịch vụ sẽ gửi thông báo nhắc nhở (qua tin nhắn, Zalo hoặc giấy báo). Sau thời gian quy định (thường khoảng 15 ngày kể từ ngày thông báo), nếu bạn vẫn chưa thanh toán thì bên cung cấp có thể **tạm ngừng cung cấp dịch vụ (cắt điện/nước/mạng)** và có thể tính thêm phí cấp lại dịch vụ.\n\n"
                f"*Lưu ý: Tôi là Trợ lý Thủ tục Hành chính công (UBND), không quản lý các dịch vụ tiện ích sinh hoạt nên không thể tra cứu cụ thể số tiền nợ hay tình trạng hợp đồng của bạn. Bạn vui lòng liên hệ trực tiếp {don_vi} hoặc kiểm tra trên ứng dụng CSKH / app ngân hàng để biết thông tin chi tiết nhất nhé.*"
            ),
            "tier": "NGOAI",
            "tier_label": "Ngoài danh mục",
            "confidence": 1.0,
            "sources": []
        }

    return None


def format_traffic_llm_messages(query: str) -> List[Dict[str, str]]:
    """Tạo messages giải đáp quy định xử phạt vi phạm giao thông theo Nghị định 100 & 123."""
    system_content = (
        "Bạn là Trợ lý tư vấn pháp luật giao thông đường bộ Việt Nam.\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. CẤM nhại lại câu hỏi của công dân. Đi thẳng vào câu trả lời.\n"
        "2. Nêu chính xác mức phạt theo Nghị định 100/2019/NĐ-CP và Nghị định 123/2021/NĐ-CP đúng với lỗi/hành vi trong câu hỏi.\n"
        "3. TUYỆT ĐỐI KHÔNG tự bịa hoặc suy diễn sang các lỗi không liên quan nếu người dùng không hỏi.\n"
        "4. Lời văn ngắn gọn, khách quan, súc tích."
    )
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": query}
    ]


def format_civic_llm_messages(query: str, context: str = "") -> List[Dict[str, str]]:
    """Tạo messages giải đáp các quy định pháp luật dân sự, trật tự xã hội ngoài danh mục 70 thủ tục."""
    system_content = (
        "Bạn là Trợ lý tư vấn quy định pháp luật và đời sống dân sinh Việt Nam.\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. CẤM nhại lại câu hỏi của công dân. Đi thẳng vào câu trả lời.\n"
        "2. Trả lời rõ ràng, chính xác theo quy định pháp luật Việt Nam hiện hành: phân tích hành vi đó có bị phạt hay không, quyền của công dân và các điều kiện/lưu ý cần tuân thủ.\n"
        "3. TUYỆT ĐỐI KHÔNG liên hệ hoặc nhầm lẫn sang luật giao thông (như mũ bảo hiểm, xe máy...) nếu câu hỏi không hỏi về giao thông đường bộ.\n"
        "4. Lời văn ngắn gọn, khách quan, dễ hiểu."
    )
    user_content = f"THÔNG TIN THAM KHẢO:\n{context}\n\nCÂU HỎI: \"{query}\"" if context else query
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]


# ==============================================================================
# 2. Phân tầng Quyết định (Decision Logic)
# ==============================================================================
def decide_tier(candidates: List[Candidate], query: str) -> Tuple[Tier, float]:
    """Xác định tầng xử lý (A/B/C/D) dựa trên điểm tin cậy và độ chênh lệch top-k."""
    if not candidates:
        return Tier.TIER_C, 0.0

    top = candidates[0]
    conf = top.confidence

    # ĐIỀU KIỆN TIÊN QUYẾT: Độ tương đồng ngữ nghĩa (Dense Semantic Similarity)
    # Các câu hỏi về 70 thủ tục đều có dense_similarity >= 0.40.
    # Nếu dense_similarity < 0.35 hoặc conf < 0.35: câu hỏi nằm ngoài phạm vi 70 thủ tục,
    # Tuyệt đối KHÔNG ép vào Tầng A (CSDL) hay Tầng B (gợi ý sai lệch).
    # Chuyển ngay sang Tầng C để tra cứu Internet qua DuckDuckGo.
    if top.dense_similarity < 0.35 or conf < 0.35:
        return Tier.TIER_C, conf

    # Ngưỡng tin cậy đủ mạnh để vào Tầng A
    if conf >= 0.40 and top.dense_similarity >= 0.38:
        # Chỉ hỏi lại khi top 1 và top 2 có điểm cực kỳ sít sao (< 0.03)
        # VÀ không thuộc cùng nhóm chủ đề
        if len(candidates) > 1:
            second = candidates[1]
            gap = conf - second.confidence
            if gap < 0.03 and top.title != second.title:
                t1 = top.title.lower()
                t2 = second.title.lower()
                marriage = ["kết hôn", "hôn nhân", "độc thân"]
                birth = ["khai sinh", "giấy chứng sinh", "cha mẹ con"]
                id_card = ["căn cước", "cccd", "định danh"]
                passport = ["hộ chiếu", "passport", "xuất cảnh"]
                residence = ["tạm trú", "thường trú", "cư trú", "hộ khẩu"]
                land = ["đất", "sổ đỏ", "sổ hồng", "địa chính", "quy hoạch"]
                topics = [marriage, birth, id_card, passport, residence, land]
                is_same_topic = any(
                    any(w in t1 for w in top_words) and any(w in t2 for w in top_words)
                    for top_words in topics
                )
                if not is_same_topic:
                    return Tier.TIER_B, conf
        return Tier.TIER_A, conf

    return Tier.TIER_B, conf


# ==============================================================================
# 3. Định dạng phản hồi các tầng
# ==============================================================================
def format_tier_a_response(candidate: Any, query: str = "") -> str:
    """
    TẦNG A: Xuất bản ghi chuẩn hóa trực tiếp từ CSDL.
    TUYỆT ĐỐI KHÔNG để LLM tự do bịa đặt thông tin, chống 100% việc nhại prompt hay cắt ngắn câu.
    """
    p = candidate.record if hasattr(candidate, "record") else candidate
    dia_diem = clean_local_references(p.dia_diem) or "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú (hoặc cơ quan có thẩm quyền theo quy định)"
    ho_so = clean_local_references(p.ho_so)

    intro = ""
    if query:
        q_lower = query.lower()
        if any(k in q_lower for k in ["đẻ", "sinh con", "sinh em bé", "khai sinh", "mới sinh"]):
            intro = f"Chào bạn! Chúc mừng gia đình có thêm thành viên mới. Thủ tục bạn cần thực hiện cho cháu là **{p.ten}** ({p.cap_thuc_hien}):\n\n"
        elif any(k in q_lower for k in ["cưới", "lấy vợ", "lấy chồng", "kết hôn", "hôn nhân", "độc thân"]):
            intro = f"Chào bạn! Đối với việc đăng ký kết hôn và xây dựng gia đình, thủ tục bạn cần thực hiện là **{p.ten}** ({p.cap_thuc_hien}):\n\n"
        elif any(k in q_lower for k in ["mất", "chết", "qua đời", "khai tử", "tử tuất"]):
            intro = f"Chào bạn! Với sự việc này, thủ tục gia đình cần thực hiện là **{p.ten}** ({p.cap_thuc_hien}):\n\n"
        elif any(k in q_lower for k in ["cccd", "căn cước", "định danh"]):
            intro = f"Chào bạn! Về thủ tục thẻ Căn cước công dân, thông tin hướng dẫn chuẩn xác như sau:\n\n"
        elif any(k in q_lower for k in ["học bổng", "miễn giảm", "học phí"]):
            intro = f"Chào bạn! Về chế độ chính sách học tập, thủ tục cần nộp hồ sơ là **{p.ten}** ({p.cap_thuc_hien}):\n\n"
        elif is_situational_query(query):
            intro = f"Chào bạn! Đối với tình huống của bạn, thủ tục hành chính cần thực hiện là **{p.ten}** ({p.cap_thuc_hien}):\n\n"

    lines = [
        f"### {p.ten}",
        f"- **Mã thủ tục**: `{p.ma_thu_tuc or 'Đang cập nhật'}`",
        f"- **Lĩnh vực**: {p.linh_vuc or 'Hành chính công'}",
        f"- **Cấp thực hiện**: {p.cap_thuc_hien or 'Cơ quan có thẩm quyền theo quy định'}",
        f"- **Thời gian giải quyết**: **{p.thoi_gian or 'Theo quy định'}**",
        f"- **Lệ phí**: **{p.le_phi or 'Miễn phí'}**",
        f"- **Nơi tiếp nhận hồ sơ**: {dia_diem}",
    ]
    if p.gio_cat_off:
        lines.append(f"- **Quy định tiếp nhận / Giờ cắt hồ sơ**: {p.gio_cat_off}")

    lines.append("\n**Thành phần hồ sơ cần chuẩn bị:**")
    if ho_so:
        # Tách dòng thông minh không bẻ đôi nội dung trong dấu ngoặc đơn
        docs = [d.strip() for d in re.split(r",\s*(?![^()]*\))", ho_so) if d.strip()]
        if len(docs) > 1:
            for doc in docs:
                lines.append(f"  * {doc}")
        else:
            lines.append(f"  * {ho_so}")
    else:
        lines.append("  * Hồ sơ theo mẫu quy định tại cơ quan tiếp nhận.")

    if p.can_cu_phap_ly:
        lines.append(f"\n*Căn cứ pháp lý: {p.can_cu_phap_ly}*")
    if p.nguon_url:
        lines.append(f"\n[Tra cứu chi tiết trên Cổng Dịch vụ công]({p.nguon_url})")

    return intro + "\n".join(lines)


def format_tier_b_response(candidates: Any, query: str = "", other_cands: Optional[List[Any]] = None) -> str:
    """
    TẦNG B: Chủ động hỏi lại người dân để làm rõ nhu cầu giữa các thủ tục tương đồng.
    """
    if isinstance(candidates, list):
        cands_list = candidates
    elif other_cands is not None:
        cands_list = [candidates] + other_cands
    else:
        cands_list = [candidates] if candidates else []
    top_cands = cands_list[:3]
    lines = [
        "Hệ thống nhận thấy yêu cầu của bạn có thể thuộc về các thủ tục hành chính dưới đây. "
        "Vui lòng bấm chọn hoặc nêu rõ thủ tục bạn muốn thực hiện:\n"
    ]
    for idx, c in enumerate(top_cands, 1):
        p = c.record if hasattr(c, "record") else c
        cap = f" ({p.cap_thuc_hien})" if p.cap_thuc_hien else ""
        phi = f" | Phí: {p.le_phi}" if p.le_phi else ""
        lines.append(f"{idx}. **{p.ten}**{cap}{phi}")

    lines.append("\n*Nếu nhu cầu của bạn khác các lựa chọn trên, hãy miêu tả chi tiết hơn nhé.*")
    return "\n".join(lines)


def web_search_gov(query: str, max_results: int = 4) -> Tuple[str, List[Dict[str, str]]]:
    """
    TẦNG C: Tra cứu thông tin từ Internet qua DuckDuckGo.
    Ưu tiên cổng dịch vụ công (.gov.vn), nếu không có thì lấy kết quả từ các nguồn tin tức/pháp luật uy tín.
    """
    results = []
    sources = []
    
    # 1. Ưu tiên tìm kiếm trên các cổng dịch vụ công chính thống
    try:
        ddgs = DDGS(timeout=10)
        hits = list(ddgs.text(f"{query} site:gov.vn", max_results=max_results))
        for h in hits:
            body = h.get("body", "").strip()
            href = h.get("href", "")
            title = h.get("title", "")
            if body:
                results.append(f"- **{title}**: {body}")
                sources.append({"title": title, "url": href})
    except Exception as e:
        print(f"[WebSearch] Lỗi tra cứu gov.vn: {e}")

    # 2. Fallback tìm kiếm mở rộng qua DuckDuckGo nếu chưa có kết quả
    if not results:
        try:
            ddgs = DDGS(timeout=10)
            hits = list(ddgs.text(query, max_results=max_results))
            for h in hits:
                body = h.get("body", "").strip()
                href = h.get("href", "")
                title = h.get("title", "")
                if body:
                    results.append(f"- **{title}**: {body}")
                    sources.append({"title": title, "url": href})
        except Exception as e:
            print(f"[WebSearch] Lỗi tra cứu mở rộng: {e}")

    context_str = "\n".join(results) if results else "Không tìm thấy dữ liệu trực tuyến."
    return context_str, sources


def format_tier_c_prompt(query: str, web_context: str) -> str:
    return (
        "Bạn là Trợ lý Dịch vụ công & Thủ tục Hành chính Việt Nam.\n"
        "Người dùng đang hỏi một câu hỏi (có thể là thủ tục hành chính hoặc vấn đề dân sinh, hóa đơn tiện ích ngoài lề).\n"
        "THÔNG TIN TRA CỨU ĐƯỢC TỪ INTERNET:\n"
        "---------------------\n"
        f"{web_context}\n"
        "---------------------\n\n"
        f"CÂU HỎI CỦA CÔNG DÂN: \"{query}\"\n\n"
        "QUY TẮC TRẢ LỜI BẮT BUỘC:\n"
        "1. Nếu câu hỏi về thủ tục hành chính: Tóm tắt ngắn gọn các bước, hồ sơ và nơi tiếp nhận.\n"
        "2. NẾU CÂU HỎI NGOÀI LỀ (như hóa đơn điện nước, cước viễn thông, sinh hoạt dân sự):\n"
        "   - Hãy trả lời tóm lược sơ bộ các ý chính để giúp người dân nắm được tình hình cơ bản.\n"
        "   - Nhắc nhở khéo léo rằng bạn là Trợ lý chuyên về Thủ tục Hành chính công (UBND), không quản lý các dịch vụ ngoài lề này nên không thể tư vấn chi tiết, và khuyên người dân liên hệ trực tiếp đơn vị cung cấp dịch vụ hoặc cơ quan có thẩm quyền để được hỗ trợ cụ thể.\n"
        "   - TUYỆT ĐỐI KHÔNG ép câu hỏi sang các thủ tục hành chính không liên quan (như hỏa táng, thị thực, khai sinh...).\n"
        "3. Lời văn ngắn gọn, khách quan, súc tích, khiêm tốn."
    )

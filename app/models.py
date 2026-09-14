"""models.py — Định nghĩa đối tượng dữ liệu (Procedure, Candidate, Schemas)."""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from pydantic import BaseModel


@dataclass
class Procedure:
    row_id: int
    ten: str
    linh_vuc: str = ""
    cap_thuc_hien: str = ""
    co_quan: str = ""
    ho_so: str = ""
    thoi_gian: str = ""
    thoi_gian_ngay: Optional[int] = None
    le_phi: str = ""
    le_phi_vnd: Optional[int] = None
    dia_diem: str = ""
    gio_cat_off: str = ""
    ghi_chu: str = ""
    can_cu_phap_ly: str = ""
    nguon_url: str = ""
    ma_thu_tuc: str = ""

    def __post_init__(self):
        if any(w in self.dia_diem.lower() for w in ["tăng nhơn phú", "lê văn việt"]):
            self.dia_diem = "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú (hoặc cơ quan có thẩm quyền theo quy định)"
        if any(w in self.co_quan.lower() for w in ["tăng nhơn phú", "lê văn việt"]):
            self.co_quan = "UBND Cấp Xã/Phường nơi cư trú"

    def view_title(self) -> str:
        parts = [f"Thủ tục: {self.ten}"]
        if self.linh_vuc:
            parts.append(f"Lĩnh vực: {self.linh_vuc}")
        if self.cap_thuc_hien:
            parts.append(f"Cấp thực hiện: {self.cap_thuc_hien}")
        return ". ".join(parts)

    def view_summary(self) -> str:
        parts = [f"Thủ tục: {self.ten}"]
        if self.thoi_gian:
            parts.append(f"Thời gian giải quyết: {self.thoi_gian}")
        if self.le_phi:
            parts.append(f"Lệ phí: {self.le_phi}")
        if self.dia_diem:
            parts.append(f"Địa điểm tiếp nhận: {self.dia_diem}")
        if self.gio_cat_off:
            parts.append(f"Giờ tiếp nhận / Cắt hồ sơ: {self.gio_cat_off}")
        return ". ".join(parts)

    def view_docs(self) -> str:
        if not self.ho_so:
            return f"Thủ tục: {self.ten}. Căn cứ pháp lý: {self.can_cu_phap_ly}"
        return f"Thủ tục: {self.ten}. Thành phần hồ sơ cần chuẩn bị: {self.ho_so}"

    def view_situational(self) -> str:
        name_lower = (self.ten + " " + self.linh_vuc).lower()
        terms = []
        if any(k in name_lower for k in ["kết hôn", "hôn nhân"]):
            terms.append("lấy vợ lấy chồng cưới xin kết hôn hôn thú làm đám cưới rước dâu đăng ký kết hôn lấy nhau hai vợ chồng kết hôn có yếu tố nước ngoài")
        if any(k in name_lower for k in ["khai sinh"]):
            terms.append("sinh con mới sinh đẻ con sinh em bé mới đẻ con mới sinh làm giấy khai sinh đăng ký khai sinh giấy chứng sinh")
        if any(k in name_lower for k in ["khai tử", "tử tuất"]):
            terms.append("người mất người chết người thân qua đời báo tử chứng tử mai táng giấy khai tử")
        if any(k in name_lower for k in ["tình trạng hôn nhân", "độc thân"]):
            terms.append("giấy độc thân xác nhận độc thân chưa có vợ chưa có chồng xin giấy độc thân")
        if any(k in name_lower for k in ["căn cước", "cccd", "định danh"]):
            terms.append("làm căn cước mất cccd làm lại căn cước đổi cccd làm thẻ căn cước cccd gắn chip vneid định danh điện tử")
        if any(k in name_lower for k in ["hộ chiếu", "passport"]):
            terms.append("làm hộ chiếu đổi hộ chiếu gia hạn hộ chiếu đi nước ngoài passport cấp hộ chiếu")
        if any(k in name_lower for k in ["tạm trú", "thường trú", "cư trú"]):
            terms.append("nhập hộ khẩu đăng ký tạm trú làm tạm trú chuyển khẩu ct07 chuyển chỗ ở nhập khẩu")
        if any(k in name_lower for k in ["sổ đỏ", "sổ hồng", "đất đai", "quy hoạch"]):
            terms.append("sang tên sổ đỏ làm sổ hồng mua đất bán nhà cấp sổ đỏ tranh chấp đất trích lục địa chính")
        if any(k in name_lower for k in ["xây dựng", "sửa chữa nhà"]):
            terms.append("xin phép xây nhà giấy phép xây dựng sửa nhà cấp phép xây dựng cơi nới nhà ở")
        if any(k in name_lower for k in ["hộ kinh doanh", "buôn bán", "kinh doanh"]):
            terms.append("mở quán mở tiệm bán hàng đăng ký kinh doanh hộ kinh doanh cá thể mở cửa hàng kinh doanh buôn bán")
        if any(k in name_lower for k in ["chứng thực", "công chứng"]):
            terms.append("sao y bản chính công chứng giấy tờ chứng thực chữ ký giấy ủy quyền công chứng hợp đồng")
        if any(k in name_lower for k in ["mai táng", "hỏa táng"]):
            terms.append("tiền mai táng hỗ trợ hỏa táng trợ cấp mai táng chi phí hỏa táng tang lễ")
        if any(k in name_lower for k in ["bảo hiểm y tế", "hộ nghèo", "trợ cấp", "khuyết tật"]):
            terms.append("làm thẻ bhyt miễn phí trợ cấp bảo trợ xã hội hỗ trợ người nghèo trợ cấp khuyết tật tiền trợ cấp")
        
        kw_str = " ".join(terms) if terms else ""
        return f"Thủ tục: {self.ten}. Tình huống thực tế đời thường của người dân: {kw_str}".strip()

    def views(self) -> List[tuple]:
        return [
            ("title", self.view_title()),
            ("summary", self.view_summary()),
            ("docs", self.view_docs()),
            ("situational", self.view_situational())
        ]

    def lexical_text(self) -> str:
        """Ghép chuỗi tối ưu cho BM25 (lặp lại tên 2 lần + từ ngữ tình huống đời thường)."""
        return " ".join(filter(None, [
            self.ten, self.ten,
            self.view_situational(),
            self.linh_vuc, self.cap_thuc_hien, self.co_quan,
            self.ho_so, self.thoi_gian, self.le_phi, self.dia_diem,
            self.can_cu_phap_ly, self.ma_thu_tuc
        ]))


@dataclass
class Candidate:
    row_id: int
    record: Procedure
    confidence: float = 0.0
    dense_similarity: float = 0.0
    best_view: str = ""
    bm25_norm: float = 0.0
    rerank_score: Optional[float] = None
    fusion_score: float = 0.0
    sources: List[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.record.ten


# --- Pydantic Schemas cho API ---
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = "Công dân"

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: str
    token: Optional[str] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = "Cuộc trò chuyện mới"

class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class ChatMessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tier: Optional[str] = None
    rating: Optional[int] = None
    created_at: str

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: str

class FeedbackRequest(BaseModel):
    rating: int  # 1 (thích), -1 (không thích)

class ResetRequest(BaseModel):
    scope: str = "my_conversations"  # "my_conversations" | "all_conversations" | "everything"
    confirm: str = ""                # phải gõ đúng "XOA"


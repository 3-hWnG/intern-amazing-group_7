"""Cổng ý định NGOÀI PHẠM VI (24/10/2026, phương án A của đợt sửa câu khó).

Đo trên real_v1 (câu thật của người dân, bộ dev): 101/220 câu lẽ ra phải từ chối lại được trả lời, vì câu có tình cờ chữ trùng tên một
thủ tục. Các câu đó thuộc vài NHÓM Ý ĐỊNH rõ ràng (REAL_V1_GUIDE.md mục 5.3): hỏi tình trạng hồ sơ của mình, khiếu nại / phản ánh,
kiến nghị của cử tri, hỏi luật / xử phạt, chế độ nội bộ ngành Công an, hỏi thủ tục KHÔNG có trong dữ liệu (lý lịch tư pháp, chứng chỉ
hành nghề, bằng lái xe dân sự...). Ở đây nhận các nhóm đó bằng cụm chữ (chữ đã bỏ dấu), không gọi LLM.

Thứ tự ưu tiên: câu có YÊU CẦU THỦ TỤC rõ ("cần giấy tờ gì", "thủ tục như thế nào", "làm ở đâu", "bao lâu"...) VÀ đã chọn được
thủ tục thì vẫn trả lời ở các nhóm "luật", "nội bộ", "chính sách" (người hỏi vừa hỏi luật vừa hỏi cách làm: real_v1-298, 053);
nhóm "tình trạng hồ sơ" chỉ nhường khi câu hỏi thời gian giải quyết CHUNG ("bao lâu", "bao nhiêu ngày"), không phải "khi nào tôi nhận";
nhóm "kiến nghị", "khiếu nại", "không có trong dữ liệu" luôn từ chối.
Tắt: S3_SCOPE_GATE=0.
"""
from __future__ import annotations

import os
import re

from system3.data.textutil import fold


def _rx(*parts: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(parts) + r")(?![a-z0-9])")


# ---- yêu cầu thủ tục rõ ràng (người hỏi muốn biết CÁCH LÀM / mục của thủ tục)
ASK_PROC = _rx(r"thu tuc (?:nhu the nao|the nao|ra sao|gi|gom|can|de|ve|cap|lam|dang ky|nhap)", r"lam (?:nhung )?thu tuc gi", r"thu tuc (?:o|tai) dau",
               r"(?:can|phai) (?:chuan bi|lam|nop|mang theo|co) (?:nhung |cac )?(?:giay to|ho so|thu tuc|gi)", r"(?:giay to|ho so) (?:gi|nao|gom|can|nhu the nao|the nao)",
               r"nhung giay to", r"cac giay to", r"lam (?:the nao|sao|nhu the nao|cach nao) (?:de|ma|thi)", r"(?:phai|can|nen) lam (?:the nao|sao|gi|nhu the nao)",
               r"cach (?:lam|thuc hien|dang ky|xin)", r"quy trinh", r"trinh tu", r"(?:nop|lam|dang ky|den|lien he) (?:o|tai) (?:dau|co quan nao|noi nao)",
               r"co quan nao", r"o dau", r"bao lau(?! nua)", r"bao nhieu ngay", r"mat may ngay", r"thoi gian (?:giai quyet|cap|lam(?! viec)|xu ly|tu khi|la bao)",
               r"le phi", r"bao nhieu tien", r"huong dan (?:thu tuc|quy trinh|cach|toi|em|giup|cu the|lam)", r"co (?:the )?(?:dang ky|lam|cap|xin|doi|nhap) .{0,40}(?:duoc )?khong",
               r"(?:dang ky|lam|cap|xin|doi|nhap) .{0,30} duoc khong", r"(?:muon|can|dinh) (?:lam|xin|dang ky|cap|doi|nhap|chuyen|lam lai|cap lai)")
# A6: ngoại lệ "vừa hỏi luật vừa hỏi cách làm" chỉ nhận câu HỎI MỤC của thủ tục; câu chỉ nêu ý muốn ("tôi muốn làm thẻ CCCD ...") hay hỏi được/không
# ("có thể ... được không") không đủ (real_v1-105: "muốn làm thẻ CCCD gắn chíp ..., tới 40 tuổi có phải đổi không?")
_INTENT_ONLY = (r"co (?:the )?(?:dang ky|lam|cap|xin|doi|nhap) .{0,40}(?:duoc )?khong", r"(?:dang ky|lam|cap|xin|doi|nhap) .{0,30} duoc khong",
                r"(?:muon|can|dinh) (?:lam|xin|dang ky|cap|doi|nhap|chuyen|lam lai|cap lai)")
ASK_INFO = re.compile(ASK_PROC.pattern.replace("|" + "|".join(_INTENT_ONLY), ""))
GENERAL_TIME = _rx(r"bao lau(?! nua)", r"bao nhieu ngay", r"mat may ngay", r"thoi gian (?:giai quyet|cap|lam(?! viec)|xu ly|tu khi|la bao|bao lau)", r"trong bao lau(?! nua)")
OWN_WHEN = _rx(r"(?:khi nao|bao gio|den bao gio|luc nao|ngay nao) (?:thi )?(?:toi|em|minh|chau|con)? ?(?:se )?(?:nhan|co|lay|duoc nhan|duoc cap|duoc tra)",
               r"(?:da|duoc) (?:giai quyet|xu ly|tra|gui) chua", r"co ket qua chua", r"da co chua", r"(?:the|giay|so|ho so) (?:da )?co chua",
               r"kiem tra giup", r"xem giup", r"tra cuu giup", r"(?:co )?van de gi", r"(?:hop le|dat) (?:hay )?khong")

# ---- các nhóm ý định ngoài phạm vi
PAST_SUBMIT = _rx(r"(?:da|vua|co) (?:di |den )?(?:nop|lam|dang ky|gui|xin|lam ho so|nop ho so|lam thu tuc|dang ki)", r"da duoc (?:tiep nhan|hen)")
# hồ sơ CỦA MÌNH đã nộp: mã / số hồ sơ, giấy hẹn, trạng thái -> hỏi tình trạng hồ sơ (không cần thêm dấu hiệu "chưa nhận")
OWN_FILE = _rx(r"(?:ma|so) ho so", r"\d{3} \d{2} \d{2} h\w*", r"giay hen", r"hen (?:tra|lay|ngay|lich)", r"(?:ngay|lich) hen", r"(?:trang thai|tinh trang) (?:ho so|xu ly)")
NOT_YET = _rx(r"(?:van |ma |nhung )?chua (?:nhan|co ket qua|thay|duoc|cap nhat|giai quyet|tra|tiep nhan|xu ly|lay)",
              r"(?:van|ma|nhung|den nay|toi nay|hien van) chua co", r"qua han", r"tre han", r"tre hen", r"khong thay (?:cap nhat|ket qua|tin nhan|thong tin)", r"bao lau nua", r"bao gio moi")
COMPLAINT = _rx(r"khieu nai", r"to cao", r"phan anh", r"buc xuc", r"lua dao", r"chiem doat", r"chu dau tu", r"dun day", r"gay kho khan", r"nhung nhieu",
                r"khong (?:ai )?(?:chiu )?giai quyet", r"tu choi giai quyet", r"tra (?:lai )?ho so", r"de nghi (?:cac cap|cac co quan|co quan|so|ubnd|uy ban|xem xet|giai quyet|kiem tra|thanh tra|vao cuoc)",
                r"kinh (?:mong|de nghi) .{0,40}(?:xem xet|giai quyet|can thiep|ho tro giai quyet)", r"(?:can thiep|thanh kiem tra) .{0,20}(?:giup|de bao ve)")
PETITION = _rx(r"cu tri", r"kien nghi", r"chat van", r"de nghi (?:bo|chinh phu|nha nuoc|quoc hoi|bo truong|cac bo|nganh chuc nang)", r"de nghi .{0,30}(?:nghien cuu|xem xet sua doi|ban hanh)")
LEGAL = _rx(r"xu phat", r"bi phat", r"muc phat", r"phat tien", r"bi xu ly", r"xu ly (?:the nao|nhu the nao|ra sao)", r"vi pham", r"truy cuu", r"hinh su", r"toi pham",
            r"an tich", r"che tai", r"co dung (?:quy dinh|luat|khong)", r"(?:huong dan|tra loi) (?:nhu vay|nhu tren|vay) (?:co )?dung", r"(?:quy dinh|can cu) (?:o|tai|trong) van ban nao",
            r"theo quy dinh (?:hien hanh|cua phap luat)", r"phap luat (?:quy dinh|co quy dinh)", r"luat .{0,30}quy dinh (?:nhu the nao|ra sao|gi)", r"co bi (?:thu hoi|tich thu|phat|xu ly)",
            r"bat buoc .{0,30}khong", r"con gia tri", r"du thao", r"(?:nghi dinh|thong tu|quyet dinh|phap lenh) (?:so )?\d+ \d{4}", r"(?:nghi dinh|thong tu|quyet dinh|phap lenh) so \d", r"con (?:su dung|dung) (?:duoc|tiep)", r"khoi kien", r"(?:luat|nghi dinh|thong tu) .{0,25}(?:co lien quan|anh huong)")
_STAFF = r"(?:can bo|chien si|si quan|ha si quan|cong nhan cong an|nhan vien hop dong|(?:vao|trong|cua|thuoc|ra khoi) (?:nganh|luc luong) cong an|cong an nhan dan|cand|cong an (?:xa|vien))"
_PERK = r"(?:che do|phu cap|luong|nghi huu|huu tri|tham nien|phong ham|nang ham|nang luong|xuat ngu|bao hiem|tro cap|chinh sach|thang cap|bien che|tuyen dung|nghi phep|tam tuyen)"
INTERNAL = _rx(_STAFF + r".{0,120}" + _PERK, _PERK + r".{0,80}" + _STAFF,
               r"(?:tuyen sinh|so tuyen|xet tuyen|du tuyen|thi tuyen|van bang 2|chi tieu) .{0,60}(?:truong|hoc vien|dai hoc|cand|cong an|canh sat|an ninh)",
               r"thi vao (?:truong|hoc vien|nganh|khoi) .{0,25}(?:cong an|canh sat|an ninh|quan doi|cand)")
RECRUIT = _rx(r"(?:tuyen sinh|so tuyen|xet tuyen|du tuyen|thi tuyen|tuyen chon|tuyen dung|tam tuyen|thi vao|tuyen vao) .{0,60}(?:cong an|cand|canh sat|an ninh|quan doi|si quan)")
NOT_IN_DB = _rx(r"ly lich tu phap", r"lltp", r"phieu ly lich", r"chung chi hanh nghe", r"cchn", r"giay phep hanh nghe",
                r"(?:doi|cap lai|cap|lam) ho chieu", r"ho chieu (?:gan chip|pho thong co|bi in sai|in sai)", r"tham duyet",
                r"khuyen mai", r"visa", r"(?:duoc (?:phep )?|co the |dang ky |dieu kien )(?:du )?thi (?:tot nghiep|dai hoc)", r"xet tuyen dai hoc", r"tuyen sinh dai hoc",
                r"diem thi", r"diem chuan", r"thi thuc", r"the tam tru", r"gia han tam tru cho nguoi nuoc ngoai", r"(?:bao hiem|tro cap) that nghiep",
                r"dang ky doanh nghiep", r"thanh lap (?:cong ty|doanh nghiep)", r"(?:nhap|thoi|tro lai|mang|hai) quoc tich", r"gpp", r"dac xa")
# bằng lái xe DÂN SỰ không có trong dữ liệu (chỉ có đổi bằng quân sự / Công an và bằng của người nước ngoài: 1.115979, 3.000351)
DRIVING = _rx(r"giay phep lai xe", r"bang lai", r"gplx", r"the pet")
# 25/10 (golden h5-047, h6-023, pr2-16): "đổi bằng lái xe NƯỚC NGOÀI", "bằng của công an / quân đội" -> có thủ tục (3.000351, 1.115979)
DRIVING_OK = _rx(r"quan su", r"nuoc ngoai", r"quan doi", r"bo quoc phong", r"(?:cua|do|nganh) cong an")
# phòng cháy chữa cháy: dữ liệu chỉ có CHẾ ĐỘ cho người được huy động / tham gia chữa cháy; thẩm duyệt, nghiệm thu, quy chuẩn... không có
FIRE = _rx(r"phong chay", r"chua chay", r"pccc", r"vu chay", r"chay no", r"thoat nan")
FIRE_OK = _rx(r"(?:che do|chinh sach) .{0,60}(?:huy dong|tham gia)", r"(?:huy dong|tham gia) .{0,60}(?:che do|chinh sach)")
INFO = _rx(r"loi ich", r"phuong an", r"giai phap", r"uu viet", r"uu diem", r"nhuoc diem", r"so sanh", r"(?:bao gio|khi nao|thoi gian nao) .{0,25}(?:trien khai|ap dung|chinh thuc|bat dau cap)", r"da trien khai chua", r"(?:chua|van chua) trien khai", r"trien khai .{0,60}(?:khi nao|bao gio)",
           r"chu truong", r"(?:co|da) (?:trien khai|ho tro) .{0,40} chua", r"(?:tai sao|vi sao) .{0,60}(?:khong|chua)")
# "có phải đổi / làm ... không": trong THƯ DÀI là hỏi quy định (real_v1-105: tới 40 tuổi có phải đổi thẻ không); câu ngắn gọi tên thủ tục
# ("khai báo tạm vắng ... có phải làm không", golden h4-019) là hỏi điều kiện của thủ tục -> trả lời
INFO_LONG = _rx(r"co phai (?:doi|lam|nop|thay) .{0,30}khong")
LONG_WORDS = 25
# hỏi CÁCH LÀM / THỜI HẠN của thủ tục giải quyết khiếu nại, tố cáo (có trong dữ liệu: 1.004327 ...), khác với tự khiếu nại (golden h6-042)
COMPLAINT_PROC = _rx(r"(?:thu tuc|quy trinh|trinh tu|giai quyet|cach|lam don|mau don|nop don|ho so|thoi han) (?:\w+ ){0,2}(?:khieu nai|to cao)")
PASSPORT_LOST = _rx(r"(?:mat|bi mat|that lac|trinh bao) .{0,15}ho chieu", r"ho chieu .{0,15}(?:bi mat|that lac)")

APOLOGY_TEXT = {
    "status": "Mình không tra được tình trạng hồ sơ cụ thể của bạn. Bạn hỏi trực tiếp nơi đã nộp hồ sơ, hoặc tra cứu bằng mã hồ sơ trên Cổng Dịch vụ công.",
    "complaint": "Đây là nội dung khiếu nại / phản ánh, mình không giải quyết được. Bạn gửi tới cơ quan có thẩm quyền (nơi giải quyết hồ sơ hoặc cơ quan cấp trên) để được xem xét.",
    "petition": "Đây là kiến nghị về chính sách, không phải câu hỏi thủ tục hành chính, nên mình không trả lời được.",
    "legal": "Câu hỏi về quy định pháp luật / xử phạt nằm ngoài phạm vi của mình: mình chỉ hướng dẫn thủ tục hành chính cấp xã/phường theo dữ liệu Cổng Dịch vụ công.",
    "internal": "Câu hỏi về chế độ, chính sách nội bộ ngành hoặc tuyển sinh không thuộc thủ tục hành chính cấp xã/phường mà mình hỗ trợ.",
    "not_in_db": "Thủ tục bạn hỏi không có trong dữ liệu thủ tục cấp xã/phường của mình (ví dụ lý lịch tư pháp, chứng chỉ hành nghề, giấy phép lái xe, hộ chiếu, phòng cháy chữa cháy), nên mình không trả lời để tránh nói sai.",
    "info": "Câu hỏi này là thông tin chính sách / triển khai chung, không phải hướng dẫn một thủ tục cụ thể, nên mình không trả lời được.",
}


# phương án C (server/planner/reader.py): ý định model đọc được -> lý do từ chối
READER_REASON = {"tinh_trang": "status", "khieu_nai": "complaint", "luat": "legal", "noi_bo": "internal", "khac": "off_topic"}


A6 = os.environ.get("S3_SCOPE_A6", "1") == "1"      # vòng sửa thứ 6 (mẫu ở trên vẫn mở rộng; cờ này chỉ tắt các QUY TẮC mới: tuyển vào ngành, ngoại lệ hỏi mục, mã hồ sơ)


def enabled() -> bool:
    return os.environ.get("S3_SCOPE_GATE", "1") == "1"


def intents(text: str) -> list[str]:
    """Các nhóm ý định ngoài phạm vi có trong câu (chữ bỏ dấu), theo thứ tự ưu tiên."""
    f = " " + " ".join(re.findall(r"[a-z0-9]+", fold(text or ""))) + " "
    out = []
    if PETITION.search(f):
        out.append("petition")
    if ((NOT_IN_DB.search(f) and not PASSPORT_LOST.search(f)) or (DRIVING.search(f) and not DRIVING_OK.search(f))
            or (FIRE.search(f) and not FIRE_OK.search(f))):
        out.append("not_in_db")
    if COMPLAINT.search(f) and not (COMPLAINT_PROC.search(f) and ASK_INFO.search(f)):
        out.append("complaint")
    if OWN_FILE.search(f) or (PAST_SUBMIT.search(f) and NOT_YET.search(f)):
        out.append("status")
    if RECRUIT.search(f):
        out.append("recruit")
    if INTERNAL.search(f):
        out.append("internal")
    if LEGAL.search(f):
        out.append("legal")
    if INFO.search(f) or (INFO_LONG.search(f) and len(f.split()) >= LONG_WORDS):
        out.append("info")
    return out


def asks_procedure(text: str) -> bool:
    f = " " + " ".join(re.findall(r"[a-z0-9]+", fold(text or ""))) + " "
    return bool(ASK_PROC.search(f))


def verdict(text: str, chosen: bool) -> str | None:
    """-> nhóm lý do từ chối, hoặc None (giữ quyết định của luật cũ). `chosen` = đã chọn được thủ tục để trả lời."""
    if not enabled():
        return None
    ks = intents(text)
    if not ks:
        return None
    f = " " + " ".join(re.findall(r"[a-z0-9]+", fold(text or ""))) + " "
    ask = bool((ASK_INFO if A6 else ASK_PROC).search(f))
    own = bool(OWN_FILE.search(f))
    for k in ks:
        if k in ("petition", "not_in_db", "complaint"):
            return k
        if k == "recruit":
            if A6:
                return "internal"
            continue
        if k == "status":
            if chosen and GENERAL_TIME.search(f) and not OWN_WHEN.search(f) and not (A6 and own):
                continue          # "đã làm 40 ngày chưa có, thời gian cấp là bao nhiêu ngày?": hỏi thời gian chung -> trả lời
            return k
        if k in ("legal", "internal", "info") and not (chosen and ask):
            return k
    return None

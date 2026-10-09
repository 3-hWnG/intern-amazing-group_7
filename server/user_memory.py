"""Phase 26: bộ nhớ người dùng (hồ sơ nhẹ + nhớ lựa chọn MCQ theo trục `subject`). Chuyển theo tinh thần hệ cũ V10.6
(`memory.js`, /api/profile, /api/mcq-memory). Lưu theo `client_id` của thiết bị (bảng user_memory), CHƯA có tài khoản.

Cách dùng: policy.check(memory=for_policy(...)) dùng `subject` để ƯU TIÊN/lọc ứng viên khi sắp hỏi lại; không bao giờ loại thủ tục
khi câu hỏi đã nêu rõ tên. Không có hồ sơ -> for_policy trả None -> hành vi y hệt trước Phase 26."""
from __future__ import annotations

import re
from functools import lru_cache

from db import store
from policy import mask_pii
from system3.data import api as data_api

# FINAL-PRODUCT: [B4][MEM] bộ nhớ khoá theo client_id do trình duyệt tự khai (X-Client-Id): ai biết/đoán được id là đọc, sửa, xoá được hồ sơ của người khác. Bản cuối: khoá theo tài khoản đăng nhập (mục 6)
DEFAULT_CLIENT = "default"
_CID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

AXES = ("subject",)                                   # trục nhớ MCQ; bỏ trục 'cấp thực hiện' (System 3 chỉ có cấp xã)
USER_TYPES = {"citizen": "Người dân", "business": "Hộ kinh doanh / doanh nghiệp", "other": "Khác"}
# Loại người dùng -> tên đối tượng THẬT trong procedure_subjects (kiểm với DB lúc dùng; tên không có trong DB bị bỏ).
# 'other' không ánh xạ: không đoán đối tượng. Hộ kinh doanh không có tên riêng trong dữ liệu -> dùng nhóm 'Doanh nghiệp'.
TYPE_SUBJECTS = {"citizen": ("Công dân Việt Nam",), "business": ("Doanh nghiệp", "Doanh nghiệp Việt Nam")}
_EQUIV = [frozenset({"Doanh nghiệp", "Doanh nghiệp Việt Nam"})]   # hai tên cổng dùng lẫn cho cùng đối tượng
LIMITS = {"province": 60, "commune": 80, "note": 200}
_LABELS = {"province": "Tỉnh/thành", "commune": "Xã/phường", "note": "Ghi chú"}

# Nguồn: danh mục 63 đơn vị hành chính cấp tỉnh trước 01/07/2025 (cùng danh sách hệ cũ V10.6 memory.js). Server KHÔNG kiểm chặt (chỉ UI gợi ý) vì sau sáp nhập còn 34.
# FINAL-PRODUCT: [MEM] đổi sang danh mục 34 tỉnh/thành mới (và xã/phường) khi nhóm chốt; hiện chỉ để hiển thị, không dùng để lọc
PROVINCES = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu", "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương",
    "Bình Phước", "Bình Thuận", "Cà Mau", "Cần Thơ", "Cao Bằng", "Đà Nẵng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai",
    "Đồng Tháp", "Gia Lai", "Hà Giang", "Hà Nam", "Hà Nội", "Hà Tĩnh", "Hải Dương", "Hải Phòng", "Hậu Giang", "Hòa Bình",
    "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định",
    "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh",
    "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa", "Thừa Thiên Huế", "Tiền Giang",
    "TP. Hồ Chí Minh", "Trà Vinh", "Tuyên Quang", "Vĩnh Long", "Vĩnh Phúc", "Yên Bái"]
assert len(PROVINCES) == 63


def client_id(raw: str | None) -> str:
    """Header X-Client-Id -> id hợp lệ; thiếu -> 'default'; sai định dạng -> ValueError (API trả 400)."""
    if raw is None or not raw.strip():
        return DEFAULT_CLIENT
    if not _CID.match(raw.strip()):
        raise ValueError("X-Client-Id chỉ gồm chữ, số, '-', '_' (tối đa 64 ký tự)")
    return raw.strip()


@lru_cache(maxsize=1)
def subject_catalog() -> tuple[tuple[str, int], ...]:
    """Danh mục đối tượng hợp lệ [(tên, số thủ tục)] đọc từ procedure_subjects (dữ liệu tĩnh, đọc một lần)."""
    return tuple((r["name"], r["n"]) for r in data_api.subject_names(data_api.connect()))


def subject_names() -> set[str]:
    return {n for n, _ in subject_catalog()}


def _clean_text(key: str, v) -> str:
    v = re.sub(r"\s+", " ", str(v or "")).strip()
    if len(v) > LIMITS[key]:
        raise ValueError(f"{_LABELS[key]} quá dài (tối đa {LIMITS[key]} ký tự)")
    if mask_pii(v) != v:      # CCCD/CMND/SĐT: từ chối, không lưu
        raise ValueError(f"{_LABELS[key]} không được chứa số CCCD/CMND hoặc số điện thoại")
    return v


def set_profile(cid: str, fields: dict) -> None:
    """fields chỉ gồm khoá có trong yêu cầu; chuỗi rỗng = xoá mục đó. Lỗi giá trị -> ValueError (không ghi gì)."""
    out = {}
    for k, v in fields.items():
        if k == "user_type":
            v = (v or "").strip()
            if v and v not in USER_TYPES:
                raise ValueError("user_type phải là citizen, business hoặc other")
            out[k] = v
        elif k in LIMITS:
            out[k] = _clean_text(k, v)
        else:
            raise ValueError(f"trường lạ: {k}")
    for k, v in out.items():
        if v:
            store.mem_set(cid, "profile." + k, v)
        else:
            store.mem_del(cid, "profile." + k)


def set_mcq(cid: str, axis: str, value: str) -> None:
    if axis not in AXES:
        raise ValueError(f"trục lạ: {axis!r} (chỉ có: {', '.join(AXES)})")
    value = (value or "").strip()
    if value not in subject_names():     # kiểm phía server theo procedure_subjects
        raise ValueError("giá trị không có trong danh mục đối tượng")
    store.mem_set(cid, "mcq." + axis, value)


def del_mcq(cid: str, axis: str) -> None:
    if axis not in AXES:
        raise ValueError(f"trục lạ: {axis!r}")
    store.mem_del(cid, "mcq." + axis)


def effective_subjects(prof: dict, mcq: dict) -> tuple[set[str], str]:
    """Đối tượng dùng để ưu tiên: lựa chọn MCQ đã nhớ (nếu có) thắng ánh xạ từ loại người dùng. -> (tập tên, 'mcq'|'user_type'|'')."""
    names = subject_names()
    v = mcq.get("subject")
    if v and v in names:
        grp = next((g for g in _EQUIV if v in g), {v})
        return {x for x in grp if x in names}, "mcq"
    ss = {s for s in TYPE_SUBJECTS.get(prof.get("user_type", ""), ()) if s in names}
    return ss, ("user_type" if ss else "")


def snapshot(cid: str) -> dict:
    raw = store.mem_all(cid)
    prof = {k: raw.get("profile." + k, "") for k in ("province", "commune", "user_type", "note")}
    mcq = {a: raw["mcq." + a] for a in AXES if "mcq." + a in raw}
    subs, src = effective_subjects(prof, mcq)
    return {"client_id": cid, "profile": prof, "mcq": mcq,
            "effective": {"subjects": sorted(subs), "source": src},
            "catalog": {"subjects": [{"name": n, "n": c} for n, c in subject_catalog()],
                        "user_types": USER_TYPES, "axes": list(AXES), "provinces": PROVINCES,
                        "user_type_subjects": {t: [s for s in ss if s in subject_names()] for t, ss in TYPE_SUBJECTS.items()}}}


def policy_memory(prof: dict, mcq: dict) -> dict | None:
    """Dữ liệu cho policy.check(memory=...) từ hồ sơ + MCQ đã nhớ. None = không có gì để ưu tiên (hành vi như cũ)."""
    subs, src = effective_subjects(prof, mcq)
    if not subs:
        return None
    return {"subjects": subs, "label": mcq.get("subject") or USER_TYPES[prof["user_type"]], "source": src}


def for_policy(cid: str) -> dict | None:
    s = snapshot(cid)
    return policy_memory(s["profile"], s["mcq"])


def suggest_after_pick(pid: str, option_pids: list[str], current: dict | None) -> dict | None:
    """Sau khi người dùng bấm một nút thẻ hỏi lại: đối tượng ĐẶC TRƯNG của thủ tục chọn = đối tượng của nó mà các lựa chọn còn lại
    không có (đúng 1 cái); không có thì lấy nếu thủ tục chỉ khai đúng 1 đối tượng. Người dùng bấm mới lưu (UI), không tự lưu."""
    subs = data_api.subjects_of(data_api.connect(), list(dict.fromkeys([pid, *option_pids])))
    mine, others = subs.get(pid, set()), set().union(*[subs[p] for p in subs if p != pid]) if len(subs) > 1 else set()
    uniq = mine - others
    val = next(iter(uniq)) if len(uniq) == 1 else (next(iter(mine)) if len(mine) == 1 else None)
    if not val or (current and val in current["subjects"]):
        return None
    return {"axis": "subject", "value": val}

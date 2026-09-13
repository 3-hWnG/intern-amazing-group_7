"""Câu mẫu (anchors) của từng luồng cho Semantic Router.

Thêm/bớt câu ở đây là đủ để chỉnh độ nhạy của router - không cần đụng vào code.
"""

LUAT_ANCHORS = [
    "đăng ký kết hôn", "thủ tục ly hôn", "làm giấy khai sinh", "đăng ký khai tử",
    "xác nhận độc thân", "xác nhận tình trạng hôn nhân", "trích lục khai sinh",
    "nhận cha mẹ con", "thay đổi họ tên", "cải chính hộ tịch",
    "mất căn cước công dân", "làm lại cccd", "đổi thẻ căn cước", "căn cước gắn chip",
    "đăng ký tạm trú", "đăng ký thường trú", "giấy xác nhận cư trú ct07", "hộ khẩu",
    "làm hộ chiếu", "passport", "tài khoản vneid", "định danh điện tử",
    "sang tên sổ đỏ", "làm sổ hồng", "cấp giấy phép xây dựng", "sửa chữa nhà",
    "trích lục địa chính", "đo đạc đất đai", "chuyển mục đích sử dụng đất",
    "xác nhận tình trạng quy hoạch", "tranh chấp đất đai",
    "công chứng giấy tờ", "chứng thực bản sao", "sao y bản chính",
    "chứng thực chữ ký", "chứng thực hợp đồng ủy quyền", "giấy ủy quyền",
    "trợ cấp mai táng", "tiền hỗ trợ hỏa táng", "chế độ liệt sĩ", "thương binh",
    "hỗ trợ hộ nghèo", "trợ cấp bảo trợ xã hội", "làm thẻ bảo hiểm y tế miễn phí",
    "đăng ký hộ kinh doanh", "mở cửa hàng buôn bán", "tạm ngừng kinh doanh",
    "thủ tục hành chính", "hồ sơ cần giấy tờ gì", "thời gian giải quyết bao lâu",
    "lệ phí bao nhiêu tiền", "nộp hồ sơ một cửa", "cổng dịch vụ công trực tuyến",
]

XAGIAO_ANCHORS = [
    "xin chào", "chào bạn", "hello", "helo", "hế lô", "hê lô", "hi", "alo",
    "chào buổi sáng", "bạn là ai", "bạn tên gì", "cảm ơn bạn", "tạm biệt",
    "chúc bạn một ngày tốt lành", "tư vấn giúp tôi với",
]

NGOAI_ANCHORS = [
    "vượt đèn đỏ phạt bao nhiêu tiền", "lỗi không đội mũ bảo hiểm",
    "uống rượu lái xe phạt bao nhiêu", "nồng độ cồn xe máy", "bị bắn tốc độ",
    "giá vàng hôm nay", "thời tiết", "chứng khoán", "tin tức thời sự", "bão lũ",
]

INTENT_ANCHORS = {
    "LUAT": LUAT_ANCHORS,
    "NGOAI": NGOAI_ANCHORS,
    "XAGIAO": XAGIAO_ANCHORS,
}

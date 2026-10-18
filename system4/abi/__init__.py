"""Lĩnh vực cứng "ABI": hỏi đáp thông tin web abi.com.vn (Trung tâm Ươm tạo Doanh nghiệp Nông nghiệp Công nghệ cao TP.HCM).

Kế hoạch: docs/PLAN_ABI_LINH_VUC.md; cách dùng, quy ước của chủ web, số đo: docs/SYSTEM4_ABI.md. Tóm tắt luồng:
  client.py    : lớp mạng duy nhất — endpoint chính thức, khoá API (Authorization: Bearer), User-Agent định danh, ≤ 2 request/giây;
                 chặn cứng /rag (không bao giờ gọi trợ lý AI của web: tốn token của chủ web)
  sync.py      : đồng bộ một nguồn (abi.com.vn = "prod" / staging.abi.com.vn = "staging") -> phiên bản mới nếu dữ liệu đổi
  normalize.py : bản API gốc -> data.json gọn, link về đúng nguồn
  store.py     : runtime/abi/versions/<id>/{raw,data}.json + versions.json (phiên bản đang dùng)
  versions.py  : dùng / xoá phiên bản; mỗi nguồn giữ 2 phiên bản mới nhất, cũ hơn tự xoá
  index.py     : mỗi phiên bản một bộ dữ liệu tìm kiếm (dùng lại vector đoạn không đổi); chỉ bộ của bản đang dùng được bật
  router.py    : nhận ý định bằng code (sự kiện, tổ chức, liên hệ, chương trình, đối tác…)
  tools.py     : code tính trên data.json (đếm, liệt kê, "sắp diễn ra" theo giờ VN lúc hỏi)
  turn.py      : chat.py gọi vào đây khi domain có engine = "abi"
  scheduler.py : lịch tự đồng bộ bản thật + API Quản trị (/s4/abi/...)
"""

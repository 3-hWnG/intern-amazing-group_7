"""Lĩnh vực cứng "ABI": hỏi đáp thông tin web abi.com.vn (Trung tâm Ươm tạo Doanh nghiệp Nông nghiệp Công nghệ cao TP.HCM).

Kế hoạch và các sự thật đã kiểm: docs/PLAN_ABI_LINH_VUC.md. Tóm tắt luồng:
  sync.py      : kéo dữ liệu từ các API công khai (GET) của web -> runtime/abi/raw.json -> normalize.py -> runtime/abi/data.json
  index.py     : data.json -> bộ dữ liệu dùng chung của domain ABI (bản ghi + vector) để search.py của System 4 tìm câu tự do
  router.py    : nhận ý định bằng code (sự kiện, tổ chức, liên hệ, chương trình, đối tác…)
  tools.py     : code tính trên data.json (đếm, liệt kê, "sắp diễn ra" theo giờ VN lúc hỏi) -> câu trả lời bằng code hoặc thẻ dữ kiện cho AI
  remote.py    : trợ lý RAG của chủ web (POST /rag/query) — chỉ dự phòng, có giới hạn tần suất
  chat.py      : chat.run của System 4 gọi vào đây khi domain có engine = "abi"
"""

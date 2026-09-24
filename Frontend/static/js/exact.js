/* Nút 🎯 TÌM CHÍNH XÁC — cửa DUY NHẤT để Hệ thống 2 tra CSDL thủ tục
   (Proposal slide 3). Tin nhắn thường = trò chuyện với LLM 2; muốn tra thủ tục
   thì bấm nút này, hoặc bấm chip gợi ý hiện dưới câu trả lời.

     bấm 🎯  -> "lên nòng" (nút sáng): tin nhắn KẾ TIẾP gửi ở mode "exact"
     bấm lại -> tháo nòng

   KHÔNG tự gửi, kể cả khi ô nhập đang có chữ. Bản đầu gửi ngay chữ đang có
   trong ô, nên "Chào" còn sót lại bị đem đi tra và ra MCQ vô nghĩa — người
   dùng phải được gõ câu hỏi thủ tục rồi mới bấm Gửi.

   Chỉ hiện ở Hệ thống 2. Luật "mỗi ô chat chỉ tra thành công một lần" do máy
   chủ giữ (trả về hộp thoại "mở ô chat mới / huỷ"), giao diện không tự đoán. */
window.Exact = (function () {
  let armed = false;
  let basePlaceholder = null;

  const btn = () => document.getElementById("exact-btn");
  const input = () => document.getElementById("input");

  function render() {
    const b = btn();
    if (!b) return;
    const show = !window.Systems || Systems.isRetrieval;
    b.hidden = !show;
    if (!show) armed = false;
    b.classList.toggle("armed", armed);
    b.setAttribute("aria-pressed", String(armed));
    b.title = "Tra thủ tục trong cơ sở dữ liệu: giấy tờ, lệ phí, thời gian, nơi nộp.\n" +
      "Mỗi cuộc trò chuyện tra được một thủ tục.";
    const i = input();
    if (i) {
      if (basePlaceholder === null) basePlaceholder = i.placeholder;
      i.placeholder = armed ? "Nhập thủ tục cần tra chính xác rồi bấm Gửi…" : basePlaceholder;
    }
  }

  /* app.js gọi lúc gửi: trả mode cho lượt này rồi tháo nòng. */
  function take() {
    const mode = armed ? "exact" : "";
    armed = false;
    render();
    return mode;
  }

  function onClick() {
    armed = !armed;
    render();
    const i = input();
    if (i) i.focus();
  }

  function init() {
    const b = btn();
    if (b) b.onclick = onClick;
    render();
  }

  return { init, render, take, get armed() { return armed; } };
})();

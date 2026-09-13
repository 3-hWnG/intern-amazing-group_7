/* Nút reset cho phát triển. Chỉ hoạt động khi server bật DEV_TOOLS_ENABLED. */
window.Dev = (function () {
  async function init(enabled) {
    const boxEl = document.getElementById("dev-box");
    if (!boxEl || !enabled) return;
    boxEl.hidden = false;
    await stats();

    document.getElementById("dev-reset").onclick = async () => {
      const scope = prompt(
        "Phạm vi xoá:\n" +
        "  1 = hội thoại của tôi\n" +
        "  2 = TẤT CẢ hội thoại (mọi người dùng)\n" +
        "  3 = TẤT CẢ, kể cả tài khoản\n\nNhập 1, 2 hoặc 3:", "1");
      if (!scope) return;
      const map = { 1: "my_conversations", 2: "all_conversations", 3: "everything" };
      if (!map[scope]) return alert("Lựa chọn không hợp lệ.");

      const confirmWord = prompt('Gõ đúng chữ  XOA  để xác nhận:');
      if (confirmWord !== "XOA") return alert("Đã huỷ.");

      try {
        const res = await API.post("/api/dev/reset", { scope: map[scope], confirm: "XOA" });
        alert("Đã xoá. " + (res.note || ""));
        location.reload();
      } catch (err) {
        alert("Lỗi: " + err.message);
      }
    };
  }

  async function stats() {
    try {
      const s = await API.get("/api/dev/stats");
      const el = document.getElementById("dev-stats");
      if (el) el.textContent =
        `${s.users} tài khoản · ${s.conversations} hội thoại · ${s.messages} tin nhắn`;
    } catch (_) { /* im lặng */ }
  }

  return { init, stats };
})();

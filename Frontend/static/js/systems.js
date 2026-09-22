/* Nút chuyển giữa HAI hệ thống trả lời (Proposal: "switch bằng nút websearch").

     BẬT  🌐 Web search   -> Hệ thống 1: tra web .gov.vn qua MCP
     TẮT  🗄 CSDL thủ tục -> Hệ thống 2: cơ sở dữ liệu thủ tục nội bộ

   Quy tắc quan trọng: ĐỔI HỆ THỐNG = MỞ CUỘC TRÒ CHUYỆN MỚI (giống Gemini).
   Hai hệ thống lấy thông tin từ hai nguồn khác nhau; để chung một ô chat thì mô
   hình trộn dữ liệu của cả hai và trả lời lẫn lộn. Máy chủ cũng chặn việc đổi
   hệ thống giữa chừng (HTTP 409), đây là phía giao diện của cùng một luật. */
window.Systems = (function () {
  const WEBSEARCH = "websearch";
  const RETRIEVAL = "retrieval";

  const FALLBACK = [
    { id: WEBSEARCH, label: "Web search", description: "Tra cứu từ các trang .gov.vn qua MCP", enabled: true },
    { id: RETRIEVAL, label: "CSDL thủ tục", description: "Tra cứu từ cơ sở dữ liệu nội bộ", enabled: false },
  ];
  const ICON = { [WEBSEARCH]: "🌐", [RETRIEVAL]: "🗄" };

  let list = FALLBACK;
  let current = WEBSEARCH;

  const btn = () => document.getElementById("system-toggle");
  const norm = (id) => (list.some((s) => s.id === id) ? id : WEBSEARCH);
  const info = (id) => list.find((s) => s.id === norm(id)) || FALLBACK[0];

  function label(id) {
    const s = info(id);
    return `${ICON[s.id] || ""} ${s.label}`.trim();
  }

  function render() {
    const b = btn();
    if (!b) return;
    const active = info(current);
    const other = info(current === WEBSEARCH ? RETRIEVAL : WEBSEARCH);
    b.textContent = label(active.id);
    b.setAttribute("aria-pressed", String(current === WEBSEARCH));
    b.classList.toggle("on", current === WEBSEARCH);
    b.title =
      `Đang dùng: ${active.label} — ${active.description}` +
      (active.enabled ? "" : " (đang xây dựng)") +
      `\nBấm để chuyển sang: ${other.label}` +
      "\nĐổi hệ thống sẽ mở một cuộc trò chuyện mới.";
  }

  /* Hiển thị đúng hệ thống của cuộc trò chuyện đang mở. */
  function reflect(system) {
    current = norm(system);
    render();
  }

  /* Câu hỏi gần nhất của người dùng — mang sang ô chat mới để họ khỏi gõ lại. */
  function lastQuestion() {
    const bubbles = document.querySelectorAll("#messages .msg.user .bubble");
    const last = bubbles[bubbles.length - 1];
    return last ? last.textContent.trim() : "";
  }

  async function toggle() {
    if (window.Chat && Chat.isSending) return;
    const next = current === WEBSEARCH ? RETRIEVAL : WEBSEARCH;
    const b = btn();
    if (b) b.disabled = true;
    try {
      const id = Conversations.activeId;
      const empty = !document.querySelector("#messages .msg");
      const carry = empty ? "" : lastQuestion();
      current = next;                       // để cuộc trò chuyện mới tạo đúng hệ thống
      if (id && empty) {
        // Chưa hỏi gì thì đổi tại chỗ, không cần mở ô chat mới.
        await API.patch(`/api/conversations/${id}`, { system: next });
        render();
        if (window.Chat) Chat.empty();
      } else {
        await Conversations.create();       // create() tự gắn hệ thống đang chọn
        const input = document.getElementById("input");
        if (input && carry) {
          // Chỉ ĐIỀN SẴN, không tự gửi — hỏi hay không là quyền người dùng.
          input.value = carry;
          input.focus();
        }
      }
    } catch (err) {
      alert(err.message);
    } finally {
      if (b) b.disabled = false;
      render();
    }
  }

  function init(cfg) {
    if (cfg && Array.isArray(cfg.systems) && cfg.systems.length) list = cfg.systems;
    current = norm((cfg && cfg.default_system) || WEBSEARCH);
    const b = btn();
    if (b) b.onclick = toggle;
    render();
  }

  return {
    init, reflect, label, render, toggle,
    WEBSEARCH, RETRIEVAL,
    get current() { return current; },
    get isRetrieval() { return current === RETRIEVAL; },
  };
})();

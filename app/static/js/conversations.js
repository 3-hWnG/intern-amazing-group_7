/* Quản lý danh sách hội thoại ở thanh bên. */
window.Conversations = (function () {
  let items = [];
  let activeId = null;
  const listEl = () => document.getElementById("conv-list");
  const titleEl = () => document.getElementById("conv-title");
  let onSelect = () => {};

  /* Lỗi phát hiện 24/09/2026: window.currentMode (app.js) là 1 biến TOÀN CỤC
     DUY NHẤT, không gắn với hội thoại nào — reload trang (luôn reset về
     "system2") hoặc xem qua hội thoại khác rồi quay lại sẽ ÂM THẦM đổi hệ
     thống xử lý (System 1 Web Search <-> System 2 CSDL nội bộ) cho các lượt
     tiếp theo trong CÙNG một hội thoại, không có cảnh báo gì trên UI. Sửa:
     nhớ mode NGAY LÚC TẠO từng hội thoại, lưu vào localStorage (cùng cách
     đang lưu "theme" ở app.js) để không mất khi tải lại trang, rồi luôn ưu
     tiên đọc mode của ĐÚNG hội thoại đang gửi tin thay vì biến toàn cục. */
  const MODE_KEY = "convModes";
  function loadModeMap() {
    try { return JSON.parse(localStorage.getItem(MODE_KEY) || "{}"); }
    catch (_) { return {}; }
  }
  function getMode(id) {
    if (id == null) return null;
    return loadModeMap()[String(id)] || null;
  }
  function recordMode(id, mode) {
    if (id == null || (mode !== "system1" && mode !== "system2")) return;
    try {
      const map = loadModeMap();
      map[String(id)] = mode;
      localStorage.setItem(MODE_KEY, JSON.stringify(map));
    } catch (_) {}
  }

  function render() {
    const el = listEl();
    el.innerHTML = "";
    if (!items.length) {
      el.innerHTML = '<p class="muted small">Chưa có cuộc trò chuyện nào.</p>';
      return;
    }
    items.forEach((c) => {
      const row = document.createElement("div");
      row.className = "conv-item" + (c.id === activeId ? " active" : "");

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "conv-open";
      btn.textContent = c.title;
      btn.title = c.title;
      btn.onclick = () => select(c.id);

      const del = document.createElement("button");
      del.type = "button";
      del.className = "conv-del";
      del.textContent = "×";
      del.title = "Xoá cuộc trò chuyện";
      del.onclick = async (e) => {
        e.stopPropagation();
        if (!confirm(`Xoá "${c.title}"?`)) return;
        await API.del(`/api/conversations/${c.id}`);
        if (activeId === c.id) activeId = null;
        await refresh();
        if (!activeId && items.length) select(items[0].id);
        else if (!items.length) onSelect(null);
      };

      row.append(btn, del);
      el.appendChild(row);
    });
  }

  async function refresh() {
    const data = await API.get("/api/conversations");
    items = data.conversations || [];
    render();
    return items;
  }

  function select(id, opts = {}) {
    activeId = id;
    const found = items.find((c) => c.id === id);
    if (found) titleEl().textContent = found.title;
    render();
    if (!opts.skipLoad) {
      onSelect(id);
    }
  }

  async function create(opts = {}) {
    const data = await API.post("/api/conversations", {});
    /* Ghi nhớ NGAY khi tạo: hội thoại này thuộc mode nào (đọc window.currentMode
       tại đúng thời điểm tạo — app.js/chat.js đều đã setMode trước khi gọi
       create() ở mọi nơi cần đổi mode). */
    recordMode(data.conversation.id, window.currentMode || "system2");
    await refresh();
    select(data.conversation.id, opts);
    return data.conversation;
  }

  return {
    refresh, create, select, render, getMode,
    get activeId() { return activeId; },
    get items() { return items; },
    set onSelect(fn) { onSelect = fn; },
  };
})();

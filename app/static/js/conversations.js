/* Quản lý danh sách hội thoại ở thanh bên. */
window.Conversations = (function () {
  let items = [];
  let activeId = null;
  const listEl = () => document.getElementById("conv-list");
  const titleEl = () => document.getElementById("conv-title");
  let onSelect = () => {};

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

  function select(id) {
    activeId = id;
    const found = items.find((c) => c.id === id);
    if (found) titleEl().textContent = found.title;
    render();
    onSelect(id);
  }

  async function create() {
    const data = await API.post("/api/conversations", {});
    await refresh();
    select(data.conversation.id);
    return data.conversation;
  }

  return {
    refresh, create, select, render,
    get activeId() { return activeId; },
    get items() { return items; },
    set onSelect(fn) { onSelect = fn; },
  };
})();

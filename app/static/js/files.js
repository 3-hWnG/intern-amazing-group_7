/* Tệp đính kèm của cuộc trò chuyện.
   Frontend chỉ cần biết ba việc (đúng như slide 7 mô tả):
     1. gửi tệp lên  -> nhận file_id
     2. hiển thị tên tệp đang đính kèm
     3. xoá tệp
   Nội dung tệp KHÔNG bao giờ đi qua đây — backend tự đánh chỉ mục và tra cứu. */
window.Files = (function () {
  let items = [];
  let convId = null;
  let pending = [];                       // tệp đang xử lý, hiện mờ

  const barEl = () => document.getElementById("attachments");

  function render() {
    const bar = barEl();
    if (!bar) return;
    bar.innerHTML = "";
    const all = [
      ...items.map((f) => ({ ...f, _pending: false })),
      ...pending.map((name) => ({ name, status: "pending", _pending: true })),
    ];
    bar.hidden = all.length === 0;
    if (!all.length) return;

    all.forEach((f) => {
      const pill = document.createElement("div");
      pill.className = "file-pill"
        + (f._pending || f.status === "pending" ? " pending" : "")
        + (f.status === "failed" ? " failed" : "");

      const name = document.createElement("span");
      name.className = "name";
      name.textContent = "📄 " + f.name;
      name.title = f.name;
      pill.appendChild(name);

      const meta = document.createElement("span");
      meta.className = "meta";
      if (f._pending || f.status === "pending") meta.textContent = "đang xử lý…";
      else if (f.status === "failed") meta.textContent = f.error || "lỗi";
      else meta.textContent = f.description || "";
      if (f.status === "failed" && f.error) pill.title = f.error;
      pill.appendChild(meta);

      if (!f._pending && f.file_id) {
        const rm = document.createElement("button");
        rm.type = "button";
        rm.className = "rm";
        rm.textContent = "×";
        rm.title = "Gỡ tệp khỏi cuộc trò chuyện";
        rm.onclick = async () => {
          rm.disabled = true;
          try {
            await API.del(`/api/files/${f.file_id}`);
            await refresh(convId);
          } catch (e) {
            rm.disabled = false;
            alert(e.message);
          }
        };
        pill.appendChild(rm);
      }
      bar.appendChild(pill);
    });
  }

  async function refresh(id) {
    convId = id;
    if (!id) { items = []; pending = []; render(); return items; }
    try {
      const data = await API.get(`/api/conversations/${id}/files`);
      items = data.files || [];
    } catch (_) {
      items = [];
    }
    render();
    return items;
  }

  async function attach(id, file) {
    convId = id;
    pending.push(file.name);
    render();
    try {
      const doc = await API.upload(`/api/conversations/${id}/files`, file);
      if (doc.status === "failed") alert(doc.error || "Không xử lý được tệp.");
    } catch (e) {
      alert(e.message);
    } finally {
      pending = pending.filter((n) => n !== file.name);
      await refresh(id);
    }
  }

  return { refresh, attach, render, get items() { return items; } };
})();

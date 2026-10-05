/* System 3 — khung chat: danh sách tin nhắn, blocks[] nhiều đoạn, thẻ clarify, dev panel.
   Không auth: conversation_id lưu ở localStorage (server cấp). Dev: ?dev=1 */
(function () {
  const DEV = new URLSearchParams(location.search).get("dev") === "1";
  const $ = (id) => document.getElementById(id);
  const box = $("messages");
  let convId = null;
  let sending = false;

  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;   // textContent: nội dung mô hình không được tin
    return e;
  };
  const scroll = () => { box.scrollTop = box.scrollHeight; };
  const store = {
    get: () => { try { return localStorage.getItem("s3_conv"); } catch (_) { return null; } },
    set: (v) => { try { v ? localStorage.setItem("s3_conv", v) : localStorage.removeItem("s3_conv"); } catch (_) {} },
  };

  async function api(url, body) {
    const res = await fetch(url, body ? {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    } : undefined);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || data.error || res.statusText);
    return data;
  }

  function empty() {
    box.innerHTML = '<div class="empty"><h2>Bạn cần làm thủ tục gì?</h2>' +
      "<p>Ví dụ: <em>“Làm giấy khai sinh cần giấy tờ gì?”</em></p></div>";
  }

  function userMsg(text) {
    const w = el("div", "msg user");
    w.appendChild(el("div", "bubble", text));
    box.appendChild(w);
  }

  function blockCard(b) {
    const c = el("div", "block-card");
    if (b.title) c.appendChild(el("h4", "", b.title));
    c.appendChild(el("div", "txt", b.text || ""));
    (b.sources || []).forEach((s) => {
      const line = el("div", "source");
      const label = typeof s === "string" ? s : (s.label || s.title || s.url || "");
      const url = typeof s === "string" ? s : s.url;
      if (/^https?:\/\//i.test(url || "")) {
        const a = el("a", "", label);
        a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer";
        line.appendChild(a);
      } else line.appendChild(el("span", "plain", label));
      c.appendChild(line);
    });
    const others = (b.variants && b.variants.others) || [];
    if (others.length) {      /* thủ tục có nhiều dạng: nút đổi sang dạng khác */
      const row = el("div", "choice-list");
      row.appendChild(el("div", "source", "Thủ tục này còn các dạng khác:"));
      others.forEach((v) => {
        const btn = el("button", "choice-item");
        btn.type = "button";
        btn.append(el("span", "choice-text", v.label));
        btn.onclick = () => send(v.label);
        row.appendChild(btn);
      });
      c.appendChild(row);
    }
    return c;
  }

  /* Thẻ hỏi lại: nút MCQ + ô gõ tự do; gửi lại kèm reply_to = id tin nhắn chứa thẻ. */
  function clarifyCard(cl, messageId, locked) {
    const wrap = el("div", "choice-table-wrap");
    const head = el("div", "choice-table-head");
    head.appendChild(el("strong", "", cl.question || ""));
    wrap.appendChild(head);
    const list = el("div", "choice-list");
    (cl.options || []).forEach((opt, i) => {
      const b = el("button", "choice-item");
      b.type = "button";
      b.append(el("span", "choice-badge", String(i + 1)), el("span", "choice-text", opt));
      b.disabled = locked;
      b.onclick = () => send(opt, messageId);
      list.appendChild(b);
    });
    wrap.appendChild(list);
    if (cl.allow_free_text) {
      const row = el("div", "choice-custom-row");
      const input = el("input", "choice-custom-input");
      input.type = "text"; input.placeholder = "Hoặc tự gõ…"; input.disabled = locked;
      const btn = el("button", "choice-custom-btn", "Gửi");
      btn.type = "button"; btn.disabled = locked;
      const go = () => { const v = input.value.trim(); if (v) send(v, messageId); };
      btn.onclick = go;
      input.onkeydown = (e) => { if (e.key === "Enter") { e.preventDefault(); go(); } };
      row.append(input, btn);
      wrap.appendChild(row);
    }
    return wrap;
  }

  function devPanel(obj) {
    const d = el("details", "evidence");
    d.appendChild(el("summary", "", "dev: plan / trace"));
    d.appendChild(el("pre", "dev-json", JSON.stringify(obj, null, 2)));
    return d;
  }

  function assistantMsg(m, locked) {
    const w = el("div", "msg assistant");
    (m.blocks || []).forEach((b) => w.appendChild(blockCard(b)));
    if (m.clarify) w.appendChild(clarifyCard(m.clarify, m.message_id || m.id, locked));
    if (!(m.blocks || []).length && !m.clarify) w.appendChild(el("div", "bubble", m.content || ""));
    if (DEV && (m.dev || m.plan)) w.appendChild(devPanel(m.dev || { plan: m.plan }));
    box.appendChild(w);
    return w;
  }

  async function loadConv(id) {
    convId = id; store.set(id);
    box.innerHTML = "";
    if (!id) { empty(); return; }
    try {
      const data = await api(`/conversations/${id}/messages`);
      const msgs = data.messages;
      if (!msgs.length) empty();
      msgs.forEach((m, i) => {
        if (m.role === "user") userMsg(m.content);
        else assistantMsg(m, i !== msgs.length - 1);   // thẻ cũ bị khoá, chỉ thẻ cuối bấm được
      });
      scroll();
    } catch (_) { convId = null; store.set(null); empty(); }
  }

  async function refreshList() {
    const { conversations } = await api("/conversations");
    const nav = $("conv-list");
    nav.innerHTML = "";
    conversations.forEach((c) => {
      const row = el("div", "conv-item" + (c.id === convId ? " active" : ""));
      const b = el("button", "conv-open", c.title);
      b.type = "button";
      b.onclick = async () => { await loadConv(c.id); refreshList(); };
      row.appendChild(b);
      nav.appendChild(row);
    });
  }

  async function send(text, replyTo) {
    if (sending || !text.trim()) return;
    sending = true; $("send").disabled = true;
    if (box.querySelector(".empty")) box.innerHTML = "";
    box.querySelectorAll(".choice-item,.choice-custom-btn,.choice-custom-input").forEach((x) => (x.disabled = true));
    userMsg(text);
    const status = el("div", "status");
    status.append(el("span", "spinner"), el("span", "", "Đang xử lý…"));
    box.appendChild(status); scroll();
    try {
      const body = { text, conversation_id: convId };
      if (replyTo) body.reply_to = replyTo;
      const r = await api("/chat", body);
      convId = r.conversation_id; store.set(convId);
      status.remove();
      assistantMsg(r, false);
      refreshList();
    } catch (e) {
      status.remove();
      const w = el("div", "msg assistant");
      w.appendChild(el("div", "bubble", "Lỗi: " + e.message));
      box.appendChild(w);
    } finally {
      sending = false; $("send").disabled = false; scroll();
    }
  }

  $("composer").addEventListener("submit", (e) => {
    e.preventDefault();
    const v = $("input").value;
    $("input").value = "";
    send(v);
  });
  $("input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("composer").requestSubmit(); }
  });
  $("new-chat").onclick = async () => { await loadConv(null); refreshList(); };
  $("reset-topic").onclick = async () => {
    if (!convId || sending) return;
    try {
      await api(`/conversations/${convId}/reset_facts`, {});
      const w = el("div", "msg assistant");
      w.appendChild(el("div", "bubble", "Đã bắt đầu chủ đề mới. Bạn muốn hỏi về thủ tục nào?"));
      box.appendChild(w); scroll();
    } catch (e) { alert("Lỗi: " + e.message); }
  };
  $("toggle-sidebar").onclick = () => $("sidebar").classList.toggle("hidden");

  api("/health").then((h) => { $("model-name").textContent = h.model + (DEV ? " · dev" : ""); }).catch(() => {});
  loadConv(store.get()).then(refreshList);
})();

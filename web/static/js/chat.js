/* System 3 — khung chat: danh sách tin nhắn, blocks[] nhiều đoạn, thẻ clarify, dev panel.
   Không auth: conversation_id lưu ở localStorage (server cấp). Dev: ?dev=1 */
(function () {
  const DEV = new URLSearchParams(location.search).get("dev") === "1";
  const $ = (id) => document.getElementById(id);
  const box = $("messages");
  let convId = null;
  let sending = false;
  let cfg = {};

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

  async function api(url, body, method) {
    const res = await fetch(url, body || method ? {
      method: method || "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined,
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

  /* Phase 20: nút "Tạo bảng full" -> GET /procedure/{id}/table (nguyên văn dữ liệu, không LLM). Bấm lần nữa để ẩn. */
  function tableButton(pid) {
    const wrap = el("div", "full-table-wrap");
    const btn = el("button", "table-btn", "Tạo bảng full");
    btn.type = "button";
    let panel = null;
    btn.onclick = async () => {
      if (panel) { panel.hidden = !panel.hidden; btn.textContent = panel.hidden ? "Tạo bảng full" : "Ẩn bảng"; return; }
      btn.disabled = true; btn.textContent = "Đang tạo bảng…";
      try {
        panel = fullTable(await api(`/procedure/${encodeURIComponent(pid)}/table`));
        wrap.appendChild(panel); btn.textContent = "Ẩn bảng";
      } catch (e) { btn.textContent = "Tạo bảng full"; wrap.appendChild(el("div", "error", "Không tạo được bảng: " + e.message)); }
      btn.disabled = false;
    };
    wrap.appendChild(btn);
    return wrap;
  }

  function fullTable(t) {
    const tb = el("table", "full-table");
    tb.appendChild(el("caption", "", t.name));
    t.rows.forEach((r) => {
      const tr = el("tr", r.status === "present" ? "" : "absent");
      tr.appendChild(el("th", "", r.title));
      const td = el("td");
      if (r.text.length > 220) {          /* mục dài: thu gọn, bấm mở */
        const d = el("details");
        d.appendChild(el("summary", "", r.text.slice(0, 90).replace(/\s+/g, " ") + "…"));
        d.appendChild(el("div", "txt", r.text));
        td.appendChild(d);
      } else td.appendChild(el("div", "txt", r.text));
      tr.appendChild(td); tb.appendChild(tr);
    });
    const tr = el("tr"); tr.appendChild(el("th", "", "Nguồn"));
    const td = el("td");
    (t.sources || []).forEach((s) => {
      const line = el("div", "source");
      if (/^https?:\/\//i.test(s.url || "")) {
        const a = el("a", "", s.label); a.href = s.url; a.target = "_blank"; a.rel = "noopener noreferrer"; line.appendChild(a);
      } else line.appendChild(el("span", "plain", s.label));
      td.appendChild(line);
    });
    tr.appendChild(td); tb.appendChild(tr);
    const w = el("div", "full-table-scroll"); w.appendChild(tb);
    return w;
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
    if (b.proc_id && cfg.table_button !== false) c.appendChild(tableButton(b.proc_id));
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

  /* quản lý hộp thoại: menu ⋯ (đổi tên, xoá) trên từng dòng + "Xoá tất cả" */
  let openMenu = null;
  const closeMenu = () => { if (openMenu) { openMenu.remove(); openMenu = null; } };
  document.addEventListener("click", closeMenu);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeMenu(); });

  function download(id, format) {   // tải file qua thẻ <a download>; server gửi Content-Disposition
    const a = el("a"); a.href = `/conversations/${id}/export?format=${format}`; a.download = "";
    document.body.appendChild(a); a.click(); a.remove();
  }

  function renameInline(row, c, btn) {
    const inp = el("input", "conv-rename"); inp.value = c.title; inp.maxLength = 60;
    let done = false;
    const finish = async (save) => {
      if (done) return; done = true;
      const t = inp.value.trim();
      if (save && t && t !== c.title) { try { await api(`/conversations/${c.id}`, { title: t }, "PATCH"); } catch (e) { alert("Lỗi: " + e.message); } }
      refreshList();
    };
    inp.onkeydown = (e) => { if (e.key === "Enter") finish(true); else if (e.key === "Escape") finish(false); };
    inp.onblur = () => finish(true);
    inp.onclick = (e) => e.stopPropagation();
    row.replaceChild(inp, btn); inp.focus(); inp.select();
  }

  async function removeConv(c) {
    if (!confirm(`Xoá hộp thoại "${c.title}"? Không khôi phục được.`)) return;
    try {
      await api(`/conversations/${c.id}`, null, "DELETE");
      if (c.id === convId) await loadConv(null);
    } catch (e) { alert("Lỗi: " + e.message); }
    refreshList();
  }

  async function refreshList() {
    const { conversations } = await api("/conversations");
    const nav = $("conv-list");
    nav.innerHTML = "";
    conversations.forEach((c) => {
      const row = el("div", "conv-item" + (c.id === convId ? " active" : "") + (c.pinned ? " pinned" : ""));
      const b = el("button", "conv-open", (c.pinned ? "📌 " : "") + c.title);
      b.type = "button"; b.title = c.title;
      b.onclick = async () => { await loadConv(c.id); refreshList(); };
      b.ondblclick = () => renameInline(row, c, b);
      const m = el("button", "conv-more", "⋯");
      m.type = "button"; m.title = "Tuỳ chọn"; m.setAttribute("aria-label", "Tuỳ chọn hộp thoại");
      m.onclick = (e) => {
        e.stopPropagation(); closeMenu();
        const menu = el("div", "conv-menu");
        const item = (label, fn, cls) => { const i = el("button", "conv-menu-item " + (cls || ""), label); i.type = "button"; i.onclick = (ev) => { ev.stopPropagation(); closeMenu(); fn(); }; menu.appendChild(i); };
        item(c.pinned ? "Bỏ ghim" : "Ghim", async () => {
          try { await api(`/conversations/${c.id}`, { pinned: !c.pinned }, "PATCH"); } catch (e) { alert("Lỗi: " + e.message); }
          refreshList();
        });
        item("Xuất Markdown", () => download(c.id, "md"));
        item("Xuất JSON", () => download(c.id, "json"));
        item("Xuất PDF", () => window.open(`/conversations/${c.id}/export?format=pdf`, "_blank"));
        item("Đổi tên", () => renameInline(row, c, b));
        item("Xoá", () => removeConv(c), "danger");
        row.appendChild(menu); openMenu = menu;
      };
      row.append(b, m);
      nav.appendChild(row);
    });
    $("clear-all").hidden = !conversations.length;
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
  $("clear-all").onclick = async () => {
    if (!confirm("Xoá TẤT CẢ hộp thoại? Không khôi phục được.")) return;
    try { await api("/conversations", null, "DELETE"); await loadConv(null); } catch (e) { alert("Lỗi: " + e.message); }
    refreshList();
  };
  $("reset-topic").onclick = async () => {
    if (!convId || sending) return;
    try {
      await api(`/conversations/${convId}/reset_facts`, {});
      /* nút/thẻ cũ không còn nghĩa với chủ đề mới: làm mờ, khoá, gắn nhãn */
      box.querySelectorAll(".choice-list,.choice-table-wrap").forEach((x) => {
        if (x.classList.contains("stale") || x.parentElement.closest(".stale")) return;
        x.classList.add("stale");
        x.querySelectorAll("button,input").forEach((y) => (y.disabled = true));
        x.appendChild(el("div", "stale-note", "Đã hết hiệu lực (chủ đề mới)"));
      });
      const w = el("div", "msg assistant");
      w.appendChild(el("div", "bubble", "Đã bắt đầu chủ đề mới. Bạn muốn hỏi về thủ tục nào?"));
      box.appendChild(w); scroll();
    } catch (e) { alert("Lỗi: " + e.message); }
  };
  if (innerWidth <= 760) $("sidebar").classList.add("hidden");   // điện thoại: thanh bên mặc định ẩn
  $("toggle-sidebar").onclick = () => $("sidebar").classList.toggle("hidden");

  /* ---- Phase 20: chỉ báo AI + panel cấu hình (GET/POST /config). Công tắc chỉ đổi được khi server chạy S3_DEV=1. ---- */
  const aiBadge = $("ai-badge"), cfgPanel = $("cfg-panel");
  function renderCfg() {
    const on = !!cfg.answer_llm;
    aiBadge.textContent = "AI " + (on ? "bật" : "tắt");
    aiBadge.className = "ai-badge " + (on ? "on" : "off");
    cfgPanel.innerHTML = "";
    const head = el("div", "cfg-main");
    const lab = el("div"); lab.append(el("b", "", "Trả lời bằng AI"), el("small", "", "Diễn giải điều kiện, so sánh. Tắt thì trả nguyên văn dữ liệu."));
    const sw = el("label", "switch"), box = el("input"), knob = el("span");
    box.type = "checkbox"; box.checked = on; box.disabled = !cfg.dev;
    box.onchange = () => saveCfg({ answer_llm: box.checked });
    sw.append(box, knob); head.append(lab, sw); cfgPanel.appendChild(head);
    const st = el("div", "cfg-sub"); const dot = el("i", cfg.model_loaded ? "ok" : "");
    st.append(dot, `${cfg.model} · ${cfg.model_loaded ? "đã nạp" : "chưa nạp"}`); cfgPanel.appendChild(st);
    const adv = el("details", "cfg-adv"); adv.appendChild(el("summary", "", "Nâng cao"));
    const row = (k, v) => { const r = el("div", "cfg-row"); r.append(el("span", "", k), v); adv.appendChild(r); };
    const val = (t) => el("b", "", t);
    if (cfg.dev) {
      const sel = el("select");
      (cfg.modes || []).forEach((m) => { const o = el("option", "", m); o.value = m; o.selected = m === cfg.mode; sel.appendChild(o); });
      sel.onchange = () => saveCfg({ mode: sel.value });
      row("Planner", sel);
    } else row("Planner", val(cfg.mode));
    row("Timeout (Planner / trả lời)", val(`${cfg.timeout}s / ${cfg.answer_timeout}s`));
    row("Ngưỡng confidence", val(String(cfg.confidence)));
    row("Dev mode", val(cfg.dev ? "bật" : "tắt"));
    if (!cfg.dev) adv.appendChild(el("div", "cfg-note", "Chỉ xem. Đổi cấu hình cần chạy server với S3_DEV=1."));
    cfgPanel.appendChild(adv);
  }
  async function loadCfg() { try { cfg = await api("/config"); renderCfg(); } catch (_) { aiBadge.textContent = "AI: ?"; } }
  async function saveCfg(patch) {
    try { cfg = await api("/config", patch); } catch (e) { alert("Lỗi: " + e.message); }
    renderCfg();
  }
  aiBadge.onclick = (e) => { e.stopPropagation(); cfgPanel.hidden = !cfgPanel.hidden; if (!cfgPanel.hidden) loadCfg(); };
  document.addEventListener("click", (e) => { if (!cfgPanel.hidden && !cfgPanel.contains(e.target)) cfgPanel.hidden = true; });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cfgPanel.hidden = true; });
  loadCfg();

  api("/health").then((h) => { $("model-name").textContent = h.model + (DEV ? " · dev" : ""); }).catch(() => {});
  loadConv(store.get()).then(refreshList);
})();

/* System 4 — trang chung Strict + Friendly.
   Strict  = nguyên hành vi System 3 (web/static/js/chat.js, copy sang đây; gọi API System 3: /chat, /conversations/...).
   Friendly = System 4 (API /s4/..., chữ hiện dần qua SSE).
   Danh sách hội thoại chung, mỗi dòng gắn nhãn chế độ. Bấm một hội thoại -> tự chuyển sang chế độ của nó. Dev: ?dev=1 */
(function () {
  const DEV = new URLSearchParams(location.search).get("dev") === "1";
  const $ = (id) => document.getElementById(id);
  const box = $("messages");
  let me = null, pub = {}, cfg = {};
  let mode = "strict";
  let convId = null;
  let sending = false, abortCtl = null;
  let convs = [];

  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;   // textContent: nội dung mô hình không được tin
    return e;
  };
  const scroll = () => { box.scrollTop = box.scrollHeight; };
  const ls = {
    get: (k) => { try { return localStorage.getItem(k); } catch (_) { return null; } },
    set: (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (_) {} },
  };
  const toLogin = () => { location.href = "/s4/login"; };

  async function api(url, body, method) {
    const res = await fetch(url, body || method ? {
      method: method || "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined,
    } : undefined);
    if (res.status === 401) { toLogin(); throw new Error("Cần đăng nhập"); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : (data.error || res.statusText));
    return data;
  }
  const base = (m, id) => (m === "strict" ? `/conversations/${id}` : `/s4/conversations/${id}`);

  /* ------------------------------------------------------------ chế độ ---- */
  function setMode(m) {
    mode = m === "friendly" ? "friendly" : "strict";
    ls.set("s4_mode", mode);
    document.body.dataset.mode = mode;
    document.querySelectorAll(".mode-switch button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
    modelName();
    $("input").placeholder = mode === "friendly" ? "Nhắn cho AI…" : "Nhập câu hỏi về thủ tục…";
    $("cfg-panel").hidden = true;
  }
  document.querySelectorAll(".mode-switch button").forEach((b) => {
    b.onclick = async () => {
      if (sending || b.dataset.mode === mode) return;
      setMode(b.dataset.mode);
      await loadConv(null);
      refreshList();
    };
  });

  function modelName() {
    $("model-name").textContent = mode === "friendly" ? (pub.friendly_model || "") : (cfg.model ? cfg.model + " · luật" : "");
  }

  function setTitle() {
    const c = convs.find((x) => x.id === convId);
    $("conv-title").textContent = c ? c.title : (pub.app_title || "Instant Specialist");
  }

  function empty() {
    box.innerHTML = mode === "friendly"
      ? '<div class="empty"><h2>Mình có thể giúp gì cho bạn?</h2><p>Chế độ Friendly: trò chuyện với AI.</p></div>'
      : '<div class="empty"><h2>Bạn cần làm thủ tục gì?</h2>' +
        "<p>Ví dụ: <em>“Làm giấy khai sinh cần giấy tờ gì?”</em></p></div>";
  }

  function userMsg(text) {
    const w = el("div", "msg user");
    w.appendChild(el("div", "bubble", text));
    box.appendChild(w);
  }

  /* -------------------------------------------- Strict: hiển thị như System 3 */
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

  function sourceLine(label, url) {
    const line = el("div", "source");
    if (/^https?:\/\//i.test(url || "")) {
      const a = el("a", "", label); a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer"; line.appendChild(a);
    } else line.appendChild(el("span", "plain", label));
    return line;
  }

  function fullTable(t) {
    const tb = el("table", "full-table");
    tb.appendChild(el("caption", "", t.name));
    t.rows.forEach((r) => {
      const tr = el("tr", r.status === "present" ? "" : "absent");
      tr.appendChild(el("th", "", r.title));
      const td = el("td");
      if (r.text.length > 220) {
        const d = el("details");
        d.appendChild(el("summary", "", r.text.slice(0, 90).replace(/\s+/g, " ") + "…"));
        d.appendChild(el("div", "txt", r.text));
        td.appendChild(d);
      } else td.appendChild(el("div", "txt", r.text));
      tr.appendChild(td); tb.appendChild(tr);
    });
    const tr = el("tr"); tr.appendChild(el("th", "", "Nguồn"));
    const td = el("td");
    (t.sources || []).forEach((s) => td.appendChild(sourceLine(s.label, s.url)));
    tr.appendChild(td); tb.appendChild(tr);
    const w = el("div", "full-table-scroll"); w.appendChild(tb);
    return w;
  }

  function blockCard(b) {
    const c = el("div", "block-card");
    if (b.title) c.appendChild(el("h4", "", b.title));
    c.appendChild(el("div", "txt", b.text || ""));
    (b.sources || []).forEach((s) => {
      const label = typeof s === "string" ? s : (s.label || s.title || s.url || "");
      c.appendChild(sourceLine(label, typeof s === "string" ? s : s.url));
    });
    if (b.proc_id && cfg.table_button !== false) c.appendChild(tableButton(b.proc_id));
    const others = (b.variants && b.variants.others) || [];
    if (others.length) {
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

  function strictMsg(m, locked) {
    const w = el("div", "msg assistant");
    (m.blocks || []).forEach((b) => w.appendChild(blockCard(b)));
    if (m.clarify) w.appendChild(clarifyCard(m.clarify, m.message_id || m.id, locked));
    if (!(m.blocks || []).length && !m.clarify) w.appendChild(el("div", "bubble", m.content || ""));
    if (DEV && (m.dev || m.plan)) w.appendChild(devPanel(m.dev || { plan: m.plan }));
    box.appendChild(w);
    return w;
  }

  /* ------------------------------------------------------ Friendly ------- */
  /* Markdown -> HTML an toàn (marked + DOMPurify, lưu sẵn trong /s4/static/vendor, không cần mạng) */
  if (window.DOMPurify) DOMPurify.addHook("afterSanitizeAttributes", (n) => {
    if (n.tagName === "A") { n.setAttribute("target", "_blank"); n.setAttribute("rel", "noopener noreferrer"); }
  });
  function md(text) {
    try { return DOMPurify.sanitize(marked.parse(text || "", { breaks: true, gfm: true })); }
    catch (_) { const d = el("div"); d.textContent = text || ""; return d.innerHTML; }
  }
  /* ẩn khối [[CHOICES]] khi đang hiện chữ dần (kể cả lúc mới gõ dở "[[CHO") */
  const visible = (t) => t.split(/\[\[\s*CHOICES/i)[0].replace(/\[(\[[A-Za-z]*)?$/, "");

  function actionBtn(label, title, fn, cls) {
    const b = el("button", "icon-btn" + (cls ? " " + cls : ""), label);
    b.type = "button"; b.title = title; b.setAttribute("aria-label", title);
    b.onclick = (e) => { e.stopPropagation(); fn(b); };
    return b;
  }

  function versionNav(m) {
    const vs = m.versions || [m.id];
    if (vs.length < 2) return null;
    const i = vs.indexOf(m.id);
    const nav = el("span", "ver-nav");
    const prev = actionBtn("‹", "Phiên bản trước", () => switchTo(vs[i - 1]));
    const next = actionBtn("›", "Phiên bản sau", () => switchTo(vs[i + 1]));
    prev.disabled = i <= 0; next.disabled = i >= vs.length - 1;
    nav.append(prev, el("span", "ver-count", (i + 1) + "/" + vs.length), next);
    return nav;
  }

  async function switchTo(mid) {
    if (sending || !convId) return;
    try { renderFriendly((await api("/s4/conversations/" + convId + "/switch", { message_id: mid })).messages); }
    catch (e) { alert("Lỗi: " + e.message); }
  }

  async function copyText(text, btn) {
    try { await navigator.clipboard.writeText(text); }
    catch (_) { const t = el("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); }
    const old = btn.textContent; btn.textContent = "✓"; setTimeout(() => { btn.textContent = old; }, 1200);
  }

  function friendlyUser(m) {
    const w = el("div", "msg user");
    w.dataset.mid = m.id;
    w.appendChild(el("div", "bubble", m.content));
    const bar = el("div", "msg-actions");
    const nav = versionNav(m); if (nav) bar.appendChild(nav);
    bar.appendChild(actionBtn("✎", "Sửa tin nhắn", () => startEdit(w, m)));
    w.appendChild(bar);
    box.appendChild(w);
  }

  function startEdit(w, m) {
    if (sending) return;
    w.innerHTML = "";
    const ta = el("textarea", "edit-box"); ta.value = m.content; ta.rows = Math.min(8, m.content.split("\n").length + 1);
    const row = el("div", "edit-row");
    const cancel = el("button", "btn-ghost", "Huỷ"); cancel.type = "button";
    const ok = el("button", "primary", "Gửi"); ok.type = "button";
    cancel.onclick = () => loadConv(convId, "friendly");
    ok.onclick = () => {
      const v = ta.value.trim(); if (!v) return;
      while (w.nextSibling) w.nextSibling.remove();   // các tin sau tin được sửa thuộc phiên bản cũ
      w.remove();
      send(v, null, { edit_of: m.id });
    };
    ta.onkeydown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ok.click(); } if (e.key === "Escape") cancel.click(); };
    row.append(cancel, ok); w.append(ta, row); ta.focus();
  }

  function friendlyAssistant(m, isLast) {
    const w = el("div", "msg assistant");
    w.dataset.mid = m.id;
    const err = m.status === "error";
    const b = el("div", "bubble md" + (err ? " err" : ""));
    if (err) b.textContent = "Lỗi: " + m.content; else b.innerHTML = md(m.content);
    w.appendChild(b);
    if (m.status === "stopped") w.appendChild(el("div", "stopped-note", "(đã dừng)"));
    const choices = (m.meta && m.meta.choices) || [];
    if (choices.length) w.appendChild(clarifyCard({ question: "Chọn nhanh:", options: choices, allow_free_text: true }, null, !isLast));
    const bar = el("div", "msg-actions");
    const nav = versionNav(m); if (nav) bar.appendChild(nav);
    if (!err) bar.appendChild(actionBtn("⧉", "Sao chép", (btn) => copyText(m.content, btn)));
    bar.appendChild(actionBtn("↻", "Tạo lại câu trả lời", () => regenerate(w, m)));
    if (!err) {
      const fb = (v, label, title) => {
        const btn = actionBtn(label, title, async (x) => {
          const val = m.feedback === v ? 0 : v;
          try { await api("/s4/conversations/" + convId + "/messages/" + m.id + "/feedback", { value: val }); } catch (e) { alert("Lỗi: " + e.message); return; }
          m.feedback = val;
          bar.querySelectorAll(".fb").forEach((y) => y.classList.remove("on"));
          if (val) x.classList.add("on");
        }, "fb" + (m.feedback === v ? " on" : ""));
        bar.appendChild(btn);
      };
      fb(1, "👍", "Câu trả lời tốt"); fb(-1, "👎", "Câu trả lời chưa tốt");
    }
    w.appendChild(bar);
    if (me && me.role === "dev" && m.meta) {   // dev: thấy guardrail / bộ lọc chữ đã can thiệp
      const notes = [];
      if (m.meta.guard) notes.push("guardrail: " + m.meta.guard);
      if (m.meta.filtered) notes.push("đã lọc " + m.meta.filtered.letters + " chữ lạ, " + m.meta.filtered.other + " ký hiệu");
      if (m.meta.leak_retry) notes.push("đã viết lại do lọt chữ lạ");
      if (notes.length) w.appendChild(el("div", "dev-note", notes.join(" · ")));
    }
    box.appendChild(w);
    return w;
  }

  function regenerate(w, m) {
    if (sending) return;
    while (w.nextSibling) w.nextSibling.remove();
    w.remove();
    send("", null, { regenerate_of: m.id });
  }

  function renderFriendly(msgs) {
    box.innerHTML = "";
    if (!msgs.length) { empty(); return; }
    const lastA = msgs.map((x) => x.role).lastIndexOf("assistant");
    msgs.forEach((x, i) => { if (x.role === "user") friendlyUser(x); else friendlyAssistant(x, i === lastA && i === msgs.length - 1); });
    scroll();
  }

  function memoryNote(ev) {
    const last = [...box.querySelectorAll(".msg.assistant")].pop();
    if (!last) return;
    const n = el("div", "mem-note");
    n.append(el("span", "", ev.added && ev.added.length ? "Đã cập nhật bộ nhớ" : "Đã xoá khỏi bộ nhớ"));
    n.title = [...(ev.added || []).map((x) => "+ " + x), ...(ev.removed || []).map((x) => "− " + x)].join("\n");
    const btn = el("button", "link", "Xem"); btn.type = "button"; btn.onclick = openMemory;
    n.appendChild(btn);
    last.appendChild(n);
  }

  /* ------------------------------------------------------- tải hội thoại -- */
  async function loadConv(id, m) {
    if (m && m !== mode) setMode(m);
    convId = id;
    ls.set("s4_conv", id ? JSON.stringify({ id, mode }) : null);
    box.innerHTML = "";
    setTitle();
    if (!id) { empty(); return; }
    try {
      const data = await api(`${base(mode, id)}/messages`);
      const msgs = data.messages;
      if (mode === "friendly") { renderFriendly(msgs); return; }
      if (!msgs.length) empty();
      msgs.forEach((x, i) => {
        if (x.role === "user") userMsg(x.content);
        else strictMsg(x, i !== msgs.length - 1);   // thẻ cũ bị khoá, chỉ thẻ cuối bấm được
      });
      scroll();
    } catch (_) { convId = null; ls.set("s4_conv", null); setTitle(); empty(); }
  }

  /* ------------------------------ danh sách hội thoại (menu ⋯, xoá tất cả) */
  let openMenu = null;
  const closeMenu = () => { if (openMenu) { openMenu.remove(); openMenu = null; } };
  document.addEventListener("click", closeMenu);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeMenu(); });

  function download(c, format) {
    const a = el("a"); a.href = `${base(c.mode, c.id)}/export?format=${format}`; a.download = "";
    document.body.appendChild(a); a.click(); a.remove();
  }

  function renameInline(row, c, btn) {
    const inp = el("input", "conv-rename"); inp.value = c.title; inp.maxLength = 60;
    let done = false;
    const finish = async (save) => {
      if (done) return; done = true;
      const t = inp.value.trim();
      if (save && t && t !== c.title) { try { await api(base(c.mode, c.id), { title: t }, "PATCH"); } catch (e) { alert("Lỗi: " + e.message); } }
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
      await api(base(c.mode, c.id), null, "DELETE");
      if (c.id === convId) await loadConv(null);
    } catch (e) { alert("Lỗi: " + e.message); }
    refreshList();
  }

  async function refreshList() {
    try { convs = (await api("/s4/conversations")).conversations; } catch (_) { return; }
    const nav = $("conv-list");
    nav.innerHTML = "";
    convs.forEach((c) => {
      const row = el("div", "conv-item" + (c.id === convId ? " active" : "") + (c.pinned ? " pinned" : ""));
      const b = el("button", "conv-open", (c.pinned ? "📌 " : "") + c.title);
      b.type = "button"; b.title = c.title;
      b.onclick = async () => { if (sending) return; await loadConv(c.id, c.mode); refreshList(); };
      b.ondblclick = () => renameInline(row, c, b);
      const tag = el("span", "mode-tag " + c.mode, c.mode === "friendly" ? "Friendly" : "Strict");
      const m = el("button", "conv-more", "⋯");
      m.type = "button"; m.title = "Tuỳ chọn"; m.setAttribute("aria-label", "Tuỳ chọn hộp thoại");
      m.onclick = (e) => {
        e.stopPropagation(); closeMenu();
        const menu = el("div", "conv-menu");
        const item = (label, fn, cls) => { const i = el("button", "conv-menu-item " + (cls || ""), label); i.type = "button"; i.onclick = (ev) => { ev.stopPropagation(); closeMenu(); fn(); }; menu.appendChild(i); };
        item(c.pinned ? "Bỏ ghim" : "Ghim", async () => {
          try { await api(base(c.mode, c.id), { pinned: !c.pinned }, "PATCH"); } catch (e) { alert("Lỗi: " + e.message); }
          refreshList();
        });
        item("Xuất Markdown", () => download(c, "md"));
        item("Xuất JSON", () => download(c, "json"));
        item("Xuất PDF", () => window.open(`${base(c.mode, c.id)}/export?format=pdf`, "_blank"));
        item("Đổi tên", () => renameInline(row, c, b));
        item("Xoá", () => removeConv(c), "danger");
        row.appendChild(menu); openMenu = menu;
      };
      row.append(b, tag, m);
      nav.appendChild(row);
    });
    $("clear-all").hidden = !convs.length;
    setTitle();
  }

  /* --------------------------------------------------------------- gửi --- */
  function statusLine(text) {
    const s = el("div", "status");
    const t = el("span", "", text);
    s.append(el("span", "spinner"), t);
    s.setText = (x) => { t.textContent = x; };
    return s;
  }

  function setBusy(on) {
    sending = on;
    $("send").textContent = on && mode === "friendly" ? "Dừng" : "Gửi";
    $("send").disabled = on && mode !== "friendly";   // Friendly: nút thành "Dừng"
  }

  async function sendStrict(text, replyTo) {
    const status = statusLine("Đang xử lý…");
    box.appendChild(status); scroll();
    try {
      const body = { text, conversation_id: convId };
      if (replyTo) body.reply_to = replyTo;
      const r = await api("/chat", body);
      convId = r.conversation_id; ls.set("s4_conv", JSON.stringify({ id: convId, mode: "strict" }));
      status.remove();
      strictMsg(r, false);
    } catch (e) {
      status.remove();
      const w = el("div", "msg assistant");
      w.appendChild(el("div", "bubble err", "Lỗi: " + e.message));
      box.appendChild(w);
    }
  }

  /* Một lượt Friendly qua SSE. Trả về khi câu trả lời xong (done/error/dừng); luồng vẫn đọc tiếp để nhận
     sự kiện "memory" (bộ nhớ cập nhật ở nền) mà không giữ nút Gửi. */
  function sendFriendly(payload) {
    return new Promise((resolve) => {
      let settled = false;
      const finish = () => { if (!settled) { settled = true; resolve(); } };
      const status = statusLine("Đang gửi…");
      box.appendChild(status); scroll();
      let wrap = null, bubble = null, raw = "", failed = false, raf = 0;
      const paint = () => { raf = 0; if (bubble) { bubble.innerHTML = md(visible(raw)); scroll(); } };
      const ensureBubble = () => {
        if (!bubble) {
          status.remove();
          wrap = el("div", "msg assistant");
          bubble = el("div", "bubble md");
          wrap.appendChild(bubble); box.appendChild(wrap);
        }
      };
      const fail = (msg) => {
        failed = true; status.remove();
        if (wrap) wrap.remove();
        const w = el("div", "msg assistant");
        w.appendChild(el("div", "bubble err", "Lỗi: " + msg));
        box.appendChild(w); finish();
      };
      const ctl = new AbortController();
      abortCtl = ctl;
      (async () => {
        try {
          const res = await fetch("/s4/chat", {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal: ctl.signal,
          });
          if (res.status === 401) { toLogin(); return; }
          if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(typeof d.detail === "string" ? d.detail : res.statusText); }
          const reader = res.body.getReader();
          const dec = new TextDecoder();
          let buf = "", myConv = null;
          for (;;) {
            const { value, done } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream: true });
            let k;
            while ((k = buf.indexOf("\n\n")) >= 0) {
              const line = buf.slice(0, k); buf = buf.slice(k + 2);
              if (!line.startsWith("data: ")) continue;
              const ev = JSON.parse(line.slice(6));
              if (ev.type === "meta") {
                myConv = ev.conversation_id;
                const isNew = convId !== myConv;
                convId = myConv; ls.set("s4_conv", JSON.stringify({ id: convId, mode: "friendly" }));
                if (isNew) refreshList();
              } else if (ev.type === "queue") status.setText("Đang chờ tới lượt (còn " + ev.position + " lượt trước bạn)…");
              else if (ev.type === "start") status.setText("AI đang trả lời…");
              else if (ev.type === "thinking") status.setText("AI đang suy nghĩ…");
              else if (ev.type === "delta") { ensureBubble(); raw += ev.text; if (!raf) raf = requestAnimationFrame(paint); }
              else if (ev.type === "restart") {
                raw = ""; if (wrap) wrap.remove(); wrap = bubble = null;
                box.appendChild(status); status.setText("Đang viết lại câu trả lời…");
              } else if (ev.type === "replace") { ensureBubble(); raw = ev.text; paint(); }
              else if (ev.type === "error") fail(ev.message);
              else if (ev.type === "done") {
                if (convId === myConv) await loadConv(convId, "friendly");   // vẽ lại: nút, phiên bản, lựa chọn
                finish();
              } else if (ev.type === "memory" && convId === myConv && mode === "friendly") memoryNote(ev);
            }
          }
          if (!settled && !failed) {
            if (bubble) { status.remove(); await loadConv(convId, "friendly"); finish(); }
            else fail("AI không trả lời");
          }
        } catch (e) {
          if (e.name === "AbortError") {
            status.remove();
            if (wrap) wrap.appendChild(el("div", "stopped-note", "(đã dừng)"));
            finish();
          } else if (!settled) fail(e.message);
        } finally {
          if (abortCtl === ctl) abortCtl = null;
          finish();
        }
      })();
    });
  }

  async function send(text, replyTo, extra) {
    const regen = !!(extra && extra.regenerate_of);
    if (sending || (!regen && !text.trim())) return;
    setBusy(true);
    if (box.querySelector(".empty")) box.innerHTML = "";
    box.querySelectorAll(".choice-item,.choice-custom-btn,.choice-custom-input").forEach((x) => (x.disabled = true));
    if (!regen) userMsg(text);
    try {
      if (mode === "friendly") await sendFriendly({ text, conversation_id: convId, ...(extra || {}) });
      else await sendStrict(text, replyTo);
    } finally {
      setBusy(false); scroll(); refreshList();
    }
  }

  $("composer").addEventListener("submit", (e) => {
    e.preventDefault();
    if (sending) { if (abortCtl) abortCtl.abort(); return; }
    const v = $("input").value;
    $("input").value = "";
    send(v);
  });
  $("input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (!sending) $("composer").requestSubmit(); }
  });
  $("new-chat").onclick = async () => { if (sending) return; await loadConv(null); refreshList(); };
  $("clear-all").onclick = async () => {
    if (!confirm("Xoá TẤT CẢ hộp thoại (cả Strict và Friendly)? Không khôi phục được.")) return;
    try { await api("/s4/conversations", null, "DELETE"); await loadConv(null); } catch (e) { alert("Lỗi: " + e.message); }
    refreshList();
  };
  $("reset-topic").onclick = async () => {
    if (!convId || sending || mode !== "strict") return;
    try {
      await api(`/conversations/${convId}/reset_facts`, {});
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
  if (innerWidth <= 760) $("sidebar").classList.add("hidden");
  $("toggle-sidebar").onclick = () => $("sidebar").classList.toggle("hidden");
  $("logout").onclick = async () => { try { await api("/s4/auth/logout", {}); } catch (_) {} toLogin(); };

  /* ---- cấu hình AI của Strict (System 3: GET/POST /config), chỉ hiện ở chế độ Strict ---- */
  const aiBadge = $("ai-badge"), cfgPanel = $("cfg-panel");
  function renderCfg() {
    const on = !!cfg.answer_llm;
    aiBadge.textContent = "AI " + (on ? "bật" : "tắt");
    aiBadge.className = "ai-badge " + (on ? "on" : "off");
    cfgPanel.innerHTML = "";
    const head = el("div", "cfg-main");
    const lab = el("div"); lab.append(el("b", "", "Trả lời bằng AI"), el("small", "", "Diễn giải điều kiện, so sánh. Tắt thì trả nguyên văn dữ liệu."));
    const sw = el("label", "switch"), cb = el("input"), knob = el("span");
    cb.type = "checkbox"; cb.checked = on; cb.disabled = !cfg.dev;
    cb.onchange = () => saveCfg({ answer_llm: cb.checked });
    sw.append(cb, knob); head.append(lab, sw); cfgPanel.appendChild(head);
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
    if (!cfg.dev) adv.appendChild(el("div", "cfg-note", "Chỉ xem. Đổi cấu hình cần chạy server với S3_DEV=1 và tài khoản dev."));
    cfgPanel.appendChild(adv);
  }
  async function loadCfg() {
    try { cfg = await api("/config"); renderCfg(); modelName(); } catch (_) { aiBadge.textContent = "AI: ?"; }
  }
  async function saveCfg(patch) {
    try { cfg = await api("/config", patch); } catch (e) { alert("Lỗi: " + e.message); }
    renderCfg();
  }
  aiBadge.onclick = (e) => { e.stopPropagation(); cfgPanel.hidden = !cfgPanel.hidden; if (!cfgPanel.hidden) loadCfg(); };
  document.addEventListener("click", (e) => { if (!cfgPanel.hidden && !cfgPanel.contains(e.target)) cfgPanel.hidden = true; });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cfgPanel.hidden = true; });

  /* ---- Cài đặt System 4 (chỉ dev): Lưu / Đặt làm mặc định / Về mặc định; tải lại trang để áp dụng ---- */
  const setModal = $("settings"), setBody = $("settings-body"), setNote = $("settings-note");
  let specs = [];

  const KINDS = [["block", "Chặn"], ["instruct", "Lời dặn"], ["replace", "Thay câu trả lời"]];
  function rulesEditor(s) {
    const wrap = el("div", "rules-editor"); wrap.dataset.rules = s.key;
    const list = el("div", "rules-list");
    const addRow = (r) => {
      const row = el("div", "rule-row");
      const on = el("input", "r-on"); on.type = "checkbox"; on.checked = r.enabled !== false; on.title = "Bật / tắt luật";
      const name = el("input", "r-name"); name.type = "text"; name.placeholder = "Tên luật"; name.value = r.name || "";
      const kind = el("select", "r-kind");
      KINDS.forEach(([v, l]) => { const o = el("option", "", l); o.value = v; o.selected = v === r.kind; kind.appendChild(o); });
      const del = el("button", "icon-btn", "✕"); del.type = "button"; del.title = "Xoá luật"; del.onclick = () => row.remove();
      const match = el("input", "r-match"); match.type = "text"; match.value = r.match || "";
      match.placeholder = "Cụm từ để khớp, cách nhau bởi | (để trống = luôn áp dụng, chỉ cho Lời dặn)";
      const msg = el("textarea", "r-msg"); msg.rows = 2; msg.value = r.message || "";
      msg.placeholder = "Chặn: câu trả lời cố định · Lời dặn: quy tắc cho AI · Thay: câu thay thế. {business} = tên doanh nghiệp";
      const head = el("div", "rule-head"); head.append(on, name, kind, del);
      row.append(head, match, msg); list.appendChild(row);
    };
    (s.value || []).forEach(addRow);
    const add = el("button", "btn-ghost", "+ Thêm luật"); add.type = "button";
    add.onclick = () => addRow({ enabled: true, kind: "instruct" });
    wrap.append(list, add);
    return wrap;
  }
  const readRules = (wrap) => [...wrap.querySelectorAll(".rule-row")].map((row) => ({
    name: row.querySelector(".r-name").value.trim(), enabled: row.querySelector(".r-on").checked,
    kind: row.querySelector(".r-kind").value, match: row.querySelector(".r-match").value.trim(),
    message: row.querySelector(".r-msg").value.trim(),
  }));
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

  function fieldInput(s) {
    if (s.type === "rules") return rulesEditor(s);
    let inp;
    if (s.type === "bool") {
      const sw = el("label", "switch"); inp = el("input"); inp.type = "checkbox"; inp.checked = !!s.value;
      sw.append(inp, el("span")); sw.dataset.key = s.key; inp.dataset.key = s.key;
      return sw;
    }
    if (s.type === "choice") {
      inp = el("select");
      s.choices.forEach((c) => { const o = el("option", "", c); o.value = c; o.selected = c === s.value; inp.appendChild(o); });
    } else if (s.type === "text") {
      inp = el("textarea"); inp.value = s.value;
    } else {
      inp = el("input"); inp.type = s.type === "int" || s.type === "float" ? "number" : "text"; inp.value = s.value;
      if (s.type === "int") inp.step = "1";
      if (s.type === "float") inp.step = "0.05";
      if (s.min !== undefined) inp.min = s.min;
      if (s.max !== undefined) inp.max = s.max;
    }
    inp.dataset.key = s.key;
    return inp;
  }

  function renderSettings(list) {
    specs = list;
    setBody.innerHTML = "";
    const groups = {};
    list.forEach((s) => { (groups[s.group] = groups[s.group] || []).push(s); });
    Object.entries(groups).forEach(([g, items]) => {
      const sec = el("section", "set-group");
      sec.appendChild(el("h3", "", g));
      items.forEach((s) => {
        const row = el("div", "set-row" + (s.type === "text" || s.type === "rules" ? " wide" : ""));
        const lab = el("div");
        const name = el("b", "", s.label);
        lab.appendChild(name);
        if (s.overridden) lab.appendChild(el("span", "over", "đã đổi"));
        const def = s.type === "bool" ? (s.default ? "bật" : "tắt") : s.type === "rules" ? s.default.length + " luật"
          : (String(s.default) || "(trống)");
        lab.appendChild(el("small", "", (s.help ? s.help + " " : "") + "Mặc định: " + (def.length > 60 ? def.slice(0, 60) + "…" : def)));
        row.append(lab, fieldInput(s));
        sec.appendChild(row);
      });
      setBody.appendChild(sec);
    });
  }

  function formValues() {
    const out = {};
    setBody.querySelectorAll("input[data-key],select[data-key],textarea[data-key]").forEach((i) => {
      const s = specs.find((x) => x.key === i.dataset.key);
      let v = s.type === "bool" ? i.checked : i.value;
      if (s.type === "int" || s.type === "float") v = i.value === "" ? NaN : Number(i.value);
      out[s.key] = v;
    });
    setBody.querySelectorAll("[data-rules]").forEach((w) => { out[w.dataset.rules] = readRules(w); });
    return out;
  }

  function note(msg, bad) {
    setNote.innerHTML = "";
    setNote.className = "set-note" + (bad ? " bad" : "");
    setNote.appendChild(el("span", "", msg));
    if (!bad) { const r = el("button", "btn-ghost", "Tải lại trang"); r.type = "button"; r.onclick = () => location.reload(); setNote.appendChild(r); }
    setNote.hidden = false;
  }

  async function settingsCall(url, body, okMsg) {
    try { const r = await api(url, body); renderSettings(r.settings); note(okMsg); } catch (e) { note(e.message, true); }
  }

  $("open-settings").onclick = async () => {
    setNote.hidden = true;
    try { renderSettings((await api("/s4/settings")).settings); setModal.hidden = false; } catch (e) { alert("Lỗi: " + e.message); }
  };
  $("settings-close").onclick = () => { setModal.hidden = true; };
  setModal.addEventListener("click", (e) => { if (e.target === setModal) setModal.hidden = true; });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { setModal.hidden = true; memModal.hidden = true; } });
  $("settings-save").onclick = () => {
    const vals = formValues(), changed = {};
    specs.forEach((s) => { if (!same(vals[s.key], s.value)) changed[s.key] = vals[s.key]; });
    if (!Object.keys(changed).length) { note("Không có thay đổi nào.", true); return; }
    settingsCall("/s4/settings", { values: changed }, "Đã lưu. Tải lại trang để áp dụng.");
  };
  $("settings-default").onclick = () => {
    const vals = formValues(), nd = {};
    specs.forEach((s) => { if (!same(vals[s.key], s.default)) nd[s.key] = vals[s.key]; });
    if (!Object.keys(nd).length) { note("Các giá trị đang hiện đã là mặc định.", true); return; }
    if (!confirm(`Ghi ${Object.keys(nd).length} giá trị đang hiện vào config.py làm mặc định mới? (config.py cũ được giữ ở config.py.bak)`)) return;
    settingsCall("/s4/settings/default", { values: nd }, "Đã ghi vào config.py. Tải lại trang để áp dụng.");
  };
  $("settings-reset").onclick = () => {
    const keys = specs.filter((s) => s.overridden).map((s) => s.key);
    if (!keys.length) { note("Không có giá trị nào đang khác mặc định.", true); return; }
    if (!confirm(`Bỏ ${keys.length} giá trị đã lưu, quay về mặc định trong config.py?`)) return;
    settingsCall("/s4/settings/reset", { keys }, "Đã về mặc định. Tải lại trang để áp dụng.");
  };

  /* ---- Bộ nhớ của mỗi người (Friendly): chế độ Tự động / Chỉ khi tôi bảo, xem và xoá từng điều ---- */
  const memModal = $("memory");
  function renderMemory(d) {
    document.querySelectorAll('input[name="mem-mode"]').forEach((r) => { r.checked = r.value === d.mode; });
    const ul = $("memory-list");
    ul.innerHTML = "";
    if (!d.items.length) ul.appendChild(el("li", "mem-empty", "Chưa nhớ điều gì."));
    d.items.forEach((m) => {
      const li = el("li");
      li.appendChild(el("span", "", m.text));
      li.appendChild(actionBtn("✕", "Quên điều này", async () => {
        try { await api("/s4/memory/" + m.id, null, "DELETE"); renderMemory(await api("/s4/memory")); } catch (e) { alert("Lỗi: " + e.message); }
      }));
      ul.appendChild(li);
    });
    $("memory-clear").disabled = !d.items.length;
  }
  async function openMemory() {
    try { renderMemory(await api("/s4/memory")); memModal.hidden = false; } catch (e) { alert("Lỗi: " + e.message); }
  }
  document.querySelectorAll('input[name="mem-mode"]').forEach((r) => {
    r.onchange = async () => { try { renderMemory(await api("/s4/memory/mode", { mode: r.value })); } catch (e) { alert("Lỗi: " + e.message); } };
  });
  $("memory-clear").onclick = async () => {
    if (!confirm("Xoá toàn bộ bộ nhớ? AI sẽ không còn nhớ gì về bạn.")) return;
    try { await api("/s4/memory", null, "DELETE"); renderMemory(await api("/s4/memory")); } catch (e) { alert("Lỗi: " + e.message); }
  };
  $("open-memory").onclick = openMemory;
  $("memory-close").onclick = () => { memModal.hidden = true; };
  memModal.addEventListener("click", (e) => { if (e.target === memModal) memModal.hidden = true; });

  /* ---------------------------------------------------------- khởi động -- */
  (async function init() {
    try { pub = await api("/s4/public"); } catch (_) { pub = {}; }
    if (!pub.user) { toLogin(); return; }
    me = pub.user;
    document.title = pub.app_title || "Instant Specialist";
    const nameEl = $("user-name");
    nameEl.textContent = me.username;
    nameEl.appendChild(el("span", "role-tag", me.role === "dev" ? "· dev" : "· user"));
    $("open-settings").hidden = me.role !== "dev";
    let saved = null;
    try { saved = JSON.parse(ls.get("s4_conv") || "null"); } catch (_) {}
    setMode(saved ? saved.mode : (ls.get("s4_mode") || pub.default_mode));
    loadCfg();
    await loadConv(saved ? saved.id : null, saved ? saved.mode : null);
    refreshList();
  })();
})();

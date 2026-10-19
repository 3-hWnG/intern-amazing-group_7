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
  let domains = [], domainId = 2;   // domain đang dùng (domain 1 = Thủ tục = Strict/System 3)
  let convId = null;
  let sending = false, abortCtl = null;
  let webOn = false;   // nút "Tìm web" (chỉ DuckDuckGo, không qua bộ dữ liệu); chỉ giữ trong phiên trang
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
  const base = (m, id) => (m === "strict" ? `/conversations/${id}` : `/s4/conversations/${id}`);   // đổi tên / ghim
  const sbase = (m, id) => (m === "strict" ? `/s4/strict/${id}` : `/s4/conversations/${id}`);   // tin nhắn, xoá, xuất (Strict có phiên bản)

  /* ------------------------------------------------------------ chế độ ---- */
  function setMode(m) {
    mode = m === "friendly" ? "friendly" : "strict";
    ls.set("s4_mode", mode);
    document.body.dataset.mode = mode;
    modelName();
    $("input").placeholder = mode === "friendly" ? "Nhắn trong «" + domainName() + "»…" : "Nhập câu hỏi về thủ tục…";
    $("cfg-panel").hidden = true;
  }

  /* ---- domain: thanh chọn (ghim) + ô chọn các domain còn lại ---- */
  const domainName = (id) => { const d = domains.find((x) => x.id === (id == null ? domainId : id)); return d ? d.name : "Friendly"; };
  function setDomain(id) {
    const d = domains.find((x) => x.id === id) || domains[0];
    if (!d) return;
    domainId = d.id;
    ls.set("s4_domain", String(domainId));
    document.body.dataset.domain = String(domainId);
    const s3 = d.engine === "strict" && d.data_mode !== "s4";   // Thủ tục ở chế độ System 4 = pipeline Friendly trên dữ liệu tải lên
    setMode(s3 ? "strict" : "friendly");
    renderDomainBar();
    $("attach").style.display = d.can_upload && !s3 ? "" : "none";   // chế độ System 3 không dùng tệp tải lên (tải ở Quản lý lĩnh vực)
    loadDatasets();
  }
  function renderDomainBar() {
    const bar = $("domain-bar"), more = $("domain-more");
    bar.innerHTML = ""; more.innerHTML = "";
    const pinned = domains.filter((d) => d.pinned || d.id === domainId), rest = domains.filter((d) => !pinned.includes(d));
    pinned.forEach((d) => {
      const b = el("button", "", d.name); b.type = "button"; b.dataset.domain = String(d.id);
      b.title = (d.kind === "hard" ? "Lĩnh vực cứng" : "Lĩnh vực mềm") + (d.locked ? " · chỉ cán bộ" : "") + (d.guardrail ? "\nGuardrail: " + d.guardrail : "");
      b.setAttribute("aria-pressed", String(d.id === domainId));
      b.onclick = () => switchDomain(d.id);
      if (d.id !== domainId) {   // dấu × nhỏ: ẩn domain khỏi thanh (vẫn còn trong ô "Khác…" và trang Lĩnh vực)
        const x = el("span", "dom-x", "×"); x.title = "Ẩn lĩnh vực này khỏi thanh chọn"; x.setAttribute("role", "button");
        x.onclick = async (e) => {
          e.stopPropagation();
          try { domains = (await api("/s4/domains/" + d.id + "/pin", { pinned: false })).domains; renderDomainBar(); } catch (err) { alert(err.message); }
        };
        b.appendChild(x);
      }
      bar.appendChild(b);
    });
    const first = el("option", "", "Khác…"); first.value = ""; more.appendChild(first);
    rest.forEach((d) => { const o = el("option", "", d.name); o.value = String(d.id); more.appendChild(o); });
    more.hidden = !rest.length;
    more.onchange = () => { const v = more.value; more.value = ""; if (v) switchDomain(Number(v)); };
  }
  async function switchDomain(id) {
    if (sending || id === domainId) return;
    setDomain(id);
    await loadConv(null);
    refreshList();
  }
  async function loadDomains() {
    try { domains = (await api("/s4/domains")).domains; } catch (_) { domains = []; }
    if (!domains.some((d) => d.id === domainId)) domainId = (domains[0] || {}).id || 2;
    renderDomainBar();
  }

  /* ---- bảng điều khiển lĩnh vực (hộp "Lĩnh vực"): dashboard.js — một chỗ cho lĩnh vực, dữ liệu, đường nhanh, thống kê.
     app.js chỉ đưa cho nó các hàm dùng chung (S4Dash.init trong init()). ---- */
  let viewUser = false;   // dev / cán bộ bật "Xem như người dùng" trong bảng điều khiển
  const isStaff = () => !viewUser && !!me && (me.role === "dev" || me.role === "can_bo");
  async function afterDomainsChanged() {
    if (!domains.some((d) => d.id === domainId)) { setDomain((domains[0] || {}).id); await loadConv(null); refreshList(); }
    else {
      const before = mode;
      renderDomainBar(); setDomain(domainId);
      if (mode !== before) { await loadConv(null); refreshList(); }   // Thủ tục đổi nguồn System 3 <-> 4: hội thoại đang mở thuộc chế độ cũ
    }
  }
  const openDomainManager = (openId, openTab) => S4Dash.open(openId, openTab);
  $("open-domains").onclick = () => openDomainManager();

  function modelName() {
    $("model-name").textContent = mode === "friendly" ? (pub.friendly_model || "") : (cfg.model ? cfg.model + " · luật" : "");
  }

  function setTitle() {
    const c = convs.find((x) => x.id === convId);
    $("conv-title").textContent = c ? c.title : (pub.app_title || "Instant Specialist");
  }

  function empty() {
    box.innerHTML = mode === "friendly"
      ? '<div class="empty"><h2>Mình có thể giúp gì cho bạn?</h2><p>Lĩnh vực: ' + domainName() + '.</p></div>'
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
    if (m.node_id) {   // tính năng kiểu ChatGPT cho Strict (NV4): phiên bản, sao chép, tạo lại, 👍/👎
      const bar = el("div", "msg-actions");
      const nav = versionNav(m, strictSwitch); if (nav) bar.appendChild(nav);
      bar.appendChild(actionBtn("⧉", "Sao chép", (btn) => copyText(m.content || "", btn)));
      if (me && me.role === "dev") bar.appendChild(actionBtn("🔍", "Soi: kế hoạch và dấu vết System 3 cho câu trả lời này", () => S4Inspect.strict(m.node_id), "inspect"));
      if (m.kind !== "chitchat" || !String(m.content || "").startsWith("Đã bắt đầu chủ đề mới"))
        bar.appendChild(actionBtn("↻", "Tạo lại câu trả lời (phát lại các câu trước để System 3 dựng lại ngữ cảnh)", () => strictRedo(w, "regenerate", { node_id: m.node_id })));
      [[1, "👍", "Câu trả lời tốt"], [-1, "👎", "Câu trả lời chưa tốt"]].forEach(([v, label, title]) => {
        bar.appendChild(actionBtn(label, title, async (x) => {
          const val = m.feedback === v ? 0 : v;
          try { await api("/s4/strict/" + convId + "/feedback", { node_id: m.node_id, value: val }); } catch (e) { alert("Lỗi: " + e.message); return; }
          m.feedback = val; bar.querySelectorAll(".fb").forEach((y) => y.classList.remove("on")); if (val) x.classList.add("on");
          fbNote(w, val);
          reasonChips(w, "strict", val, (reason) => api("/s4/strict/" + convId + "/feedback", { node_id: m.node_id, value: -1, reason }));
        }, "fb" + (m.feedback === v ? " on" : "")));
      });
      w.appendChild(bar);
    }
    box.appendChild(w);
    return w;
  }

  /* Sau 👎: hàng nút chọn nhanh lý do (không bắt buộc). send(reason) gửi lại 👎 kèm lý do; lý do tự mất khi bỏ 👎 / đổi 👍. */
  const REASONS = {
    strict: [["wrong_proc", "Sai thủ tục"], ["wrong_number", "Sai số liệu"], ["no_clarify", "Không hỏi lại"], ["other", "Khác"]],
    friendly: [["wrong_info", "Sai thông tin"], ["off_topic", "Không đúng ý hỏi"], ["bad_format", "Dài / khó đọc"], ["other", "Khác"]],
  };
  /* D13: bấm 👍/👎 -> báo rõ cặp hỏi–đáp (đã che số) được giữ lại, kể cả khi xoá tài khoản */
  const FEEDBACK_NOTE = "Câu hỏi và câu trả lời (đã che số giấy tờ) được giữ để cải thiện hệ thống, kể cả khi bạn xoá tài khoản.";
  function fbNote(wrap, val) {
    const old = wrap.querySelector(".fb-note"); if (old) old.remove();
    if (val) wrap.appendChild(el("div", "fb-note muted small", FEEDBACK_NOTE));
  }
  function reasonChips(wrap, kind, val, send) {
    const old = wrap.querySelector(".fb-reason"); if (old) old.remove();
    if (val !== -1) return;
    const row = el("div", "fb-reason", "");
    row.appendChild(el("span", "muted small", "Vì sao? "));
    REASONS[kind].forEach(([key, label]) => {
      const b = el("button", "chip", label); b.type = "button";
      b.onclick = async () => { try { await send(key); } catch (e) { alert("Lỗi: " + e.message); return; }
        row.querySelectorAll(".chip").forEach((y) => y.classList.remove("on")); b.classList.add("on"); };
      row.appendChild(b);
    });
    wrap.appendChild(row);
  }

  function strictUser(m) {
    const w = el("div", "msg user");
    w.appendChild(el("div", "bubble", m.content));
    const bar = el("div", "msg-actions");
    const nav = versionNav(m, strictSwitch); if (nav) bar.appendChild(nav);
    bar.appendChild(actionBtn("✎", "Sửa tin nhắn", () => {
      if (sending) return;
      w.innerHTML = "";
      const ta = el("textarea", "edit-box"); ta.value = m.content; ta.rows = Math.min(8, m.content.split("\n").length + 1);
      const row = el("div", "edit-row");
      const cancel = el("button", "btn-ghost", "Huỷ"); cancel.type = "button"; cancel.onclick = () => loadConv(convId, "strict");
      const ok = el("button", "primary", "Gửi"); ok.type = "button";
      ok.onclick = () => { const v = ta.value.trim(); if (!v) return; strictRedo(w, "edit", { node_id: m.node_id, text: v }, v); };
      ta.onkeydown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ok.click(); } if (e.key === "Escape") cancel.click(); };
      row.append(cancel, ok); w.append(ta, row); ta.focus();
    }));
    w.appendChild(bar);
    box.appendChild(w);
  }

  function renderStrict(msgs) {
    box.innerHTML = "";
    if (!msgs.length) { empty(); return; }
    msgs.forEach((x, i) => { if (x.role === "user") strictUser(x); else strictMsg(x, i !== msgs.length - 1); });   // thẻ cũ bị khoá
    scroll();
  }

  async function strictSwitch(nid) {
    if (sending || !convId) return;
    try { renderStrict((await api("/s4/strict/" + convId + "/switch", { node_id: nid })).messages); } catch (e) { alert("Lỗi: " + e.message); }
  }

  /* sửa / tạo lại ở Strict: System 4 phát lại các câu trước vào nhánh mới rồi hỏi lại System 3 */
  async function strictRedo(w, action, body, newText) {
    if (sending) return;
    while (w.nextSibling) w.nextSibling.remove();
    w.remove();
    if (newText) userMsg(newText);
    setBusy(true);
    const status = statusLine(action === "edit" ? "Đang gửi câu đã sửa (phát lại các câu trước để System 3 dựng lại ngữ cảnh)…" : "Đang tạo lại câu trả lời (phát lại các câu trước)…");
    box.appendChild(status); scroll();
    try { renderStrict((await api("/s4/strict/" + convId + "/" + action, body)).messages); }
    catch (e) { status.remove(); const x = el("div", "msg assistant"); x.appendChild(el("div", "bubble err", "Lỗi: " + e.message)); box.appendChild(x); }
    finally { setBusy(false); refreshList(); }
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

  function versionNav(m, sw) {
    const go = sw || switchTo;
    const vs = m.versions || [m.id];
    if (vs.length < 2) return null;
    const i = vs.indexOf(m.id);
    const nav = el("span", "ver-nav");
    const prev = actionBtn("‹", "Phiên bản trước", () => go(vs[i - 1]));
    const next = actionBtn("›", "Phiên bản sau", () => go(vs[i + 1]));
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
    const srcs = (m.meta && m.meta.sources) || [];
    if (err) b.textContent = "Lỗi: " + m.content;
    else {
      const byN = {}, urlN = {}; srcs.forEach((s) => { byN[s.n] = s.record_id || s.url; if (s.url) urlN[s.n] = s.url; });
      /* [n] -> số nguồn bấm được (chỉ với số có trong danh sách nguồn của câu trả lời) */
      b.innerHTML = md(m.content).replace(/\[(\d{1,2})\]/g, (all, n) => byN[n] ? '<a class="cite" href="' + (urlN[n] ? urlN[n].replace(/"/g, "%22") + '" target="_blank" rel="noopener' : "#") + '" data-rec="' + (urlN[n] ? "" : byN[n]) + '">' + n + "</a>" : all);
      b.querySelectorAll("a.cite").forEach((a) => { if (a.dataset.rec) a.onclick = (e) => { e.preventDefault(); openRecord(+a.dataset.rec); }; });
    }
    w.appendChild(b);
    const consulted = (m.meta && m.meta.consulted) || [];
    if (srcs.length || consulted.length) {
      const row = el("div", "src-row");
      row.appendChild(el("span", "", srcs.length ? "Nguồn:" : "Đã tra cứu:"));
      (srcs.length ? srcs : consulted).forEach((s) => {
        const c = el("button", "src-chip", (s.n ? "[" + s.n + "] " : "") + s.title);
        c.type = "button"; c.title = s.title + " · " + s.dataset;
        if (s.url) c.onclick = () => window.open(s.url, "_blank", "noopener"); else if (s.record_id) c.onclick = () => openRecord(s.record_id); else c.disabled = true;   /* kết quả công cụ bảng: không có bản ghi riêng */
        row.appendChild(c);
      });
      w.appendChild(row);
    }
    if (m.status === "stopped") w.appendChild(el("div", "stopped-note", "(đã dừng)"));
    if (m.meta && m.meta.cached) w.appendChild(el("div", "stopped-note", "Câu trả lời có sẵn (đã được đánh giá hữu ích). Bấm ↻ để AI trả lời lại."));
    const choices = (m.meta && m.meta.choices) || [];
    if (choices.length) w.appendChild(clarifyCard({ question: "Chọn nhanh:", options: choices, allow_free_text: true }, null, !isLast));
    const bar = el("div", "msg-actions");
    const nav = versionNav(m); if (nav) bar.appendChild(nav);
    if (!err) bar.appendChild(actionBtn("⧉", "Sao chép", (btn) => copyText(m.content, btn)));
    bar.appendChild(actionBtn("↻", "Tạo lại câu trả lời", () => regenerate(w, m)));
    if (me && me.role === "dev") bar.appendChild(actionBtn("🔍", "Soi: AI đã tìm gì, nhận lời dặn gì, nghĩ gì, kiểm soát nào đã chạy", () => S4Inspect.friendly(m.id, true), "inspect"));
    else if (m.meta && m.meta.specialist) bar.appendChild(actionBtn("Vì sao?", "Vì sao có câu trả lời này: nguồn và độ liên quan", () => S4Inspect.friendly(m.id, false), "deeper"));
    if (!err) {
      const fb = (v, label, title) => {
        const btn = actionBtn(label, title, async (x) => {
          const val = m.feedback === v ? 0 : v;
          try { await api("/s4/conversations/" + convId + "/messages/" + m.id + "/feedback", { value: val }); } catch (e) { alert("Lỗi: " + e.message); return; }
          m.feedback = val;
          bar.querySelectorAll(".fb").forEach((y) => y.classList.remove("on"));
          if (val) x.classList.add("on");
          fbNote(w, val);
          reasonChips(w, "friendly", val, (reason) => api("/s4/conversations/" + convId + "/messages/" + m.id + "/feedback", { value: -1, reason }));
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
      if (m.meta.retrieval) notes.push("tìm: " + m.meta.retrieval.candidates_n + " ứng viên" + (m.meta.retrieval.reranked ? ", đã xếp hạng lại" : ", không xếp hạng lại"));
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
      const data = await api(`${sbase(mode, id)}/messages`);
      if (mode === "friendly") renderFriendly(data.messages); else renderStrict(data.messages);
    } catch (_) { convId = null; ls.set("s4_conv", null); setTitle(); empty(); }
  }

  /* ------------------------------ danh sách hội thoại (menu ⋯, xoá tất cả) */
  let openMenu = null;
  const closeMenu = () => { if (openMenu) { openMenu.remove(); openMenu = null; } };
  document.addEventListener("click", closeMenu);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeMenu(); });

  function download(c, format) {
    const a = el("a"); a.href = `${sbase(c.mode, c.id)}/export?format=${format}`; a.download = "";
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
      await api(sbase(c.mode, c.id), null, "DELETE");
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
      b.onclick = async () => { if (sending) return; if (c.domain_id && c.domain_id !== domainId) setDomain(c.domain_id); await loadConv(c.id, c.mode); refreshList(); };
      b.ondblclick = () => renameInline(row, c, b);
      const tag = el("span", "mode-tag " + c.mode, c.mode === "friendly" ? domainName(c.domain_id) : "Thủ tục");
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
        item("Xuất PDF", () => window.open(`${sbase(c.mode, c.id)}/export?format=pdf`, "_blank"));
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
    $("send").textContent = on ? "Dừng" : "Gửi";   // đang trả lời: nút thành "Dừng" (cả hai chế độ)
    $("send").disabled = false;
  }

  async function sendStrict(text, replyTo) {
    const status = statusLine("Đang xử lý…");
    box.appendChild(status); scroll();
    const ctl = new AbortController(); abortCtl = ctl;
    try {
      const body = { text, root: convId, websearch: webOn };
      if (replyTo) body.reply_to = replyTo;
      const res = await fetch("/s4/strict/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: ctl.signal });
      if (res.status === 401) { toLogin(); return; }
      const r = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof r.detail === "string" ? r.detail : res.statusText);
      convId = r.conversation_id; ls.set("s4_conv", JSON.stringify({ id: convId, mode: "strict" }));
      status.remove();
      await loadConv(convId, "strict");   // vẽ lại để có nút phiên bản / sao chép / tạo lại
    } catch (e) {
      status.remove();
      const w = el("div", "msg assistant");
      if (e.name === "AbortError") w.appendChild(el("div", "stopped-note", "(đã dừng chờ — System 3 vẫn trả lời ở nền, mở lại hội thoại để xem)"));
      else w.appendChild(el("div", "bubble err", "Lỗi: " + e.message));
      box.appendChild(w);
    } finally {
      if (abortCtl === ctl) abortCtl = null;
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
      if (mode === "friendly") await sendFriendly({ text, conversation_id: convId, websearch: webOn, domain_id: domainId, ...(extra || {}) });
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
      renderStrict((await api(`/s4/strict/${convId}/reset`, {})).messages);
    } catch (e) { alert("Lỗi: " + e.message); }
  };
  if (innerWidth <= 760) $("sidebar").classList.add("hidden");
  $("toggle-sidebar").onclick = () => $("sidebar").classList.toggle("hidden");
  $("web-toggle").onclick = () => { webOn = !webOn; const b = $("web-toggle"); b.setAttribute("aria-pressed", String(webOn)); b.classList.toggle("on", webOn); $("input").focus(); };
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
    if (s.options && s.options.length) {   // ô chọn model: xổ ra TẤT CẢ model trong Ollama (datalist chỉ hiện mục khớp chữ đang gõ)
      inp = el("select");
      const names = s.options.slice();
      if (s.value && !names.includes(s.value)) names.unshift(s.value);
      if (s.optional) { const o = el("option", "", "(dùng model trả lời nhanh)"); o.value = ""; o.selected = !s.value; inp.appendChild(o); }
      names.forEach((m) => { const o = el("option", "", s.options.includes(m) ? m : m + " (chưa có trong Ollama)"); o.value = m; o.selected = m === s.value; inp.appendChild(o); });
    } else if (s.type === "choice") {
      inp = el("select");
      s.choices.forEach((c) => { const o = el("option", "", c); o.value = c; o.selected = c === s.value; inp.appendChild(o); });
    } else if (s.type === "text") {
      inp = el("textarea"); inp.value = s.value;
    } else if (s.secret) {   // khoá bí mật: server không gửi giá trị; để trống = giữ nguyên khoá đã lưu
      inp = el("input"); inp.type = "password"; inp.value = ""; inp.autocomplete = "new-password";
      inp.placeholder = s.is_set ? "đã lưu — để trống để giữ nguyên" : "chưa có";
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
      if (s.secret && !i.value) return;   // khoá bí mật để trống: không gửi (giữ khoá đã lưu)
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
    try { const r = await api(url, body); renderSettings(r.settings); note(okMsg.replace("Tải lại trang để áp dụng.", "Đang tải lại trang…")); setTimeout(() => location.reload(), 600); } catch (e) { note(e.message, true); }
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
    specs.forEach((s) => { if (vals[s.key] !== undefined && !same(vals[s.key], s.value)) changed[s.key] = vals[s.key]; });   // undefined = khoá bí mật để trống
    if (!Object.keys(changed).length) { note("Không có thay đổi nào.", true); return; }
    settingsCall("/s4/settings", { values: changed }, "Đã lưu. Tải lại trang để áp dụng.");
  };
  $("settings-default").onclick = () => {
    const vals = formValues(), nd = {};
    specs.forEach((s) => { if (vals[s.key] !== undefined && !s.secret && !same(vals[s.key], s.default)) nd[s.key] = vals[s.key]; });   // khoá bí mật không vào config.py
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

  /* ---- NV3: Dữ liệu của tôi — tải lên (+), bật/tắt, xem, xoá; chế độ Chuyên gia tự bật khi có bộ dữ liệu đang bật ---- */
  let ds = { datasets: [], active: { datasets: 0, warnings: [] }, quota: {} }, dsTimer = null;
  const pending = new Map();   // id bộ dữ liệu vừa tải lên -> tên tệp (để báo khi xử lý xong)
  const fmtSize = (b) => (b < 1024 * 1024 ? Math.max(1, Math.round(b / 1024)) + " KB" : (b / 1048576).toFixed(b < 10485760 ? 1 : 0) + " MB");
  const KIND = { table: "Bảng (đã khớp cấu trúc)", rows: "Bảng (không khớp, lưu dạng dòng chữ)", text: "Văn bản", mixed: "Bảng + văn bản" };

  async function loadDatasets() {
    try { ds = await api("/s4/datasets?domain_id=" + domainId); } catch (_) { return; }
    $("attach").style.display = ds.can_upload && mode !== "strict" ? "" : "none";
    renderSpecBadge();
    ds.datasets.forEach((d) => {
      if (!pending.has(d.id)) return;
      if (d.status === "ready") { uploadPill(pending.get(d.id), "Đã sẵn sàng · " + d.n_records + " bản ghi" + (d.active ? " · Chuyên gia đã bật" : " · đang tắt (vượt giới hạn)"), "ok", 6000); pending.delete(d.id); }
      else if (d.status === "error") { uploadPill(pending.get(d.id), d.message, "failed", 12000); pending.delete(d.id); }
      else uploadPill(pending.get(d.id), d.message || "Đang xử lý…", "pending");
    });
    clearTimeout(dsTimer);
    if (ds.datasets.some((d) => d.status === "queued" || d.status === "processing")) dsTimer = setTimeout(loadDatasets, 2000);
  }

  function renderSpecBadge() {
    const n = ds.active.datasets, b = $("spec-badge");
    b.textContent = n ? "Chuyên gia · " + n + " bộ dữ liệu" : "AI chung";
    b.classList.toggle("on", !!n);
    b.title = n ? "AI chỉ trả lời từ " + n + " bộ dữ liệu đang bật. Bấm để quản lý." : "Chưa bật bộ dữ liệu nào: AI trò chuyện chung. Bấm để tải / bật dữ liệu.";
  }

  function uploadPill(name, text, cls, hideAfter) {
    const box2 = $("upload-status");
    let p = [...box2.children].find((x) => x.dataset.name === name);
    if (!p) { p = el("div", "file-pill"); p.dataset.name = name; box2.appendChild(p); }
    p.className = "file-pill " + (cls || "");
    p.innerHTML = "";
    p.append(el("span", "name", name), el("span", "meta", text));
    const x = el("button", "rm", "✕"); x.type = "button"; x.title = "Ẩn"; x.onclick = () => { p.remove(); box2.hidden = !box2.children.length; };
    p.appendChild(x);
    box2.hidden = false;
    if (hideAfter) setTimeout(() => { p.remove(); box2.hidden = !box2.children.length; }, hideAfter);
  }

  function uploadOne(file, did) {
    return new Promise((resolve, reject) => {
      const x = new XMLHttpRequest();
      x.open("POST", "/s4/datasets");
      x.upload.onprogress = (e) => { if (e.lengthComputable) uploadPill(file.name, "Đang tải lên " + Math.round((e.loaded / e.total) * 100) + "%", "pending"); };
      x.onload = () => {
        let d = {}; try { d = JSON.parse(x.responseText); } catch (_) {}
        if (x.status === 401) { toLogin(); return; }
        if (x.status >= 200 && x.status < 300) resolve(d); else reject(new Error(typeof d.detail === "string" ? d.detail : x.statusText));
      };
      x.onerror = () => reject(new Error("Lỗi mạng"));
      const fd = new FormData(); fd.append("file", file); fd.append("domain_id", String(did || domainId)); x.send(fd);
    });
  }

  async function uploadFiles(files, did) {
    for (const f of files) {
      uploadPill(f.name, "Đang tải lên…", "pending");
      try { const r = await uploadOne(f, did); pending.set(r.dataset.id, f.name); uploadPill(f.name, "Đang chờ xử lý…", "pending"); }
      catch (e) { uploadPill(f.name, e.message, "failed", 12000); }
    }
    loadDatasets(); refreshPanels();
  }

  /* Dữ liệu nằm trong trình quản lý lĩnh vực: mỗi dòng lĩnh vực có nút "Dữ liệu" mở bảng riêng của lĩnh vực đó. */
  const panels = new Set();
  const refreshPanels = () => panels.forEach((p) => { if (p.isConnected) p.refresh(); else panels.delete(p); });

  function dsItem(d, refresh, canShare) {   // canShare: lĩnh vực mềm không riêng ai + dev / cán bộ -> nút "Dùng chung"
    const li = el("li");
    const sw = el("label", "switch"), cb = el("input"), knob = el("span");
    const mineDs = d.user_id === me.id || isStaff();
    cb.type = "checkbox"; cb.checked = d.active; cb.disabled = d.status !== "ready" || !mineDs;
    cb.title = d.status === "ready" ? (d.active ? "Đang bật: AI dùng bộ này" : "Đang tắt") : "Chờ xử lý xong";
    cb.onchange = async () => {
      try { await api("/s4/datasets/" + d.id, { active: cb.checked }, "PATCH"); }
      catch (e) { alert(e.message); cb.checked = !cb.checked; }
      refresh();
    };
    sw.append(cb, knob);
    const main = el("div", "ds-main");
    main.appendChild(el("div", "ds-name", d.name));
    main.appendChild(el("div", "ds-msg" + (d.status === "error" ? " err" : ""), d.message || d.status));
    if (d.status === "queued" || d.status === "processing") { const pg = el("div", "ds-progress"); const i = el("i"); i.style.width = d.progress + "%"; pg.appendChild(i); main.appendChild(pg); }
    main.appendChild(el("div", "ds-meta", [KIND[d.kind] || "", d.n_records ? d.n_records + " bản ghi" : "", fmtSize(d.size_bytes), d.filename,
      d.user_id !== me.id ? "dùng chung (" + (d.username || "dev") + ")" : d.shared ? "dùng chung với mọi người" : "", d.locked ? "chỉ cán bộ" : ""].filter(Boolean).join(" · ")));
    const act = el("div", "ds-actions");
    if (d.status === "ready") act.appendChild(actionBtn("Xem", "Xem các bản ghi", () => openRecords(d)));
    if (d.status === "ready") act.appendChild(actionBtn("Cách đọc", "Xem hệ thống đã đọc tệp thế nào: dòng tiêu đề, cột tiêu đề, bản ghi đầu", () => S4Inspect.reading(d.id)));
    if (canShare && d.user_id === me.id) act.appendChild(actionBtn(d.shared ? "Thôi dùng chung" : "Dùng chung", "Dùng chung: mọi người dùng được lĩnh vực này đều thấy và hỏi được bộ dữ liệu (chỉ đọc)", async () => {
      try { await api("/s4/datasets/" + d.id, { shared: !d.shared }, "PATCH"); } catch (e) { alert(e.message); }
      refresh();
    }));
    if (isStaff()) act.appendChild(actionBtn(d.locked ? "Mở khoá" : "Khoá", "Khoá: chỉ dev và cán bộ dùng bộ dữ liệu này", async () => {
      try { await api("/s4/datasets/" + d.id, { locked: !d.locked }, "PATCH"); } catch (e) { alert(e.message); }
      refresh();
    }));
    if (mineDs && (d.status === "error" || d.status === "ready")) act.appendChild(actionBtn("Xử lý lại", "Đọc lại tệp và tạo lại chỉ mục", async () => { try { await api("/s4/datasets/" + d.id + "/retry", {}); pending.set(d.id, d.filename); } catch (e) { alert(e.message); } refresh(); }));
    if (mineDs) act.appendChild(actionBtn("Xoá", "Xoá bộ dữ liệu", async () => {
      if (!confirm('Xoá bộ dữ liệu "' + d.name + '"? Không khôi phục được.')) return;
      try { await api("/s4/datasets/" + d.id, null, "DELETE"); } catch (e) { alert(e.message); }
      refresh();
    }));
    main.appendChild(act);
    li.append(sw, main);
    return li;
  }

  function dataPanel(dom, uploadedOnly) {   // uploadedOnly: chỉ tệp tải lên (lĩnh vực cứng có dữ liệu đồng bộ riêng, vd. ABI)
    const root = el("div", "dom-data");
    const quota = el("div", "quota"), warn = el("div", "data-warn"), list = el("ul", "data-list");
    const up = el("button", "primary", "+ Tải tệp lên"); up.type = "button";
    const fin = el("input"); fin.type = "file"; fin.multiple = true; fin.hidden = true;
    up.onclick = () => fin.click();
    fin.onchange = () => { const f = [...fin.files]; fin.value = ""; if (f.length) uploadFiles(f, dom.id); };
    root.append(quota, warn, list, up, fin);
    let timer = null;
    root.refresh = async () => {
      let st;
      try { st = await api("/s4/datasets?domain_id=" + dom.id + (uploadedOnly ? "&uploaded=1" : "")); } catch (_) { return; }
      const q = st.quota || {}, used = q.used || 0;
      quota.innerHTML = "";
      if (q.limit) {
        const pct = Math.min(100, (used / q.limit) * 100);
        const bar = el("div", "bar"); const fill = el("i", pct > 90 ? "full" : ""); fill.style.width = pct + "%"; bar.appendChild(fill);
        quota.append(bar, el("small", "", "Đã dùng " + fmtSize(used) + " / " + fmtSize(q.limit) + (pct > 90 ? " · sắp hết, hãy xoá bớt bộ dữ liệu cũ" : "")));
      } else quota.appendChild(el("small", "", "Đã dùng " + fmtSize(used) + " · tài khoản dev không giới hạn dung lượng"));
      warn.textContent = (st.active.warnings || []).join(" "); warn.hidden = !(st.active.warnings || []).length;
      fin.accept = (st.formats || []).join(",");
      up.hidden = !st.can_upload;
      list.innerHTML = "";
      if (!st.datasets.length) list.appendChild(el("li", "mem-empty", st.can_upload ? 'Chưa có bộ dữ liệu nào trong lĩnh vực này. Bấm "+ Tải tệp lên".' : "Lĩnh vực này chưa có bộ dữ liệu dùng chung."));
      st.datasets.forEach((d) => list.appendChild(dsItem(d, () => { root.refresh(); if (dom.id === domainId) loadDatasets(); }, st.domain && st.domain.can_share)));
      clearTimeout(timer);
      if (st.datasets.some((d) => d.status === "queued" || d.status === "processing")) timer = setTimeout(() => { if (root.isConnected) root.refresh(); }, 2000);
    };
    panels.add(root);
    root.refresh();
    return root;
  }

  /* xem bản ghi của một bộ dữ liệu (tìm + xem thêm) */
  let recState = null;
  function recCard(r) {
    const c = el("div", "rec-card");
    c.appendChild(el("b", "", r.title));
    const f = Object.entries(r.fields || {});
    c.appendChild(el("div", "rec-fields", f.length ? f.map(([k, v]) => k + ": " + v).join("\n") : r.text));
    c.appendChild(el("small", "", r.source));
    return c;
  }
  async function loadRecords(reset) {
    if (reset) { recState.offset = 0; $("records-list").innerHTML = ""; }
    try {
      const r = await api("/s4/datasets/" + recState.ds.id + "/records?offset=" + recState.offset + "&limit=50&q=" + encodeURIComponent(recState.q));
      r.records.forEach((x) => $("records-list").appendChild(recCard(x)));
      recState.offset += r.records.length;
      $("records-count").textContent = r.total + " bản ghi" + (recState.q ? " khớp \"" + recState.q + "\"" : "");
      $("records-more").hidden = recState.offset >= r.total;
    } catch (e) { alert(e.message); }
  }
  function openRecords(d) {
    recState = { ds: d, offset: 0, q: "" };
    $("records-title").textContent = d.name; $("records-q").value = "";
    $("records-modal").hidden = false; loadRecords(true);
  }
  let recQTimer = null;
  $("records-q").oninput = () => { clearTimeout(recQTimer); recQTimer = setTimeout(() => { recState.q = $("records-q").value.trim(); loadRecords(true); }, 300); };
  $("records-more").onclick = () => loadRecords(false);

  /* xem nguồn của câu trả lời */
  async function openRecord(id) {
    try {
      const r = await api("/s4/records/" + id);
      const body = $("source-body"); body.innerHTML = "";
      $("source-title").textContent = r.record.title;
      body.appendChild(el("div", "mem-help", "Bộ dữ liệu: " + r.dataset.name + " · " + r.record.source));
      const f = Object.entries(r.record.fields || {});
      if (f.length) {
        const t = el("table", "src-table");
        f.forEach(([k, v]) => { const tr = el("tr"); tr.append(el("th", "", k), el("td", "", v)); t.appendChild(tr); });
        body.appendChild(t);
      } else body.appendChild(el("div", "src-text", r.record.text));
      $("source-modal").hidden = false;
    } catch (e) { alert("Không mở được nguồn: " + e.message); }
  }

  $("attach").onclick = () => $("file-input").click();
  $("file-input").onchange = () => { const f = [...$("file-input").files]; $("file-input").value = ""; if (f.length) uploadFiles(f); };
  $("spec-badge").onclick = () => openDomainManager(domainId);
  [["records-close", "records-modal"], ["source-close", "source-modal"]].forEach(([b, m]) => {
    $(b).onclick = () => { $(m).hidden = true; };
    $(m).addEventListener("click", (e) => { if (e.target === $(m)) $(m).hidden = true; });
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") ["records-modal", "source-modal"].forEach((m) => { $(m).hidden = true; }); });
  /* kéo thả tệp vào khung chat (Friendly) */
  box.addEventListener("dragover", (e) => { if (mode === "friendly") e.preventDefault(); });
  box.addEventListener("drop", (e) => { if (mode !== "friendly") return; e.preventDefault(); const f = [...e.dataTransfer.files]; if (f.length) uploadFiles(f); });

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

  /* ---- Tài khoản & quyền riêng tư (G1.4, G1.7): dung lượng, đổi mật khẩu, xoá hội thoại / bộ nhớ / tài khoản ---- */
  const accModal = $("account");
  const mb = (n) => (n / 1048576).toLocaleString("vi-VN", { maximumFractionDigits: 1 }) + " MB";
  async function openAccount() {
    try {
      const d = await api("/s4/account"), u = d.usage;
      $("rules-only").checked = !!d.rules_only;
      $("account-ai").textContent = d.ai && d.ai.cpu_only ? "Máy đang chạy AI bằng CPU (" + (d.ai.why || "không có card đồ hoạ") + "): AI trả lời chậm." : "";
      $("account-usage").textContent = `Đã dùng ${mb(u.used)}` + (u.quota ? ` / ${mb(u.quota)}` : " (dev: không giới hạn)") +
        ` — dữ liệu tải lên ${mb(u.datasets)}, hội thoại Strict ${mb(u.strict)}, hội thoại Friendly ${mb(u.friendly)}.`;
      accModal.hidden = false;
    } catch (e) { alert("Lỗi: " + e.message); }
  }
  $("open-account").onclick = openAccount;
  async function setRulesOnly(on) {   // G3.3: theo tài khoản, lưu ở server
    try { const d = await api("/s4/account/prefs", { rules_only: on }); $("rules-only").checked = $("rules-only-banner").checked = d.rules_only; }
    catch (e) { alert("Lỗi: " + e.message); }
  }
  $("rules-only").onchange = (e) => setRulesOnly(e.target.checked);
  $("rules-only-banner").onchange = (e) => setRulesOnly(e.target.checked);
  $("account-close").onclick = () => { accModal.hidden = true; };
  accModal.addEventListener("click", (e) => { if (e.target === accModal) accModal.hidden = true; });
  $("account-password").onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    try { await api("/s4/account/password", { old_password: f.old_password.value, new_password: f.new_password.value }); f.reset(); alert("Đã đổi mật khẩu."); }
    catch (err) { alert("Lỗi: " + err.message); }
  };
  $("account-del-convs").onclick = async () => {
    if (!confirm("Xoá TẤT CẢ hội thoại (Strict và Friendly) của bạn? Không khôi phục được.")) return;
    try { await api("/s4/account/conversations", null, "DELETE"); await loadConv(null, mode); refreshList(); openAccount(); }
    catch (e) { alert("Lỗi: " + e.message); }
  };
  $("account-del-memory").onclick = async () => {
    if (!confirm("Xoá bộ nhớ (những điều AI nhớ về bạn và hồ sơ của chế độ Strict)?")) return;
    try { await api("/s4/account/memory", null, "DELETE"); alert("Đã xoá bộ nhớ."); } catch (e) { alert("Lỗi: " + e.message); }
  };
  $("account-delete").onsubmit = async (e) => {
    e.preventDefault();
    if (!confirm("Xoá tài khoản và toàn bộ dữ liệu của bạn? Không khôi phục được.")) return;
    try { await api("/s4/account", { password: e.target.password.value }, "DELETE"); toLogin(); }
    catch (err) { alert("Lỗi: " + err.message); }
  };

  /* ---------------------------------------------------------- khởi động -- */
  (async function init() {
    try { pub = await api("/s4/public"); } catch (_) { pub = {}; }
    if (!pub.user) { toLogin(); return; }
    me = pub.user;
    document.title = pub.app_title || "Instant Specialist";
    const nameEl = $("user-name");
    nameEl.textContent = me.username;
    nameEl.appendChild(el("span", "role-tag", "· " + ({ dev: "dev", can_bo: "cán bộ" }[me.role] || "người dân")));
    $("open-settings").hidden = me.role !== "dev";
    $("open-admin").hidden = me.role !== "dev";
    $("cpu-banner").hidden = !pub.cpu_mode;   // G3.3: máy không có card đồ hoạ
    $("rules-only-banner").checked = !!pub.rules_only;
    S4Dash.init({ api, el, me: () => me, domains: () => domains, setDomains: (d) => { domains = d; }, loadDomains, renderDomainBar,
                  afterDomainsChanged, switchDomain, domainId: () => domainId, dataPanel, openRecords,
                  setViewUser: (v) => { viewUser = v; refreshPanels(); } });
    let saved = null;
    try { saved = JSON.parse(ls.get("s4_conv") || "null"); } catch (_) {}
    await loadDomains();
    const wantMode = saved ? saved.mode : (ls.get("s4_mode") || pub.default_mode);
    const byMode = domains.find((d) => wantMode === "strict" ? d.engine === "strict" && d.data_mode !== "s4" : d.engine === "friendly");
    setDomain(Number(ls.get("s4_domain")) || (byMode || domains[0] || {}).id);
    if (saved && mode !== saved.mode) saved = null;   // domain đã chọn khác chế độ của hội thoại cũ (domain bị khoá…)
    loadCfg();
    await loadConv(saved ? saved.id : null, saved ? saved.mode : null);
    refreshList();
    if (new URLSearchParams(location.search).get("dash") === "1") openDomainManager();   // liên kết từ trang Quản trị
  })();
})();

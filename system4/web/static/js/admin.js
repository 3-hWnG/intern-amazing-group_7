/* System 4 — trang Quản trị (chỉ dev): tài khoản người dùng (+ hội thoại của từng người, chỉ xem) và Thử tìm kiếm.
   Dữ liệu Strict / ABI / bộ dữ liệu người dùng, đường nhanh và thống kê ở bảng điều khiển lĩnh vực (dashboard.js, nút "Lĩnh vực"). */
(function () {
  const $ = (id) => document.getElementById(id);
  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };
  const btn = (label, fn, cls, title) => {
    const b = el("button", cls || "btn-ghost", label); b.type = "button"; if (title) b.title = title;
    b.onclick = (e) => { e.stopPropagation(); fn(b); };
    return b;
  };
  async function api(url, body, method) {
    const res = await fetch(url, body || method ? { method: method || "POST", headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined } : undefined);
    if (res.status === 401) { location.href = "/s4/login"; throw new Error("Cần đăng nhập"); }
    const d = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof d.detail === "string" ? d.detail : res.statusText);
    return d;
  }
  const fmtSize = (b) => (b < 1048576 ? Math.max(1, Math.round(b / 1024)) + " KB" : (b / 1048576).toFixed(1) + " MB");
  const ROLES = { user: "Người dân", can_bo: "Cán bộ", dev: "Dev" };
  const row = (cells, cls) => { const tr = el("tr", cls || ""); cells.forEach((c) => { const td = el("td"); if (c instanceof Node) td.appendChild(c); else td.textContent = c == null ? "" : String(c); tr.appendChild(td); }); return tr; };
  const head = (t, cols) => { t.innerHTML = ""; const tr = el("tr"); cols.forEach((c) => tr.appendChild(el("th", "", c))); t.appendChild(tr); };
  const span = (text, cls) => el("span", cls, text);

  /* ---------- tab ---------- */
  document.querySelectorAll(".admin-tabs .tab").forEach((t) => {
    t.onclick = () => {
      document.querySelectorAll(".admin-tabs .tab").forEach((x) => x.classList.toggle("active", x === t));
      document.querySelectorAll(".admin-tab").forEach((s) => { s.hidden = s.id !== "tab-" + t.dataset.tab; });
      ({ users: loadUsers, lab: loadLab })[t.dataset.tab]();
    };
  });
  document.querySelectorAll(".s4-modal").forEach((m) => {
    m.querySelector(".close").onclick = () => { m.hidden = true; };
    m.addEventListener("click", (e) => { if (e.target === m) m.hidden = true; });
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") document.querySelectorAll(".s4-modal").forEach((m) => { m.hidden = true; }); });

  /* ================= Người dùng ================= */
  async function loadUsers() {
    let r; try { r = await api("/s4/admin/users"); } catch (e) { alert(e.message); return; }
    renderUsers(r.users);
  }
  function renderUsers(users) {
    const t = $("users"); head(t, ["Tên", "Vai trò", "Trạng thái", "Hội thoại", "Dữ liệu", "Bộ nhớ", "Tạo lúc (UTC)", ""]);
    users.forEach((u) => {
      const role = el("select");
      Object.entries(ROLES).forEach(([x, name]) => { const o = el("option", "", name); o.value = x; o.selected = u.role === x; role.appendChild(o); });
      role.onchange = () => patch(u, { role: role.value }, () => { role.value = u.role; });
      const st = span(u.disabled ? "đã khoá" : "hoạt động", u.disabled ? "tag bad" : "tag on");
      const act = el("div");
      act.appendChild(btn("Hội thoại", () => openUserConvs(u), "btn-ghost", "Xem hội thoại của người này (chỉ xem) và soi từng câu trả lời"));
      act.appendChild(btn(u.disabled ? "Mở khoá" : "Khoá", () => patch(u, { disabled: !u.disabled })));
      act.appendChild(btn("Đặt lại mật khẩu", () => { const p = prompt(`Mật khẩu mới cho ${u.username}:`); if (p) patch(u, { password: p }, null, "Đã đặt mật khẩu mới (người dùng bị đăng xuất)."); }));
      act.appendChild(btn("Xoá", () => {
        if (!confirm(`Xoá tài khoản ${u.username} cùng TOÀN BỘ hội thoại, bộ dữ liệu, bộ nhớ của họ? Không khôi phục được.`)) return;
        api("/s4/admin/users/" + u.id, null, "DELETE").then((r) => renderUsers(r.users)).catch((e) => alert(e.message));
      }));
      const tr = row([u.username, role, st, `${u.strict_chats} Strict · ${u.friendly_chats} Friendly`,
        `${u.datasets.n} bộ · ${fmtSize(u.datasets.b)}`, u.memories, u.created_at, act]);
      tr.lastChild.className = "actions";
      t.appendChild(tr);
    });
  }
  async function patch(u, body, undo, okMsg) {
    try { const r = await api("/s4/admin/users/" + u.id, body, "PATCH"); renderUsers(r.users); if (okMsg) alert(okMsg); }
    catch (e) { alert(e.message); if (undo) undo(); }
  }
  $("new-user").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.target;
    try { const r = await api("/s4/admin/users", { username: f.username.value.trim(), password: f.password.value, role: f.role.value }); f.reset(); renderUsers(r.users); }
    catch (err) { alert(err.message); }
  });

  /* ================= Hội thoại của người dùng (chỉ xem) + 🔍 ================= */
  async function openUserConvs(u) {
    let r; try { r = await api("/s4/admin/users/" + u.id + "/conversations"); } catch (e) { alert(e.message); return; }
    $("conv-title").textContent = "Hội thoại của " + u.username;
    const body = $("conv-body"); body.innerHTML = "";
    if (!r.conversations.length) body.appendChild(el("p", "muted", "Chưa có hội thoại nào."));
    const ul = el("ul", "conv-pick");
    r.conversations.forEach((c) => {
      const li = el("li"); li.append(span(c.mode === "strict" ? "Strict" : "Friendly", "tag"), el("span", "", " " + c.title), el("span", "muted small", " · " + c.created_at));
      li.onclick = () => openConv(u, c);
      ul.appendChild(li);
    });
    body.appendChild(ul);
    $("conv-modal").hidden = false;
  }
  async function openConv(u, c) {
    const url = c.mode === "strict" ? "/s4/strict/" + c.id + "/messages" : "/s4/conversations/" + c.id + "/messages";
    let r; try { r = await api(url); } catch (e) { alert(e.message); return; }
    $("conv-title").textContent = u.username + " · " + c.title;
    const body = $("conv-body"); body.innerHTML = "";
    body.appendChild(btn("← Danh sách hội thoại", () => openUserConvs(u)));
    const view = el("div", "chat-view");
    r.messages.forEach((m) => {
      if (m.role === "user") { view.appendChild(el("div", "u", m.content)); return; }
      const a = el("div", "a", c.mode === "strict" && m.blocks && m.blocks.length ? m.blocks.map((b) => (b.title ? b.title + "\n" : "") + (b.text || "")).join("\n\n") : m.content);
      a.appendChild(el("br"));
      a.appendChild(btn("🔍 Soi", () => (c.mode === "strict" ? S4Inspect.strict(m.node_id) : S4Inspect.friendly(m.id, true))));
      view.appendChild(a);
    });
    body.appendChild(view);
  }

  /* ================= Thử tìm kiếm ================= */
  let labReady = false;
  async function loadLab() {
    if (labReady) return;
    labReady = true;
    try {
      const [us, st] = await Promise.all([api("/s4/admin/users"), api("/s4/settings")]);
      const sel = $("lab-user"); sel.innerHTML = "";
      us.users.forEach((u) => { const o = el("option", "", u.username + ` (${u.datasets.n} bộ dữ liệu)`); o.value = u.id; sel.appendChild(o); });
      const get = (k) => (st.settings.find((s) => s.key === k) || {}).value;
      $("lab-cand").value = get("RETRIEVAL_CANDIDATES"); $("lab-topk").value = get("RETRIEVAL_TOP_K");
      $("lab-min").value = get("RERANK_MIN_SCORE"); $("lab-rr").checked = !!get("RERANKER_ENABLED");
      sel.onchange = labDatasets; labDatasets();
    } catch (e) { alert(e.message); }
  }
  async function labDatasets() {
    const uid = +$("lab-user").value, box = $("lab-ds"); box.innerHTML = "";
    const r = await api("/s4/admin/datasets");
    const mine = r.datasets.filter((d) => d.user_id === uid && d.status === "ready");
    if (!mine.length) { box.appendChild(el("span", "muted", "Người này chưa có bộ dữ liệu sẵn sàng.")); return; }
    mine.forEach((d) => { const l = el("label"); const cb = el("input"); cb.type = "checkbox"; cb.value = d.id; cb.checked = !!d.active; l.append(cb, el("span", "", " " + d.name + ` (${d.n_records})`)); box.appendChild(l); });
  }
  function labBody() {
    return {
      query: $("lab-q").value.trim(), user_id: +$("lab-user").value,
      dataset_ids: [...$("lab-ds").querySelectorAll("input:checked")].map((x) => +x.value),
      overrides: { RETRIEVAL_CANDIDATES: +$("lab-cand").value, RETRIEVAL_TOP_K: +$("lab-topk").value,
                   RERANK_MIN_SCORE: +$("lab-min").value, RERANKER_ENABLED: $("lab-rr").checked },
    };
  }
  $("lab-run").onclick = async () => {
    const b = labBody(); if (!b.query) { alert("Nhập câu hỏi"); return; }
    if (!b.dataset_ids.length) { alert("Chọn ít nhất một bộ dữ liệu"); return; }
    const out = $("lab-out"); out.hidden = false; out.innerHTML = ""; out.appendChild(el("p", "muted", "Đang tìm…"));
    try { const r = await api("/s4/admin/searchlab", b); out.innerHTML = ""; out.appendChild(el("h2", "", "Xếp hạng")); out.appendChild(S4Inspect.candidates(r.info)); }
    catch (e) { out.innerHTML = ""; out.appendChild(el("p", "error", e.message)); }
  };
  $("lab-q").addEventListener("keydown", (e) => { if (e.key === "Enter") $("lab-run").click(); });
  $("lab-ask").onclick = async () => {
    const b = labBody(); if (!b.query || !b.dataset_ids.length) { alert("Nhập câu hỏi và chọn bộ dữ liệu"); return; }
    const box = $("lab-answer"); box.hidden = false; box.innerHTML = ""; box.appendChild(el("p", "muted", "Đang hỏi AI (chế độ Nhanh)…"));
    try {
      const r = await api("/s4/admin/searchlab/ask", b);
      box.innerHTML = "";
      box.appendChild(el("h2", "", "Câu trả lời của AI"));
      box.appendChild(el("pre", "insp-pre", (r.parsed && r.parsed.answer) || "(không đọc được JSON)"));
      box.appendChild(el("h3", "", "Kế hoạch ẩn"));
      box.appendChild(el("pre", "insp-pre", (r.parsed && r.parsed.plan) || ""));
      const d1 = el("details"); d1.appendChild(el("summary", "", "Lời dặn hệ thống đã gửi")); d1.appendChild(el("pre", "insp-pre", r.prompt)); box.appendChild(d1);
      const d2 = el("details"); d2.appendChild(el("summary", "", "JSON thô")); d2.appendChild(el("pre", "insp-pre", r.raw)); box.appendChild(d2);
      $("lab-out").hidden = false; $("lab-out").innerHTML = ""; $("lab-out").appendChild(el("h2", "", "Xếp hạng")); $("lab-out").appendChild(S4Inspect.candidates(r.info));
    } catch (e) { box.innerHTML = ""; box.appendChild(el("p", "error", e.message)); }
  };

  /* ---------- khởi động ---------- */
  fetch("/s4/public").then((r) => r.json()).then((p) => {
    if (!p.user) { location.href = "/s4/login"; return; }
    if (p.user.role !== "dev") { location.href = "/"; return; }
    $("me").textContent = p.user.username + " · dev";
    loadUsers();
  });
})();

/* System 4 — trang Quản trị (dev): dữ liệu Strict (phiên bản, nháp, so sánh, áp dụng, cào), dữ liệu người dùng, người dùng. */
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
  const SRC = { original: "Gốc", edit: "Sửa tay", scrape: "Cào" };
  const row = (cells, cls) => { const tr = el("tr", cls || ""); cells.forEach((c) => { const td = el("td"); if (c instanceof Node) td.appendChild(c); else td.textContent = c == null ? "" : String(c); tr.appendChild(td); }); return tr; };
  const head = (t, cols) => { t.innerHTML = ""; const tr = el("tr"); cols.forEach((c) => tr.appendChild(el("th", "", c))); t.appendChild(tr); };
  const span = (text, cls) => el("span", cls, text);

  /* ---------- tab ---------- */
  document.querySelectorAll(".admin-tabs .tab").forEach((t) => {
    t.onclick = () => {
      document.querySelectorAll(".admin-tabs .tab").forEach((x) => x.classList.toggle("active", x === t));
      document.querySelectorAll(".admin-tab").forEach((s) => { s.hidden = s.id !== "tab-" + t.dataset.tab; });
      ({ strict: loadProcs, datasets: loadDatasets, users: loadUsers })[t.dataset.tab]();
    };
  });
  document.querySelectorAll(".s4-modal").forEach((m) => {
    m.querySelector(".close").onclick = () => { m.hidden = true; };
    m.addEventListener("click", (e) => { if (e.target === m) m.hidden = true; });
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") document.querySelectorAll(".s4-modal").forEach((m) => { m.hidden = true; }); });

  /* ================= Tab 1: Dữ liệu Strict ================= */
  let P = null, jobTimer = null;
  const procView = { version: "draft", q: "", offset: 0 };

  async function loadProcs() {
    try { P = await api("/s4/admin/procs"); } catch (e) { alert(e.message); return; }
    const active = P.versions.find((v) => v.id === P.active_id);
    $("active-label").textContent = active ? `phiên bản ${active.id} · ${active.label} · ${active.n_records} thủ tục` : "?";
    const t = $("versions"); head(t, ["#", "Tên", "Nguồn", "Thủ tục", "Tạo lúc (UTC)", "Ghi chú", ""]);
    P.versions.forEach((v) => {
      const name = el("span", "", v.label);
      if (v.id === P.active_id) name.appendChild(span("đang dùng", "tag on"));
      if (v.id === P.original_id) name.appendChild(span("gốc", "tag"));
      const act = el("div");
      act.appendChild(btn("Xem", () => { procView.version = String(v.id); fillVersionSelect(); loadProcList(true); $("procs").scrollIntoView({ behavior: "smooth" }); }));
      if (v.id !== P.active_id) {
        act.appendChild(btn("So sánh", () => showDiff(String(P.active_id), String(v.id), "Bản đang dùng → phiên bản " + v.id)));
        act.appendChild(btn("Áp dụng", () => applyVersion(v), "primary", "Strict mode chuyển sang phiên bản này"));
      }
      if (v.id !== P.active_id && v.id !== P.original_id) act.appendChild(btn("Xoá", async () => {
        if (!confirm(`Xoá phiên bản ${v.id} (${v.label})?`)) return;
        try { await api("/s4/admin/procs/versions/" + v.id, null, "DELETE"); } catch (e) { alert(e.message); }
        loadProcs();
      }));
      const tr = row([v.id, name, SRC[v.source] || v.source, v.n_records, v.created_at, v.note, act]);
      tr.lastChild.className = "actions";
      t.appendChild(tr);
    });
    const d = P.draft;
    $("draft-info").textContent = d.changes ? `dựa trên phiên bản ${d.base}: ${d.changes} thay đổi (${d.deleted} xoá)` : "chưa có thay đổi — mở một thủ tục ở chế độ \"Bản nháp\" để sửa / xoá";
    ["draft-diff", "draft-save", "draft-discard"].forEach((id) => { $(id).disabled = !d.changes; });
    fillVersionSelect();
    renderJob(P.job);
    if (!$("procs").children.length) loadProcList(true);
  }

  function fillVersionSelect() {
    const s = $("proc-version"); s.innerHTML = "";
    const o = el("option", "", "Bản nháp (sửa được)"); o.value = "draft"; s.appendChild(o);
    P.versions.forEach((v) => { const x = el("option", "", `Phiên bản ${v.id} · ${v.label}` + (v.id === P.active_id ? " (đang dùng)" : "")); x.value = String(v.id); s.appendChild(x); });
    s.value = procView.version;
  }
  $("proc-version").onchange = () => { procView.version = $("proc-version").value; loadProcList(true); };
  let qTimer = null;
  $("proc-q").oninput = () => { clearTimeout(qTimer); qTimer = setTimeout(() => { procView.q = $("proc-q").value.trim(); loadProcList(true); }, 300); };
  $("proc-more").onclick = () => loadProcList(false);

  async function loadProcList(reset) {
    const t = $("procs");
    if (reset) { procView.offset = 0; head(t, ["Mã", "Tên thủ tục", "Lĩnh vực", "Tỉnh"]); }
    let r;
    try { r = await api(`/s4/admin/procs/records?version=${procView.version}&q=${encodeURIComponent(procView.q)}&offset=${procView.offset}&limit=50`); }
    catch (e) { alert(e.message); return; }
    r.records.forEach((x) => {
      const name = el("span", "name", x.name); if (x.changed) name.appendChild(span("đã sửa", "tag warn"));
      const tr = row([x.proc_id, name, x.domain, x.province], "clickable");
      tr.onclick = () => openRecord(x.proc_id);
      t.appendChild(tr);
    });
    procView.offset += r.records.length;
    $("proc-count").textContent = `${r.total} thủ tục` + (procView.version === "draft" && r.deleted.length ? ` · ${r.deleted.length} đã xoá trong nháp (${r.deleted.join(", ")})` : "");
    $("proc-more").hidden = procView.offset >= r.total;
  }

  /* xem / sửa một thủ tục: chuỗi sửa trực tiếp, danh sách / đối tượng sửa dạng JSON; máy chủ kiểm chuẩn dữ liệu */
  async function openRecord(pid) {
    let r;
    try { r = await api(`/s4/admin/procs/record/${encodeURIComponent(pid)}?version=${procView.version}`); } catch (e) { alert(e.message); return; }
    const editable = procView.version === "draft";
    const body = $("rec-body"); body.innerHTML = ""; $("rec-err").hidden = true;
    $("rec-title").textContent = r.record.name + (r.changed ? " (đã sửa trong nháp)" : "");
    body.appendChild(el("div", "muted small", editable ? "Bản nháp: sửa xong bấm \"Lưu vào nháp\". Chuỗi sửa trực tiếp; danh sách / đối tượng sửa dạng JSON. Không đổi được mã thủ tục."
      : "Đang xem phiên bản " + procView.version + " (chỉ đọc). Chọn \"Bản nháp\" để sửa."));
    const inputs = {};
    Object.entries(r.record).forEach(([k, v]) => {
      const f = el("div", "field");
      const lab = el("label"); lab.append(el("span", "", k), el("small", "", (r.profile[k] || []).join(" / ")));
      const ta = el("textarea");
      const isStr = typeof v === "string";
      ta.value = isStr ? v : JSON.stringify(v, null, 1);
      ta.rows = Math.min(14, Math.max(1, ta.value.split("\n").length, Math.ceil(ta.value.length / 110)));
      ta.readOnly = !editable || k === "proc_id";
      ta.dataset.kind = isStr ? "str" : "json";
      inputs[k] = ta;
      f.append(lab, ta); body.appendChild(f);
    });
    const foot = $("rec-foot"); foot.innerHTML = "";
    const close = () => { $("rec-modal").hidden = true; };
    if (editable) {
      if (r.changed) foot.appendChild(btn("Bỏ thay đổi", async () => { try { await api(`/s4/admin/procs/draft/${encodeURIComponent(pid)}/revert`, {}); close(); loadProcs(); loadProcList(true); } catch (e) { alert(e.message); } }));
      foot.appendChild(btn("Xoá thủ tục (trong nháp)", async () => {
        if (!confirm("Xoá thủ tục này khỏi bản nháp?")) return;
        try { await api(`/s4/admin/procs/draft/${encodeURIComponent(pid)}`, null, "DELETE"); close(); loadProcs(); loadProcList(true); } catch (e) { alert(e.message); }
      }));
      foot.appendChild(btn("Lưu vào nháp", async () => {
        const rec = {}; const errs = [];
        Object.entries(inputs).forEach(([k, ta]) => {
          if (ta.dataset.kind === "str") rec[k] = ta.value;
          else { try { rec[k] = JSON.parse(ta.value); } catch (_) { errs.push(`"${k}" không phải JSON hợp lệ`); } }
        });
        if (errs.length) { $("rec-err").textContent = errs.join(" · "); $("rec-err").hidden = false; return; }
        try { await api(`/s4/admin/procs/draft/${encodeURIComponent(pid)}`, { record: rec }, "PUT"); close(); loadProcs(); loadProcList(true); }
        catch (e) { $("rec-err").textContent = e.message; $("rec-err").hidden = false; }
      }, "primary"));
    }
    $("rec-modal").hidden = false;
  }

  async function showDiff(a, b, title) {
    let d;
    try { d = await api(`/s4/admin/procs/diff?a=${a}&b=${b}`); } catch (e) { alert(e.message); return; }
    $("diff-title").textContent = title;
    const body = $("diff-body"); body.innerHTML = "";
    const c = d.counts;
    const counts = el("div", "diff-counts");
    counts.append(span(`+${c.added} mới`, "tag on"), span(`−${c.removed} không còn`, "tag bad"), span(`${c.changed} thay đổi`, "tag warn"));
    body.appendChild(counts);
    const section = (label, items, fn) => {
      if (!items.length) return;
      body.appendChild(el("h3", "", label));
      const ul = el("ul", "diff-list");
      items.forEach((x) => { const li = el("li"); li.append(el("b", "", x.proc_id + " "), el("span", "", x.name + (x.fields ? " — " + x.fields.join(", ") : ""))); if (fn) { li.style.cursor = "pointer"; li.onclick = () => fn(x, li); } ul.appendChild(li); });
      body.appendChild(ul);
    };
    section("Mới", d.added); section("Không còn", d.removed);
    section("Thay đổi (bấm để xem chi tiết)", d.changed, async (x, li) => {
      if (li.querySelector(".diff-field")) return;
      try {
        const r = await api(`/s4/admin/procs/diff/${encodeURIComponent(x.proc_id)}?a=${a}&b=${b}`);
        r.fields.forEach((f) => {
          const box = el("div", "diff-field"); box.appendChild(el("b", "", f.field));
          const s = (v) => (typeof v === "string" ? v : JSON.stringify(v, null, 1));
          box.append(el("pre", "old", "− " + s(f.old)), el("pre", "new", "+ " + s(f.new)));
          li.appendChild(box);
        });
      } catch (e) { alert(e.message); }
    });
    if (!c.added && !c.removed && !c.changed) body.appendChild(el("p", "muted", "Hai phiên bản giống nhau."));
    $("diff-modal").hidden = false;
  }

  $("draft-diff").onclick = () => showDiff(String(P.draft.base), "draft", "Phiên bản " + P.draft.base + " → bản nháp");
  $("draft-save").onclick = async () => {
    const label = prompt("Tên phiên bản mới:", "Sửa " + P.draft.changes + " thủ tục");
    if (label === null) return;
    try { const r = await api("/s4/admin/procs/draft/save", { label }); alert(`Đã tạo phiên bản ${r.version_id} (so với bản đang dùng: +${r.diff.added}, −${r.diff.removed}, ${r.diff.changed} thay đổi). Bấm "Áp dụng" để Strict mode dùng phiên bản này.`); }
    catch (e) { alert(e.message); }
    procView.version = "draft"; loadProcs(); loadProcList(true);
  };
  $("draft-discard").onclick = async () => {
    if (!confirm("Bỏ toàn bộ thay đổi trong bản nháp?")) return;
    try { await api("/s4/admin/procs/draft", null, "DELETE"); } catch (e) { alert(e.message); }
    loadProcs(); loadProcList(true);
  };

  async function applyVersion(v) {
    if (!confirm(`Strict mode sẽ chuyển sang phiên bản ${v.id} (${v.label}, ${v.n_records} thủ tục). Dựng lại DB mất khoảng 1 phút. Tiếp tục?`)) return;
    try { renderJob((await api("/s4/admin/procs/apply", { version_id: v.id })).job); } catch (e) { alert(e.message); }
  }
  $("scrape-btn").onclick = async () => {
    const limit = parseInt($("scrape-limit").value || "0", 10) || 0;
    if (!confirm((limit ? `Cào thử ${limit} thủ tục` : "Cào toàn bộ thủ tục cấp Xã/Phường (khoảng 1.350, tải vài chục MB, có thể mất hàng chục phút)") + " từ dichvucong.gov.vn? Cần internet. Kết quả thành một phiên bản mới, CHƯA áp dụng.")) return;
    try { renderJob((await api("/s4/admin/procs/scrape", { limit })).job); } catch (e) { alert(e.message); }
  };

  function renderJob(j) {
    const box = $("job");
    clearTimeout(jobTimer);
    if (!j || j.state === "idle") { box.hidden = true; return; }
    box.hidden = false; box.className = "job " + (j.state === "running" ? "" : j.state);
    box.innerHTML = "";
    const what = j.kind === "scrape" ? "Cào dữ liệu" : "Áp dụng phiên bản";
    box.appendChild(el("b", "", what + ": "));
    box.appendChild(el("span", "", j.message));
    if (j.kind === "scrape" && j.progress) {
      const p = j.progress;
      if (p.catalog) {
        box.appendChild(el("div", "small muted", `Danh mục: ${p.catalog} thủ tục · đã lấy chi tiết: ${p.details}`));
        const bar = el("div", "bar"); const i = el("i"); i.style.width = Math.min(100, (p.details / p.catalog) * 100) + "%"; bar.appendChild(i); box.appendChild(bar);
      }
    }
    if (j.state === "running") jobTimer = setTimeout(pollJob, 2000);
    else if (j.state === "done" && j.kind) { /* xong: làm mới danh sách phiên bản một lần */ if (!box.dataset.refreshed) { box.dataset.refreshed = "1"; loadProcs(); } }
  }
  async function pollJob() {
    try {
      const r = await api("/s4/admin/procs/job");
      $("job").dataset.refreshed = "";
      renderJob(r.job);
      if (r.log && r.log.length && r.job.state !== "done") { const pre = el("pre", "", r.log.slice(-8).join("\n")); $("job").appendChild(pre); }
    } catch (_) { jobTimer = setTimeout(pollJob, 4000); }
  }

  /* ================= Tab 2: Dữ liệu người dùng ================= */
  const KIND = { table: "Bảng", rows: "Bảng (dòng chữ)", text: "Văn bản", mixed: "Bảng + văn bản" };
  async function loadDatasets() {
    let r; try { r = await api("/s4/admin/datasets"); } catch (e) { alert(e.message); return; }
    const t = $("all-datasets"); head(t, ["Người dùng", "Tên", "Loại", "Bản ghi", "Dung lượng", "Trạng thái", ""]);
    if (!r.datasets.length) t.appendChild(row(["Chưa có bộ dữ liệu nào.", "", "", "", "", "", ""]));
    r.datasets.forEach((d) => {
      const st = el("span", "", d.status === "ready" ? (d.active ? "đang bật" : "đang tắt") : d.status);
      if (d.status === "error") st.className = "tag bad";
      const act = el("div");
      if (d.status === "ready") act.appendChild(btn("Mở", () => openDataset(d)));
      act.appendChild(btn("Xoá", async () => {
        if (!confirm(`Xoá bộ dữ liệu "${d.name}" của ${d.username}?`)) return;
        try { await api("/s4/datasets/" + d.id, null, "DELETE"); } catch (e) { alert(e.message); }
        loadDatasets();
      }));
      const tr = row([d.username, d.name + " (" + d.filename + ")", KIND[d.kind] || "", d.n_records, fmtSize(d.size_bytes), st, act]);
      tr.lastChild.className = "actions";
      t.appendChild(tr);
    });
  }
  let dsState = null;
  async function loadDs(reset) {
    if (reset) { dsState.offset = 0; $("ds-list").innerHTML = ""; }
    try {
      const r = await api(`/s4/datasets/${dsState.d.id}/records?offset=${dsState.offset}&limit=50&q=${encodeURIComponent(dsState.q)}`);
      r.records.forEach((x) => {
        const c = el("div", "rec-card"); c.appendChild(el("b", "", x.title));
        const f = Object.entries(x.fields || {});
        c.appendChild(el("div", "rec-fields", f.length ? f.map(([k, v]) => k + ": " + v).join("\n") : x.text));
        c.appendChild(el("small", "", x.source)); $("ds-list").appendChild(c);
      });
      dsState.offset += r.records.length;
      $("ds-count").textContent = r.total + " bản ghi";
      $("ds-more").hidden = dsState.offset >= r.total;
    } catch (e) { alert(e.message); }
  }
  function openDataset(d) { dsState = { d, offset: 0, q: "" }; $("ds-title").textContent = d.username + " · " + d.name; $("ds-q").value = ""; $("ds-modal").hidden = false; loadDs(true); }
  let dsTimer = null;
  $("ds-q").oninput = () => { clearTimeout(dsTimer); dsTimer = setTimeout(() => { dsState.q = $("ds-q").value.trim(); loadDs(true); }, 300); };
  $("ds-more").onclick = () => loadDs(false);

  /* ================= Tab 3: Người dùng ================= */
  async function loadUsers() {
    let r; try { r = await api("/s4/admin/users"); } catch (e) { alert(e.message); return; }
    renderUsers(r.users);
  }
  function renderUsers(users) {
    const t = $("users"); head(t, ["Tên", "Vai trò", "Trạng thái", "Hội thoại", "Dữ liệu", "Bộ nhớ", "Tạo lúc (UTC)", ""]);
    users.forEach((u) => {
      const role = el("select");
      ["user", "dev"].forEach((x) => { const o = el("option", "", x); o.value = x; o.selected = u.role === x; role.appendChild(o); });
      role.onchange = () => patch(u, { role: role.value }, () => { role.value = u.role; });
      const st = span(u.disabled ? "đã khoá" : "hoạt động", u.disabled ? "tag bad" : "tag on");
      const act = el("div");
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

  /* ---------- khởi động ---------- */
  fetch("/s4/public").then((r) => r.json()).then((p) => {
    if (!p.user) { location.href = "/s4/login"; return; }
    if (p.user.role !== "dev") { location.href = "/"; return; }
    $("me").textContent = p.user.username + " · dev";
    loadProcs();
  });
})();

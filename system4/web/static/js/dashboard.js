/* Bảng điều khiển lĩnh vực = hộp "Lĩnh vực" mở rộng: MỘT chỗ quản lý mọi thứ về lĩnh vực, dữ liệu và thống kê.
   Trái: danh sách lĩnh vực (+ "Thêm lĩnh vực"; dev / cán bộ có thêm "Dữ liệu mọi người dùng", "Thống kê chung").
   Phải: tab của lĩnh vực đang chọn — Tổng quan (ghim, sửa, hồ sơ) · Dữ liệu (Thủ tục: phiên bản / nháp / thủ tục / cào;
   ABI: phiên bản / đồng bộ; lĩnh vực khác: bộ dữ liệu) · Đường nhanh (biên dịch + tự kiểm) · Thống kê (Thủ tục).
   Dev và cán bộ thấy như nhau; người dùng thường thấy ít hơn. "Xem như người dùng" vẽ lại đúng như người dùng thường thấy
   (máy chủ vẫn kiểm quyền thật). Tài khoản và Thử tìm kiếm ở /s4/admin (chỉ dev).
   API: /s4/domains, /s4/datasets, /s4/fastpath, /s4/admin/procs|stats|datasets|feedback, /s4/abi. */
(function () {
  let A = null;                         // trợ giúp của app.js (S4Dash.init)
  let sel = null, tab = "overview", userView = false;
  let jobTimer = null, abiTimer = null, fpTimer = null;
  const $ = (id) => document.getElementById(id);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const btn = (label, fn, cls, title) => { const b = el("button", cls || "btn-ghost", label); b.type = "button"; if (title) b.title = title; b.onclick = (e) => { e.stopPropagation(); fn(b); }; return b; };
  const span = (text, cls) => el("span", cls, text);
  const realStaff = () => { const m = A.me(); return !!m && (m.role === "dev" || m.role === "can_bo"); };
  const staff = () => !userView && realStaff();
  const fmtSize = (b) => (b < 1048576 ? Math.max(1, Math.round(b / 1024)) + " KB" : (b / 1048576).toFixed(1) + " MB");
  const fmtTime = (s) => { if (!s) return "—"; const d = new Date(s); return isNaN(d) ? s : d.toLocaleString("vi-VN"); };
  const card = (title, ...kids) => { const c = el("div", "card"); if (title) c.appendChild(el("h3", "", title)); kids.forEach((k) => k && c.appendChild(k)); return c; };
  const fold = (title, open, ...kids) => {   // phần dài (cào dữ liệu, thống kê): thu gọn được
    const d = el("details", "dash-fold"); d.open = !!open; d.appendChild(el("summary", "", title)); kids.forEach((k) => k && d.appendChild(k)); return d;
  };
  const table = (cols) => { const t = el("table", "grid"); const tr = el("tr"); cols.forEach((c) => tr.appendChild(el("th", "", c))); t.appendChild(tr); return t; };
  const row = (cells, cls) => { const tr = el("tr", cls || ""); cells.forEach((c) => { const td = el("td"); if (c instanceof Node) td.appendChild(c); else td.textContent = c == null ? "" : String(c); tr.appendChild(td); }); return tr; };
  const errBox = (e) => el("p", "error", "Lỗi: " + (e && e.message ? e.message : e));
  const domain = () => A.domains().find((d) => d.id === sel);

  /* ================================================================ khung ================== */
  function init(helpers) {
    A = helpers;
    $("domain-close").onclick = close;
    $("domain-modal").addEventListener("click", (e) => { if (e.target === $("domain-modal")) close(); });
    $("dash-userview").onchange = () => { userView = $("dash-userview").checked; A.setViewUser(userView); render(); };
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      const sub = ["dash-rec-modal", "dash-diff-modal"].find((id) => !$(id).hidden);
      if (sub) $(sub).hidden = true; else if (!$("domain-modal").hidden) close();
    });
    ["dash-rec-modal", "dash-diff-modal"].forEach((id) => {
      const m = $(id);
      m.querySelector(".close").onclick = () => { m.hidden = true; };
      m.addEventListener("click", (e) => { if (e.target === m) m.hidden = true; });
    });
  }
  function close() {
    $("domain-modal").hidden = true;
    [jobTimer, abiTimer, fpTimer].forEach(clearTimeout);
  }
  async function open(openId, openTab) {
    await A.loadDomains();
    if (openId) {
      sel = openId;
      const d0 = A.domains().find((d) => d.id === openId);
      tab = openTab || (d0 && d0.engine === "friendly" ? "data" : "overview");
    }
    if (sel == null || (typeof sel === "number" && !domain())) { sel = A.domainId(); tab = "overview"; }
    $("dash-userview-lab").hidden = !realStaff();
    $("dash-admin-link").hidden = !(A.me() && A.me().role === "dev");
    render();
    $("domain-modal").hidden = false;
  }
  function render() { renderSide(); renderMain(); }

  function renderSide() {
    const ul = $("domain-list"); ul.innerHTML = "";
    const item = (key, label, tags, title) => {
      const li = el("li", "dash-item" + (sel === key ? " on" : "")); li.tabIndex = 0; li.setAttribute("role", "button");
      li.appendChild(el("span", "dash-name", label));
      (tags || []).forEach(([t, c]) => li.appendChild(span(t, "dom-tag " + (c || ""))));
      if (title) li.title = title;
      const go = () => { sel = key; tab = "overview"; if (typeof key === "number") { const d = domain(); if (d && d.engine === "friendly") tab = "data"; } render(); };
      li.onclick = go; li.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } };
      ul.appendChild(li);
    };
    A.domains().filter((d) => !(userView && d.locked)).forEach((d) => {
      const tags = [[d.kind === "hard" ? "Cứng" : "Mềm", d.kind]];
      if (d.engine === "strict") tags.push([d.data_mode === "s4" ? "System 4" : "System 3"]); else if (d.engine === "abi") tags.push(["abi.com.vn"]); else if (d.engine === "flm") tags.push(["flm.fpt.edu.vn"]);
      if (d.locked) tags.push(["Chỉ cán bộ", "lock"]);
      if (d.mine) tags.push(["Của tôi"]);
      item(d.id, d.name, tags, d.guardrail ? "Guardrail: " + d.guardrail : "");
    });
    item("__new", "+ Thêm lĩnh vực");
    if (staff()) {
      ul.appendChild(el("li", "dash-sep", "Chung"));
      item("__all", "Dữ liệu mọi người dùng", [], "Mọi bộ dữ liệu đã tải lên (dev và cán bộ mở / xoá được)");
      item("__stats", "Thống kê chung", [], "Phản hồi 👍/👎, tài khoản, tải phản hồi");
    }
  }

  function tabsFor(d) {
    const t = [["overview", "Tổng quan"]];
    // lĩnh vực cứng có dữ liệu cào / đồng bộ riêng: thêm thẻ "Dữ liệu tải thêm" (tệp dùng chung do dev / cán bộ tải lên)
    if (d.engine === "strict") { if (staff()) t.push(["data", "Dữ liệu thủ tục"], ["extra", "Dữ liệu tải lên"], ["stats", "Thống kê"]); if (d.data_mode === "s4") t.push(["fast", "Đường nhanh"]); }
    else if (d.engine === "abi") { if (staff()) t.push(["data", "Dữ liệu ABI"], ["extra", "Dữ liệu tải thêm"]); }
    else if (d.engine === "flm") { if (staff()) t.push(["data", "Dữ liệu FLM"], ["extra", "Dữ liệu tải thêm"]); t.push(["fast", "Đường nhanh"]); }
    else t.push(["data", "Dữ liệu"], ["fast", "Đường nhanh"]);
    return t;
  }
  function extraData(d, pane) {
    const help = d.engine === "strict"
      ? (d.data_mode === "s4" ? "Đang ở chế độ System 4: lĩnh vực Thủ tục CHỈ trả lời từ các tệp dưới đây (DB thủ tục của System 3 đang tắt)."
        : "Đang ở chế độ System 3: các tệp dưới đây CHƯA được dùng. Chuyển nguồn dữ liệu sang System 4 ở thẻ Tổng quan để dùng chúng (khi đó DB thủ tục của System 3 tắt).")
      : "Tệp dùng chung tải thêm vào lĩnh vực, tìm chung với dữ liệu đồng bộ (phiên bản đang dùng). Chuyển phiên bản không bật / tắt các tệp này.";
    pane.appendChild(el("p", "mem-help", help));
    pane.appendChild(A.dataPanel(d, true));
  }

  function renderMain() {
    [jobTimer, abiTimer, fpTimer].forEach(clearTimeout);
    const tabs = $("dash-tabs"), pane = $("dash-pane");
    tabs.innerHTML = ""; pane.innerHTML = "";
    if (sel === "__new") { pane.appendChild(newDomainForm()); return; }
    if (sel === "__all") { if (staff()) allDatasets(pane); return; }
    if (sel === "__stats") { if (staff()) generalStats(pane); return; }
    const d = domain();
    if (!d) return;
    const ts = tabsFor(d);
    if (!ts.some(([k]) => k === tab)) tab = "overview";
    ts.forEach(([k, label]) => {
      const b = el("button", "tab" + (k === tab ? " active" : ""), label); b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-selected", String(k === tab));
      b.onclick = () => { tab = k; renderMain(); };
      tabs.appendChild(b);
    });
    pane.appendChild(el("h3", "dash-title", d.name));
    ({ overview: overviewTab, data: d.engine === "strict" ? strictData : d.engine === "abi" ? abiData : d.engine === "flm" ? flmData : friendlyData, extra: extraData, fast: fastTab, stats: strictStats })[tab](d, pane);
  }

  /* ================================================================ tổng quan ============== */
  function overviewTab(d, pane) {
    const kind = d.kind === "hard" ? "Lĩnh vực cứng: không xoá được, dữ liệu dùng chung do dev / cán bộ tải lên, mọi người (được phép) cùng dùng."
      : "Lĩnh vực mềm: kiểu Friendly; dữ liệu là của riêng từng người.";
    const eng = d.engine === "strict" ? (d.data_mode === "s4" ? " Chế độ System 4: trả lời từ dữ liệu tải lên của lĩnh vực (DB thủ tục của System 3 đang tắt)."
        : " Trả lời bằng luật của System 3 (thủ tục hành chính), có nguồn.")
      : d.engine === "abi" ? " Dữ liệu abi.com.vn tự đồng bộ; câu đếm / liệt kê / theo ngày do code trả lời."
      : d.engine === "flm" ? " Khung chương trình + đề cương môn học của ĐH FPT, đồng bộ từ flm.fpt.edu.vn (bấm Đồng bộ FLM, có thể cần tích captcha); câu tra cứu rõ ràng do đường nhanh trả lời." : "";
    pane.appendChild(el("p", "mem-help", kind + eng + (d.locked ? " Đang khoá: chỉ dev và cán bộ dùng." : "")));
    const acts = el("div", "row");
    acts.appendChild(btn(d.pinned ? "Bỏ ghim khỏi thanh chọn" : "Ghim lên thanh chọn", async () => {
      try { A.setDomains((await A.api("/s4/domains/" + d.id + "/pin", { pinned: !d.pinned })).domains); A.renderDomainBar(); render(); } catch (e) { alert(e.message); }
    }));
    acts.appendChild(btn("Dùng lĩnh vực này", () => { close(); A.switchDomain(d.id); }, "primary"));
    if (d.can_delete && !userView) {
      const del = btn("Xoá lĩnh vực", async () => {
        if (!del.dataset.sure) { del.dataset.sure = "1"; del.textContent = "Bấm lần nữa để xoá"; setTimeout(() => { delete del.dataset.sure; del.textContent = "Xoá lĩnh vực"; }, 4000); return; }
        try { A.setDomains((await A.api("/s4/domains/" + d.id, null, "DELETE")).domains); sel = null; await A.afterDomainsChanged(); open(); }
        catch (e) { del.textContent = "Lỗi: " + e.message; }
      }, "btn-ghost", "Xoá lĩnh vực mềm cùng dữ liệu của nó; hội thoại cũ về \"Trò chuyện chung\"");
      acts.appendChild(del);
    }
    pane.appendChild(acts);
    if (!d.can_edit || userView) return;
    const ed = el("div", "dom-edit");
    const name = el("input"); name.type = "text"; name.value = d.name; name.maxLength = 40; name.disabled = d.engine === "strict";
    const g = el("textarea"); g.rows = 3; g.maxLength = 1000; g.value = d.guardrail; g.placeholder = "Guardrail: lời dặn gửi thẳng cho AI trước khi trả lời trong lĩnh vực này";
    ed.append(el("label", "dash-lab", "Tên"), name, el("label", "dash-lab", "Guardrail"), g);
    let prof = null;
    if (d.profile) {
      prof = el("textarea", "dom-profile"); prof.rows = 8; prof.spellcheck = false; prof.value = JSON.stringify(d.profile, null, 1);
      prof.title = "answer_mode: free | grounded | verbatim · require_citation · clarify · retrieval {top_k, rerank} · tools [\"table\"] · persona · web_allowed · fast_path" + (d.engine === "abi" ? " · code_answer" : "");
      ed.append(el("label", "dash-lab", "Hồ sơ lĩnh vực (JSON) — cách trả lời, trích dẫn, hỏi lại, tìm kiếm, công cụ, vai trò, tìm web, đường nhanh"), prof);
    }
    const flags = {};
    if (staff()) {
      [["hard", "Lĩnh vực cứng (dữ liệu dùng chung, không xoá được)", d.kind === "hard", d.engine !== "friendly"], ["locked", "Khoá: chỉ dev và cán bộ dùng", d.locked, false],
       ["upload", "Cho người dùng thường tải dữ liệu riêng (lĩnh vực mềm)", d.user_upload, d.engine !== "friendly"]].forEach(([k, label, on, off]) => {
        const lab = el("label", "dom-check"), cb = el("input"); cb.type = "checkbox"; cb.checked = on; cb.disabled = off; flags[k] = cb;
        lab.append(cb, " " + label); ed.appendChild(lab);
      });
    }
    let mode = null;   // Thủ tục: hai nguồn dữ liệu loại trừ nhau (leader 19/10)
    if (staff() && d.engine === "strict") {
      mode = el("select");
      [["s3", "System 3 — luật + DB thủ tục cào từ Cổng DVC (mặc định)"], ["s4", "System 4 — chỉ dữ liệu tải lên (tắt DB thủ tục của System 3)"]].forEach(([v, t]) => {
        const o = el("option", "", t); o.value = v; o.selected = (d.data_mode || "s3") === v; mode.appendChild(o);
      });
      ed.append(el("label", "dash-lab", "Nguồn dữ liệu (hội thoại Strict cũ chỉ còn xem khi ở System 4)"), mode);
    }
    ed.appendChild(btn("Lưu", async () => {
      const body = { guardrail: g.value };
      if (prof) {
        let p; try { p = JSON.parse(prof.value || "{}"); } catch (e) { alert("Hồ sơ lĩnh vực không phải JSON hợp lệ: " + e.message); return; }
        const def = d.profile_defaults || {};
        body.profile = Object.fromEntries(Object.entries(p).filter(([k, v]) => JSON.stringify(v) !== JSON.stringify(def[k])));
      }
      if (d.engine !== "strict") body.name = name.value;
      if (staff()) { body.locked = flags.locked.checked; if (d.engine !== "strict") { body.kind = flags.hard.checked ? "hard" : "soft"; body.user_upload = flags.upload.checked; } }
      if (mode) { body.data_mode = mode.value; if (mode.value !== "s4") delete body.profile; }   // hồ sơ chỉ dùng ở chế độ System 4
      try { A.setDomains((await A.api("/s4/domains/" + d.id, body, "PATCH")).domains); await A.afterDomainsChanged(); render(); } catch (e) { alert(e.message); }
    }, "primary"));
    pane.appendChild(card("Sửa lĩnh vực", ed));
  }

  function newDomainForm() {
    const f = el("form", "dom-form");
    f.innerHTML = "";
    f.appendChild(el("h3", "", "Thêm lĩnh vực"));
    const name = el("input"); name.name = "name"; name.placeholder = "Tên lĩnh vực (ví dụ: Du lịch)"; name.maxLength = 40; name.required = true;
    const g = el("textarea"); g.rows = 2; g.maxLength = 1000; g.placeholder = "Guardrail (không bắt buộc): lời dặn cho AI trong lĩnh vực này";
    f.append(name, g);
    let hard = null;
    if (staff()) { const lab = el("label", "dom-check"); hard = el("input"); hard.type = "checkbox"; lab.append(hard, " Lĩnh vực cứng (dữ liệu dùng chung)"); f.appendChild(lab); }
    const sub = el("button", "primary", "Thêm"); sub.type = "submit"; f.appendChild(sub);
    f.onsubmit = async (e) => {
      e.preventDefault();
      try {
        const r = await A.api("/s4/domains", { name: name.value, guardrail: g.value, kind: hard && hard.checked ? "hard" : "soft" });
        A.setDomains(r.domains); A.renderDomainBar(); sel = r.domain.id; tab = "data"; render();
      } catch (err) { alert(err.message); }
    };
    return f;
  }

  /* ================================================================ dữ liệu: lĩnh vực Friendly / cứng khác ===== */
  function friendlyData(d, pane) {
    pane.appendChild(el("p", "mem-help", d.kind === "hard"
      ? "Bộ dữ liệu dùng chung của lĩnh vực: dev / cán bộ tải lên, mọi người dùng được. Bật bộ nào thì AI chỉ trả lời từ bộ đó."
      : "Bộ dữ liệu riêng của bạn trong lĩnh vực này: tải lên, bật/tắt, xem, xoá. Không hiện ở lĩnh vực khác."
        + (d.can_share ? " Dev / cán bộ bấm \"Dùng chung\" ở một bộ để mọi người dùng được lĩnh vực này đều thấy và hỏi được bộ đó (chỉ đọc)." : "")));
    pane.appendChild(A.dataPanel(d));
  }

  /* ================================================================ đường nhanh ============ */
  const ROUTE = { field: "Tra trường", aggregate: "Đếm / liệt kê", text: "Văn bản" };
  const TYPE = { flag: "đánh dấu", date: "ngày", number: "số", id: "mã", enum: "nhóm", text: "chữ", empty: "trống" };
  async function fastTab(d, pane) {
    pane.appendChild(el("p", "mem-help", "Lúc nạp, hệ thống biên dịch từng bảng (kiểu cột, tên trường, cách hỏi) và tự kiểm bằng câu hỏi sinh từ chính dữ liệu. " +
      "Loại câu đạt ngưỡng thì code trả lời ngay (vài mili giây, không gọi AI); loại chưa đạt, hoặc câu không chắc, đi đường cũ (tìm kiếm + AI). " +
      "Bài tự kiểm chỉ bắt lỗi cấu trúc (tiêu đề trùng, cột lọc sai…), không thay được câu hỏi thật."));
    const box = el("div"); pane.appendChild(box);
    let st;
    try { st = await A.api("/s4/datasets?domain_id=" + d.id); } catch (e) { box.appendChild(errBox(e)); return; }
    const ready = st.datasets.filter((x) => x.status === "ready");
    if (!ready.length) { box.appendChild(el("p", "mem-empty", "Chưa có bộ dữ liệu nào sẵn sàng trong lĩnh vực này.")); return; }
    let busy = false;
    for (const ds of ready) {
      let r; try { r = await A.api("/s4/fastpath/" + ds.id); } catch (e) { box.appendChild(card(ds.name, errBox(e))); continue; }
      busy = busy || r.status === "queued" || r.status === "building";
      box.appendChild(fastCard(ds, r, () => renderMain()));
    }
    if (busy) fpTimer = setTimeout(() => { if (!$("domain-modal").hidden && tab === "fast") renderMain(); }, 2500);
  }
  function badge(on, label, test) {
    const b = span(label + (test && test.rate != null ? " " + Math.round(test.rate * 100) + "%" : ""), "tag " + (on ? "on" : "bad"));
    b.title = test ? `${test.pass}/${test.n} câu tự kiểm đạt` + (on ? "" : " — dưới ngưỡng: loại câu này đi đường cũ") : "chưa kiểm";
    return b;
  }
  function fastCard(ds, r, reload) {
    const head = el("div", "row-between");
    const t = el("div"); t.append(el("b", "", ds.name + " "), span({ ready: "sẵn sàng", queued: "đang chờ", building: "đang biên dịch…", error: "lỗi", skipped: "bỏ qua", none: "chưa biên dịch" }[r.status] || r.status, "tag" + (r.status === "ready" ? " on" : r.status === "error" ? " bad" : "")));
    head.appendChild(t);
    const mine = ds.user_id === A.me().id || staff();
    if (mine && !userView && r.status !== "building" && r.status !== "queued") head.appendChild(btn("Biên dịch lại", async () => { try { await A.api("/s4/fastpath/" + ds.id + "/rebuild", {}); reload(); } catch (e) { alert(e.message); } }));
    const c = card(null, head, el("p", "mem-help", r.message || ""));
    if (r.compile_ms != null) c.appendChild(el("p", "muted small", `Biên dịch ${r.compile_ms} ms · tự kiểm ${r.selftest_ms} ms · AI đặt tên trường cho ${r.llm_tables || 0} bảng`));
    (r.tables || []).filter((x) => !x.parent).forEach((tb) => {
      const line = el("div", "row");
      line.append(el("b", "", tb.name), span(`${tb.rows} dòng · mỗi dòng là một «${tb.entity_noun || tb.title_label}»`, "muted small"));
      ["field", "aggregate"].forEach((k) => {
        if (!tb.test[k]) return;
        const b = badge(tb.enabled[k] !== false && (k !== "aggregate" || r.aggregate_on), ROUTE[k], tb.test[k]);
        if (k === "aggregate" && !r.aggregate_on) { b.textContent += " · tắt ở ⚙"; b.title = "⚙ FASTPATH_AGGREGATE đang tắt (mặc định): câu đếm / liệt kê đi đường cũ. " + b.title; }
        line.appendChild(b);
      });
      const ft = table(["Cột", "Tên trường", "Kiểu", "Cách hỏi (gợi ý)"]);
      tb.fields.forEach((f) => ft.appendChild(row([f.name, f.label, (TYPE[f.type] || f.type) + (f.long ? " (dài)" : ""), [...f.cues, ...f.absent.map((a) => "≠ " + a)].join(" · ")])));
      const extra = [];
      const drop = Object.entries(tb.dropped || {});
      if (drop.length) extra.push(fold(`Gợi ý bị code bỏ (${drop.reduce((n, [, v]) => n + v.length, 0)})`, false,
        el("pre", "insp-pre", drop.map(([f, v]) => f + ": " + v.map(([c, why]) => `«${c}» (${why})`).join(", ")).join("\n"))));
      const fails = ["field", "aggregate"].flatMap((k) => ((tb.test[k] || {}).fails || []).map((x) => `[${ROUTE[k]}] ${x.q}\n   → ${x.got}`));
      if (fails.length) extra.push(fold("Câu tự kiểm chưa đạt (tối đa 5 mỗi loại)", false, el("pre", "insp-pre", fails.join("\n"))));
      c.appendChild(line);
      c.appendChild(fold("Cột, tên trường, cách hỏi" + (extra.length ? ", câu tự kiểm chưa đạt" : ""), false, scrollBox(ft), ...extra));
    });
    (r.tables || []).filter((x) => x.parent).forEach((tb) => c.appendChild(el("p", "muted small", `Bảng con «${tb.name}» (${tb.rows} dòng) gắn vào bảng cha qua cột «${tb.parent.via}».`)));
    if (r.texts) {
      const line = el("div", "row"); line.append(el("b", "", "Văn bản"), span(r.texts + " đoạn", "muted small"));
      if (r.text_test) line.appendChild(badge(r.text_test.on, ROUTE.text, r.text_test));
      c.appendChild(line);
    }
    return c;
  }

  /* ================================================================ Thủ tục (System 3) ===== */
  const SRC = { original: "Gốc", edit: "Sửa tay", scrape: "Cào" };
  const procView = { version: "draft", q: "", offset: 0 };
  async function strictData(d, pane) {
    let P;
    try { P = await A.api("/s4/admin/procs"); } catch (e) { pane.appendChild(errBox(e)); return; }
    const active = P.versions.find((v) => v.id === P.active_id);
    const top = el("div", "row-between");
    top.appendChild(el("div", "", "Strict mode đang dùng: " + (active ? `phiên bản ${active.id} · ${active.label} · ${active.n_records} thủ tục` : "?")));
    top.appendChild(btn("Xuất Excel", (b) => exportXlsx("active", b), "btn-ghost", "Tải DB thủ tục đang dùng thành tệp Excel: mọi bảng, liên kết row_id / proc_id, link cổng"));
    const job = el("div", "job"); job.hidden = true;
    pane.appendChild(card(null, top, job));
    // phiên bản
    const vt = table(["#", "Tên", "Nguồn", "Thủ tục", "Tạo lúc (UTC)", "Ghi chú", ""]);
    P.versions.forEach((v) => {
      const name = el("span", "", v.label);
      if (v.id === P.active_id) name.appendChild(span("đang dùng", "tag on"));
      if (v.id === P.original_id) name.appendChild(span("gốc", "tag"));
      const act = el("div");
      act.appendChild(btn("Xem", () => { procView.version = String(v.id); fillSel(); loadList(true); list.scrollIntoView({ behavior: "smooth" }); }));
      act.appendChild(btn("Xuất Excel", (b) => exportXlsx(v.id === P.active_id ? "active" : String(v.id), b)));
      if (v.id !== P.active_id) {
        act.appendChild(btn("So sánh", () => showDiff(String(P.active_id), String(v.id), "Bản đang dùng → phiên bản " + v.id)));
        act.appendChild(btn("Áp dụng", async () => {
          if (!confirm(`Strict mode sẽ chuyển sang phiên bản ${v.id} (${v.label}, ${v.n_records} thủ tục). Dựng lại DB mất khoảng 1 phút. Tiếp tục?`)) return;
          try { renderJob(job, (await A.api("/s4/admin/procs/apply", { version_id: v.id })).job); } catch (e) { alert(e.message); }
        }, "primary", "Strict mode chuyển sang phiên bản này"));
      }
      if (v.id !== P.active_id && v.id !== P.original_id) act.appendChild(btn("Xoá", async () => {
        if (!confirm(`Xoá phiên bản ${v.id} (${v.label})?`)) return;
        try { await A.api("/s4/admin/procs/versions/" + v.id, null, "DELETE"); } catch (e) { alert(e.message); }
        renderMain();
      }));
      const tr = row([v.id, name, SRC[v.source] || v.source, v.n_records, v.created_at, v.note, act]); tr.lastChild.className = "actions"; vt.appendChild(tr);
    });
    pane.appendChild(card("Phiên bản", scrollBox(vt)));
    // bản nháp
    const dr = P.draft;
    const drow = el("div", "row");
    const dDiff = btn("Xem thay đổi", () => showDiff(String(dr.base), "draft", "Phiên bản " + dr.base + " → bản nháp"));
    const dSave = btn("Lưu thành phiên bản", async () => {
      const label = prompt("Tên phiên bản mới:", "Sửa " + dr.changes + " thủ tục"); if (label === null) return;
      try { const r = await A.api("/s4/admin/procs/draft/save", { label }); alert(`Đã tạo phiên bản ${r.version_id} (so với bản đang dùng: +${r.diff.added}, −${r.diff.removed}, ${r.diff.changed} thay đổi). Bấm "Áp dụng" để Strict mode dùng phiên bản này.`); }
      catch (e) { alert(e.message); }
      procView.version = "draft"; renderMain();
    }, "primary");
    const dDrop = btn("Bỏ nháp", async () => { if (!confirm("Bỏ toàn bộ thay đổi trong bản nháp?")) return; try { await A.api("/s4/admin/procs/draft", null, "DELETE"); } catch (e) { alert(e.message); } renderMain(); });
    [dDiff, dSave, dDrop].forEach((b) => { b.disabled = !dr.changes; drow.appendChild(b); });
    pane.appendChild(card("Bản nháp", el("p", "muted small", dr.changes ? `dựa trên phiên bản ${dr.base}: ${dr.changes} thay đổi (${dr.deleted} xoá)` : "chưa có thay đổi — mở một thủ tục ở chế độ \"Bản nháp\" để sửa / xoá"), drow));
    // danh sách thủ tục
    const vsel = el("select"), q = el("input", "search"); q.type = "search"; q.placeholder = "Tìm theo tên, mã, lĩnh vực…"; q.value = procView.q;
    const fillSel = () => {
      vsel.innerHTML = "";
      const o = el("option", "", "Bản nháp (sửa được)"); o.value = "draft"; vsel.appendChild(o);
      P.versions.forEach((v) => { const x = el("option", "", `Phiên bản ${v.id} · ${v.label}` + (v.id === P.active_id ? " (đang dùng)" : "")); x.value = String(v.id); vsel.appendChild(x); });
      vsel.value = procView.version;
    };
    fillSel();
    const count = el("div", "muted small"), list = table(["Mã", "Tên thủ tục", "Lĩnh vực", "Tỉnh"]), more = btn("Xem thêm", () => loadList(false));
    async function loadList(reset) {
      if (reset) { procView.offset = 0; while (list.rows.length > 1) list.deleteRow(1); }
      let r;
      try { r = await A.api(`/s4/admin/procs/records?version=${procView.version}&q=${encodeURIComponent(procView.q)}&offset=${procView.offset}&limit=50`); } catch (e) { alert(e.message); return; }
      r.records.forEach((x) => {
        const name = el("span", "name", x.name); if (x.changed) name.appendChild(span("đã sửa", "tag warn"));
        const tr = row([x.proc_id, name, x.domain, x.province], "clickable"); tr.onclick = () => openProc(x.proc_id); list.appendChild(tr);
      });
      procView.offset += r.records.length;
      count.textContent = `${r.total} thủ tục` + (procView.version === "draft" && r.deleted.length ? ` · ${r.deleted.length} đã xoá trong nháp (${r.deleted.join(", ")})` : "");
      more.hidden = procView.offset >= r.total;
    }
    vsel.onchange = () => { procView.version = vsel.value; loadList(true); };
    let qt = null; q.oninput = () => { clearTimeout(qt); qt = setTimeout(() => { procView.q = q.value.trim(); loadList(true); }, 300); };
    const tools = el("div", "row"); tools.append(vsel, q);
    pane.appendChild(card("Thủ tục", tools, count, scrollBox(list), more));
    loadList(true);
    // cào dữ liệu: dài + chỉ khi cần -> thu gọn
    const lim = el("input", "num"); lim.type = "number"; lim.min = "0"; lim.value = "0";
    const go = btn("Cào dữ liệu mới", async () => {
      const limit = parseInt(lim.value || "0", 10) || 0;
      if (!confirm((limit ? `Cào thử ${limit} thủ tục` : "Cào toàn bộ thủ tục cấp Xã/Phường (khoảng 1.350, tải vài chục MB, có thể mất hàng chục phút)") + " từ dichvucong.gov.vn? Cần internet. Kết quả thành một phiên bản mới, CHƯA áp dụng.")) return;
      try { renderJob(job, (await A.api("/s4/admin/procs/scrape", { limit })).job); } catch (e) { alert(e.message); }
    }, "primary", "Cào lại từ dichvucong.gov.vn (cần internet, có thể mất hàng chục phút)");
    const lab = el("label", "small"); lab.append("Giới hạn ", lim, " (0 = tất cả)");
    const srow = el("div", "row"); srow.append(lab, go);
    pane.appendChild(fold("Cào dữ liệu từ dichvucong.gov.vn", false, el("p", "mem-help", "Kết quả cào thành một phiên bản mới (nguồn \"Cào\"), chưa áp dụng; so sánh rồi bấm Áp dụng ở bảng Phiên bản. Phải qua cổng kiểm chất lượng."), srow));
    renderJob(job, P.job);
  }
  const scrollBox = (t) => { const w = el("div", "dash-scroll"); w.appendChild(t); return w; };
  function renderJob(box, j) {
    clearTimeout(jobTimer);
    if (!j || j.state === "idle") { box.hidden = true; return; }
    box.hidden = false; box.className = "job " + (j.state === "running" ? "" : j.state); box.innerHTML = "";
    box.append(el("b", "", (j.kind === "scrape" ? "Cào dữ liệu" : "Áp dụng phiên bản") + ": "), el("span", "", j.message));
    if (j.kind === "scrape" && j.progress && j.progress.catalog) {
      const p = j.progress; box.appendChild(el("div", "small muted", `Danh mục: ${p.catalog} thủ tục · đã lấy chi tiết: ${p.details}`));
      const bar = el("div", "bar"); const i = el("i"); i.style.width = Math.min(100, (p.details / p.catalog) * 100) + "%"; bar.appendChild(i); box.appendChild(bar);
    }
    if (j.state === "running") jobTimer = setTimeout(async () => {
      try { const r = await A.api("/s4/admin/procs/job"); if (r.job.state === "done") { renderMain(); return; } renderJob(box, r.job); if (r.log && r.log.length) box.appendChild(el("pre", "", r.log.slice(-8).join("\n"))); }
      catch (_) { jobTimer = setTimeout(() => renderJob(box, j), 4000); }
    }, 2000);
  }
  async function exportXlsx(version, b) {
    const label = b.textContent;
    b.disabled = true; b.textContent = version === "active" ? "Đang xuất… (~20 giây)" : "Đang dựng + xuất… (~1-2 phút)";
    try {
      const res = await fetch("/s4/admin/procs/export.xlsx?version=" + encodeURIComponent(version));
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(typeof d.detail === "string" ? d.detail : res.statusText); }
      const name = (/filename="?([^";]+)"?/.exec(res.headers.get("Content-Disposition") || "") || [])[1] || "du_lieu_strict.xlsx";
      const url = URL.createObjectURL(await res.blob());
      const a = el("a"); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch (e) { alert("Xuất Excel lỗi: " + e.message); }
    finally { b.disabled = false; b.textContent = label; }
  }
  async function openProc(pid) {   // xem / sửa một thủ tục (bản nháp): chuỗi sửa trực tiếp, danh sách / đối tượng dạng JSON; máy chủ kiểm chuẩn dữ liệu
    let r;
    try { r = await A.api(`/s4/admin/procs/record/${encodeURIComponent(pid)}?version=${procView.version}`); } catch (e) { alert(e.message); return; }
    const editable = procView.version === "draft";
    const body = $("dash-rec-body"); body.innerHTML = ""; $("dash-rec-err").hidden = true;
    $("dash-rec-title").textContent = r.record.name + (r.changed ? " (đã sửa trong nháp)" : "");
    body.appendChild(el("div", "muted small", editable ? "Bản nháp: sửa xong bấm \"Lưu vào nháp\". Chuỗi sửa trực tiếp; danh sách / đối tượng sửa dạng JSON. Không đổi được mã thủ tục."
      : "Đang xem phiên bản " + procView.version + " (chỉ đọc). Chọn \"Bản nháp\" để sửa."));
    const inputs = {};
    Object.entries(r.record).forEach(([k, v]) => {
      const f = el("div", "field"), lab = el("label"); lab.append(el("span", "", k), el("small", "", (r.profile[k] || []).join(" / ")));
      const ta = el("textarea"); const isStr = typeof v === "string";
      ta.value = isStr ? v : JSON.stringify(v, null, 1);
      ta.rows = Math.min(14, Math.max(1, ta.value.split("\n").length, Math.ceil(ta.value.length / 110)));
      ta.readOnly = !editable || k === "proc_id"; ta.dataset.kind = isStr ? "str" : "json"; inputs[k] = ta;
      f.append(lab, ta); body.appendChild(f);
    });
    const foot = $("dash-rec-foot"); foot.innerHTML = "";
    const done = () => { $("dash-rec-modal").hidden = true; renderMain(); };
    if (editable) {
      if (r.changed) foot.appendChild(btn("Bỏ thay đổi", async () => { try { await A.api(`/s4/admin/procs/draft/${encodeURIComponent(pid)}/revert`, {}); done(); } catch (e) { alert(e.message); } }));
      foot.appendChild(btn("Xoá thủ tục (trong nháp)", async () => { if (!confirm("Xoá thủ tục này khỏi bản nháp?")) return; try { await A.api(`/s4/admin/procs/draft/${encodeURIComponent(pid)}`, null, "DELETE"); done(); } catch (e) { alert(e.message); } }));
      foot.appendChild(btn("Lưu vào nháp", async () => {
        const rec = {}, errs = [];
        Object.entries(inputs).forEach(([k, ta]) => { if (ta.dataset.kind === "str") rec[k] = ta.value; else { try { rec[k] = JSON.parse(ta.value); } catch (_) { errs.push(`"${k}" không phải JSON hợp lệ`); } } });
        if (errs.length) { $("dash-rec-err").textContent = errs.join(" · "); $("dash-rec-err").hidden = false; return; }
        try { await A.api(`/s4/admin/procs/draft/${encodeURIComponent(pid)}`, { record: rec }, "PUT"); done(); }
        catch (e) { $("dash-rec-err").textContent = e.message; $("dash-rec-err").hidden = false; }
      }, "primary"));
    }
    $("dash-rec-modal").hidden = false;
  }
  async function showDiff(a, b, title) {
    let d;
    try { d = await A.api(`/s4/admin/procs/diff?a=${a}&b=${b}`); } catch (e) { alert(e.message); return; }
    $("dash-diff-title").textContent = title;
    const body = $("dash-diff-body"); body.innerHTML = "";
    const c = d.counts, counts = el("div", "diff-counts");
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
        const r = await A.api(`/s4/admin/procs/diff/${encodeURIComponent(x.proc_id)}?a=${a}&b=${b}`);
        const s = (v) => (typeof v === "string" ? v : JSON.stringify(v, null, 1));
        r.fields.forEach((f) => { const box = el("div", "diff-field"); box.appendChild(el("b", "", f.field)); box.append(el("pre", "old", "− " + s(f.old)), el("pre", "new", "+ " + s(f.new))); li.appendChild(box); });
      } catch (e) { alert(e.message); }
    });
    if (!c.added && !c.removed && !c.changed) body.appendChild(el("p", "muted", "Hai phiên bản giống nhau."));
    $("dash-diff-modal").hidden = false;
  }
  async function strictStats(d, pane) {
    let r; try { r = await A.api("/s4/admin/stats"); } catch (e) { pane.appendChild(errBox(e)); return; }
    const t = table(["#", "Thủ tục", "Số lần", "Gần nhất (UTC)"]);
    r.procedures.forEach((p, i) => t.appendChild(row([i + 1, p.label + " (" + p.proc_id + ")", p.n, p.last_at])));
    if (!r.procedures.length) t.appendChild(row(["", "Chưa có dữ liệu", "", ""]));
    pane.appendChild(fold("Thủ tục được hỏi nhiều nhất (Strict)", true, el("p", "muted small", "Gộp theo mã chuẩn của phiên bản đang dùng (mã cũ đã cấp lại tính vào mã mới)."), scrollBox(t)));
    pane.appendChild(fold("Phản hồi 👍 / 👎 của Strict", false, el("p", "", `👍 ${r.feedback.strict.up} · 👎 ${r.feedback.strict.down}`)));
  }

  /* ================================================================ ABI ==================== */
  const ABI_LABEL = { departments: "Phòng ban", people: "Cán bộ", events: "Sự kiện", programs: "Chương trình", catalog: "Đối tác / SP / DV", posts: "Tin tức", pages: "Trang" };
  async function abiData(d, pane) {
    const box = el("div"); pane.appendChild(box);
    const load = async () => { try { draw(await A.api("/s4/abi/status")); } catch (e) { box.innerHTML = ""; box.appendChild(errBox(e)); } };
    function draw(r) {
      box.innerHTML = "";
      const act = r.active, st = r.state || {}, vs = r.versions || [];
      const building = vs.find((v) => v.dataset && v.dataset.status !== "ready"), busy = !!st.running || !!building;
      box.appendChild(card(null, el("div", "", "Lĩnh vực ABI đang dùng: " + (act ? `phiên bản ${act.id} · ${act.label} · đồng bộ ${fmtTime(act.synced_at)}` : "chưa có dữ liệu"))));
      const vt = table(["#", "Nguồn", "Đồng bộ lúc", "Kiểm lần cuối", ...Object.values(ABI_LABEL), "Chỉ mục", ""]);
      if (!vs.length) vt.appendChild(row(["Chưa có phiên bản nào: mở phần Đồng bộ."]));
      vs.forEach((v) => {
        const name = el("span", "", v.label);
        if (v.active) name.appendChild(span("đang dùng", "tag on"));
        if (v.newest) name.appendChild(span("mới nhất", "tag"));
        const a2 = el("div");
        if (!v.active) {
          a2.appendChild(btn("Dùng bản này", async (b) => { b.disabled = true; try { draw(await A.api(`/s4/abi/versions/${v.id}/activate`, {})); } catch (e) { alert(e.message); load(); } }, "primary", "Lĩnh vực ABI chuyển sang phiên bản này ngay"));
          a2.appendChild(btn("Xoá", async () => { if (!confirm(`Xoá phiên bản ${v.id} (${v.label}, ${fmtTime(v.synced_at)})?`)) return; try { draw(await A.api(`/s4/abi/versions/${v.id}`, null, "DELETE")); } catch (e) { alert(e.message); } }));
        }
        const ds = v.dataset ? (v.dataset.status === "ready" ? v.dataset.n_records + " đoạn" : v.dataset.status + " " + (v.dataset.progress || 0) + "%") : "chưa có";
        const tr = row([v.id, name, fmtTime(v.synced_at), fmtTime(v.checked_at), ...Object.keys(ABI_LABEL).map((k) => (v.counts || {})[k] ?? ""), ds, a2]); tr.lastChild.className = "actions"; vt.appendChild(tr);
      });
      box.appendChild(card("Phiên bản (mỗi nguồn giữ 2 bản mới nhất)", scrollBox(vt)));
      const job = el("div", "job");
      job.hidden = !busy && r.api_key !== "chưa có";
      job.textContent = r.api_key === "chưa có" ? "Chưa có khoá API của abi.com.vn: dev điền ở ⚙ Cài đặt → Lĩnh vực ABI → Khoá API."
        : st.running ? "Đang đồng bộ " + st.source + ": " + (st.step || "…") : building ? `Đang tạo chỉ mục cho phiên bản ${building.id}… ${building.dataset.progress || 0}%` : "";
      const brow = el("div", "row");
      (r.sources || []).forEach((src) => {
        const b = btn("Đồng bộ " + src.label, async () => {
          try { const res = await A.api("/s4/abi/sync", { source: src.id }); draw(res); if (!res.started && res.reason) alert(res.reason); } catch (e) { alert(e.message); }
        }, src.auto ? "primary" : "btn-ghost", src.auto ? "Tự đồng bộ theo lịch; bấm để tải lại ngay (chỉ tải phần đổi)" : "Staging chỉ đồng bộ khi bấm");
        b.disabled = busy; brow.appendChild(b);
      });
      const runs = table(["Bắt đầu", "Nguồn", "Kết quả", "Request", "Thời gian", "Thay đổi"]);
      (r.runs || []).forEach((x) => {
        const ch = x.diff ? Object.entries(x.diff).filter(([, v]) => v.added || v.removed || v.changed).map(([k, v]) => `${ABI_LABEL[k] || k}: +${v.added} −${v.removed} ~${v.changed}`).join("; ") || "không đổi" : "";
        const res = x.ok ? (x.result === "unchanged" ? "không có gì mới" : `phiên bản mới ${x.version_id}`) + (x.deleted_versions && x.deleted_versions.length ? ` · tự xoá ${x.deleted_versions.join(", ")}` : "") + (x.index_error ? " · chỉ mục lỗi: " + x.index_error : "")
          : x.skipped ? "bỏ qua: " + x.reason : "lỗi: " + (x.error || "");
        runs.appendChild(row([fmtTime(x.started), x.source || "prod", res, x.requests ?? "", x.ms ? Math.round(x.ms / 1000) + " s" : "", ch]));
      });
      box.appendChild(fold("Đồng bộ abi.com.vn (API chính thức, khoá API) — không bao giờ gọi trợ lý AI của web", busy, job, brow, el("h4", "", "Các lần đồng bộ gần đây"), scrollBox(runs)));
      clearTimeout(abiTimer);
      if (busy) abiTimer = setTimeout(() => { if (!$("domain-modal").hidden && tab === "data") load(); }, 2000);
    }
    load();
  }

  /* ================================================================ FLM (flm.fpt.edu.vn) === */
  const FLM_SHEETS = ["Chương trình", "Khung chương trình", "Môn học", "CLO", "Đánh giá"];
  async function flmData(d, pane) {
    const box = el("div"); pane.appendChild(box);
    const load = async () => { try { draw(await A.api("/s4/flm/status")); } catch (e) { box.innerHTML = ""; box.appendChild(errBox(e)); } };
    function draw(r) {
      box.innerHTML = "";
      const st = r.state || {}, vs = r.versions || [];
      const act = vs.find((v) => v.active);
      const building = vs.find((v) => v.dataset && v.dataset.status !== "ready"), busy = !!st.running || !!building;
      box.appendChild(card(null, el("div", "", "Lĩnh vực FLM đang dùng: " + (act ? `${act.label} · ${(act.curricula || []).map((c) => c.code).join(", ")}` : "chưa có dữ liệu — bấm Đồng bộ FLM")),
        el("p", "mem-help", `Ngành (⚙ FLM_PROGRAMS): ${(r.programs || []).join(", ") || "chưa đặt"} — mỗi ngành lấy khung chương trình mới nhất + đề cương các môn, chế độ khách (không có tài liệu / lịch buổi học).`)));
      const vt = table(["#", "Phiên bản", "Khung chương trình", ...FLM_SHEETS, "Bộ dữ liệu", ""]);
      if (!vs.length) vt.appendChild(row(["Chưa có phiên bản nào."]));
      vs.forEach((v) => {
        const name = el("span", "", v.label);
        if (v.active) name.appendChild(span("đang dùng", "tag on"));
        const a2 = el("div");
        if (!v.active) {
          a2.appendChild(btn("Dùng bản này", async (b) => { b.disabled = true; try { draw(await A.api(`/s4/flm/versions/${v.id}/activate`, {})); } catch (e) { alert(e.message); load(); } }, "primary"));
          a2.appendChild(btn("Xoá", async () => { if (!confirm(`Xoá ${v.label}?`)) return; try { draw(await A.api(`/s4/flm/versions/${v.id}`, null, "DELETE")); } catch (e) { alert(e.message); } }));
        }
        const ds = v.dataset ? (v.dataset.status === "ready" ? v.dataset.n_records + " bản ghi" : v.dataset.status + " " + (v.dataset.progress || 0) + "%") : "đã mất";
        const tr = row([v.id, name, (v.curricula || []).map((c) => `${c.code} (${c.subjects} môn)`).join(", "), ...FLM_SHEETS.map((k) => (v.counts || {})[k] ?? ""), ds, a2]);
        tr.lastChild.className = "actions"; vt.appendChild(tr);
      });
      box.appendChild(card(`Phiên bản (giữ ${r.keep || 2} bản mới nhất)`, scrollBox(vt)));
      const job = el("div", "job" + (st.captcha ? " warn" : ""));
      job.hidden = !busy;
      job.textContent = st.running ? (st.step || "Đang đồng bộ…") : building ? `Đang nạp phiên bản ${building.id}… ${building.dataset.progress || 0}%` : "";
      const go = (mode) => async () => {
        try { const res = await A.api("/s4/flm/sync", { mode }); draw(res); if (!res.started && res.reason) alert(res.reason); } catch (e) { alert(e.message); }
      };
      const b = btn("Đồng bộ FLM (khách)", go("guest"), "primary", "Các ngành trong ⚙ FLM_PROGRAMS, trang khách: mở Chrome riêng; nếu FLM đòi captcha thì tích \"I'm not a robot\" trong cửa sổ đó");
      const bf = btn("Đồng bộ đầy đủ (đăng nhập)", go("full"), "btn-ghost", "MỌI ngành + tài liệu, lịch từng buổi, câu hỏi (30–40 phút): mở Chrome riêng ở trang đăng nhập FLM, bạn tự đăng nhập trong cửa sổ đó");
      b.disabled = bf.disabled = busy;
      const runs = table(["Bắt đầu", "Kết quả", "Request", "Kết thúc"]);
      (r.runs || []).forEach((x) => runs.appendChild(row([fmtTime(x.started) + (x.mode === "full" ? " · đầy đủ" : ""), x.ok ? (x.result === "unchanged" ? `không có gì mới (phiên bản ${x.version})` : `phiên bản mới ${x.version}` + (x.pruned && x.pruned.length ? ` · tự xoá ${x.pruned.join(", ")}` : "")) : "lỗi: " + (x.error || ""), x.requests ?? "", fmtTime(x.finished)])));
      const brow = el("div", "row"); brow.append(b, bf);
      box.appendChild(fold("Đồng bộ flm.fpt.edu.vn (1 request/giây; không tự chạy theo lịch vì captcha / đăng nhập cần người bấm)", busy || !vs.length,
        el("p", "mem-help", "Khách: server mở cửa sổ Chrome riêng ở trang FLM; nếu FLM hiện captcha, tích \"I'm not a robot\" rồi bấm Continue (không cần đăng nhập). " +
          "Đầy đủ: cửa sổ Chrome riêng mở trang ĐĂNG NHẬP của FLM — bạn tự đăng nhập trong đó (Google @fpt.edu.vn hoặc Sign In); mật khẩu chỉ đi tới FLM / Google, " +
          "hệ thống không thấy và không lưu. Phiên giữ tới khi tắt server" + (r.login_open ? " (đang mở: lần sau không phải đăng nhập lại)" : "") +
          ". Lấy khung mới nhất của mọi ngành, môn combo / tự chọn, tài liệu, lịch từng buổi, câu hỏi (tệp đính kèm chỉ lấy link), khoảng 30–40 phút. " +
          "Dữ liệu đổi thì thành phiên bản mới; không đổi thì chỉ ghi lần kiểm."),
        job, brow, el("h4", "", "Các lần đồng bộ gần đây"), scrollBox(runs)));
      clearTimeout(abiTimer);
      if (busy) abiTimer = setTimeout(() => { if (!$("domain-modal").hidden && tab === "data") load(); }, 2000);
    }
    load();
  }

  /* ================================================================ chung (dev + cán bộ) === */
  const KIND = { table: "Bảng", rows: "Bảng (dòng chữ)", text: "Văn bản", mixed: "Bảng + văn bản" };
  async function allDatasets(pane) {
    pane.appendChild(el("h3", "dash-title", "Dữ liệu mọi người dùng"));
    pane.appendChild(el("p", "mem-help", "Mọi bộ dữ liệu đã tải lên, của mọi người dùng và mọi lĩnh vực. Dev và cán bộ mở xem / xoá được (dữ liệu riêng: chỉ mở khi cần hỗ trợ)."));
    let r; try { r = await A.api("/s4/admin/datasets"); } catch (e) { pane.appendChild(errBox(e)); return; }
    const names = Object.fromEntries(A.domains().map((d) => [d.id, d.name]));
    const t = table(["Người dùng", "Lĩnh vực", "Tên", "Loại", "Bản ghi", "Dung lượng", "Trạng thái", ""]);
    if (!r.datasets.length) t.appendChild(row(["Chưa có bộ dữ liệu nào."]));
    r.datasets.forEach((d) => {
      const st = el("span", d.status === "error" ? "tag bad" : "", d.status === "ready" ? (d.active ? "đang bật" : "đang tắt") : d.status);
      const act = el("div");
      if (d.status === "ready") act.appendChild(btn("Mở", () => A.openRecords(d)));
      if (d.status === "ready") act.appendChild(btn("Cách đọc", () => S4Inspect.reading(d.id), "btn-ghost", "Dòng tiêu đề đã chọn, cột tiêu đề, bản ghi đầu"));
      act.appendChild(btn("Xoá", async () => { if (!confirm(`Xoá bộ dữ liệu "${d.name}" của ${d.username}?`)) return; try { await A.api("/s4/datasets/" + d.id, null, "DELETE"); } catch (e) { alert(e.message); } renderMain(); }));
      const tr = row([d.username, names[d.domain_id] || d.domain_id, d.name + " (" + d.filename + ")", KIND[d.kind] || "", d.n_records, fmtSize(d.size_bytes), st, act]);
      tr.lastChild.className = "actions"; t.appendChild(tr);
    });
    pane.appendChild(scrollBox(t));
  }
  async function generalStats(pane) {
    pane.appendChild(el("h3", "dash-title", "Thống kê chung"));
    let r; try { r = await A.api("/s4/admin/stats"); } catch (e) { pane.appendChild(errBox(e)); return; }
    const ROLES = { user: "Người dân", can_bo: "Cán bộ", dev: "Dev" };
    const o = table(["Mục", "Số lượng"]);
    o.appendChild(row(["Friendly 👍 / 👎", r.feedback.friendly.up + " / " + r.feedback.friendly.down]));
    o.appendChild(row(["Strict 👍 / 👎", r.feedback.strict.up + " / " + r.feedback.strict.down]));
    Object.entries(ROLES).forEach(([k, name]) => o.appendChild(row(["Tài khoản " + name, r.roles[k] || 0])));
    pane.appendChild(fold("Phản hồi và tài khoản", true, o));
    const dl = el("div", "row");
    [["csv", "Tải phản hồi (.csv, mở bằng Excel)"], ["jsonl", "Tải phản hồi (.jsonl)"]].forEach(([ext, label]) => {
      const a = el("a", "btn-ghost", label); a.href = "/s4/admin/feedback." + ext; a.setAttribute("download", ""); dl.appendChild(a);
    });
    pane.appendChild(fold("Tải các câu đã 👍 / 👎 (đã che CCCD / số điện thoại)", false, dl));
    pane.appendChild(el("p", "muted small", "Thống kê theo lĩnh vực: chọn lĩnh vực ở bên trái → tab Thống kê (hiện có cho Thủ tục)."));
  }

  window.S4Dash = { init, open, close };
})();

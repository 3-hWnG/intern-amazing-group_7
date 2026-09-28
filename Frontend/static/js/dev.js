/* Bảng Dev / Admin Portal: Giám sát toàn diện hệ thống, Metrics, Trace, CSDL, User & Telemetry */
window.Dev = (function () {
  let on = false;               // server có đang ghi vết không
  let open = false;             // bảng có đang mở không
  let available = false;

  const $ = (id) => document.getElementById(id);

  function esc(v) { return String(v === undefined || v === null ? "" : v); }
  // Escape HTML thật — mọi dữ liệu do người dùng/CSDL đưa vào innerHTML phải qua đây.
  function h(v) {
    return esc(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function row(label, value, cls) {
    const d = document.createElement("div");
    d.className = "dev-row" + (cls ? " " + cls : "");
    const k = document.createElement("span");
    k.className = "dev-k"; k.textContent = label;
    const v = document.createElement("span");
    v.className = "dev-v"; v.textContent = esc(value);
    d.append(k, v);
    return d;
  }

  /* ---------------- vết chạy ---------------- */
  function describe(e) {
    let text = `+${e.at_ms}ms  ${e.kind}`;
    if (e.ms !== undefined) text += ` (${e.ms} ms)`;
    if (e.kind === "understand") {
      text += `  intent=${e.intent}  gác=${e.gate}  → ${e.route}`;
      if ((e.missing || []).length) text += `  thiếu=[${e.missing.join(", ")}]`;
    } else if (e.kind === "search_queries") {
      text += `  [${(e.queries || []).join(" · ")}]`;
    } else if (e.kind === "keyword_search") {
      text += `  khoá="${e.keyword}"  khớp chắc=${e.strong}  ${e.n_hits} kết quả`;
    } else if (e.kind === "extract_keys") {
      text += `  lần ${e.attempt}  khoá="${e.primary_keyword}"  vực="${e.domain}"`;
    } else if (e.kind === "lookup") {
      text += `  lần ${e.attempt}  ${e.n_hits} ứng viên  khớp chắc=${e.strong}`;
    } else if (e.kind === "mcq_ask") {
      text += `  hỏi trục=${e.axis}  ${e.n_options} lựa chọn`;
    } else if (e.kind === "build_table") {
      text += `  thủ tục=${e.proc_id}  đã chọn=${e.picked}`;
    } else if (e.kind === "verify") {
      text += `  ${e.verdict}  lần ${e.attempt || 1}`;
      if (e.reason) text += `  (${e.reason})`;
    } else if (e.note) {
      text += `  ${e.note}`;
    }
    return text;
  }

  function renderTrace(t) {
    const box = document.createElement("div");
    box.className = "dev-trace";

    const head = document.createElement("div");
    head.className = "dev-trace-head";
    head.textContent = `${t.question || "(không có câu hỏi)"} — ${t.total_ms || 0} ms`;
    box.appendChild(head);

    const body = document.createElement("div");
    body.className = "dev-trace-body";
    (t.events || []).forEach((e) => {
      const line = document.createElement("div");
      line.className = "dev-event";
      line.textContent = describe(e);
      body.appendChild(line);
    });
    box.appendChild(body);
    head.onclick = () => body.classList.toggle("open");
    return box;
  }

  async function refreshTrace() {
    const host = $("dev-traces");
    if (!host) return;
    try {
      const data = await API.get("/api/dev/trace?limit=15");
      host.innerHTML = "";
      if (!data.traces || !data.traces.length) {
        host.innerHTML = '<p class="muted small">Chưa có vết chạy nào.</p>';
        return;
      }
      data.traces.forEach((t) => host.appendChild(renderTrace(t)));
    } catch (_) { /* im lặng */ }
  }

  async function refreshStatus() {
    try {
      const s = await API.get("/api/dev/status");
      on = Boolean(s.developer_mode);
      if ($("dev-toggle")) {
        $("dev-toggle").setAttribute("aria-pressed", on ? "true" : "false");
        $("dev-toggle").textContent = on ? "Ghi vết: BẬT" : "Ghi vết: TẮT";
      }
      renderConfig(s);
    } catch (_) {}
  }

  function renderConfig(s) {
    const host = $("dev-config");
    if (!host) return;
    host.innerHTML = "";
    host.appendChild(row("LLM Model", s.llm_model));
    host.appendChild(row("Hệ thống mặc định", s.default_system));
    host.appendChild(row("Queue Concurrency", s.queue_concurrency || "4"));
    host.appendChild(row("MCP Transport", s.mcp_transport));
    host.appendChild(row("Search Provider", s.search_provider));
    host.appendChild(row("Verifier Enabled", s.verifier_enabled ? "Bật" : "Tắt"));
    host.appendChild(row("Dev Tools", s.dev_tools_enabled ? "Bật" : "Tắt"));
  }

  /* ---------------- Metrics Realtime ---------------- */
  async function refreshMetrics() {
    try {
      const m = await API.get("/api/dev/metrics");
      if ($("m-online-users")) $("m-online-users").textContent = m.online_users || 0;
      if ($("m-online-label") && m.online_window_seconds) {
        $("m-online-label").textContent = `Đang online (${Math.round(m.online_window_seconds / 60)} phút)`;
      }
      if ($("m-logged-in-users")) $("m-logged-in-users").textContent = m.logged_in_users || 0;
      if ($("m-queue-depth")) $("m-queue-depth").textContent = m.queue_depth || 0;
      if ($("m-queue-concurrency")) $("m-queue-concurrency").textContent = m.queue_concurrency || 4;
      if ($("m-total-users")) $("m-total-users").textContent = m.total_users || 0;
      if ($("m-total-convs")) $("m-total-convs").textContent = m.total_conversations || 0;
      if ($("m-total-msgs")) $("m-total-msgs").textContent = m.total_messages || 0;
      if ($("m-unmatched-queries")) $("m-unmatched-queries").textContent = m.unmatched_queries_unresolved || 0;
    } catch (_) {}
  }

  /* ---------------- Modal Thêm / Duyệt Synonym ---------------- */
  let activeUnmatchedItem = null;

  function openSynonymModal(rawDefault = "", canonDefault = "", unmatchedItem = null) {
    activeUnmatchedItem = unmatchedItem;
    const modal = $("synonym-modal");
    const backdrop = $("synonym-backdrop");
    if (!modal) return;
    $("syn-raw-input").value = rawDefault;
    $("syn-canon-input").value = canonDefault;
    const errBox = $("syn-modal-error");
    if (errBox) {
      errBox.style.display = "none";
      errBox.textContent = "";
    }
    modal.removeAttribute("hidden");
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    if (backdrop) backdrop.classList.add("open");
    $("syn-raw-input").focus();
  }

  function closeSynonymModal() {
    activeUnmatchedItem = null;
    const modal = $("synonym-modal");
    const backdrop = $("synonym-backdrop");
    if (modal) {
      modal.setAttribute("hidden", "");
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }
    if (backdrop) backdrop.classList.remove("open");
  }

  async function saveSynonymModal() {
    const raw = ($("syn-raw-input").value || "").trim();
    const canon = ($("syn-canon-input").value || "").trim();
    const errBox = $("syn-modal-error");
    if (!raw || !canon) {
      if (errBox) {
        errBox.textContent = "Vui lòng nhập cả từ thô và từ khóa chuẩn.";
        errBox.style.display = "block";
      }
      return;
    }
    const saveBtn = $("syn-modal-save");
    if (saveBtn) saveBtn.disabled = true;
    try {
      if (activeUnmatchedItem) {
        await API.post(`/api/dev/telemetry/unmatched/${activeUnmatchedItem.id}/resolve`, {
          raw_term: raw,
          canonical_keyword: canon,
          notes: `Đã thêm synonym: ${raw} -> ${canon}`
        });
        refreshUnmatched();
      } else {
        await API.post("/api/dev/synonyms", { raw_term: raw, canonical_keyword: canon });
      }
      refreshSynonyms();
      closeSynonymModal();
    } catch (e) {
      if (errBox) {
        errBox.textContent = "Lỗi: " + e.message;
        errBox.style.display = "block";
      }
    } finally {
      if (saveBtn) saveBtn.disabled = false;
    }
  }

  /* Kết quả cuối của ca LLM 1: đủ để dev quyết \"LLM 1 làm đúng chưa\". */
  function outcomeCell(item) {
    const labels = {
      resolved_ok: ["success", "Người dân đã chốt"],
      llm1_strong: ["success", "LLM 1 khớp chắc"],
      llm1_weak: ["warn", "LLM 1 khớp yếu"],
      not_found: ["warn", "Không tìm ra"],
      user_rejected: ["warn", "Người dân bác bỏ"],
    };
    const [cls, text] = labels[item.outcome] || ["", item.outcome || "Chưa rõ"];
    let html = `<span class="badge ${cls}">${h(text)}</span>`;
    if (item.final_proc_name) {
      html += `<div class="small" style="margin-top:4px;">→ <strong>${h(item.final_proc_name)}</strong></div>`;
    } else if ((item.top_candidates || []).length) {
      html += `<div class="small muted" style="margin-top:4px;">Gợi ý: ${h(item.top_candidates.map((c) => c.name).filter(Boolean).slice(0, 2).join(" · "))}</div>`;
    }
    return html;
  }

  /* ---------------- Unmatched Queries Telemetry ---------------- */
  async function refreshUnmatched() {
    const host = $("dev-unmatched-list");
    if (!host) return;
    host.innerHTML = '<p class="muted small">Đang tải danh sách từ khóa trượt...</p>';
    try {
      const res = await API.get("/api/dev/telemetry/unmatched?limit=30");
      host.innerHTML = "";
      const items = res.items || [];
      if (!items.length) {
        host.innerHTML = '<p class="muted small text-center" style="padding:15px;">Tuyệt vời! Chưa có câu hỏi nào bị trượt từ khóa FTS5.</p>';
        return;
      }

      const table = document.createElement("table");
      table.className = "dev-table";
      table.innerHTML = `
        <thead>
          <tr>
            <th>Thời gian</th>
            <th>Câu hỏi người dân</th>
            <th>Khoá LLM 1 rút trích</th>
            <th>Kết quả để duyệt</th>
            <th>Trạng thái</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
      const tbody = table.querySelector("tbody");

      items.forEach((item) => {
        const tr = document.createElement("tr");
        const timeStr = (item.created_at || "").replace("T", " ").slice(5, 19);
        const keys = item.extracted_keys || {};
        const keyDesc = keys.primary_keyword ? `<strong>${h(keys.primary_keyword)}</strong> (${h(keys.domain || "không rõ vực")})` : "(chưa có)";

        tr.innerHTML = `
          <td><small class="muted">${h(timeStr)}</small></td>
          <td>${h(item.query)}</td>
          <td>${keyDesc}</td>
          <td>${outcomeCell(item)}</td>
          <td>${item.resolved ? '<span class="badge success">Đã giải quyết</span>' : '<span class="badge warn">Chưa xử lý</span>'}</td>
          <td></td>
        `;
        const actTd = tr.querySelector("td:last-child");
        if (!item.resolved) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "dev-btn small";
          btn.textContent = "Thêm synonym";
          btn.onclick = () => {
            const rawDefault = (item.query || "").trim();
            const canonDefault = (keys.primary_keyword || "").trim();
            openSynonymModal(rawDefault, canonDefault, item);
          };
          actTd.appendChild(btn);
        } else {
          actTd.textContent = "—";
        }
        tbody.appendChild(tr);
      });

      host.appendChild(table);
    } catch (e) {
      host.innerHTML = '<p class="muted small danger">Lỗi tải dữ liệu: ' + h(e.message) + '</p>';
    }
  }

  /* ---------------- Dynamic Synonyms ---------------- */
  async function refreshSynonyms() {
    const host = $("dev-syn-list");
    if (!host) return;
    try {
      const res = await API.get("/api/dev/synonyms");
      host.innerHTML = "";
      const synonyms = res.synonyms || [];
      if (!synonyms.length) {
        host.innerHTML = '<p class="muted small" style="margin:8px 0;">Chưa có từ đồng nghĩa động nào.</p>';
        return;
      }
      const table = document.createElement("table");
      table.className = "dev-table";
      table.innerHTML = `
        <thead>
          <tr>
            <th>Từ thô / viết tắt</th>
            <th>Từ khóa chuẩn</th>
            <th>Thời gian</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
      const tbody = table.querySelector("tbody");
      synonyms.forEach((syn) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><code>${h(syn.raw_term)}</code></td>
          <td><strong>${h(syn.canonical_keyword)}</strong></td>
          <td><small class="muted">${h((syn.created_at || "").replace("T", " ").slice(0, 19))}</small></td>
          <td><button type="button" class="dev-btn small danger">Xóa</button></td>
        `;
        const delBtn = tr.querySelector("button");
        delBtn.onclick = async () => {
          if (!confirm(`Xóa synonym "${syn.raw_term}"?`)) return;
          delBtn.disabled = true;
          try {
            await API.del(`/api/dev/synonyms/${syn.id}`);
            refreshSynonyms();
          } catch (e) {
            alert("Lỗi: " + e.message);
            delBtn.disabled = false;
          }
        };
        tbody.appendChild(tr);
      });
      host.appendChild(table);
    } catch (e) {
      host.innerHTML = '<p class="muted small danger">Lỗi tải synonyms: ' + h(e.message) + '</p>';
    }
  }

  /* ---------------- Procedures DB Stats ---------------- */
  async function refreshProceduresStats() {
    const host = $("dev-proc-stats");
    if (!host) return;
    try {
      const data = await API.get("/api/dev/db/procedures/stats");
      host.innerHTML = "";
      if (!data.available) {
        host.innerHTML = `<p class="muted small danger">Chưa tìm thấy tệp procedures.db tại ${h(data.path)}.</p>`;
        return;
      }
      host.appendChild(row("Trạng thái", "Đang hoạt động (active)", "success"));
      host.appendChild(row("Thủ tục hiện hành (active)", data.active));
      host.appendChild(row("Bản ghi lưu trữ cũ (archived)", data.archived));
      host.appendChild(row("Thủ tục hết hiệu lực (expired)", data.expired));
      host.appendChild(row("Tệp biểu mẫu đính kèm", data.files_count));
      
      const topDomains = (data.top_domains || []).map((d) => `${d.domain}: ${d.c}`).join(" · ");
      if (topDomains) host.appendChild(row("Lĩnh vực tiêu biểu", topDomains));
    } catch (_) {}
  }

  /* ---------------- Procedures DB Backups ---------------- */
  async function refreshProceduresBackups() {
    const host = $("dev-proc-backups");
    if (!host) return;
    try {
      const data = await API.get("/api/dev/db/procedures/backups");
      host.innerHTML = "";
      const backups = data.backups || [];
      if (!backups.length) {
        host.innerHTML = '<p class="muted small" style="margin:6px 0;">Chưa có bản sao lưu nào.</p>';
        return;
      }
      const table = document.createElement("table");
      table.className = "dev-table";
      table.innerHTML = `
        <thead>
          <tr>
            <th>Tên tệp</th>
            <th>Dung lượng</th>
            <th>Thời gian tạo</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
      const tbody = table.querySelector("tbody");
      backups.forEach((b) => {
        const tr = document.createElement("tr");
        const timeStr = (b.created_at || "").replace("T", " ").slice(0, 19);
        tr.innerHTML = `
          <td><code>${h(b.filename)}</code></td>
          <td>${b.size_kb} KB</td>
          <td><small class="muted">${h(timeStr)}</small></td>
          <td><button type="button" class="dev-btn small danger">Phục hồi</button></td>
        `;
        const rBtn = tr.querySelector("button");
        rBtn.onclick = async () => {
          if (!confirm(`Bạn có chắc muốn phục hồi CSDL từ bản sao lưu "${b.filename}"?`)) return;
          rBtn.disabled = true;
          const statusBox = $("dev-proc-import-status");
          if (statusBox) statusBox.innerHTML = `<p class="muted small">Đang phục hồi từ ${h(b.filename)}...</p>`;
          try {
            const res = await API.post("/api/dev/db/procedures/rollback", { backup_filename: b.filename });
            if (statusBox) statusBox.innerHTML = `<p class="small success" style="color:var(--success, #22c55e);">✅ ${h(res.message)}</p>`;
            refreshProceduresStats();
            refreshProceduresBackups();
          } catch (err) {
            if (statusBox) statusBox.innerHTML = `<p class="small danger">❌ Lỗi: ${h(err.message)}</p>`;
            rBtn.disabled = false;
          }
        };
        tbody.appendChild(tr);
      });
      host.appendChild(table);
    } catch (e) {
      host.innerHTML = '<p class="muted small danger">Lỗi tải danh sách sao lưu: ' + h(e.message) + '</p>';
    }
  }

  /* ---------------- Users Management ---------------- */
  async function refreshUsers() {
    const host = $("dev-users-list");
    if (!host) return;
    host.innerHTML = '<p class="muted small">Đang tải danh sách tài khoản...</p>';
    try {
      const res = await API.get("/api/dev/users");
      host.innerHTML = "";
      const users = res.users || [];
      if (!users.length) {
        host.innerHTML = '<p class="muted small">Chưa có người dùng nào.</p>';
        return;
      }

      const table = document.createElement("table");
      table.className = "dev-table";
      table.innerHTML = `
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Tên hiển thị</th>
            <th>Vai trò</th>
            <th>Số hội thoại</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
      const tbody = table.querySelector("tbody");

      users.forEach((u) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${u.id}</td>
          <td><strong>${h(u.email)}</strong></td>
          <td>${h(u.display_name || "—")}</td>
          <td>
            <button type="button" class="badge ${u.is_admin ? "admin" : "user"} role-toggle">
              ${u.is_admin ? "Admin" : "User"}
            </button>
          </td>
          <td>${u.n_conversations || 0}</td>
          <td class="dev-user-actions">
            <button type="button" class="link small view-chat-btn" title="Xem hội thoại + vết chạy của user này">Xem chat</button>
            <button type="button" class="link small danger nuke-btn" title="Xoá toàn bộ cuộc trò chuyện của user này">Nuke chats</button>
            <button type="button" class="link small danger del-user-btn" title="Xoá tài khoản">Xoá</button>
          </td>
        `;

        const roleBtn = tr.querySelector(".role-toggle");
        roleBtn.onclick = async () => {
          const next = !u.is_admin;
          if (!confirm(`Đổi quyền của ${u.email} thành ${next ? "Admin" : "User"}?`)) return;
          try {
            await API.post(`/api/dev/users/${u.id}/role`, { is_admin: next });
            refreshUsers();
          } catch (err) { alert("Lỗi: " + err.message); }
        };

        tr.querySelector(".view-chat-btn").onclick = () => openConvBrowser(u.id);

        const nukeBtn = tr.querySelector(".nuke-btn");
        nukeBtn.onclick = async () => {
          if (!confirm(`Bạn có chắc muốn xoá TOÀN BỘ hội thoại của user ${u.email}?`)) return;
          try {
            await API.post(`/api/dev/users/${u.id}/nuke`, {});
            alert("Đã xoá sạch lịch sử chat của user này.");
            refreshUsers();
          } catch (err) { alert("Lỗi: " + err.message); }
        };

        const delBtn = tr.querySelector(".del-user-btn");
        delBtn.onclick = async () => {
          if (!confirm(`Xoá tài khoản ${u.email} và toàn bộ dữ liệu kèm theo?`)) return;
          try {
            await API.del(`/api/dev/users/${u.id}`);
            refreshUsers();
          } catch (err) { alert("Lỗi: " + err.message); }
        };

        tbody.appendChild(tr);
      });
      host.appendChild(table);
    } catch (e) {
      host.innerHTML = '<p class="muted small danger">Lỗi: ' + h(e.message) + '</p>';
    }
  }

  /* ---------------- Reset Dữ liệu ---------------- */
  function wireReset() {
    const btn = $("dev-reset");
    if (!btn) return;
    btn.onclick = async () => {
      const scope = prompt(
        "Nhập phạm vi xoá:\n" +
        "  my_conversations  -> chỉ xoá các cuộc trò chuyện của bạn\n" +
        "  all_conversations -> xoá mọi cuộc trò chuyện của toàn hệ thống\n" +
        "  everything        -> xoá sạch cả tài khoản người dùng\n\n" +
        "Gõ đúng một trong 3 từ trên:", "my_conversations");
      if (!scope) return;
      const confirmWord = prompt('Gõ chữ "XOA" (viết hoa, không dấu) để xác nhận:');
      if (confirmWord !== "XOA") {
        alert("Đã huỷ thao tác.");
        return;
      }
      try {
        const res = await API.post("/api/dev/reset", { scope, confirm: confirmWord });
        alert("Đã thực hiện xong: " + (res.note || res.scope));
        location.reload();
      } catch (e) {
        alert("Lỗi: " + e.message);
      }
    };
  }

  /* ---------------- Hội thoại & vết chạy của bất kỳ user ---------------- */
  async function loadConvUsers(selectUserId) {
    const sel = $("dev-conv-user");
    if (!sel) return;
    try {
      const res = await API.get("/api/dev/users?limit=200");
      sel.innerHTML = "";
      (res.users || []).forEach((u) => {
        const o = document.createElement("option");
        o.value = u.id;
        o.textContent = `${u.email} (${u.n_conversations || 0} hội thoại)`;
        sel.appendChild(o);
      });
      if (selectUserId) sel.value = String(selectUserId);
      await loadUserConvs();
    } catch (e) {
      sel.innerHTML = "";
      $("dev-conv-messages").innerHTML = '<p class="small danger">Lỗi: ' + h(e.message) + "</p>";
    }
  }

  async function loadUserConvs() {
    const uid = $("dev-conv-user").value;
    const sel = $("dev-conv-select");
    sel.innerHTML = "";
    $("dev-conv-messages").innerHTML = "";
    $("dev-msg-trace-wrap").hidden = true;
    if (!uid) return;
    const res = await API.get(`/api/dev/users/${uid}/conversations`);
    const convs = res.conversations || [];
    if (!convs.length) {
      sel.innerHTML = '<option value="">(user này chưa có hội thoại)</option>';
      return;
    }
    convs.forEach((c) => {
      const o = document.createElement("option");
      o.value = c.id;
      o.textContent = `#${c.id} · ${c.title} · ${c.n_messages} tin`;
      sel.appendChild(o);
    });
    await loadConvMessages();
  }

  async function loadConvMessages() {
    const cid = $("dev-conv-select").value;
    const host = $("dev-conv-messages");
    host.innerHTML = "";
    $("dev-msg-trace-wrap").hidden = true;
    if (!cid) return;
    try {
      const res = await API.get(`/api/dev/conversations/${cid}/messages`);
      (res.messages || []).forEach((m) => {
        const box = document.createElement("div");
        box.className = "dev-msg " + m.role;
        const who = document.createElement("strong");
        who.textContent = m.role === "user" ? "Người dân: " : "Trợ lý: ";
        const text = document.createElement("span");
        text.textContent = (m.content || "").slice(0, 400);
        box.append(who, text);
        if (m.role !== "user") {
          const meta = document.createElement("small");
          meta.className = "muted";
          meta.textContent = ` [${m.kind || "?"}${m.verdict ? " · " + m.verdict : ""}]`;
          box.appendChild(meta);
          if (m.has_trace) {
            const b = document.createElement("button");
            b.type = "button";
            b.className = "link small";
            b.textContent = " 🔍 Xem vết";
            b.onclick = () => showMessageTrace(m.id);
            box.appendChild(b);
          }
        }
        host.appendChild(box);
      });
    } catch (e) {
      host.innerHTML = '<p class="small danger">Lỗi: ' + h(e.message) + "</p>";
    }
  }

  async function showMessageTrace(messageId) {
    const wrap = $("dev-msg-trace-wrap");
    const host = $("dev-msg-trace");
    wrap.hidden = false;
    wrap.open = true;
    host.innerHTML = '<p class="muted small">Đang tải vết…</p>';
    try {
      const res = await API.get(`/api/dev/messages/${messageId}/trace`);
      host.innerHTML = "";
      const t = res.trace || {};
      const tr = t.trace || {};
      const head = document.createElement("div");
      head.className = "small muted";
      head.textContent = `Hệ thống: ${t.system || "?"} · ${t.total_ms || 0} ms · ${(t.created_at || "").replace("T", " ").slice(0, 19)}`;
      host.appendChild(head);
      const box = renderTrace({ question: t.question, total_ms: t.total_ms, events: tr.events || [] });
      box.querySelector(".dev-trace-body").classList.add("open");
      host.appendChild(box);
      if (res.evidence) {
        const d = document.createElement("details");
        d.className = "dev-sect";
        const s = document.createElement("summary");
        s.textContent = "Evidence Pack (bằng chứng đã dùng)";
        const pre = document.createElement("pre");
        pre.className = "dev-pre";
        pre.textContent = JSON.stringify(res.evidence, null, 2).slice(0, 6000);
        d.append(s, pre);
        host.appendChild(d);
      }
    } catch (e) {
      host.innerHTML = '<p class="small danger">' + h(e.message) + "</p>";
    }
  }

  /* Mở thẳng tab Hội thoại cho một user (nút \"Xem chat\" ở tab Người dùng). */
  function openConvBrowser(userId) {
    const btn = document.querySelector('.dev-tab-nav-btn[data-tab="dev-tab-convs"]');
    if (btn) btn.click();
    loadConvUsers(userId);
  }

  /* ---------------- Tab Switching ---------------- */
  function initTabs() {
    const tabBtns = document.querySelectorAll(".dev-tab-nav-btn");
    tabBtns.forEach((btn) => {
      btn.onclick = () => {
        tabBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const target = btn.dataset.tab;
        document.querySelectorAll(".dev-tab-panel").forEach((panel) => {
          panel.hidden = panel.id !== target;
        });

        // Tải dữ liệu tương ứng khi chọn tab
        if (target === "dev-tab-metrics") refreshMetrics();
        if (target === "dev-tab-traces") refreshTrace();
        if (target === "dev-tab-unmatched") { refreshUnmatched(); refreshSynonyms(); }
        if (target === "dev-tab-procedures") { refreshProceduresStats(); refreshProceduresBackups(); }
        if (target === "dev-tab-users") refreshUsers();
        if (target === "dev-tab-convs") loadConvUsers();
      };
    });
  }

  async function init(devToolsEnabled) {
    available = Boolean(devToolsEnabled);
    const trigger = $("dev-open");
    if (!trigger) return;
    trigger.hidden = !available;
    if (!available) return;

    function setOpen(val) {
      open = Boolean(val);
      const panel = $("dev-panel");
      const backdrop = $("dev-backdrop");
      if (panel) {
        panel.classList.toggle("open", open);
        panel.setAttribute("aria-hidden", open ? "false" : "true");
      }
      if (backdrop) {
        backdrop.classList.toggle("open", open);
      }
      if (trigger) {
        trigger.setAttribute("aria-pressed", open ? "true" : "false");
      }
      if (open) {
        refreshStatus();
        refreshMetrics();
        refreshTrace();
      }
    }

    trigger.onclick = () => {
      setOpen(!open);
    };

    if ($("dev-close")) {
      $("dev-close").onclick = () => {
        setOpen(false);
      };
    }
    if ($("dev-backdrop")) {
      $("dev-backdrop").onclick = () => {
        setOpen(false);
      };
    }
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && open) {
        setOpen(false);
      }
    });

    // Synonym modal events
    if ($("syn-modal-close")) $("syn-modal-close").onclick = closeSynonymModal;
    if ($("syn-modal-cancel")) $("syn-modal-cancel").onclick = closeSynonymModal;
    if ($("syn-modal-save")) $("syn-modal-save").onclick = saveSynonymModal;
    if ($("synonym-backdrop")) $("synonym-backdrop").onclick = closeSynonymModal;

    if ($("dev-toggle")) {
      $("dev-toggle").onclick = async () => {
        const next = !on;
        await API.post("/api/dev/toggle", { enabled: next });
        await refreshStatus();
      };
    }

    if ($("dev-refresh")) $("dev-refresh").onclick = () => { refreshStatus(); refreshTrace(); refreshMetrics(); };
    if ($("dev-clear")) $("dev-clear").onclick = async () => { await API.del("/api/dev/trace"); refreshTrace(); };

    // Thêm dynamic synonym thủ công
    if ($("dev-syn-add-btn")) {
      $("dev-syn-add-btn").onclick = async () => {
        const raw = ($("dev-syn-raw").value || "").trim();
        const canon = ($("dev-syn-canon").value || "").trim();
        if (!raw || !canon) { alert("Vui lòng nhập cả từ thô và từ khóa chuẩn."); return; }
        try {
          await API.post("/api/dev/synonyms", { raw_term: raw, canonical_keyword: canon });
          $("dev-syn-raw").value = "";
          $("dev-syn-canon").value = "";
          refreshSynonyms();
        } catch (e) {
          alert("Lỗi: " + e.message);
        }
      };
    }

    // Export procedures JSONL
    if ($("dev-export-procs-btn")) {
      $("dev-export-procs-btn").onclick = () => {
        location.href = "/api/dev/db/procedures/export?format=jsonl";
      };
    }

    // Import procedures JSONL
    const fileInput = $("dev-import-procs-file");
    const statusBox = $("dev-proc-import-status");
    if (fileInput) {
      fileInput.onchange = async () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file) return;
        if (!confirm(`Nạp tệp "${file.name}" (${(file.size / 1024).toFixed(1)} KB) vào procedures.db?\nHệ thống sẽ tự động sao lưu CSDL hiện tại vào thư mục runtime/backups.`)) {
          fileInput.value = "";
          return;
        }
        if (statusBox) statusBox.innerHTML = '<p class="muted small">Đang tải lên và nạp CSDL (tự động sao lưu)...</p>';
        try {
          const form = new FormData();
          form.append("file", file);
          const res = await fetch("/api/dev/db/procedures/import", {
            method: "POST",
            body: form
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || "Lỗi khi nạp tệp");
          const s = data.stats || {};
          if (statusBox) {
            statusBox.innerHTML = `<p class="small success" style="color:var(--success, #22c55e);">✅ ${h(data.message)} (Thêm mới: ${s.inserted || 0}, Cập nhật: ${s.updated || 0}, Giữ nguyên: ${s.unchanged || 0})</p>`;
          }
          refreshProceduresStats();
          refreshProceduresBackups();
        } catch (err) {
          if (statusBox) statusBox.innerHTML = `<p class="small danger">❌ Lỗi: ${h(err.message)}</p>`;
        } finally {
          fileInput.value = "";
        }
      };
    }

    // Rollback procedures backup
    if ($("dev-rollback-procs-btn")) {
      $("dev-rollback-procs-btn").onclick = async () => {
        if (!confirm("Bạn có chắc chắn muốn khôi phục CSDL procedures.db từ bản sao lưu gần nhất?")) return;
        if (statusBox) statusBox.innerHTML = '<p class="muted small">Đang phục hồi bản sao lưu...</p>';
        try {
          const res = await API.post("/api/dev/db/procedures/rollback", {});
          if (statusBox) statusBox.innerHTML = `<p class="small success" style="color:var(--success, #22c55e);">✅ ${h(res.message)}</p>`;
          refreshProceduresStats();
          refreshProceduresBackups();
        } catch (err) {
          if (statusBox) statusBox.innerHTML = `<p class="small danger">❌ Lỗi: ${h(err.message)}</p>`;
        }
      };
    }

    // Tra thử Web search MCP
    if ($("dev-web-go")) {
      $("dev-web-go").onclick = async () => {
        const q = ($("dev-web-q").value || "").trim();
        const out = $("dev-web-out");
        out.textContent = "Đang tra thử qua MCP…";
        try {
          const res = await API.post("/api/dev/websearch", { query: q });
          out.textContent = JSON.stringify(res, null, 2);
        } catch (e) {
          out.textContent = "Lỗi gọi endpoint: " + e.message;
        }
      };
    }

    // Xuất hội thoại ra TXT
    if ($("dev-export-conv")) {
      $("dev-export-conv").onclick = () => {
        const id = window.Conversations ? Conversations.activeId : null;
        if (!id) { alert("Chưa chọn cuộc trò chuyện nào để xuất."); return; }
        location.href = `/api/dev/export/conversation/${id}`;
      };
    }
    if ($("dev-export-all")) {
      $("dev-export-all").onclick = () => {
        location.href = "/api/dev/export/all";
      };
    }

    if ($("dev-conv-user")) $("dev-conv-user").onchange = loadUserConvs;
    if ($("dev-conv-select")) $("dev-conv-select").onchange = loadConvMessages;
    if ($("dev-conv-export")) {
      $("dev-conv-export").onclick = () => {
        const cid = $("dev-conv-select").value;
        if (cid) location.href = `/api/dev/export/conversation/${cid}`;
      };
    }
    document.querySelectorAll(".dev-base-url").forEach((n) => { n.textContent = location.origin; });

    initTabs();
    wireReset();
    await Promise.all([refreshStatus(), refreshMetrics()]);
  }

  async function stats() {
    await refreshMetrics();
  }

  function afterTurn() {
    if (available && open) {
      refreshTrace();
      refreshMetrics();
    }
  }

  return { init, stats, afterTurn, refreshMetrics, refreshUnmatched };
})();

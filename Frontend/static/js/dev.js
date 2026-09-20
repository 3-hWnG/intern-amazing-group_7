/* Bảng Dev: soi vì sao trợ lý trả lời như vậy.

   Chỉ chạy khi server bật DEV_TOOLS_ENABLED (nếu tắt thì endpoint không tồn
   tại, ẩn nút không phải là bảo mật). Công tắc trong bảng chỉ bật/tắt việc GHI
   VẾT, không mở lại route. */
window.Dev = (function () {
  let on = false;               // server có đang ghi vết không
  let open = false;             // bảng có đang mở không
  let available = false;

  const $ = (id) => document.getElementById(id);

  function esc(v) { return String(v === undefined || v === null ? "" : v); }

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
      if ((e.missing_information || []).length) text += `  thiếu: ${e.missing_information.join("; ")}`;
      if ((e.search_queries || []).length) text += `  truy vấn: ${e.search_queries.join(" | ")}`;
    }
    if (e.kind === "search" || e.kind === "research") {
      text += `  ${e.transport || ""}  ${e.n_sources} nguồn`;
      if (e.query) text += `  «${e.query}»`;
      if (e.error) text += `  — ${e.error}`;
    }
    if (e.kind === "verify") {
      text += `  lần ${e.attempt}: ${e.verdict}`;
      if ((e.issues || []).length) text += `  — ${e.issues.join("; ")}`;
      if (e.explanation) text += `  (${e.explanation})`;
    }
    if (e.chars !== undefined) text += `  ${e.chars} ký tự`;
    if (e.missing) text += `  thiếu: ${e.missing.join("; ")}`;
    if (e.note) text += `  — ${e.note}`;
    return text;
  }

  function renderTrace(t) {
    const box = document.createElement("div");
    box.className = "dev-card";

    const head = document.createElement("div");
    head.className = "dev-card-head";
    head.textContent = `#${t.id} · ${t.total_ms} ms · ${esc(t.question).slice(0, 48)}`;
    box.appendChild(head);

    box.appendChild(row("Ý định", t.intent || "—"));
    if (t.standalone) box.appendChild(row("Câu hỏi đã làm rõ", t.standalone));
    box.appendChild(row("Kết quả", `${t.kind || "—"}${t.verdict ? " · " + t.verdict : ""}`));
    if ((t.queries || []).length) box.appendChild(row("Truy vấn MCP", t.queries.join("  |  ")));
    if ((t.sources || []).length) box.appendChild(row("Nguồn được trích", t.sources.join(", ")));
    if (t.timings) {
      box.appendChild(row("Thời gian (ms)",
        Object.entries(t.timings).map(([k, v]) => `${k} ${v}`).join(" · ")));
    }

    (t.events || []).forEach((e) => {
      const d = document.createElement("div");
      d.className = "dev-ev"
        + (e.verdict === "FAIL" || e.kind === "error" || e.error ? " bad" : "")
        + (e.verdict === "PASS" ? " good" : "");
      d.textContent = describe(e);
      box.appendChild(d);
      if (e.diagnostics) {
        const pre = document.createElement("pre");
        pre.className = "dev-pre";
        pre.textContent = e.diagnostics;
        box.appendChild(pre);
      }
    });
    return box;
  }

  async function refreshTrace() {
    const host = $("dev-traces");
    if (!host) return;
    host.innerHTML = "";
    try {
      const data = await API.get("/api/dev/trace?limit=8");
      on = data.enabled;
      syncToggle();
      if (!data.traces.length) {
        host.innerHTML = '<p class="muted small">Chưa có lượt nào. Gửi một câu hỏi rồi quay lại.</p>';
        return;
      }
      data.traces.forEach((t) => host.appendChild(renderTrace(t)));
    } catch (e) {
      const p = document.createElement("p");
      p.className = "small";
      p.style.color = "var(--danger)";
      p.textContent = e.message;
      host.appendChild(p);
    }
  }

  /* ---------------- chẩn đoán tìm kiếm qua MCP ---------------- */
  async function testWeb() {
    const out = $("dev-web-out");
    const q = ($("dev-web-q").value || "").trim();
    out.textContent = "Đang tra…";
    try {
      const r = await API.post("/api/dev/websearch", { query: q });
      const m = r.mcp || {};
      const lines = [
        `KẾT QUẢ : ${r.ok ? "CHẠY TỐT" : "HỎNG"}${r.error ? " — " + r.error : ""}`,
        `MCP     : ${m.transport} · kết nối=${m.connected} · công cụ=${(m.tools || []).join(", ")}`
          + (m.last_error ? ` · lỗi gần nhất: ${m.last_error}` : ""),
        `đường đi: ${r.transport || "—"} · nhà cung cấp: ${r.provider} · ${r.elapsed_ms} ms`,
        "",
        ...(r.diagnostics || []),
        "",
        ...(r.results || []).map((x, i) => `${i + 1}. [${x.trust}] ${x.title}\n   ${x.url}`),
      ];
      out.textContent = lines.join("\n");
      out.className = "dev-pre " + (r.ok ? "good" : "bad");
    } catch (e) {
      out.textContent = "Lỗi gọi API: " + e.message;
      out.className = "dev-pre bad";
    }
  }

  /* ---------------- cấu hình đang chạy ---------------- */
  async function refreshStatus() {
    const host = $("dev-config");
    if (!host) return;
    try {
      const s = await API.get("/api/dev/status");
      on = s.developer_mode;
      syncToggle();
      host.innerHTML = "";
      Object.entries(s.config).forEach(([k, v]) => host.appendChild(row(k, v)));
    } catch (_) { /* im lặng */ }
  }

  function syncToggle() {
    const b = $("dev-toggle");
    if (!b) return;
    b.setAttribute("aria-pressed", String(on));
    b.textContent = on ? "Ghi vết: BẬT" : "Ghi vết: TẮT";
  }

  /* ---------------- reset dữ liệu ---------------- */
  function wireReset() {
    const btn = $("dev-reset");
    if (!btn) return;
    btn.onclick = async () => {
      const scope = prompt(
        "Phạm vi xoá:\n" +
        "  1 = hội thoại của tôi\n" +
        "  2 = TẤT CẢ hội thoại (mọi người dùng)\n" +
        "  3 = TẤT CẢ, kể cả tài khoản\n\nNhập 1, 2 hoặc 3:", "1");
      if (!scope) return;
      const map = { 1: "my_conversations", 2: "all_conversations", 3: "everything" };
      if (!map[scope]) return alert("Lựa chọn không hợp lệ.");
      if (prompt('Gõ đúng chữ  XOA  để xác nhận:') !== "XOA") return alert("Đã huỷ.");
      try {
        const res = await API.post("/api/dev/reset", { scope: map[scope], confirm: "XOA" });
        alert("Đã xoá. " + (res.note || ""));
        location.reload();
      } catch (err) {
        alert("Lỗi: " + err.message);
      }
    };
  }

  /* ---------------- vòng đời ---------------- */
  function setOpen(v) {
    open = v;
    const panel = $("dev-panel"), back = $("dev-backdrop"), btn = $("dev-open");
    panel.classList.toggle("open", open);
    panel.setAttribute("aria-hidden", String(!open));
    if (back) back.classList.toggle("open", open);
    if (btn) btn.setAttribute("aria-pressed", String(open));
    if (open) { refreshStatus(); refreshTrace(); }
  }

  async function init(enabled) {
    available = !!enabled;
    const panel = $("dev-panel");
    const openBtn = $("dev-open");
    const back = $("dev-backdrop");
    if (!available) {
      if (openBtn) openBtn.hidden = true;
      if (panel) panel.remove();
      if (back) back.remove();
      return;
    }
    openBtn.hidden = false;

    openBtn.onclick = () => setOpen(!open);
    $("dev-close").onclick = () => setOpen(false);
    if (back) back.onclick = () => setOpen(false);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && open) setOpen(false);
    });

    $("dev-toggle").onclick = async () => {
      try {
        const r = await API.post("/api/dev/toggle", {});
        on = r.developer_mode;
        syncToggle();
      } catch (e) { alert(e.message); }
    };
    $("dev-refresh").onclick = refreshTrace;
    $("dev-clear").onclick = async () => {
      await API.del("/api/dev/trace");
      refreshTrace();
    };
    $("dev-web-go").onclick = testWeb;

    const expConv = $("dev-export-conv");
    if (expConv) {
      expConv.onclick = async () => {
        const convId = Conversations.activeId;
        if (!convId) { alert("Chưa chọn cuộc trò chuyện nào để xuất."); return; }
        try {
          const res = await fetch(`/api/dev/export/conversation/${convId}`);
          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            alert("Không thể xuất file: " + (err.detail || res.statusText));
            return;
          }
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `danh_gia_hoi_thoai_${convId}.txt`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
        } catch (e) {
          alert("Lỗi xuất file: " + e.message);
        }
      };
    }
    const expAll = $("dev-export-all");
    if (expAll) {
      expAll.onclick = async () => {
        try {
          const res = await fetch("/api/dev/export/all");
          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            alert("Không thể xuất file: " + (err.detail || res.statusText));
            return;
          }
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `tat_ca_hoi_thoai_danh_gia_${new Date().toISOString().slice(0, 10)}.txt`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
        } catch (e) {
          alert("Lỗi xuất file: " + e.message);
        }
      };
    }

    wireReset();
    await Promise.all([refreshStatus(), stats()]);
  }

  async function stats() {
    try {
      const s = await API.get("/api/dev/stats");
      const r = s.ratings || {};
      const el = $("dev-stats");
      if (el) el.textContent =
        `${s.users} tài khoản · ${s.conversations} hội thoại · ${s.messages} tin nhắn · ` +
        `phản hồi: 👍 ${r.phu_hop || 0} / 👎 ${r.khong_phu_hop || 0} / chưa đánh giá ${r.unrated || 0}`;
    } catch (_) { /* im lặng */ }
  }

  /* app.js gọi sau mỗi lượt chat để bảng tự cập nhật */
  function afterTurn() { if (available && open) refreshTrace(); }

  return { init, stats, afterTurn };
})();

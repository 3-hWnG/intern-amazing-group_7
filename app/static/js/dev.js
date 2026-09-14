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
  function renderTrace(t) {
    const box = document.createElement("div");
    box.className = "dev-card";

    const head = document.createElement("div");
    head.className = "dev-card-head";
    head.textContent = `#${t.id} · ${t.total_ms} ms · ${esc(t.question).slice(0, 48)}`;
    box.appendChild(head);

    box.appendChild(row("Nguồn bằng chứng", t.kind || "—"));
    box.appendChild(row("Nhãn / độ tin cậy", `${t.tier || "—"} · ${t.confidence ?? "—"}`));
    if (t.facet) box.appendChild(row("Trường được hỏi", t.facet));
    if (t.current) box.appendChild(row("Thủ tục trong ngữ cảnh", `${t.current[1]} (id=${t.current[0]})`));
    box.appendChild(row("Chuỗi công cụ", (t.tools || []).join("  →  ") || "—"));
    if (t.factcheck) box.appendChild(row("Kiểm chứng", t.factcheck));
    if (t.sources && t.sources.length) box.appendChild(row("Nguồn", t.sources.join(", ")));
    box.appendChild(row("Chế độ trả lời", t.mode === "text" ? "sinh xong mới phát" : "stream"));

    (t.events || []).forEach((e) => {
      let text = `+${e.at_ms}ms  ${e.kind}`;
      if (e.tool) text += `  ${e.tool}(${esc(e.query).slice(0, 30)})`;
      if (e.kind === "tool") text += `  ${e.ok ? "ok" : "HỎNG"} conf=${e.confidence}`;
      if (e.title) text += `  «${e.title}»`;
      if (e.note) text += `  — ${e.note}`;
      if (e.kind === "sticky") text += `  ← quay lại «${e.title}» (mới chỉ ${e.fresh_confidence})`;
      if (e.problem) text += `  — ${e.problem}`;
      const d = document.createElement("div");
      d.className = "dev-ev" + (e.ok === false || e.kind === "web_failed" ? " bad" : "")
        + (e.kind === "sticky" ? " good" : "");
      d.textContent = text;
      box.appendChild(d);
    });

    if (t.diagnostics) {
      const pre = document.createElement("pre");
      pre.className = "dev-pre";
      pre.textContent = t.diagnostics;
      box.appendChild(pre);
    }
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
      host.innerHTML = `<p class="small" style="color:var(--danger)">${esc(e.message)}</p>`;
    }
  }

  /* ---------------- chẩn đoán tra web ---------------- */
  async function testWeb() {
    const out = $("dev-web-out");
    const q = ($("dev-web-q").value || "").trim();
    out.textContent = "Đang tra…";
    try {
      const r = await API.post("/api/dev/websearch", { query: q });
      const lines = [
        `CHẨN ĐOÁN: ${r.diagnosis}`,
        r.fix ? `CÁCH SỬA : ${r.fix}` : "",
        "",
        `thư viện : ${r.library || r.library_error}`,
        `bật      : ${r.enabled}   strict: ${r.strict}   timeout: ${r.timeout}s`,
        `backend  : ${(r.backends || []).join(", ")}`,
        "",
        r.report || "",
      ];
      out.textContent = lines.filter(Boolean).join("\n");
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

    wireReset();
    await Promise.all([refreshStatus(), stats()]);
  }

  async function stats() {
    try {
      const s = await API.get("/api/dev/stats");
      const el = $("dev-stats");
      if (el) el.textContent =
        `${s.users} tài khoản · ${s.conversations} hội thoại · ${s.messages} tin nhắn`;
    } catch (_) { /* im lặng */ }
  }

  /* app.js gọi sau mỗi lượt chat để bảng tự cập nhật */
  function afterTurn() { if (available && open) refreshTrace(); }

  return { init, stats, afterTurn };
})();

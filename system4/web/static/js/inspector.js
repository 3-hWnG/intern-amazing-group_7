/* System 4 — bộ công cụ dev (dùng chung cho trang chat và trang Quản trị).
   S4Inspect.friendly(mid, dev)  : "🔍 Soi" (dev: tìm kiếm / lời dặn / AI nghĩ gì / kiểm soát / JSON) hoặc "Vì sao?" (người dùng)
   S4Inspect.strict(nodeId)      : kế hoạch + dấu vết System 3 của một câu trả lời Strict (dev)
   S4Inspect.reading(datasetId)  : "Cách đọc tệp" — dòng tiêu đề đã chọn, cột tiêu đề, các trường, vài bản ghi đầu
   S4Inspect.candidates(box, info): bảng xếp hạng tìm kiếm (phòng thử tìm kiếm của trang Quản trị dùng lại) */
(function () {
  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  };
  async function get(url) {
    const res = await fetch(url);
    const d = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof d.detail === "string" ? d.detail : res.statusText);
    return d;
  }
  const pre = (obj) => el("pre", "insp-pre", typeof obj === "string" ? obj : JSON.stringify(obj, null, 2));
  const kv = (rows) => {
    const t = el("table", "insp-kv");
    rows.forEach(([k, v]) => {
      if (v === undefined) return;
      const tr = el("tr"); tr.append(el("th", "", k));
      const td = el("td"); if (v instanceof Node) td.appendChild(v); else td.textContent = v === null ? "—" : (typeof v === "object" ? JSON.stringify(v) : String(v));
      tr.appendChild(td); t.appendChild(tr);
    });
    return t;
  };
  const yes = (b) => (b ? "có" : "không");
  const relev = (s) => (s === null || s === undefined ? "" : s >= 3 ? "rất liên quan" : s >= 0 ? "liên quan" : s >= -3 ? "hơi liên quan" : "ít liên quan");

  /* ---------- khung cửa sổ có tab ---------- */
  function modal(title, tabs) {
    const m = el("div", "s4-modal insp");
    const d = el("div", "s4-dialog wide"); d.setAttribute("role", "dialog"); d.setAttribute("aria-modal", "true");
    const h = el("header"); h.appendChild(el("h2", "", title));
    const x = el("button", "icon", "✕"); x.type = "button"; x.setAttribute("aria-label", "Đóng"); x.onclick = () => m.remove();
    h.appendChild(x); d.appendChild(h);
    const nav = el("div", "insp-tabs"); const body = el("div", "body");
    const names = Object.keys(tabs);
    names.forEach((n, i) => {
      const b = el("button", "tab" + (i === 0 ? " active" : ""), n); b.type = "button";
      b.onclick = () => { nav.querySelectorAll(".tab").forEach((y) => y.classList.toggle("active", y === b)); body.innerHTML = ""; body.appendChild(tabs[n]()); };
      nav.appendChild(b);
    });
    if (names.length > 1) d.appendChild(nav);
    body.appendChild(tabs[names[0]]());
    d.appendChild(body); m.appendChild(d);
    m.addEventListener("click", (e) => { if (e.target === m) m.remove(); });
    document.addEventListener("keydown", function esc(e) { if (e.key === "Escape") { m.remove(); document.removeEventListener("keydown", esc); } });
    document.body.appendChild(m);
  }

  /* ---------- bảng xếp hạng tìm kiếm ---------- */
  function candidates(info) {
    const w = el("div");
    if (!info) { w.appendChild(el("p", "muted", "Câu này không ở chế độ Chuyên gia (không tìm trong dữ liệu).")); return w; }
    const s = info.settings || {};
    w.appendChild(kv([
      ["Câu dùng để tìm", info.query], ["Truy vấn từ khoá (FTS5)", info.fts_query || "(trống)"],
      ["Số bộ dữ liệu", info.datasets], ["Tìm từ khoá / theo nghĩa", `${info.keyword ?? 0} / ${info.vector ?? 0} kết quả`],
      ["Xếp hạng lại (reranker)", info.reranked ? "có" : "không"], ["Ngưỡng reranker", s.RERANK_MIN_SCORE],
      ["Ứng viên / gửi AI tối đa", `${s.RETRIEVAL_CANDIDATES} / ${s.RETRIEVAL_TOP_K}`], ["Thời gian tìm", info.search_ms != null ? info.search_ms + " ms" : undefined],
    ]));
    const list = info.candidates || [];
    if (!list.length) { w.appendChild(el("p", "muted", "Không có ứng viên nào.")); return w; }
    w.appendChild(el("p", "muted small", "Bấm một dòng để xem đúng đoạn chữ AI nhận. Xanh = gửi cho AI; gạch = dưới ngưỡng reranker."));
    const t = el("table", "insp-grid");
    const hr = el("tr"); ["#", "Tiêu đề", "Bộ dữ liệu", "Từ khoá", "Nghĩa (giống)", "RRF", "Reranker", "Gửi AI"].forEach((c) => hr.appendChild(el("th", "", c))); t.appendChild(hr);
    list.forEach((c, i) => {
      const tr = el("tr", c.sent ? "sent" : c.passed ? "" : "failed");
      [i + 1, c.title, c.dataset, c.keyword_rank ?? "—", c.vector_rank ? `${c.vector_rank} (${c.vector_score})` : "—", c.rrf,
        c.rerank ?? "—", c.sent ? "✓" : c.passed ? "" : "dưới ngưỡng"].forEach((v) => tr.appendChild(el("td", "", v)));
      tr.onclick = () => {
        if (tr.nextSibling && tr.nextSibling.classList.contains("insp-text")) { tr.nextSibling.remove(); return; }
        const x = el("tr", "insp-text"); const td = el("td"); td.colSpan = 8; td.appendChild(el("div", "", c.source)); td.appendChild(pre(c.text)); x.appendChild(td);
        tr.after(x);
      };
      t.appendChild(tr);
    });
    w.appendChild(t);
    return w;
  }

  /* ---------- "Vì sao?" cho người dùng ---------- */
  function why(w) {
    const box = el("div");
    box.appendChild(el("p", "", (w.mode === "think" ? "Chế độ Suy nghĩ kỹ" : "Chế độ Nhanh") + (w.interrupted ? " (đã bấm Trả lời nhanh)" : "") +
      (w.specialist ? ` · Chuyên gia: đã tìm trong ${w.datasets_searched} bộ dữ liệu đang bật` : " · AI chung (không có bộ dữ liệu đang bật)")));
    const src = w.sources.length ? w.sources : w.consulted;
    if (w.specialist) {
      box.appendChild(el("p", "", w.sources.length ? "Câu trả lời dựa trên:" : src.length ? "AI không ghi nguồn cụ thể; các đoạn đã tra cứu:" : "Không tìm thấy đoạn dữ liệu nào liên quan."));
      const ul = el("ul", "insp-why");
      src.forEach((s) => { const li = el("li"); li.append(el("b", "", (s.n ? `[${s.n}] ` : "") + s.title), el("span", "muted", ` · ${s.dataset}` + (s.score != null ? ` · độ liên quan ${s.score} (${relev(s.score)})` : ""))); ul.appendChild(li); });
      box.appendChild(ul);
    }
    if (w.guard) box.appendChild(el("p", "muted", `Quy tắc đã áp dụng: ${w.guard}.`));
    return box;
  }

  async function friendly(mid, dev) {
    let d;
    try { d = await get("/s4/trace/" + mid); } catch (e) { alert("Không mở được: " + e.message); return; }
    if (!dev || !d.trace) {
      if (dev && !d.trace) return modal("🔍 Soi câu trả lời", { "Vì sao?": () => { const b = why(d.why); b.appendChild(el("p", "muted", "Chi tiết đầy đủ không còn (chỉ giữ " + d.kept + " câu gần nhất) hoặc câu này có trước khi có bộ công cụ.")); return b; } });
      return modal("Vì sao có câu trả lời này?", { "": () => why(d.why) });
    }
    const t = d.trace, ch = t.checks || {}, out = t.output || {};
    modal("🔍 Soi câu trả lời", {
      "Tìm kiếm": () => candidates(t.retrieval),
      "Lời dặn": () => {
        const w = el("div");
        if (t.blocked_by) { w.appendChild(el("p", "", `Bị chặn bởi guardrail "${t.blocked_by}" — không gọi AI.`)); return w; }
        (t.prompts || []).forEach((p) => {
          w.appendChild(el("h3", "", p.why));
          p.messages.forEach((m) => { w.appendChild(el("div", "insp-role", `${m.role} · ~${Math.round(m.content.length / 3)} token`)); w.appendChild(pre(m.content)); });
        });
        return w;
      },
      "AI nghĩ gì": () => {
        const w = el("div");
        if (out.plan) { w.appendChild(el("h3", "", "Kế hoạch ẩn (chế độ Nhanh)")); w.appendChild(pre(out.plan)); }
        if (out.thinking) { w.appendChild(el("h3", "", "Suy nghĩ ẩn (chế độ Suy nghĩ kỹ)")); w.appendChild(pre(out.thinking)); }
        if (out.raw_json) { w.appendChild(el("h3", "", "JSON thô model trả về")); w.appendChild(pre(out.raw_json)); }
        w.appendChild(el("h3", "", "Câu trả lời cuối (sau lọc / guardrail)")); w.appendChild(pre(out.final_text || d.content || ""));
        if (!out.plan && !out.thinking && !out.raw_json) w.prepend(el("p", "muted", "Không có phần suy nghĩ / kế hoạch cho câu này."));
        return w;
      },
      "Kiểm soát": () => {
        const w = el("div");
        const a = t.after || {}, mem = a.memory || {};
        w.appendChild(kv([
          ["Chế độ", (t.mode === "think" ? "Suy nghĩ kỹ" : "Nhanh") + (t.final_mode !== t.mode ? ` → ${t.final_mode}` : "")],
          ["Chuyên gia", yes(t.specialist)], ["Trạng thái", t.status + (t.error ? ` · ${t.error}` : "")],
          ["Không phải tiếng Việt (xin lỗi trước)", yes(ch.foreign)], ["Người dùng bực bội (thêm câu đồng cảm)", yes(ch.upset)],
          ["Số lần hỏi lại liên tiếp trước đó", ch.clarify_streak], ["Hết lượt hỏi lại", yes(ch.clarify_exhausted)],
          ["Lời dặn từ guardrail", (ch.instructions || []).join(" | ") || "—"],
          ["Guardrail thay câu trả lời", ch.guard_replaced || "—"], ["Chốt 'chỉ trả lời từ dữ liệu'", yes(ch.kb_guard)],
          ["Bộ lọc chữ lạ / emoji", ch.filtered ? `${ch.filtered.letters} chữ lạ, ${ch.filtered.other} ký hiệu` : "không phải lọc"],
          ["Viết lại do lọt chữ lạ", yes(ch.leak_retry)], ["Bấm Trả lời nhanh", yes(ch.interrupted)],
          ["Điều nhớ đưa vào lời dặn", ch.memories_in_prompt], ["Có tóm tắt hội thoại", yes(ch.summary_in_prompt)], ["Số tin lịch sử gửi kèm", ch.history_messages],
          ["Bước ghi nhớ", a.memory ? (mem.checked ? `đã chạy · thêm ${(mem.added || []).length}, xoá ${(mem.removed || []).length}` : `bỏ qua (${mem.why || ""})`) : "chưa xong / không có"],
          ["AI đề xuất ghi nhớ", mem.proposed ? JSON.stringify(mem.proposed) : undefined], ["Tóm tắt hội thoại sau lượt này", a.summarized !== undefined ? yes(a.summarized) : undefined],
          ["Thời gian tìm", t.timing && t.timing.search_ms != null ? t.timing.search_ms + " ms" : "—"],
          ["Thời gian AI", t.timing && t.timing.llm_ms != null ? t.timing.llm_ms + " ms" : "—"], ["Tổng", t.timing && t.timing.total_ms != null ? t.timing.total_ms + " ms" : "—"],
        ]));
        return w;
      },
      "Người dùng thấy": () => why(d.why),
      "JSON": () => pre(d),
    });
  }

  async function strict(nodeId) {
    let d;
    try { d = await get("/s4/strict/trace/" + nodeId); } catch (e) { alert("Không mở được: " + e.message); return; }
    if (!d.plan && !d.s3_trace) return modal("Nguồn câu trả lời", { "": () => pre(d.why) });
    modal("🔍 Soi câu trả lời Strict (System 3)", {
      "Kế hoạch": () => { const w = el("div"); w.appendChild(el("p", "muted small", "Kế hoạch do Planner của System 3 lập (luật / hybrid) cho câu hỏi này.")); w.appendChild(pre(d.plan || "(không có)")); return w; },
      "Dấu vết System 3": () => { const w = el("div"); w.appendChild(el("p", "muted small", "System 3 tự lưu cho mỗi câu trả lời: từng bước Planner → Policy → Answerer, thời gian xử lý.")); w.appendChild(pre(d.s3_trace || "(System 3 không lưu dấu vết cho câu này)")); return w; },
      "Phiên bản": () => kv([["Nút", d.node.id], ["Hội thoại System 3 chứa câu này", d.node.s3_cid + (d.branch ? " (nhánh ẩn, tạo khi sửa / tạo lại)" : " (gốc)")], ["Tin System 3", d.node.s3_mid], ["Trả lời thẻ hỏi lại", yes(d.node.replied)]]),
      "Nguồn": () => pre(d.why),
    });
  }

  async function reading(dsId) {
    let d;
    try { d = await get("/s4/datasets/" + dsId + "/reading"); } catch (e) { alert("Không mở được: " + e.message); return; }
    const ds = d.dataset, parts = (ds.mapping && ds.mapping.parts) || [];
    modal("Cách đọc tệp: " + ds.filename, {
      "Cách đọc": () => {
        const w = el("div");
        w.appendChild(el("p", "", ds.message));
        if (ds.mapping && ds.mapping.reader) w.appendChild(el("p", "muted small", "Phiên bản bộ đọc: " + ds.mapping.reader));
        parts.forEach((p) => {
          w.appendChild(el("h3", "", (p.sheet || p.title || "Phần") + " · " + ({ table: "bảng khớp cấu trúc", rows: "bảng KHÔNG khớp (lưu dạng dòng chữ)", text: "văn bản" }[p.kind] || p.kind)));
          w.appendChild(kv([
            ["Dòng tiêu đề cột", p.header_row != null ? "dòng " + p.header_row + " của tệp" : p.kind === "text" ? undefined
              : !("header_row" in p) ? "chưa ghi lại (tệp xử lý trước khi có thông tin này — bấm \"Xử lý lại\" để xem)" : "không có (đặt tên Cột 1, Cột 2…)"],
            ["Bỏ qua phía trên", p.skipped_above && p.skipped_above.length ? p.skipped_above.join(" ⏎ ") : undefined],
            ["Cột tiêu đề bản ghi", p.title_column], ["Các trường", p.fields ? p.fields.join(", ") : undefined], ["Số đoạn", p.chunks],
            ["Cách nhận ra", [p.two_row_header ? "tiêu đề cột hai tầng (đã ghép)" : "", p.sideways ? "bảng nằm ngang (đã xoay lại)" : "",
              p.header_chosen ? "dòng tiêu đề do bạn chọn" : ""].filter(Boolean).join(" · ") || undefined],
          ]));
          if (p.kind === "table" || p.kind === "rows") {   /* chọn lại dòng tiêu đề cột rồi xử lý lại tệp */
            const row = el("div", "src-row"), inp = el("input"), go = el("button", "", "Đọc lại");
            inp.type = "number"; inp.min = "0"; inp.style.width = "5em"; inp.value = p.header_row || "";
            inp.title = "Số dòng trong tệp chứa tên cột; 0 = để hệ thống tự đoán";
            go.type = "button";
            go.onclick = async () => {
              const r = await fetch("/s4/datasets/" + dsId + "/header", { method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ part: p.sheet, row: +inp.value || 0 }) });
              if (r.ok) { go.textContent = "Đang xử lý lại…"; go.disabled = true; } else alert("Không lưu được: " + (await r.text()));
            };
            row.append(el("span", "", "Dòng tiêu đề cột:"), inp, go);
            w.appendChild(row);
          }
        });
        return w;
      },
      "Bản ghi đầu (AI thấy thế này)": () => {
        const w = el("div");
        w.appendChild(el("p", "muted small", `${d.total} bản ghi; dưới đây là ${d.first.length} bản ghi đầu, đúng đoạn chữ dùng để tìm và gửi cho AI.`));
        d.first.forEach((r) => { w.appendChild(el("h3", "", r.title)); w.appendChild(pre(r.text)); w.appendChild(el("div", "muted small", r.source)); });
        return w;
      },
    });
  }

  window.S4Inspect = { friendly, strict, reading, candidates };
})();

/* Khung chat: trạng thái xử lý, câu trả lời có trích dẫn [S#], nhãn kiểm chứng,
   nguồn, Evidence Pack (chứng minh RAG) và phản hồi Phù hợp / Không phù hợp. */
window.Chat = (function () {
  const TRUST = {
    official: "chính thống", legal: "CSDL pháp luật", news: "báo chí",
    other: "nguồn khác", attachment: "tệp đính kèm",
  };
  const BADGE = {
    PASS: ["✓ Đã kiểm chứng với nguồn", "badge-pass"],
    FAIL: ["⚠ Chưa kiểm chứng đầy đủ", "badge-fail"],
    answer: ["Chưa qua kiểm chứng", "badge-muted"],
    clarify: ["Cần thêm thông tin", "badge-clarify"],
    no_evidence: ["Không tìm được nguồn", "badge-fail"],
    not_in_sources: ["Nguồn chưa có thông tin này", "badge-muted"],
    error: ["Lỗi hệ thống", "badge-fail"],
  };

  const box = () => document.getElementById("messages");

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  }

  const isUrl = (u) => /^https?:\/\//i.test(u || "");

  function scroll() {
    const b = box();
    b.scrollTop = b.scrollHeight;
  }

  /* Tin nhắn cũ lưu nguồn dạng chuỗi; tin nhắn mới dạng object có id S#. */
  function normSources(sources) {
    return (sources || []).map((s, i) =>
      typeof s === "string" ? { id: `S${i + 1}`, title: s, url: isUrl(s) ? s : "" } : s);
  }

  /* Escape TRƯỚC rồi mới chèn thẻ: nội dung đến từ mô hình + web, không tin được. */
  function rich(text, sources) {
    const byId = {};
    sources.forEach((s) => { if (s.id) byId[String(s.id).toUpperCase()] = s; });
    let html = esc(text);
    html = html.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/^#{1,4}\s+(.+)$/gm, "<strong>$1</strong>");
    html = html.replace(/\[((?:S\d+\s*[,;]?\s*)+)\]/gi, (_, inner) =>
      inner.split(/[\s,;]+/).filter(Boolean).map((id) => {
        const s = byId[id.toUpperCase()];
        const n = id.replace(/\D/g, "");
        if (s && isUrl(s.url)) {
          return `<a class="cite" href="${esc(s.url)}" target="_blank" rel="noopener noreferrer" title="${esc(s.title || s.url)}">${n}</a>`;
        }
        return `<span class="cite" title="${esc(s ? s.title : "")}">${n}</span>`;
      }).join(""));
    return html;
  }

  function badge(meta) {
    const key = meta.kind === "answer" ? (meta.verdict || "answer") : meta.kind;
    const found = BADGE[key];
    return found ? el("span", `badge ${found[1]}`, found[0]) : null;
  }

  function sourceList(sources) {
    if (!sources.length) return null;
    const wrap = el("div", "sources");
    wrap.appendChild(el("span", "sources-label", "Nguồn — bấm để tự kiểm tra"));
    sources.forEach((s, i) => {
      const line = el("div", "source");
      const n = String(s.id || `S${i + 1}`).replace(/\D/g, "");
      line.appendChild(el("span", "source-n", n));
      if (isUrl(s.url)) {
        const a = el("a", "", s.title || s.url);
        a.href = s.url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.title = s.url;
        line.appendChild(a);
      } else {
        line.appendChild(el("span", "plain", s.title || ""));
      }
      const meta = [s.domain, TRUST[s.trust], s.published_at ? String(s.published_at).slice(0, 10) : ""]
        .filter(Boolean).join(" · ");
      if (meta) line.appendChild(el("span", "source-meta", meta));
      wrap.appendChild(line);
    });
    return wrap;
  }

  /* ---------------- Evidence Pack: nạp lười khi mở ---------------- */
  function evidencePanel(messageId) {
    const d = el("details", "evidence");
    d.appendChild(el("summary", "", "Evidence Pack — dữ liệu RAG đã dùng để trả lời"));
    const body = el("div", "ev-body", "Đang tải…");
    d.appendChild(body);
    let loaded = false;
    d.addEventListener("toggle", async () => {
      if (!d.open || loaded) return;
      loaded = true;
      try {
        const data = await API.get(`/api/messages/${messageId}/evidence`);
        renderEvidence(body, data.evidence || {}, data.model || {});
      } catch (e) {
        body.textContent = "Không tải được: " + e.message;
        loaded = false;
      }
    });
    return d;
  }

  function renderEvidence(body, pack, model) {
    body.innerHTML = "";
    const row = (k, v) => {
      const r = el("div", "ev-row");
      r.append(el("span", "ev-k", k), el("span", "ev-v", v));
      body.appendChild(r);
    };
    row("Câu hỏi tra cứu", pack.question || "—");
    row("Truy vấn MCP", (pack.queries || []).join("  |  ") || "—");
    row("Truy xuất", `${String(pack.retrieved_at || "").replace("T", " ").slice(0, 16)} · ${pack.transport || ""} · ${pack.provider || ""}`);
    const tuned = model.finetuned_at ? `fine-tune lúc ${String(model.finetuned_at).slice(0, 16).replace("T", " ")}` : "chưa fine-tune";
    row("Mô hình", `${model.model || ""} — kiến thức tới ~${model.knowledge_cutoff || "?"} (${tuned})`);
    const newest = (pack.sources || []).map((s) => String(s.published_at || "").slice(0, 10)).filter(Boolean).sort().pop();
    if (newest) {
      const newer = newest.slice(0, 7) > String(model.knowledge_cutoff || "");
      row("So sánh thời gian", `nguồn mới nhất ${newest} ${newer ? "MỚI HƠN" : "không mới hơn"} kiến thức mô hình → ${newer ? "câu trả lời bám nguồn" : "vẫn bám nguồn"}`);
    }
    if (pack.error) row("Lỗi", pack.error);

    (pack.sources || []).forEach((s) => {
      const card = el("div", "ev-card");
      const head = el("div", "ev-card-head");
      head.appendChild(el("span", "source-n", String(s.id || "").replace(/\D/g, "")));
      if (isUrl(s.url)) {
        const a = el("a", "", s.title || s.url);
        a.href = s.url; a.target = "_blank"; a.rel = "noopener noreferrer";
        head.appendChild(a);
      } else {
        head.appendChild(el("span", "", s.title || ""));
      }
      card.appendChild(head);
      card.appendChild(el("div", "source-meta", [
        s.domain, TRUST[s.trust],
        s.published_at ? "đăng " + String(s.published_at).slice(0, 10) : "",
        s.fetched ? "đọc toàn văn" : "chỉ có đoạn trích", s.score !== undefined ? "điểm " + s.score : "",
      ].filter(Boolean).join(" · ")));
      card.appendChild(el("pre", "ev-content", s.content || s.snippet || ""));
      body.appendChild(card);
    });

    if ((pack.diagnostics || []).length) {
      const diag = el("details", "ev-diag");
      diag.appendChild(el("summary", "", "Nhật ký tìm kiếm"));
      diag.appendChild(el("pre", "ev-content", pack.diagnostics.join("\n")));
      body.appendChild(diag);
    }
  }

  function feedback(messageId) {
    const fb = el("div", "feedback");
    [["phu_hop", "👍 Phù hợp"], ["khong_phu_hop", "👎 Không phù hợp"]].forEach(([verdict, label]) => {
      const b = el("button", "", label);
      b.type = "button";
      b.onclick = async () => {
        try {
          await API.post("/api/feedback", { message_id: messageId, verdict });
          fb.querySelectorAll("button").forEach((x) => (x.disabled = true));
          b.classList.add("chosen");
        } catch (e) { alert(e.message); }
      };
      fb.appendChild(b);
    });
    return fb;
  }

  function choiceBox(choices, convId) {
    if (!choices || !choices.length) return null;
    const wrap = el("div", "choice-table-wrap");
    const head = el("div", "choice-table-head");
    head.innerHTML = `<strong>💡 Gợi ý tìm kiếm DuckDuckGo</strong><span>(Bấm 1 câu để AI tra cứu ngay, hoặc tự nhập bên dưới)</span>`;
    wrap.appendChild(head);

    const list = el("div", "choice-list");
    choices.slice(0, 3).forEach((choice, idx) => {
      const item = el("button", "choice-item");
      item.type = "button";
      const badge = el("span", "choice-badge", String(idx + 1));
      const text = el("span", "choice-text", choice);
      item.append(badge, text);
      item.onclick = (e) => {
        e.preventDefault();
        if (isSending) return;
        wrap.querySelectorAll(".choice-item").forEach((c) => c.classList.remove("selected"));
        item.classList.add("selected");
        send(convId, choice, { directSearch: true });
      };
      list.appendChild(item);
    });
    wrap.appendChild(list);

    const customRow = el("div", "choice-custom-row");
    const input = el("input", "choice-custom-input");
    input.type = "text";
    input.placeholder = "Hoặc tự nhập nội dung tra cứu theo ý bạn…";
    const btn = el("button", "choice-custom-btn", "Gửi tra cứu");
    btn.type = "button";

    const submitCustom = () => {
      const val = input.value.trim();
      if (!val || isSending) return;
      input.value = "";
      send(convId, val, { directSearch: true });
    };

    btn.onclick = (e) => {
      e.preventDefault();
      submitCustom();
    };
    input.onkeydown = (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        submitCustom();
      }
    };
    customRow.append(input, btn);
    wrap.appendChild(customRow);

    return wrap;
  }

  function fillAssistant(wrap, body, text, meta, convId) {
    const sources = normSources(meta.sources);
    body.innerHTML = rich(text, sources);
    const tags = el("div", "msg-tags");
    const b = badge(meta);
    if (b) tags.appendChild(b);
    if (tags.childNodes.length) wrap.appendChild(tags);

    if (meta.choices && meta.choices.length) {
      const cBox = choiceBox(meta.choices, convId || activeLoadId);
      if (cBox) wrap.appendChild(cBox);
    }

    const src = sourceList(sources);
    if (src) wrap.appendChild(src);
    if (meta.id && meta.has_evidence) wrap.appendChild(evidencePanel(meta.id));
    if (meta.id && meta.kind !== "error") wrap.appendChild(feedback(meta.id));
  }

  function render(role, text, meta, convId) {
    const wrap = el("div", `msg ${role}`);
    const body = el("div", "bubble");
    wrap.appendChild(body);
    if (role === "assistant") fillAssistant(wrap, body, text, meta || {}, convId);
    else body.textContent = text || "";
    box().appendChild(wrap);
    scroll();
    return wrap;
  }

  function clear() { box().innerHTML = ""; }

  function empty() {
    box().innerHTML =
      '<div class="empty"><h2>Bạn cần làm thủ tục gì?</h2>' +
      '<p>Ví dụ: <em>“Con tôi mới sinh, làm giấy khai sinh cần gì?”</em></p></div>';
  }

  let activeLoadId = null;
  let isSending = false;

  async function load(convId) {
    activeLoadId = convId;
    if (isSending) return;
    if (!convId) {
      clear();
      empty();
      return;
    }
    try {
      const data = await API.get(`/api/conversations/${convId}`);
      if (activeLoadId !== convId || isSending) return;
      clear();
      if (!data.messages || !data.messages.length) {
        empty();
        return;
      }
      data.messages.forEach((m) => render(m.role, m.content, {
        id: m.id,
        kind: m.kind,
        verdict: m.verdict,
        sources: m.sources,
        has_evidence: m.has_evidence,
        choices: m.choices || [],
      }, convId));
    } catch (err) {
      console.error("Lỗi tải cuộc trò chuyện:", err);
    }
  }

  async function send(convId, text, opts = {}) {
    activeLoadId = convId;
    isSending = true;
    let done = null;
    const directSearch = Boolean(opts && opts.directSearch);
    try {
      if (box().querySelector(".empty")) clear();
      render("user", text);

      const wrap = el("div", "msg assistant");
      const status = el("div", "status");
      const statusText = el("span", "status-text", directSearch ? "Đang gửi DuckDuckGo qua MCP…" : "Đang gửi…");
      status.append(el("span", "spinner"), statusText);
      const body = el("div", "bubble");
      body.hidden = true;
      wrap.append(status, body);
      box().appendChild(wrap);
      scroll();

      let acc = "";
      await API.stream(`/api/conversations/${convId}/chat`, { text, direct_search: directSearch }, (evt) => {
        if (evt.type === "status" || evt.type === "queue") {
          statusText.textContent = evt.text;
        } else if (evt.type === "delta") {
          body.hidden = false;
          acc += evt.text;
          body.textContent = acc;
          scroll();
        } else if (evt.type === "done") {
          done = evt;
        } else if (evt.type === "error") {
          body.hidden = false;
          acc += (acc ? "\n\n" : "") + "[Lỗi] " + evt.text;
          body.textContent = acc;
        }
      });

      status.remove();
      body.hidden = false;
      if (done) {
        fillAssistant(wrap, body, acc, {
          id: done.message_id,
          kind: done.kind,
          verdict: done.verdict,
          sources: done.sources,
          has_evidence: done.has_evidence,
          choices: done.choices || [],
        }, convId);
      } else if (!acc) {
        body.textContent = "[Lỗi] Không nhận được phản hồi từ máy chủ.";
      }
      scroll();
    } finally {
      isSending = false;
    }
    return done;
  }

  return { load, send, clear, empty, get isSending() { return isSending; } };
})();

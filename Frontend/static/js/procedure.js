/* BẢNG THỦ TỤC của Hệ thống 2 — vẽ thẳng từ dữ liệu CSDL, KHÔNG qua mô hình.

   Proposal gọi phần này là "UI Formatting Engine (Zero LLM Hallucination Risk)".
   Vì vậy tệp này KHÔNG được "làm đẹp" dữ liệu: không suy ra, không gộp, không
   đoán hộ. Máy chủ gửi ô nào rỗng kèm lý do thì hiện đúng lý do đó.

   Mỗi ô đến dưới dạng {value, status, note}:
       present  -> vẽ giá trị
       absent   -> vẽ `note` màu xám ("cổng không công bố…")
       unknown  -> vẽ `note` ("chưa cào được")
   KHÔNG BAO GIỜ bỏ trống một mục: ô trống bị người dân đọc thành "miễn phí"
   hoặc "không cần giấy tờ gì", sai nguy hiểm hơn thiếu.

   Các dạng `table` mà máy chủ gửi xuống:
       {kind: "mcq"}            -> câu hỏi trắc nghiệm, kèm ô "nhớ lựa chọn"
       {kind: "new_procedure"}  -> đang xem bảng mà hỏi thủ tục khác: mời ô chat mới
       {kind: "exact_hint"}     -> chip "🎯 Tìm chính xác" dưới câu trả lời trò chuyện
       {kind: "exact_used"}     -> 🎯 lần hai: [ô chat mới và tra] [huỷ]
       (không có kind)          -> BẢNG THỦ TỤC đầy đủ
*/
window.Procedure = (function () {
  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  const isUrl = (u) => /^https?:\/\//i.test(u || "");

  /* Một ô có thể rỗng: trả về phần tử hiển thị giá trị HOẶC lý do vì sao trống. */
  function cellBody(cell, renderValue) {
    if (cell && cell.status === "present") return renderValue(cell.value);
    const note = el("p", "proc-absent", (cell && cell.note) || "Chưa có thông tin.");
    return note;
  }

  /* `collapsed`: mục dài (giải thích, các bước, tài liệu, nguồn) thu gọn sẵn —
     bảng mở hết thì dài vài màn hình. Chỉ ẩn khỏi mắt, KHÔNG bỏ mục nào. */
  function section(title, node, extraClass, collapsed) {
    const cls = "proc-section" + (extraClass ? " " + extraClass : "");
    if (!collapsed) {
      const s = el("section", cls);
      s.appendChild(el("h4", "proc-h", title));
      s.appendChild(node);
      return s;
    }
    const d = el("details", cls + " proc-collapsible");
    const sum = el("summary");
    sum.appendChild(el("h4", "proc-h", title));
    d.append(sum, node);
    return d;
  }

  function paragraph(text) {
    const p = el("div", "proc-text");
    // Mô tả của cổng là một khối dài; tách dòng theo gạch đầu dòng cho dễ đọc.
    String(text || "")
      .split(/(?:^|\s)[-•]\s+(?=[A-ZĐÀ-Ỹ])/)
      .map((s) => s.trim())
      .filter(Boolean)
      .forEach((chunk) => p.appendChild(el("p", "", chunk)));
    if (!p.childNodes.length) p.appendChild(el("p", "", String(text || "")));
    return p;
  }

  /* ─── Checklist tick được. Trạng thái tick lưu theo thủ tục ở localStorage,
     để người dân đóng tab rồi quay lại vẫn còn — họ đi làm hồ sơ nhiều ngày. */
  /* `visible`: chỉ hiện chừng ấy dòng đầu, phần còn lại gói vào "Xem thêm" —
     cổng hay nhồi 20-30 dòng ghi chú vào thành phần hồ sơ (đo: bảng cao 5.000px). */
  function checklist(items, storeKey, render, visible) {
    const list = el("div", "proc-check");
    let target = list;
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem(storeKey) || "{}"); } catch (e) { saved = {}; }

    items.forEach((item, i) => {
      if (visible && i === visible) {
        const more = el("details", "proc-more");
        more.appendChild(el("summary", "", `Xem thêm ${items.length - visible} mục`));
        list.appendChild(more);
        target = more;
      }
      const row = el("label", "proc-check-row");
      const box = el("input");
      box.type = "checkbox";
      box.checked = Boolean(saved[i]);
      if (box.checked) row.classList.add("done");
      box.onchange = () => {
        row.classList.toggle("done", box.checked);
        saved[i] = box.checked;
        try { localStorage.setItem(storeKey, JSON.stringify(saved)); } catch (e) { /* chế độ riêng tư */ }
      };
      row.appendChild(box);
      row.appendChild(render(item));
      target.appendChild(row);
    });
    return list;
  }

  function componentRow(c) {
    const wrap = el("span", "proc-check-text");
    wrap.appendChild(el("span", "proc-check-name", c.name));
    const bits = [];
    if (c.quantity) bits.push(c.quantity);
    if (c.case_name) bits.push(c.case_name);
    if (bits.length) wrap.appendChild(el("span", "proc-check-meta", bits.join(" · ")));
    return wrap;
  }

  function stepRow(s) {
    const wrap = el("span", "proc-check-text");
    if (s.label) wrap.appendChild(el("span", "proc-check-name", s.label));
    wrap.appendChild(el("span", "proc-step-detail", s.detail));
    return wrap;
  }

  /* ─────────────────────────────────────────────── BẢNG THỦ TỤC ───────── */
  function table(t, convId) {
    const box = el("div", "proc-card");

    /* Cảnh báo hết hạn — nếu có, phải nằm TRÊN CÙNG. */
    if (t.expired) {
      const w = el("div", "proc-warn");
      w.appendChild(el("strong", "", "⚠️ Thủ tục này không còn trong danh mục Cổng Dịch vụ công"));
      w.appendChild(el("p", "", "Cổng không công bố ngày hết hiệu lực; " +
        (t.expired_at ? "ngày mình phát hiện nó biến mất: " + t.expired_at + ". " : "") +
        "Thông tin dưới đây là bản cũ — hãy đối chiếu lại bằng nút Web search trước khi đi nộp hồ sơ."));
      box.appendChild(w);
    }

    /* Tiêu đề */
    const head = el("div", "proc-head");
    head.appendChild(el("h3", "proc-title", t.name));
    const tags = el("div", "proc-tags");
    if (t.domain) tags.appendChild(el("span", "proc-tag", t.domain));
    tags.appendChild(el("span", "proc-tag muted", "Mã " + t.proc_id));
    if (t.scope && t.scope.nationwide) tags.appendChild(el("span", "proc-tag muted", "Toàn quốc"));
    // Bản địa phương: nói rõ tỉnh nào CÔNG BỐ (không phải "chỉ áp dụng ở").
    if (t.scope && t.scope.province) tags.appendChild(el("span", "proc-tag", "📍 Bản của " + t.scope.province));
    // Thuế/Hải quan: cổng xếp cấp xã nhưng ngành dọc giải quyết — không nộp ở phường.
    if (t.scope && t.scope.vertical) tags.appendChild(el("span", "proc-tag", "🏛️ Do " + t.scope.vertical + " giải quyết"));
    head.appendChild(tags);
    box.appendChild(head);

    /* Lựa chọn MCQ đã áp dụng + trí nhớ đã đỡ được câu hỏi nào */
    if (t.memory_used && t.memory_used.length) {
      const m = el("div", "proc-memory");
      m.appendChild(el("span", "", "🧠 Đã dùng lựa chọn bạn nhờ nhớ: " +
        t.memory_used.map((x) => x.value).join(" · ")));
      const undo = el("button", "proc-link-btn", "Quên đi");
      undo.type = "button";
      undo.onclick = async () => {
        for (const x of t.memory_used) {
          try { await API.del("/api/mcq-memory?axis=" + encodeURIComponent(x.axis)); } catch (e) { /* bỏ qua */ }
        }
        m.replaceChildren(el("span", "", "Đã quên. Lần sau mình sẽ hỏi lại bạn."));
      };
      m.appendChild(undo);
      box.appendChild(m);
    }

    /* Giải thích thủ tục */
    box.appendChild(section("Giải thích thủ tục",
      cellBody(t.explanation, (v) => paragraph(v)), "", true));

    /* Thành phần hồ sơ — tick được */
    box.appendChild(section("Thành phần hồ sơ (giấy tờ phải nộp)",
      cellBody(t.components, (v) => checklist(v, `proc:${t.proc_id}:comp`, componentRow, 6))));

    /* Hình thức nộp · Chi phí · Thời gian · Địa điểm — nhóm thành lưới */
    const grid = el("div", "proc-grid");

    const addFact = (label, node) => {
      const cell = el("div", "proc-fact");
      cell.appendChild(el("span", "proc-fact-label", label));
      cell.appendChild(node);
      grid.appendChild(cell);
    };

    addFact("Hình thức nộp", t.submission_methods && t.submission_methods.length
      ? el("span", "proc-fact-value", t.submission_methods.join(" · "))
      : el("span", "proc-absent", "Chưa có thông tin về hình thức nộp: Cổng không công bố."));

    addFact("Chi phí", cellBody(t.fees, (v) => {
      const ul = el("div", "proc-fact-value");
      v.forEach((line) => ul.appendChild(el("div", "", line)));
      return ul;
    }));

    addFact("Thời gian giải quyết",
      cellBody(t.processing_time, (v) => el("span", "proc-fact-value", v)));

    addFact("Địa điểm tiếp nhận trực tiếp",
      cellBody(t.address, (v) => el("span", "proc-fact-value", v)));

    if (t.executing_agency) {
      addFact("Cơ quan thực hiện", el("span", "proc-fact-value", t.executing_agency));
    }
    box.appendChild(section("Thông tin chính", grid, "proc-section-grid"));

    /* Checklist những việc cần làm — tick được */
    if (t.steps && t.steps.length) {
      box.appendChild(section("Checklist những việc cần làm",
        checklist(t.steps, `proc:${t.proc_id}:steps`, stepRow), "", true));
    }

    /* Tài liệu liên quan (bấm để tải) */
    box.appendChild(section("Tài liệu liên quan", cellBody(t.files, (v) => {
      const list = el("div", "proc-files");
      v.forEach((f) => {
        const row = el("div", "proc-file");
        const a = el("a", "proc-file-link", "📄 " + f.name);
        a.href = f.url;
        a.setAttribute("download", f.name);
        row.appendChild(a);
        if (f.description) row.appendChild(el("span", "proc-file-desc", f.description));
        list.appendChild(row);
      });
      return list;
    }), "", true));

    /* Link tới web đăng ký online */
    box.appendChild(section("Nộp hồ sơ trực tuyến", cellBody(t.online, (v) => {
      const wrap = el("div", "proc-online");
      if (isUrl(v.url)) {
        const a = el("a", "proc-online-btn", "🌐 Mở trang nộp hồ sơ trực tuyến");
        a.href = v.url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        wrap.appendChild(a);
      }
      (v.services || []).slice(0, 5).forEach((s) => {
        const line = s.service_name +
          (s.processing_qty
            // Cổng có lúc chỉ ghi số, không ghi đơn vị — nói rõ, đừng để người đọc tự đoán "ngày".
            ? ` — ${s.processing_qty} ${s.processing_unit || "(cổng không ghi đơn vị)"}` : "");
        wrap.appendChild(el("div", "proc-online-svc", line));
      });
      if (!wrap.childNodes.length) wrap.appendChild(el("span", "proc-absent", "Chưa có thông tin về đường dẫn nộp trực tuyến."));
      return wrap;
    })));

    /* Thông tin meta */
    const meta = t.meta || {};
    const mBox = el("div", "proc-meta");
    const metaLine = (label, value) => {
      if (!value) return;
      const r = el("div", "proc-meta-row");
      r.appendChild(el("span", "proc-meta-label", label));
      r.appendChild(el("span", "", value));
      mBox.appendChild(r);
    };
    metaLine("Quyết định công bố", [meta.decision_number, meta.decision_date].filter(Boolean).join(" · "));
    metaLine("Cơ quan ban hành", meta.issuing_agency || meta.department);
    metaLine("Cổng cập nhật", meta.source_updated_at);
    metaLine("Mình cào về ngày", (meta.scraped_at || "").slice(0, 10));
    if (meta.legal_basis && meta.legal_basis.length) {
      const r = el("div", "proc-meta-row");
      r.appendChild(el("span", "proc-meta-label", "Căn cứ pháp lý"));
      const v = el("div", "proc-legal");
      meta.legal_basis.slice(0, 6).forEach((l) =>
        v.appendChild(el("div", "", [l.code, l.name].filter(Boolean).join(" — "))));
      r.appendChild(v);
      mBox.appendChild(r);
    }
    // Nói thẳng là KHÔNG biết ngày hết hạn, thay vì im lặng.
    if (meta.expiry_note) mBox.appendChild(el("p", "proc-absent", "ℹ️ " + meta.expiry_note));
    if (isUrl(meta.portal_url)) {
      const a = el("a", "proc-meta-link", "Xem trên Cổng Dịch vụ công ↗");
      a.href = meta.portal_url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      mBox.appendChild(a);
    }
    if (t.scope && t.scope.note) mBox.appendChild(el("p", "proc-absent", "ℹ️ " + t.scope.note));
    box.appendChild(section("Thông tin nguồn", mBox, "proc-section-meta", true));

    box.appendChild(footer(t, convId));
    return box;
  }

  /* Chân bảng: web search · báo sai ngữ nghĩa · ô chat mới. */
  function footer(t, convId) {
    const f = el("div", "proc-footer");

    const l1 = el("p", "proc-foot-line");
    l1.appendChild(document.createTextNode("Nếu câu trả lời không còn hợp thời, bạn "));
    const ws = el("button", "proc-link-btn", "dùng tính năng Web search");
    ws.type = "button";
    // Systems.toggle() lật sang hệ thống còn lại + tự mở ô chat mới và mang
    // theo câu hỏi cũ. Bảng này chỉ xuất hiện ở Hệ thống 2 nên lật = sang Web search.
    ws.onclick = () => { if (window.Systems && Systems.isRetrieval) Systems.toggle(); };
    l1.appendChild(ws);
    l1.appendChild(document.createTextNode(" để tra lại từ các trang .gov.vn."));
    f.appendChild(l1);

    /* Báo sai ngữ nghĩa -> gửi lại như một câu hỏi mới (hệ thống chạy lại từ đầu). */
    const fix = el("div", "proc-fix");
    fix.appendChild(el("p", "proc-foot-line",
      "Nếu mình hiểu sai ý bạn, hãy mô tả lại thủ tục bạn cần:"));
    const row = el("div", "proc-fix-row");
    const input = el("input", "proc-fix-input");
    input.type = "text";
    input.placeholder = "Ví dụ: tôi cần đăng ký kết hôn với người nước ngoài…";
    const btn = el("button", "proc-fix-btn", "Tra lại");
    btn.type = "button";
    const resend = () => {
      const v = input.value.trim();
      if (!v || (window.Chat && Chat.isSending)) return;
      input.value = "";
      // mode "resubmit": máy chủ xoá bảng cũ rồi tra lại từ đầu trong CÙNG ô
      // chat — không tính là lần 🎯 thứ hai (trước đây bị bộ gác coi là
      // "thủ tục khác" và đuổi sang ô chat mới).
      Chat.send(convId, v, { mode: "resubmit" });
    };
    btn.onclick = resend;
    input.onkeydown = (e) => { if (e.key === "Enter") { e.preventDefault(); resend(); } };
    row.append(input, btn);
    fix.appendChild(row);
    f.appendChild(fix);

    const l2 = el("p", "proc-foot-line muted");
    l2.appendChild(document.createTextNode("Bạn có thể hỏi thêm về thủ tục này ngay bên dưới. Muốn hỏi thủ tục khác, hãy "));
    const nb = el("button", "proc-link-btn", "mở cuộc trò chuyện mới");
    nb.type = "button";
    nb.onclick = () => { if (window.Conversations) Conversations.create(); };
    l2.appendChild(nb);
    l2.appendChild(document.createTextNode(" để mình không trộn lẫn giấy tờ của hai thủ tục."));
    f.appendChild(l2);

    return f;
  }

  /* ─────────────────────────────────────────────────── CÂU HỎI MCQ ─────── */
  function mcq(t, convId) {
    const box = el("div", "proc-mcq");
    box.appendChild(el("p", "proc-mcq-q", t.question));

    const list = el("div", "proc-mcq-list");
    let remember = false;

    (t.options || []).forEach((o, i) => {
      const b = el("button", "proc-mcq-opt");
      b.type = "button";
      b.appendChild(el("span", "proc-mcq-num", String(i + 1)));
      const txt = el("span", "proc-mcq-text");
      txt.appendChild(el("span", "proc-mcq-label", o.label));
      if (o.hint) txt.appendChild(el("span", "proc-mcq-hint", o.hint));
      b.appendChild(txt);
      b.onclick = async () => {
        if (window.Chat && Chat.isSending) return;
        list.querySelectorAll("button").forEach((x) => (x.disabled = true));
        b.classList.add("selected");
        // Nhớ TRƯỚC khi gửi, để chính lượt này cũng được hưởng.
        if (remember && t.memorable) {
          try {
            await API.post("/api/mcq-memory", { axis: t.axis, value: o.value });
          } catch (e) { /* nhớ hỏng thì vẫn phải trả lời được câu hỏi */ }
        }
        Chat.send(convId, o.label);
      };
      list.appendChild(b);
    });
    box.appendChild(list);

    /* "Hỏi xem người dùng có muốn nhớ lựa chọn để về sau đỡ phải chọn hay không"
       — chỉ hiện với trục MÔ TẢ NGƯỜI DÙNG (tư cách, cấp nộp hồ sơ). */
    if (t.memorable) {
      const lab = el("label", "proc-mcq-remember");
      const cb = el("input");
      cb.type = "checkbox";
      cb.onchange = () => { remember = cb.checked; };
      lab.appendChild(cb);
      lab.appendChild(el("span", "", t.remember_label || "Nhớ lựa chọn này cho những lần sau"));
      box.appendChild(lab);
    }
    return box;
  }

  /* ───────────────────────────────────────── MỜI MỞ Ô CHAT MỚI ─────────── */
  function newProcedure(t) {
    const box = el("div", "proc-newchat");
    box.appendChild(el("p", "", "Đang xem: " + (t.current || "")));
    const b = el("button", "proc-online-btn",
      t.question ? "＋ Mở cuộc trò chuyện mới và tra câu này" : "＋ Mở cuộc trò chuyện mới");
    b.type = "button";
    b.onclick = () => { b.disabled = true; searchInNewChat(t.question); };
    box.appendChild(b);
    return box;
  }

  /* Mở ô chat mới rồi tra luôn câu hỏi bằng 🎯 — người dân khỏi gõ lại. */
  async function searchInNewChat(question) {
    if (!window.Conversations) return;
    try {
      const conv = await Conversations.create();
      if (question && window.Chat) {
        await Chat.send(conv.id, question, { mode: "exact" });
        await Conversations.refresh();      // cập nhật tiêu đề ở thanh bên
      }
    } catch (e) { alert(e.message); }
  }

  /* ───────────────────────── GỢI Ý 🎯 dưới câu trả lời trò chuyện ─────── */
  /* Bộ nhận diện (máy chủ) thấy câu này giống hỏi thủ tục -> một chip bấm là
     tra đúng câu đó ở mode "exact". */
  function exactHint(t, convId) {
    const box = el("div", "proc-exact-hint");
    const q = t.question || "";
    const shown = q.length > 70 ? q.slice(0, 70) + "…" : q;
    const b = el("button", "proc-exact-chip", "🎯 Tìm chính xác: “" + shown + "”");
    b.type = "button";
    b.onclick = () => {
      if (window.Chat && Chat.isSending) return;
      b.disabled = true;
      Chat.send(convId, q, { mode: "exact" });
    };
    box.appendChild(b);
    return box;
  }

  /* ──────────────── 🎯 lần hai trong cùng ô chat: ô chat mới hay huỷ ─── */
  function exactUsed(t) {
    const box = el("div", "proc-newchat");
    box.appendChild(el("p", "", "Đang xem: " + (t.current || "")));
    const row = el("div", "proc-choice-row");
    const go = el("button", "proc-online-btn", "＋ Mở cuộc trò chuyện mới và tra câu này");
    go.type = "button";
    const cancel = el("button", "proc-link-btn", "Huỷ");
    cancel.type = "button";
    go.onclick = () => {
      go.disabled = cancel.disabled = true;
      searchInNewChat(t.question);
    };
    cancel.onclick = () => {
      go.disabled = cancel.disabled = true;
      box.appendChild(el("p", "", "Đã huỷ — bạn cứ tiếp tục hỏi về thủ tục đang xem."));
    };
    row.append(go, cancel);
    box.appendChild(row);
    return box;
  }

  /* Điểm vào duy nhất mà chat.js gọi. */
  function render(t, convId) {
    if (!t || typeof t !== "object") return null;
    if (t.kind === "mcq") return mcq(t, convId);
    if (t.kind === "new_procedure") return newProcedure(t);
    if (t.kind === "exact_hint") return exactHint(t, convId);
    if (t.kind === "exact_used") return exactUsed(t);
    if (!t.proc_id) return null;
    return table(t, convId);
  }

  return { render };
})();

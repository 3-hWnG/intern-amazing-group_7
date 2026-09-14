/* Khung chat: hiển thị tin nhắn, stream câu trả lời, nhãn độ tin cậy, phản hồi. */
window.Chat = (function () {
  const TIER_LABEL = {
    A: ["Từ cơ sở dữ liệu thủ tục", "tier-a"],
    B: ["Cần làm rõ thêm", "tier-b"],
    C: ["Nguồn chính thống — chưa đối chiếu nội bộ", "tier-c"],
    D: ["Thông tin chung — KHÔNG chắc chắn", "tier-d"],
  };

  /* v6: nhãn theo NGUỒN BẰNG CHỨNG thật, chính xác hơn nhãn tầng A/B/C/D.
     Tin nhắn nạp lại từ CSDL chỉ có tier nên vẫn cần bảng trên làm dự phòng. */
  const EVIDENCE_LABEL = {
    procedures: ["Từ cơ sở dữ liệu thủ tục", "tier-a"],
    attachments: ["Từ tệp bạn đính kèm", "evidence-attachments"],
    mixed: ["Nhiều nguồn — xem phần Nguồn ở cuối", "evidence-mixed"],
    smalltalk: null,                    /* lời chào: không gắn nhãn gì cả */
    web: ["Nguồn chính thống — chưa đối chiếu nội bộ", "tier-c"],
    none: ["Thông tin chung — KHÔNG chắc chắn", "tier-d"],
  };

  function labelFor(meta) {
    if (meta && meta.evidence && meta.evidence in EVIDENCE_LABEL) {
      return EVIDENCE_LABEL[meta.evidence];      /* null = cố ý không gắn nhãn */
    }
    return (meta && TIER_LABEL[meta.tier]) || null;
  }

  function badge(meta) {
    const found = labelFor(meta);
    if (!found) return null;
    const [label, cls] = found;
    const tag = document.createElement("span");
    tag.className = `tier ${cls}`;
    tag.textContent = label
      + (meta.confidence ? ` · ${Number(meta.confidence).toFixed(2)}` : "");
    /* chuỗi công cụ đã gọi — soi nhanh khi demo, không chiếm chỗ trên màn hình */
    if (meta.tools) tag.title = "Công cụ đã dùng: " + meta.tools;
    return tag;
  }

  const box = () => document.getElementById("messages");

  function scroll() {
    const el = box();
    el.scrollTop = el.scrollHeight;
  }

  function bubble(role, text, meta) {
    const wrap = document.createElement("div");
    wrap.className = `msg ${role}`;

    const body = document.createElement("div");
    body.className = "bubble";
    body.textContent = text || "";
    wrap.appendChild(body);

    if (role === "assistant" && meta) {
      const tag = badge(meta);
      if (tag) wrap.appendChild(tag);
      const src = sourceList(meta.sources);
      if (src) wrap.appendChild(src);
    }

    if (role === "assistant" && meta && meta.id) {
      const fb = document.createElement("div");
      fb.className = "feedback";
      [["phu_hop", "👍"], ["khong_phu_hop", "👎"]].forEach(([verdict, icon]) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = icon;
        b.title = verdict === "phu_hop" ? "Phù hợp" : "Không phù hợp";
        b.onclick = async () => {
          await API.post("/api/feedback", { message_id: meta.id, verdict });
          fb.querySelectorAll("button").forEach((x) => (x.disabled = true));
          b.classList.add("chosen");
        };
        fb.appendChild(b);
      });
      wrap.appendChild(fb);
    }

    box().appendChild(wrap);
    scroll();
    return body;
  }

  /* Nguồn tra cứu. Dựng bằng DOM API chứ KHÔNG phải innerHTML: chuỗi này đến
     từ kết quả tìm kiếm ngoài, nhét thẳng vào innerHTML là mở cửa cho XSS. */
  function sourceList(sources) {
    if (!sources || !sources.length) return null;
    const box = document.createElement("div");
    box.className = "sources";
    const label = document.createElement("span");
    label.className = "sources-label";
    label.textContent = "Nguồn — bấm để tự kiểm tra";
    box.appendChild(label);

    sources.forEach((s, i) => {
      const line = document.createElement("div");
      if (/^https?:\/\//i.test(s)) {
        const a = document.createElement("a");
        a.href = s;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        let shown = s;
        try { shown = decodeURI(s); } catch (_) {}
        a.textContent = `${i + 1}. ${shown}`;
        a.title = s;
        line.appendChild(a);
      } else {
        line.className = "plain";
        line.textContent = `${i + 1}. ${s}`;   /* nguồn nội bộ, không phải link */
      }
      box.appendChild(line);
    });
    return box;
  }

  function clear() {
    box().innerHTML = "";
  }

  function empty() {
    box().innerHTML =
      '<div class="empty"><h2>Bạn cần tra cứu thủ tục nào?</h2>' +
      '<p>Ví dụ: <em>“Con tôi mới sinh, làm giấy khai sinh cần gì?”</em></p></div>';
  }

  async function load(convId) {
    clear();
    if (!convId) { empty(); return; }
    const data = await API.get(`/api/conversations/${convId}`);
    if (!data.messages.length) { empty(); return; }
    data.messages.forEach((m) =>
      bubble(m.role, m.content, { tier: m.tier, confidence: m.confidence,
                                  id: m.id, sources: m.sources }));
  }

  async function send(convId, text, opts) {
    if (box().querySelector(".empty")) clear();
    bubble("user", text);
    const target = bubble("assistant", "…");
    let acc = "";
    let meta = {};

    await API.stream(
      `/api/conversations/${convId}/chat`,
      { text, force_web: !!(opts && opts.forceWeb) },
      (chunk) => {
        if (acc === "") target.textContent = "";
        acc += chunk;
        target.textContent = acc;
        scroll();
      },
      (headers) => {
        meta = {
          tier: headers.get("X-Tier"),
          confidence: headers.get("X-Confidence"),
          evidence: headers.get("X-Evidence"),
          tools: headers.get("X-Tools"),
        };
        const pos = headers.get("X-Queue-Position");
        const info = document.getElementById("queue-info");
        if (info) {
          info.textContent = pos && Number(pos) > 0
            ? `Hàng đợi: còn ${pos} người trước bạn`
            : "";
        }
      }
    );

    const tag = badge(meta);
    if (tag) target.parentElement.appendChild(tag);
    const info = document.getElementById("queue-info");
    if (info) info.textContent = "";
    return acc;
  }

  return { load, send, clear, empty };
})();

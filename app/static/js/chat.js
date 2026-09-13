/* Khung chat: hiển thị tin nhắn, stream câu trả lời, nhãn độ tin cậy, phản hồi. */
window.Chat = (function () {
  const TIER_LABEL = {
    A: ["Từ cơ sở dữ liệu thủ tục", "tier-a"],
    B: ["Cần làm rõ thêm", "tier-b"],
    C: ["Nguồn chính thống — chưa đối chiếu nội bộ", "tier-c"],
    D: ["Thông tin chung — KHÔNG chắc chắn", "tier-d"],
  };

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

    if (role === "assistant" && meta && meta.tier && TIER_LABEL[meta.tier]) {
      const [label, cls] = TIER_LABEL[meta.tier];
      const tag = document.createElement("span");
      tag.className = `tier ${cls}`;
      tag.textContent = label + (meta.confidence ? ` · ${Number(meta.confidence).toFixed(2)}` : "");
      wrap.appendChild(tag);
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
      bubble(m.role, m.content, { tier: m.tier, confidence: m.confidence, id: m.id }));
  }

  async function send(convId, text) {
    if (box().querySelector(".empty")) clear();
    bubble("user", text);
    const target = bubble("assistant", "…");
    let acc = "";
    let meta = {};

    await API.stream(
      `/api/conversations/${convId}/chat`,
      { text },
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

    if (meta.tier && TIER_LABEL[meta.tier]) {
      const [label, cls] = TIER_LABEL[meta.tier];
      const tag = document.createElement("span");
      tag.className = `tier ${cls}`;
      tag.textContent = label + ` · ${Number(meta.confidence || 0).toFixed(2)}`;
      target.parentElement.appendChild(tag);
    }
    const info = document.getElementById("queue-info");
    if (info) info.textContent = "";
    return acc;
  }

  return { load, send, clear, empty };
})();

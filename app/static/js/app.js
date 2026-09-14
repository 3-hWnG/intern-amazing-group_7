/* Ráp các module lại và xử lý sự kiện trang chính. */
(function () {
  const $ = (id) => document.getElementById(id);

  async function boot() {
    let cfg = {};
    try {
      cfg = await API.get("/api/config");
      const me = await API.get("/api/me");
      $("user-name").textContent = me.user.display_name || me.user.email;
    } catch (_) {
      return;   // API.js đã tự chuyển sang /login
    }

    Conversations.onSelect = (id) => {
      Chat.load(id);
      if (cfg.attachments_enabled !== false) Files.refresh(id);
    };
    const items = await Conversations.refresh();
    if (items.length) Conversations.select(items[0].id);
    else Chat.empty();

    await Dev.init(cfg.dev_tools);

    $("new-chat").onclick = () => Conversations.create();

    /* -------- đính kèm tệp -------- */
    const fileInput = $("file-input");
    const attachBtn = $("attach");
    if (cfg.attachments_enabled === false) {
      if (attachBtn) attachBtn.hidden = true;
    } else if (attachBtn && fileInput) {
      try {
        const sup = await API.get("/api/files/supported");
        fileInput.accept = (sup.extensions || []).join(",");
        attachBtn.title = "Đính kèm tệp (" + (sup.extensions || []).join(" ") + ")";
      } catch (_) {}

      attachBtn.onclick = () => fileInput.click();
      fileInput.onchange = async () => {
        const file = fileInput.files && fileInput.files[0];
        fileInput.value = "";
        if (!file) return;
        let id = Conversations.activeId;
        if (!id) id = (await Conversations.create()).id;
        attachBtn.disabled = true;
        try {
          await Files.attach(id, file);
        } finally {
          attachBtn.disabled = false;
        }
      };
    }

    $("logout").onclick = async () => {
      await API.post("/api/logout");
      location.href = "/login";
    };

    $("toggle-sidebar").onclick = () =>
      $("sidebar").classList.toggle("hidden");

    $("theme").onclick = () => {
      const dark = document.body.classList.toggle("light");
      try { localStorage.setItem("theme", dark ? "light" : "dark"); } catch (_) {}
    };
    try {
      if (localStorage.getItem("theme") === "light") document.body.classList.add("light");
    } catch (_) {}

    /* -------- nút Web: ép tra mạng cho đúng lượt tiếp theo -------- */
    const webBtn = $("web-toggle");
    let forceWeb = false;
    if (webBtn) {
      webBtn.onclick = () => {
        forceWeb = !forceWeb;
        webBtn.setAttribute("aria-pressed", String(forceWeb));
        webBtn.title = forceWeb
          ? "Lượt này sẽ tra trên mạng — bấm lại để tắt"
          : "Bắt buộc tra cứu trên mạng cho câu hỏi này";
      };
    }

    const input = $("input");
    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.max(52, Math.min(input.scrollHeight, 220)) + "px";
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        $("composer").requestSubmit();
      }
    });

    let sending = false;
    $("composer").onsubmit = async (e) => {
      e.preventDefault();
      if (sending) return;              // chặn bấm Gửi + Enter cùng lúc
      const text = input.value.trim();
      if (!text) return;
      sending = true;

      let convId = Conversations.activeId;
      if (!convId) convId = (await Conversations.create()).id;

      input.value = "";
      input.style.height = "auto";
      $("send").disabled = true;
      try {
        await Chat.send(convId, text, { forceWeb });
        await Chat.load(convId);      // nạp lại để tin nhắn có id -> bật nút 👍/👎
        if (cfg.attachments_enabled !== false) await Files.refresh(convId);
        await Conversations.refresh();
        Conversations.render();
        if (cfg.dev_tools) { await Dev.stats(); Dev.afterTurn(); }
      } finally {
        sending = false;
        $("send").disabled = false;
        /* Web là lựa chọn cho MỘT lượt, không phải chế độ dính mãi. */
        if (forceWeb && webBtn) {
          forceWeb = false;
          webBtn.setAttribute("aria-pressed", "false");
        }
        input.focus();
      }
    };
  }

  boot();
})();

/* Ráp các module lại và xử lý sự kiện trang chính. */
(function () {
  const $ = (id) => document.getElementById(id);

  /* Bộ nhớ dài hạn: tỉnh/thành, xã/phường trợ lý đã ghi nhớ cho người dùng. */
  async function showMemory(profile) {
    const host = $("memory");
    if (!host) return;
    if (profile === undefined) {
      try { profile = (await API.get("/api/profile")).profile; } catch (_) { profile = {}; }
    }
    const bits = [profile && profile.province, profile && profile.ward].filter(Boolean);
    host.innerHTML = "";
    host.hidden = !bits.length;
    if (!bits.length) return;
    const label = document.createElement("span");
    label.textContent = "🧠 Ghi nhớ: " + bits.join(" · ");
    label.title = "Trợ lý dùng thông tin này cho cả các cuộc trò chuyện sau";
    const rm = document.createElement("button");
    rm.type = "button";
    rm.className = "link";
    rm.textContent = "Xoá";
    rm.onclick = async () => { await API.del("/api/profile"); showMemory({}); };
    host.append(label, rm);
  }

  async function boot() {
    let cfg = {};
    try {
      cfg = await API.get("/api/config");
      const me = await API.get("/api/me");
      $("user-name").textContent = me.user.display_name || me.user.email;
    } catch (_) {
      return;   // api.js đã tự chuyển sang /login
    }
    if ($("model-name")) $("model-name").textContent = cfg.llm_model || "";
    Systems.init(cfg);          // nút Web search: Hệ thống 1 <-> Hệ thống 2

    Conversations.onSelect = (id) => {
      Chat.load(id);
      if (cfg.attachments_enabled !== false) Files.refresh(id);
    };
    const items = await Conversations.refresh();
    if (items.length) Conversations.select(items[0].id);
    else Chat.empty();

    await Promise.all([Dev.init(cfg.dev_tools), showMemory()]);

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
      const light = document.body.classList.toggle("light");
      try { localStorage.setItem("theme", light ? "light" : "dark"); } catch (_) {}
    };
    try {
      if (localStorage.getItem("theme") === "light") document.body.classList.add("light");
    } catch (_) {}

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
      if (!convId) convId = (await Conversations.create({ skipLoad: true })).id;

      input.value = "";
      input.style.height = "auto";
      $("send").disabled = true;
      try {
        const done = await Chat.send(convId, text);
        await Conversations.refresh();
        const current = Conversations.items.find((c) => c.id === convId);
        if (current) $("conv-title").textContent = current.title;
        if (done && done.profile) showMemory(done.profile);
        if (cfg.dev_tools) { await Dev.stats(); Dev.afterTurn(); }
      } finally {
        sending = false;
        $("send").disabled = false;
        input.focus();
      }
    };
  }

  boot();
})();

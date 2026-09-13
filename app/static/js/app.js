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

    Conversations.onSelect = (id) => Chat.load(id);
    const items = await Conversations.refresh();
    if (items.length) Conversations.select(items[0].id);
    else Chat.empty();

    await Dev.init(cfg.dev_tools);

    $("new-chat").onclick = () => Conversations.create();

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

    const input = $("input");
    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 200) + "px";
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
        await Chat.send(convId, text);
        await Chat.load(convId);      // nạp lại để tin nhắn có id -> bật nút 👍/👎
        await Conversations.refresh();
        Conversations.render();
        if (cfg.dev_tools) await Dev.stats();
      } finally {
        sending = false;
        $("send").disabled = false;
        input.focus();
      }
    };
  }

  boot();
})();

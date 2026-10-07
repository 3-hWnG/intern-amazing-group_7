/* System 4 — trang đăng nhập / đăng ký. Thành công -> server đặt cookie phiên -> về trang chính "/". */
(function () {
  const $ = (id) => document.getElementById(id);
  let tab = "login", pub = {};

  function setTab(t) {
    tab = t;
    const signup = t === "signup";
    $("tab-login").classList.toggle("active", !signup);
    $("tab-signup").classList.toggle("active", signup);
    $("tab-login").setAttribute("aria-selected", String(!signup));
    $("tab-signup").setAttribute("aria-selected", String(signup));
    $("pw2-row").hidden = !signup;
    $("password").autocomplete = signup ? "new-password" : "current-password";
    $("auth-submit").textContent = signup ? "Tạo tài khoản" : "Đăng nhập";
    $("auth-sub").textContent = signup
      ? `Tạo tài khoản mới (mật khẩu ít nhất ${pub.min_password_length || 6} ký tự)` : "Đăng nhập để tiếp tục";
    showError("");
  }

  function showError(msg) { $("auth-error").textContent = msg; $("auth-error").hidden = !msg; }

  $("tab-login").onclick = () => setTab("login");
  $("tab-signup").onclick = () => setTab("signup");

  $("auth-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = { username: $("username").value.trim(), password: $("password").value };
    if (!body.username || !body.password) { showError("Nhập tên đăng nhập (hoặc email) và mật khẩu"); return; }
    if (tab === "signup") body.password2 = $("password2").value;
    $("auth-submit").disabled = true;
    try {
      const res = await fetch(tab === "signup" ? "/s4/auth/signup" : "/s4/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Có lỗi, vui lòng thử lại");
      location.href = "/";
    } catch (err) {
      showError(err.message);
    } finally {
      $("auth-submit").disabled = false;
    }
  });

  fetch("/s4/public").then((r) => r.json()).then((p) => {
    pub = p;
    if (p.user) { location.href = "/"; return; }
    document.title = "Đăng nhập · " + p.app_title;
    $("app-title").textContent = p.app_title;
    $("tab-signup").hidden = !p.signup_open;
    $("first-hint").hidden = !p.first_account;
    setTab(p.first_account ? "signup" : "login");
  }).catch(() => {});
})();

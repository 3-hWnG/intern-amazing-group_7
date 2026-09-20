/* Trang đăng nhập / đăng ký. */
(function () {
  const form = document.getElementById("auth-form");
  if (!form) return;

  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const nameRow = document.getElementById("name-row");
  const errorEl = document.getElementById("auth-error");
  const submit = document.getElementById("submit");
  let mode = "login";

  function setMode(next) {
    mode = next;
    tabLogin.classList.toggle("active", mode === "login");
    tabRegister.classList.toggle("active", mode === "register");
    nameRow.hidden = mode === "login";
    submit.textContent = mode === "login" ? "Đăng nhập" : "Tạo tài khoản";
    document.getElementById("password").autocomplete =
      mode === "login" ? "current-password" : "new-password";
    errorEl.hidden = true;
  }

  tabLogin.onclick = () => setMode("login");
  tabRegister.onclick = () => setMode("register");

  form.onsubmit = async (e) => {
    e.preventDefault();
    errorEl.hidden = true;
    submit.disabled = true;
    try {
      await API.post(mode === "login" ? "/api/login" : "/api/register", {
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
        display_name: document.getElementById("display_name").value.trim(),
      });
      location.href = "/";
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.hidden = false;
    } finally {
      submit.disabled = false;
    }
  };

  setMode("login");
})();

/* Lớp gọi API dùng chung. Mọi fetch đi qua đây để xử lý lỗi và 401 một chỗ. */
window.API = (function () {
  async function request(url, options = {}) {
    const res = await fetch(url, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (res.status === 401) {
      if (!location.pathname.startsWith("/login")) location.href = "/login";
      throw new Error("Chưa đăng nhập");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || data.detail || "Lỗi không xác định");
    return data;
  }

  return {
    get: (url) => request(url),
    post: (url, body) => request(url, { method: "POST", body: JSON.stringify(body || {}) }),
    patch: (url, body) => request(url, { method: "PATCH", body: JSON.stringify(body || {}) }),
    del: (url) => request(url, { method: "DELETE" }),

    /* Stream trả về text/plain theo từng mẩu. */
    async stream(url, body, onChunk, onHeaders) {
      const res = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.status === 401) { location.href = "/login"; return; }
      if (onHeaders) onHeaders(res.headers);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        onChunk(`\n[Lỗi] ${err.detail || res.statusText}`);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        onChunk(decoder.decode(value, { stream: true }));
      }
    },
  };
})();

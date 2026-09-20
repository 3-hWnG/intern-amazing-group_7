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

    /* Tải tệp lên: gửi thẳng byte, tên tệp nằm ở header (không cần multipart). */
    async upload(url, file) {
      const res = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Filename": encodeURIComponent(file.name),
          "Content-Type": file.type || "application/octet-stream",
        },
        body: file,
      });
      if (res.status === 401) { location.href = "/login"; throw new Error("Chưa đăng nhập"); }
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || data.error || "Tải tệp thất bại");
      return data;
    },

    /* Luồng NDJSON: mỗi dòng một sự kiện {type, ...}. Dòng không phải JSON
       được coi là chữ thô để không bao giờ nuốt mất thông báo lỗi. */
    async stream(url, body, onEvent) {
      const res = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.status === 401) { location.href = "/login"; return; }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        onEvent({ type: "error", text: err.detail || res.statusText });
        return;
      }
      const flush = (line) => {
        if (!line.trim()) return;
        try { onEvent(JSON.parse(line)); }
        catch (_) { onEvent({ type: "delta", text: line }); }
      };
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let i;
        while ((i = buf.indexOf("\n")) >= 0) {
          flush(buf.slice(0, i));
          buf = buf.slice(i + 1);
        }
      }
      flush(buf + decoder.decode());
    },
  };
})();

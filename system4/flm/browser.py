"""Chrome riêng cho FLM (flm.fpt.edu.vn), điều khiển qua Chrome DevTools Protocol — chỉ dùng thư viện chuẩn.

Trang khách của FLM đòi reCAPTCHA (không có API công khai, leader 19/10/2026: chế độ khách, KHÔNG đăng nhập):
  1. mở Chrome có cửa sổ, hồ sơ riêng (system4/runtime/flm/chrome_profile — không đụng Chrome của người dùng), ở trang captcha;
  2. người dùng tự tích "I'm not a robot"; code chỉ chờ tới khi trang đã qua captcha;
  3. mọi request sau đó chạy BẰNG fetch() bên trong trang đó (cùng cookie, cùng trình duyệt) — không lấy cookie ra ngoài.
Hồ sơ giữ lại giữa các lần, nên phiên còn hạn thì lần sau không phải giải captcha.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path

CHROME_PATHS = (r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")


class BrowserError(Exception):
    pass


def find_chrome() -> str:
    for p in (os.environ.get("FLM_CHROME"), *CHROME_PATHS, shutil.which("chrome"), shutil.which("msedge")):
        if p and Path(p).exists():
            return p
    raise BrowserError("Không tìm thấy Chrome / Edge trên máy (đặt biến FLM_CHROME = đường dẫn chrome.exe).")


class _WS:
    """WebSocket tối giản (RFC 6455) cho CDP trên localhost: khung chữ, có mặt nạ phía client, đọc khung dài 64 bit."""

    def __init__(self, url: str, timeout: float = 60):
        assert url.startswith("ws://")
        hostport, path = url[5:].split("/", 1)
        host, port = hostport.split(":")
        self.s = socket.create_connection((host, int(port)), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.s.recv(4096)
            if not chunk:
                raise BrowserError("CDP đóng kết nối khi bắt tay")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise BrowserError(f"CDP không nhận websocket: {head[:200]!r}")
        self.buf = head.split(b"\r\n\r\n", 1)[1]

    def _read(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise BrowserError("Chrome đã đóng")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, text: str) -> None:
        data = text.encode()
        n = len(data)
        head = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n) if n < 65536
                                else bytes([0x80 | 127]) + struct.pack(">Q", n))
        mask = os.urandom(4)
        self.s.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self) -> str:
        parts = []
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            op = b0 & 0x0F
            if op == 0x8:
                raise BrowserError("Chrome đóng kết nối")
            if op in (0x9, 0xA):   # ping / pong
                continue
            parts.append(payload)
            if b0 & 0x80:
                return b"".join(parts).decode("utf-8", "replace")

    def close(self) -> None:
        try:
            self.s.close()
        except OSError:
            pass


class Browser:
    def __init__(self, profile: Path, port: int = 9333):
        self.profile, self.port = profile, port
        self.proc: subprocess.Popen | None = None
        self.ws: _WS | None = None
        self._id = 0

    # ------------------------------------------------------------ khởi động
    def _targets(self) -> list[dict]:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=3) as r:
            return json.loads(r.read())

    def start(self, url: str) -> None:
        self.profile.mkdir(parents=True, exist_ok=True)
        try:
            self._targets()   # Chrome FLM của lần trước vẫn mở: dùng lại
        except OSError:
            self.proc = subprocess.Popen([find_chrome(), f"--remote-debugging-port={self.port}", "--remote-allow-origins=*",
                                          f"--user-data-dir={self.profile}", "--no-first-run", "--no-default-browser-check",
                                          "--new-window", url])
            for _ in range(60):
                try:
                    self._targets()
                    break
                except OSError:
                    time.sleep(0.25)
            else:
                raise BrowserError("Chrome không mở được cổng điều khiển")
        page = next((t for t in self._targets() if t.get("type") == "page"), None)
        if not page:
            raise BrowserError("Chrome không có tab nào")
        self.ws = _WS(page["webSocketDebuggerUrl"])
        if self.proc is None:   # dùng lại cửa sổ cũ: đưa về trang cần mở
            self.call("Page.navigate", url=url)

    def call(self, method: str, **params) -> dict:
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise BrowserError(f"{method}: {msg['error'].get('message')}")
                return msg.get("result") or {}

    def eval(self, expr: str, timeout: float = 120):
        """Chạy JS trong trang (chờ Promise xong), trả giá trị JSON."""
        r = self.call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True, timeout=int(timeout * 1000))
        if r.get("exceptionDetails"):
            raise BrowserError("JS lỗi: " + json.dumps(r["exceptionDetails"], ensure_ascii=False)[:300])
        return (r.get("result") or {}).get("value")

    def location(self) -> str:
        return self.eval("location.href") or ""

    def fetch(self, url: str) -> tuple[int, str, str]:
        """GET url (cùng trang web) bằng fetch() của trang. Trả (mã HTTP, địa chỉ cuối sau chuyển hướng, nội dung)."""
        r = self.eval(f"fetch({json.dumps(url)}, {{credentials: 'include'}}).then(async r => [r.status, r.url, await r.text()])")
        return int(r[0]), r[1], r[2]

    def close(self, quit_chrome: bool = True) -> None:
        if self.ws:
            self.ws.close()
            self.ws = None
        if quit_chrome and self.proc:
            try:
                self.proc.terminate()
            except OSError:
                pass
            self.proc = None

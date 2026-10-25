"""Tình trạng AI dùng chung cho Strict và Friendly (G3.3, P15, D8).

- cpu_only(): model đang chạy KHÔNG nằm trên card đồ hoạ (Ollama `ps`: size_vram = 0) hoặc S4_FORCE_CPU=1.
  Chưa nạp model nào: đoán theo có `nvidia-smi` hay không (chỉ tới khi model được nạp lần đầu). Đệm 30 giây.
  Máy không GPU: bước LLM của Strict (hạn 7 s) gần như chắc hết giờ rồi rơi về bản code -> BỎ QUA hẳn, trả bản code ngay.
  Friendly vẫn dùng AI (chậm 7–40 giây), giao diện hiện cảnh báo.
- breaker: ngắt mạch Ollama — 3 lỗi liên tiếp thì bỏ qua LLM 60 giây (không bắt người dùng chờ hết hạn từng lần).
- rules_only(request): lượt Strict này có bỏ bước LLM không = máy không GPU, hoặc người dùng bật "Chỉ trả lời bằng luật"
  (System 4 gắn RULES_ONLY_PROVIDER đọc tuỳ chọn của tài khoản)."""
from __future__ import annotations

import os
import shutil
import threading
import time

FAILS, OPEN_SECONDS = 3, 60
RULES_ONLY_PROVIDER = None   # System 4: fn(request) -> bool (tuỳ chọn "Chỉ trả lời bằng luật" của tài khoản)


class Breaker:
    def __init__(self, fails: int = FAILS, open_seconds: float = OPEN_SECONDS):
        self.max_fails, self.open_seconds = fails, open_seconds
        self._lock = threading.Lock()
        self.fails, self.open_until = 0, 0.0

    def allow(self) -> bool:
        return time.monotonic() >= self.open_until

    def ok(self) -> None:
        with self._lock:
            self.fails = 0

    def fail(self) -> None:
        with self._lock:
            self.fails += 1
            if self.fails >= self.max_fails:
                self.open_until, self.fails = time.monotonic() + self.open_seconds, 0

    def state(self) -> dict:
        left = max(0.0, self.open_until - time.monotonic())
        return {"open": left > 0, "seconds_left": round(left, 1), "fails": self.fails}


breaker = Breaker()
_cpu = {"at": 0.0, "value": False, "why": ""}


def _probe() -> tuple[bool, str]:
    if os.environ.get("S4_FORCE_CPU") == "1":
        return True, "S4_FORCE_CPU=1"
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    try:
        import httpx
        models = httpx.get(host.rstrip("/") + "/api/ps", timeout=1.0).json().get("models") or []
    except Exception:
        models = None
    if models:
        on_gpu = [m for m in models if (m.get("size_vram") or 0) > 0]
        return (not on_gpu), ("model nằm trên GPU" if on_gpu else "model đang chạy bằng CPU (size_vram = 0)")
    if shutil.which("nvidia-smi") is None:
        return True, "chưa nạp model; không thấy nvidia-smi"
    return False, "chưa nạp model; có nvidia-smi"


def cpu_only(max_age: float = 30.0) -> bool:
    if os.environ.get("S4_FORCE_CPU") == "1":
        return True
    if time.monotonic() - _cpu["at"] > max_age:
        v, why = _probe()
        _cpu.update(at=time.monotonic(), value=v, why=why)
    return _cpu["value"]


def status() -> dict:
    return {"cpu_only": cpu_only(), "why": _cpu["why"] or ("S4_FORCE_CPU=1" if os.environ.get("S4_FORCE_CPU") == "1" else ""),
            "breaker": breaker.state()}


def rules_only(request=None) -> bool:
    """Lượt Strict này bỏ bước LLM? Máy không GPU, hoặc tài khoản bật "Chỉ trả lời bằng luật"."""
    if cpu_only():
        return True
    if RULES_ONLY_PROVIDER is not None and request is not None:
        try:
            return bool(RULES_ONLY_PROVIDER(request))
        except Exception:
            return False
    return False

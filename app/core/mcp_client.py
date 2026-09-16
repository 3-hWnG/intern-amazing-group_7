"""Client MCP — giữ MỘT phiên kết nối lâu dài tới MCP search server.

    MCP_TRANSPORT=stdio   app tự bật app/mcp_search/server.py làm tiến trình con (mặc định)
    MCP_TRANSPORT=http    nối tới server đang chạy ở MCP_SERVER_URL (Docker)
    MCP_TRANSPORT=direct  gọi thẳng engine trong tiến trình, KHÔNG qua MCP (gỡ lỗi)

Phiên MCP là async (anyio) còn pipeline chạy trong luồng của hàng đợi, nên phiên
sống trong một event loop riêng. Mọi lời gọi đi qua một hàng đợi nội bộ để việc
mở và đóng phiên luôn nằm trong CÙNG một task — anyio bắt buộc như vậy.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import sys
import threading

from config import (APP_DIR, MCP_FALLBACK_DIRECT, MCP_SERVER_URL, MCP_TIMEOUT,
                    MCP_TRANSPORT, PROJECT_ROOT)

SERVER_SCRIPT = APP_DIR / "mcp_search" / "server.py"
_STOP = "__stop__"
_PING = "__ping__"


class MCPUnavailable(RuntimeError):
    pass


class MCPTimeout(MCPUnavailable):
    """Công cụ chạy quá lâu. KHÔNG gọi lại engine trong tiến trình: việc đó vừa
    chạy xong ở phía server, làm lại chỉ tốn thêm đúng ngần ấy thời gian nữa."""


def _describe(exc: BaseException) -> str:
    inner = getattr(exc, "exceptions", None)          # ExceptionGroup của anyio
    if inner:
        return _describe(inner[0])
    return f"{type(exc).__name__}: {exc}"


class _Bridge:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self.connected = False
        self.last_error = ""
        self.tools: list[str] = []

    # ------------------------------------------------------------ vòng đời --
    def ensure_started(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._ready.clear()
            self._loop = (asyncio.ProactorEventLoop() if sys.platform == "win32"
                          else asyncio.new_event_loop())
            self._thread = threading.Thread(target=self._run, name="mcp-client", daemon=True)
            self._thread.start()
            self._ready.wait(5)

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._queue = asyncio.Queue()
        self._loop.create_task(self._owner())
        self._loop.call_soon(self._ready.set)
        self._loop.run_forever()

    def _target(self):
        if MCP_TRANSPORT == "http":
            return MCP_SERVER_URL
        from mcp.client.stdio import StdioServerParameters
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        return StdioServerParameters(command=sys.executable, args=[str(SERVER_SCRIPT)],
                                     cwd=str(PROJECT_ROOT), env=env)

    async def _owner(self) -> None:
        from mcp import Client
        pending = None
        while True:
            if pending is None:
                pending = await self._queue.get()
            if pending[0] == _STOP:
                break
            inflight = None
            try:
                async with Client(self._target(), read_timeout_seconds=MCP_TIMEOUT) as client:
                    listed = await client.list_tools()
                    self.tools = [t.name for t in getattr(listed, "tools", listed)]
                    self.connected, self.last_error = True, ""
                    while True:
                        if pending is None:
                            pending = await self._queue.get()
                        inflight, pending = pending, None
                        name, args, fut = inflight
                        if name == _STOP:
                            self.connected = False
                            self._loop.stop()
                            return
                        if not fut.done():
                            result = (list(self.tools) if name == _PING
                                      else await client.call_tool(name, args))
                            if not fut.done():
                                fut.set_result(result)
                        inflight = None
            except Exception as exc:
                self.connected = False
                self.last_error = _describe(exc)
                failed = [x for x in (inflight, pending) if x]
                pending = None
                while not self._queue.empty():
                    failed.append(self._queue.get_nowait())
                for name, _, fut in failed:
                    if name == _STOP:
                        self._loop.stop()
                        return
                    if not fut.done():
                        fut.set_exception(MCPUnavailable(self.last_error))
        self._loop.stop()

    def submit(self, name: str, args: dict, timeout: float):
        self.ensure_started()
        fut: concurrent.futures.Future = concurrent.futures.Future()
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (name, args, fut))
        try:
            return fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            fut.cancel()
            raise MCPTimeout(f"MCP không phản hồi sau {timeout:.0f} giây") from exc

    def stop(self) -> None:
        if self._loop and self._thread and self._thread.is_alive():
            fut: concurrent.futures.Future = concurrent.futures.Future()
            self._loop.call_soon_threadsafe(self._queue.put_nowait, (_STOP, {}, fut))
            self._thread.join(timeout=5)


_bridge = _Bridge()


def _payload(result):
    """CallToolResult -> dữ liệu Python (ưu tiên structured content)."""
    if getattr(result, "is_error", False) or getattr(result, "isError", False):
        raise MCPUnavailable(f"công cụ MCP báo lỗi: {_text(result)[:300]}")
    data = getattr(result, "structured_content", None)
    if data is None:
        data = getattr(result, "structuredContent", None)
    if isinstance(data, dict) and set(data) == {"result"}:
        data = data["result"]
    if data is not None:
        return data
    text = _text(result)
    try:
        return json.loads(text)
    except Exception:
        return text


def _text(result) -> str:
    return "".join(getattr(c, "text", "") or "" for c in (getattr(result, "content", None) or []))


def _direct(name: str, args: dict):
    from mcp_search import engine
    if name == "search_evidence":
        return engine.build_evidence_pack(args.get("question", ""), args.get("queries"),
                                          args.get("top_k", 5))
    if name == "web_search":
        log: list[str] = []
        return {"query": args.get("query", ""), "diagnostics": log,
                "results": engine.web_search(args.get("query", ""), args.get("max_results", 8), log)}
    if name == "fetch_page":
        return engine.fetch_page(args.get("url", ""))
    raise MCPUnavailable(f"không có công cụ {name}")


# ==========================================================================
# API cho phần còn lại của ứng dụng
# ==========================================================================
def call_tool(name: str, args: dict, timeout: float = MCP_TIMEOUT + 10) -> tuple[object, str]:
    """Gọi công cụ -> (kết quả, transport thực tế đã dùng)."""
    if MCP_TRANSPORT == "direct":
        return _direct(name, args), "direct"
    try:
        return _payload(_bridge.submit(name, args, timeout)), f"mcp/{MCP_TRANSPORT}"
    except Exception as exc:
        if isinstance(exc, MCPTimeout) or not MCP_FALLBACK_DIRECT:
            raise
        return _direct(name, args), f"direct (MCP lỗi: {_describe(exc)})"


def search_evidence(question: str, queries: list[str], top_k: int) -> dict:
    try:
        pack, transport = call_tool("search_evidence",
                                    {"question": question, "queries": queries, "top_k": top_k})
    except Exception as exc:
        return {"question": question, "queries": queries, "sources": [], "diagnostics": [],
                "error": f"MCP lỗi: {_describe(exc)}", "transport": f"mcp/{MCP_TRANSPORT}"}
    if not isinstance(pack, dict):
        pack = {"question": question, "queries": queries, "sources": [],
                "diagnostics": [], "error": f"MCP trả về dữ liệu lạ: {str(pack)[:200]}"}
    pack["transport"] = transport
    return pack


def connect(timeout: float = 30) -> dict:
    """Mở phiên sớm lúc khởi động để câu hỏi đầu tiên không phải chờ bật server."""
    if MCP_TRANSPORT != "direct":
        try:
            _bridge.submit(_PING, {}, timeout)
        except Exception:
            pass
    if MCP_TRANSPORT == "direct" or MCP_FALLBACK_DIRECT:
        # engine có thể chạy ngay trong tiến trình này -> import sẵn thư viện đọc trang
        import threading
        from mcp_search import engine
        threading.Thread(target=engine.warm_up, daemon=True).start()
    return status()


def status() -> dict:
    return {"transport": MCP_TRANSPORT,
            "url": MCP_SERVER_URL if MCP_TRANSPORT == "http" else "",
            "connected": _bridge.connected if MCP_TRANSPORT != "direct" else None,
            "tools": list(_bridge.tools), "last_error": _bridge.last_error}


def shutdown() -> None:
    _bridge.stop()

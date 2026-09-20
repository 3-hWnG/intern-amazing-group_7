"""MCP server "tthc-search" — công cụ tìm kiếm cho Evidence Pack.

    python Backend/mcp_search/server.py                              # stdio (app tự bật)
    python Backend/mcp_search/server.py --transport http --host 0.0.0.0 --port 8765

Công cụ:
    search_evidence(question, queries, top_k)  tra web -> xếp hạng -> đọc trang -> Evidence Pack
    web_search(query, max_results)             kết quả tìm kiếm thô đã xếp độ tin cậy
    fetch_page(url)                            nội dung chính của một trang

Ở chế độ stdio, stdout là kênh giao thức: KHÔNG print gì ra stdout.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# parents[1] = Backend/ (các gói) · parents[2] = gốc dự án (config.py)
for _p in (str(Path(__file__).resolve().parents[1]),
           str(Path(__file__).resolve().parents[2])):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from mcp.server.mcpserver import MCPServer  # noqa: E402

from mcp_search import engine  # noqa: E402

server = MCPServer(
    "tthc-search",
    instructions=("Tra cứu thông tin thủ tục hành chính Việt Nam trên web, ưu tiên "
                  "nguồn chính thống (.gov.vn), trả về Evidence Pack có URL và ngày."),
    log_level="WARNING",
)


@server.tool()
def search_evidence(question: str, queries: list[str], top_k: int = 5) -> dict:
    """Tra web theo nhiều truy vấn, xếp hạng nguồn (ưu tiên .gov.vn, mới nhất), đọc
    trang và trả về Evidence Pack: các nguồn kèm đoạn nội dung liên quan nhất."""
    return engine.build_evidence_pack(question, queries, max(1, min(int(top_k), 10)))


@server.tool()
def web_search(query: str, max_results: int = 8) -> dict:
    """Tìm kiếm web một truy vấn; trả về kết quả kèm tên miền và mức độ tin cậy."""
    log: list[str] = []
    results = engine.web_search(query, max(1, min(int(max_results), 20)), log)
    return {"query": query, "results": results, "diagnostics": log}


@server.tool()
def fetch_page(url: str) -> dict:
    """Tải một trang web và trích nội dung chính (văn bản thuần + ngày đăng nếu có)."""
    return engine.fetch_page(url)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    logging.getLogger().setLevel(logging.WARNING)
    for noisy in ("httpx", "httpcore", "primp", "ddgs", "trafilatura", "htmldate"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    engine.warm_up()          # import sẵn trafilatura trước khi nhận câu hỏi đầu tiên
    if args.transport == "stdio":
        server.run("stdio")
        return

    kwargs = {"host": args.host, "port": args.port}
    if args.host not in ("127.0.0.1", "localhost"):
        # Trong Docker, app gọi tới bằng tên dịch vụ (mcp-search:8765): tắt chặn
        # DNS-rebinding vốn chỉ cho phép Host là localhost.
        from mcp.server.transport_security import TransportSecuritySettings
        kwargs["transport_security"] = TransportSecuritySettings(
            enable_dns_rebinding_protection=False)
    server.run("streamable-http", **kwargs)


if __name__ == "__main__":
    main()

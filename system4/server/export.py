"""Xuất hội thoại Friendly: Markdown, JSON, trang in (trình duyệt tự mở hộp thoại in -> Lưu thành PDF)."""
from __future__ import annotations
import html
import json
import re

_ROLE = {"user": "Bạn", "assistant": "Trợ lý"}


def filename(title: str, ext: str) -> str:
    base = re.sub(r"[^\w\- ]+", "", title, flags=re.UNICODE).strip().replace(" ", "_")[:50] or "hoi_thoai"
    return f"{base}.{ext}".encode("ascii", "ignore").decode() or f"hoi_thoai.{ext}"


def to_markdown(conv: dict, msgs: list[dict]) -> str:
    out = [f"# {conv['title']}", "", f"_Friendly mode · tạo lúc {conv['created_at']} (UTC)_", ""]
    for m in msgs:
        out += [f"**{_ROLE.get(m['role'], m['role'])}:**", "", m["content"], ""]
    return "\n".join(out)


def to_json(conv: dict, msgs: list[dict]) -> str:
    return json.dumps({"conversation": {**conv, "mode": "friendly"}, "messages": msgs}, ensure_ascii=False, indent=2)


def to_print_html(conv: dict, msgs: list[dict]) -> str:
    rows = "".join(f"<h3>{_ROLE.get(m['role'], m['role'])}</h3><div class='m'>{html.escape(m['content'])}</div>" for m in msgs)
    return (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'><title>{html.escape(conv['title'])}</title>"
            "<style>body{font:15px/1.55 'Segoe UI',sans-serif;max-width:760px;margin:24px auto;padding:0 16px}"
            ".m{white-space:pre-wrap}h3{margin:18px 0 4px;font-size:14px;color:#3f8ae0}</style></head>"
            f"<body><h1>{html.escape(conv['title'])}</h1>{rows}<script>print()</script></body></html>")

"""Xuất hộp thoại ra file: Markdown (đọc/in) hoặc JSON (lưu/xử lý). Chỉ nội dung người dùng thấy, KHÔNG kèm plan/trace dev."""
import html
import json
import re
import unicodedata


def _public(m: dict) -> dict:
    d = {"role": m["role"], "time": m["created_at"], "text": m["content"]}
    if m.get("blocks"):
        d["blocks"] = [{"title": b.get("title", ""), "text": b.get("text", ""), "sources": b.get("sources", [])} for b in m["blocks"]]
    if m.get("clarify"):
        cl = m["clarify"]
        d["clarify"] = {"question": cl.get("question", ""), "options": cl.get("options", [])}
    return d


def to_json(conv: dict, messages: list[dict]) -> str:
    return json.dumps({"title": conv["title"], "created_at": conv["created_at"], "messages": [_public(m) for m in messages]},
                      ensure_ascii=False, indent=2)


def to_markdown(conv: dict, messages: list[dict]) -> str:
    out = [f"# {conv['title']}", f"*Tạo lúc {conv['created_at']} (UTC) · xuất từ System 3*", ""]
    for m in messages:
        p = _public(m)
        if p["role"] == "user":
            out += [f"**Bạn:** {p['text']}", ""]
            continue
        out.append("**Trợ lý:**")
        out.append("")
        for b in p.get("blocks") or []:
            if b["title"]:
                out += [f"### {b['title']}", ""]
            out += [b["text"].strip(), ""]
            for s in b["sources"]:
                out.append(f"- Nguồn: [{s.get('label', 'nguồn')}]({s.get('url', '')})" if s.get("url") else f"- Nguồn: {s.get('label', '')}")
            if b["sources"]:
                out.append("")
        if p.get("clarify"):
            cl = p["clarify"]
            out += [cl["question"], ""] + [f"{i}. {o}" for i, o in enumerate(cl["options"], 1)] + [""]
        if not p.get("blocks") and not p.get("clarify"):
            out += [p["text"], ""]
        out.append("---")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def to_print_html(conv: dict, messages: list[dict]) -> str:
    """Trang in được: mở ở tab mới, tự gọi hộp thoại in để 'Lưu thành PDF' (không cần thư viện PDF, font tiếng Việt do trình duyệt lo).
    ponytail: người dùng phải bấm Lưu trong hộp thoại in; cần tải thẳng file PDF thì thêm fpdf2/reportlab + font có dấu."""
    e = html.escape
    parts = []
    for m in messages:
        p = _public(m)
        if p["role"] == "user":
            parts.append(f'<div class="turn user"><div class="who">Bạn</div><div class="bubble">{e(p["text"])}</div></div>')
            continue
        body = []
        for b in p.get("blocks") or []:
            if b["title"]:
                body.append(f'<h3>{e(b["title"])}</h3>')
            body.append(f'<div class="txt">{e(b["text"].strip())}</div>')
            for s_ in b["sources"]:
                lab, url = e(s_.get("label", "nguồn")), s_.get("url", "")
                body.append(f'<div class="src">Nguồn: <a href="{e(url, quote=True)}">{lab}</a></div>' if url.startswith(("http://", "https://")) else f'<div class="src">Nguồn: {lab}</div>')
        if p.get("clarify"):
            cl = p["clarify"]
            body.append(f'<div class="txt">{e(cl["question"])}</div><ol>' + "".join(f"<li>{e(o)}</li>" for o in cl["options"]) + "</ol>")
        if not body:
            body.append(f'<div class="txt">{e(p["text"])}</div>')
        parts.append(f'<div class="turn bot"><div class="who">Trợ lý</div><div class="bubble">{"".join(body)}</div></div>')
    title = e(conv["title"])
    return f"""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><title>{title}</title>
<style>
body{{font:14px/1.55 "Segoe UI",Roboto,Arial,sans-serif;color:#1d2330;max-width:780px;margin:24px auto;padding:0 16px}}
h1{{font-size:20px;margin:0 0 4px}} .meta{{color:#6b7280;font-size:12px;margin-bottom:18px}}
.turn{{margin:12px 0;page-break-inside:avoid}} .who{{font-size:12px;font-weight:600;color:#6b7280;margin-bottom:3px}}
.bubble{{border:1px solid #dde2e9;border-radius:10px;padding:10px 14px}} .user .bubble{{background:#eef4ff}}
.txt{{white-space:pre-wrap;overflow-wrap:anywhere}} h3{{font-size:14px;color:#1d5fd1;margin:0 0 6px}}
.src{{font-size:12px;color:#4b5563;margin-top:4px}} a{{color:#1d5fd1}}
.bar{{position:sticky;top:0;background:#fff;padding:8px 0;margin-bottom:8px;border-bottom:1px solid #dde2e9}}
.bar button{{font:inherit;padding:6px 14px;border:1px solid #dde2e9;border-radius:8px;background:#f6f7f9;cursor:pointer}}
@media print{{.bar{{display:none}} body{{margin:0;max-width:none}}}}
</style></head><body>
<div class="bar"><button onclick="window.print()">In / Lưu thành PDF</button></div>
<h1>{title}</h1><div class="meta">Tạo lúc {e(conv["created_at"])} (UTC) · xuất từ System 3</div>
{"".join(parts)}
<script>window.addEventListener("load", function () {{ setTimeout(function () {{ window.print(); }}, 300); }});</script>
</body></html>"""


def filename(title: str, ext: str) -> str:
    """Tên file ASCII an toàn (bỏ dấu), tối đa 50 ký tự."""
    s = unicodedata.normalize("NFKD", title.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")[:50] or "hop-thoai"
    return f"{s}.{ext}"

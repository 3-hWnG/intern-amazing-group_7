"""Bản đọc được (HTML -> PDF qua LibreOffice) của bản nháp LaTeX bài 1, khi chưa biên dịch được bằng LaTeX.

Chỉ hiểu phần LaTeX mà bài dùng: \\section, \\subsection, \\textbf, \\emph, \\cite, \\ref, \\label, itemize, bảng \\tbl + tabular,
toán nội dòng đơn giản, \\todo. Dàn trang KHÁC template ws-vjcs; số trang thật phải biên dịch trên Overleaf.

    python tools/tex_to_html.py <thư mục latex> <tệp .html ra>
"""
import html
import re
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
read = lambda p: open(f"{SRC}/{p}", encoding="utf-8").read()


def strip_comments(s):
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", l) for l in s.splitlines())


def arg(s, i):
    """s[i] == '{' -> (nội dung trong ngoặc, vị trí sau ngoặc đóng)."""
    assert s[i] == "{", s[i:i + 30]
    d, j = 0, i
    while True:
        if s[j] == "{" and s[j - 1] != "\\":
            d += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            d -= 1
            if d == 0:
                return s[i + 1:j], j + 1
        j += 1


def expand_inputs(s):
    return re.sub(r"\\input\{([^}]+)\}", lambda m: strip_comments(read(m.group(1) + ".tex")), s)


SYM = {r"\kappa": "κ", r"\approx": "≈", r"\cdot": "·", r"\rightarrow": "→", r"\leq": "≤", r"\geq": "≥", r"\times": "×", r"\pm": "±"}


def math(m):
    t = m.group(1)
    for k, v in SYM.items():
        t = t.replace(k, v)
    t = re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", t)
    t = re.sub(r"\^(\w)", r"<sup>\1</sup>", t)
    t = t.replace("-", "−").replace("<", "&lt;").replace("&lt;sup>", "<sup>").replace("&lt;/sup>", "</sup>")
    return t


def bib():
    s = read("refs.bib")
    out = {}
    for chunk in re.split(r"\n(?=@)", s):
        m = re.match(r"\s*@\w+\{([^,]+),", chunk)
        if not m:
            continue
        f = dict(re.findall(r'(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"', chunk))
        out[m.group(1).strip()] = {k: re.sub(r"[{}]", "", v).replace("--", "–").replace("\\&", "&amp;") for k, v in f.items()}
    return out


def fmt_ref(e):
    parts = [e.get("author", ""), "“" + e.get("title", "") + "”"]
    for k in ("journal", "booktitle", "howpublished"):
        if e.get(k):
            parts.append("<i>" + e[k] + "</i>")
    if e.get("volume"):
        parts.append("vol. " + e["volume"])
    if e.get("pages"):
        parts.append("pp. " + e["pages"].replace("--", "–"))
    parts.append(e.get("year", ""))
    if e.get("note"):
        parts.append(e["note"])
    return ", ".join(p for p in parts if p) + "."


def main():
    main_tex = strip_comments(read("main.tex"))
    title, _ = arg(main_tex, main_tex.index(r"\title{") + 6)
    author, _ = arg(main_tex, main_tex.index(r"\author{") + 7)
    address, _ = arg(main_tex, main_tex.index(r"\address{") + 8)
    keywords, _ = arg(main_tex, main_tex.index(r"\keywords{") + 9)
    body = expand_inputs(main_tex[main_tex.index(r"\maketitle"):main_tex.index(r"\bibliographystyle")])
    abstract = strip_comments(read("sections/abstract.tex"))
    body = body.replace(abstract, "")
    body = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}", "", body, flags=re.S)
    body = re.sub(r"\\(maketitle|pub\{[^}]*\}\{[^}]*\})", "", body)
    # đánh số mục, nhãn
    labels, cites, n_sec, n_sub, n_tab = {}, [], 0, 0, 0
    for m in re.finditer(r"\\(section|subsection)(\*?)\{([^}]*)\}(\\label\{([^}]*)\})?|\\label\{(tab:[^}]*)\}|\\cite\{([^}]*)\}", body):
        if m.group(1) == "section" and not m.group(2):
            n_sec += 1; n_sub = 0
            if m.group(5): labels[m.group(5)] = str(n_sec)
        elif m.group(1) == "subsection":
            n_sub += 1
            if m.group(5): labels[m.group(5)] = f"{n_sec}.{n_sub}"
        elif m.group(6):
            n_tab += 1; labels[m.group(6)] = str(n_tab)
        elif m.group(7):
            for k in m.group(7).split(","):
                if k.strip() not in cites:
                    cites.append(k.strip())
    refs = bib()
    num = {k: i + 1 for i, k in enumerate(cites)}
    s = body
    # bảng
    def table(m):
        cap, j = arg(m.group(0), m.group(0).index(r"\tbl{") + 4)
        lab = re.search(r"\\label\{([^}]*)\}", cap)
        cap = re.sub(r"\\label\{[^}]*\}", "", cap)
        t0 = m.group(0)
        k = t0.index(r"\begin{tabular}") + len(r"\begin{tabular}")
        _, k = arg(t0, k)                                   # bỏ phần định dạng cột {@{}lccc@{}} (có ngoặc lồng)
        tab = t0[k:t0.index(r"\end{tabular}")]
        tab = re.sub(r"\\(toprule|midrule|bottomrule)", "", tab)
        rows = [r.strip() for r in tab.split(r"\\") if r.strip()]
        out = [f'</p><p class="cap"><b>Table {labels.get(lab.group(1), "")}.</b> {cap}</p>'
               '<table border="1" cellspacing="0" cellpadding="2" frame="hsides" rules="rows">']
        for i, r in enumerate(rows):
            tag = "th" if i == 0 else "td"
            out.append("<tr>" + "".join(f"<{tag}>{c.strip()}</{tag}>" for c in r.split("&")) + "</tr>")
        return "".join(out) + "</table><p>"
    s = re.sub(r"\\begin\{table\}(\[[^]]*\])?.*?\\end\{table\}", table, s, flags=re.S)
    # lệnh nội dòng
    s = re.sub(r"\$([^$]+)\$", math, s)
    s = re.sub(r"\\cite\{([^}]*)\}", lambda m: "<sup>[" + ",".join(str(num[k.strip()]) for k in m.group(1).split(",")) + "]</sup>", s)
    s = re.sub(r"(Section|Table)~\\ref\{([^}]*)\}", lambda m: f"{m.group(1)} {labels.get(m.group(2), '?')}", s)
    s = re.sub(r"\\ref\{([^}]*)\}", lambda m: labels.get(m.group(1), "?"), s)
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    for _ in range(4):
        s = re.sub(r"\\textbf\{([^{}]*)\}", r"<b>\1</b>", s)
        s = re.sub(r"\\emph\{([^{}]*)\}", r"<i>\1</i>", s)
        s = re.sub(r"\\todo\{([^{}]*)\}", r'<span class="todo">[TODO: \1]</span>', s)
    sec = [0, 0]
    def heading(m):
        star, t = m.group(2), m.group(3)
        if m.group(1) == "section":
            if star:
                return f"<h2>{t}</h2>"
            sec[0] += 1; sec[1] = 0
            return f"<h2>{sec[0]}. {t}</h2>"
        sec[1] += 1
        return f"<h3>{sec[0]}.{sec[1]} {t}</h3>"
    s = re.sub(r"\\(section|subsection)(\*?)\{([^}]*)\}", heading, s)
    s = s.replace(r"\begin{itemize}", "<ul>").replace(r"\end{itemize}", "</ul>")
    s = re.sub(r"\\item\s*", "<li>", s)
    s = s.replace("``", "“").replace("''", "”").replace("---", "—").replace("--", "–").replace("~", "&nbsp;")
    s = s.replace(r"\%", "%").replace(r"\&", "&amp;").replace(r"\_", "_").replace(r"\,", "&thinsp;").replace(r"\ ", " ").replace(r"\\", "<br>")
    s = s.replace(r"\rlap", "")
    s = re.sub(r"\n\s*\n", "\n</p><p>\n", s)
    reflist = "".join(f"<li>{fmt_ref(refs[k])}</li>" for k in cites if k in refs)
    def clean_inline(t):
        t = re.sub(r"\\footnote\{([^}]*)\}", r"<sup>*</sup>", t)
        return t.replace(r"\\", "<br>").replace("--", "–")
    head = f"""<!doctype html><html><head><meta charset="utf-8"><title>Paper 1 draft</title><style>
body{{font-family:'Times New Roman',serif;font-size:11pt;line-height:1.35;max-width:6.5in;margin:auto}}
h1{{font-size:15pt;text-align:center}} h2{{font-size:12pt;margin-top:14pt}} h3{{font-size:11pt;font-style:italic}}
.meta{{text-align:center;font-size:10pt}} .abstract{{font-size:10pt;margin:10pt 0.4in}} .draft{{color:#a00;font-size:9pt;text-align:center}}
table{{border-collapse:collapse;font-size:9pt;margin:8pt auto;line-height:1.1}} td,th{{border-top:1px solid #999;border-bottom:1px solid #999;padding:1pt 5pt;margin:0}}
th{{text-align:left}}
.cap{{font-size:9pt;margin:8pt 0 2pt 0}} .todo{{color:#c00;font-weight:bold}} ol{{font-size:9pt}}
</style></head><body>
<p class="draft">DRAFT, not for distribution. Readable version generated from the LaTeX sources (tools/tex_to_html.py); the layout differs from the VJCS template.</p>
<h1>{clean_inline(title)}</h1><p class="meta">{clean_inline(author)}<br>{clean_inline(address)}</p>
<div class="abstract"><b>Abstract.</b> {re.sub(r"[$]([^$]+)[$]", math, abstract).replace(chr(92) + "%", "%").replace("--", "–")}<br><b>Keywords:</b> {keywords}</div>
<p>"""
    open(OUT, "w", encoding="utf-8").write(head + s + f"</p><h2>References</h2><ol>{reflist}</ol></body></html>")
    print("sections", sec[0], "tables", n_tab, "citations", len(cites), "missing refs", [k for k in cites if k not in refs])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

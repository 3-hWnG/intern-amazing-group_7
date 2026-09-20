r"""Sinh Documentation\CODEBASE_INDEX.md - ban do ma nguon.

    .venv\Scripts\python.exe Utility\scripts\make_index.py

Muc dich: cho NGUOI va cho AI (Claude/Gemini) biet "thu gi nam o dau" ma khong
phai mo tung file. Doc index ~10KB thay vi doc ca repo ~900KB.
Chay lai sau moi lan them/xoa/doi ten file.

Purpose: a compact map of the codebase so a human or an AI can locate code
without reading every file. Regenerate after adding or renaming files.
"""

from __future__ import annotations

import ast
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Documentation" / "CODEBASE_INDEX.md"

# Thu muc quet, theo thu tu hien thi. (folder, mo ta ngan)
SECTIONS = [
    ("Backend", "May chu: API, pipeline tra loi, CSDL, MCP search"),
    ("Frontend", "Giao dien: HTML + CSS + JS thuan, khong framework"),
    ("Database", "Luoc do + du lieu nguon + CSDL dang chay"),
    ("Evaluation", "Cham diem pipeline va chat luong truy van"),
    ("Utility", "Fine-tune + script van hanh"),
]
SKIP_DIRS = {".venv", ".git", "__pycache__", "runtime", "results", "output", "node_modules"}
CODE_EXT = {".py", ".js", ".css", ".html", ".sql", ".ps1", ".bat"}


def iter_files(base: Path):
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.suffix.lower() in CODE_EXT:
            yield p


def first_doc_line(path: Path, text: str) -> str:
    """Mot dong mo ta file: docstring Python, hoac dong chu thich dau tien."""
    if path.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text)) or ""
        except SyntaxError:
            doc = ""
        line = doc.strip().splitlines()[0] if doc.strip() else ""
        if line:
            return line
    for raw in text.splitlines()[:12]:
        s = raw.strip()
        for mark in ("# ", "// ", "/* ", "-- ", "<!-- "):
            if s.startswith(mark):
                s = s[len(mark):].strip(" -*/<!>")
                if len(s) > 3 and not s.startswith(("---", "===")):
                    return s
        if s.startswith("<h1") or s.startswith("# "):
            return s.lstrip("# ").strip()
    return ""


def py_symbols(text: str) -> list[str]:
    """Class / def cap cao nhat + method cua class, kem so dong."""
    out: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.append(f"c:{node.name}@{node.lineno}")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and not sub.name.startswith("_"):
                    out.append(f"  .{sub.name}@{sub.lineno}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                out.append(f"f:{node.name}@{node.lineno}")
    return out


def js_symbols(text: str) -> list[str]:
    out = []
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        for pat in ("export function ", "export async function ",
                    "function ", "async function ", "export class ", "class "):
            if s.startswith(pat):
                name = s[len(pat):].split("(")[0].split("{")[0].strip()
                if name:
                    out.append(f"f:{name}@{i}")
                break
    return out


def wrap(items: list[str], width: int = 88) -> list[str]:
    lines, cur = [], ""
    for it in items:
        piece = it if not cur else "  " + it
        if len(cur) + len(piece) > width:
            lines.append(cur)
            cur = it
        else:
            cur += piece
    if cur:
        lines.append(cur)
    return lines


def main() -> int:
    parts: list[str] = []
    parts.append("# Ban do ma nguon / Codebase index\n")
    parts.append(f"*Sinh tu dong ngay {date.today().isoformat()} bang "
                 "`Utility\\scripts\\make_index.py`. Dung sua tay - chay lai script.*\n")
    parts.append(
        "**Cach doc / How to read** — moi dong: `duong/dan (so_dong) - mo ta`, "
        "dong duoi la cac ky hieu chinh:\n"
        "`f:ten@dong` = ham / function · `c:Ten@dong` = lop / class · "
        "`.ten@dong` = method cua lop ngay tren.\n\n"
        "Mo dung cho: `Read file_path offset=<dong>`.\n")

    total_files = total_lines = 0
    for folder, desc in SECTIONS:
        base = ROOT / folder
        if not base.is_dir():
            continue
        parts.append(f"\n---\n\n## {folder}/\n\n{desc}\n")
        current_dir = None
        for p in iter_files(base):
            rel = p.relative_to(ROOT).as_posix()
            parent = Path(rel).parent.as_posix()
            if parent != current_dir:
                current_dir = parent
                parts.append(f"\n**`{parent}/`**\n")
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            n = text.count("\n") + 1
            total_files += 1
            total_lines += n
            doc = first_doc_line(p, text)
            parts.append(f"- `{p.name}` ({n}d)" + (f" - {doc}" if doc else ""))
            syms = py_symbols(text) if p.suffix == ".py" else (
                js_symbols(text) if p.suffix == ".js" else [])
            for line in wrap(syms):
                parts.append(f"  `{line}`")

    parts.append(f"\n---\n\n**Tong / total: {total_files} tep, {total_lines} dong.**\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"[OK] {OUT}")
    print(f"     {total_files} files, {total_lines} lines, {OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

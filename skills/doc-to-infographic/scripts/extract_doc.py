#!/usr/bin/env python3
"""
extract_doc.py — convert a source document to clean Markdown for ingestion.

Usage:
    python extract_doc.py <path> [> out.md]

Supported inputs:
    .md / .markdown / .txt   -> printed through unchanged
    .docx                    -> headings, paragraphs, and tables -> Markdown
    .html / .htm             -> text + tables -> Markdown (best effort)

Strategy for .docx (first that works wins):
    1) mammoth  -> Markdown (best structure)
    2) python-docx -> manual paragraph + table extraction
    3) pandoc (if installed) via subprocess

Missing libraries are auto-installed with --break-system-packages. The goal is a
faithful Markdown rendering — especially TABLES, which carry most of the structure
in business/finance frameworks. Never drop tables.
"""
import sys, os, subprocess, importlib


def _ensure(mod, pip_name=None):
    try:
        return importlib.import_module(mod)
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet",
             "--break-system-packages", pip_name or mod],
            check=False,
        )
        try:
            return importlib.import_module(mod)
        except ImportError:
            return None


def passthrough(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def docx_via_mammoth(path):
    mammoth = _ensure("mammoth")
    if not mammoth:
        return None
    try:
        with open(path, "rb") as f:
            return mammoth.convert_to_markdown(f).value
    except Exception:
        return None


def docx_via_python_docx(path):
    docx = _ensure("docx", "python-docx")
    if not docx:
        return None
    try:
        doc = docx.Document(path)
    except Exception:
        return None

    out = []

    def emit_table(tbl):
        rows = [[c.text.strip().replace("\n", " ") for c in r.cells] for r in tbl.rows]
        if not rows:
            return
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        out.append("| " + " | ".join(rows[0]) + " |")
        out.append("| " + " | ".join(["---"] * ncol) + " |")
        for r in rows[1:]:
            out.append("| " + " | ".join(r) + " |")
        out.append("")

    # Walk body in document order so tables land where they belong.
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parent = doc.element.body
    for child in parent.iterchildren():
        if child.tag.endswith("}p"):
            p = Paragraph(child, doc)
            text = p.text.strip()
            if not text:
                continue
            style = (p.style.name or "").lower() if p.style else ""
            if "heading 1" in style or style == "title":
                out.append(f"# {text}")
            elif "heading 2" in style:
                out.append(f"## {text}")
            elif "heading 3" in style:
                out.append(f"### {text}")
            elif "heading" in style:
                out.append(f"#### {text}")
            else:
                out.append(text)
            out.append("")
        elif child.tag.endswith("}tbl"):
            emit_table(Table(child, doc))
    return "\n".join(out)


def docx_via_pandoc(path):
    try:
        r = subprocess.run(["pandoc", "-f", "docx", "-t", "gfm", path],
                           capture_output=True, text=True, check=True)
        return r.stdout
    except Exception:
        return None


def html_to_md(path):
    raw = passthrough(path)
    md = _ensure("markdownify")
    if md:
        try:
            return md.markdownify(raw, heading_style="ATX")
        except Exception:
            pass
    import re
    return re.sub(r"<[^>]+>", "", raw)


def main():
    if len(sys.argv) < 2:
        print("usage: python extract_doc.py <path>", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    ext = os.path.splitext(path)[1].lower()

    if ext in (".md", ".markdown", ".txt"):
        result = passthrough(path)
    elif ext == ".docx":
        result = (docx_via_mammoth(path)
                  or docx_via_python_docx(path)
                  or docx_via_pandoc(path))
        if result is None:
            print("error: could not convert .docx (install mammoth, python-docx, "
                  "or pandoc)", file=sys.stderr)
            sys.exit(1)
    elif ext in (".html", ".htm"):
        result = html_to_md(path)
    else:
        # last resort: try reading as text
        result = passthrough(path)

    sys.stdout.write(result)


if __name__ == "__main__":
    main()

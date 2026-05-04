#!/usr/bin/env python3
"""Build a standalone static site from chapter files.

Generates a complete, self-contained website in the site/public/ directory.
Zero dependencies — Python stdlib only.
Upload site/public/ to GitHub Pages, Vercel, Cloudflare Pages, or any static host.
"""

import os
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "chapters"
OUTPUT_DIR = PROJECT_ROOT / "docs"

CSS = """\
:root {
    --bg: #faf9f7;
    --text: #2c2c2c;
    --link: #8b4513;
    --border: #e0d8cf;
    --accent: #f5f0e8;
    --muted: #999;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    max-width: 720px; margin: 0 auto; padding: 2rem 1.5rem;
    font-family: "Noto Serif SC", "Source Han Serif SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Georgia, serif;
    background: var(--bg); color: var(--text); line-height: 1.9; font-size: 1.08rem;
}
h1 { font-size: 1.8rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
h2 { font-size: 1.3rem; margin: 2rem 0 0.8rem; }
nav { margin: 1.5rem 0; }
nav a { color: var(--link); text-decoration: none; margin-right: 1rem; }
nav a:hover { text-decoration: underline; }
.chapter-list { list-style: none; padding: 0; }
.chapter-list li { padding: 0.75rem 0; border-bottom: 1px solid var(--border); }
.chapter-list a { color: var(--link); text-decoration: none; font-size: 1.1rem; }
.chapter-list a:hover { text-decoration: underline; }
.chapter-date { color: var(--muted); font-size: 0.85rem; margin-left: 1rem; }
article p { text-indent: 2em; margin: 0.6em 0; }
article h2 { text-indent: 0; }
.chapter-nav { display: flex; justify-content: space-between; margin: 2rem 0; padding: 1rem 0; border-top: 1px solid var(--border); }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.85rem; text-align: center; }
.intro { margin: 1.5rem 0; font-size: 1.05rem; }
.cta { margin: 1.5rem 0; }
.cta a { display: inline-block; padding: 0.4rem 1.2rem; background: var(--link); color: #fff; text-decoration: none; border-radius: 4px; margin-right: 0.5rem; }
.cta a.rss { background: none; color: var(--link); border: 1px solid var(--border); }
"""


def _get_chapters() -> list[dict]:
    """Parse all chapter files and return sorted list."""
    chapters = []
    for f in sorted(CHAPTERS_DIR.glob("chapter-*.md")):
        text = f.read_text(encoding="utf-8")
        info = _parse_chapter(text, f.stem)
        if info:
            chapters.append(info)
    return sorted(chapters, key=lambda c: c["weight"])


def _parse_chapter(text: str, filename: str) -> dict | None:
    """Parse a chapter markdown file with frontmatter."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    meta = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
    body = parts[2].strip()
    # Convert markdown headings to HTML
    body_html = _md_to_html(body)
    return {
        "title": meta.get("title", filename),
        "date": meta.get("date", ""),
        "weight": int(meta.get("weight", 0)),
        "filename": filename,
        "body_html": body_html,
    }


def _md_to_html(text: str) -> str:
    """Minimal markdown-to-HTML converter."""
    lines = text.split("\n")
    out = []
    in_para = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_para:
                out.append("</p>")
                in_para = False
            continue
        if stripped.startswith("## "):
            if in_para:
                out.append("</p>")
                in_para = False
            out.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            if in_para:
                out.append("</p>")
                in_para = False
            out.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped == "---":
            if in_para:
                out.append("</p>")
                in_para = False
            out.append("<hr>")
        else:
            if not in_para:
                out.append("<p>")
                in_para = True
            else:
                out.append("")
            # Inline formatting
            content = stripped
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", content)
            out[-1] += content

    if in_para:
        out.append("</p>")
    return "\n".join(out)


def _render_page(title: str, body: str, nav_links: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
{nav_links}
{body}
<footer><p>剑雨江湖 · 每日更新 · AI 辅助创作</p></footer>
</body>
</html>"""


def build():
    """Build the complete static site."""
    chapters = _get_chapters()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build index page
    index_body = _build_index(chapters)
    index_html = _render_page("剑雨江湖", index_body, '<nav><strong>剑雨江湖</strong></nav>')
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Build individual chapter pages
    for i, ch in enumerate(chapters):
        prev_link = ""
        next_link = ""
        if i > 0:
            prev = chapters[i - 1]
            prev_link = f'<a href="{prev["filename"]}.html">← {prev["title"]}</a>'
        if i < len(chapters) - 1:
            nxt = chapters[i + 1]
            next_link = f'<a href="{nxt["filename"]}.html">{nxt["title"]} →</a>'

        nav = f'<nav><a href="index.html">← 目录</a></nav>'
        nav_footer = ""
        if prev_link or next_link:
            nav_footer = f'<div class="chapter-nav">{prev_link}{next_link}</div>'

        body = f"<article><h2>{ch['title']}</h2>{ch['body_html']}{nav_footer}</article>"
        html = _render_page(f"{ch['title']} — 剑雨江湖", body, nav)
        (OUTPUT_DIR / f"{ch['filename']}.html").write_text(html, encoding="utf-8")

    # Copy chapters as raw markdown too (useful for some deployments)
    print(f"Built {len(chapters)} chapter pages + index")
    print(f"Output: {OUTPUT_DIR}")


def _build_index(chapters: list[dict]) -> str:
    items = ""
    for ch in reversed(chapters):
        items += f'<li><a href="{ch["filename"]}.html">{ch["title"]}</a><span class="chapter-date">{ch["date"]}</span></li>\n'

    return f"""<h1>剑雨江湖</h1>
<div class="intro"><p>连载小说 · 每日更新 · {len(chapters)} 章</p></div>
<h2>章节目录</h2>
<ul class="chapter-list">{items}</ul>"""


if __name__ == "__main__":
    build()

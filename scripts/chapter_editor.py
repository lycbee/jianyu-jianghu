"""Editor pass — review and revise a generated chapter draft."""

import os
from pathlib import Path

from api_client import call_claude
from context_builder import _chinese_num

STORY_BIBLE_DIR = Path(__file__).resolve().parent.parent / "story-bible"
CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "chapters"


def get_model() -> str:
    return os.getenv("EDITOR_MODEL", "claude-sonnet-4-6")


def get_style_guide() -> str:
    path = STORY_BIBLE_DIR / "style-guide.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def get_character_summary() -> str:
    path = STORY_BIBLE_DIR / "characters.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def edit_chapter(chapter_text: str, chapter_num: int, dry_run: bool = False) -> str:
    """Review and revise a chapter draft."""
    cn = _chinese_num(chapter_num)
    prev_chapter_path = CHAPTERS_DIR / f"chapter-{chapter_num - 1:03d}.md"
    prev_chapter = ""
    if prev_chapter_path.exists():
        prev_chapter = prev_chapter_path.read_text(encoding="utf-8")[-2000:]

    prompt = f"""你是一位严格的小说编辑。请审查并修订以下新章节。

## 风格指南
{get_style_guide()}

## 角色参考
{get_character_summary()}

## 前一章结尾（检查连贯性）
{prev_chapter if prev_chapter else "（这是第一章，无前文）"}

## 待审章节
{chapter_text}

---

请检查以下方面：
1. **连贯性（最高优先级）**：本章开头是否直接承接了前一章结尾的场景、地点、时间和人物状态？如果前一章结尾有未解决的冲突，本章是否处理了？如果发现跳跃或断裂，必须重写开头使其衔接顺畅。角色行为、对话风格是否与设定一致？
2. **情节**：情节推进是否合理？本章大纲是否完成？
3. **节奏**：是否过于拖沓或仓促？
4. **语言**：是否有重复用词、陈词滥调、语法错误？
5. **悬念**：章末是否有足够的钩子吸引读者继续阅读？

请直接输出修订后的完整章节正文。如果不需要修改，请输出 "NO_CHANGES_NEEDED"（仅此一行）。

重要规则：
- 只输出章节正文，不要附加任何修订说明、注释或点评
- 保持原文的优点和风格
- 只修改确实有问题的地方
- 不要无故删减篇幅
- 以 "## 第{cn}章" 开头
- 输出格式必须是纯粹的章节内容，不能包含任何元评论"""

    if dry_run:
        print(f"[DRY RUN] Would review chapter {chapter_num}")
        return chapter_text

    result = call_claude(
        prompt,
        system="你是一位资深的中文文学编辑，对文字质量要求严格，擅长发现情节漏洞和角色不一致。",
        model=get_model(),
        max_tokens=4096,
        temperature=0.3,
    )

    if result.strip() == "NO_CHANGES_NEEDED":
        return chapter_text

    return result


def _get_used_titles() -> set[str]:
    """Collect all previously used chapter titles."""
    used = set()
    for f in sorted(CHAPTERS_DIR.glob("chapter-*.md")):
        text = f.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("title:"):
                # Extract title between quotes, remove "第X章 · " prefix
                raw = line.split(":", 1)[1].strip().strip('"')
                # "第X章 · Title" -> "Title"
                if " · " in raw:
                    title_part = raw.split(" · ", 1)[1]
                    used.add(title_part)
                break
    return used


def generate_title(chapter_text: str, chapter_num: int, dry_run: bool = False) -> str:
    """Generate a chapter title based on the chapter content."""
    if dry_run:
        return ""

    used = _get_used_titles()
    avoid = ""
    if used:
        avoid = f"\n\n请勿使用以下已有标题：{'、'.join(sorted(used))}"

    prompt = (
        f"请为以下小说章节取一个标题。要求：2-6个汉字，概括本章核心内容或点睛之笔，"
        f"有江湖气不要太直白，只输出标题本身不要任何其他内容。{avoid}\n\n"
        f"章节内容：\n{chapter_text[:2000]}\n\n标题："
    )

    title = call_claude(
        prompt,
        model=get_model(),
        max_tokens=50,
        temperature=0.7,
    )
    title = title.strip()

    # Post-generation dedup: force retry if title already used
    used = _get_used_titles()
    if title in used:
        retry_prompt = (
            f"请为以下小说章节重新取一个标题。要求：2-6个汉字，概括本章核心内容或点睛之笔，"
            f"有江湖气不要太直白，只输出标题本身不要任何其他内容。\n\n"
            f"重要：绝对不能使用以下已有标题：{'、'.join(sorted(used))}\n\n"
            f"章节内容：\n{chapter_text[:2000]}\n\n标题："
        )
        title = call_claude(
            retry_prompt,
            model=get_model(),
            max_tokens=50,
            temperature=0.7,
        )
        title = title.strip()

    return title


def finalize_chapter(chapter_text: str, chapter_num: int, title: str = "") -> Path:
    """Save the final edited chapter to the chapters directory."""
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)
    cn = _chinese_num(chapter_num)

    title_part = f"第{cn}章"
    if title:
        title_part += f" · {title}"

    final_text = f"""---
title: "{title_part}"
date: {_today()}
weight: {chapter_num}
---

{chapter_text}
"""
    path = CHAPTERS_DIR / f"chapter-{chapter_num:03d}.md"
    path.write_text(final_text, encoding="utf-8")
    return path


def _today() -> str:
    from datetime import date
    return date.today().isoformat()

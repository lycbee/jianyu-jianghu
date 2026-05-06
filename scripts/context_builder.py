"""Assemble prompt context from the Story Bible for a chapter generation."""

import re
from pathlib import Path

STORY_BIBLE_DIR = Path(__file__).resolve().parent.parent / "story-bible"
CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "chapters"


def _read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_yaml_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-style frontmatter and return (metadata, body)."""
    text = text.strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            metadata = {}
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    metadata[key.strip()] = val.strip()
            return metadata, parts[2].strip()
    return {}, text


def get_style_guide_condensed(max_chars: int = 500) -> str:
    """Return a condensed version of the style guide."""
    full = _read_file(STORY_BIBLE_DIR / "style-guide.md")
    if not full:
        return ""
    # Take the body after frontmatter, but limit length
    _, body = _parse_yaml_frontmatter(full)
    if len(body) <= max_chars:
        return body
    # Truncate to max_chars at nearest paragraph boundary
    return body[:max_chars].rsplit("\n\n", 1)[0]


def get_characters_context(max_chars: int = 800) -> str:
    """Return character profiles relevant to the current story stage."""
    full = _read_file(STORY_BIBLE_DIR / "characters.md")
    if not full:
        return ""
    _, body = _parse_yaml_frontmatter(full)
    return _truncate_to(body, max_chars)


def get_previous_chapters(count: int = 3) -> list[str]:
    """Return the full text of the most recent N chapters."""
    chapter_files = sorted(CHAPTERS_DIR.glob("chapter-*.md"))
    recent = chapter_files[-count:] if len(chapter_files) >= count else chapter_files
    chapters = []
    for f in recent:
        text = _read_file(f)
        if text:
            chapters.append(text)
    return chapters


# Chinese numeral mapping for chapter headers
_CHINESE_NUMERALS = {
    1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
    6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
    11: "十一", 12: "十二", 13: "十三", 14: "十四", 15: "十五",
    16: "十六", 17: "十七", 18: "十八", 19: "十九", 20: "二十",
    21: "二十一", 22: "二十二", 23: "二十三", 24: "二十四", 25: "二十五",
    26: "二十六", 27: "二十七", 28: "二十八", 29: "二十九", 30: "三十",
    31: "三十一", 32: "三十二", 33: "三十三", 34: "三十四", 35: "三十五",
    36: "三十六", 37: "三十七", 38: "三十八", 39: "三十九", 40: "四十",
    41: "四十一", 42: "四十二", 43: "四十三", 44: "四十四", 45: "四十五",
    46: "四十六", 47: "四十七", 48: "四十八", 49: "四十九", 50: "五十",
    51: "五十一", 52: "五十二", 53: "五十三", 54: "五十四", 55: "五十五",
    56: "五十六", 57: "五十七", 58: "五十八", 59: "五十九", 60: "六十",
    61: "六十一", 62: "六十二", 63: "六十三", 64: "六十四", 65: "六十五",
    66: "六十六", 67: "六十七", 68: "六十八", 69: "六十九", 70: "七十",
    71: "七十一", 72: "七十二", 73: "七十三", 74: "七十四", 75: "七十五",
    76: "七十六", 77: "七十七", 78: "七十八", 79: "七十九", 80: "八十",
    81: "八十一", 82: "八十二", 83: "八十三", 84: "八十四", 85: "八十五",
    86: "八十六", 87: "八十七", 88: "八十八", 89: "八十九", 90: "九十",
    91: "九十一", 92: "九十二", 93: "九十三", 94: "九十四", 95: "九十五",
    96: "九十六", 97: "九十七", 98: "九十八", 99: "九十九",
    100: "一百", 101: "一百零一", 102: "一百零二", 103: "一百零三",
    104: "一百零四", 105: "一百零五", 106: "一百零六", 107: "一百零七",
    108: "一百零八", 109: "一百零九", 110: "一百一十",
}


def _chinese_num(n: int) -> str:
    return _CHINESE_NUMERALS.get(n, str(n))


def get_chapter_outline(chapter_num: int) -> str:
    """Extract the outline for a specific chapter from outline.md."""
    full = _read_file(STORY_BIBLE_DIR / "outline.md")
    if not full:
        return ""
    _, body = _parse_yaml_frontmatter(full)
    cn = _chinese_num(chapter_num)
    # Match both "## 第X章" and "### 第X章" formats
    for hashes in ("###", "##"):
        pattern = rf"{hashes} 第{cn}章.*?\n(.*?)(?={hashes} 第|\Z)"
        match = re.search(pattern, body, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""


def get_next_chapter_number() -> int:
    """Determine the next chapter number to write."""
    chapter_files = sorted(CHAPTERS_DIR.glob("chapter-*.md"))
    if not chapter_files:
        return 1
    last = chapter_files[-1].stem  # "chapter-042"
    try:
        return int(last.split("-")[1]) + 1
    except (IndexError, ValueError):
        return 1


def get_previous_chapter_ending(char_count: int = 500) -> str:
    """Extract the last N chars of the most recent chapter for continuity injection."""
    chapter_files = sorted(CHAPTERS_DIR.glob("chapter-*.md"))
    if not chapter_files:
        return ""
    text = _read_file(chapter_files[-1])
    if not text:
        return ""
    _, body = _parse_yaml_frontmatter(text)
    body = body.strip()
    if len(body) <= char_count:
        return body
    return body[-char_count:]


def get_previous_chapter_hook() -> str:
    """Extract the cliffhanger from chapter-summaries.md for the last completed chapter."""
    full = _read_file(STORY_BIBLE_DIR / "chapter-summaries.md")
    if not full:
        return ""
    _, body = _parse_yaml_frontmatter(full)

    chapter_files = sorted(CHAPTERS_DIR.glob("chapter-*.md"))
    if not chapter_files:
        return ""
    try:
        last_num = int(chapter_files[-1].stem.split("-")[1])
    except (IndexError, ValueError):
        return ""
    cn = _chinese_num(last_num)

    pattern = rf"## 第{cn}章\b.*?- 章节钩子:\s*(.*?)(?=\n## |\n\n## |\Z)"
    match = re.search(pattern, body, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: last hook in file
    last = ""
    for m in re.finditer(r"- 章节钩子:\s*(.*)", body):
        last = m.group(1).strip()
    return last


def get_unresolved_foreshadowing(max_chars: int = 300) -> str:
    """Extract unresolved foreshadowing items from plot-tracker."""
    full = _read_file(STORY_BIBLE_DIR / "plot-tracker.md")
    if not full:
        return ""
    _, body = _parse_yaml_frontmatter(full)
    # Extract the "Planted (unresolved)" section
    pattern = r"### Planted \(unresolved\)\s*\n(.*?)(?=###)"
    match = re.search(pattern, body, re.DOTALL)
    if match:
        items = match.group(1).strip()
        return _truncate_to(items, max_chars)
    return ""


def get_emotional_curve() -> str:
    """Return recent emotional curve data."""
    full = _read_file(STORY_BIBLE_DIR / "chapter-summaries.md")
    if not full:
        return ""
    _, body = _parse_yaml_frontmatter(full)
    # Extract the tension table row
    pattern = r"\| Tension \|(.*)\|"
    match = re.search(pattern, body)
    if match:
        return f"Recent tension levels: {match.group(1).strip()}"
    return ""


def _truncate_to(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0]


def build_context(chapter_num: int | None = None) -> dict:
    """Assemble the full context for writing the next chapter.

    Returns a dict with assembled prompt sections and the chapter number.
    """
    if chapter_num is None:
        chapter_num = get_next_chapter_number()

    outline = get_chapter_outline(chapter_num)
    prev_chapters = get_previous_chapters(3)
    prev_text = "\n\n---\n\n".join(prev_chapters) if prev_chapters else "(This is the first chapter)"

    context = {
        "chapter_num": chapter_num,
        "style_guide": get_style_guide_condensed(500),
        "characters": get_characters_context(800),
        "previous_chapters": prev_text,
        "previous_chapter_ending": get_previous_chapter_ending(500),
        "previous_chapter_hook": get_previous_chapter_hook(),
        "chapter_outline": outline,
        "unresolved_foreshadowing": get_unresolved_foreshadowing(300),
        "emotional_curve": get_emotional_curve(),
    }
    return context


def build_writer_prompt(context: dict) -> str:
    """Build the full writing prompt from assembled context."""
    cn = _chinese_num(context["chapter_num"])

    ending_block = ""
    if context.get("previous_chapter_ending"):
        ending_block = f"""

## 前一章结尾（必须直接衔接——你的第一句话就要从这个场景开始）
{context['previous_chapter_ending']}"""

    hook_block = ""
    if context.get("previous_chapter_hook"):
        hook_block = f"""

## 前一章钩子（本章开头必须回收或延续此悬念）
{context['previous_chapter_hook']}"""

    prompt = f"""你是一位专业的小说作家。请根据以下指南，用中文撰写小说章节。

## 风格指南
{context['style_guide']}

## 角色档案
{context['characters']}

## 前文回顾（最近三章全文）
{context['previous_chapters']}{ending_block}{hook_block}

## 本章大纲
{context['chapter_outline']}

## 待回收伏笔
{context['unresolved_foreshadowing'] or '无'}

## 情绪曲线参考
{context['emotional_curve'] or '无'}

---

请撰写第{cn}章。要求：
1. 严格遵循本章大纲，但如果大纲与前文实际内容有矛盾，以前文实际内容为准
2. 保持与前文的连贯性（角色性格、说话方式、情节发展）
3. 约 2500 字
4. 章节结尾要有悬念或钩子，引导读者继续阅读下一章
5. 如果有待回收的伏笔，在本章中自然地回收
6. 直接输出章节正文，以 "## 第{cn}章" 开头
7. 重要：章节开头必须直接承接前一章结尾的场景——地点一致、时间连续、人物状态延续。不能跳到不同地点，不能无故跳过时间
8. 如果前一章结尾有未解决的冲突或悬念（如门被撬开、敌人逼近、角色遇险），本章开头必须直接处理该场景，不能跳过"""
    return prompt

"""Update the Story Bible after a chapter is finalized.

This is the "memory consolidation" step — it extracts key information
from the new chapter and updates the relevant bible files.
"""

import os
from pathlib import Path

from api_client import call_claude
from context_builder import _chinese_num

STORY_BIBLE_DIR = Path(__file__).resolve().parent.parent / "story-bible"


def get_model() -> str:
    return os.getenv("EDITOR_MODEL", "claude-sonnet-4-6")


def _read_bible_file(name: str) -> str:
    path = STORY_BIBLE_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _write_bible_file(name: str, content: str) -> None:
    path = STORY_BIBLE_DIR / name
    path.write_text(content, encoding="utf-8")


def update_all(chapter_text: str, chapter_num: int, title: str = "",
               dry_run: bool = False) -> dict[str, str]:
    """Run all bible updates for a newly finalized chapter."""
    updates = {}

    new_summaries = update_chapter_summaries(chapter_text, chapter_num, title, dry_run)
    updates["chapter-summaries.md"] = new_summaries

    new_chars = update_characters(chapter_text, chapter_num, dry_run)
    updates["characters.md"] = new_chars

    new_plot = update_plot_tracker(chapter_text, chapter_num, dry_run)
    updates["plot-tracker.md"] = new_plot

    new_world = update_world_building(chapter_text, chapter_num, dry_run)
    updates["world-building.md"] = new_world

    return updates


def update_chapter_summaries(chapter_text: str, chapter_num: int,
                              title: str = "", dry_run: bool = False) -> str:
    """Append a new chapter summary entry."""
    current = _read_bible_file("chapter-summaries.md")
    cn = _chinese_num(chapter_num)

    prompt = f"""请为以下小说章节生成摘要记录。以严格的Markdown格式输出。

## 第{cn}章
{chapter_text[:3000]}

输出格式：
```
## 第{cn}章{' — ' + title if title else ''}
- 摘要: [200字以内的摘要，包括关键事件、出场角色、发生了什么变化]
- 出场角色: [列出角色名]
- 地点: [列出地点]
- 紧张度: [1-10的数字]
- 基调: [dark/light/tense/hopeful/等]
- 章节钩子: [章节结尾的悬念或引导]
```"""

    if dry_run:
        summary_entry = f"""## 第{cn}章{' — ' + title if title else ''}
- 摘要: (DRY RUN)
- 出场角色: ?
- 地点: ?
- 紧张度: 5
- 基调: neutral
- 章节钩子: (DRY RUN)
"""
    else:
        result = call_claude(
            prompt,
            model=get_model(),
            max_tokens=1024,
            temperature=0.3,
        )
        summary_entry = result.strip()

    # Append before the Emotional Curve section
    if "## Emotional Curve" in current:
        before, after = current.split("## Emotional Curve", 1)
        new_content = before.rstrip() + "\n\n" + summary_entry + "\n\n## Emotional Curve" + after
    else:
        new_content = current.rstrip() + "\n\n" + summary_entry

    _write_bible_file("chapter-summaries.md", new_content)
    return new_content


def update_characters(chapter_text: str, chapter_num: int,
                       dry_run: bool = False) -> str:
    """Update character statuses based on the new chapter."""
    current = _read_bible_file("characters.md")
    cn = _chinese_num(chapter_num)

    prompt = f"""分析以下小说章节，提取角色状态变化。

## 当前角色档案
{current}

## 新章节（第{cn}章）
{chapter_text[:4000]}

请输出更新后的角色档案中每个角色的 "Current Status" 和 "Status Updated" 字段。
对于没有变化的角色，保持原有状态不变。
对于新出场的角色，添加完整档案。
输出完整的characters.md文件内容（保持原有格式）。"""

    if dry_run:
        return current

    result = call_claude(
        prompt,
        model=get_model(),
        max_tokens=4096,
        temperature=0.3,
    )
    new_content = result.strip()

    _write_bible_file("characters.md", new_content)
    return new_content


def update_plot_tracker(chapter_text: str, chapter_num: int,
                         dry_run: bool = False) -> str:
    """Update plot tracker — move resolved foreshadowing, add new ones."""
    current = _read_bible_file("plot-tracker.md")
    cn = _chinese_num(chapter_num)

    prompt = f"""分析以下小说章节，更新情节追踪器。

## 当前情节追踪器
{current}

## 新章节（第{cn}章）
{chapter_text[:4000]}

请输出更新后的plot-tracker.md完整内容：
1. 如果有新的伏笔被埋下，添加到 "Planted (unresolved)" 列表（格式：- [ch-{chapter_num:03d}] [细节] → 目标回收: [大概章节]）
2. 如果有伏笔在本章被回收，将其从 "Planted" 移到 "Resolved" 列表（格式：- [ch-XXX] [细节] → [ch-{chapter_num:03d}] [如何回收]）
3. 如果有新的冲突或子剧情出现，更新相应列表
4. 保持原有格式不变"""

    if dry_run:
        return current

    result = call_claude(
        prompt,
        model=get_model(),
        max_tokens=4096,
        temperature=0.3,
    )
    new_content = result.strip()

    _write_bible_file("plot-tracker.md", new_content)
    return new_content


def update_world_building(chapter_text: str, chapter_num: int,
                           dry_run: bool = False) -> str:
    """Update world-building if new locations or rules are introduced."""
    current = _read_bible_file("world-building.md")
    cn = _chinese_num(chapter_num)

    prompt = f"""分析以下小说章节，检查是否有新的世界观信息需要记录。

## 当前世界观设定
{current}

## 新章节（第{cn}章）
{chapter_text[:4000]}

如果有新的地点、规则、世界背景被引入或改变，请输出更新后的world-building.md完整内容。
如果没有变化，请输出 "NO_CHANGES"。"""

    if dry_run:
        return current

    result = call_claude(
        prompt,
        model=get_model(),
        max_tokens=4096,
        temperature=0.3,
    )

    if result.strip() == "NO_CHANGES":
        return current

    _write_bible_file("world-building.md", result)
    return result

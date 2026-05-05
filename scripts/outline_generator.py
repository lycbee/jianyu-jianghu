"""Auto-generate chapter outlines at milestones.

- Every 10 chapters: generate detailed outlines for the next 10 chapters
- Act transitions (ch 30, 70): deep review + next act planning
"""

import os
import re
from pathlib import Path

from api_client import call_claude
from context_builder import _chinese_num, _read_file, _parse_yaml_frontmatter

STORY_BIBLE_DIR = Path(__file__).resolve().parent.parent / "story-bible"
CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "chapters"


def _get_latest_chapters(count: int = 5) -> str:
    """Get summaries of the most recent N chapters."""
    summaries = _read_file(STORY_BIBLE_DIR / "chapter-summaries.md")
    if not summaries:
        return ""
    return summaries[-4000:] if len(summaries) > 4000 else summaries


def generate_next_outlines(start_chapter: int, count: int = 10,
                            dry_run: bool = False) -> str:
    """Generate detailed outlines for the next batch of chapters.

    Args:
        start_chapter: First chapter to plan (e.g., 11 for chapters 11-20)
        count: How many chapters to plan (default 10)
        dry_run: If True, only print prompt, no API call.

    Returns:
        The generated outline text in Markdown format.
    """
    end = start_chapter + count - 1
    print(f"\n  生成第{start_chapter}-{end}章逐章大纲...")

    # Gather context
    plot_tracker = _read_file(STORY_BIBLE_DIR / "plot-tracker.md")
    characters = _read_file(STORY_BIBLE_DIR / "characters.md")
    current_outline = _read_file(STORY_BIBLE_DIR / "outline.md")
    chapter_summaries = _get_latest_chapters(5)

    # Get recent chapter content for continuity
    recent_chapters = sorted(CHAPTERS_DIR.glob("chapter-*.md"))[-3:]
    recent_text = ""
    for f in recent_chapters:
        text = f.read_text(encoding="utf-8")
        if "---" in text:
            text = text.split("---", 2)[-1]
        recent_text += text[:2000] + "\n\n---\n\n"

    prompt = f"""你是一位小说大纲规划师。请为《剑雨江湖》续写详细章节大纲。

## 当前情节追踪器
{plot_tracker}

## 角色档案
{characters}

## 现有大纲
{current_outline[-5000:] if len(current_outline) > 5000 else current_outline}

## 最近章节摘要
{chapter_summaries}

## 最近章节原文（结尾部分）
{recent_text[-4000:]}

---

请为第{start_chapter}章到第{end}章生成逐章详细大纲。每章格式如下：

### 第{_chinese_num(start_chapter)}章

- POV角色:
- 主要地点:
- 场景目标（本章POV角色想要什么）:
- 关键事件（3-5条）:
  1.
  2.
  3.
- 出场角色:
- 情感弧线（开始 → 结束）:
- 章末钩子:
- 伏笔要埋:

...（第{start_chapter+1}章到第{end}章，同样格式）

要求：
1. 严格遵循三幕结构和现有情节走向
2. 每个章节要有独立的场景目标和情感弧线
3. 章节之间要有因果链（前一章的钩子 → 下一章的展开）
4. 合理分配伏笔的"埋下"和"回收"
5. 紧张度要有起伏，避免连续高强度或连续平淡
6. 直接输出大纲，不要任何额外说明"""

    if dry_run:
        print(f"  [DRY RUN] 将生成 {start_chapter}-{end} 章大纲")
        return ""

    result = call_claude(
        prompt,
        model=os.getenv("EDITOR_MODEL", "deepseek-chat"),
        max_tokens=8192,
        temperature=0.5,
    )
    return result.strip()


def append_outlines_to_file(outlines_text: str) -> None:
    """Append generated outlines to outline.md."""
    current = _read_file(STORY_BIBLE_DIR / "outline.md")
    if not current:
        current = "---\nname: outline\ndescription: 全书大纲与逐章详细计划\n---\n\n# 全书大纲\n"

    new_content = current.rstrip() + "\n\n" + outlines_text + "\n"
    path = STORY_BIBLE_DIR / "outline.md"
    path.write_text(new_content, encoding="utf-8")
    print(f"  已更新 outline.md")


def review_act(next_act: int, dry_run: bool = False) -> str:
    """Deep review of current act and plan the next act.

    Args:
        next_act: The act number that's about to begin (2 or 3)
        dry_run: If True, only print prompt.
    """
    act_name = {2: "第二幕：江湖风雨（第31-70章）", 3: "第三幕：剑问天下（第71-100章）"}
    name = act_name.get(next_act, f"第{next_act}幕")
    print(f"\n📖 幕结束 — 深度回顾与{name}规划...")

    plot_tracker = _read_file(STORY_BIBLE_DIR / "plot-tracker.md")
    chapter_summaries = _read_file(STORY_BIBLE_DIR / "chapter-summaries.md")
    current_outline = _read_file(STORY_BIBLE_DIR / "outline.md")

    prompt = f"""你是一位小说总编。请对《剑雨江湖》当前阶段做深度回顾，并为下一幕做详细规划。

## 情节追踪器
{plot_tracker}

## 所有章节摘要
{chapter_summaries}

## 现有大纲
{current_outline}

---

请完成以下任务：

1. **当前幕回顾**（200字内）：当前幕写得如何？有哪些亮点和需要改进的地方？

2. **角色状态评估**：主要角色目前的状态是否合理？角色弧线是否需要调整？

3. **伏笔审计**：还有哪些重要伏笔未回收？是否需要调整回收时机？

4. **下一幕详细规划**：更新 plot-tracker.md 中下一幕的关键节点，并输出更新后的完整三幕结构部分。

请以 Markdown 格式输出，可以直接粘贴到相关文件。"""

    if dry_run:
        print(f"  [DRY RUN] 将进行第{next_act}幕回顾与规划")
        return ""

    result = call_claude(
        prompt,
        model=os.getenv("EDITOR_MODEL", "deepseek-chat"),
        max_tokens=8192,
        temperature=0.5,
    )
    return result.strip()

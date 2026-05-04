"""Call Claude API to generate a chapter draft."""

import os
from pathlib import Path

from api_client import call_claude
from context_builder import build_context, build_writer_prompt, _chinese_num

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "chapters"
DRAFTS_DIR = Path(__file__).resolve().parent.parent / "drafts"


def get_model() -> str:
    return os.getenv("WRITER_MODEL", "claude-opus-4-7")


def write_chapter(chapter_num: int | None = None, dry_run: bool = False) -> str:
    """Generate a single chapter draft."""
    context = build_context(chapter_num)
    prompt = build_writer_prompt(context)
    num = context["chapter_num"]
    cn = _chinese_num(num)

    if dry_run:
        print(f"[DRY RUN] Would generate chapter {num}")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Outline: {context['chapter_outline'][:200]}...")
        return f"## 第{cn}章\n\n(DRY RUN — no API call made)\n\n"

    chapter_text = call_claude(
        prompt,
        system="你是一位经验丰富的中文小说作家，擅长创作引人入胜的连载小说。你的写作风格生动、细腻，注重人物心理刻画和情节推进。",
        model=get_model(),
        max_tokens=4096,
        temperature=0.85,
    )

    # Save draft
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    draft_path = DRAFTS_DIR / f"chapter-{num:03d}.md"
    draft_path.write_text(chapter_text, encoding="utf-8")

    return chapter_text

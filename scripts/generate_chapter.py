#!/usr/bin/env python3
"""Main orchestrator — run the full daily novel generation pipeline.

Usage:
    python3 scripts/generate_chapter.py [--dry-run] [--chapters N] [--no-deploy]

The script generates N chapters (default: 8), each going through:
write → edit → finalize → update story bible.
After all chapters are done, it builds the static site.

Zero external dependencies — uses only Python standard library.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv() -> None:
    """Minimal .env loader — no external dependencies."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


# Load .env before importing modules that read from os.environ
load_dotenv()

from context_builder import get_next_chapter_number
from chapter_writer import write_chapter
from chapter_editor import edit_chapter, finalize_chapter, generate_title
from bible_updater import update_all
from outline_generator import generate_next_outlines, append_outlines_to_file, review_act
from site_builder import build


def generate_one_chapter(dry_run: bool = False) -> tuple[int, str]:
    """Generate, edit, and finalize a single chapter.

    Returns (chapter_num, title_or_summary).
    """
    num = get_next_chapter_number()
    print(f"\n{'='*60}")
    print(f"开始生成第{num}章")
    print(f"{'='*60}")

    # Step 1: Write draft
    print(f"[{num}] 写作初稿...")
    draft = write_chapter(num, dry_run=dry_run)
    print(f"  初稿: {len(draft)} 字")

    # Step 2: Editor review
    print(f"[{num}] 编辑审校...")
    edited = edit_chapter(draft, num, dry_run=dry_run)
    print(f"  定稿: {len(edited)} 字")

    # Step 2.5: Generate title
    print(f"[{num}] 生成标题...")
    title = generate_title(edited, num, dry_run=dry_run)
    print(f"  标题: {title}")

    # Step 3: Finalize and save
    print(f"[{num}] 保存章节...")
    finalized_path = finalize_chapter(edited, num, title=title)
    print(f"  已保存: {finalized_path}")

    # Step 4: Update Story Bible
    print(f"[{num}] 更新故事圣经...")
    updates = update_all(edited, num, dry_run=dry_run)
    for fname in updates:
        print(f"  已更新: {fname}")

    return num, title


def main():
    parser = argparse.ArgumentParser(description="剑雨江湖 — 每日自动写作流水线")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="试运行，不调用 API"
    )
    parser.add_argument(
        "--chapters", type=int, default=8,
        help="生成章节数（默认：8）"
    )
    parser.add_argument(
        "--no-deploy", action="store_true",
        help="跳过 Vercel 部署触发"
    )
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        print("错误: 未设置 ANTHROPIC_API_KEY。请在 .env 文件中设置，或使用 --dry-run 测试。")
        sys.exit(1)

    start_time = datetime.now()
    print(f"=== 剑雨江湖 — 每日自动写作 ===")
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"计划生成: {args.chapters} 章")
    print(f"试运行模式: {'是' if args.dry_run else '否'}")

    results = []
    for i in range(args.chapters):
        try:
            num, title = generate_one_chapter(dry_run=args.dry_run)
            results.append((num, title))
        except Exception as e:
            print(f"\n生成章节时出错: {e}")
            continue

    # Step 5: Check milestones — auto-generate outlines if needed
    if results:
        last_chapter = max(r[0] for r in results)

        # Every 10 chapters: generate next 10-chapter outlines
        if last_chapter % 10 == 0:
            print(f"\n{'='*60}")
            print(f"🎯 第{last_chapter}章里程碑 — 自动生成下10章大纲")
            print(f"{'='*60}")
            try:
                outlines = generate_next_outlines(last_chapter + 1, 10, dry_run=args.dry_run)
                if outlines:
                    append_outlines_to_file(outlines)
            except Exception as e:
                print(f"  大纲生成失败: {e}")

        # Act transitions: deep review
        if last_chapter in [30, 70]:
            next_act = 2 if last_chapter == 30 else 3
            print(f"\n{'='*60}")
            print(f"📖 第{last_chapter}章幕结束 — 深度回顾与规划")
            print(f"{'='*60}")
            try:
                review = review_act(next_act, dry_run=args.dry_run)
                if review:
                    print(f"\n{'='*60}")
                    print("回顾与规划报告:")
                    print(f"{'='*60}")
                    print(review[:2000])
            except Exception as e:
                print(f"  幕回顾失败: {e}")

    # Step 6: Build site
    print(f"\n{'='*60}")
    print("构建静态站点...")
    print(f"{'='*60}")
    build(trigger_deploy=not args.no_deploy and not args.dry_run)

    end_time = datetime.now()
    elapsed = end_time - start_time
    print(f"\n=== 流水线完成 ===")
    print(f"成功生成: {len(results)}/{args.chapters} 章")
    for num, title in results:
        print(f"  第{num}章: {title}")
    print(f"耗时: {elapsed}")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

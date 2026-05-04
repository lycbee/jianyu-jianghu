# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

剑雨江湖 — AI 驱动的每日自动写作与发布系统。
- 每日定时生成连载小说章节（约 2500 字/章）
- Story Bible 分层记忆架构，维持长篇写作一致性
- DeepSeek API（写作 + 编辑双模型）
- 零外部依赖（Python 标准库），自动部署到 GitHub Pages
- 站点地址：https://lycbee.github.io/jianyu-jianghu/
- 始终使用中文回复

## Environment

- Linux (6.17.0-22-generic)
- Shell: bash
- API 密钥：复制 `.env.example` 为 `.env`，填入 `ANTHROPIC_API_KEY`（实际对接 DeepSeek API）
- 网络代理：本机通过代理访问外网，端口 `7897`。涉及 GitHub 操作需先设置：
  ```bash
  export https_proxy=http://127.0.0.1:7897
  ```

## Architecture

```
story-bible/          # 故事记忆系统（角色/世界观/大纲/伏笔/风格）
scripts/              # 核心流水线
  generate_chapter.py # 主编排器（写→编→取标题→更新圣经→构建站点）
  context_builder.py  # 上下文组装（从圣经中提取相关切片注入prompt）
  api_client.py       # 多Provider API客户端（Anthropic/DeepSeek自动检测）
  chapter_writer.py   # 调用API写作（temp 0.85）
  chapter_editor.py   # 调用API审校（temp 0.3）
  bible_updater.py    # 更新故事圣经（记忆沉淀步骤）
  build_site.py       # 生成静态HTML站点（零依赖）
  site_builder.py     # 站点构建+部署触发
chapters/             # 最终发布的章节（Markdown + Hugo frontmatter）
drafts/               # 初稿（不提交git）
docs/                 # 生成的静态站点（GitHub Pages 部署目录）
site/                 # Hugo 站点配置（备用）
.github/workflows/    # GitHub Actions 每日定时任务
```

## Commands

### 生成章节并发布
```bash
python3 scripts/generate_chapter.py --chapters 1          # 生成1章（含：写作→审校→取标题→更新圣经→构建站点）
python3 scripts/generate_chapter.py --chapters 8          # 生成8章（每日默认量）
python3 scripts/generate_chapter.py --dry-run --chapters 1 # 试运行，不调API
# 生成后手动推送：
git add -A && git commit -m "第X章 · 标题" && git push
```
推送前需设置代理：`export https_proxy=http://127.0.0.1:7897`

### 仅重建站点（不生成新章节）
```bash
python3 scripts/build_site.py    # 重新生成 docs/ 下的 HTML
```

### 流水线步骤
写作（temp 0.85）→ 编辑审校（temp 0.3）→ 取标题（2-6字）→ 保存章节 → 更新故事圣经 → 构建站点

## Gotchas

- **API 是 DeepSeek 不是 Anthropic**：环境变量名是 `ANTHROPIC_API_KEY`，但密钥前缀非 `sk-ant` 时自动切换为 DeepSeek 接口。
- **GitHub Pages 只支持 `/docs`**：静态 HTML 输出到 `docs/` 目录。
- **章节目录为正序**：旧章在上，新章在下（build_site.py 不使用 reversed）。
- **`.env` 和 `.claude/settings.local.json` 不得提交**：gitignore 已配置。
- **生成后检查章节末尾**：偶有编辑附加的"修订说明"需手动删除。
- **Story Bible 质量决定输出质量**：角色、大纲、风格指南为空时不可生成。
- **git push 需要代理 `7897`**：本机直连 GitHub 不通。
- **GitHub Pages 部署有约 1 分钟延迟**：推送后稍等再刷新。

## Skill Usage Conventions

Always invoke the relevant skill before these categories of work.

| 场景 | 使用技能 |
|------|----------|
| 写 HTML/CSS/UI | `frontend-design` |
| 代码审查/质量 | `simplify`（改后）、`security-review`（合并前） |
| PR 审查 | `review` 或 `pr-review-toolkit:review-pr` |
| Git 提交 | `commit-commands:commit` |
| 提交+推送+PR | `commit-commands:commit-push-pr` |
| 修改 settings.json | `update-config` |
| 减少权限提示 | `fewer-permission-prompts` |
| 更新 CLAUDE.md | `claude-md-management:claude-md-improver` |
| 复杂功能开发 | `feature-dev` |
| 定时/循环任务 | `loop` |
| 自动行为钩子 | `hookify:hookify` |
| Anthropic SDK/API | `claude-api`（本项目用 DeepSeek，通常跳过） |

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

剑雨江湖 — AI 驱动的仙侠连载小说，全书 115 章，已于 2026-05-19 完结。
- Story Bible 分层记忆架构，维持长篇写作一致性
- DeepSeek API（写作 + 编辑双模型），零外部依赖（Python 标准库）
- 静态站点部署到 GitHub Pages
- 站点地址：https://lycbee.github.io/jianyu-jianghu/
- 始终使用中文回复

## Environment

- Shell: bash
- API 密钥：复制 `.env.example` 为 `.env`，填入 `ANTHROPIC_API_KEY`（实际对接 DeepSeek API）
- 网络代理：本机通过代理访问外网，端口 `7897`。Git 操作需代理：
  ```bash
  export https_proxy=http://127.0.0.1:7897
  ```

## Architecture

```
story-bible/          # 故事记忆系统（角色/世界观/大纲/伏笔/风格）
scripts/              # 核心流水线
  generate_chapter.py # 主编排器（写→编→取标题→更新圣经→构建站点→里程碑检测）
  outline_generator.py # 自动大纲生成（每10章更新下10章大纲，每30/70章幕回顾）
  context_builder.py  # 上下文组装（从圣经中提取相关切片注入prompt）
  api_client.py       # 多Provider API客户端（Anthropic/DeepSeek自动检测）
  chapter_writer.py   # 调用API写作（temp 0.85）
  chapter_editor.py   # 调用API审校（temp 0.3）
  bible_updater.py    # 更新故事圣经（记忆沉淀步骤）
  build_site.py       # 生成静态HTML站点（零依赖）
  site_builder.py     # 站点构建封装 + Vercel 部署触发（未使用）
chapters/             # 最终发布的章节（Markdown + Hugo frontmatter）
drafts/               # 初稿（不提交git）
docs/                 # 生成的静态站点（GitHub Pages 部署目录）
.github/workflows/    # GitHub Actions（仅手动触发，定时已取消）
```

## Commands

### 重建站点（不生成新章节）
```bash
python3 scripts/build_site.py    # 重新生成 docs/ 下的 HTML
```

### 生成章节（仅用于调试/补写，全书已完结）
```bash
python3 scripts/generate_chapter.py --dry-run --chapters 1 # 试运行，不调API
python3 scripts/generate_chapter.py --chapters 1           # 生成1章（超过115章自动停止）
```
推送前需设置代理：`export https_proxy=http://127.0.0.1:7897`

### 流水线步骤
写作（temp 0.85）→ 编辑审校（temp 0.3）→ 取标题（2-6字）→ 保存章节 → 更新故事圣经 → 构建站点 → 里程碑检测（10/20/30章边界自动触发大纲生成，30/70章幕回顾）

## Gotchas

- **API 是 DeepSeek 不是 Anthropic**：环境变量名是 `ANTHROPIC_API_KEY`，但密钥前缀非 `sk-ant` 时自动切换为 DeepSeek 接口。
- **GitHub Pages 只支持 `/docs`**：静态 HTML 输出到 `docs/` 目录。站点构建用 `build_site.py`，不要用旧的 Hugo `site/` 目录（已删除）。
- **章节目录为正序**：旧章在上，新章在下（build_site.py 不使用 reversed）。
- **`.env` 和 `.claude/settings.local.json` 不得提交**：gitignore 已配置。`drafts/` 和 `__pycache__/` 也已排除。
- **Story Bible 质量决定输出质量**：角色、大纲、风格指南为空时不可生成。
- **大纲必须包含桥接指令**：手工大纲和自动生成的大纲每章开头都必须有 `**桥接上一章**` 段，描述如何从上一章结尾场景直接衔接。`outline_generator.py` 已优化为强制要求此字段，且注入最近章节的结尾钩子作为显式提醒。
- **Bible 输出会被 API 污染**：API 返回的 bible 内容可能被 ```markdown 包装或附带前言（"好的，根据..."等），`bible_updater._clean_api_output()` 自动清理。
- **标题自动去重已强化**：`generate_title()` 注入已有标题列表避免重复，且增加了硬检查——如果生成标题仍与已有标题冲突，强制重试一次。
- **git push 需要代理 `7897`**：本机直连 GitHub 不通。
- **GitHub Pages 部署有约 1 分钟延迟**：推送后稍等再刷新。
- **重大改动后更新 README**：对项目结构、机制、命令有改动时，同步更新 README.md。
- **MAX_CHAPTERS = 115（`context_builder.py`）**：全书共 115 章。`generate_chapter.py` 在循环前和每次迭代时检查章号，超过则自动停止。`outline_generator.py` 在里程碑触发时不会生成超过 115 章的大纲。GitHub Actions workflow 在达到 115 章后跳过生成。
- **完结检测（`build_site.py`）**：`_is_completed()` 同时检查 outline.md 中是否有 `**全书完**` 标记和实际章节数是否 >= MAX_CHAPTERS。完结后首页显示"已完结"，页脚改为"全书完 · AI 辅助创作"，最终章页面添加完结标记。

## Skill Usage Conventions

| 场景 | 使用技能 |
|------|----------|
| Git 提交 | `commit-commands:commit` |
| 更新 CLAUDE.md | `claude-md-management:claude-md-improver` |

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

- Shell: bash
- API 密钥：复制 `.env.example` 为 `.env`，填入 `ANTHROPIC_API_KEY`（实际对接 DeepSeek API）
- 网络代理：本机通过代理访问外网，端口 `7897`。API 调用和 Git 操作均需代理：
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
  site_builder.py     # 站点构建封装 + Vercel 部署触发
chapters/             # 最终发布的章节（Markdown + Hugo frontmatter）
drafts/               # 初稿（不提交git）
docs/                 # 生成的静态站点（GitHub Pages 部署目录）
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

### 手动触发 GitHub Actions
`gh` CLI 未安装，需用 curl 调用 API（token 从 `git remote -v` 中提取）：
```bash
TOKEN="ghp_xxx"  # 从 git remote get-url origin 中提取
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/lycbee/jianyu-jianghu/actions/workflows/daily-write.yml/dispatches \
  -d '{"ref":"main"}'
# 检查状态：
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/lycbee/jianyu-jianghu/actions/runs?per_page=1
```

### 流水线步骤
写作（temp 0.85）→ 编辑审校（temp 0.3）→ 取标题（2-6字）→ 保存章节 → 更新故事圣经 → 构建站点 → 里程碑检测（10/20/30章边界自动触发大纲生成，30/70章幕回顾）

## Gotchas

- **API 是 DeepSeek 不是 Anthropic**：环境变量名是 `ANTHROPIC_API_KEY`，但密钥前缀非 `sk-ant` 时自动切换为 DeepSeek 接口。
- **GitHub Pages 只支持 `/docs`**：静态 HTML 输出到 `docs/` 目录。站点构建用 `build_site.py`，不要用旧的 Hugo `site/` 目录（已删除）。
- **章节目录为正序**：旧章在上，新章在下（build_site.py 不使用 reversed）。
- **`.env` 和 `.claude/settings.local.json` 不得提交**：gitignore 已配置。`drafts/` 和 `__pycache__/` 也已排除。
- **生成后检查章节末尾**：偶有编辑附加的"修订说明"需手动删除。
- **Story Bible 质量决定输出质量**：角色、大纲、风格指南为空时不可生成。
- **大纲分层管理**：第1-10章为手工大纲，第11章起由里程碑自动生成（每10章一批）。生成后需抽查大纲质量，尤其是与已写内容的连贯性。
- **大纲必须包含桥接指令**：手工大纲中每章开头必须有 `**桥接上一章**` 段，描述如何从上一章结尾场景直接衔接。这是防止章节间跳跃断裂的核心机制。
- **context_builder.py 的连续性注入**：`get_previous_chapter_ending()` 提取上一章最后500字，`get_previous_chapter_hook()` 提取上一章的章末钩子，两者均注入到写入器 prompt 中。写入器被明确要求"章节开头必须直接承接前一章结尾的场景"。
- **里程碑检测扫描批次**：不在只检查 `last_chapter`，而是遍历批次中所有章节号，避免跳批时遗漏。第10/20/30章触发大纲生成，第30/70章额外触发幕回顾。
- **Bible 输出会被 API 污染**：API 返回的 bible 内容可能被 ```markdown 包装或附带前言（"好的，根据..."等），`bible_updater._clean_api_output()` 自动清理。
- **标题自动去重已强化**：`generate_title()` 注入已有标题列表避免重复，且增加了硬检查——如果生成标题仍与已有标题冲突，强制重试一次。
- **git push 需要代理 `7897`**：本机直连 GitHub 不通。
- **GitHub Pages 部署有约 1 分钟延迟**：推送后稍等再刷新。
- **重大改动后更新 README**：对项目结构、机制、命令有改动时，同步更新 README.md。

## Skill Usage Conventions

| 场景 | 使用技能 |
|------|----------|
| 写 HTML/CSS/UI | `frontend-design` |
| 代码审查/质量 | `simplify`（改后）、`security-review`（合并前） |
| Git 提交 | `commit-commands:commit` |
| 提交+推送+PR | `commit-commands:commit-push-pr` |
| 修改 settings.json | `update-config` |
| 更新 CLAUDE.md | `claude-md-management:claude-md-improver` |
| 复杂功能开发 | `feature-dev` |
| 定时/循环任务 | `loop` |

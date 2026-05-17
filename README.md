# 剑雨江湖

AI 驱动的每日自动写作与发布系统 —— 长篇仙侠连载小说，零外部依赖。

**阅读地址**：[lycbee.github.io/jianyu-jianghu](https://lycbee.github.io/jianyu-jianghu/)

## 核心机制

- **每日自动生成**：定时生成连载章节（约 2500 字/章），写作模型（temp 0.85）+ 编辑模型（temp 0.3）双模型协作
- **全书 115 章**：三幕结构（1-30 困兽之斗 / 31-70 问剑天下 / 71-115 剑雨终章），到达 115 章后自动停止
- **Story Bible 分层记忆**：角色档案、逐章大纲、情节追踪、伏笔管理——维持长篇写作一致性
- **章间连续性保障**：桥接指令 + 上章结尾注入 + 章末钩子回收，确保每章开头直接承接上章结尾场景
- **自动大纲滚动更新**：每 10 章生成下 10 章大纲（不超过 115），每 30/70 章进行幕回顾与深度规划
- **完结自动检测**：`outline.md` 含 `**全书完**` 标记且章节数达到 115 时，站点自动切换为完结状态
- **零外部依赖**：纯 Python 标准库，API 调用使用 `urllib.request`
- **自动部署**：生成后构建静态 HTML → GitHub Pages，全程自动化

## 项目结构

```
story-bible/          # 故事记忆系统（角色/世界观/大纲/伏笔/风格）
scripts/              # 核心流水线
  generate_chapter.py # 主编排器（写→编→取标题→更新圣经→构建站点→里程碑检测）
  outline_generator.py # 自动大纲生成
  context_builder.py  # 上下文组装（从圣经中提取切片注入 prompt）
  api_client.py       # 多 Provider API 客户端（Anthropic/DeepSeek 自动检测）
  chapter_writer.py   # 调用 API 写作
  chapter_editor.py   # 调用 API 审校
  bible_updater.py    # 更新故事圣经（记忆沉淀）
  build_site.py       # 生成静态 HTML 站点
  site_builder.py     # 站点构建 + 部署触发
chapters/             # 最终发布的章节（Markdown）
docs/                 # 生成的静态站点（GitHub Pages 部署目录）
.github/workflows/    # GitHub Actions 每日定时任务
```

## 快速开始

```bash
# 1. 配置 API 密钥
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY（对接 DeepSeek API）

# 2. 设置代理（如需）
export https_proxy=http://127.0.0.1:7897

# 3. 生成章节
python3 scripts/generate_chapter.py --chapters 1    # 生成 1 章
python3 scripts/generate_chapter.py --chapters 8    # 生成 8 章（每日默认）
python3 scripts/generate_chapter.py --dry-run --chapters 1  # 试运行

# 4. 仅重建站点
python3 scripts/build_site.py

# 5. 推送到 GitHub Pages
git push
```

## 流水线步骤

```
写作（temp 0.85）→ 编辑审校（temp 0.3）→ 取标题（2-6 字）
→ 保存章节 → 更新故事圣经 → 构建站点
→ 里程碑检测（10/20/30 章边界自动生成大纲，30/70 章幕回顾）
```

## 技术说明

- **API**：环境变量名为 `ANTHROPIC_API_KEY`，根据密钥前缀自动切换 Anthropic / DeepSeek 接口
- **站点**：静态 HTML 输出到 `docs/` 目录（GitHub Pages 要求）
- **密钥安全**：`.env` 和 `.claude/settings.local.json` 已在 `.gitignore` 中排除
- **章节上限**：`context_builder.py` 中 `MAX_CHAPTERS = 115`，`generate_chapter.py` 在循环前后双重检查，到达上限自动停止
- **完结状态**：大纲末尾有 `**全书完**` 标记。`build_site.py` 同时检查标记和实际章节数，完结后首页显示"已完结"、页脚改为"全书完 · AI 辅助创作"、最终章页面添加完结标记
- **CI 节省**：GitHub Actions 在章节数 >= 115 时跳过生成步骤，避免空跑 API 费用

# 知识库（含技能库）整理工作流

> 来自 2026-06-15 实际执行经验。每次月度知识库整理按此流程执行。

## 前置条件

- Obsidian vault 已按 llm-wiki 中文架构组织（架构.md/首页.md/日志.md/概念/实体/比较/原始资料）
- gbrain 已安装，GPU 嵌入服务器可用
- git repo 已在 vault 根目录初始化

## 完整步骤

### Step 0 — 加载技能

先加载 llm-wiki.skill 和 gbrain-memory-hub 获取最新指令。

### Step 1 — 定位与定向

读 架构.md（确认领域约定和标签体系）、首页.md（了解已有页面和索引结构）、日志.md（最近 20-30 行了解近期活动）。

检查目标目录现状：概念/、比较/、技能库/

### Step 2 — 对比 Hermes 技能集与 vault 现状

列出 Hermes 已安装技能（ls ~/AppData/Local/hermes/skills/*/），与 Obsidian vault 中已有的评估页对比，找出缺失评估的新技能和未记录的对比。

### Step 3 — 创建/更新技能评估页

每页放 `概念/技能评估-<name>.md`，含：
- frontmatter（title/created/updated/type/tags/sources/confidence）
- 基本信息（分类/darwin-skill评分/评估日期）
- 功能摘要
- 使用场景
- 评估结论（✅/🟡/🔴）
- 依赖与关系（depends_on/composes_with/similar_to）
- 优化历史（时间线）

### Step 4 — 创建技能对比页

当两个技能标记了 similar_to（SkillDAG 边类型），在 比较/ 下创建对比分析，使用表格对比多维度。

### Step 5 — 更新首页.md

两处修改：
1. 跨领域目录表的页面数（根概念/比较/等）
2. 跨领域笔记一览段落添加新页面的 wikilink + 摘要

### Step 6 — 追加日志.md

标准格式：
```
## [YYYY-MM-DD] skill-curator | 技能知识库整理
- **新增评估**：<skill-name>（<score>分<grade>）→ 概念/技能评估-<name>.md
- **新增对比**：<skill-A> vs <skill-B> → 比较/<name>.md
- **更新首页**：首页.md → 技能评估索引 + 对比页入口
```

### Step 7 — git 提交

只 stage 新建/修改的知识页，不碰 vault 中其他未跟踪文件：
```bash
git add "概念/技能评估-*.md" "比较/*.md" 首页.md 日志.md
git commit -m "[YYYY-MM-DD] skill-curator：知识库整理"
```

### Step 8 — gbrain 同步

```bash
# 先确保 GPU 嵌入服务器启动
python D:/gbrain-ensure-server.py

# 同步 vault 变更
cd /f/gbrain
npx gbrain sync --repo "D:/Documents/Obsidian Vault"
```

**陷阱**：gbrain sync --repo 内部会尝试 git pull 并 fallback 到全量导入。如果 vault 的 git 有冲突未解决，sync 会全量 fallback。提前确保 working tree 干净。

### Step 9 — 验证

```bash
npx gbrain doctor | grep -E '^\s+\[(OK|WARN|FAIL)\]'
```

关注点：
- embeddings: 100% coverage（嵌入完整）
- sync_freshness: OK（同步最新）
- 核心全绿即可，graph/link 低分对纯知识库 vault 是正常的

### Step 10 — PDH 记录

在 skill-curator 的 decision_log/index.json 追加一条决策历史四元组（diagnosis/candidates/evidence/result），同时在 SKILL.md §最近决策历史 快照区追加 YAML 块。

## 常见陷阱

| 陷阱 | 避免方法 |
|------|---------|
| 技能评估页放错目录 | 跨领域 → 概念/；领域专属 → [领域]/概念/ |
| 忘记更新首页页面数 | 每次新增页面必须同步更新首页目录表 |
| git 提交附带不相关的未跟踪文件 | 显式 git add 只 add 新建/修改的知识文件 |
| gbrain sync 后忘记验证 | 至少 check 一次 stats，确认 pages/chunks 增长 |
| PDH 决策记录写一半 | 四元组（diagnosis/candidates/evidence/result）缺一不可 |
| 忘记 gbrain 需要 GPU 服务器 | 先跑 python D:/gbrain-ensure-server.py |

# 三层记忆架构（Three-Tier Memory Architecture）

## 概述

当 Hermes Agent 需要进行知识库（含技能库）维护时，使用一套三层架构来实现持久化记忆与语义检索的结合。该架构由 Obsidian llm-wiki（结构化知识库）+ gbrain（本地 GPU 嵌入） + cron 定时管线组成。

## 架构分层

| 层级 | 组件 | 职责 | 频率 |
|------|------|------|------|
| **T1** | Obsidian llm-wiki | 结构化知识持久化：概念笔记、技能评估、对比分析 | 按需（手动） |
| **T2** | gbrain (本地 GPU) | 语义嵌入 + 向量检索，支持跨笔记的模糊语义查询 | 每6h增量同步 |
| **T3** | cron 管线 | 自动化同步、去重、老化提醒 | 定时 + llm-wiki.skill |

## T1：Obsidian llm-wiki（结构化知识库）

基于 llm-wiki 中文架构，Vault 目录结构：

```
Obsidian Vault/
├── 架构.md           # Schema 定义
├── 首页.md           # 入口索引
├── 日志.md           # 操作记录
├── 实体/             # 实体笔记（人物、项目、工具）
├── 概念/             # 概念笔记（含技能评估）
├── 比较/             # 双主体对比分析
├── 查询存档/         # 查询历史
└── 原始资料/         # 外部源材料
```

技能评估笔记命名规范：`概念/技能评估-<skill-name>.md`

评分等级：
- 🟢 优秀（≥80 分）
- 🟡 一般（60–79 分）
- 🔴 待改进（<60 分）

评估维度：完整性、可用性、一致性、文档质量、维护性

## T2：gbrain（本地 GPU 语义嵌入）

- **嵌入模型**：bge-small-zh-v1.5（512 维，中文优化）
- **运行模式**：本地 GPU 服务（端口 18081），按需启动不常驻
- **启动命令**：`python D:/gbrain-ensure-server.py`
- **数据规模参考**：~1,575 pages / ~6,043 chunks（2026-06-15 实测）
- **同步命令**：`npx gbrain sync --repo "D:/Documents/Obsidian Vault"`
- **健康检查**：`npx gbrain doctor`

嵌入服务仅在维护操作前启动，完成后不主动关闭（由用户或后续 pipeline 决定）。

## T3：cron 自动化管线

```yaml
- gbrain 同步:    每6小时   增量同步 Obsidian → gbrain
- SkillDAG 周审:  每周      审计技能依赖图
- 选题池维护:     每周      选题老化提醒 + P0 推荐
- gbrain 版本检查: 每7天     gbrain 版本更新通知
```

## 知识库整理流程

1. 加载 `llm-wiki.skill` 确认架构规范
2. 识别需要维护的技能：评分偏低（🟡/🔴）、长期未更新、依赖变化
3. 为每个技能编写概念笔记（`概念/技能评估-<name>.md`），含 ID 化、评分、评估细节
4. 新增对比笔记（`比较/<topic>.md`）记录技能间关系
5. 更新 `首页.md` 的页面统计和技能索引
6. 追加 `日志.md` 维护记录
7. 启动 gbrain 嵌入服务 → 增量同步 → 验证健康状态
8. 用 `decision_log/` 记录 PDH 决策四元组（诊断/候选/证据/结果）

## 关键命令速查

```bash
# 启动 GPU 嵌入服务
python D:/gbrain-ensure-server.py

# 健康检查
curl http://127.0.0.1:18081/health

# 同步 Vault
npx gbrain sync --repo "D:/Documents/Obsidian Vault"

# 查看统计
npx gbrain stats

# 全面健康检查
npx gbrain doctor
```

## 注意事项

- **gbrain 按需启动**：不要在未启动 GPU 服务时调用 `npx gbrain` 操作（会报服务不可用）
- **数据规模**：6K+ chunks 的嵌入约需 30–60 秒，RTX 5070 Ti 上无压力
- **版本兼容**：gbrain v0.35.8.0，嵌入模型保持 bge-small-zh-v1.5（512-dim）
- **同步后验证**：`npx gbrain stats` 检查 page/chunk 数是否合理增长，`npx gbrain doctor` 确认嵌入健康度

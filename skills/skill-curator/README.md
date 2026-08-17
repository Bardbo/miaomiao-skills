# Skill Curator · 技能管理与持续改进系统

<p align="center">
  <a href="#readme">🇨🇳 中文</a> · <a href="README_EN.md">🇬🇧 English</a>
</p>

> 综合技能管理与持续改进系统——整合 darwin-skill 9维评分 + 对照集最佳实践 + SkillDAG 自进化技能图谱 + **SkillHone 持久化决策历史** + **SGDR 状态锚定动态检索**。
>
> 基于腾讯两篇论文方法论（SkillHone arXiv:2606.08671 + SGDR arXiv:2606.04391）。

## 它能做什么

| 功能 | 说明 |
|------|------|
| **SKILL 全景仪表盘** | 统计安装数、健康评分、分类分布，一目了然 |
| **健康评估** | 用 darwin-skill 9维评分体系做基线评估，分级预警 |
| **优化管线** | 识别薄弱技能，从对照集汲取经验自动优化 |
| **生命周期管理** | 评估→优化→归档→淘汰全自动，定期清理比不断堆积更有价值 |
| **SkillDAG 技能图谱** | 5种边类型追踪技能关系，Agent 自主编辑进化 |
| **自动安装决策** | 发现高价值新技能 → 自主评估并安装 |
| **持久化决策历史 (PDH)** | 每次修改记录四元组（诊断/候选/证据/结果），避免重复试错 |
| **优化角色隔离** | 优化端与评估端权限分离，防止"背答案" |
| **定向回归修复** | 性能倒退时精准修补退化部分，保留有用编辑，不整段回滚 |
| **SGDR 动态检索** | 执行中每步按任务+状态双信号 + MMR 去重重新选择最优技能 |
| **知识库定期优化** | 使用 llm-wiki.skill 架构，定期审计技能知识库与结构维护 |

## 自动管理权限

用户已授权 skill-curator 自主决策：

- 发现高价值新技能 → 自主评估并安装到合适分类
- 发现对照集有更好方案 → 评估差异，优化现有或安装替代
- 定期跑基线评分 → 自动记录到 `evaluation.md`
- 使用中发现问题 → 即时优化修正
- 执行中发现技能间关系 → 自动编辑 SkillDAG 边
- 知识库（含技能库）定期使用 llm-wiki.skill 做结构审计与整理
- 用户只需看结果报告，无需逐一手动批准

## 使用方式

Skill Curator 是为 **Hermes Agent** 设计的 skill，加载即执行：

```bash
# 安装到 Hermes Agent
cp -r skill-curator ~/.hermes/skills/

# 在对话中触发
# 说：「技能管理」「skill管理」「技能盘点」「评估所有skill」
# 「优化哪些skill」「skill质量检查」「skill关系」「技能图谱」
# 「决策历史」「PDH」「角色隔离」「定向修复」「动态检索」「SGDR」
# 「知识库整理」「技能知识库」「llm-wiki」
```

## 依赖

| 组件 | 用途 |
|------|------|
| **darwin-skill** | 9维评分引擎 + 优化循环 |
| **meta-skill-orchestrator** | 工作流编排框架 |
| **huashu-nuwa** | 新技能蒸馏与创建 |
| **SkillDAG 论文** | 自进化技能图谱方法论 |
| **SkillHone 论文** | 持久化决策历史 + 角色隔离 + 定向修复 |
| **SGDR 论文** | 状态锚定动态检索 + MMR 去重 |
| **llm-wiki** | 知识库（含技能库）整理维护 |

## 项目结构

```
skill-curator/
├── SKILL.md                         # 技能定义与完整管线（v2.0.0）
├── README.md                        # 本文件
├── README_EN.md                     # English README
├── decision_log/
│   └── index.json                   # PDH 持久化决策历史索引
├── references/
│   ├── baseline-methodology.md      # 评估方法论与评分细则
│   ├── collection-evaluation.md     # 对照集评估报告
│   ├── knowledge-base-consolidation-workflow.md  # 知识库整理工作流
│   ├── skillhone-sgdr-notes.md      # SkillHone & SGDR 论文笔记
│   └── ppt-master-pipeline-notes.md # PPT 生成管线笔记
└── scripts/
    ├── dag_audit.py                 # SkillDAG 自动审计脚本（cron）
    ├── sync-skill-to-git.py         # Skill → Git 同步脚本
    └── gbrain-ensure-server.py      # gbrain GPU 嵌入服务管理
```

## 许可证

MIT

---

> 本项目由 [Hermes Agent](https://hermes-agent.nousresearch.com/) 辅助生成。
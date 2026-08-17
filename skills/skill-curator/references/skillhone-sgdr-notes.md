# SkillHone & SGDR 论文速查

> 腾讯系两篇 Skill 进化论文，2026-06-11。
> 已在 skill-curator v2.0.0 中实现（§9-§12）。

---

## SkillHone — 给技能进化装上记忆

**论文**：arXiv:2606.08671 — 《SkillHone: A Harness for Continual Agent Skill Evolution Through Persistent Decision History》

### 核心发现

1. **持久化决策历史（PDH）**：传统版本控制只记录文件变化，不记录为什么变。SkillHone 在每次修改时记录四元组——诊断、候选修订、评估证据、结果。后续优化时能查到"上次为什么改""什么方案被否了""评估怎么说的"。

2. **角色隔离**：优化 Agent 只看脱敏报告（数字和摘要），不能碰测试题和评分器；评估 Agent 跑测试但不能碰技能库。权限边界是结构性的（通过 task 派发），不靠提示词约束。Table 2 列出了 9 种子 Agent 派发模式。

3. **定向修复**：性能倒退时不是整段回滚，而是只修复出问题的那部分改动，保留其余有用编辑。Figure 3 显示从 30%→70% 的优化轨迹中有两次倒退都被定向修复回来。

### 实验结果

- 在用 Qwen3.6-35B-A3B（非顶级模型）时，GAIA 上达到 **64.6%**，超过配商业搜索的 deep-research agent 15.8 分
- WebWalkerQA-EN 上 **66.4%**，超过 3.2 分
- 比 Skill-Creator 高 **20.5 分**，比 Hermes-SE 高 **14.2 分**

---

## SGDR — 走到哪技能配到哪

**论文**：arXiv:2606.04391 — 《Online Skill Learning for Web Agents via State-Grounded Dynamic Retrieval》  
**GitHub**：https://github.com/plusnli/skill-dynamic-retrieval

### 核心发现

1. **双信号检索**：每次决策时重新检索，同时看任务目标 + 当前网页状态。
   `检索分数 = α × 任务相关性 + (1-α) × 状态相关性`
   消融实验确认 `α=0.5` 最优。

2. **滑动窗口提取**：从已完成的成功轨迹中抽取子技能，窗口长度 2-5 个动作。每个技能用**文本-代码对**表示：自然语言描述负责检索匹配，可执行代码负责直接调用。

3. **MMR 去重**：相邻窗口抽出的技能可能重复，用 MMR（λ=0.7）鼓励多样性。消融实验证实 MMR 比简单取 Top-M 更好。

### 实验结果

- WebArena 五个域上，GPT-4.1 backbone **37.5%** 平均成功率，相对最强基线 CER 提升 **10.6%**
- Qwen3-4B 也达到 **24.3%**，相对提升 **10.0%**
- 平均 **4.8 步**完成任务（Vanilla 要 6.0 步，CER 要 6.4 步）

---

## 与 skill-curator 的对应关系

| 论文机制 | skill-curator 实现 |
|---------|------------------|
| 持久化决策历史 | §9 PDH — `decision_log/` 目录 + 四元组记录格式 |
| 角色隔离 | §10 — delegate_task toolsets 限制 + 脱敏报告协议 |
| 定向修复 | §11 — 5种退化类型 + 行级/语义级修复策略 |
| 双信号检索 | §12.1-12.2 — `α=0.5` 任务+状态双信号伪代码 |
| MMR 去重 | §12.3 — λ=0.7 的 Top-10→Top-5 筛选 |
| 滑动窗口子技能 | §12.4 — 成功轨迹→`概念/执行模式/` 知识库 |

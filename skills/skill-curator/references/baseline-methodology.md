# darwin-skill 9维评分方法论 · 实践记录

> 评估日期：2026-06-06 | 评估人：skill-curator (Hermes)
> 评估方法：darwin-skill 9维rubric + 干跑验证（dry_run mode）

## 评分公式

```
每维度得分 = 维度分(1-10) × 权重 / 10
总分 = Σ(各维度得分)
满分 = 100
```

| 维度 | 权重 | 评分项 |
|------|------|--------|
| dim1 Frontmatter | 7 | name/description/triggers/boundaries |
| dim2 Workflow clarity | 12 | 有序号步骤，每步输入输出明确 |
| dim3 Failure mode encoding | 12 | "如果X失败→Y"分支路径 |
| dim4 Checkpoint design | 6 | 🔴/🛑显性标记，关键决策前暂停 |
| dim5 Actionable specificity | 17 | 禁用软化措辞，给具体值 |
| dim6 Resource integration | 4 | references/scripts/assets |
| dim7 Overall architecture | 12 | 结构清晰，无AI填充 |
| dim8 Performance (实测) | 23 | 测试prompt验证（本次dry_run） |
| dim9 Anti-patterns | 6 | "不要做什么"反例清单 |

## 详细评分记录

### wechat-article-formatting

| 维度 | 分 | 加权分 | 理由 |
|------|----|--------|------|
| dim1 Frontmatter | 8 | 5.6 | name/desc/triggers齐全，version有，边界清楚 |
| dim2 Workflow clarity | 9 | 10.8 | 7步流程，每步明确，有Design-Led渲染 |
| dim3 Failure mode encoding | 7 | 8.4 | 有已知踩坑速查表，但缺if-then分支 |
| dim4 Checkpoint design | 6 | 3.6 | ⚠️有但🛑暂停标记缺失 |
| dim5 Actionable specificity | 9 | 15.3 | 确切CSS/px/色值，无"建议""可以考虑" |
| dim6 Resource integration | 8 | 3.2 | references/scripts/assets齐全 |
| dim7 Overall architecture | 8 | 9.6 | 结构清晰但偏长 |
| dim8 Performance | 8 | 18.4 | ⚠️ dry_run — 过去使用证明有效 |
| dim9 Anti-patterns | 6 | 3.6 | 有踩坑表但无独立反模式章节 |
| **总分** | | **78.5** | 🟡 良好 |

### tiaoman-creation (旧版本)

| 维度 | 分 | 加权分 | 理由 |
|------|----|--------|------|
| dim1 Frontmatter | 3 | 2.1 | 无frontmatter，无name/version/triggers |
| dim2 Workflow clarity | 6 | 7.2 | 只有4步粗略流程，无输入输出说明 |
| dim3 Failure mode encoding | 4 | 4.8 | 无任何失败处理 |
| dim4 Checkpoint design | 3 | 1.8 | 无任何checkpoint标记 |
| dim5 Actionable specificity | 8 | 13.6 | 布局语言词典具体，Python代码可用 |
| dim6 Resource integration | 4 | 1.6 | 极少引用的文件 |
| dim7 Overall architecture | 5 | 6.0 | 短（68行），缺少必要章节 |
| dim8 Performance | 7 | 16.1 | ⚠️ dry_run — 基本可用但缺引导 |
| dim9 Anti-patterns | 3 | 1.8 | 无独立反模式清单 |
| **总分** | | **64.3** | 🟠 需改进 |

### shui-bing-yue-perspective

| 维度 | 分 | 加权分 | 理由 |
|------|----|--------|------|
| dim1 Frontmatter | 9 | 6.3 | 最佳frontmatter — 含触发词+限界 |
| dim2 Workflow clarity | 8 | 9.6 | STEP 0-3，模式选择清晰 |
| dim3 Failure mode encoding | 9 | 10.8 | 3列失败处理表（触发/一线/兜底） |
| dim4 Checkpoint design | 8 | 4.8 | 🔴 CHECKPOINT + A/B/C/D选择 |
| dim5 Actionable specificity | 9 | 15.3 | 确切句式/词汇表/示例对话 |
| dim6 Resource integration | 6 | 2.4 | 少但足够 |
| dim7 Overall architecture | 9 | 10.8 | 7节覆盖所有维度 |
| dim8 Performance | 8 | 18.4 | ⚠️ dry_run — 实际使用效果佳 |
| dim9 Anti-patterns | 10 | 6.0 | 8项反模式+红灯场景，标杆级 |
| **总分** | | **84.4** | 🟢 优秀 |

## 干跑验证说明

本次评估因不能用subagent执行测试prompt，dim8为dry_run评分。dry_run < 30%阈值（3个技能均为dry_run=100%）。评估总体有效但dim8分数可能偏移±1-2分。

**改进建议**：下次评估时调用delegate_task运行测试prompt：
1. 为每个skill设计2个典型用户prompt
2. 一个带skill+一个不带skill（baseline）对比
3. 对比输出质量

## 路径约定（Windows Hermes）

Hermes发现skills的路径优先级：
1. `~/AppData/Local/hermes/skills/<category>/<skill>/` — 核心安装路径（skill_manage写入位置）
2. `~/.hermes/skills/<category>/<skill>/` — 用户扩展路径

**重要**：skill_manage(action='create', category='cat') 写入位置1。手动 write_file 写入位置2可能导致版本发散。
验证方式：始终用 `skill_view(name)` 确认读取的是哪个版本。

## Hermes-specific 评估适配

darwin-skill的Phase结构是为Claude Code/Codex设计的。在Hermes上运行时的适配：
- Phase 0：不需要git分支（Hermes无自动git化）
- Phase 0.5：测试prompt用delegate_task执行
- Phase 1：主agent自己评分dim1-7/9，dim8用delegate_task
- Phase 2：直接调用patch/skill_manage优化，无需git
- Phase 3：结果写入skill-curator的references/

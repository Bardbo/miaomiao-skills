# Talk · 多角色对话模拟

<p align="center">
  <a href="#readme">🇨🇳 中文</a> · <a href="README_EN.md">🇬🇧 English</a>
</p>

> **⚠️ 测试版** — 此技能正在积极开发中，API 和行为可能发生变化。欢迎提交 Issue 和 PR。

## 概述

模拟 2 名或多名角色之间的沉浸式对话或讨论。Agent 按照本文档的步骤执行，不依赖 Python 状态机。支持角色人格检测、逐句生成、实时违规约束、第三方验证器检查。

本技能的设计参考了以下项目/技能的方法论：

- **[huashu-nuwa](https://github.com/Bardbo/miaomiao-skills)** — 技能蒸馏与创建框架。`talk` 的角色构建流程（本地技能 → 仓库搜索 → nuwa 蒸馏 → Fallback）直接继承自 nuwa 的源材料分析思路
- **[darwin-skill](https://github.com/Bardbo/miaomiao-skills)** — 9 维评分体系，用于持续评估对话神似度与质量改进
- **[skill-curator](https://github.com/Bardbo/miaomiao-skills)** — 综合技能管理系统，为 talk 提供了技能生命周期管理的参考
- **[openai-adapter / opencli](https://github.com/OpenInterpreter/open-interpreter)** — 工具调用的接口设计模式，影响了 talk 的 agent 驱动执行流程

## 核心原则

1. **SKILL.md 就是状态机** — Agent 读文档按步骤走，不靠 Python 代码推进流程
2. **Python 脚本只做 Agent 做不了的事** — 搜索本地技能、检测仓库、验证输出
3. **逐句生成** — 禁止一次性生成整段对话，每句调用一次
4. **违规事前约束 + 事后检查** — 生成时参照规则自我约束，生成后用脚本验证

## 功能

| 特性 | 说明 |
|------|------|
| **人格检测管线（4 级）** | Level 1 本地技能 → Level 2 仓库搜索 → Level 3 nuwa 蒸馏 → Level 4 Fallback 构建 |
| **逐句生成** | 每句一轮生成，Agent 自我约束避免旁白/叙事 |
| **实时违规约束** | 6.7 神似规则：本色过滤 / 距离感 / 禁止死亡自述 / 素材密度控制 / 文本密度控制 / 无动作描写禁言 |
| **第三方验证** | `dialogue_validator.py`：违规检测、节奏检查、角色覆盖度量 |
| **角色覆盖度量** | 统计每个角色的出场轮次，确保均衡覆盖 |
| **场景标题 + 免责声明** | 强制生成，保证对话完整性 |
| **强制检查项** | 生日/国籍/背景检查，防止事实性错误 |

## 文件结构

```
talk/
├── SKILL.md                           # 技能主文件（执行步骤 + 神似规则）
├── README.md                          # 本文件（中文）
├── README_EN.md                       # 英文 README
├── test-prompts.json                  # 测试用提示词
├── scripts/
│   ├── persona_detector.py            # 人格检测：搜索本地技能、仓库、构建 fallback
│   ├── dialogue_validator.py          # 对话验证：违规检测、节奏检查、全面验证
│   └── gen_dialogue.py                # 对话生成辅助脚本
├── references/
│   ├── expressive-dna-template.md     # 表达 DNA 模板（角色人格特征定义格式）
│   ├── hard-constraints-pattern.md    # 硬约束表模式（角色事实约束）
│   ├── persona-repos.md               # 人格仓库搜索配置
│   ├── einstein-fallback.md           # 爱因斯坦 Fallback 示例
│   ├── shizhongyuan-fallback.md       # 十日终焉角色 Fallback 示例
│   ├── chinese-novel-character-research.md  # 中文小说角色研究方法
│   ├── 神似示例-三人对话.md            # 神似对话示例（巴菲特/芒格/马斯克）
│   ├── 话题簇-桥接范例.md              # 话题桥接示例
```

## 快速开始

```bash
# 1. 在 Hermes Agent 中加载技能
skill_view(name='talk')

# 2. 按照 Step 0-4 执行
#    Step 0: 确认角色、场合、主题、长度
#    Step 1: 角色人格检测（4 级管线）
#    Step 2: 逐句生成
#    Step 3: 第三方验证
#    Step 4: 交付（含场景标题 + 免责声明）
```

## 依赖

- Python 3.9+
- Hermes Agent（需启用 `terminal` / `skill_view` / `delegate_task` 等工具）
- 可选：网络连接（用于仓库搜索和 nuwa 蒸馏）
- 可选：Baidu Baike、Bing 等角色资料源

## 已知问题 / 限制

1. **假阳性检测** — `dialogue_validator` 的正则模式可能将合法对话（如"你是说"、"小说"等）误判为旁白，目前已在 `_SAFE_VERB_PATTERNS` 中逐步补充豁免模式
2. **角色覆盖偏差** — 在自由对话中，主导型角色（如齐夏）的轮次数可能超出配角，验证器目前只统计不限制
3. **Fallback 构建依赖搜索** — 对于冷门角色，需依赖网络搜索或用户提供的原稿，无法自动生成
4. **中文语境限制** — 验证器主要面向中文对话，英文对话的假阳性率可能更高
5. **Agent 指令谬误** — 逐句生成模式增加了对话轮次，但偶有 Agent 跳过步骤直接输出整段，需要人工审查

## 许可

MIT — 可自由使用、修改和分发。保留原始署名即可。
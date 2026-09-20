# 📝 jev-survey-simulation

> **基于 TypeSafe jev 决策模型的问卷批量模拟填写技能——按目标人群画像批量生成仿真问卷作答数据。**

[![version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/Bardbo/miaomiao-skills)
[![license](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Bardbo/miaomiao-skills)
[![English](https://img.shields.io/badge/lang-English-blue)](README_EN.md)

## 简介

jev-survey-simulation 是一个 [Hermes Skill](https://hermes-agent.nousresearch.com/docs)，用 TypeSafe 的 jev 决策模型（System One 模型）按目标人群画像批量模拟填写问卷。核心思路：

- 问卷题型与 jev 三种原语一一对应：单选题→choice、量表题→score、是非题→noul
- 大模型根据问卷内容与目标人群，结合预设画像库，**现场设计 6~15 个代表画像**（MBTI + 职业 + 人生轨迹），各配一个比例
- 每个画像（state）只调用一次 jev API 填完整份问卷，按比例复制出指定份数
- 逐份复制时按 jev 返回的 probabilities 加权采样，**副本之间有自然方差**，避免千人一面
- 输出：逐份答卷（JSON/CSV）+ 总体统计（每题分布 + 每题置信度 + 低置信度清单）

## 功能

| 功能 | 说明 |
|------|------|
| **画像现场设计** | LLM 结合 `profile-library.md` 预设素材，按问卷+人群设计画像与比例 |
| **一次调用填整份** | 每个 state 一个 fan-out 请求，93 题规模的问卷约 2 秒返回 |
| **按比例复制** | 最大余数法分份，逐份带概率采样噪声，可复现（种子=state+副本号） |
| **三级兜底链** | jev 不可用 → 宿主 agent 代填 → 无 AI 规则引擎 |
| **置信度质量指标** | 每 state 每题 confidence，输出低置信度清单 |
| **开放题处理** | 主观题预置在每个画像的 `open_answers` 中 |
| **成本透明** | 自动打印 token 用量与估算成本 |

## 快速开始

### 前置条件

```bash
# TypeSafe API Key（也可以后续以环境变量提供）
export TYPESAFE_API_KEY=your_key_here
```

### 使用方法

在 Hermes 中加载 skill：

```bash
skill_view('jev-survey-simulation')
```

然后提供三要素：

> "我有这份大学生问卷，帮我做 500 份模拟作答，目标人群是在校本科生。"

Skill 会自动：
1. 解析问卷，把题目映射为 jev 的 choice/score/noul 问题
2. 设计 6~15 个代表性画像（MBTI/职业/轨迹）× 比例，展示给你确认
3. 每个 state 调用一次 jev 填完整份问卷
4. 按比例复制+带噪声采样出 500 份
5. 输出 `responses.json` / `responses.csv` / `summary.json`

### 手动调用管道脚本

```bash
python scripts/survey_pipeline.py spec.json --out ./result
```

spec 结构见 `templates/example-survey-spec.json`。

### 已实测数据

- 93 题中文 choice（MBTI 全卷）一次调用：7,601 input tokens，2.1 秒，约 $0.32
- 2 画像 × 4 题小问卷：1,173 tokens，成本 ~$0.0001
- 中文识别正常（实测 jev-1.13.0）

## 文件结构

```
jev-survey-simulation/
├── SKILL.md                    # 核心技能指令（工作流+兜底链+结果定性）
├── references/
│   ├── jev-api.md              # TypeSafe API 浓缩参考（原语/限流/错误码）
│   └── profile-library.md      # 画像库素材（MBTI 16型/职业/轨迹/人群默认比例）
├── scripts/
│   └── survey_pipeline.py      # 批填+复制+统计管道（TSAFE_API_KEY 环境变量）
├── templates/
│   └── example-survey-spec.json # spec 范例（可直接修改使用）
├── README.md                   # 中文说明（默认）
└── README_EN.md                # English Version
```

## 兜底链

检测：无 `TYPESAFE_API_KEY` / 401 / 402（余额不足）/ 429（限流重试耗尽）/ 网络失败。触发时明确告知用户原因，然后按其选择执行：

1. **宿主 agent 兜底** — 由当前 agent 按同一套画像逐题逐份填写（无概率分布，慢）
2. **无 AI 规则引擎** — 不调任何模型，按 profile 模板答案 + 固定种子伪随机生成（零依赖，但说明局限）

## 结果性质

产物是「按输入画像与比例推测的模拟投影」，**不是真实调研数据**，用于测试/预演/教学/演示。

## 数据来源

| 来源 | 用途 |
|------|------|
| [TypeSafe API](https://docs.typesafe.ai) | jev 决策模型（`jev-latest`，System One 模型） |
| [TypeSafe 文档](https://docs.typesafe.ai/llms.txt) | API 细节（本文档如有出入以官方为准） |

## License

MIT
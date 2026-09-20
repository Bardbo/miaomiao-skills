---
name: jev-survey-simulation
description: >
  Use when 批量填问卷/模拟人群作答。用 TypeSafe jev 按画像批填、按比例复制并统计，含兜底。
---

# Jev 问卷批量模拟填写

用 jev（TypeSafe 旗舰决策模型）按目标人群画像批量模拟填写问卷。核心思路：
问卷题型与 jev 三种原语一一对应，每个画像(state)只调一次 API 填完整份问卷，
按人群比例复制出指定份数，得到逐份答卷与总体统计。

## 何时使用

- 用户说：批量填问卷 / 帮我生成 N 份问卷数据 / 模拟某人群的问卷回答
- 手上有问卷题目文本（或链接），需要按目标人群生成仿真作答
- 目的通常是：问卷答题逻辑测试、课程/调研预演、演示、教学

## 工作流（每步要落地为真实产物）

### 1. 收集输入（若缺信息先问，一次问全）

| 输入 | 说明 |
|---|---|
| 问卷内容 | 题目文本/链接。无现成文本需先提取（链接→web_extract/浏览器） |
| 目标人群 | 用户描述，如「在校大学生」「一线城市互联网从业者」「考研二战考生」 |
| 份数 | 预计生成的问卷份数 N |
| 比例（可选） | 三档：用户手填 > 目标人群常识默认分布 > 由 LLM 按人群推定（默认推给用户确认） |

### 2. 设计画像（LLM 现场设计，这是核心智力环节）

- 素材来自 `references/profile-library.md`：MBTI 16型、职业、人生轨迹、年龄段等维度
- **不要穷举**：从素材库按目标人群结构抽取 6~15 个代表 profile，覆盖人群主要构成，
  每个配一个比例（合计 100%）。每个 profile 是：`标签 + 完整 state 文本 + open_answers`
- state 撰写规范：第三人称、具体事实、包含基本身份/个性倾向/典型行为/生活阶段/
  当前情境（问卷相关），让模型能据此对各题做有根据的判断（见 profile-library 模板）
- **长尾处理**：用户调研对象独特时（如「985 大四保研边缘的学生」），
  不硬套素材库，按问卷内容+人群现场设计维度与画像
- 开放题（主观/填空）：jev 不能生成自由文本，容纳在 profile 的 `open_answers` 里预置答案，
  每个 profile 一份基础答案（同一 state 的副本共用该模板；如需每份不同，agent 最后做后处理变体），
  语气与 state 一致
- 跳题逻辑：若问卷有分支题，先按 profile 预判分支归属，过滤掉不适用的题再进 jev 调用；
  jev 批内题目互相独立、看不到彼此答案，分支不能交给批内动态处理
- 展示画像清单与比例给用户确认后再调 API（用户可改比例）

### 3. jev 批填（每 state 一次调用）

- 问卷题型映射：

| 问卷题型 | jev 原语 | criteria/levels |
|---|---|---|
| 单选题 | choice | `{"选项id": "选项文本"}`（有"其他"选项就加进 criteria，符合官方"include no-match"建议） |
| 量表题(李克特) | score | 有序 levels 数组 2~10 个，**描述情境**而非程度词（"严重影响工作"优于"非常严重"） |
| 是非/判断题 | noul | instructions 即判断题陈述 |
| 开放题 | 不走 jev | 用 profile.open_answers |
- 每个 state 一个 POST `https://api.typesafe.ai/v1/systemone`，`model: "jev-latest"`，
  questions map 的 key 用 `q1/q2…`，model 看不到 key，选项描述要能互相区分
- API 细节/限流/错误码见 `references/jev-api.md`；key 只从环境变量 `TYPESAFE_API_KEY` 读，
  绝不写进文件或代码
- 每个 state 保存原始响应（含 probabilities/confidence），并打印 input_tokens 与估算成本

### 4. 复制与统计（用 `scripts/survey_pipeline.py` 做，勿手写浮点数逻辑）

- 每 state 份数 = round(N×比例)，总数差用最大余数法补齐
- **逐份复制带噪声**：choice 按 probabilities 加权采样、score 按层级概率采样、
  noul 按概率采样——同一 state 的副本之间自然浮动，避免千人一面
- 质量指标顺手产出：每题平均置信度、低置信度题清单（这些题的答案可信度低，标注）

### 5. 输出

- 逐份答卷：`responses.json`（含每份的 state 标签与分析）+ `responses.csv`
- 总体统计：`summary.json`——每题各选项人数与占比、量表均值、交叉表（若用户要）
- 交付时给用户一个简表：份数、画像数、每题分布概览、总成本
- 产物存工作目录/桌面某文件夹，报告绝对路径

## 兜底链（jev 不可用时）

检测：无 TYPESAFE_API_KEY / 401 / 402 余额不足 / 429 重试耗尽 / 网络失败。
触发时**明确告知用户原因**，然后询问并按其选择执行：

1. **宿主 agent 兜底**：由当前 agent 按同一套画像，逐题逐份填写（无概率分布、慢、逐份真实消耗 token）
2. **无 AI 规则引擎**：不调任何模型，按 profile 模板答案 + 固定种子伪随机生成逐份数据
   （零依赖最稳，但要说明：逐份差异仅来自规则噪声）

## 结果性质（必须向用户说明）

产物是「按输入画像与比例推测的模拟投影」，不是真实调研数据；用于测试/预演/教学/演示。
若用户声称要交给真实研究或平台，改为提醒其用真人作答。

## API 细节以官方文档为准

TypeSafe 官方 skill：`github.com/typesafe-ai/skills`（SKILL.md 可直接读）。
live docs 索引 `https://docs.typesafe.ai/llms.txt`（Mintlify 可加 `.md` 后缀读 Markdown）。
调 API 前若遇到版本/字段疑问，读 `docs.typesafe.ai/api.md` 与对应 primitives 页。
本 skill 的 `references/jev-api.md` 是浓缩版，冲突时以官方为准。

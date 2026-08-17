# 🧠 Smart-Pick（慧选）—— 通用多方案权衡助手

> **版本：** v2.1 | **状态：** Beta | **达尔文评分：** 84.3/100

慧选是一个**完全通用、不预设领域规则**的多方案决策辅助工具。无论是商品比价、保险方案、标书对比、项目计划还是人生规划，只要你有多个选项需要权衡，慧选就能帮你做结构化比较。

## 核心能力

| 能力 | 说明 |
|------|------|
| **动态权重** | 每次根据场景特征（风险、资金、专业需求等）+ 用户历史偏好自动生成权重，不写死 |
| **OCR 图文识别** | 集成 PaddleOCR，截图/保单图片直接提取文字进分析 |
| **实时比价** | 集成 OpenCLI smzdm 适配器，从京东/拼多多/天猫等平台获取实时价格 |
| **分层追问** | 信息不足时先问最关键的 2 个问题，再问次要问题，不堆砌 |
| **外部方案搜索** | 自动判断是否需要搜索更优方案，用户确认后才执行 |
| **反馈学习** | 记录用户最终选择，逐步调整偏好向量，越用越懂你 |
| **可干预** | 用户随时调整权重或忽略某个维度，结果透明可解释 |

## 工作流程（七步法）

```
Step 0  加载偏好 + 动态权重生成
Step 1  方案识别与维度提取
Step 2  信息补全（分层追问）
Step 3  个性化加权评分
Step 4  外部方案搜索（可选）
Step 5  输出推荐 + 对比表
Step 6  反馈学习 → 更新偏好画像
```

## 文件结构

```
smart-pick/
├── SKILL.md                        # 核心指令（Hermes Skill 格式）
├── test-prompts.json               # 达尔文测试集
├── assets/
│   └── output_template.md          # 输出格式模板
├── references/
│   ├── scene_features.md           # 场景特征→关键词映射
│   ├── scoring_methods.md          # 评分算法
│   ├── examples.md                 # 典型场景示例
│   ├── ocr-integration.md          # OCR + 慧选集成工作流
│   └── opencli-price-source.md     # OpenCLI 实时比价集成
└── scripts/
    └── search_external.py          # 外部搜索（Mock 示例）
```

## 安装

### 作为 Hermes Skill

```bash
# 将 SKILL.md 复制到 Hermes skills 目录
cp -r smart-pick/ ~/.hermes/skills/productivity/
```

### 独立使用

SKILL.md 本身就是完整指令，支持任何兼容 Agent Skills 规范的平台（Claude Code / Codex / Cursor / OpenClaw / Hermes）。

## 适用场景

- 🛒 **商品比价**：多款手机、笔记本、显卡等
- 🚗 **保险方案**：车保、医疗险、寿险方案对比
- 📄 **标书/项目**：多份投标书或项目计划权衡
- 🎓 **志愿填报**：学校、专业选择
- 📈 **投资方案**：理财产品、投资组合比较
- 🏠 **人生决策**：买房方案、职业选择、退休规划

## 设计方法

慧选的设计受以下作品启发：

- **[达尔文 Skill](https://github.com/alchaincyf/darwin-skill)**：Microsoft Research SkillLens（arXiv 2605.23899）+ SkillOpt（arXiv 2605.23904）的 9 维评估药方
- **[花叔的女娲 Skill](https://github.com/alchaincyf/huashu-nuwa-skill)**：思维蒸馏与认知框架构建
- **[同事.skill](https://github.com/niceman/tongshi-skill)**：职场知识封装范式
- **Karpathy autoresearch**：自主实验循环与棘轮机制

## License

MIT
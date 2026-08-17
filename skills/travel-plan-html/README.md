# 🗺️ Travel Plan HTML Generator

> **根据用户输入的旅行需求，自动生成带飞猪实时价格、天气预报、小红书灵感和高德地图的完整 HTML 旅行规划文件。**

[![version](https://img.shields.io/badge/version-2.1.0-green)](https://github.com/Bardbo/travel-plan-html)
[![license](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Bardbo/travel-plan-html)
[![English](https://img.shields.io/badge/lang-English-blue)](README_EN.md)

## 简介

Travel Plan HTML Generator 是一个 [Hermes Skill](https://hermes-agent.nousresearch.com/docs)，可自动生成完整的旅行规划 HTML 文件。它集成了：

- **实时比价** — 通过飞猪 FlyAI CLI 查询酒店和火车票实时价格，每条数据都带可点击的预订链接
- **天气预报** — 从天气网获取 15 天预报，嵌入每天的时间轴卡片
- **小红书灵感** — 搜索目的地的热门笔记，提取推荐内容，嵌入时间轴中
- **高德地图** — 生成交互式行程路线地图，标注各城市 POI

## 功能

| 功能 | 说明 |
|------|------|
| **实时数据** | 飞猪实时酒店/火车票价格 + 预订链接 |
| **天气集成** | 15 天预报嵌入每天卡片 |
| **小红书笔记** | 搜索旅行灵感，嵌入可点击链接 |
| **高德地图** | 交互式行程路线图 + POI 搜索按钮 |
| **费用汇总** | 自动计算预算表 |
| **断点续传** | 检查点文件保存进度 |

## 快速开始

### 前置条件

```bash
# 安装飞猪 FlyAI CLI（用于实时酒店/火车票数据）
npm i -g @fly-ai/flyai-cli

# 安装 OpenCLI（可选，用于小红书搜索）
npm install -g @jackwener/opencli
```

### 使用方法

在 Hermes 中加载 skill：

```bash
skill_view('travel-plan-html')
```

然后提供你的旅行需求，例如：

> "帮我做一个7天广西攻略，从长沙出发，7月13日到7月19日，3个人2间房，必须包含南宁。"

Skill 会自动：
1. 搜索小红书获取目的地灵感
2. 通过飞猪 CLI 查询实时酒店和车次价格
3. 获取天气预报
4. 生成完整的 HTML 攻略文件（含预订链接和地图）

### 输出示例

```
Day 1: 长沙→南宁 (高铁¥3xx/人，约4h)
  - 酒店：维也纳酒店(南湖公园店) (¥2xx/晚) [预订→]
  - 晚餐：中山路夜市
  - 🌧️ 阵雨 26~32°C

Day 3: 南宁→桂林 (高铁¥1xx/人，2.5h)
  - 酒店：麗枫酒店·象鼻山景区店 (¥3xx/晚) [预订→]
  - 景点：东西巷 + 桂林米粉
  - 🌧️ 小雨 24~30°C
```

## 文件结构

```
travel-plan-html/
├── SKILL.md                    # 核心技能指令（Hermes Skill 格式）
├── references/
│   └── html-template.md        # HTML 模板参考
├── README.md                   # 中文说明（默认）
└── README_EN.md                # English Version
```

## 数据来源

| 来源 | 用途 |
|------|------|
| [飞猪 FlyAI](https://flyai.open.fliggy.com/) | 实时酒店和火车票价格 |
| [天气网](https://www.tianqi.com/) | 15 天天气预报 |
| [高德 LBS](https://lbs.amap.com/) | 地图可视化和 POI 搜索 |
| [小红书](https://www.xiaohongshu.com/) | 旅行灵感笔记 |

## 注意事项

- 酒店和火车票价格为体验模式（显示为 ¥1xx、¥2xx）。前往[飞猪 AI 开放平台](https://flyai.open.fliggy.com/)获取免费 API Key 可查看精确价格
- 天气数据建议出发前 2 天复查
- 具体店名和价格建议出行前在小红书或大众点评确认最新信息
- **禁止编造店名、价格、营业时间**。不确定的信息用搜索链接代替

## 设计原则

1. **准确性** — 所有价格来自实时 API 查询，不估不编
2. **连贯性** — 推荐内容与当天时间线地理和时间匹配
3. **透明性** — 不确定的信息链向搜索结果页，不猜测
4. **整合性** — 小红书灵感嵌入时间轴，不单独成块

## License

MIT
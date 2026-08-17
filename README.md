# 喵喵技能包 (Miaomiao Skills)

[English](./README.en.md)

> 一个为 Hermes AI Agent 打造的技能合集，专注于微信公众号内容创作与 AI 辅助工作流。

## 技能列表

| 技能 | 说明 | SKILL.md |
|------|------|----------|
| [wechat-featured-list](./skills/wechat-featured-list/) | 公众号往期精选卡片墙——丢链接自动抓标题封面，3×3 圆角卡片，三行错开摆动 | ✅ |
| [wechat-svg](./skills/wechat-svg/) | 公众号 SVG 交互组件——砸金蛋、翻牌、刮刮卡、进度条、序列帧、错层滑动等 | ✅ |
| [wechat-chat-simulator](./skills/wechat-chat-simulator/) | 将对话 Markdown 渲染为微信聊天模拟器 HTML 页面 | ✅ |
| [travel-plan-html](./skills/travel-plan-html/) | 生成带实时价格查询的旅行计划 HTML 页面 | ✅ |
| [tavern-rp](./skills/tavern-rp/) | 在 Hermes 中加载 SillyTavern 角色卡进行角色扮演 | ✅ |
| [talk](./skills/talk/) | 模拟沉浸式多角色对话，带人格管理与上下文压缩 | ✅ |
| [smart-pick](./skills/smart-pick/) | 通用多方案权衡助手，支持动态权重生成与外部方案搜索 | ✅ |
| [skill-curator](./skills/skill-curator/) | 综合技能管理与持续改进系统（9 维评估 + 优化引擎） | ✅ |

## 项目结构

```
miaomiao-skills/
├── README.md              ← 中文文档（默认展示）
├── README.en.md           ← 英文文档
└── skills/
    ├── wechat-featured-list/  往期精选卡片墙
    ├── wechat-svg/            公众号 SVG 交互
    ├── wechat-chat-simulator/ 微信聊天模拟器
    ├── travel-plan-html/      旅行计划 HTML
    ├── tavern-rp/             角色扮演
    ├── talk/                  多角色对话
    ├── smart-pick/            方案权衡
    └── skill-curator/         技能管理
```

## 使用方式

每个技能都是独立的 Hermes agent skill，包含 `SKILL.md` 主文件及可选的 `references/`、`scripts/`、`templates/` 等子目录。

### 安装到 Hermes

```bash
# 将技能目录复制到 Hermes 技能目录
cp -r skills/wechat-svg /path/to/hermes/skills/

# 或使用 Hermes 的 skill_manage 工具安装
# 在 Hermes 对话中调用 skill_manage(action='install', name='wechat-svg')
```

### 直接从 Hermes 调用

所有技能都可以在 Hermes Agent 对话中通过 `skill_view` 加载使用：

```
Hermes > 加载 wechat-svg 技能
```

## 关于

由 [Bardbo](https://github.com/Bardbo)（公众号「穿梭在银河的喵喵」）基于 [Hermes Agent](https://hermes-agent.nousresearch.com) 构建。

所有技能均在真实公众号文章中验证可用。
# 喵喵技能包 (Miaomiao Skills)

[English](./README.md)

一个为 Hermes AI Agent 打造的技能合集，专注于微信公众号内容创作，尤其是 SVG 交互组件。

## 包含技能

| 技能 | 说明 |
|------|------|
| [wechat-svg](./skills/wechat-svg/) | 为公众号文章生成可交互的 SVG 动画——点击揭秘、翻牌卡片、刮刮卡、进度条、序列帧动画等 |
| [wechat-featured-list](./skills/wechat-featured-list/) | 生成公众号文章底部「往期精选」卡片墙——3×3 网格、自动错开滚动、封面图、圆角卡片 |
| [wechat-chat-simulator](./skills/wechat-chat-simulator/) | 将对话 Markdown 渲染为微信聊天模拟器 HTML 页面 |
| [travel-plan-html](./skills/travel-plan-html/) | 生成带实时价格查询的旅行计划 HTML 页面 |
| [tavern-rp](./skills/tavern-rp/) | 在 Hermes 中加载 SillyTavern 角色卡进行角色扮演 |
| [talk](./skills/talk/) | 模拟沉浸式多角色对话，带人格管理 |
| [smart-pick](./skills/smart-pick/) | 通用多方案权衡助手，支持动态权重生成 |
| [skill-curator](./skills/skill-curator/) | 综合技能管理与持续改进系统 |

## 使用方法

每个技能都是独立的 Hermes agent 技能。将技能目录复制到你的 Hermes 技能文件夹，或使用 `skill_manage` 工具安装。

## 关于

由 [Bardbo](https://github.com/Bardbo) 基于 [Hermes Agent](https://hermes-agent.nousresearch.com) 构建。
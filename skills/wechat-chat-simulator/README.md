# WeChat Chat Simulator · 微信聊天模拟器

<p align="center">
  <a href="#readme">🇨🇳 中文</a> · <a href="README_EN.md">🇬🇧 English</a>
</p>

> **⚠️ 测试版** — 此技能正在积极开发中，API 和行为可能发生变化。欢迎提交 Issue 和 PR。

## 概述

将对话式 Markdown（如 `talk` 技能输出）渲染为独立的微信风格聊天 HTML 页面。支持群聊和双人对话两种布局，包含头像上传、改名、导出长图等交互功能，适合用于公众号配图、演示截图或预览。

本技能的设计参考了以下项目/技能的方法论：

- **[huashu-nuwa](https://github.com/Bardbo/skill-curator)** — 技能蒸馏与创建框架，为角色构建提供了人格提取的底层思路
- **[darwin-skill](https://github.com/Bardbo/skill-curator)** — 9 维评分体系的评估方法论，用于持续优化渲染质量
- **[talk](https://github.com/Bardbo/skill-curator/tree/main/talk)** — 多角色对话生成技能，本技能是 talk 的下游渲染端

## 功能

| 特性 | 说明 |
|------|------|
| **群聊模式** | 3+ 角色自动切换为左对齐白气泡 + 昵称标签 + 头像 |
| **双人对话模式** | 2 角色自动切换为己方绿色气泡（右）/ 对方白色气泡（左） |
| **头像上传** | 点击任意头像上传自定义图片，即时生效 |
| **改名** | 顶部工具栏的"改名"按钮可修改聊天标题 |
| **实时发送** | 底部输入框可打字发送新消息 |
| **导出长图** | 使用 html2canvas 导出 PNG，自动处理 box-shadow 溢出问题 |
| **SVG 头像** | 内置纯色 SVG 首字母头像，无需外部资源 |
| **单一 HTML** | 所有 CSS/JS inline，一个文件即可运行 |

## 快速开始

```bash
# 1. 在 Hermes Agent 中加载技能
skill_view(name='wechat-chat-simulator')

# 2. 准备好对话数据（Markdown 格式，每段用 **角色名：** 内容 格式）
# 3. 按照 SKILL.md 的步骤生成 HTML
```

生成的文件在桌面的 `群聊模拟器/` 目录下，直接用浏览器打开即可。

## 文件结构

```
wechat-chat-simulator/
├── SKILL.md                           # 技能主文件（执行步骤 + Pitfalls）
├── README.md                          # 本文件（中文）
├── README_EN.md                       # 英文 README
├── references/
│   ├── wechat-chat-template.html      # 渲染模板（核心）
│   ├── avatar-export-strategy.md      # 头像与导出策略
│   ├── base64-avatar-fallback.md      # Base64 头像备用方案
│   └── svg-encoding-pitfalls.md       # SVG 编码陷阱
```

## 依赖

- 浏览器（Chrome / Edge / Firefox）
- html2canvas（CDN 在线加载，首次需要网络）
- 图标字体（Twemoji，CDN 在线加载）

## 已知问题 / 限制

1. **html2canvas CDN** — 在 `file://` 协议下首次打开时需要网络加载 html2canvas，加载完成后离线可用
2. **SVG 渐变** — SVG data URI 中的 `url(#gradient)` 引用会因双重编码失效，建议使用纯色填充
3. **SVG 引号碰撞** — SVG 属性必须使用双引号，因为外层 JS 变量使用单引号包裹
4. **导出大图** — 长对话的导出 PNG 可能达到 1.5MB+，浏览器控制台可能截断 data URL
5. **字体对齐** — 中英文混合时行高略有差异，建议使用系统默认字体

## 许可

MIT — 可自由使用、修改和分发。保留原始署名即可。
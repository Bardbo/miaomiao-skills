# 公众号 SVG 交互组件

<p align="center">
  <a href="../README.md">🇨🇳 中文</a> · <a href="README.md">🇬🇧 English</a>
</p>

为公众号文章生成可交互的 SVG 动画组件。点击揭秘、翻牌卡片、刮刮卡、进度条、序列帧动画、错层滑动等，全部纯 SVG 实现，不需要 JavaScript。

## 功能

- **点击揭秘（砸金蛋/刮刮卡）** — 点击后揭示隐藏内容
- **翻牌卡片** — 点击翻面显示背面内容
- **错层滑动** — 点击滑动图层，露出下方内容
- **自动动画（进度条/呼吸灯）** — 自动运行的进度条、脉冲按钮、闪烁光标
- **序列帧** — 元素依次出现
- **往期精选卡片墙** — 3×3 文章卡片墙，错开滚动（见 [wechat-featured-list](../wechat-featured-list/)）

## 原理

公众号编辑器原生支持 SVG。每个交互组件都是一段自包含的 SVG 代码，可以直接粘贴到编辑器的 HTML 模式。

## SVG 兼容性（微信版）

微信的 SVG 解析器有特定限制，关键规则：

- **全小写** — 属性名和标签名必须全小写（`attributename`、`animatetransform`、`viewbox`）
- **`<svg>` 上不写 `style`** — 样式放到外层 `<section>` 上
- **点击事件** — 使用 `begin="mousedown"` + `fill="freeze"` + `restart="never"`
- **无 JS** — `<script>`、`onclick`、`onmouseover` 全部被拦截
- **无 `id`/`class`/`defs`/`clipPath`** — 全部禁用
- **`foreignObject`** — 只用于链接热区，不要用于文字（会错位）
- **图片圆角** — 用 CSS `border-radius` + `background-image`，不要用 `<image rx>`（只是视觉裁剪，方形像素会露出来）

## 使用方法

将 SKILL.md 内容复制到你的 Hermes agent 技能目录，或使用 `skill_manage` 工具安装。

## 关于

由 [Bardbo](https://github.com/Bardbo) 基于 [Hermes Agent](https://hermes-agent.nousresearch.com) 构建。
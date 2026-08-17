# WeChat SVG Interactive Components · 公众号 SVG 交互组件

<p align="center">
  <a href="../README.md">🇨🇳 中文</a> · <a href="#readme">🇬🇧 English</a>
</p>

Generate interactive SVG animations for WeChat Official Account (公众号) articles. Click-to-reveal, card flips, scratch cards, progress bars, sequence animations, and more — all pure SVG, no JavaScript required.

## Features

- **Click-to-Reveal (砸金蛋/刮刮卡)** — Tap to reveal hidden content underneath
- **Card Flip (翻牌)** — Tap to flip a card and show the reverse side
- **Slide Layer (错层滑动)** — Tap to slide a layer and reveal content beneath
- **Auto Animation (进度条/呼吸灯)** — Self-running progress bars, pulsing buttons, blinking cursors
- **Sequence Frame (序列帧)** — Elements appear one by one in sequence
- **Featured Card Wall (往期精选卡片墙)** — 3×3 grid of article cards with staggered scrolling (see [wechat-featured-list](../wechat-featured-list/))

## How It Works

WeChat Official Account editor supports SVG natively. Each interactive component is a self-contained SVG snippet that you can paste directly into the editor's HTML mode.

## SVG Compatibility (WeChat Edition)

WeChat's SVG parser has specific quirks. Key rules:

- **All lowercase** — attribute names and tag names must be lowercase (`attributename`, `animatetransform`, `viewbox`)
- **No `style` on `<svg>`** — put styles on the wrapper `<section>` instead
- **Click events** — use `begin="mousedown" + fill="freeze" + restart="never"`
- **No JS** — `<script>`, `onclick`, `onmouseover` are all blocked
- **No `id`/`class`/`defs`/`clipPath`** — all disabled
- **`foreignObject`** — use only for link hot zones, not for text (text will misalign)
- **Round corners on images** — use CSS `border-radius` via `background-image`, not `<image rx>` (which is visual-only and leaves square pixels)

## Usage

Copy the SKILL.md content to your Hermes agent's skill directory, or use the `skill_manage` tool to install it.

## About

Built with [Hermes Agent](https://hermes-agent.nousresearch.com) by [Bardbo](https://github.com/Bardbo).
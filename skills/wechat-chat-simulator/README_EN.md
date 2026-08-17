# WeChat Chat Simulator

<p align="center">
  <a href="README.md">🇨🇳 中文</a> · <a href="#readme">🇬🇧 English</a>
</p>

> **⚠️ Beta** — This skill is under active development. API and behavior may change. Issues and PRs welcome.

## Overview

Convert dialogue-style Markdown (e.g. output from the `talk` skill) into a standalone WeChat-style chat HTML page. Supports both group chat and two-person conversation layouts, with interactive features including avatar upload, rename, and image export. Ideal for WeChat Official Account illustrations, presentation screenshots, or previews.

This skill's design references the following projects/skills:

- **[huashu-nuwa](https://github.com/Bardbo/miaomiao-skills)** — Skill distillation and creation framework, providing the underlying approach for persona extraction
- **[darwin-skill](https://github.com/Bardbo/miaomiao-skills)** — 9-dimension evaluation methodology, used for continuous rendering quality optimization
- **[talk](https://github.com/Bardbo/miaomiao-skills/tree/main/talk)** — Multi-character dialogue generation skill; this skill is the downstream rendering companion to talk

## Features

| Feature | Description |
|---------|-------------|
| **Group Chat Mode** | 3+ speakers: left-aligned white bubbles + name labels + avatars |
| **Dual Mode** | 2 speakers: self = green bubble (right), other = white bubble (left) |
| **Avatar Upload** | Click any avatar to upload a custom image, updates instantly |
| **Rename** | "Rename" button in toolbar to change chat title |
| **Live Send** | Bottom input to type and send new messages |
| **Export as PNG** | Uses html2canvas with box-shadow overflow handling |
| **SVG Avatars** | Built-in solid-color first-letter SVG avatars, no external deps |
| **Single HTML** | All CSS/JS inline, one file ready to open |

## Quick Start

```bash
# 1. Load the skill in Hermes Agent
skill_view(name='wechat-chat-simulator')

# 2. Prepare dialogue data (Markdown: **Speaker: ** content per paragraph)
# 3. Follow SKILL.md instructions to generate the HTML
```

Output is placed in the `群聊模拟器/` directory on your desktop. Open the HTML directly in any browser.

## File Structure

```
wechat-chat-simulator/
├── SKILL.md                           # Main skill file (execution steps + Pitfalls)
├── README.md                          # Chinese README
├── README_EN.md                       # This file (English)
├── references/
│   ├── wechat-chat-template.html      # Rendering template (core)
│   ├── avatar-export-strategy.md      # Avatar & export strategy
│   ├── base64-avatar-fallback.md      # Base64 avatar fallback
│   └── svg-encoding-pitfalls.md       # SVG encoding pitfalls
```

## Dependencies

- Browser (Chrome / Edge / Firefox)
- html2canvas (loaded via CDN, requires network on first open)
- Twemoji icon font (loaded via CDN)

## Known Issues / Limitations

1. **html2canvas CDN** — Requires network on first open under `file://` protocol; works offline after caching
2. **SVG Gradients** — `url(#gradient)` references in SVG data URIs break due to double-encoding; use solid fills instead
3. **SVG Quote Collision** — SVG attributes must use double quotes since the outer JS uses single quotes
4. **Large Export** — Long conversations may produce 1.5MB+ PNGs; data URLs may be truncated in browser consoles
5. **Font Alignment** — Minor line-height differences when mixing CJK and Latin characters; stick to system fonts

## License

MIT — Free to use, modify, and distribute. Attribution appreciated.
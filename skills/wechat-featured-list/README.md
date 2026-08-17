# WeChat Featured Articles Card Wall · 公众号往期精选卡片墙

<p align="center">
  <a href="../README.zh.md">🇨🇳 中文</a> · <a href="#readme">🇬🇧 English</a>
</p>

Generate a "Featured Articles" card wall at the bottom of your WeChat Official Account articles. Automatically fetches titles and cover images, arranges them in a 3×3 grid with staggered scrolling animation.

## Features

- **Auto-fetch** — Given article URLs, automatically fetches titles (`og:title`) and cover images (`og:image`)
- **3×3 Grid** — 9 articles arranged in 3 rows × 3 columns
- **Staggered Scrolling** — Each row has a subtle horizontal sway (±26px), with different phases per row — creates a natural, non-uniform dynamic feel
- **Rounded Corners** — CSS `border-radius:10px` via `background-image`, properly clips corners (not the fake `<image rx>` that leaves square pixels showing)
- **Smart Title Wrapping** — Short titles display in one line, long titles wrap to two lines (prefers breaking at punctuation)
- **Title Visibility** — Semi-transparent black bar at the bottom of each card ensures white text is readable on any cover image
- **Caching** — Fetched titles and covers are cached; repeat runs don't re-request
- **White Background** — Clean white background matching the WeChat editor's default
- **Clickable** — Each card is a full-area clickable link via E2.COOL's official `foreignObject` + `<a>` component

## Security

- **Only fetches short links** (`https://mp.weixin.qq.com/s/xxx`). Long tracking links (with `?__biz=`, `chksm=` parameters) are **skipped** to avoid WeChat anti-crawling measures and account bans.
- **Local HTML files** — Use filenames as titles, no network requests made.

## Usage

```bash
# Configure (JSON): put your article links in featured_config.json
# {"title": "往期精选", "urls": ["https://mp.weixin.qq.com/s/xxx", ...]}

# Generate standalone HTML
python scripts/gen_featured.py featured_config.json featured_list.html

# Or append to an existing article HTML
python scripts/gen_featured.py featured_config.json --append article.html
```

## About

Built with [Hermes Agent](https://hermes-agent.nousresearch.com) by [Bardbo](https://github.com/Bardbo).
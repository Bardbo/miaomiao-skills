# WeChat Featured Articles Card Wall · 公众号往期精选卡片墙

<p align="center">
  <a href="#readme">🇬🇧 English</a> · <a href="./README_CN.md">🇨🇳 中文</a>
</p>

Generate a "Featured Articles" card wall at the bottom of your WeChat Official Account articles. Drop in article links, and the script automatically fetches titles and cover images, arranging them into a 3×3 rounded-corner card wall with staggered scrolling rows on a white background.

## Features

- Auto-fetch titles (`og:title`) and cover images (`og:image`) from links
- 3 rows × 3 columns = 9 articles, taking the last 9 entries from config (append new links at the end)
- Each row sways ±26px with different phases — a staggered, natural dynamic feel
- CSS `border-radius` truly clips corners; no square pixels leak through
- Smart title wrapping: short titles stay one line, long titles wrap to two (preferring punctuation breaks)
- Semi-transparent black bar at card bottom keeps white titles readable on any cover
- Fetch results cached to `featured_cache.json`; repeat runs make no network requests
- White background matching the WeChat editor's default

## Usage

```bash
# 1. Configure your links (JSON)
# Create featured_config.json:
# {"title": "往期精选", "urls": ["https://mp.weixin.qq.com/s/xxx", ...]}

# 2. Generate standalone HTML
python scripts/gen_featured.py featured_config.json featured_list.html

# Or append directly to your article HTML
python scripts/gen_featured.py featured_config.json --append article.html
```

## Security

- Only fetches short links (`https://mp.weixin.qq.com/s/xxx`)
- Long tracking links (with `?__biz=` parameters) are skipped to avoid WeChat anti-crawling measures
- Local HTML files use their filenames as titles; no network requests made

## About

Built with [Hermes Agent](https://hermes-agent.nousresearch.com) by [Bardbo](https://github.com/Bardbo).
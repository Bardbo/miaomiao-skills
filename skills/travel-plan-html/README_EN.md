# 🗺️ Travel Plan HTML Generator

> **Generate beautiful, interactive HTML travel plans with real-time flight/hotel data from Fliggy, weather forecasts, Xiaohongshu travel inspiration, and AMap visualizations.**

[![version](https://img.shields.io/badge/version-2.1.0-green)](https://github.com/Bardbo/travel-plan-html)
[![license](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Bardbo/travel-plan-html)
[![中文 README](https://img.shields.io/badge/lang-中文-green)](README.md)

## Overview

Travel Plan HTML Generator is a [Hermes Skill](https://hermes-agent.nousresearch.com/docs) that creates comprehensive HTML travel planning files. It automatically searches Xiaohongshu for travel inspiration, queries real-time hotel/train prices via Fliggy FlyAI CLI, fetches weather forecasts, and generates a beautiful HTML document with clickable booking links, restaurant recommendations, and an interactive route map.

## Features

- **Real-time Data** — Hotels and train tickets with booking links from Fliggy
- **Weather Integration** — 15-day forecasts embedded in each day card
- **Xiaohongshu Notes** — Search travel inspiration, embed as clickable links
- **AMap Route Map** — Interactive map with POI markers for each city
- **Cost Summary** — Auto-calculated budget table
- **Checkpoint/Resume** — Saves progress for long-running tasks

## Prerequisites

```bash
# Install Fliggy FlyAI CLI (required for real-time data)
npm i -g @fly-ai/flyai-cli

# Install OpenCLI (optional, for Xiaohongshu integration)
npm install -g @jackwener/opencli
```

## Usage

Load the skill in Hermes:

```bash
skill_view('travel-plan-html')
```

Then describe your trip:

> "I want a 7-day trip to Guangxi, starting from Changsha on July 13, 3 people, 2 rooms. Must include Nanning."

The skill will:
1. Search Xiaohongshu for travel inspiration about each destination
2. Query real-time hotel and train prices via FlyAI CLI
3. Fetch weather forecasts from tianqi.com
4. Generate a complete HTML file with:
   - Daily timeline cards with weather badges
   - Hotel and train tables with booking links
   - Restaurant recommendations
   - Interactive AMap route map
   - Cost breakdown table

## Output Example

```
Day 1: Changsha → Nanning (Train ¥3xx/person, 4h)
  - Hotel: Vienna Hotel Nanhu Park (¥2xx/night) [Book →]
  - Dinner: Zhongshan Road Night Market
  - 🌧️ Rainy 26~32°C

Day 3: Nanning → Guilin (Train ¥1xx/person, 2.5h)
  - Hotel: Lavande Hotel Xiangbishan (¥3xx/night) [Book →]
  - Visit: East West Alley + Guilin Rice Noodles
  - 🌧️ Light Rain 24~30°C
```

## File Structure

```
travel-plan-html/
├── SKILL.md                    # Core skill instruction (Hermes Skill format)
├── references/
│   └── html-template.md        # HTML template reference
├── README.md                   # Chinese (default)
└── README_EN.md                # English README
```

## Data Sources

| Source | Usage |
|--------|-------|
| [Fliggy FlyAI](https://flyai.open.fliggy.com/) | Real-time hotel & train pricing |
| [tianqi.com](https://www.tianqi.com/) | 15-day weather forecast |
| [AMap LBS](https://lbs.amap.com/) | Map visualization & POI search |
| [Xiaohongshu](https://www.xiaohongshu.com/) | Travel inspiration notes |

## Important Notes

- Hotel and train prices are in demo mode (¥1xx, ¥2xx). Get a free API key from Fliggy AI Open Platform for exact pricing.
- Weather data should be rechecked 2 days before departure.
- Specific restaurant names and prices should be verified on Xiaohongshu or Dianping before travel.
- **Never fabricate restaurant names, prices, or opening hours.** Use Xiaohongshu search links if uncertain.

## Design Principles

1. **Accuracy** — All prices come from real-time API queries, never estimated
2. **Coherence** — Recommendations must match the daily timeline geographically and temporally
3. **Transparency** — Uncertain information links to search results rather than guessing
4. **Integration** — Xiaohongshu tips are embedded in the timeline, not isolated in a separate section

## License

MIT
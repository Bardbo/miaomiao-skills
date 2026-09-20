# 📝 jev-survey-simulation

> **Batch survey response simulation powered by the TypeSafe jev decision model — generate simulated survey answers for a target population profile.**

[![version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/Bardbo/miaomiao-skills)
[![license](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Bardbo/miaomiao-skills)
[![中文](https://img.shields.io/badge/lang-中文-red)](README.md)

## Overview

jev-survey-simulation is a [Hermes Skill](https://hermes-agent.nousresearch.com/docs) that uses TypeSafe's jev decision model (a System One model) to batch-simulate survey responses for a target population. The core idea:

- Survey item types map 1:1 to jev's three primitives: single-choice → `choice`, Likert scale → `score`, yes/no → `noul`
- An LLM designs **6–15 representative profiles on the fly** (MBTI + occupation + life trajectory) from a preset library, each with a proportion
- Each profile (state) is submitted **once** to the jev API and fills the entire survey; results are then replicated by proportion
- Replication samples from jev's returned `probabilities`, so copies have **natural variance** — no two look identical
- Outputs: individual responses (JSON/CSV) + aggregate statistics (per-item distributions, per-state confidence, low-confidence list)

## Features

| Feature | Description |
|---------|-------------|
| **On-the-fly profile design** | LLM combines preset `profile-library.md` material with the survey + target population |
| **One call fills the whole survey** | One fan-out request per state; a 93-item survey returns in ~2 seconds |
| **Proportion-based replication** | Largest-remainder allocation, probability-sampled noise per copy, reproducible (seed = state + copy) |
| **Three-tier fallback** | jev unavailable → host agent fills → no-AI rule engine |
| **Confidence quality metrics** | Per-state per-item confidence + low-confidence list |
| **Open-ended items** | Prefilled per-profile in `open_answers` |
| **Cost transparency** | Prints token usage and estimated cost |

## Quick Start

### Prerequisites

```bash
# TypeSafe API Key (can also be provided as an environment variable later)
export TYPESAFE_API_KEY=your_key_here
```

### Usage

Load the skill in Hermes:

```bash
skill_view('jev-survey-simulation')
```

Then provide three things:

> "I have this university student survey — generate 500 simulated responses for undergraduate students."

The skill will automatically:
1. Parse the survey and map items to jev choice/score/noul questions
2. Design 6–15 representative profiles (MBTI/occupation/trajectory) × proportions, and show them for your confirmation
3. Call jev once per state to fill the whole survey
4. Replicate with probability-sampled noise to produce 500 responses
5. Output `responses.json` / `responses.csv` / `summary.json`

### Run the pipeline script directly

```bash
python scripts/survey_pipeline.py spec.json --out ./result
```

See `templates/example-survey-spec.json` for the spec structure.

### Measured performance

- 93 Chinese-choice items (full MBTI) in one call: 7,601 input tokens, 2.1s, ~$0.32
- 2 profiles × 4 items mini survey: 1,173 tokens, ~$0.0001
- Chinese is handled correctly (tested on jev-1.13.0)

## File Structure

```
jev-survey-simulation/
├── SKILL.md                    # Core skill instructions (workflow + fallback chain + result disclaimer)
├── references/
│   ├── jev-api.md              # Condensed TypeSafe API reference (primitives/limits/error codes)
│   └── profile-library.md      # Profile library material (MBTI 16 types/occupations/trajectories/default proportions)
├── scripts/
│   └── survey_pipeline.py      # Batch-fill + replicate + statistics pipeline (reads TYPESAFE_API_KEY env var)
├── templates/
│   └── example-survey-spec.json # Example spec (edit and reuse)
├── README.md                   # 中文说明 (Chinese, default)
└── README_EN.md                # English Version
```

## Fallback Chain

Detects: missing `TYPESAFE_API_KEY` / 401 / 402 (insufficient balance) / 429 (rate limit retries exhausted) / network failure. When triggered, clearly tells the user why, then executes their chosen option:

1. **Host agent fallback** — the current agent fills item-by-item using the same profiles (no probability distribution, slower)
2. **No-AI rule engine** — generates copies from profile template answers + fixed-seed pseudo-randomness (zero dependencies, but with noted limitations)

## Result Nature

Output is a **simulated projection derived from the input profiles and proportions**, **not real survey data** — intended for testing/practice/teaching/demos.

## Data Sources

| Source | Purpose |
|--------|---------|
| [TypeSafe API](https://docs.typesafe.ai) | jev decision model (`jev-latest`, System One) |
| [TypeSafe Docs](https://docs.typesafe.ai/llms.txt) | API details (official docs take precedence over this file) |

## License

MIT
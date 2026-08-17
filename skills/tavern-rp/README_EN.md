# Tavern RP — Play SillyTavern Character Cards in Hermes

[English](README_EN.md) | [中文](README.md)

---

## Introduction

**Tavern RP** is a Hermes Agent skill that allows you to load and play SillyTavern character cards (PNG format) directly in Hermes, without needing to run SillyTavern itself.

It parses the `chara_card_v3` data embedded in character cards, extracts character settings, personality, scenario, greetings, world info, and builds a complete role-playing context. It also supports persistent conversation history and context compression.

## Features

| Feature | Description |
|---------|-------------|
| Character Card Loading | Parse SillyTavern PNG/JSON cards, supports `chara_card_v3` spec |
| Auto-detect Card Type | Automatically distinguish character cards vs world cards |
| Placeholder Replacement | Handles `{{user}}` and `{{char}}` placeholders |
| Alternate Greetings | View and switch between multiple greetings |
| World Info Keyword Triggering | Match world info entries by keywords or regex patterns |
| Dialogue Examples | Inject `mes_example` into system prompt |
| Depth Prompt | Support SillyTavern's `depth_prompt` extension |
| Persistent History | Auto-save conversation history to local JSON files |
| Context Compression | Auto-summarize when history exceeds threshold |
| Multi-character Management | Load multiple cards, switch between them |
| Avatar Extraction | Extract avatar PNG from character card |
| Card Export | Pack card data back to PNG for sharing |
| Token Estimation | Estimate token usage of current conversation |

## Quick Start

```bash
# Load a character card
python scripts/rp.py load --card "character.png" --persona "Your Name"

# Send a message
python scripts/rp.py chat "Character Name" "Your message" --role user

# Build full prompt (for agent use)
python scripts/rp.py prompt "Character Name" "User message"

# View conversation history
python scripts/rp.py history "Character Name"

# View/switch alternate greetings
python scripts/rp.py alts "Character Name"
python scripts/rp.py alts "Character Name" --select 2

# One-click replay
python scripts/rp.py replay --card "character.png" --persona "Your Name"
```

## Directory Structure

```
tavern-rp/
├── SKILL.md              # Hermes skill documentation (workflow + commands)
├── README.md             # Chinese README
├── README_EN.md          # English README (this file)
└── scripts/
    ├── parse_card.py     # Card parser (PNG/JSON → JSON)
    └── rp.py             # Roleplay CLI tool
```

Runtime data is stored in `~/.hermes/tavern-rp/` (not committed to repo):
```
~/.hermes/tavern-rp/
├── cards/                # Parsed card JSONs
├── states/               # Conversation state (history)
└── avatars/              # Extracted avatar images
```

## SillyTavern Feature Alignment

- [x] Character card loading (PNG/JSON, chara_card_v3)
- [x] Description / Personality / Scenario / System Prompt / Post-history Instructions
- [x] `{{user}}` and `{{char}}` placeholder replacement
- [x] Alternate greetings (alternate_greetings)
- [x] World info keyword/regex matching
- [x] Dialogue examples (mes_example) injection
- [x] Depth prompt (depth_prompt)
- [x] Character/World card auto-detection
- [x] User persona
- [x] Persistent conversation history
- [x] Context compression
- [x] Avatar extraction
- [x] Token estimation
- [x] Card export
- [ ] Group chat — todo

## License

MIT
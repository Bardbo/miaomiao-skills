# Miaomiao Skills

[中文](./README.md)

> A curated collection of Hermes AI Agent skills, focused on WeChat Official Account (公众号) content creation and AI-assisted workflows.

## Skills

| Skill | Description | SKILL.md |
|-------|-------------|----------|
| [wechat-svg](./skills/wechat-svg/) | Interactive SVG components for WeChat articles — gold egg smash, card flip, scratch card, progress bar, sequence animation, slide layer | ✅ |
| [wechat-chat-simulator](./skills/wechat-chat-simulator/) | Convert dialogue markdown into WeChat-style chat simulator HTML pages | ✅ |
| [travel-plan-html](./skills/travel-plan-html/) | Generate travel plan HTML pages with real-time price queries | ✅ |
| [tavern-rp](./skills/tavern-rp/) | Load SillyTavern character cards for role-playing in Hermes | ✅ |
| [talk](./skills/talk/) | Simulate immersive multi-character dialogue with persona management and context compression | ✅ |
| [smart-pick](./skills/smart-pick/) | Multi-option comparison assistant with dynamic weight generation and external search | ✅ |
| [skill-curator](./skills/skill-curator/) | Comprehensive skill management and continuous improvement system (9-dimension evaluation + optimization engine) | ✅ |

## Structure

```
miaomiao-skills/
├── README.md              ← Chinese (default)
├── README.en.md           ← English
└── skills/
    ├── wechat-svg/            WeChat SVG interactive components
    ├── wechat-chat-simulator/ WeChat chat simulator
    ├── travel-plan-html/      Travel plan HTML
    ├── tavern-rp/             Role-playing
    ├── talk/                  Multi-character dialogue
    ├── smart-pick/            Decision assistant
    └── skill-curator/         Skill management
```

## Usage

Each skill is a standalone Hermes agent skill, containing `SKILL.md` plus optional `references/`, `scripts/`, and `templates/` directories.

### Install into Hermes

```bash
# Copy a skill directory into your Hermes skills folder
cp -r skills/wechat-svg /path/to/hermes/skills/

# Or install via Hermes skill_manage tool
# In a Hermes session: skill_manage(action='install', name='wechat-svg')
```

### Use from Hermes

All skills can be loaded in a Hermes Agent conversation:

```
Hermes > load wechat-svg skill
```

## About

Built by [Bardbo](https://github.com/Bardbo) (WeChat Official Account: 「穿梭在银河的喵喵」) with [Hermes Agent](https://hermes-agent.nousresearch.com).

All skills have been verified in real WeChat Official Account articles.
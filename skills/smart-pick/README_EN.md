# 🧠 Smart-Pick — Universal Multi-Option Decision Assistant

> **Version:** v2.1 | **Status:** Beta | **Darwin Score:** 84.3/100

Smart-Pick is a **fully generic, domain-agnostic** decision-making assistant. Whether you're comparing products, insurance plans, project bids, college applications, or life plans — if you have multiple options to weigh, Smart-Pick helps you make a structured, explainable choice.

## Core Features

| Feature | Description |
|---------|-------------|
| **Dynamic Weights** | Generates weights per session based on scenario features (risk, capital, expertise needs) + user preference history. No hardcoded weights. |
| **OCR Integration** | Built-in PaddleOCR pipeline — extract text from screenshots, insurance policies, and documents automatically |
| **Real-time Price Comparison** | OpenCLI smzdm adapter pulls live prices from JD, PDD, Tmall, Douyin — no login required |
| **Layered Questioning** | Asks 2 critical questions first, then optional follow-ups — never overwhelms the user |
| **Proactive External Search** | Automatically detects when better options may exist, asks before searching |
| **Feedback Learning** | Records user choices over time, adjusts preference vectors — gets smarter with use |
| **Transparent & Intervenable** | All recommendations come with scored comparison tables; user can override weights at any time |

## Workflow (7 Steps)

```
Step 0  Load user profile + generate dynamic weights
Step 1  Identify options & extract comparison dimensions
Step 2  Complete missing info (layered questioning)
Step 3  Personalized weighted scoring
Step 4  External option search (optional)
Step 5  Output recommendation + comparison table
Step 6  Feedback learning → update preference profile
```

## File Structure

```
smart-pick/
├── SKILL.md                        # Core instructions (Hermes Skill format)
├── test-prompts.json               # Darwin-skill test prompts
├── assets/
│   └── output_template.md          # Output format template
├── references/
│   ├── scene_features.md           # Scenario feature → keyword mapping
│   ├── scoring_methods.md          # Scoring algorithm reference
│   ├── examples.md                 # Typical use case examples
│   ├── ocr-integration.md          # OCR + Smart-Pick integration workflow
│   └── opencli-price-source.md     # OpenCLI real-time pricing integration
└── scripts/
    └── search_external.py          # External search (Mock example)
```

## Installation

### As a Hermes Skill

```bash
cp -r smart-pick/ ~/.hermes/skills/productivity/
```

### Standalone

SKILL.md is a self-contained instruction document compatible with any Agent Skills platform (Claude Code, Codex, Cursor, OpenClaw, Hermes).

## Use Cases

- 🛒 **Product Comparison**: phones, laptops, GPUs across multiple e-commerce platforms
- 🚗 **Insurance Plans**: auto, health, life insurance policy comparison
- 📄 **Bid/Project Evaluation**: tender documents, vendor proposals
- 🎓 **College Applications**: school and major selection based on exam scores
- 📈 **Investment Options**: portfolio comparison, financial product evaluation
- 🏠 **Life Decisions**: housing plans, career choices, retirement planning

## Inspirations

- **[Darwin Skill](https://github.com/alchaincyf/darwin-skill)** — Microsoft Research SkillLens (arXiv 2605.23899) + SkillOpt (arXiv 2605.23904) 9-dimension evaluation rubric
- **[Huashu Nuwa Skill](https://github.com/alchaincyf/huashu-nuwa-skill)** — Thought distillation and cognitive framework extraction
- **[Tongshi Skill](https://github.com/niceman/tongshi-skill)** — Workplace knowledge encapsulation paradigm
- **Karpathy autoresearch** — Autonomous experimentation loop with ratchet mechanism

## License

MIT
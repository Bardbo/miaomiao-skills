# Talk — Multi-Character Dialogue Simulation

<p align="center">
  <a href="README.md">🇨🇳 中文</a> · <a href="#readme">🇬🇧 English</a>
</p>

> **⚠️ Beta** — This skill is under active development. API and behavior may change. Issues and PRs welcome.

## Overview

Simulate immersive dialogue between 2+ characters. The Agent follows documented steps (no Python state machine). Features include persona detection pipelines, line-by-line generation, real-time violation constraints, and third-party validation.

This skill's design references the following projects/skills:

- **[huashu-nuwa](https://github.com/Bardbo/miaomiao-skills)** — Skill distillation and creation framework. Talk's persona construction pipeline (local skills → repo search → nuwa distillation → Fallback build) directly inherits from nuwa's source material analysis approach.
- **[darwin-skill](https://github.com/Bardbo/miaomiao-skills)** — 9-dimension evaluation methodology, used for continuous dialogue faithfulness assessment.
- **[skill-curator](https://github.com/Bardbo/miaomiao-skills)** — Comprehensive skill management system, providing lifecycle management reference for talk.
- **[openai-adapter / opencli](https://github.com/OpenInterpreter/open-interpreter)** — Tool invocation interface design patterns that influenced talk's agent-driven execution flow.

## Core Principles

1. **SKILL.md is the state machine** — Agent reads instructions step by step; no Python state machine
2. **Python scripts only do what Agent cannot** — search local skills, detect repos, validate output
3. **Line-by-line generation** — Never generate an entire dialogue in one shot
4. **Pre-constraint + Post-check** — Self-constrain during generation, validate with script afterwards

## Features

| Feature | Description |
|---------|-------------|
| **4-Level Persona Detection** | L1: local skills → L2: repo search → L3: nuwa distillation → L4: Fallback build |
| **Line-by-Line Generation** | One LLM call per line, Agent self-constrains against narration |
| **Real-Time Violation Constraints** | 6.7 realism rules: voice filtering, distance, no death self-narration, material/text density control |
| **Third-Party Validation** | `dialogue_validator.py`: violation detection, pacing check, character coverage metrics |
| **Character Coverage Metrics** | Counts appearances per character to ensure balanced coverage |
| **Scene Title + Disclaimer** | Mandatory generation for dialogue completeness |
| **Fact Checking** | Birthday/nationality/background checks to prevent factual errors |

## File Structure

```
talk/
├── SKILL.md                           # Main skill (execution steps + realism rules)
├── README.md                          # Chinese README
├── README_EN.md                       # This file (English)
├── test-prompts.json                  # Test prompts
├── scripts/
│   ├── persona_detector.py            # Persona detection: local → repos → fallback
│   ├── dialogue_validator.py          # Dialogue validation: violations, pacing, coverage
│   └── gen_dialogue.py                # Dialogue generation helper
├── references/
│   ├── expressive-dna-template.md     # Expression DNA template (persona definition format)
│   ├── hard-constraints-pattern.md    # Hard constraint table pattern (factual bounds)
│   ├── persona-repos.md               # Persona repo search config
│   ├── einstein-fallback.md           # Einstein Fallback example
│   ├── shizhongyuan-fallback.md       # Shizhongyuan characters Fallback example
│   ├── chinese-novel-character-research.md  # Chinese novel character research methodology
│   ├── 神似示例-三人对话.md            # Realism example (Buffett/Munger/Musk)
│   ├── 话题簇-桥接范例.md              # Topic bridging examples
```

## Quick Start

```bash
# 1. Load the skill in Hermes Agent
skill_view(name='talk')

# 2. Follow Step 0–4
#    Step 0: Confirm characters, setting, topic, length
#    Step 1: Character persona detection (4-level pipeline)
#    Step 2: Line-by-line generation
#    Step 3: Third-party validation
#    Step 4: Deliver (with scene title + disclaimer)
```

## Dependencies

- Python 3.9+
- Hermes Agent (requires `terminal`, `skill_view`, `delegate_task` tools)
- Optional: Network connection (for repo search and nuwa distillation)
- Optional: Baidu Baike, Bing, etc. (character research sources)

## Known Issues / Limitations

1. **False Positive Detection** — Validator regex may flag legitimate dialogue (e.g. "你是说", "小说") as narration. Mitigated by gradually expanding `_SAFE_VERB_PATTERNS`.
2. **Coverage Imbalance** — Dominant characters may speak more in free-form dialogue; validator currently counts but does not enforce balance.
3. **Fallback Relies on Search** — Obscure characters require web search or user-supplied material; cannot auto-generate.
4. **Chinese-Centric** — Validator is optimized for CJK dialogue; English false-positive rates may be higher.
5. **Agent Skip Risk** — Line-by-line mode increases turn count; occasionally Agent skips steps and outputs entire dialogue in one shot — requires manual review.

## License

MIT — Free to use, modify, and distribute. Attribution appreciated.
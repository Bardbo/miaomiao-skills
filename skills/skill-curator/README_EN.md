# Skill Curator · Skill Management & Continuous Improvement System

<p align="center">
  <a href="README.md">🇨🇳 中文</a> · <a href="#readme">🇬🇧 English</a>
</p>

> Comprehensive skill management and continuous improvement system — integrates darwin-skill 9-dimension scoring, reference-set best practices, SkillDAG self-evolving skill graphs, **SkillHone persistent decision history**, and **SGDR state-anchored dynamic retrieval**.
>
> Based on Tencent's two papers (SkillHone arXiv:2606.08671 + SGDR arXiv:2606.04391).

## Features

| Feature | Description |
|---------|-------------|
| **SKILL Dashboard** | Statistics on installation count, health scores, category distribution at a glance |
| **Health Assessment** | Baseline evaluation using darwin-skill 9-dimension rubric with tiered warnings |
| **Optimization Pipeline** | Identify weak skills, draw experience from reference sets, auto-optimize |
| **Lifecycle Management** | Evaluate → Optimize → Archive → Remove automated, periodic cleanup beats constant accumulation |
| **SkillDAG Skill Graph** | 5 edge types track skill relationships, Agent autonomously edit and evolve |
| **Auto Installation Decision** | Discover high-value new skills → self-evaluate and install |
| **Persistent Decision History (PDH)** | Records quadruple (diagnosis/candidates/evidence/result) per change, prevents repeated trial-and-error |
| **Role Isolation** | Optimizer and evaluator permissions separated, prevents "cheating on answers" |
| **Targeted Regression Repair** | Precisely patch degraded parts only, preserve useful edits, no full rollback |
| **SGDR Dynamic Retrieval** | Re-select optimal skills each step using dual-signal (task+state) + MMR dedup |
| **Knowledge Base Maintenance** | Regular skill knowledge base audits using llm-wiki.skill architecture |

## Auto-Management Authority

User has authorized skill-curator to make autonomous decisions:

- Discover high-value new skills → self-evaluate and install to appropriate category
- Discover better solutions in reference sets → evaluate differences, optimize existing or install alternatives
- Run baseline scores periodically → auto-log to `evaluation.md`
- Discover issues during execution → immediate optimization fixes
- Discover skill relationships during execution → auto-edit SkillDAG edges
- Knowledge base (including skill library) regularly audited using llm-wiki.skill
- Users only need to review results reports, no per-decision manual approval required

## Usage

Skill Curator is a skill for **Hermes Agent**, executes immediately upon loading:

```bash
# Install to Hermes Agent
cp -r skill-curator ~/.hermes/skills/

# Trigger in conversation
# Say: "skill management", "skill dashboard", "evaluate all skills"
# "optimize which skills", "skill quality check", "skill relationships", "skill graph"
# "PDH", "decision history", "role isolation", "directed repair", "dynamic retrieval", "SGDR"
```

## Dependencies

| Component | Purpose |
|-----------|---------|
| **darwin-skill** | 9-dimension scoring engine + optimization loop |
| **meta-skill-orchestrator** | Workflow orchestration framework |
| **huashu-nuwa** | New skill distillation and creation |
| **SkillDAG paper** | Self-evolving skill graph methodology |
| **SkillHone paper** | Persistent decision history + role isolation + targeted repair |
| **SGDR paper** | State-anchored dynamic retrieval + MMR dedup |
| **llm-wiki** | Knowledge base (incl. skill library) maintenance |

## Project Structure

```
skill-curator/
├── SKILL.md                         # Skill definition and full pipeline (v2.0.0)
├── README.md                        # Chinese README
├── README_EN.md                     # This file
├── decision_log/
│   └── index.json                   # PDH persistent decision history index
├── references/
│   ├── baseline-methodology.md      # Evaluation methodology and scoring details
│   ├── collection-evaluation.md     # Reference-set evaluation report
│   ├── knowledge-base-consolidation-workflow.md  # Knowledge base maintenance workflow
│   ├── skillhone-sgdr-notes.md      # SkillHone & SGDR paper notes
│   └── ppt-master-pipeline-notes.md # PPT generation pipeline notes
└── scripts/
    ├── dag_audit.py                 # SkillDAG auto-audit script (cron)
    ├── sync-skill-to-git.py         # Skill → Git sync helper
    └── gbrain-ensure-server.py      # gbrain GPU embedding server management
```

## License

MIT

---

> Generated with assistance from [Hermes Agent](https://hermes-agent.nousresearch.com/).
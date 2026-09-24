# resume-tailor · AI Resume Optimization & JD-Tailoring Skill

> 🌐 Bilingual: [中文](README.md)

Helps users turn their **real experience** into a maintainable **master resume**, then derive **company/role-specific versions** from it. Makes a resume more competitive *without drift from the truth* — **filter only, never fabricate**.

---

## What it does (three capabilities)

| Capability | Description | Status |
|---|---|---|
| **① Audit a resume** | Diagnose missing facts, AI-taste wording, weak interview-defensibility, bad layout | ✅ Ready to use (strongest part) |
| **② Optimize & polish** | Rewrite phrasing, strip AI-taste, strengthen quantification & defensibility | 🟡 Usable; ship docx to deliver |
| **③ Tailor to a JD** | Select / reorder / refocus entries against a real job description | ✅ End-to-end proven (李四 → J1) |

**The only deliverable is the resume itself.** Civil-service exams (no resume submitted), job hunting, interview coaching, and career planning are out of scope.

---

## Core stance

> **Filter only, never fabricate.** Nothing absent from the master ever appears in any tailored version.

"Impressive" does not come from invented facts. It comes from three fact-preserving moves: **translate** (jargon → industry terms), **focus** (what I did → what problem I solved), **elevate** (execution layer → solution layer). The facts are unchanged; only the reading changes — that is the legal packaging space, and the entire value of this Skill.

Anti-fabrication is enforced by the **Gate chain G1–G6** (below). G1 traceability / G2 evidence / G3 JD coverage / G4 de-AI-taste are hard-checked by scripts — rules written as prompts get bypassed by LLMs; rules written in code do not.

---

## Directory layout

```
<your workspace>/                # Where user data lives (skill upgrades never touch it)
└── people/
    ├── _template/               # Templates (created by init; copy, do not edit)
    ├── _jd/                     # JD library (multiple roles)
    └── <name>/
        ├── master.yaml          # Master — single source of truth
        ├── sources/             # Raw materials (append-only, never edited)
        ├── targets/<track>/      # Per-role tailoring (tailored.yaml + jd_snapshot)
        └── output/              # Rendered artifacts (html/docx/pdf)

resume-tailor/                   # Skill body (self-contained; copy anywhere)
├── SKILL.md                     # Full methodology & workflow
├── requirements.txt             # Dependency manifest
├── assets/                      # Bundled templates + flat blocklist (for G4)
├── config/                      # Shared config across people (not copied per person)
│   ├── forbidden_terms.txt      # Chinese AI-taste blocklist (graded, for lint)
│   └── tech_terms.txt           # Tech term dictionary
├── references/                  # 9 playbooks: schema / intake / mining / polish / jd / company / rewrite / gate / writeback
└── scripts/
    ├── resume.py                # Entry point (init/people/new/check/lint/preview/render)
    ├── validate_master.py       # Validate + preview
    ├── density.py               # Page-fill engine (A4 capacity model)
    ├── polish.py                # Bullet audit (L0–L3)
    ├── render_resume.py         # Render: YAML → HTML (single source)
    ├── analyze_jd.py            # JD parsing & gap comparison
    ├── check_gates.py           # G1–G4 hard checks
    ├── export_docx.py           # HTML → text-layer .docx (ATS-parseable)
    ├── export_pdf.py            # HTML → text-layer .pdf
    ├── export_pdf.js            # node playwright + chromium real print
    └── measure_pages.js         # Browser-measured page count
```

> **Package / workspace split**: `resume-tailor/` is a **read-only package** you can copy anywhere (scripts / config / assets / references all live inside, resolved from the script's own location);
> `people/` is **your data**, kept in your own workspace. **Upgrading or reinstalling the skill never wipes client resumes**, and one skill can serve multiple workspaces.

---

## Installation

### 1. Put the skill package in place
`resume-tailor/` is self-contained (scripts, config, assets and references all live inside; paths resolve from the script's own location), so it runs from anywhere.
```bash
# Option A: install as a WorkBuddy Skill
cp -r resume-tailor ~/.workbuddy/skills/

# Option B: keep it inside your project and run it directly (this repo's current shape)
```

### 2. Install dependencies
```bash
pip install -r resume-tailor/requirements.txt     # PyYAML + python-docx (required)

# Optional: PDF rendering / measured page count needs node + playwright
npm install playwright && npx playwright install chromium
# If playwright is elsewhere: export NODE_PATH=<path to node_modules>
```
> Playwright is optional: docx export and the estimated page-fill diagnosis work without it.

### 3. Initialize a workspace
Run once inside the directory where you want to keep resumes (creates `people/` and drops the bundled templates into `people/_template/`):
```bash
python <pkg-path>/resume-tailor/scripts/resume.py init
```

### Unified interpreter (PyYAML / python-docx already installed)
```
# Windows (isolated venv)
%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe
# macOS / Linux
~/.workbuddy/binaries/python/envs/default/bin/python
```
Extracting text from an old PDF resume (Phase 0 import) additionally needs `pip install pymupdf`; paths resolve dynamically — never hardcode a username.

> **Path convention**: run commands from the **workspace directory that contains `people/`**, invoking scripts as `resume-tailor/scripts/xxx.py` (relative or absolute).
> `people/` defaults to `./people` under the current directory; override with the `RESUME_WORKSPACE` environment variable.
> **Never hardcode another person's master path into a script or doc default.**

---

## Quick start

```bash
# —— Unified entry (omit --person to auto-select when only one person) ——
python resume-tailor/scripts/resume.py people                      # list people & master versions
python resume-tailor/scripts/resume.py new     --person ZhangSan    # create from template
python resume-tailor/scripts/resume.py check   --person LiuJingbo   # validate (G1/G2/G4)
python resume-tailor/scripts/resume.py lint    --person LiuJingbo   # AI-taste scan only
python resume-tailor/scripts/resume.py preview --person LiuJingbo   # read-only Markdown preview
python resume-tailor/scripts/resume.py render  --person LiuJingbo --mode draft|final

# —— Density & polish (density first, polish next, tailoring last) ——
python resume-tailor/scripts/density.py --person LiuJingbo          # page-fill diagnosis (estimate)
python resume-tailor/scripts/density.py --person LiuJingbo --measure # page-fill (browser-measured, pre-render)
python resume-tailor/scripts/polish.py  --person LiuJingbo          # bullet audit & rewrite direction

# —— Tailor to JD (Phase 2 → Phase 4 check → render) ——
python resume-tailor/scripts/analyze_jd.py people/_jd/J1-校招技术.md \
    --master people/ChenSiyuan/master.yaml --emit targets/J1-校招软件研发/analysis.yaml
python resume-tailor/scripts/check_gates.py \
    --master people/ChenSiyuan/master.yaml \
    --target people/ChenSiyuan/targets/J1-校招软件研发/tailored.yaml \
    --rendered people/ChenSiyuan/output/resume-J1-校招软件研发-draft.html

# —— Render (text-layer, ATS-parseable) ——
python resume-tailor/scripts/export_docx.py --person ChenSiyuan --target targets/J1-校招软件研发/tailored.yaml --mode draft
python resume-tailor/scripts/export_pdf.py  --person ChenSiyuan --target targets/J1-校招软件研发/tailored.yaml --mode draft
```

> Do not deliver PNG screenshots of HTML — no text layer, ATS cannot parse them.

---

## Gate chain (G1–G6)

| Gate | Checks | On failure |
|---|---|---|
| **G1 Traceability** | can each bullet trace to a master entry ID | untraceable = L4 violation, reject |
| **G2 Evidence** | are `pending`/`inferred` written as certain | downgrade to "involved" or mark `【待补】` |
| **G3 Coverage** | P1/P2/P3 keyword hit-rate in **rendered** output | misses → gaps; P1 miss = hard gap |
| **G4 De-AI-taste** | blocklist words + phrasing | forced rewrite |
| **G5 Reverse interview** | does each bullet survive 3 layers of追问 | downgrade or delete if not |
| **G6 Layout** | docx/PDF render check | reject if layout fails |

G1/G2/G3/G4 are hard-checked by `check_gates.py`; G5/G6 need manual/script review before delivery.

**`evidence` five tiers (enforced by render, unaffected by profile/polish)**

| Tier | Meaning | In resume? |
|---|---|---|
| `verified` | third-party verifiable (patent/paper/public record) | ✅ strong claims kept |
| `self_reported` | explicitly stated by the person | ✅ writable, not downgraded |
| `pending` | incomplete, awaiting input | ⚠️ hidden on render, less is more |
| `inferred` | AI inference | ❌ forbidden in master |
| `unusable` | confidential / owned by other party | ❌ forbidden in any tailored version |

---

## Two prerequisite parameters

| Dim | Governs | Values |
|---|---|---|
| **`profile`** persona | which materials kept, section order, skill convergence | `campus` / `junior` / `experienced`(default) / `expert` |
| **`polish`** packaging level | how far a fact is pushed | `sincere` / `balanced`(default) / `bold` |

profile is a filter, polish is an amplifier — an amplifier cannot amplify what was not selected; polish cannot unlock evidence limits.

---

## Publish status

**Ready for self-use client work.** This repo is the publish-ready form of the skill: it contains **no real resume data** (`people/` is the user's workspace data, created by the `init` command and never shipped with the repo).

---

## Reference files

| File | Content |
|---|---|
| `resume-tailor/SKILL.md` | Full methodology & workflow (must-read) |
| `resume-tailor/references/schema.md` | Master & tailored field spec |
| `resume-tailor/references/gate-checklist.md` | G1–G6 itemized checks |
| `resume-tailor/references/polish-playbook.md` | Bullet four-tier model & rewrite |
| `resume-tailor/references/mining-playbook.md` | Material mining |
| `resume-tailor/references/rewrite-rules.md` | Persona / packaging / Chinese writing rules |

# Pre-Publish Security Scan Script

Reusable script for checking skill directories before publishing to SkillHub, GitHub, or sharing externally.

## Usage

```python
import os, re

# 1. Set the base path to the skill directory
base = os.path.expanduser("~/AppData/Local/hermes/skills/<category>/<skill-name>/")

# 2. Run scan
checks = {
    "绝对路径": r'(?:C:\\Users|D:\\Documents)',
    "用户Home路径": r'~/.hermes/skills/[a-z]+/[a-z-]+/SKILL\.md',
    "内网IP": r'\b(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)\b',
    "邮箱": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "端口号": r'\b(?:3200|54321|3000|9128|11434|9999|14013|14023|18888)\b',
    "GitHub username": r'Bardbo',
    "SSH私钥": r'-----BEGIN.*PRIVATE KEY',
    "API Key/Token": r'(?:api[_-]?key|token|secret|password|credential)[^a-zA-Z]',
}

for root, dirs, files in os.walk(base):
    for fname in files:
        fpath = os.path.join(root, fname)
        relpath = os.path.relpath(fpath, base)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        for name, pattern in checks.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"  {relpath} | {name}: {set(matches)[:5]}")
```

## Files to scan
- SKILL.md — main documentation
- references/*.md — may contain paths, examples, notes
- scripts/*.py — may contain hardcoded paths, configs
- decision_log/*.json — check before publishing if includes internal structure

## Decision
- Only scan markdown and Python files by default (covers 99% of cases)
- JSON files in decision_log/ may contain internal references — review manually
- .gitignore / .publish manifests should specify which files are safe to publish
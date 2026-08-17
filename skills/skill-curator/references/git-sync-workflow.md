# Git 同步工作流

> 优化一个 skill 后，如果它有对应的 Git 项目（在 `D:/Documents/Obsidian Vault/我的Git项目/<skill-name>/`），
> 必须同步优化结果到 Git 项目并更新 README。

## 执行步骤

### 1. 运行同步脚本

```bash
cd ~/AppData/Local/hermes/skills/software-development/skill-curator/
python scripts/sync-skill-to-git.py <skill-name> --push
```

`--push` 会自动推送到 GitHub。如果网络不通，不加 `--push` 只做本地 commit。

### 2. 更新 README

同步脚本只同步 SKILL.md + 引用文件，**不会自动更新 README.md 和 README_EN.md**（它们是 skill 目录外的独立维护文件）。

优化后必须手动检查：

| 检查项 | 说明 |
|--------|------|
| 功能表 | README.md 的「它能做什么」表格是否包含新功能？ |
| 依赖表 | 是否有新的依赖需添加到「依赖」表？ |
| 触发词 | 是否新增了触发词需同步到「使用方式」？ |
| 项目结构 | 是否新增了目录/文件需更新「项目结构」？ |
| README_EN.md | 同上，英文版同步更新 |

### 3. 提交并推送

```bash
cd "D:/Documents/Obsidian Vault/我的Git项目/<skill-name>"
git add -A
git commit -m "docs: update README for new feature"
git push
```

## Pitfalls

- **不要在 Windows CMD 下用 `VAR=value git push` 语法** — 这是 bash 语法，Windows CMD 不识别。
  改用以下任一方式：
  - 直接 `git push`（PATH 中有 git-bash 的 git 即可）
  - 或用 `git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 push`（git 的自身配置覆盖语法，跨 shell 兼容）
- **git push 网络不通时不阻塞** — 本地 commit 已完成，push 失败不丢失任何变更。用户知道网络问题时会自己处理。
- **README 不会自动同步** — 这是有意的。README.md/README_EN.md 在 git 项目中是独立维护的，sync 脚本会特意保留它们不被 SKILL.md 覆盖。
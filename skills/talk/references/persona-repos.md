# 人格技能仓库索引

## 已验证的有效仓库

### awesome-ai-persona-skills
- **地址**: https://github.com/momozi1996/awesome-ai-persona-skills
- **内容**: 100+ 中文人格 Skill 合集，覆盖名人、作家、古籍、二次元等
- **镜像**: ghproxy.net

### 名人独立 Skill 仓库

| 仓库 | 地址 | 说明 |
|------|------|------|
| munger-skill | `alchaincyf/munger-skill` | 查理·芒格思维操作系统 |
| buffett-skill | `alchaincyf/buffett-skill` | 沃伦·巴菲特 |
| feynman-perspective | `alchaincyf/feynman-perspective` | 理查德·费曼 |
| taleb-perspective | `alchaincyf/taleb-perspective` | 纳西姆·塔勒布 |
| naval-perspective | `alchaincyf/naval-perspective` | Naval Ravikant |
| musk-perspective | `alchaincyf/musk-perspective` | 伊隆·马斯克 |

### huashu-nuwa（女娲造人）
- **地址**: https://github.com/alchaincyf/nuwa-skill（已迁移至本地 skill: `huashu-nuwa`）
- **用途**: 为无人格 skill 的角色蒸馏生成人格定义
- **本地路径**: `~/.hermes/skills/huashu-nuwa/`

## 本机已安装的人格 Skill（本地检测用）

运行 `persona_detector.py detect` 会自动搜索 `~/.hermes/skills/` 目录。

## 搜索策略

1. 本地 `~/.hermes/skills/` 目录搜索
2. awesome-ai-persona-skills 总列表
3. 名人独立 skill 仓库（`{name}-skill` / `{name}-perspective`）
4. huashu-nuwa 蒸馏（需要用户确认）
5. Fallback 构建

## 网络代理

所有 GitHub 请求通过以下镜像：
- `https://ghproxy.net/https://raw.githubusercontent.com/...`
- `https://ghproxy.io/https://raw.githubusercontent.com/...`
- `https://raw.githubusercontent.com/...`（直连，最后一个尝试）
# Tavern RP — 在 Hermes 里玩酒馆角色卡

[English](README_EN.md) | [中文](README.md)

---

## 简介

**Tavern RP** 是一个 Hermes Agent 技能（Skill），让你在 Hermes 中直接加载 SillyTavern 角色卡（PNG 格式）进行角色扮演，无需启动 SillyTavern 本体。

它解析角色卡中的 `chara_card_v3` 格式数据，提取角色设定、人格、场景、开场白、世界书等信息，构建完整的角色扮演上下文，并支持对话历史的持久化存储和上下文压缩。

## 功能

| 功能 | 说明 |
|------|------|
| 角色卡加载 | 解析 SillyTavern PNG/JSON 角色卡，支持 `chara_card_v3` 规范 |
| 角色卡/世界卡自动识别 | 自动判断卡片类型，世界卡会提示用户设置角色名 |
| 占位符替换 | 自动处理 `{{user}}` 和 `{{char}}` 占位符 |
| 备用开场白 | 查看和切换角色卡的多个开场白 |
| 世界书关键词触发 | 根据对话内容匹配世界书条目，支持正则表达式 |
| 对话示例注入 | 将角色卡的对话示例注入到 system prompt 中 |
| 深度提示 | 支持 SillyTavern 的 depth_prompt 扩展 |
| 对话历史持久化 | 对话记录自动保存到本地 JSON 文件 |
| 上下文压缩 | 对话历史超过阈值时自动摘要压缩 |
| 多角色管理 | 支持加载多个角色卡，随时切换 |
| 头像提取 | 从角色卡中提取头像 PNG |
| 角色卡导出 | 将角色数据打包回 PNG 文件，便于分享 |
| Token 估算 | 估算当前对话的 token 用量 |

## 快速开始

```bash
# 加载角色卡
python scripts/rp.py load --card "角色卡.png" --persona "你的角色名"

# 开始对话（记录用户消息）
python scripts/rp.py chat "角色名" "你的消息" --role user

# 构建完整 prompt（供 agent 使用）
python scripts/rp.py prompt "角色名" "用户消息"

# 查看对话历史
python scripts/rp.py history "角色名"

# 查看/切换备用开场白
python scripts/rp.py alts "角色名"
python scripts/rp.py alts "角色名" --select 2

# 一键重玩
python scripts/rp.py replay --card "角色卡.png" --persona "你的角色名"
```

## 目录结构

```
tavern-rp/
├── SKILL.md              # Hermes 技能说明（工作流 + 命令参考）
├── README.md             # 本文件（中文）
├── README_EN.md          # 英文说明
└── scripts/
    ├── parse_card.py     # 角色卡解析脚本（PNG/JSON → JSON）
    └── rp.py             # 角色扮演核心逻辑（CLI）
```

运行时数据存储在 `~/.hermes/tavern-rp/`（不会提交到仓库）：
```
~/.hermes/tavern-rp/
├── cards/                # 解析后的角色卡 JSON
├── states/               # 对话状态（历史记录）
└── avatars/              # 提取的角色头像
```

## 与 SillyTavern 功能对齐

- [x] 角色卡加载 (PNG/JSON, chara_card_v3)
- [x] 角色描述 / 人格 / 场景 / 系统提示词 / 后指令
- [x] `{{user}}` 和 `{{char}}` 占位符替换
- [x] 备用开场白 (alternate_greetings)
- [x] 世界书 (character_book) 关键词/正则触发
- [x] 对话示例 (mes_example) 注入
- [x] 深度提示 (depth_prompt)
- [x] 角色卡/世界卡自动检测
- [x] 用户身份 (Persona)
- [x] 对话历史持久化
- [x] 上下文压缩
- [x] 头像提取
- [x] Token 估算
- [x] 角色卡导出
- [ ] 群聊 (Group Chat) — 待实现

## 许可证

MIT
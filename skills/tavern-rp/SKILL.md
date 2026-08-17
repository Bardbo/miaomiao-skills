---
name: tavern-rp
description: "在 Hermes 中加载 SillyTavern 角色卡进行角色扮演。支持换卡、记忆持久化、上下文压缩、世界书关键词触发。"
tags: [sillytavern, rp, roleplay, character-card, world-book]
---

# Tavern RP — 在 Hermes 里玩酒馆角色卡

## 功能总览

| 功能 | SillyTavern | tavern-rp | 说明 |
|------|:-----------:|:---------:|------|
| 角色卡加载 (PNG/JSON) | ✅ | ✅ | 支持 chara_card_v3 |
| {{user}} 占位符 | ✅ | ✅ | 替换为用户角色名 |
| {{char}} 占位符 | ✅ | ✅ | 替换为角色卡名称 |
| 备用开场白切换 | ✅ | ✅ | `alts --select N` |
| 世界书关键词触发 | ✅ | ✅ | 根据对话内容匹配关键词 |
| 对话示例 (mes_example) | ✅ | ✅ | 注入 system prompt |
| 深度提示 (depth_prompt) | ✅ | ✅ | 来自 extensions |
| 角色卡/世界卡检测 | ✅ | ✅ | 自动判断 |
| 多角色管理 | ✅ | ✅ | `list` 列出所有角色 |
| 对话历史持久化 | ✅ | ✅ | JSON 文件存储 |
| 上下文压缩 | ✅ | ✅ | 超阈值自动摘要 |
| 头像提取 | ✅ | ✅ | `avatar` 命令 |
| Token 估算 | ✅ | ✅ | `tokens` 命令 |
| 筛选/搜索 | ✅ | ✅ | `list --filter` |
| 用户身份 (Persona) | ✅ | ✅ | `--persona` 参数 |
| 群聊 (Group Chat) | ❌ | ❌ | 暂不支持 |
| 正则世界书触发 | ❌ | ✅ | 关键词以 `/` 包围即为正则 |
| 角色卡导出 | ❌（仅手动） | ✅ | `export` 命令打包为 PNG |
| 角色卡删除 | ✅ | ✅ | `delete` 命令 |

## 卡片类型

| 类型 | 检测方式 | 行为 |
|------|---------|------|
| **角色卡** | 人格中无世界卡关键词 | Agent 扮演该角色 |
| **世界卡** | 人格含 `推进<user>剧情`/`narrator`/`旁白` 等 | Agent 扮演叙事者，用户需指定角色名 |

## 角色卡格式

数据以 base64 编码嵌入 PNG 的 `tEXt` 块（key=`chara`）。

核心字段详见 `scripts/parse_card.py`。

## 命令参考

### 基础命令

```bash
# 加载角色卡
python rp.py load --card "<路径>" --persona "<角色名>"

# 列出已加载的角色
python rp.py list
python rp.py list --filter "宝可梦"    # 按名称/标签筛选

# 查看角色卡信息
python rp.py info "<角色名>"

# 查看/切换备用开场白
python rp.py alts "<角色名>"           # 列出所有开场白
python rp.py alts "<角色名>" --select 2  # 切换到第 2 个

# 提取头像
python rp.py avatar "<角色名>"
python rp.py avatar "<角色名>" --output "C:/path/to/avatar.png"

# 导出角色卡为 PNG（可分享）
python rp.py export "<角色名>"
python rp.py export "<角色名>" --output "C:/path/to/card.png"

# 删除角色卡及其所有数据
python rp.py delete "<角色名>"          # 确认模式
python rp.py delete "<角色名>" --force  # 直接删除
```

### 对话命令

```bash
# 记录对话
python rp.py chat "<角色名>" "<消息>" --role user      # 用户消息
python rp.py chat "<角色名>" "<回复>" --role assistant  # 助手回复

# 输出完整 prompt（供 agent 直接使用）
python rp.py prompt "<角色名>" "<用户消息>"

# 查看历史
python rp.py history "<角色名>"          # 截断显示
python rp.py history "<角色名>" --full   # 完整显示

# 估算 token 用量
python rp.py tokens "<角色名>"
```

### 管理命令

```bash
# 触发摘要压缩
python rp.py summary "<角色名>"          # 至少 6 条历史才压缩
python rp.py summary "<角色名>" --force  # 强制压缩

# 重置对话
python rp.py reset "<角色名>"

# 一键重玩（重置+加载）
python rp.py replay --card "<路径>" --persona "<角色名>"
```

## Agent 工作流

### 加载角色卡

1. 执行 `load --card <路径> [--persona <角色名>]`
2. 检查输出中的 `card_type`（角色卡/世界卡）
3. 如果是世界卡且用户未提供 persona，**必须询问用户扮演的角色名**
4. 检查 `turn_count` > 0？询问用户「继续还是重玩」

### 开始角色扮演

1. 用 `render_first_mes()` 渲染开场白（替换 `{{user}}` `{{char}}`）
2. 立即以角色身份输出开场白，进入角色扮演状态
3. 用户不说退出就不结束

### 每轮对话

1. 用户发消息 → `chat <名> "<消息>" --role user`
2. 用 `prompt <名> "<消息>"` 获取完整 system prompt + 历史
3. 以角色身份回复
4. 助手回复 → `chat <名> "<回复>" --role assistant`
5. 注意 `chat` 输出中的压缩提示，需要时执行 `summary`

### 世界书关键词触发

`prompt` 命令自动根据用户消息中的关键词匹配世界书条目，只注入相关条目到 system prompt 中，避免浪费 token。

### 上下文压缩

- 当 `history` 超过 30 条时，`chat` 命令会提示压缩
- 执行 `summary <名>` 压缩最早的一半对话为摘要
- 压缩后保留最近部分，摘要自动追加到 system prompt

### 换卡/重玩

- 换卡：直接 `load` 新卡即可，旧卡状态自动保存
- 重玩：`replay --card <路径> --persona <名>` 一键重置+加载

## 世界书关键词匹配算法

`match_world_entries(character_book, text)` 函数：
1. 遍历世界书所有条目
2. 对每个条目的 `keys` 数组，检查是否有任何关键词出现在用户消息中
3. 返回所有匹配的条目
4. 仅匹配的条目被注入到 system prompt

## 所有与 SillyTavern 对齐的功能

- [x] 角色卡加载 (PNG/JSON, chara_card_v3)
- [x] {{user}} 和 {{char}} 占位符替换
- [x] 角色描述 / 人格 / 场景 / 系统提示词 / 后指令
- [x] 备用开场白 (alternate_greetings)
- [x] 世界书 (character_book) 关键词触发
- [x] 对话示例 (mes_example) 注入
- [x] 深度提示 (depth_prompt)
- [x] 创作者备注 / 版本 / 标签
- [x] 角色卡/世界卡自动检测
- [x] 用户身份 (Persona)
- [x] 对话历史持久化
- [x] 上下文压缩
- [x] 头像提取
- [x] Token 估算
- [x] 搜索/筛选
- [x] 正则表达式世界书触发 — 关键词以 `/` 包围
- [x] 角色卡导出 — `export` 命令打包 JSON→PNG
- [x] 角色卡删除 — `delete` 命令（含 --force）
- [ ] 群聊 (Group Chat) — 待实现
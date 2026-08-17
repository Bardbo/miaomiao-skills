#!/usr/bin/env python3
"""
酒馆角色扮演核心逻辑 — 与 SillyTavern 原生功能对齐。

用法：
  python rp.py load --card <路径> [--persona <角色名>]     # 加载角色卡
  python rp.py list [--filter <关键词>]                    # 列出角色卡
  python rp.py chat <角色名> "<消息>" [--role user|assistant]  # 记录对话
  python rp.py prompt <角色名> "<用户消息>"                  # 输出完整 prompt
  python rp.py history <角色名> [--full]                   # 查看对话历史
  python rp.py alts <角色名> [--select <序号>]              # 查看/切换开场白
  python rp.py info <角色名>                               # 查看角色卡信息
  python rp.py summary <角色名> [--force]                  # 触发摘要压缩
  python rp.py reset <角色名>                              # 重置对话
  python rp.py replay --card <路径> [--persona <角色名>]    # 重置并重玩
  python rp.py avatar <角色名> [--output <路径>]            # 提取头像
  python rp.py tokens <角色名>                             # 估算 token 用量
"""

import json
import os
import sys
import argparse
import base64
import re
import struct
import zlib
import math
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.expanduser('~/.hermes/tavern-rp')
CARDS_DIR = os.path.join(BASE_DIR, 'cards')
STATES_DIR = os.path.join(BASE_DIR, 'states')
AVATARS_DIR = os.path.join(BASE_DIR, 'avatars')
MAX_HISTORY_PAIRS = 50
COMPRESSION_THRESHOLD = 30


def ensure_dirs():
    for d in [CARDS_DIR, STATES_DIR, AVATARS_DIR]:
        os.makedirs(d, exist_ok=True)


# ========== PNG 解析 ==========

def parse_png_card(filepath):
    """从 PNG 文件中提取角色卡 JSON 和头像数据"""
    avatar_data = None
    with open(filepath, 'rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Not a valid PNG file')

        # 先读取所有块，提取 chara 和头像
        chunks = []
        while True:
            header = f.read(8)
            if len(header) < 8:
                break
            length = int.from_bytes(header[:4], 'big')
            chunk_type = header[4:8]
            data = f.read(length)
            crc = f.read(4)
            chunks.append((chunk_type, data, crc))

            if chunk_type == b'IEND':
                break

        card_data = None
        for ctype, data, _ in chunks:
            if ctype == b'tEXt':
                null_pos = data.find(b'\x00')
                if null_pos < 0:
                    continue
                keyword = data[:null_pos].decode('latin-1')
                text = data[null_pos + 1:].decode('latin-1')
                if keyword == 'chara':
                    try:
                        card_data = json.loads(base64.b64decode(text))
                    except Exception:
                        card_data = json.loads(text)

        if not card_data:
            raise ValueError('No chara chunk found in PNG')

        # 提取头像（IHDR 之后的第一个 IDAT 块之前的 tEXt 块标记的头像区域）
        # 实际上，SillyTavern 角色卡的头像是 PNG 本身，我们可以直接复制
        with open(filepath, 'rb') as f2:
            avatar_data = f2.read()

        return card_data, avatar_data


def parse_json_card(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f), None


# ========== 占位符处理 ==========

def render_text(text, persona, char_name):
    """替换文本中的 {{user}}、{{char}} 占位符"""
    if not text:
        return text
    text = text.replace('{{user}}', persona or '你')
    text = text.replace('{user}', persona or '你')
    text = text.replace('{{char}}', char_name)
    text = text.replace('{char}', char_name)
    return text


def render_first_mes(card, persona):
    """渲染开场白"""
    first_mes = card['data'].get('first_mes', '')
    return render_text(first_mes, persona, card['data']['name'])


# ========== 卡片类型检测 ==========

def detect_card_type(card_data):
    """判断卡片类型：角色卡 / 世界卡"""
    d = card_data.get('data', card_data)
    personality = (d.get('personality') or '').lower()
    description = (d.get('description') or '').lower()
    combined = personality + ' ' + description
    is_world = any(kw in combined for kw in [
        '推进user', '推进剧情', '推进<user>', 'narrator',
        '不参与', '叙述者', '旁白', '世界观'
    ])
    return 'world' if is_world else 'character'


# ========== 世界书关键词匹配 ==========

def match_world_entries(character_book, text):
    """根据对话内容匹配世界书条目，支持关键词和正则表达式。

    SillyTavern 世界书条目可以设置：
    - 关键词匹配（默认）：关键词出现在文本中即匹配
    - 正则匹配：如果关键词以 // 开头和结尾，则作为正则表达式处理
    """
    if not character_book or not character_book.get('entries'):
        return []
    matched = []
    for entry in character_book['entries']:
        keys = entry.get('keys', [])
        for key in keys:
            if not key:
                continue
            # 正则模式：关键词以 / 开头和结尾
            if key.startswith('/') and key.endswith('/'):
                try:
                    pattern = key[1:-1]
                    if re.search(pattern, text, re.IGNORECASE):
                        matched.append(entry)
                        break
                except re.error:
                    # 正则无效，回退到关键词匹配
                    if key.lower() in text.lower():
                        matched.append(entry)
                        break
            else:
                # 关键词匹配（SillyTavern 默认行为）
                if key.lower() in text.lower():
                    matched.append(entry)
                    break
    return matched


# ========== Token 估算 ==========

def estimate_tokens(text):
    """粗略估算 token 数"""
    if not text:
        return 0
    # 中文字符约 1.5 tokens/字
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    # 英文单词约 1.3 tokens/词
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    # 数字
    digits = len(re.findall(r'\d+', text))
    # 其他（标点、空格等）
    other = len(text) - chinese_chars - sum(len(w) for w in re.findall(r'[a-zA-Z]+', text))
    return int(chinese_chars * 1.5 + english_words * 1.3 + digits * 0.5 + other * 0.3)


# ========== 加载角色卡 ==========

def load_card(card_path, persona=None):
    """加载角色卡"""
    ext = os.path.splitext(card_path)[1].lower()
    if ext == '.png':
        card_data, avatar_data = parse_png_card(card_path)
    else:
        card_data, avatar_data = parse_json_card(card_path)

    d = card_data.get('data', card_data)
    name = d.get('name', '未知角色')
    safe_name = name.replace(' ', '_').replace('/', '_')
    card_type = detect_card_type(card_data)

    output = {
        'spec': card_data.get('spec', 'unknown'),
        'spec_version': card_data.get('spec_version', '1.0'),
        'source_file': os.path.basename(card_path),
        'source_path': os.path.abspath(card_path),
        'card_type': card_type,
        'data': {
            'name': name,
            'description': d.get('description', ''),
            'personality': d.get('personality', ''),
            'scenario': d.get('scenario', ''),
            'first_mes': d.get('first_mes', ''),
            'mes_example': d.get('mes_example', ''),
            'creator_notes': d.get('creator_notes', ''),
            'system_prompt': d.get('system_prompt', ''),
            'post_history_instructions': d.get('post_history_instructions', ''),
            'tags': d.get('tags', []),
            'creator': d.get('creator', ''),
            'character_version': d.get('character_version', ''),
            'alternate_greetings': d.get('alternate_greetings', {}),
            'extensions': d.get('extensions', {}),
            'character_book': d.get('character_book', None),
            'talkativeness': d.get('talkativeness', 0.5),
        }
    }

    # 保存角色卡 JSON
    os.makedirs(CARDS_DIR, exist_ok=True)
    card_save_path = os.path.join(CARDS_DIR, f'{safe_name}.json')
    with open(card_save_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 保存头像
    if avatar_data:
        avatar_path = os.path.join(AVATARS_DIR, f'{safe_name}.png')
        with open(avatar_path, 'wb') as f:
            f.write(avatar_data)

    # 创建或更新状态
    os.makedirs(STATES_DIR, exist_ok=True)
    state_path = os.path.join(STATES_DIR, f'{safe_name}_state.json')
    if os.path.exists(state_path):
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        # 更新 persona
        if persona:
            state['persona'] = persona
    else:
        state = {
            'card_name': name,
            'card_type': card_type,
            'card_path': card_save_path,
            'persona': persona or '',
            'activated_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'summary': '',
            'turn_count': 0,
            'history': [],
            'current_greeting': 'default',
            'total_tokens_estimate': 0,
        }

    state['last_active'] = datetime.now().isoformat()
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return output, state_path


# ========== 状态操作 ==========

def get_state(card_name):
    safe_name = card_name.replace(' ', '_').replace('/', '_')
    state_path = os.path.join(STATES_DIR, f'{safe_name}_state.json')
    if not os.path.exists(state_path):
        return None, None
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f), state_path


def get_card(card_name):
    safe_name = card_name.replace(' ', '_').replace('/', '_')
    card_path = os.path.join(CARDS_DIR, f'{safe_name}.json')
    if not os.path.exists(card_path):
        return None, None
    with open(card_path, 'r', encoding='utf-8') as f:
        return json.load(f), card_path


def list_cards(filter_keyword=None):
    ensure_dirs()
    cards = []
    for f in os.listdir(CARDS_DIR):
        if f.endswith('.json'):
            with open(os.path.join(CARDS_DIR, f), 'r', encoding='utf-8') as cf:
                card = json.load(cf)
            name = card['data']['name']
            state, _ = get_state(name)
            turns = state['turn_count'] if state else 0

            if filter_keyword:
                kw = filter_keyword.lower()
                if kw not in name.lower() and kw not in ' '.join(card['data'].get('tags', [])).lower():
                    continue

            cards.append({
                'name': name,
                'type': card.get('card_type', 'unknown'),
                'turns': turns,
                'persona': state.get('persona', '') if state else '',
                'tags': card['data'].get('tags', []),
                'last_active': state['last_active'][:16] if state and state.get('last_active') else '从未',
            })
    return cards


def add_history(card_name, role, content):
    state, state_path = get_state(card_name)
    if not state:
        return None
    state['history'].append({
        'role': role,
        'content': content,
        'ts': datetime.now().isoformat(),
    })
    state['turn_count'] = state.get('turn_count', 0) + 1
    state['last_active'] = datetime.now().isoformat()
    state['total_tokens_estimate'] = sum(
        estimate_tokens(h['content']) for h in state['history']
    )
    if len(state['history']) > COMPRESSION_THRESHOLD:
        state['needs_compression'] = True
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return state


# ========== Prompt 构建 ==========

def build_system_prompt(card, state, user_message=''):
    """构建完整的 system prompt，包含世界书关键词匹配"""
    d = card['data']
    persona = state.get('persona', '') or '你'
    card_type = card.get('card_type', 'character')
    char_name = d['name']
    parts = []

    # 角色身份定义
    if card_type == 'world':
        parts.append(f'你是《{char_name}》世界的叙事者，负责描述场景、推进剧情、扮演所有NPC。')
        parts.append(f'用户扮演的角色是：{persona}')
    else:
        parts.append('你正在扮演以下角色，请完全代入角色，用角色的口吻、性格和背景回应。')
        parts.append(f'角色名称：{char_name}')

    parts.append('')

    # 核心设定
    if d.get('description'):
        rendered = render_text(d['description'], persona, char_name)
        parts.append(f'角色描述：{rendered}')
    if d.get('personality'):
        rendered = render_text(d['personality'], persona, char_name)
        parts.append(f'人格设定：{rendered}')
    if d.get('scenario'):
        rendered = render_text(d['scenario'], persona, char_name)
        parts.append(f'场景设定：{rendered}')
    if d.get('system_prompt'):
        rendered = render_text(d['system_prompt'], persona, char_name)
        parts.append(f'系统提示词：{rendered}')
    if d.get('post_history_instructions'):
        rendered = render_text(d['post_history_instructions'], persona, char_name)
        parts.append(f'额外指令：{rendered}')

    # 深度提示 (depth_prompt)
    depth = d.get('extensions', {}).get('depth_prompt', {})
    if depth and depth.get('prompt'):
        rendered = render_text(depth['prompt'], persona, char_name)
        depth_role = depth.get('role', 'system')
        parts.append(f'[{depth_role} 深度提示] {rendered}')

    # 对话示例 (mes_example)
    if d.get('mes_example'):
        rendered = render_text(d['mes_example'], persona, char_name)
        # 只取前 500 字作为示例，避免过长
        if len(rendered) > 500:
            rendered = rendered[:500] + '...'
        parts.append('')
        parts.append('对话风格参考：')
        parts.append(rendered)

    # 世界书关键词匹配
    if d.get('character_book') and d['character_book'].get('entries') and user_message:
        matched = match_world_entries(d['character_book'], user_message)
        if matched:
            parts.append('')
            parts.append(f'当前关联的世界观设定（{d["character_book"].get("name", "世界书")}）：')
            for entry in matched:
                content = entry.get('content', '')
                if content:
                    parts.append(content[:300])

    # 对话历史摘要
    if state.get('summary'):
        parts.append('')
        parts.append(f'对话历史摘要：{state["summary"]}')

    return '\n'.join(parts)


def build_chat_context(card, state, user_message):
    """构建完整对话上下文"""
    d = card['data']
    persona = state.get('persona', '') or '你'
    card_type = card.get('card_type', 'character')
    char_name = d['name']

    system_prompt = build_system_prompt(card, state, user_message)

    # 构建对话历史
    history_lines = []
    for h in state.get('history', []):
        if h['role'] == 'user':
            history_lines.append(f'{persona}：{h["content"]}')
        elif h['role'] == 'assistant':
            label = '叙事者' if card_type == 'world' else char_name
            history_lines.append(f'{label}：{h["content"]}')

    return {
        'system_prompt': system_prompt,
        'history': '\n'.join(history_lines[-20:]),
        'user_message': user_message,
        'persona': persona,
        'card_type': card_type,
        'character_name': char_name,
        'token_estimate': estimate_tokens(system_prompt) + estimate_tokens(user_message) + sum(
            estimate_tokens(h['content']) for h in state.get('history', [])[-20:]
        ),
    }


# ========== 主入口 ==========

def main():
    parser = argparse.ArgumentParser(description='酒馆角色扮演 — 与 SillyTavern 功能对齐')
    sub = parser.add_subparsers(dest='command', required=True)

    # load
    p_load = sub.add_parser('load', help='加载角色卡')
    p_load.add_argument('--card', '-c', required=True, help='角色卡 PNG/JSON 路径')
    p_load.add_argument('--persona', '-p', help='用户扮演的角色名（世界卡必需）')

    # list
    p_list = sub.add_parser('list', help='列出已加载的角色')
    p_list.add_argument('--filter', '-f', help='按名称或标签筛选')

    # chat
    p_chat = sub.add_parser('chat', help='记录对话到历史')
    p_chat.add_argument('name', help='角色名')
    p_chat.add_argument('message', help='消息内容')
    p_chat.add_argument('--role', default='user', choices=['user', 'assistant'], help='消息角色')

    # prompt
    p_prompt = sub.add_parser('prompt', help='输出完整 system prompt + 历史（供 agent 直接使用）')
    p_prompt.add_argument('name', help='角色名')
    p_prompt.add_argument('message', help='用户消息')

    # history
    p_hist = sub.add_parser('history', help='查看对话历史')
    p_hist.add_argument('name', help='角色名')
    p_hist.add_argument('--full', action='store_true', help='显示完整消息内容')

    # alts
    p_alts = sub.add_parser('alts', help='查看/切换备用开场白')
    p_alts.add_argument('name', help='角色名')
    p_alts.add_argument('--select', '-s', type=int, help='选择第 N 个开场白')

    # info
    p_info = sub.add_parser('info', help='查看角色卡详细信息')
    p_info.add_argument('name', help='角色名')

    # summary
    p_sum = sub.add_parser('summary', help='触发摘要压缩')
    p_sum.add_argument('name', help='角色名')
    p_sum.add_argument('--force', action='store_true', help='强制压缩，即使历史不足')

    # reset
    p_reset = sub.add_parser('reset', help='重置对话历史')
    p_reset.add_argument('name', help='角色名')

    # replay
    p_replay = sub.add_parser('replay', help='重置并重新加载角色卡（一键重玩）')
    p_replay.add_argument('--card', '-c', required=True, help='角色卡路径')
    p_replay.add_argument('--persona', '-p', help='用户扮演的角色名')

    # avatar
    p_avatar = sub.add_parser('avatar', help='提取角色卡头像')
    p_avatar.add_argument('name', help='角色名')
    p_avatar.add_argument('--output', '-o', help='输出路径（默认 avatars 目录）')

    # tokens
    p_tokens = sub.add_parser('tokens', help='估算当前对话的 token 用量')
    p_tokens.add_argument('name', help='角色名')

    # export
    p_export = sub.add_parser('export', help='将角色卡导出为 PNG（JSON→PNG 打包）')
    p_export.add_argument('name', help='角色名')
    p_export.add_argument('--output', '-o', help='输出 PNG 路径（默认桌面）')

    # delete
    p_delete = sub.add_parser('delete', help='删除角色卡及其所有数据')
    p_delete.add_argument('name', help='角色名')
    p_delete.add_argument('--force', action='store_true', help='强制删除，不确认')

    args = parser.parse_args()
    ensure_dirs()

    # ====== load ======
    if args.command == 'load':
        card, state_path = load_card(args.card, args.persona)
        d = card['data']
        card_type = card.get('card_type', 'character')
        print(f'✅ 加载成功')
        print(f'类型: {"🌍 世界卡" if card_type == "world" else "🎭 角色卡"}')
        print(f'名称: {d["name"]}')
        if card_type == 'world':
            print(f'用户角色: {args.persona or "（未设置，请用 --persona 指定）"}')
        if d.get('description'):
            print(f'描述: {d["description"][:100]}')
        # 备用开场白
        alts = d.get('alternate_greetings', {})
        if isinstance(alts, dict) and alts:
            alts_list = list(alts.values()) if any(isinstance(v, str) for v in alts.values()) else list(alts.keys())
            print(f'备用开场白: {len(alts_list)} 个（用 alts --select N 切换）')
        elif isinstance(alts, list) and alts:
            print(f'备用开场白: {len(alts)} 个（用 alts --select N 切换）')
        # 渲染开场白
        first_mes_rendered = render_first_mes(card, args.persona)
        if first_mes_rendered:
            print(f'开场白: {first_mes_rendered[:120]}...')
        # 检测旧对话
        state, _ = get_state(d['name'])
        if state and state.get('turn_count', 0) > 0:
            print(f'📌 注意：已有 {state["turn_count"]} 轮对话历史，如需重玩请用 replay 命令')

    # ====== list ======
    elif args.command == 'list':
        cards = list_cards(args.filter)
        if not cards:
            print('📭 还没有加载过角色卡' if not args.filter else f'📭 没有匹配 "{args.filter}" 的角色卡')
        else:
            print(f'📚 {"已加载的角色" if not args.filter else f"筛选结果"} ({len(cards)}):')
            for c in cards:
                icon = '🌍' if c['type'] == 'world' else '🎭'
                tags = f' [{", ".join(c["tags"][:3])}]' if c['tags'] else ''
                persona = f' [扮演: {c["persona"]}]' if c['persona'] else ''
                print(f'  {icon} {c["name"]}{persona}{tags} — {c["turns"]} 轮, 上次: {c["last_active"]}')

    # ====== chat ======
    elif args.command == 'chat':
        state, _ = get_state(args.name)
        if not state:
            print(f'❌ 角色 "{args.name}" 未加载')
            sys.exit(1)
        # 自动压缩检查
        if state.get('needs_compression') and args.role == 'assistant':
            print(f'💡 提示：对话历史已达 {len(state["history"])} 条，建议运行 summary 压缩')
        add_history(args.name, args.role, args.message)
        card, _ = get_card(args.name)
        char_name = card['data']['name'] if card else args.name
        role_label = '用户' if args.role == 'user' else char_name
        print(f'✅ 已记录 [{role_label}] {args.message[:80]}...' if len(args.message) > 80 else f'✅ 已记录 [{role_label}] {args.message}')

    # ====== prompt ======
    elif args.command == 'prompt':
        card, _ = get_card(args.name)
        state, _ = get_state(args.name)
        if not card or not state:
            print(f'❌ 角色 "{args.name}" 未加载')
            sys.exit(1)
        ctx = build_chat_context(card, state, args.message)
        print(json.dumps(ctx, ensure_ascii=False, indent=2))

    # ====== history ======
    elif args.command == 'history':
        state, _ = get_state(args.name)
        if not state or not state.get('history'):
            print(f'📭 还没有对话历史')
        else:
            print(f'📜 {args.name}（{state["turn_count"]} 轮, 约 {state.get("total_tokens_estimate", 0)} tokens）')
            if state.get('summary'):
                print(f'   摘要: {state["summary"][:200]}...')
            print()
            for i, h in enumerate(state['history']):
                icon = '🧑' if h['role'] == 'user' else '🎭'
                ts = h.get('ts', '')[:16]
                if args.full:
                    print(f'  [{ts}] {icon} {h["content"]}')
                    if i < len(state['history']) - 1:
                        print()
                else:
                    content = h['content'][:80] + '...' if len(h['content']) > 80 else h['content']
                    print(f'  [{ts[:10]}] {icon} {content}')

    # ====== alts ======
    elif args.command == 'alts':
        card, _ = get_card(args.name)
        if not card:
            print(f'❌ 角色 "{args.name}" 未加载')
            sys.exit(1)
        d = card['data']
        alts = d.get('alternate_greetings', {})
        if isinstance(alts, dict) and alts:
            alts_list = list(alts.values()) if any(isinstance(v, str) for v in alts.values()) else list(alts.keys())
        elif isinstance(alts, list) and alts:
            alts_list = alts
        else:
            print(f'📭 角色 "{args.name}" 没有备用开场白')
            sys.exit(0)

        if args.select is not None:
            if args.select < 1 or args.select > len(alts_list):
                print(f'❌ 序号 {args.select} 超出范围（1-{len(alts_list)}）')
                sys.exit(1)
            selected = alts_list[args.select - 1]
            # 渲染并保存到状态
            state, state_path = get_state(args.name)
            rendered = render_text(selected, state.get('persona', ''), d['name'])
            state['current_greeting'] = f'alt_{args.select}'
            state['pending_greeting'] = rendered
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print(f'✅ 已选择开场白 #{args.select}：')
            print(rendered[:300])
        else:
            print(f'🔄 {args.name} 的备用开场白（{len(alts_list)} 个）：')
            for i, alt in enumerate(alts_list, 1):
                preview = alt[:80] + '...' if len(alt) > 80 else alt
                print(f'  {i}. {preview}')

    # ====== info ======
    elif args.command == 'info':
        card, _ = get_card(args.name)
        state, _ = get_state(args.name)
        if not card:
            print(f'❌ 角色 "{args.name}" 未加载')
            sys.exit(1)
        d = card['data']
        print(f'名称: {d["name"]}')
        print(f'类型: {card.get("card_type", "unknown")}')
        print(f'规范: {card.get("spec", "?")} v{card.get("spec_version", "?")}')
        if state and state.get('persona'):
            print(f'用户角色: {state["persona"]}')
        print(f'描述: {d["description"] or "(无)"}')
        print(f'人格: {d["personality"] or "(无)"}')
        print(f'场景: {d["scenario"] or "(无)"}')
        print(f'系统提示词: {"有" if d.get("system_prompt") else "无"}')
        print(f'历史后指令: {"有" if d.get("post_history_instructions") else "无"}')
        print(f'深度提示: {"有" if d.get("extensions", {}).get("depth_prompt", {}).get("prompt") else "无"}')
        print(f'对话示例: {"有" if d.get("mes_example") else "无"}')
        print(f'标签: {", ".join(d.get("tags", [])) or "(无)"}')
        print(f'创作者: {d.get("creator") or "(无)"}')
        alts = d.get('alternate_greetings', {})
        if isinstance(alts, (dict, list)) and alts:
            print(f'备用开场白: {len(alts)} 个')
        cb = d.get('character_book')
        if cb and cb.get('entries'):
            print(f'世界书: {cb.get("name", "N/A")} ({len(cb["entries"])} 条)')
        if state:
            print(f'---')
            print(f'对话轮次: {state["turn_count"]}')
            print(f'历史条数: {len(state.get("history", []))}')
            print(f'Token 估算: {state.get("total_tokens_estimate", 0)}')
            if state.get('summary'):
                print(f'摘要: {state["summary"][:150]}...')
            print(f'当前开场白: {state.get("current_greeting", "default")}')

    # ====== summary ======
    elif args.command == 'summary':
        state, state_path = get_state(args.name)
        if not state or not state.get('history'):
            print('📭 没有可压缩的对话历史')
            return
        if len(state['history']) < 6 and not args.force:
            print(f'💬 对话历史仅 {len(state["history"])} 条，尚不需要压缩（至少 6 条）')
            return

        half = len(state['history']) // 2
        early = state['history'][:half]
        late = state['history'][half:]

        # 构建摘要文本
        summary_lines = []
        for h in early:
            label = '用户' if h['role'] == 'user' else '角色'
            content = h['content'][:80]
            summary_lines.append(f'{label}: {content}')
        summary_text = ' | '.join(summary_lines)

        old = state.get('summary', '')
        state['summary'] = f'{old}\n[{len(early)} 条对话] {summary_text[:300]}...' if old else f'[{len(early)} 条对话] {summary_text[:300]}...'
        state['history'] = late
        state['needs_compression'] = False
        state['total_tokens_estimate'] = sum(estimate_tokens(h['content']) for h in late)

        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f'✅ 已压缩：保留最近 {len(late)} 条，删除 {len(early)} 条，摘要已更新')
        print(f'📊 当前 token 估算: {state["total_tokens_estimate"]}')

    # ====== reset ======
    elif args.command == 'reset':
        state, state_path = get_state(args.name)
        if not state:
            print('📭 没有可重置的对话')
        else:
            state['history'] = []
            state['summary'] = ''
            state['turn_count'] = 0
            state['total_tokens_estimate'] = 0
            state['last_active'] = datetime.now().isoformat()
            if 'needs_compression' in state:
                del state['needs_compression']
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print(f'✅ 已重置 "{args.name}" 的对话历史')

    # ====== replay ======
    elif args.command == 'replay':
        try:
            ext = os.path.splitext(args.card)[1].lower()
            if ext == '.png':
                card_data, _ = parse_png_card(args.card)
            else:
                card_data, _ = parse_json_card(args.card)
            card_name = card_data.get('data', card_data).get('name', '未知角色')
        except Exception as e:
            print(f'❌ 无法读取角色卡: {e}')
            sys.exit(1)

        # 重置
        state, state_path = get_state(card_name)
        if state:
            state['history'] = []
            state['summary'] = ''
            state['turn_count'] = 0
            state['total_tokens_estimate'] = 0
            state['last_active'] = datetime.now().isoformat()
            if 'needs_compression' in state:
                del state['needs_compression']
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

        # 加载
        card, _ = load_card(args.card, args.persona)
        d = card['data']
        card_type = card.get('card_type', 'character')
        print(f'✅ 重玩成功')
        print(f'类型: {"🌍 世界卡" if card_type == "world" else "🎭 角色卡"}')
        print(f'名称: {d["name"]}')
        if card_type == 'world' and args.persona:
            print(f'用户角色: {args.persona}')
        first_mes_rendered = render_first_mes(card, args.persona)
        if first_mes_rendered:
            print(f'开场白: {first_mes_rendered[:120]}...')

    # ====== avatar ======
    elif args.command == 'avatar':
        card, _ = get_card(args.name)
        if not card:
            print(f'❌ 角色 "{args.name}" 未加载')
            sys.exit(1)
        safe_name = args.name.replace(' ', '_').replace('/', '_')
        avatar_path = os.path.join(AVATARS_DIR, f'{safe_name}.png')
        if os.path.exists(avatar_path):
            size = os.path.getsize(avatar_path)
            if args.output:
                import shutil
                shutil.copy2(avatar_path, args.output)
                print(f'✅ 已导出头像到 {args.output} ({size} bytes)')
            else:
                print(f'✅ 头像路径: {avatar_path} ({size} bytes)')
        else:
            # 从源文件提取
            src = card.get('source_path', '')
            if src and os.path.exists(src):
                import shutil
                os.makedirs(AVATARS_DIR, exist_ok=True)
                shutil.copy2(src, avatar_path)
                size = os.path.getsize(avatar_path)
                print(f'✅ 已提取头像: {avatar_path} ({size} bytes)')
            else:
                print(f'❌ 找不到头像文件，源文件可能已移动')

    # ====== tokens ======
    elif args.command == 'tokens':
        state, _ = get_state(args.name)
        if not state:
            print(f'📭 角色 "{args.name}" 未加载')
            sys.exit(1)
        card, _ = get_card(args.name)
        d = card['data'] if card else {}
        history = state.get('history', [])

        # 估算各部分
        system_text = f'角色名称：{d.get("name", "")} 描述：{d.get("description", "")} 人格：{d.get("personality", "")}'
        system_tokens = estimate_tokens(system_text)
        history_tokens = sum(estimate_tokens(h['content']) for h in history)
        summary_tokens = estimate_tokens(state.get('summary', ''))
        total = system_tokens + history_tokens + summary_tokens

        print(f'📊 Token 估算 — {args.name}')
        print(f'  System prompt: ~{system_tokens} tokens')
        print(f'  对话历史 ({len(history)} 条): ~{history_tokens} tokens')
        print(f'  摘要: ~{summary_tokens} tokens')
        print(f'  ───────────────')
        print(f'  总计: ~{total} tokens')
    elif args.command == 'export':
        card, _ = get_card(args.name)
        if not card:
            print(f'❌ 角色 "{args.name}" 未加载')
            sys.exit(1)
        import shutil
        safe_name = args.name.replace(' ', '_').replace('/', '_')
        avatar_path = os.path.join(AVATARS_DIR, f'{safe_name}.png')
        if not os.path.exists(avatar_path):
            src = card.get('source_path', '')
            if src and os.path.exists(src):
                os.makedirs(AVATARS_DIR, exist_ok=True)
                shutil.copy2(src, avatar_path)
            else:
                print(f'❌ 找不到头像源文件，无法导出')
                sys.exit(1)
        d = card['data']
        chara_data = {
            'spec': card.get('spec', 'chara_card_v3'),
            'spec_version': card.get('spec_version', '3.0'),
            'data': {
                'name': d['name'],
                'description': d.get('description', ''),
                'personality': d.get('personality', ''),
                'scenario': d.get('scenario', ''),
                'first_mes': d.get('first_mes', ''),
                'mes_example': d.get('mes_example', ''),
                'creator_notes': d.get('creator_notes', ''),
                'system_prompt': d.get('system_prompt', ''),
                'post_history_instructions': d.get('post_history_instructions', ''),
                'tags': d.get('tags', []),
                'creator': d.get('creator', ''),
                'character_version': d.get('character_version', ''),
                'alternate_greetings': d.get('alternate_greetings', {}),
                'extensions': d.get('extensions', {}),
                'character_book': d.get('character_book', None),
                'talkativeness': d.get('talkativeness', 0.5),
            }
        }
        json_str = json.dumps(chara_data, ensure_ascii=False, separators=(',', ':'))
        b64_data = base64.b64encode(json_str.encode('utf-8')).decode('ascii')
        with open(avatar_path, 'rb') as f:
            png_data = f.read()
        iend_pos = png_data.rfind(b'IEND')
        if iend_pos < 0:
            print('❌ PNG 格式错误')
            sys.exit(1)
        keyword = b'chara'
        text_data = b64_data.encode('ascii')
        chunk_data = keyword + b'\x00' + text_data
        chunk_length = len(chunk_data)
        chunk_crc = struct.pack('>I', zlib.crc32(b'tEXt' + chunk_data) & 0xffffffff)
        insert_pos = iend_pos - 4
        new_png = png_data[:insert_pos] + struct.pack('>I', chunk_length) + b'tEXt' + chunk_data + chunk_crc + png_data[insert_pos:]
        output_path = args.output or os.path.expanduser(f'~/Desktop/export_{safe_name}.png')
        with open(output_path, 'wb') as f:
            f.write(new_png)
        print(f'✅ 已导出角色卡: {output_path}')
        print(f'📦 大小: {len(new_png)} bytes')

    elif args.command == 'delete':
        card, _ = get_card(args.name)
        if not card:
            print(f'❌ 角色 "{args.name}" 未加载')
            sys.exit(1)
        if not args.force:
            print(f'⚠️  确认删除 "{args.name}" 及其所有对话数据？')
            print(f'   使用 --force 确认删除')
            sys.exit(0)
        safe_name = args.name.replace(' ', '_').replace('/', '_')
        deleted = []
        for path in [
            os.path.join(CARDS_DIR, f'{safe_name}.json'),
            os.path.join(STATES_DIR, f'{safe_name}_state.json'),
            os.path.join(AVATARS_DIR, f'{safe_name}.png'),
        ]:
            if os.path.exists(path):
                os.remove(path)
                deleted.append(os.path.basename(path))
        print(f'✅ 已删除 "{args.name}" 的数据:')
        for f in deleted:
            print(f'  - {f}')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

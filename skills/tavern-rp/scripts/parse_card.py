#!/usr/bin/env python3
"""
解析 SillyTavern 角色卡 PNG/JSON 文件。

用法：
  python parse_card.py --input <角色卡路径> [--output <输出目录>]

输出：
  - <角色名>.json — 角色完整数据
  - 如果指定了 --output，还会复制头像为 <角色名>.png
"""

import base64
import json
import os
import sys
import argparse


def parse_png_card(filepath):
    """从 PNG 文件中提取 chara 角色的 JSON 数据"""
    with open(filepath, 'rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Not a valid PNG file')

        while True:
            header = f.read(8)
            if len(header) < 8:
                break
            length = int.from_bytes(header[:4], 'big')
            chunk_type = header[4:8]
            data = f.read(length)
            crc = f.read(4)

            if chunk_type == b'tEXt':
                null_pos = data.find(b'\x00')
                if null_pos < 0:
                    continue
                keyword = data[:null_pos].decode('latin-1')
                text = data[null_pos + 1:].decode('latin-1')

                if keyword == 'chara':
                    try:
                        decoded = base64.b64decode(text)
                        return json.loads(decoded)
                    except Exception:
                        # 可能不是 base64，尝试直接解析 JSON
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            raise ValueError('chara chunk is not valid JSON or base64')

            if chunk_type == b'IEND':
                break

    raise ValueError('No chara chunk found in PNG')


def parse_json_card(filepath):
    """从 JSON 文件加载角色卡数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='解析 SillyTavern 角色卡')
    parser.add_argument('--input', '-i', required=True, help='角色卡文件路径 (.png 或 .json)')
    parser.add_argument('--output', '-o', help='输出目录（可选）')
    args = parser.parse_args()

    input_path = args.input
    if not os.path.exists(input_path):
        print(f'❌ 文件不存在: {input_path}')
        sys.exit(1)

    ext = os.path.splitext(input_path)[1].lower()

    # 解析角色卡
    if ext == '.png':
        card_data = parse_png_card(input_path)
    elif ext == '.json':
        card_data = parse_json_card(input_path)
    else:
        print(f'❌ 不支持的文件格式: {ext}')
        sys.exit(1)

    # 提取数据
    spec = card_data.get('spec', 'unknown')
    d = card_data.get('data', card_data)  # 兼容裸数据格式
    name = d.get('name', '未知角色')
    safe_name = name.replace(' ', '_').replace('/', '_')

    # 构建输出
    output = {
        'spec': spec,
        'spec_version': card_data.get('spec_version', '1.0'),
        'source_file': os.path.basename(input_path),
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

    # 输出
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        out_path = os.path.join(args.output, f'{safe_name}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f'✅ 已保存: {out_path}')
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

    print(f'📋 角色: {name} (spec: {spec})')
    print(f'📝 描述: {output["data"]["description"][:100]}...' if output['data']['description'] else '📝 描述: (无)')
    print(f'💬 开场白: {output["data"]["first_mes"][:100]}...' if output['data']['first_mes'] else '💬 开场白: (无)')


if __name__ == '__main__':
    main()
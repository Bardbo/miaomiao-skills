#!/usr/bin/env python3
"""
dialogue_validator.py — 对话验证脚本

验证已生成的对话质量：违规检测、节奏检查、角色覆盖。

用法:
  python3 dialogue_validator.py validate \
    --input "./dialogue.md" \
    --characters "巴菲特,芒格"

  python3 dialogue_validator.py check-line \
    --line '"这句话有问题"' \
    --speaker "巴菲特" \
    --characters "巴菲特,芒格"

模式:
  默认（short）: 单句上限 3 句（快速角色扮演）
  --mode article: 单句上限 7 句（公众号长文对话）
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# 违规模板: 常见不是旁白的语义组合，排除误报
# ---------------------------------------------------------------------------

# 常见以 说/在想/认为 结尾但不是第三人称叙述的合法短语
_SAFE_VERB_PATTERNS = {
    "说": [
        "在说", "说到", "说起", "虽说", "再说",
        "比如说", "也就是说", "可说的是",
        "不得不说的是", "不是我说", "要我说",
        "照我说", "听我说", "跟我说的", "你说",
        "你说到", "我说到", "谁都说的",
        "有句话说的", "话又说回来",
        "刚才说", "你刚才说", "所以我说",
        "都说", "人们说", "来说", "会说",
        "听说", "大家都说", "你这样说的", "你们说",
        "你俩说", "你别说", "你这说", "你是说",
        "小说", "就是说",
    ],
    "在想": [
        "我在想", "你想想", "我在想的是",
    ],
    "认为": [
        "被人们认为", "普遍认为",
    ],
}


def _is_safe_verb(prefix: str, verb: str) -> bool:
    """检查 prefix+verb 是否是合法表达（非第三人称旁白）"""
    candidate = prefix + verb
    for safe in _SAFE_VERB_PATTERNS.get(verb, []):
        if safe in candidate or candidate in safe:
            return True
    # "在说" -> 检测方式: prefix='在', verb='说'
    # "说到" -> prefix='说', next_char='到', not matched by this check
    return False


# ---------------------------------------------------------------------------
# 违规检测（单句）
# ---------------------------------------------------------------------------

class ViolationChecker:
    """每句对话的违规检测"""

    @classmethod
    def check_line(cls, line: str, speaker: str, all_characters: list[str],
                   max_sentences: int = 3) -> dict:
        """检测单句对话"""
        violations = []

        clean_line = line.strip().strip('"').strip('\u201c').strip('\u201d').strip()

        # 1. 第三方人称旁白 / 解释性旁白
        # 只匹配句首或标点后 + 2字以上人称 + 说的模式，排除"你说"等直接称呼
        narration_patterns = [
            (r'(?:^|[。！？，,])[\u4e00-\u9fff]{2,4}说[：:：]?\s*', "第三方人称旁白"),
            (r'(?:^|[。！？，,])[\u4e00-\u9fff]{2,4}在想[，,：:]?\s*', "第三方人称旁白"),
            (r'(?:^|[。！？，,])[\u4e00-\u9fff]{2,4}认为[，,：:]?\s*', "第三方人称旁白"),
            (r'其实在说', "解释性旁白"),
            (r'这个观点有意思', "解释性旁白"),
        ]

        for pattern, vtype in narration_patterns:
            for m in re.finditer(pattern, clean_line):
                # 提取匹配到的 2-4 字前缀
                matched_text = m.group(0)
                # 从匹配文本中提取前缀（去掉句首标点和后缀":说"）
                # 匹配格式: (句首/标点)(2-4字)说...
                prefix_match = re.search(r'[\u4e00-\u9fff]{2,4}(?=说[：:：]?\s*$|在想|认为)', matched_text)
                if prefix_match:
                    prefix = prefix_match.group(0)
                    verb = "说" if "说" in matched_text else ("在想" if "在想" in matched_text else "认为")
                    if _is_safe_verb(prefix, verb):
                        continue
                violations.append(vtype)
                break

        # 2. 提及其他角色名+动词（排除"向XX说"等合法用法）
        for other in all_characters:
            if other == speaker or len(other) < 1:
                continue
            for verb in ["说", "在想", "认为", "其实在说"]:
                pattern = re.escape(other) + verb
                if re.search(pattern, clean_line):
                    # 检查前面是否有"向"、"对"
                    if not re.search(rf'[向对]' + re.escape(other) + verb, clean_line):
                        violations.append(f"第三方人称旁白: '{other}{verb}'")
                        break

        # 3. 跳出角色
        meta_patterns = [r'作为AI', r'我是语言模型', r'我是一个AI', r'作为一个AI']
        for p in meta_patterns:
            if re.search(p, clean_line):
                violations.append("跳出角色")
                break

        # 4. 长度（按句子数）
        sentences = [s.strip() for s in re.split(r'[。！？!?\n]', clean_line) if s.strip()]
        if len(sentences) > max_sentences:
            violations.append(f"发言过长: {len(sentences)} 句（上限{max_sentences}句）")

        return {
            "failed": len(violations) > 0,
            "violations": violations,
            "count": len(violations),
        }


# ---------------------------------------------------------------------------
# 对话解析
# ---------------------------------------------------------------------------

def parse_dialogue(text: str) -> list[dict]:
    """解析对话文本，返回 [{speaker, content}] 列表"""
    lines = []
    # "**角色名**: 内容" 或 "角色名：内容" 或 "角色名: 内容"
    pattern = r'\*{0,2}([^*：:]+)\*{0,2}[：:]\s*(.+)'

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        match = re.match(pattern, line)
        if match:
            lines.append({
                "speaker": match.group(1).strip(),
                "content": match.group(2).strip(),
            })
        else:
            lines.append({
                "speaker": "__unknown__",
                "content": line,
            })

    return lines


# ---------------------------------------------------------------------------
# 节奏检查
# ---------------------------------------------------------------------------

class RhythmChecker:
    """检查对话节奏"""

    @classmethod
    def check(cls, parsed_lines: list[dict], target_rounds: int,
              characters: list[str]) -> list[str]:
        issues = []

        speaker_counts: dict[str, int] = {}
        for pl in parsed_lines:
            s = pl["speaker"]
            speaker_counts[s] = speaker_counts.get(s, 0) + 1

        for char in characters:
            count = speaker_counts.get(char, 0)
            if count < target_rounds:
                issues.append(f"角色失声: {char} 仅发言 {count} 次（目标 >= {target_rounds}）")

        max_consecutive = 0
        current_consecutive = 0
        last_speaker = ""
        for pl in parsed_lines:
            if pl["speaker"] == last_speaker:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
                last_speaker = pl["speaker"]

        if max_consecutive >= 3:
            issues.append(f"长篇独白: 有角色连续发言 {max_consecutive} 次（上限2次）")

        return issues


# ---------------------------------------------------------------------------
# 完整验证
# ---------------------------------------------------------------------------

class FullValidator:
    """生成完成后的全面验证"""

    @classmethod
    def validate(cls, text: str, characters: list[str],
                 target_rounds: int, max_sentences: int = 3) -> dict:
        checks = []
        parsed_lines = parse_dialogue(text)

        if not parsed_lines:
            return {
                "all_passed": False,
                "checks": [{"name": "对话解析", "passed": False,
                           "detail": "无法解析对话文本，请确认格式为「角色名：内容」"}],
            }

        # 逐句违规检测
        violation_results = []
        for pl in parsed_lines:
            speaker = pl["speaker"]
            if speaker == "__unknown__":
                continue
            vr = ViolationChecker.check_line(
                pl["content"], speaker, characters,
                max_sentences=max_sentences,
            )
            if vr["failed"]:
                violation_results.append({
                    "speaker": speaker,
                    "content": pl["content"][:60],
                    "violations": vr["violations"],
                })

        if violation_results:
            checks.append({
                "name": "违规检测",
                "passed": False,
                "detail": f"{len(violation_results)} 句有违规",
                "violations": violation_results,
            })
        else:
            checks.append({"name": "违规检测", "passed": True})

        # 角色覆盖
        speaker_counts: dict[str, int] = {}
        for pl in parsed_lines:
            s = pl["speaker"]
            if s != "__unknown__":
                speaker_counts[s] = speaker_counts.get(s, 0) + 1

        for char in characters:
            count = speaker_counts.get(char, 0)
            if count < target_rounds:
                checks.append({
                    "name": f"角色覆盖-{char}",
                    "passed": False,
                    "detail": f"仅发言 {count} 次（目标 >= {target_rounds}）",
                })
            else:
                checks.append({
                    "name": f"角色覆盖-{char}",
                    "passed": True,
                    "detail": f"发言 {count} 次",
                })

        # 节奏
        rhythm_issues = RhythmChecker.check(parsed_lines, target_rounds, characters)
        checks.append({
            "name": "节奏检查",
            "passed": len(rhythm_issues) == 0,
            "detail": rhythm_issues or "通过",
        })

        # 总长度
        total_lines = len(parsed_lines)
        expected_min = target_rounds * len(characters)
        checks.append({
            "name": "总长度",
            "passed": total_lines >= expected_min,
            "detail": f"{total_lines} 句（期望 >= {expected_min}）",
        })

        all_passed = all(c.get("passed", False) for c in checks)

        return {
            "all_passed": all_passed,
            "checks": checks,
            "summary": {
                "total_lines": total_lines,
                "characters_found": list(speaker_counts.keys()),
                "speaker_counts": speaker_counts,
            },
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="对话验证脚本")
    subparsers = parser.add_subparsers(dest="command")

    # validate 命令
    val_parser = subparsers.add_parser("validate", help="验证已有对话文件")
    val_parser.add_argument("--input", required=True, help="对话文件路径（.md）")
    val_parser.add_argument("--characters", required=True, help="角色列表，逗号分隔")
    val_parser.add_argument("--rounds", default="10", help="目标轮次数")
    val_parser.add_argument("--mode", choices=["short", "article"], default="short",
                            help="验证模式: short(默认3句上限) / article(7句上限)")
    val_parser.add_argument("--output", choices=["json", "text"], default="json",
                            help="输出格式")

    # check-line 命令
    line_parser = subparsers.add_parser("check-line", help="检测单句对话")
    line_parser.add_argument("--line", required=True, help="对话文本")
    line_parser.add_argument("--speaker", required=True, help="说话角色")
    line_parser.add_argument("--characters", required=True, help="所有角色列表，逗号分隔")
    line_parser.add_argument("--max-sentences", type=int, default=3,
                             help="单句上限句数（默认3）")
    line_parser.add_argument("--output", choices=["json", "text"], default="json",
                             help="输出格式")

    args = parser.parse_args()

    if args.command == "validate":
        input_path = Path(args.input)
        if not input_path.exists():
            print(json.dumps({
                "error": f"文件不存在: {args.input}",
                "all_passed": False,
            }, ensure_ascii=False))
            sys.exit(1)

        text = input_path.read_text(encoding="utf-8")
        characters = [c.strip() for c in args.characters.split(",") if c.strip()]
        target_rounds = int(args.rounds)

        max_sentences = 7 if args.mode == "article" else 3
        result = FullValidator.validate(text, characters, target_rounds,
                                        max_sentences=max_sentences)

        if args.output == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status = "通过" if result["all_passed"] else "未通过"
            print(f"\n=== 验证结果: {status} ===\n")
            for check in result["checks"]:
                mark = "+" if check.get("passed") else "x"
                detail = check.get("detail", "")
                if isinstance(detail, list):
                    detail = "; ".join(detail)
                print(f"  [{mark}] {check['name']}: {detail}")
            print(f"\n总计 {result['summary']['total_lines']} 句")
            for char, cnt in result['summary']['speaker_counts'].items():
                print(f"  {char}: {cnt} 次")

    elif args.command == "check-line":
        characters = [c.strip() for c in args.characters.split(",") if c.strip()]
        result = ViolationChecker.check_line(args.line, args.speaker, characters,
                                             max_sentences=args.max_sentences)

        if args.output == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result["failed"]:
                print(f"违规 ({result['count']} 项): {', '.join(result['violations'])}")
            else:
                print("无违规")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
persona_detector.py — 人格技能检测模块

检测角色的可用人格 skill，按优先级链搜索：
  1. 本地已安装的 skills 目录
  2. awesome-ai-persona-skills + 名人独立 skill 仓库
  3. 标记需要 nuwa 蒸馏（由 agent 询问用户）
  4. Fallback 构建

用法：
  python3 persona_detector.py detect --char "巴菲特" --char "芒格"
  python3 persona_detector.py search --char "巴菲特"
  python3 persona_detector.py fallback --char "某个未知角色"
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# Hermes skills 目录
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
HERMES_SKILLS_DIR = HERMES_HOME / "skills"

# 仓库配置
PERSONA_REPOS = [
    {
        "name": "awesome-ai-persona-skills",
        "url": "https://github.com/momozi1996/awesome-ai-persona-skills",
        "mirror": "https://ghproxy.net/https://raw.githubusercontent.com/momozi1996/awesome-ai-persona-skills/main",
        "paths": ["persona-skills.md"],
    },
]

# 名人独立 skill 仓库模式
NAMED_REPOS = [
    {"name": "munger-skill", "owner_repo": "alchaincyf/munger-skill"},
    {"name": "buffett-skill", "owner_repo": "alchaincyf/buffett-skill"},
    {"name": "feynman-perspective", "owner_repo": "alchaincyf/feynman-perspective"},
    {"name": "taleb-perspective", "owner_repo": "alchaincyf/taleb-perspective"},
    {"name": "naval-perspective", "owner_repo": "alchaincyf/naval-perspective"},
    {"name": "musk-perspective", "owner_repo": "alchaincyf/musk-perspective"},
]

GITHUB_MIRRORS = [
    "https://ghproxy.net/https://raw.githubusercontent.com",
    "https://ghproxy.io/https://raw.githubusercontent.com",
    "https://raw.githubusercontent.com",
]

SCRIPT_DIR = Path(__file__).parent.resolve()


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def try_http_get(url: str, timeout: int = 10) -> tuple[bool, str]:
    """尝试 HTTP GET，返回 (成功, 内容)"""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        if result.returncode == 0 and result.stdout:
            return True, result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: 用 python urllib
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "hermes-talk-skill/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, resp.read().decode("utf-8", errors="replace")
    except Exception:
        pass

    return False, ""


def try_multiple_mirrors(owner_repo: str, file_path: str, timeout: int = 10) -> tuple[bool, str]:
    """依次尝试多个镜像 URL"""
    for mirror in GITHUB_MIRRORS:
        url = f"{mirror}/{owner_repo}/main/{file_path}"
        success, content = try_http_get(url, timeout)
        if success:
            return True, content
    return False, ""


# ---------------------------------------------------------------------------
# 本地搜索
# ---------------------------------------------------------------------------

def search_local_skills(char_name: str) -> list[dict]:
    """搜索本地已安装的 Hermes skills"""
    results = []

    if not HERMES_SKILLS_DIR.exists():
        return results

    for skill_root in HERMES_SKILLS_DIR.rglob("SKILL.md"):
        try:
            content = skill_root.read_text(encoding="utf-8")
            parent = skill_root.parent.name.lower()
            name_lower = char_name.lower()

            # 匹配：目录名含角色名、文件描述含角色名
            if name_lower in parent or name_lower in content.lower():
                results.append({
                    "source": "local",
                    "path": str(skill_root.parent),
                    "skill_name": skill_root.parent.name,
                    "category": skill_root.parent.parent.name if skill_root.parent.parent.name != "skills" else "",
                })
        except Exception:
            pass

    return results


# ---------------------------------------------------------------------------
# 仓库搜索
# ---------------------------------------------------------------------------

def search_awesome_repo(char_name: str) -> list[dict]:
    """在 awesome-ai-persona-skills 中搜索"""
    results = []
    name_lower = char_name.lower()

    for repo in PERSONA_REPOS:
        for mirror in GITHUB_MIRRORS:
            for path in repo["paths"]:
                url = f"{mirror}/{repo['url'].replace('https://github.com/', '')}/main/{path}"
                success, content = try_http_get(url)
                if success and name_lower in content.lower():
                    results.append({
                        "source": "awesome-repo",
                        "repo": repo["name"],
                        "file": path,
                        "url": url,
                        "matched": True,
                    })
                    break
            if results:
                break
        if results:
            break

    return results


def search_named_repos(char_name: str) -> list[dict]:
    """搜索名人独立 skill 仓库"""
    results = []
    name_lower = char_name.lower()

    for repo in NAMED_REPOS:
        # 检查仓库名是否匹配角色名
        if name_lower in repo["name"].lower() or name_lower in repo["owner_repo"].lower():
            success, content = try_multiple_mirrors(repo["owner_repo"], "SKILL.md")
            if success and name_lower in content.lower():
                results.append({
                    "source": "named-repo",
                    "repo": repo["name"],
                    "owner_repo": repo["owner_repo"],
                    "matched": True,
                })
                break

    return results


# ---------------------------------------------------------------------------
# Fallback 构建
# ---------------------------------------------------------------------------

def build_fallback(char_name: str) -> dict:
    """构建 Fallback 人格摘要"""
    return {
        "name": char_name,
        "skill_level": 4,
        "source": "Fallback 构建",
        "persona": {
            "thinking_style": "逻辑",
            "emotional_rhythm": "沉稳",
            "core_stance": "中立",
            "catchphrase": "",
        },
        "warning": "这是 Fallback 构建的人格，准确性有限。建议寻找更精准的人格 skill 或使用 huashu-nuwa 蒸馏。",
    }


# ---------------------------------------------------------------------------
# 主检测逻辑
# ---------------------------------------------------------------------------

def detect_personas(characters: list[str]) -> dict:
    """完整的人格检测流程"""
    results = {}

    for char in characters:
        char_results = {
            "character": char,
            "detections": [],
            "recommended_level": None,
        }

        # 优先级 1: 本地搜索
        local = search_local_skills(char)
        if local:
            char_results["detections"].append({
                "level": 1,
                "method": "local_skills",
                "found": True,
                "items": local,
            })
            char_results["recommended_level"] = 1
        else:
            char_results["detections"].append({
                "level": 1,
                "method": "local_skills",
                "found": False,
            })

        # 优先级 2: 仓库搜索
        repo_results = search_named_repos(char) + search_awesome_repo(char)
        if repo_results:
            char_results["detections"].append({
                "level": 2,
                "method": "repo_search",
                "found": True,
                "items": repo_results,
            })
            if not char_results["recommended_level"] or char_results["recommended_level"] > 2:
                char_results["recommended_level"] = 2
        else:
            char_results["detections"].append({
                "level": 2,
                "method": "repo_search",
                "found": False,
            })

        # 优先级 3: nuwa 蒸馏（标记可用，等用户决定）
        char_results["detections"].append({
            "level": 3,
            "method": "nuwa_distill",
            "found": False,
            "requires_user_confirmation": True,
        })
        if not char_results["recommended_level"]:
            char_results["recommended_level"] = 3

        # 优先级 4: Fallback
        fallback = build_fallback(char)
        char_results["detections"].append({
            "level": 4,
            "method": "fallback",
            "found": True,
            "fallback": fallback,
        })
        if not char_results["recommended_level"]:
            char_results["recommended_level"] = 4

        results[char] = char_results

    return results


def format_text_output(results: dict) -> str:
    """格式化为可读文本"""
    lines = []
    for char, data in results.items():
        lines.append(f"\n=== {char} ===")
        for det in data["detections"]:
            level = det["level"]
            method = det["method"]
            if det.get("found") and det.get("items"):
                items = det["items"]
                lines.append(f"  [级别 {level}] {method}: 找到 {len(items)} 个")
                for item in items[:3]:
                    if item.get("path"):
                        lines.append(f"        路径: {item['path']}")
                    if item.get("repo"):
                        lines.append(f"        仓库: {item['repo']}")
            elif det.get("requires_user_confirmation"):
                lines.append(f"  [级别 {level}] {method}: 可用（需要您确认是否使用）")
            elif det.get("fallback"):
                lines.append(f"  [级别 {level}] {method}: 可用（最后一招）")
            else:
                lines.append(f"  [级别 {level}] {method}: 未找到")
        lines.append(f"  → 推荐级别: {data['recommended_level']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="人格技能检测工具")
    parser.add_argument("command", choices=["detect", "search", "fallback"],
                        help="命令: detect=完整检测, search=只搜仓库, fallback=构建 fallback")
    parser.add_argument("--char", action="append", dest="characters",
                        help="角色名（可多次指定）")
    parser.add_argument("--output", choices=["json", "text"], default="json",
                        help="输出格式")

    args = parser.parse_args()

    if not args.characters:
        parser.error("至少需要一个 --char 参数")

    if args.command == "detect":
        results = detect_personas(args.characters)
    elif args.command == "search":
        # 只搜索仓库层面
        results = {}
        for char in args.characters:
            repo_results = search_named_repos(char) + search_awesome_repo(char)
            results[char] = {
                "character": char,
                "repo_results": repo_results,
            }
    elif args.command == "fallback":
        results = {}
        for char in args.characters:
            results[char] = build_fallback(char)

    if args.output == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        print(format_text_output(results))


if __name__ == "__main__":
    main()
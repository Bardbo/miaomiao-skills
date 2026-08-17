#!/usr/bin/env python3
"""
SkillDAG Audit — 只读扫描器，每轮输出技能关系图的结构审计报告。

功能：
1. 扫描所有 SKILL.md 提取 e_self / e_needs 双视角字段
2. 提取五种边类型（depends_on, specializes, composes_with, similar_to, conflicts_with）
3. 三结构不变性检查：无环性 / 不矛盾 / 可逆性（可逆性仅确认 log 存在）
4. 输出格式化报告，供 agent 或 cron job 消费

用法：
  python scripts/dag_audit.py [--skills-dir PATH] [--output json|markdown]
"""

import argparse
import os
import sys
import re
import json
from collections import defaultdict
from pathlib import Path
from datetime import date


def find_all_skills(skills_dir: Path) -> list[dict]:
    """扫描 skills 目录下所有 SKILL.md，返回列表：[{path, name, frontmatter_lines, content}]"""
    skills = []
    for root, dirs, files in os.walk(skills_dir):
        if "SKILL.md" not in files:
            continue
        path = Path(root) / "SKILL.md"
        # 跳过 .git
        if ".git" in root:
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        # 提取 YAML frontmatter
        frontmatter_raw = ""
        content = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter_raw = parts[1].strip()
                content = parts[2].strip()

        frontmatter = parse_frontmatter(frontmatter_raw)
        name = frontmatter.get("name", path.parent.name)

        skills.append({
            "path": str(path),
            "name": name,
            "frontmatter": frontmatter,
            "frontmatter_raw": frontmatter_raw,
            "content": content,
        })
    return skills


def parse_frontmatter(raw: str) -> dict:
    """简易 YAML frontmatter 解析器。只解析我们需要的字段，不依赖 pyyaml。"""
    result = {}
    if not raw:
        return result

    # 行级解析
    lines = raw.splitlines()
    current_key = None
    current_list = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # 新 key: value
        m = re.match(r"^(\w[\w_-]*):\s*(.*)", line)
        if m:
            if current_key and current_list is not None:
                result[current_key] = current_list
                current_list = None
            key, val = m.group(1), m.group(2).strip()
            # 处理 |
            if val == "|" or val == "|2" or val == ">" or val.startswith(">-"):
                current_key = key
                current_list = []
            elif val:
                result[key] = val
                current_key = key
                current_list = None
            else:
                current_key = key
                current_list = None
            continue

        # 列表项 - 开头（用原始 line 保留前导空白供正则匹配）
        lst_m = re.match(r"^\s+-\s+(.*)", line)
        if lst_m and current_key is not None:
            val = lst_m.group(1).strip()
            # 去掉引号
            val = val.strip("\"'")
            if current_list is None:
                current_list = [val]
            else:
                current_list.append(val)
            continue

        # 多行字符串续行（缩进行）
        if current_list is not None and stripped:
            pass  # 续行已在新 key: | 中

    if current_key and current_list is not None:
        result[current_key] = current_list

    return result


def extract_edges_from_frontmatter(skill: dict) -> list[dict]:
    """从 frontmatter 提取边。"""
    edges = []
    name = skill["name"]
    fm = skill["frontmatter"]

    # needs -> depends_on (needs 里的 skill 名)
    needs = fm.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    for need in needs:
        edges.append({
            "from": name,
            "to": need,
            "type": "depends_on",
            "source": "frontmatter.needs",
        })

    # composes_with
    composes = fm.get("composes_with", [])
    if isinstance(composes, str):
        composes = [composes]
    for c in composes:
        edges.append({
            "from": name,
            "to": c,
            "type": "composes_with",
            "source": "frontmatter.composes_with",
        })

    # similar_to
    similar = fm.get("similar_to", [])
    if isinstance(similar, str):
        similar = [similar]
    for s in similar:
        edges.append({
            "from": name,
            "to": s,
            "type": "similar_to",
            "source": "frontmatter.similar_to",
        })

    # conflicts_with
    conflicts = fm.get("conflicts_with", [])
    if isinstance(conflicts, str):
        conflicts = [conflicts]
    for c in conflicts:
        edges.append({
            "from": name,
            "to": c,
            "type": "conflicts_with",
            "source": "frontmatter.conflicts_with",
        })

    # specializes
    specializes = fm.get("specializes", [])
    if isinstance(specializes, str):
        specializes = [specializes]
    for s in specializes:
        edges.append({
            "from": name,
            "to": s,
            "type": "specializes",
            "source": "frontmatter.specializes",
        })

    return edges


def extract_edges_from_content(skill: dict) -> list[dict]:
    """从 SKILL.md 正文的 Markdown 表格中提取边。

    解析 §5.6 风格的技能关系表：
    | from | to | type | evidence |
    """
    edges = []
    content = skill["content"]

    # 标准表格行: | 技能名 | 技能名 | 边类型 | ... |
    table_pattern = re.findall(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(depends_on|specializes|composes_with|similar_to|conflicts_with)\s*\|",
        content,
        re.MULTILINE,
    )
    for from_skill, to_skill, edge_type in table_pattern:
        from_skill = from_skill.strip()
        to_skill = to_skill.strip()
        # 跳过表头行（纯 --- 分隔行已被 [^|]+ 排除）
        if from_skill.lower() in ("来源", "from", "source"):
            continue
        if to_skill.lower() in ("目标", "to", "target"):
            continue
        # 跳过 self-loop
        if from_skill == to_skill:
            continue
        edges.append({
            "from": from_skill,
            "to": to_skill,
            "type": edge_type,
            "source": "content.section-5.6-table",
        })

    return edges


def build_graph(skills: list[dict]) -> dict:
    """构建完整技能图并分析。"""
    all_names = {s["name"] for s in skills}
    edges = []
    skill_needs = {}  # skill_name -> bool (has e_needs)

    for s in skills:
        fm = s["frontmatter"]
        has_needs = "needs" in fm
        skill_needs[s["name"]] = has_needs

        edges.extend(extract_edges_from_frontmatter(s))
        edges.extend(extract_edges_from_content(s))

    # 去重 (same from/to/type)
    seen = set()
    unique_edges = []
    for e in edges:
        key = (e["from"], e["to"], e["type"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    # 按类型分组
    by_type = defaultdict(list)
    for e in unique_edges:
        by_type[e["type"]].append(e)

    # 需要方向性的边（depends_on, specializes）
    directed_types = {"depends_on", "specializes"}
    # 无向边（composes_with, similar_to, conflicts_with）
    undirected_types = {"composes_with", "similar_to", "conflicts_with"}

    directed_edges = [e for e in unique_edges if e["type"] in directed_types]
    undirected_edges = [e for e in unique_edges if e["type"] in undirected_types]

    # ---- 检查 1: 无环性 ----
    cycles = detect_cycles(directed_edges)

    # ---- 检查 2: 不矛盾 ----
    contradictions = detect_contradictions(unique_edges)

    # ---- 检查 3: 可逆性（确认 log 存在）----
    reversibility = check_reversibility()

    # ---- 统计 ----
    skills_no_needs = [s["name"] for s in skills if not skill_needs.get(s["name"])]
    skills_no_edges = [s["name"] for s in skills if not any(
        e["from"] == s["name"] or e["to"] == s["name"] for e in unique_edges
    )]

    return {
        "total_skills": len(skills),
        "total_edges": len(unique_edges),
        "edges_by_type": {k: len(v) for k, v in by_type.items()},
        "directed_edges": directed_edges,
        "undirected_edges": undirected_edges,
        "cycles": cycles,
        "contradictions": contradictions,
        "reversibility": reversibility,
        "skills_missing_needs": skills_no_needs,
        "skills_no_edges": skills_no_edges,
        "all_edges": unique_edges,
    }


def detect_cycles(directed_edges: list[dict]) -> list[list[str]]:
    """DFS 检测 directed_edges 中的环。返回环列表（每个环是节点名列表）。"""
    adj = defaultdict(list)
    for e in directed_edges:
        adj[e["from"]].append(e["to"])

    cycles = []
    visited = set()
    path = []
    path_set = set()

    def dfs(node):
        if node in path_set:
            # 找到环
            idx = path.index(node)
            cycle = path[idx:] + [node]
            cycles.append(cycle)
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for neighbor in adj.get(node, []):
            dfs(neighbor)
        path.pop()
        path_set.discard(node)

    for node in list(adj.keys()):
        dfs(node)

    return cycles


def detect_contradictions(edges: list[dict]) -> list[dict]:
    """检测同一对技能既有 conflicts_with 又有正向边。"""
    positive_types = {"depends_on", "specializes", "composes_with"}
    conflict_pairs = set()
    positive_pairs = set()

    for e in edges:
        key = (e["from"], e["to"])
        if e["type"] == "conflicts_with":
            conflict_pairs.add(key)
        elif e["type"] in positive_types:
            positive_pairs.add(key)

    contradictions = []
    for pair in conflict_pairs:
        if pair in positive_pairs:
            contradictions.append({
                "pair": list(pair),
                "reason": f"同时有 conflicts_with 和正向边",
            })
        # 反向也要检查（conflicts 通常是对称的）
        rev_pair = (pair[1], pair[0])
        if rev_pair in positive_pairs:
            contradictions.append({
                "pair": [pair[1], pair[0]],
                "reason": f"反向同时有 conflicts_with 和正向边",
            })

    return contradictions


def check_reversibility() -> dict:
    """检查是否有边编辑日志"""
    log_path = Path(__file__).parent.parent / "dag_audit_log.json"
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                entries = json.load(f)
            return {"has_log": True, "entries": len(entries), "path": str(log_path)}
        except (json.JSONDecodeError, OSError):
            return {"has_log": False, "entries": 0, "path": str(log_path), "error": "corrupt"}
    return {"has_log": False, "entries": 0, "path": str(log_path)}


def format_markdown(graph: dict) -> str:
    """输出 Markdown 审计报告"""
    lines = []
    lines.append(f"# SkillDAG 审计报告")
    lines.append(f"生成日期：{date.today()}")
    lines.append(f"")
    lines.append(f"## 概览")
    lines.append(f"")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 技能总数 | {graph['total_skills']} |")
    lines.append(f"| 关系边总数 | {graph['total_edges']} |")
    for t, n in sorted(graph["edges_by_type"].items()):
        lines.append(f"| 边类型 `{t}` | {n} |")
    lines.append(f"")

    # 健康检查
    lines.append(f"## 结构不变性检查")
    lines.append(f"")

    # 无环性
    if graph["cycles"]:
        lines.append(f"### ❌ 环检测：发现 {len(graph['cycles'])} 个环")
        for i, cycle in enumerate(graph["cycles"], 1):
            lines.append(f"{i}. `{' → '.join(cycle)}`")
    else:
        lines.append(f"### ✅ 无环性：通过（0 个环）")
    lines.append(f"")

    # 不矛盾
    if graph["contradictions"]:
        lines.append(f"### ❌ 矛盾检测：发现 {len(graph['contradictions'])} 处矛盾")
        for c in graph["contradictions"]:
            lines.append(f"- `{'` ↔ `'.join(c['pair'])}`：{c['reason']}")
    else:
        lines.append(f"### ✅ 不矛盾：通过（0 处矛盾）")
    lines.append(f"")

    # 可逆性
    r = graph["reversibility"]
    if r["has_log"]:
        lines.append(f"### ✅ 可逆性：日志存在（{r['entries']} 条条目）")
    else:
        lines.append(f"### ⚠️ 可逆性：无边编辑日志（dag_audit_log.json 不存在）")
        lines.append(f"  首次运行时没问题，编辑边后自然会生成。")
    lines.append(f"")

    # 缺少双视角声明的技能
    lines.append(f"## 缺失双视角声明（e_needs）")
    lines.append(f"")
    missing = graph["skills_missing_needs"]
    if missing:
        lines.append(f"共 {len(missing)} 个技能缺少 `needs` 字段：")
        for s in sorted(missing):
            lines.append(f"- `{s}`")
    else:
        lines.append(f"所有技能均已声明 `needs` 字段 ✅")
    lines.append(f"")

    # 孤立技能
    lines.append(f"## 孤立技能（无边关系）")
    lines.append(f"")
    isolated = graph["skills_no_edges"]
    if isolated:
        lines.append(f"共 {len(isolated)} 个技能没有任何关系边：")
        for s in sorted(isolated)[:20]:  # 只显示前 20
            lines.append(f"- `{s}`")
        if len(isolated) > 20:
            lines.append(f"- ... 及 {len(isolated) - 20} 个更多")
        lines.append(f"")
        lines.append(f"> 提示：孤立技能不影响正常运行，建议在下次优化时补充 `needs` 字段。")
    else:
        lines.append(f"所有技能均已参与关系图 ✅")
    lines.append(f"")

    # 全部边的详细表
    lines.append(f"## 全部关系边")
    lines.append(f"")
    lines.append(f"| 来源 | 目标 | 类型 | 来源位置 |")
    lines.append(f"|------|------|------|---------|")
    for e in sorted(graph["all_edges"], key=lambda x: (x["type"], x["from"])):
        lines.append(f"| `{e['from']}` | `{e['to']}` | `{e['type']}` | {e['source']} |")
    lines.append(f"")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="SkillDAG Audit — 只读技能关系图扫描器")
    parser.add_argument(
        "--skills-dir",
        default=os.environ.get(
            "HERMES_SKILLS_DIR",
            str(Path.home() / "AppData/Local/hermes/skills")
        ),
        help="Hermes skills 目录路径",
    )
    parser.add_argument(
        "--output", choices=["markdown", "json"], default="markdown",
        help="输出格式（默认 markdown）"
    )
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    if not skills_dir.is_dir():
        print(f"❌ 技能目录不存在：{skills_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 扫描技能目录：{skills_dir}", file=sys.stderr)
    skills = find_all_skills(skills_dir)
    print(f"📦 找到 {len(skills)} 个 SKILL.md", file=sys.stderr)

    graph = build_graph(skills)
    print(f"🔗 提取 {graph['total_edges']} 条关系边", file=sys.stderr)

    if args.output == "json":
        # 输出 JSON（适合程序消费）
        report = {
            "audit_date": str(date.today()),
            "skills_dir": str(skills_dir),
            **graph,
        }
        # 清理不可 JSON 序列化的
        report["all_edges"] = [
            {k: str(v) if not isinstance(v, (str, int, float, bool, list)) else v
             for k, v in e.items()}
            for e in report["all_edges"]
        ]
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(graph))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JD 解析器 —— 岗位解析环节的机械化部分

设计原则：词频统计与分层信号由脚本完成（零幻觉），语义判断留给人工/LLM 复核。

用法:
  # 单份 JD 解析
  python scripts/analyze_jd.py targets/xxx/jd.txt

  # 同类岗位横向对比（抓 5-10 家同岗位 JD，得出真硬性要求）
  python scripts/analyze_jd.py jd1.txt jd2.txt jd3.txt --compare

  # 与母版技能比对，输出命中与缺口
  python scripts/analyze_jd.py jd.txt --master master/master.yaml

  # 生成可直接粘贴进 tailored.yaml 的片段
  python scripts/analyze_jd.py jd.txt --emit targets/xxx/analysis.yaml
"""
import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

# 优先级信号：出现在技术词上下文（前后 40 字）中时的判定依据
SIG_P1 = ["精通", "熟练掌握", "必须", "要求熟练", "深入理解", "扎实", "精通于", "专家级", "核心要求"]
SIG_P3 = ["优先", "加分", "者优先", "有额外加分", "了解", "接触过", "nice to have", "加分项"]
SIG_P2 = ["熟悉", "掌握", "有经验", "使用过", "了解原理", "具备"]

SEC_REQ = ["任职要求", "职位要求", "岗位要求", "任职资格", "我们需要", "requirements", "qualifications"]
SEC_DUTY = ["岗位职责", "工作内容", "你将负责", "主要职责", "responsibilities", "what you"]
SEC_PLUS = ["加分项", "优先条件", "加分", "preferred", "nice to have", "bonus"]

DEGREE_PAT = re.compile(r"(博士|硕士|研究生|本科|统招|全日制|大专)")
YEAR_PAT = re.compile(r"(\d+)\s*年以上|(\d+)\s*年(?:相关|工作|开发)?经验|(\d+)\s*-\s*(\d+)\s*年")


def load_terms(path):
    terms, section = [], None
    if not path.exists():
        print(f"警告：未找到词典 {path}")
        return terms
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^\[(.+?)\](.*)$", s)
        if m:
            section = m.group(1).strip()
            continue
        terms.append((s, section))
    return terms


def build_regex(term):
    if re.fullmatch(r"[\x00-\x7F]+", term):
        return re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", re.I)
    return re.compile(re.escape(term))


def split_sections(text):
    """把 JD 切成 职责 / 要求 / 加分 三段，返回 {段名: 文本}"""
    lines = text.splitlines()
    marks = []
    for i, ln in enumerate(lines):
        low = ln.strip().lower()
        if any(k in low for k in SEC_PLUS) and len(ln.strip()) < 30:
            marks.append((i, "plus"))
        elif any(k in low for k in SEC_REQ) and len(ln.strip()) < 30:
            marks.append((i, "req"))
        elif any(k in low for k in SEC_DUTY) and len(ln.strip()) < 30:
            marks.append((i, "duty"))
    sections = defaultdict(str)
    if not marks:
        sections["req"] = text
        return sections
    marks.sort()
    for idx, (ln, name) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        sections[name] += "\n".join(lines[ln:end]) + "\n"
    return sections


def split_items(text):
    """把 JD 切成语义条目。按行切，超长行再按句号/分号切。

    关键：上下文必须以"条目"为单位，不能用固定字符窗口。
    否则"精通 Go 语言"和下一行的"熟悉 MySQL"会被同一个窗口吞掉，
    导致 MySQL 被误判成 P1。
    """
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) > 80:
            items.extend(s.strip() for s in re.split(r"[。；;]", line) if s.strip())
        else:
            items.append(line)
    return items


def classify(term, text, sections, category=None):
    """返回 (层级, 信号说明)"""
    rx = build_regex(term)
    # 软技能不参与技术分层，谁都写"沟通能力强"，没有命中/缺口意义
    if category == "软技能":
        return "P3", "软技能"
    hits_items = [it for it in split_items(text) if rx.search(it)]
    ctx = " | ".join(hits_items)
    section_names = {name for name, body in sections.items() if rx.search(body)}

    hits_p1 = [s for s in SIG_P1 if s in ctx]
    hits_p3 = [s for s in SIG_P3 if s in ctx]
    hits_p2 = [s for s in SIG_P2 if s in ctx]

    if "plus" in section_names and not hits_p1:
        return "P3", "位于加分项"
    if hits_p1:
        return "P1", f"信号:{hits_p1[0]}"
    if hits_p3 and not hits_p2:
        return "P3", f"信号:{hits_p3[0]}"
    if hits_p2:
        return "P2", f"信号:{hits_p2[0]}"
    if "req" in section_names:
        return "P2", "位于任职要求"
    if "duty" in section_names:
        return "P2", "位于岗位职责"
    return "P3", "无明确信号"


def extract_hard(text):
    d = DEGREE_PAT.search(text)
    y = YEAR_PAT.search(text)
    years = None
    if y:
        years = int(next(g for g in y.groups() if g))
    return (d.group(1) if d else ""), years


def analyze(text, terms):
    sections = split_sections(text)
    found = {}
    for term, sec in terms:
        if build_regex(term).search(text):
            found[term] = sec
    ranked = {"P1": [], "P2": [], "P3": []}
    for term, cat in found.items():
        lvl, why = classify(term, text, sections, cat)
        ranked[lvl].append((term, why, cat))
    for k in ranked:
        ranked[k].sort(key=lambda x: len(x[0]))
    return ranked, sections


def report(name, ranked, degree, years):
    print(f"\n{'='*60}\n{name}\n{'='*60}")
    hard = " / ".join(x for x in [degree, f"{years}年以上" if years else ""] if x)
    print(f"硬性门槛: {hard or '未识别（需人工确认）'}")
    for lvl, label in (("P1", "关键要求（缺失即出局）"), ("P2", "重要要求"), ("P3", "加分项")):
        items = ranked[lvl]
        print(f"\n{lvl} {label}  ({len(items)})")
        for t, why, sec in items:
            print(f"   - {t:<14} {why}")
    return


def compare(files, terms):
    """横向对比。

    关键口径：只统计出现在【职责/要求】段落的词，加分项单独统计。
    否则"大家都写在加分项里的 Kubernetes"会被误判成硬性要求。
    """
    freq, plus_freq = defaultdict(list), defaultdict(list)
    n = len(files)
    for f in files:
        text = Path(f).read_text(encoding="utf-8", errors="ignore")
        secs = split_sections(text)
        main_body = (secs.get("req", "") + "\n" + secs.get("duty", "")).strip()
        plus_body = secs.get("plus", "")
        if not main_body:
            main_body = text
        stem = Path(f).stem
        for term, _ in terms:
            rx = build_regex(term)
            if rx.search(main_body):
                freq[term].append(stem)
            elif plus_body and rx.search(plus_body):
                plus_freq[term].append(stem)

    common, mid, rare = [], [], []
    for term, hits in freq.items():
        rate = len(hits) / n
        if rate >= 0.7:
            common.append((term, len(hits)))
        elif rate >= 0.3:
            mid.append((term, len(hits)))
        else:
            rare.append((term, len(hits)))
    common.sort(key=lambda x: -x[1])
    mid.sort(key=lambda x: -x[1])
    rare.sort(key=lambda x: -x[1])
    plus_common = sorted(
        [(t, len(h)) for t, h in plus_freq.items() if len(h) / n >= 0.5], key=lambda x: -x[1]
    )

    print(f"\n{'='*60}\n{n} 份同类 JD 横向对比\n{'='*60}")
    if n < 5:
        print(f"（样本 {n} 份偏少，结论仅供粗略参考，建议攒到 5-10 份）")
    print("\n真硬性要求（≥70% JD 在职责/要求中提及）→ 归入 P1")
    for t, c in common:
        print(f"   {t:<16} {c}/{n}")
    print("\n常见要求（30%-70%）→ 归入 P2")
    for t, c in mid:
        print(f"   {t:<16} {c}/{n}")
    if plus_common:
        print("\n高频加分项（≥50% JD 提及，但都不是硬门槛）→ 归入 P3")
        for t, c in plus_common:
            print(f"   {t:<16} {c}/{n}")
    print("\n个性化偏好（<30%）→ 归入 P3，针对该公司定制时才用")
    for t, c in rare:
        print(f"   {t:<16} {c}/{n}")
    print("\n提示：横向统计是纯词频，零幻觉；单家公司的 JD 语义判断才需要 LLM 参与。")
    return common, mid, rare


def match_master(ranked, master_path):
    data = yaml.safe_load(Path(master_path).read_text(encoding="utf-8")) or {}
    have = {}
    for s in data.get("skills") or []:
        have[s.get("name", "")] = s.get("evidence_refs") or []
    tags = set()
    for e in data.get("experiences") or []:
        tags.update(e.get("tech_tags") or [])
        for a in e.get("achievements") or []:
            tags.update(a.get("tech_tags") or [])
    print(f"\n{'='*60}\n与母版比对\n{'='*60}")
    hit, gap, weak = [], [], []
    for lvl in ("P1", "P2", "P3"):
        for t, _, _ in ranked[lvl]:
            key = next((k for k in have if k.lower() == t.lower()), None)
            if key:
                (hit if have[key] else weak).append((t, lvl, len(have[key])))
            elif t in tags:
                hit.append((t, lvl, 0))
            else:
                gap.append((t, lvl))
    print("\n已命中（母版有证据支撑）")
    for t, lvl, c in hit:
        print(f"   [{lvl}] {t}")
    if weak:
        print("\n命中但无证据（出片时会被降权，建议补挂成就）")
        for t, lvl, _ in weak:
            print(f"   [{lvl}] {t}  ← skills 中 evidence_refs 为空")
    print("\n缺口（母版完全没有）")
    for t, lvl in gap:
        print(f"   [{lvl}] {t}")
    p1_gap = [t for t, lvl in gap if lvl == "P1"]
    if p1_gap:
        print(f"\n注意：P1 缺口 {len(p1_gap)} 项 —— 这些是硬伤，靠改写解决不了，")
        print("要么回母版补真实经历，要么诚实评估这个岗位是否该投。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--compare", action="store_true", help="多份 JD 横向对比")
    ap.add_argument("--master", help="与母版技能比对")
    ap.add_argument("--emit", help="输出可直接粘贴进 tailored.yaml 的 YAML 片段")
    args = ap.parse_args()

    terms = load_terms(ROOT / "config" / "tech_terms.txt")
    if not terms:
        return 1

    if args.compare or len(args.files) > 1:
        compare(args.files, terms)
        if not args.emit:
            return 0

    text = Path(args.files[0]).read_text(encoding="utf-8", errors="ignore")
    ranked, _ = analyze(text, terms)
    degree, years = extract_hard(text)
    report(Path(args.files[0]).stem, ranked, degree, years)

    if args.master:
        match_master(ranked, args.master)

    if args.emit:
        out = {
            "jd_snapshot": {
                "source_url": "",
                "fetched_at": "",
                "text": text,
            },
            "analysis": {
                "hard_requirements": {"degree": degree, "years": years},
                "p1_critical": [t for t, _, _ in ranked["P1"]],
                "p2_important": [t for t, _, _ in ranked["P2"]],
                "p3_nice": [t for t, _, _ in ranked["P3"]],
            },
        }
        p = Path(args.emit)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            yaml.safe_dump(out, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"\n已写入 {p}（分层结果需人工复核后再用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

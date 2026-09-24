#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bullet 体检器 polish.py —— 把「润色」里可机械判定的部分做成检查。

为什么需要它：
    「帮我润色简历」这类需求，人工做一遍要通读全部 bullet，
    而其中 70% 的问题（缺结果、缺难点、职责型空话、强动词无证据）
    是**可以直接判定的**。靠人眼过一遍，第 30 条之后必然开始漏。

    本脚本不改写任何内容 —— 它只做体检并给出改写方向。
    真正的改写需要事实，而事实只能从用户那里来。

交付：
    1. 每条 bullet 的 L0–L3 分级（见 polish-playbook.md 第 1 节）
    2. 缺失要素清单（result / difficulty / method / scope）
    3. 可机械判定的问题（动词重复、超长、占位残留、强动词无证据）
    4. 汇总的「润色优先级」—— 先改哪几条收益最大

用法：
    python scripts/polish.py --person 张三
    python scripts/polish.py --person 张三 --only L0,L1    # 只看低级别
    python scripts/polish.py --person 张三 --json
"""

import argparse
import io
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 包根：config/
WORKSPACE = os.environ.get("RESUME_WORKSPACE") or os.getcwd()        # 工作区：people/ 所在目录
PEOPLE = os.path.join(WORKSPACE, "people")

# ── 动词强度分级（见 polish-playbook.md §3.1）
# 强动词必须与 evidence 匹配：用超过证据强度的动词 = 邀请对方追问到崩
VERB_STRONG = ("主导", "统筹", "牵头", "从零搭建", "从 0 搭建", "从0搭建",
               "负责整体", "全面负责", "首创", "首次")
VERB_MID = ("设计", "搭建", "重构", "优化", "推动", "建立", "独立负责",
            "独立完成", "独立承担", "从零")
VERB_WEAK = ("参与", "协助", "配合", "跟进", "支持")

# ── 职责型信号：出现这些且没有 method/result 的，基本是 L0
DUTY_SIGNALS = ("负责", "参与", "协助", "处理", "管理", "维护", "跟进", "支持")

# ── 占位残留（成稿里出现即事故）
PLACEHOLDERS = ("待补", "待确认", "待填", "【", "TODO", "TBD", "？", "??", "xxx")


def load_master(person):
    p = os.path.join(PEOPLE, person, "master.yaml")
    if not os.path.exists(p):
        raise SystemExit("母版不存在：%s" % p)
    with io.open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def em_width(text):
    """视觉宽度（em）。与 density.py 保持一致。"""
    import unicodedata
    w = 0.0
    for ch in str(text or ""):
        w += 1.0 if unicodedata.east_asian_width(ch) in ("W", "F", "A") else 0.52
    return w


def bullet_text(a):
    """复刻渲染拼装，用于量长度与查占位。"""
    parts = []
    act, obj = (a.get("action") or "").strip(), (a.get("object") or "").strip()
    meth, diff = (a.get("method") or "").strip(), (a.get("difficulty") or "").strip()
    res = a.get("result") or {}
    if isinstance(res, dict):
        r = " ".join(x for x in [res.get("metric", ""), res.get("value", "")] if x).strip()
        if res.get("scope"):
            r = (r + "（范围：" + res["scope"] + "）") if r else "范围：" + res["scope"]
    else:
        r = str(res or "").strip()
    if act and obj:
        parts.append(act + obj)
    elif obj:
        parts.append(obj)
    if meth:
        parts.append(meth)
    if r:
        parts.append(r)
    if diff:
        parts.append("（难点：" + diff + "）")
    return "，".join(p for p in parts if p)


def grade(a):
    """给单条 bullet 定级 L0–L3，并列出缺失要素。"""
    issues = []
    meth = (a.get("method") or "").strip()
    diff = (a.get("difficulty") or "").strip()
    res = a.get("result") or {}
    has_res = bool((res.get("value") or "").strip()) if isinstance(res, dict) else bool(str(res or "").strip())
    has_scope = bool((res.get("scope") or "").strip()) if isinstance(res, dict) else False
    act = (a.get("action") or "").strip()
    txt = bullet_text(a)

    if not meth and not has_res:
        level = "L0"
        issues.append("职责型：既没说怎么做，也没说结果 —— 润色救不了，回采集")
    elif meth and not has_res:
        level = "L1"
        issues.append("缺结果：做了什么清楚，做得怎么样不知道")
    elif has_res and not diff:
        level = "L2"
        issues.append("缺难点：结果有，但说不清为什么不是谁都能做")
    else:
        level = "L3"

    if has_res and not has_scope:
        issues.append("缺影响范围：结果有了，但看不出覆盖多广、谁在用")
    if not meth:
        issues.append("缺方法：关键词无处安放，且读不出技术含量")

    # 强动词与证据不匹配
    ev = a.get("evidence")
    if any(act.startswith(v) for v in VERB_STRONG) and ev not in ("verified", "self_reported"):
        issues.append("强动词「%s」配 %s 证据 —— 出片会隐藏，或面试必崩" % (act, ev))

    # 长度
    w = em_width(txt)
    lines = max(1, int(w // 45) + (1 if w % 45 else 0))
    if lines > 3:
        issues.append("过长（约 %d 行）：拆分或砍修饰" % lines)
    elif w < 20:
        issues.append("过短（%d 字）：信息量不足，撑不起一行" % int(w))

    # 占位残留
    for ph in PLACEHOLDERS:
        if ph in txt:
            issues.append("占位残留「%s」" % ph)
            break

    return {"level": level, "issues": issues, "text": txt,
            "lines": lines, "action": act, "evidence": ev}


def run(master, only=None):
    rows = []
    verb_counter = {}

    for e in (master.get("experiences") or []):
        org, title = e.get("org", ""), e.get("title", "")
        achs = e.get("achievements") or []
        for a in achs:
            g = grade(a)
            if only and g["level"] not in only:
                continue
            g.update({"id": a.get("id"), "org": org, "title": title,
                      "period": e.get("period", {})})
            rows.append(g)
            verb_counter[g["action"]] = verb_counter.get(g["action"], 0) + 1

    # 句首动词重复：同一段经历里多条 bullet 用同一动词，读起来像流水账
    from collections import Counter
    per_exp = Counter((r["org"], r["action"]) for r in rows)
    for r in rows:
        if per_exp[(r["org"], r["action"])] > 1 and r["action"]:
            r["issues"].append("同段动词「%s」重复 %d 次 —— 换个说法"
                               % (r["action"], per_exp[(r["org"], r["action"])]))

    # 排序：级别低的排前面（最该改的先看到）
    order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    rows.sort(key=lambda r: (order[r["level"]], r["org"]))
    return rows


def fmt(rows, person):
    L = []
    a = L.append
    dist = {}
    for r in rows:
        dist[r["level"]] = dist.get(r["level"], 0) + 1

    a("=" * 66)
    a("bullet 体检  ·  %s" % person)
    a("=" * 66)
    a("")
    a("【分级分布】共 %d 条" % len(rows))
    for lv in ("L0", "L1", "L2", "L3"):
        n = dist.get(lv, 0)
        pct = (n * 100.0 / len(rows)) if rows else 0
        bar = "█" * int(pct / 3)
        a("  %s  %2d 条  %4.0f%%  %s" % (lv, n, pct, bar))
    a("")
    if rows:
        strong = (dist.get("L2", 0) + dist.get("L3", 0)) * 100.0 / len(rows)
        a("  L2 以上占比 %.0f%%（目标 ≥60%%，且至少 1 条 L3）" % strong)
        if dist.get("L0", 0):
            a("  ⚠ %d 条 L0 职责型 —— 这些不是润色能救的，要回采集" % dist["L0"])
        a("")

    cur = None
    for r in rows:
        if r["org"] != cur:
            cur = r["org"]
            a("── %s　%s ──" % (r["org"], r.get("title", "")))
        a("  [%s] %s" % (r["level"], r["id"]))
        a("      %s" % (r["text"][:100] + ("…" if len(r["text"]) > 100 else "")))
        for it in r["issues"]:
            a("      · %s" % it)
        a("")

    if not rows:
        a("（没有匹配的 bullet）")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="bullet 体检与润色方向")
    ap.add_argument("--person", required=True)
    ap.add_argument("--only", default="", help="只显示指定级别，逗号分隔，如 L0,L1")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    master = load_master(args.person)
    only = set(x.strip().upper() for x in args.only.split(",") if x.strip()) or None
    rows = run(master, only)

    if args.json:
        print(json.dumps({"person": args.person, "rows": rows},
                         ensure_ascii=False, indent=2))
    else:
        print(fmt(rows, args.person))

    # 有 L0/L1 即视为未达标（退出码供脚本串联用）
    bad = sum(1 for r in rows if r["level"] in ("L0", "L1"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

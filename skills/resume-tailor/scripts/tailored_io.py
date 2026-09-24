#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""定制版 tailored.yaml 的统一加载 —— 兼容两种 schema。

⚠ 为什么必须有这个文件（一次真实的静默失效事故）：

    早期定制版把 selection / target / gaps / proposals 写成**顶层键**，
    与 `tailored:` 平级，而 `tailored:` 里只有 id / master_version / created_at：

        tailored:
          id: t-xxx
          master_version: 8
        selection:          # ← 顶层，不在 tailored 里
          hidden_achievements: [...]
        target:             # ← 顶层
          analysis: {...}

    现行 schema 则把所有字段嵌在 `tailored:` 下。

    而 check_gates.py 与 render_resume.py 都一律 `.get("tailored")` 解包一层
    再取 selection / target —— 于是**旧 schema 文件的筛选与 JD 依据全部拿不到**
    （实测 4 个定制版里 3 个中招）：
      · selection=None → 该藏的没藏，成稿按未筛选渲染
      · target.analysis=None → G3 直接跳过，报「无 JD 依据」
    最坏的是它**不报错**：闸门照样输出「通过」，看着和真的一样。

    → 故在此统一归一化，新旧两种写法都能读，杜绝这类静默失效。
"""
from pathlib import Path

import yaml


def _load(path):
    p = Path(path)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_tailored(path):
    """加载定制版并返回**归一化后**的 tailored 字典。

    归一化规则：以 `tailored:` 内的内容为主；若其中缺少某字段而顶层有同名字段，
    则用顶层补齐。这样两种 schema 都得到同一个结果，调用方不必关心文件年代。
    """
    raw = _load(path)
    if not isinstance(raw, dict):
        return {}

    t = raw.get("tailored")
    merged = dict(t) if isinstance(t, dict) else {}

    for k, v in raw.items():
        if k == "tailored":
            continue
        # 只在 tailored 里**没有有效值**时才用顶层补齐，避免覆盖现行 schema 的内容
        if k not in merged or merged.get(k) in (None, [], {}, ""):
            merged[k] = v

    return merged


def schema_kind(path):
    """诊断用：返回 'nested'（现行）/ 'flat'（早期顶层写法）/ 'unknown'。"""
    raw = _load(path)
    if not isinstance(raw, dict):
        return "unknown"
    t = raw.get("tailored")
    has_flat = any(k in raw for k in ("selection", "target", "rewrite_policy"))
    has_nested = isinstance(t, dict) and any(
        k in t for k in ("selection", "target", "rewrite_policy"))
    if has_nested:
        return "nested"
    if has_flat:
        return "flat"
    return "unknown"


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(f"{p}\n  schema = {schema_kind(p)}")
        d = load_tailored(p)
        sel = d.get("selection") or {}
        an = (d.get("target") or {}).get("analysis") or {}
        print(f"  selection 可见 = {bool(sel)}")
        print(f"  analysis  可见 = {bool(an)}")

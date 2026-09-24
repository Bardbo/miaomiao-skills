#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gate 静态硬校验：G1 溯源 / G2 证据 / G3 覆盖 / G4 去 AI 味 / 版本漂移

用法:
    python check_gates.py --master people/<人>/master.yaml \
                          --target people/<人>/targets/<岗位>/tailored.yaml \
                          [--draft draft.md] [--rendered output/resume-final.html] \
                          [--jd 岗位JD.txt] [--strict]

为什么必须用脚本:
    写在提示词里的规则会被 LLM 绕过; 写在脚本里的不会。
    evidence 字段之所以有价值, 正是因为有这道硬校验兜底。

⚠ 历史事故（本次修复）:
    旧版按「加法白名单」理解 selection（期待 experiences / achievements 是选中列表），
    而 render_resume.py 实际按「减法黑名单」实现（hidden_achievements / hidden_skills …）。
    两者对不上，导致 G1 遍历到 0 个条目 —— 闸门恒真，17 个警告照样判「通过」。
    防造假的核心防线失效了却没人发现，因为**通过的报告看起来和真的一样**。

    本版改为复刻 render_resume.py 的真实筛选语义，先算出「生效条目集」再校验；
    且任何被引用的 ID 若不存在于母版一律 ERROR ——
    拼错的 ID 在减法语义下是**静默失效**（既不报错也不生效），必须拦住。

退出码: 0 = 通过; 1 = 有 ERROR（--strict 时警告也拦）
"""
import argparse
import html as _html
from html.parser import HTMLParser
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tailored_io import load_tailored   # noqa: E402  兼容新旧两种 tailored schema

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]   # 包根：resume-tailor/（config/ assets/ scripts/）

errors = []
warns = []
infos = []


def err(gate, msg):
    errors.append((gate, msg))


def warn(gate, msg):
    warns.append((gate, msg))


def info(gate, msg):
    infos.append((gate, msg))


def load(p):
    path = Path(p)
    if not path.exists():
        print(f"[错误] 找不到文件: {path}")
        sys.exit(2)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# 复刻 render_resume.py 的筛选语义，算出真正会出片的条目集
# ---------------------------------------------------------------------------
# selection 支持两套写法（见 render_resume.py:568-601）：
#   experiences / achievements   白名单（只显示列出的，按给定顺序）
#   hidden_experiences / hidden_achievements / hidden_skills /
#   hidden_publications / hidden_patents / hidden_honors / hidden_ai  黑名单
# 两者可共存：先按白名单裁，再按黑名单裁。

BLACKLISTS = [
    ("hidden_experiences", "experiences"),
    ("hidden_achievements", "achievements"),
    ("hidden_skills", "skills"),
    ("hidden_publications", "publications"),
    ("hidden_patents", "patents"),
    ("hidden_honors", "honors"),
    ("hidden_ai", "ai_native"),
]


def _index(items):
    """按 id 与 name 同时建索引 —— 黑名单两种写法都接受。"""
    idx = {}
    for it in items or []:
        if not isinstance(it, dict):
            continue
        if it.get("id"):
            idx[str(it["id"])] = it
        if it.get("name"):
            idx[str(it["name"])] = it
    return idx


def resolve_selection(master, tailored):
    """返回 (生效条目集, 引用错误列表)。

    生效集里每一项都是母版的**原对象**，不是副本 ——
    后续 G2/G3 检查的就是真正会出片的内容。
    """
    sel = tailored.get("selection") or {}
    exps_all = master.get("experiences") or []
    exp_idx = _index(exps_all)
    ach_idx = {}
    for e in exps_all:
        for a in e.get("achievements") or []:
            if isinstance(a, dict) and a.get("id"):
                ach_idx[str(a["id"])] = a

    # ---- 校验被引用 ID 的存在性（拼错 = 静默失效，必须拦）----
    bad_refs = []
    for key in ("experiences", "entry_ids"):
        for rid in sel.get(key) or []:
            if str(rid) not in exp_idx:
                bad_refs.append(("经历", key, rid))
    for rid in sel.get("achievements") or []:
        if str(rid) not in ach_idx:
            bad_refs.append(("成就", "achievements", rid))

    # ---- 生效经历 ----
    ids = sel.get("experiences") or sel.get("entry_ids")
    hid = {str(x) for x in (sel.get("hidden_experiences") or [])}
    if ids:
        eff_exps = [exp_idx[str(i)] for i in ids if str(i) in exp_idx]
    else:
        eff_exps = [e for e in exps_all if str(e.get("id")) not in hid]
    # 黑名单在白名单之后生效（文档语义：白名单优先、黑名单兜底）
    eff_exps = [e for e in eff_exps if str(e.get("id")) not in hid]

    # ---- 生效成就（先白名单后黑名单）----
    show = {str(x) for x in (sel.get("achievements") or [])}
    hide = {str(x) for x in (sel.get("hidden_achievements") or [])}
    eff_ach = []
    for e in eff_exps:
        for a in e.get("achievements") or []:
            if not isinstance(a, dict) or not a.get("id"):
                continue
            aid = str(a["id"])
            if show and aid not in show:
                continue
            if aid in hide:
                continue
            eff_ach.append(a)

    # ---- 其余生效集合（纯黑名单减法）----
    eff = {"experiences": eff_exps, "achievements": eff_ach}
    for sel_key, col in BLACKLISTS:
        if sel_key in ("hidden_experiences", "hidden_achievements"):
            continue
        items = master.get(col) or []
        idx = _index(items)
        hid = set()
        for rid in sel.get(sel_key) or []:
            r = str(rid)
            if r in idx:
                hid.add(r)
            else:
                bad_refs.append((col, sel_key, rid))
        eff[col] = [it for it in items
                    if str(it.get("id") or it.get("name")) not in hid]

    return eff, bad_refs


# ---------------------------------------------------------------------------
# G1 溯源
# ---------------------------------------------------------------------------
def g1_trace(master, tailored, eff, bad_refs):
    for col, key, rid in bad_refs:
        err("G1", f"selection.{key} 引用了「{rid}」，但母版里没有这个{col} ID"
                  f" —— 该约束会**静默失效**（既不报错也不生效），请核对或删除")

    # L4 硬闸门：定制版不得新增母版里没有的内容
    pol = tailored.get("rewrite_policy") or {}
    level = str(pol.get("level") or "").strip().upper()
    if level == "L4":
        err("G1", "rewrite_policy.level = L4（新增母版没有的内容）—— 硬 Gate 拦截。"
                  "正确动作是把缺的内容作为新条目加进母版并标 pending，由本人去补")

    # C 类回流闸门：AI 推断内容禁止回流母版
    for i, pr in enumerate(tailored.get("proposals") or [], 1):
        if not isinstance(pr, dict):
            continue
        if str(pr.get("type", "")).strip().upper() == "C" and \
                str(pr.get("decision", "")).strip().lower() == "accepted":
            err("G1", f"proposals[{i}] 是 C 类（推断填充）却被裁决为 accepted"
                      f" —— C 类闸门必须焊死，禁止回流母版")

    # unusable 条目不得进入任何定制版
    for a in eff["achievements"]:
        if a.get("evidence") == "unusable":
            err("G1", f"{a.get('id')} 证据状态为 unusable（权属归他方/涉密）"
                      f" —— 禁止进入任何定制版，请加进 selection.hidden_achievements")

    n_ach = len(eff["achievements"])
    n_exp = len(eff["experiences"])
    print(f"G1 溯源：生效 {n_exp} 段经历 / {n_ach} 条成就，引用错误 {len(bad_refs)} 处")


# ---------------------------------------------------------------------------
# G2 证据
# ---------------------------------------------------------------------------
def g2_evidence(master, eff):
    n_pending = n_inferred = n_risky = 0
    for a in eff["achievements"]:
        ev = a.get("evidence", "pending")
        aid = a.get("id", "?")
        if ev == "inferred":
            n_inferred += 1
            err("G2", f"{aid} 证据状态为 inferred —— 禁止出现在成品中")
        elif ev == "pending":
            n_pending += 1
            warn("G2", f"{aid} 证据状态为 pending —— 出片会被隐藏，"
                       f"且不得写成确定语气；要写就让本人确认后转 self_reported")
        if a.get("strength") == "strong" and ev != "verified":
            if ev == "pending":
                n_risky += 1
                err("G2", f"{aid} 含强主张（主导/从0到1）但证据状态为 {ev}"
                          f" —— 必须降级为「参与」")
            elif ev == "self_reported":
                warn("G2", f"{aid} 强主张来自本人陈述（无第三方验证）"
                           f" —— 面试必追问细节，确认讲得清")

    # 技能：只查生效且未归档的。
    # 旧版扫全量（含 archived），噪声把有效信号淹了 —— 17 条警告里大部分是噪音。
    n_unbacked = 0
    for s in eff.get("skills") or []:
        if s.get("status") == "archived":
            continue
        if not (s.get("evidence_refs") or []):
            n_unbacked += 1
            if s.get("kind") == "commodity":
                warn("G2", f"技能「{s.get('name')}」是 commodity 却既无佐证、"
                           f"也没藏进任何交付物 bullet —— 等于只在母版里占位，"
                           f"要么挂到交付物，要么归档")
            else:
                warn("G2", f"技能「{s.get('name')}」无证据引用 —— 出片时会被降权或隐藏")

    print(f"G2 证据：inferred {n_inferred} / pending {n_pending} / "
          f"强主张风险 {n_risky} / 无佐证技能 {n_unbacked}")


# ---------------------------------------------------------------------------
# G3 JD 关键词覆盖
# ---------------------------------------------------------------------------
SKIP_KEYS = {"rationale", "evidence_note", "why", "note", "question",
             "impact", "reason", "risk", "comment"}


def _collect_text(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in SKIP_KEYS:
                continue
            _collect_text(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _collect_text(v, out)


def _norm(txt):
    """归一化：HTML 实体 → 字符 / 去标签 / 压空白 / 转小写。

    不归一化的话 &amp; 之类实体会把匹配打掉，同一份简历在不同渲染产物间
    覆盖率会漂 —— 这是「G3 数字每次都不一样」的根因之一。
    """
    if not txt:
        return ""
    txt = _html.unescape(txt)
    txt = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", txt)
    txt = re.sub(r"(?s)<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip().lower()


class _TextExtractor(HTMLParser):
    """提取可见正文，跳过 class 含 noprint / gaps / footer 的**整个子树**。

    ⚠ 为什么要剔：gaps 脚注写的是「还缺什么」—— 比如
    「是否持有中国证券投资基金业协会的基金从业资格？」这句话里就含
    「基金从业资格」。若把脚注算进覆盖率，**缺失的硬性要求反而会被判成命中**，
    覆盖率虚高。这正是本产品要防的自欺；且 noprint 区块本来就不进 PDF。

    为什么用解析器而不是正则：gaps 块内有 <li> / <b> / <span class='empty'>
    等嵌套，正则的 .*?</div> 会在第一个 </div> 处提前收尾，把脚注正文留在
    文本里（实测「补齐这些」被剔、基金从业资格却仍在）。解析器按标签栈跳过
    整棵子树才可靠。
    """
    # pending = 【待补】批注，是给本人看的校对提示，不是简历正文
    SKIP_CLS = re.compile(r"(?:^|\s)(?:noprint|gaps|footer|pending)(?:\s|$)")

    def __init__(self):
        super().__init__(convert_charrefs=True)   # &amp; 之类实体直接还原
        self.parts = []
        self.stack = []                           # 每层 True = 该子树被跳过

    def _skipping(self):
        return any(self.stack)

    def handle_starttag(self, tag, attrs):
        cls = " ".join(v for k, v in attrs if k == "class") or ""
        skip = (self._skipping() or tag in ("script", "style")
                or bool(self.SKIP_CLS.search(cls)))
        self.stack.append(skip)

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not self._skipping():
            self.parts.append(data)

    def text(self):
        return " ".join(self.parts)


def _s(v):
    """字段值转字符串 —— result.value / baseline / scope 用户常填数字。

    闸门不该因为 `baseline: 3` 这种写法崩掉：用户看到的是 Python 堆栈而不是
    「简历哪里有问题」。render_resume.py 早有同款容错，这里补上，
    否则 G5 会在第一个数字型字段处 AttributeError（实测赵六案例中招）。
    """
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return str(v)


def _html_text(txt):
    """成稿 HTML → 可见正文（已剔除 noprint / gaps / footer 子树）。"""
    p = _TextExtractor()
    try:
        p.feed(txt)
        p.close()
    except Exception:
        return txt          # 解析失败就退回原文，宁可少剔也不要静默丢正文
    return p.text()


def _resolve_rendered(tailored, target_path, explicit, prefer="final"):
    """成稿/草稿 HTML 的解析：显式路径 > tailored.output.path 推导 > 目录兜底。

    prefer="final" 给 G3（覆盖率按成稿算，draft 的【待补】批注会污染统计）；
    prefer="draft" 给 G4（去 AI 味要扫作者写出的草稿，且 draft 一定存在时才扫）。
    """
    if explicit:
        return Path(explicit)
    out = (tailored.get("output") or {}).get("path") or ""
    if out and target_path:
        # output.path 是相对该人目录写的（如 output/resume-xx-draft.docx）。
        # target 路径形如 people/<人>/targets/<岗位>/tailored.yaml，
        # 往回数三层才是该人目录：0=<岗位> 1=targets 2=<人>
        person_dir = Path(target_path).resolve().parents[2]
        base = re.sub(r"\.docx$", ".html", out, flags=re.I)
        if prefer == "draft":
            cands = (re.sub(r"-final\.html$", "-draft.html", base, flags=re.I), base)
        else:
            cands = (re.sub(r"-draft\.html$", "-final.html", base, flags=re.I), base)
        for cand in cands:
            p = person_dir / cand
            if p.exists():
                return p

    # 兜底：output.path 指向的文件可能根本不存在（实测「方向B-安稳向」写的
    # 是 output/方向B-安稳向.html，实际产物却是 resume-方向B-安稳向-draft.html）。
    # 再按「定制版目录名」在该人 output/ 里找一遍。
    if target_path:
        tp = Path(target_path).resolve()
        out_dir = tp.parents[2] / "output"
        if out_dir.is_dir():
            tname = tp.parent.name
            cands = sorted(out_dir.glob(f"*{tname}*.html")) or \
                    sorted(out_dir.glob("*.html"))
            if cands:
                if prefer == "draft":
                    drafts = [c for c in cands if "draft" in c.name]
                    return (drafts or cands)[0]
                finals = [c for c in cands if "final" in c.name]
                return (finals or cands)[0]
    return None


def _haystack(master, eff, rendered_path):
    """优先用真实成稿文本；拿不到则退化为「母版全量 + 生效条目」估算并 WARN。"""
    if rendered_path:
        p = Path(rendered_path)
        if p.exists():
            return _norm(_html_text(p.read_text(encoding="utf-8"))), "成稿文本"
        warn("G3", f"找不到成稿文件 {rendered_path}，改用母版估算覆盖率")
    out = []
    _collect_text(eff, out)
    # 生效条目只有经历 + 成就；教育 / 技能 / 摘要必须另外补进来，
    # 否则「硕士」「估值」这类落在别处的词会被误判为未命中。
    for k in ("education", "educations", "skills", "summary",
              "basics", "profile", "honors", "publications", "certificates"):
        if isinstance(master, dict) and k in master:
            _collect_text(master.get(k), out)
    return _norm(" ".join(out)), "母版估算（未含成稿筛选与改写效果）"


def _jd_terms(tailored, jd_path):
    """取 P1/P2/P3：优先人工复核过的 analysis，其次现场解析 JD 原文。"""
    an = (tailored.get("target") or {}).get("analysis") or {}
    p1 = [str(x).strip() for x in (an.get("p1_critical") or []) if str(x).strip()]
    p2 = [str(x).strip() for x in (an.get("p2_important") or []) if str(x).strip()]
    p3 = [str(x).strip() for x in (an.get("p3_nice") or []) if str(x).strip()]
    if p1 or p2 or p3:
        # 注意：这里返回的是**词表来源**，不是覆盖率的依据 ——
        # 旧文案「依据 target.analysis（人工复核）」被误读成「覆盖率靠人工判定」，
        # 实际命中率一律按文本真匹配算。
        return p1, p2, p3, "target.analysis 词表（人工复核）"

    text = ""
    if jd_path and Path(jd_path).exists():
        text = Path(jd_path).read_text(encoding="utf-8")
    else:
        snap = (tailored.get("target") or {}).get("jd_snapshot") or {}
        text = snap.get("text") or ""
    if not text.strip():
        return [], [], [], None

    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import analyze_jd as A
    except Exception as e:
        warn("G3", f"无法加载 analyze_jd 解析 JD：{e}")
        return [], [], [], None
    terms = A.load_terms(ROOT / "config" / "tech_terms.txt")
    ranked, _deg, _yr = A.analyze(text, terms)
    g = lambda lv: [t for t, _s, _c in ranked.get(lv, [])]
    return g("P1"), g("P2"), g("P3"), "JD 现场解析词表"


def _split_term(t):
    """JD 词常带括号备注或斜杠列举，拆开逐个匹配。"""
    parts = re.split(r"[（(]|）|\)|、|,|，|/|；|;]", t)
    return [x.strip() for x in parts if x.strip()]


def _looks_like_clause(t):
    """P1 词条疑似**描述性长句**（JD 条款）而非可匹配的关键词。

    为什么必须识别：JD 里写着「5 年以上权益投研经验」「无监管处罚与行业违规记录」
    「可公开查证的投资业绩」—— 这些是**条款**，不是 ATS 关键词，按字面在任何简历里
    都匹配不到。若不识别，覆盖率会被系统性低估，然后把「词表写错了」误判成
    「这个人不匹配」——冤枉候选人，也让闸门的结论不可信。
    带分隔符（/ 、）的会被 _split_term 拆开，不算长句；纯 ASCII（Oracle/JavaScript）
    是正常关键词，也不算。
    """
    if re.search(r"[/／、,，;；]", t):
        return False
    return len(t) > 7 and re.search(r"[\u4e00-\u9fff]", t) is not None


def g3_coverage(master, tailored, eff, rendered_path, jd_path, target_path=None):
    p1, p2, p3, src = _jd_terms(tailored, jd_path)
    if not (p1 or p2 or p3):
        print("G3 覆盖：无 JD 依据，跳过（用 --jd 传入 JD 原文，"
              "或在 target.analysis 里填 p1_critical / p2_important）")
        warn("G3", "本定制版没有 JD 依据 —— 「针对这个岗位定制」无法验证，"
                   "成稿可能只是一份通用简历")
        return

    resolved = _resolve_rendered(tailored, target_path, rendered_path)
    hay, hay_src = _haystack(master, eff, resolved)
    if hay_src != "成稿文本":
        warn("G3", "未取到成稿 HTML，本次覆盖率为估算值 —— "
                   "请用 --rendered 指向成稿 HTML 才能测真实命中率")

    report = {}
    for lvl, terms in (("P1", p1), ("P2", p2), ("P3", p3)):
        hit, miss = [], []
        for t in terms:
            cands = _split_term(t) or [t]
            if any(_norm(c) in hay for c in cands):
                hit.append(t)
            else:
                miss.append(t)
        report[lvl] = (hit, miss)

    tot_hit = sum(len(v[0]) for v in report.values())
    tot = tot_hit + sum(len(v[1]) for v in report.values())
    rate = (tot_hit / tot * 100) if tot else 0.0
    print(f"G3 覆盖：命中 {tot_hit}/{tot}（{rate:.0f}%，词表 {src}，命中基于{hay_src}）")

    for lvl in ("P1", "P2", "P3"):
        hit, miss = report[lvl]
        if not (hit or miss):
            continue
        print(f"   {lvl}: 命中 {len(hit)} / 共 {len(hit) + len(miss)}")
        for t in miss:
            if lvl == "P1":
                warn("G3", f"P1「{t}」未命中 —— 硬性要求缺失。改写解决不了："
                           f"要么回母版补真实经历，要么写进 gaps 让本人确认是否要投")
            elif lvl == "P2":
                warn("G3", f"P2「{t}」未命中 —— 若母版确有相关经历，"
                           f"检查是否写成了 JD 不认识的同义词")
            else:
                info("G3", f"P3「{t}」未命中（加分项，可忽略）")

    # ---- 匹配结论（硬）----
    # 覆盖率只报数字是不够的：22% 和 47% 在报告里长得差不多，但一个该投、
    # 一个不该投。闸门若只 warn，等于把「要不要投」这个最关键的决定留给
    # 被 30 条警告淹没的读者——这正是「闸门变橡皮图章」的路径。
    # 判据用 **P1（硬性要求）** 而不是总覆盖率：总覆盖率会被一堆 P2/P3 长尾
    # 稀释，而 P1 全灭意味着这个人压根不满足岗位准入门槛。
    p1_hit, p1_miss = report.get("P1", ([], []))
    n_p1 = len(p1_hit) + len(p1_miss)
    p1_rate = (len(p1_hit) / n_p1) if n_p1 else None
    desc = [t for t in p1 if _looks_like_clause(t)]
    desc_share = (len(desc) / n_p1) if n_p1 else 0.0
    if desc:
        warn("G3", f"词表质量：P1 有 {len(desc)}/{n_p1} 条疑似**描述性长句**"
                   f"（如「{desc[0]}」）—— 这类 JD 条款按字面永远匹配不上，"
                   f"覆盖率会被系统性低估。请把 P1 改成 ATS 关键词形式"
                   f"（「5 年以上权益投研经验」→「权益投研」），再重跑。")

    if n_p1 and not p1_hit:
        err("G3", f"匹配结论：**不建议投** —— P1 硬性要求 0/{n_p1} 命中"
                  f"（总覆盖率 {rate:.0f}%）。P1 是准入门槛，改写救不了："
                  f"回母版补真实经历，或换岗位。"
                  f"（若该 P1 词表尚未人工复核，请先复核词表再采信此结论）")
        print("G3 结论：不建议投")
    elif p1_rate is not None and p1_rate < 0.5:
        if desc_share >= 0.5:
            # 过半 P1 是长句 → 覆盖率不可信，此时下「不建议投」是冤枉人。
            # 宁可说「待定」，也不给一个基于坏词表的错误结论。
            warn("G3", f"匹配结论：**待定** —— P1 命中不足半数，但其中 "
                       f"{len(desc)}/{n_p1} 条是描述性长句，覆盖率不可信。"
                       f"先按关键词形式复核 P1 词表，再用本结论决定投不投。")
            print("G3 结论：待定（先复核 P1 词表）")
        else:
            warn("G3", f"匹配结论：**不建议直接投** —— P1 硬性要求只命中 "
                       f"{len(p1_hit)}/{n_p1}（不足半数）。先回母版补这些硬性经历，"
                       f"再考虑投递；投了也大概率卡在初筛。")
            print(f"G3 结论：不建议直接投（P1 仅 {len(p1_hit)}/{n_p1}）")
    elif rate < 30:
        # P1 过关但总量低 —— 这不是「不匹配」，是**措辞没对上 JD 的语言**：
        # 缺口集中在 P2/P3 长尾。修法是按 JD 用词重写，而不是换岗位。
        warn("G3", f"匹配结论：措辞与 JD 不通 —— P1 已命中 {len(p1_hit)}/{n_p1}，"
                   f"但总覆盖率仅 {rate:.0f}%，缺口集中在 P2/P3。"
                   f"按 JD 用词重写同义表述即可，不必换岗位。")
        print(f"G3 结论：可投（但需按 JD 语言重写：P1 过，总量 {rate:.0f}%）")
    elif rate < 50:
        info("G3", f"匹配结论：可投，但需先在 gaps 里逐条确认缺口"
                   f"（总覆盖率 {rate:.0f}%）")
        print("G3 结论：可投（需确认 gaps）")
    else:
        info("G3", f"匹配结论：匹配良好（总覆盖率 {rate:.0f}%）")
        print("G3 结论：匹配良好")


# ---------------------------------------------------------------------------
# G4 去 AI 味
# ---------------------------------------------------------------------------
def _load_graded_terms(path):
    """解析**分级**禁用词表 → (levels, patterns)。

    词表本身是有等级设计的（见 config/forbidden_terms.txt 头部）：
        A 级 = 无信息量，直接删      → 硬拦
        B 级 = 模糊含义，必须替换    → 硬拦
        C 级 = 强主张，**允许保留但必须挂证据**（母版 strength: strong）→ 不硬拦
    早期 G4 读的是 assets/forbidden_terms.txt —— 那是**剥掉分级的扁平镜像**，
    于是「主导 / 牵头 / 独立完成 / 唯一」这些 C 级词被当成 A 级硬 ERROR，
    把正常简历语言判成 AI 味（实测钱七「沉淀/对齐/打法/主导」四条里，
    只有三条该删）。分级必须回到 G4，否则闸门会逼作者删掉真实主张。
    """
    levels, patterns, section, lvl = {}, [], None, None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^\[([ABC])\]", s)
        if m:
            lvl, section = m.group(1), "word"
            continue
        m = re.match(r"^\[(句式|标点|数字)\]", s)
        if m:
            section, lvl = m.group(1), None
            continue
        if section == "word" and lvl:
            w = re.split(r"\s*->", s)[0].strip()
            if w:
                levels[w] = lvl
        elif section in ("句式", "标点"):
            name = re.split(r"\s+", s)[0].strip()
            if not name:
                continue
            note = s[len(name):].strip(" \t-—")
            rx = re.escape(name).replace(r"\.\.\.", r".{0,12}") if "..." in name \
                else re.escape(name)
            patterns.append((name, rx, note, section))
    return levels, patterns


def g4_ai_smell(scan_path, terms_path, eff=None):
    """扫**成稿正文**找 AI 味词（自动解析，无需手动传 --draft）。

    为什么扫成稿而不是草稿：草稿里混着【待补：…】批注和「○本人陈述」标记，
    它们是给本人看的校对信息、不进投递稿。实测张三草稿的 gaps 面板写着
    「这是唯一的 P0 阻塞项」——这种编辑说明不该算简历 AI 味。成稿才是投递稿，
    与 G3 的统计口径一致。（难点 / 范围 / ✔ 自 2026-09-21 起改为**仅校对稿可见**，
    成稿不再出现 —— 它们都是内部字段名，雇主看不懂；G4 扫成稿时也就不必再考虑它们。）
    """
    if not scan_path:
        print("G4 AI 味：未找到成稿/草稿 HTML，跳过")
        return
    dp = Path(scan_path)
    if not dp.exists():
        warn("G4", f"找不到待扫描文件: {dp}")
        return
    tp = Path(terms_path)
    if not tp.exists():
        warn("G4", f"找不到禁用词表: {tp}")
        return

    levels, patterns = _load_graded_terms(tp)
    if not levels:
        # 扁平表（无 [A]/[B]/[C] 头）→ 全部按 A 级处理，保持向后兼容
        levels = {l.strip(): "A" for l in
                  tp.read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")}

    raw = dp.read_text(encoding="utf-8")
    # 只扫**简历正文**：复用 G3 那套解析器提取（_html_text 按标签栈剔除
    # noprint / gaps / footer / pending 整棵子树），再 _norm 归一化两侧。
    #
    # 为什么不能只剥 <style>/<script>：那只挡住了 CSS 注释里的「对齐」，
    # 校对模式的**批注块**仍然留在文本里。实测张三草稿的 gaps 面板写着
    # 「这是唯一的 P0 阻塞项」「目前唯一可第三方查证的硬证据」——这是写给
    # 本人看的编辑说明，被当成简历 AI 味词误报成 ERROR。与 G3 是同一类坑：
    # 辅助区块污染正文统计。
    text = _norm(_html_text(raw))

    hitsA = sorted(w for w, l in levels.items() if l == "A" and _norm(w) in text)
    hitsB = sorted(w for w, l in levels.items() if l == "B" and _norm(w) in text)
    hitsC = sorted(w for w, l in levels.items() if l == "C" and _norm(w) in text)

    for w in hitsA:
        err("G4", f"命中 A 级 AI 味词：「{w}」—— 无信息量，直接删")
    for w in hitsB:
        err("G4", f"命中 B 级 AI 味词：「{w}」—— 必须替换为具体表述")

    # C 级：强主张不是错，缺证据才是。母版里已有 strength: strong 的条目，
    # 就只提示「确认这条主张对应其中一条」；一条都没有才升级为 WARN。
    has_strong = any(isinstance(a, dict) and a.get("strength") == "strong"
                     for a in ((eff or {}).get("achievements") or []))
    for w in hitsC:
        if has_strong:
            info("G4", f"「{w}」是 C 级强主张 —— 母版已有 strong 证据条目，"
                       f"确认该主张对应其中一条即可保留")
        else:
            warn("G4", f"「{w}」是 C 级强主张但母版无 strength: strong 条目 —— "
                       f"挂证据，或降级为具体动作描述")

    # 句式 / 标点（同表内定义）
    for name, rx, note, section in patterns:
        n = len(re.findall(rx, text))
        if not n:
            continue
        if name == "！":
            err("G4", f"简历出现感叹号（{n} 处）—— 简历中禁用")
        elif name in ("——", "；") and n > (1 if name == "——" else 2):
            warn("G4", f"「{name}」出现 {n} 处 —— {note or '建议精简'}")
        elif section == "句式":
            info("G4", f"命中句式「{name}」（{n} 处）—— {note or '可精简'}")

    # 量化率（同表 [数字] 段）：含精确数字的成就占比，反映「扛追问」的底子
    if eff:
        achs = [a for a in (eff.get("achievements") or []) if isinstance(a, dict)]
        if achs:
            q = sum(1 for a in achs
                    if _s((a.get("result") or {}).get("value")).strip()) / len(achs)
            if q < 0.30:
                info("G4", f"量化不足：含精确数字的成就仅 {q*100:.0f}%"
                           f"（建议 50%-70%）")

    total = len(hitsA) + len(hitsB)
    if total:
        print(f"G4 AI 味：硬拦 {total} 词"
              f"（A {len(hitsA)} / B {len(hitsB)}）"
              + (f"，C 级强主张 {len(hitsC)} 个另议" if hitsC else ""))
    else:
        print("G4 AI 味：未命中 A/B 级禁用词"
              + (f"（C 级强主张 {len(hitsC)} 个已提示）" if hitsC else ""))


# ---------------------------------------------------------------------------
# G5 反向面试（静态代理）
# ---------------------------------------------------------------------------
# 设计文档把 G5 定义为「假设面试官对每个 bullet 追问三层，扛得住吗」，
# 并称它「全场最有效」。真人追问无法脚本化，这里用**结构化数据做静态代理**：
# 凡是会在追问下崩的 bullet，其母版字段必然缺了某块「答辩材料」。
#   · 证据 pending / inferred —— 被问「怎么证明」只能说「我记得」
#   · 无量化结果且主张弱 —— 被问「提升了多少」答不上
# 这两类即「扛不住追问」，应降级或删除（与 G5 哲学一致）。
# 另有「软项」：有结果但无基线/无范围、或纯定性描述 —— 能扛但不够稳，给加固建议。
# 注意：这是**代理**不是真面试；结果作为 WARN，--strict 时升级为 ERROR。
def g5_interview(master, eff):
    """反向面试：只看**真正出片的条目**。

    为什么必须排除 pending / inferred：render_resume 在 final 模式会把它们
    整条隐藏（宁缺毋滥）。对一条根本不进成稿的经历问「面试官追问扛不扛得住」
    是无效的 —— 旧实现把它算成「扛不住」，于是给了一份干净成稿一堆假警报。
    与 G3「只测成稿文本」保持同一口径：**统计只统计会交付的东西**。
    """
    collapse, soft, hidden = [], [], []
    n_diff, n_ship, n_val = 0, 0, 0
    for a in eff.get("achievements") or []:
        if not isinstance(a, dict) or not a.get("id"):
            continue
        aid = str(a["id"])
        ev = a.get("evidence")
        strength = a.get("strength")
        r = a.get("result")
        r = r if isinstance(r, dict) else {}      # result 也可能被写成纯字符串
        val = _s(r.get("value")).strip()
        base = _s(r.get("baseline")).strip()
        scope = _s(r.get("scope")).strip()

        if ev in ("pending", "inferred"):
            hidden.append((aid, "待确认" if ev == "pending" else "推断"))
            continue

        n_ship += 1
        if val:
            n_val += 1
        # difficulty（难点）是设计文档点名的「抗追问能力主要来源」——
        # 填了就说明这条有别人复制不了的门槛，计入正面指标。
        if _s(a.get("difficulty")).strip():
            n_diff += 1

        reasons = []
        if not val and strength == "weak":
            reasons.append("无量化结果且主张弱，被问『提升多少』答不上")
        if reasons:
            collapse.append((aid, reasons))

        # 软项：能扛但不够稳
        if val and not base:
            soft.append((aid, "有结果无基线（『从什么水平到什么水平』答不上）"))
        elif val and not scope:
            soft.append((aid, "有结果无范围（『在什么规模上』答不上）"))
        elif not val:
            soft.append((aid, "纯定性描述无数字，追问量化时会吃力"))

    # 扛不住追问 = 硬拦。设计文档原话「扛不住的降级或删除」——留一条自己都
    # 讲不清的 bullet，就是在给面试官递刀。判据很窄（无量化 + 弱主张），
    # 不量化但证据扎实的条目不会误伤。
    for aid, rs in collapse:
        err("G5", f"{aid} 扛不住反向面试：{'；'.join(rs)} —— 降级或删除后再出片")
    for aid, msg in soft:
        info("G5", f"{aid} 可加固：{msg}")
    for aid, why in hidden:
        info("G5", f"{aid} 证据{why}，出片已隐藏 —— 补证据可复活，"
                   f"或从 selection 里移除")

    q = (n_val / n_ship) if n_ship else 0.0
    print(f"G5 反向面试（静态代理）：出片 {n_ship} 条 —— "
          f"{len(collapse)} 条扛不住追问 / {len(soft)} 条可加固"
          + (f"；{n_diff}/{n_ship} 条填了「难点」" if n_diff else "")
          + f"；量化率 {q*100:.0f}%"
          + (f"（另有 {len(hidden)} 条已隐藏）" if hidden else ""))
    if n_ship and q < 0.30:
        warn("G5", f"量化不足：出片条目里含精确数字的仅 {q*100:.0f}%"
                   f"（对照表建议 50%-70%）—— 追问「提升了多少」时容易答不上，"
                   f"建议按 R3 做深度补强")


# ---------------------------------------------------------------------------
# G6 版式
# ---------------------------------------------------------------------------
# 两类问题，两类证据：
#   ① 内部标记泄漏 —— 纯静态可判。校对批注（【待补】/○本人陈述/⚠）是写给
#      本人看的，印进投递稿等于把草稿交出去。判据用 _html_text（只取可见正文），
#      noprint 的页脚/批注块天然被剔除，不会误伤。
#   ② 分页是否真的没崩 —— 必须**实测**。静态 HTML 里只有一个 #page0，
#      页数是浏览器端分页 JS 算出来的；靠读文件永远看不到"第 3 页只剩两行"。
#      所以这里调用 measure_pages.js（有 node + playwright 才跑，否则降级为提示）。
def g6_layout(tailored, target_path, rendered_path):
    resolved = _resolve_rendered(tailored, target_path, rendered_path)
    if not resolved or not Path(resolved).exists():
        warn("G6", "拿不到成稿 HTML，版式未检查")
        return
    raw = Path(resolved).read_text(encoding="utf-8")

    # ⚠ 后三个是新补的：✔（证据档位=verified）/（难点：/（范围： 都是**内部字段名**，
    #   原先没有任何 mode 守卫，12/12 份 final 稿全被印了出来 —— 雇主会看到一颗没有图例
    #   的绿勾，以及一堆字段标签。G6 的泄漏清单里原本没有它们，所以闸门全绿、53 项回归
    #   也全绿，却没人发现。补进来，让这类问题以后必被拦。
    leaks = [m for m in ("【待补", "○本人陈述", "校对模式", "出片模式",
                         "母版 v", "待确认", "需补充证据",
                         "✔", "（难点：", "（范围：")
             if m in _html_text(raw)]
    for m in leaks:
        err("G6", f"成稿正文泄漏内部标记「{m}」—— 这是校对信息，不该印进投递稿")

    low = raw.lower()
    if "<h1" not in low:
        err("G6", "成稿缺姓名标题（h1），版式不完整")
    if 'class="item"' not in raw and "class='item'" not in raw:
        err("G6", "成稿没有任何经历块（.item）—— 版式不完整")

    measure = Path(__file__).resolve().parent / "measure_pages.js"
    node = (os.environ.get("NODE_BIN") or shutil.which("node")
            or r"本机node路径")
    if not measure.exists() or not (shutil.which(node) or Path(node).exists()):
        info("G6", "本机无 node/playwright，实测分页跳过（版式仅做了静态检查）")
        print("G6 版式：静态检查通过（分页未实测）")
        return
    env = dict(os.environ)
    env.setdefault("NODE_PATH", os.environ.get("NODE_MODULES")
                   or r"本机node_modules")
    try:
        r = subprocess.run([node, str(measure), str(resolved)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env, timeout=240)
        out = r.stdout or ""
    except Exception as e:                      # 超时/找不到浏览器都不该让闸门崩
        info("G6", f"实测分页未跑成（{e}）—— 版式仅做了静态检查")
        print("G6 版式：静态检查通过（分页未实测）")
        return

    m = re.search(r"页数 (\d+)", out)
    pages = int(m.group(1)) if m else 0
    fills = [int(x) for x in re.findall(r"(\d+)%  \d+mm", out)]
    last = fills[-1] if fills else 0
    if "⚠ 有页内容超出" in out:
        err("G6", "分页未兜住：有页内容超出 A4 内容区")
    elif "残页（内容量够" in out:
        err("G6", "末页残页且内容量充足 —— 均衡逻辑失效")
    elif "内容不足" in out:
        info("G6", f"内容总量撑不满 {pages} 页，已尽量均分（非版式缺陷）")
    elif last and last < 55:
        warn("G6", f"末页填充仅 {last}%")
    print(f"G6 版式：实测 {pages} 页，末页填充 {last}%，"
          f"{'无溢出/残页' if not (last and last < 55) else '末页偏空'}")


def g_version_drift(master, tailored):
    mv = (master.get("master") or {}).get("version", 1)
    tv = tailored.get("master_version")
    if tv is None:
        warn("版本", "定制版未记录 master_version，无法检测漂移")
    elif tv < mv:
        warn("版本", f"母版已升到 v{mv}，本定制版基于 v{tv} —— 建议重新生成")
    else:
        print(f"版本漂移：母版 v{mv}，定制版基于 v{tv}，一致")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--draft", default=None,
                    help="待检查文件（默认自动解析成稿 HTML；传此参数可覆盖）")
    ap.add_argument("--rendered", default=None,
                    help="已渲染的成稿 HTML —— G3 用它测真实命中率（推荐）")
    ap.add_argument("--jd", default=None, help="JD 原文文件（G3 用）")
    ap.add_argument("--terms", default=None, help="禁用词表路径")
    ap.add_argument("--strict", action="store_true", help="警告也视为不通过")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    # 默认用**分级**词表（config/），不是 assets/ 的扁平镜像 ——
    # 镜像丢了 A/B/C 分级，会把 C 级「强主张」当 A 级「必删」硬拦。
    # config/ 缺失时才回落到镜像（此时全部按 A 级处理）。
    graded = here.parent / "config" / "forbidden_terms.txt"
    terms = args.terms or str(graded if graded.exists()
                              else here.parent / "assets" / "forbidden_terms.txt")

    master = load(args.master)
    # 定制版有两种 schema：现行写法把字段全嵌在 `tailored:` 下，早期写法把
    # selection / target 写在顶层与 `tailored:` 平级。若一律只 `.get("tailored")`，
    # 早期文件的筛选与 JD 依据会**静默失效**（实测 4 个定制版里 3 个中招）。
    # load_tailored 统一归一化，两种写法都能读到。
    tailored = load_tailored(args.target)

    print("=" * 58)
    eff, bad_refs = resolve_selection(master, tailored)
    g1_trace(master, tailored, eff, bad_refs)
    g2_evidence(master, eff)
    g3_coverage(master, tailored, eff, args.rendered, args.jd, args.target)
    # G4 默认开启：没显式传 --draft 时，自动解析成稿 HTML 来扫 AI 味。
    # 旧实现要手动传 --draft 才跑，等于「默认出片路径不查 AI 味」——与 README
    # 声称的「G4 硬校验」自相矛盾。扫成稿而非草稿：草稿含【待补】等校对批注。
    scan_path = args.draft or _resolve_rendered(tailored, args.target, None)
    g4_ai_smell(scan_path, terms, eff)
    g5_interview(master, eff)
    g6_layout(tailored, args.target, args.rendered)
    g_version_drift(master, tailored)
    print("=" * 58)

    for gate, msg in infos:
        print(f"[INFO] {gate}: {msg}")
    for gate, msg in warns:
        print(f"[WARN] {gate}: {msg}")
    for gate, msg in errors:
        print(f"[ERROR] {gate}: {msg}")

    if errors:
        print(f"\n不通过：{len(errors)} 个 ERROR 必须修复后才能出片。")
        sys.exit(1)
    if args.strict and warns:
        print(f"\n严格模式不通过：{len(warns)} 个警告。")
        sys.exit(1)
    print(f"\n通过。（{len(warns)} 个警告 / {len(infos)} 条提示，请人工确认）")


if __name__ == "__main__":
    main()

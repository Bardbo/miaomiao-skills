#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历母版 / 定制版 校验器 —— Gate G1(溯源) G2(证据) G4(去 AI 味) 的自动化部分

用法:
  python scripts/validate_master.py check   master/master.yaml
  python scripts/validate_master.py check   targets/xxx/tailored.yaml --master master/master.yaml
  python scripts/validate_master.py lint    master/master.yaml
  python scripts/validate_master.py preview master/master.yaml [-o master/master.preview.md]

退出码: 0 通过 / 1 有 error / 2 只有 warning
"""
import sys
import re
import argparse
from pathlib import Path
from datetime import date

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
ROOT = Path(__file__).resolve().parent.parent   # 包根：config/
WORKSPACE = Path(os.environ.get("RESUME_WORKSPACE") or Path.cwd())  # 工作区：people/
# verified      有第三方可查证证据（专利号 / 论文 / 可核实的公开记录）
# self_reported 本人明确陈述（来自用户提供的材料或回答），可写但面试会被追问
# pending       信息不全，等待补充
# inferred      AI 推断 —— 禁止进入母版
# unusable      证据存在但不可对外使用（权属归他方 / 涉密）—— 禁止进入任何定制版
VALID_EVIDENCE = {"verified", "self_reported", "pending", "inferred", "unusable"}
VALID_STRENGTH = {"normal", "strong"}
VALID_TYPES = {"work", "project", "internship", "opensource", "award"}
# 待确认：候选技能尚未经本人确认等级（needs_confirm: true），此时不得凭空给级别
VALID_LEVELS = {"了解", "熟悉", "熟练", "精通", "待确认"}
# v9 技能表达范式 —— 详见 references/rewrite-rules.md
#   commodity  装个工具 / 问一句 AI 就能获得 → 真实但无区分度，不单列，藏进交付物
#   capability 能独立从 0 做到 1 并交付给人用 → 主战场
#   leverage   放大产出效率（AI 原生、受限环境交付）→ 单列
VALID_KINDS = {"commodity", "capability", "leverage"}
POLISH_LABEL = {"sincere": "真诚", "balanced": "适度包装", "bold": "酥化"}

# 人群画像（写什么）—— 与 render_resume.PROFILES 保持一致，改一处必须改另一处
VALID_PROFILES = {
    "campus": {"label": "校招", "skill_cap": 0, "require_evidence": False, "drop_student": False},
    "junior": {"label": "初级", "skill_cap": 14, "require_evidence": False, "drop_student": False},
    "experienced": {"label": "社招", "skill_cap": 10, "require_evidence": True, "drop_student": True},
    "expert": {"label": "资深", "skill_cap": 0, "require_evidence": True, "drop_student": True},
}
# 包装级别（怎么写）—— 只调表达方式，不产生事实，也不能解锁 evidence 限制
VALID_POLISH = {"sincere", "balanced", "bold"}

errors, warnings, infos = [], [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def info(msg):
    infos.append(msg)


# ---------------- 禁用词表 ----------------
def load_terms(path):
    """解析 forbidden_terms.txt，返回 {级别: [词]}, {词: 替换建议}"""
    grouped, replace = {}, {}
    section = None
    if not path.exists():
        warn(f"未找到禁用词表 {path}，跳过 G4 检查")
        return grouped, replace
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[(.+?)\](.*)$", line)
        if m:
            section = m.group(1).strip()
            grouped.setdefault(section, [])
            continue
        if "->" in line:
            word, sug = [x.strip() for x in line.split("->", 1)]
            replace[word] = sug
            grouped.setdefault(section, []).append(word)
        else:
            grouped.setdefault(section, []).append(line)
    return grouped, replace


def _is_compound(text, w):
    """A 类「无信息量词」的复合词豁免。

    「推进落地」「实现落地」是空话，但「算法落地」「落地项目运行数据」有实义 ——
    一刀切会逼着把真实内容改成病句。判定：任一次出现落在复合词里就整体跳过
    （保守取向 —— 宁可漏报，不可误报。误报的代价是用户开始不信校验器）。
    """
    for m in re.finditer(re.escape(w), text):
        i = m.start()
        if i > 0 and text[i - 1] in A_COMPOUND_PREFIX:
            return True
        if i + len(w) < len(text) and text[i + len(w)] in A_COMPOUND_SUFFIX:
            return True
    return False


# 前接这些字说明「落地」等词已被限定为某个具体事物的一部分
A_COMPOUND_PREFIX = "算法技术项目业务成果方案模型产品系统流程"
# 后接这些字说明该词是定语而非空泛动词
A_COMPOUND_SUFFIX = "项目运行数据场景后率方案效果"


def lint_text(text, label, grouped, replace):
    if not text:
        return
    for w in grouped.get("A", []):
        if w in text and not _is_compound(text, w):
            warn(f"[G4-A] {label} 含无信息量词「{w}」，建议直接删除")
    for w in grouped.get("B", []):
        if w in text:
            sug = replace.get(w, "")
            warn(f"[G4-B] {label} 含模糊词「{w}」" + (f"，建议替换为「{sug}」" if sug else ""))
    for w in grouped.get("C", []):
        if w in text:
            info(f"[G4-C] {label} 含强主张「{w}」，需确认已挂 evidence_note")
    for pat in grouped.get("句式", []):
        if "..." in pat or "…" in pat:
            segs = [s for s in re.split(r"\.\.\.|…", pat) if s]
            if not segs:
                continue
            rx = ".*?".join(re.escape(s) for s in segs)
            if re.search(rx, text):
                warn(f"[G4-句式] {label} 疑似「{pat}」句式，建议改写为直述")
        elif pat in text:
            warn(f"[G4-句式] {label} 含套话「{pat}」，建议删除")
    for p in grouped.get("标点", []):
        if p in text:
            cnt = text.count(p)
            limit = 1 if p == "——" else 2
            if cnt > limit:
                warn(f"[G4-标点] {label} 含 {cnt} 处「{p}」，建议不超过 {limit} 处")


# ---------------- 母版校验 ----------------
def _count_pending(data):
    """跨所有段落统计 pending 条目数 —— 用于判断 bold 包装的风险敞口"""
    n = 0
    for e in data.get("experiences") or []:
        for a in e.get("achievements") or []:
            if a.get("evidence") == "pending":
                n += 1
    for sec in ("publications", "patents", "honors", "certifications"):
        for p in data.get(sec) or []:
            if p.get("evidence") == "pending":
                n += 1
    return n


def check_profile_and_polish(data):
    """画像（写什么）与包装级别（怎么写）—— 两者正交，都不能解锁 evidence 限制"""
    pref = data.get("preferences") or {}
    profile = pref.get("profile")
    if profile is None:
        info("preferences.profile 未设置 —— 默认按社招（experienced）处理，建议显式声明")
        profile = "experienced"
    elif profile not in VALID_PROFILES:
        err(f"preferences.profile 非法: {profile!r}（应为 {sorted(VALID_PROFILES)}）")
        profile = "experienced"
    pr = VALID_PROFILES[profile]

    polish = pref.get("polish") or "balanced"
    if polish not in VALID_POLISH:
        err(f"preferences.polish 非法: {polish!r}（应为 {sorted(VALID_POLISH)}）")
        polish = "balanced"

    # ---- 技能堆叠：社招画像下是负分项，不是加分项 ----
    active = [s for s in (data.get("skills") or [])
              if (s.get("status") or "active") != "archived"]
    # v9 范式：commodity（装个工具就能获得）不单列，故不计入技能上限
    commodity = [s.get("name", "?") for s in active
                 if (s.get("kind") or "capability") == "commodity" and not s.get("keep")]
    active = [s for s in active
              if (s.get("kind") or "capability") != "commodity" or s.get("keep")]
    if commodity:
        info(f"[范式] {len(commodity)} 项商品化能力不单列（真实但无区分度）：{'、'.join(commodity)}"
             f" —— 它们应已挂在交付物 bullet 的 tech_tags 里")
    if pr["skill_cap"] and len(active) > pr["skill_cap"]:
        warn(f"[画像 {pr['label']}] 生效技能 {len(active)} 项，超过建议上限 {pr['skill_cap']} 项 —— "
             f"技能堆叠会被 HR 读成「泛而不精」，建议把无佐证的标 status: archived")
    if pr["require_evidence"]:
        unbacked = [s.get("name", "?") for s in active
                    if not (s.get("evidence_refs") or []) and not s.get("keep")]
        if unbacked:
            info(f"[画像 {pr['label']}] {len(unbacked)} 项技能无项目佐证，出片时自动隐藏："
                 f"{'、'.join(unbacked)}")

    # ---- 校园内容：社招下不是假，是稀释信号 ----
    hons = data.get("honors") or []
    if pr["drop_student"]:
        stud = [h.get("name", "?") for h in hons if h.get("student_era")]
        if stud:
            info(f"[画像 {pr['label']}] 校园内容已自动过滤：{'、'.join(stud)}"
                 f"（不是判定它假，是它会稀释「能立刻干活」的信号）")

    # ---- 荣誉段门控（v10「low 感」）----
    # 剩下的全是低价值条目就整段隐藏 —— 一条「优秀团员」挂在简历上是负分
    rest = [h for h in hons
            if not (pr["drop_student"] and h.get("student_era"))]
    if rest:
        solid = [h for h in rest
                 if (h.get("relevance") or "normal") != "low" or h.get("force")]
        if not solid:
            info(f"[low感] 荣誉段将被整段隐藏：剩下的全是低价值条目"
                 f"（{'、'.join(h.get('name','?') for h in rest)}）—— "
                 f"无竞争性荣誉上简历不是加分，是告诉对方「我把能找到的都写上了」。"
                 f"确有需要时用 force: true 显式开启")

    # ---- pending 二分：别把「未采集」当「存疑」误杀了 ----
    # 典型事故：已授权发明专利因为缺专利号被判 pending，成稿里连成果段都没有。
    # 判据：删掉缺失字段后句子是否还成立 —— status 已授权/已录用 且 title 完整的，
    # 事实本身是确定的，缺的只是可查证编号，属「未采集」而非「存疑」。
    def _title_ok(t):
        t = str(t or "")
        return t and not t.startswith("（题目待补")
    soft = []
    for blk, ok_status in (("patents", ("已授权", "已公开", "已受理")),
                           ("publications", ("已录用", "已发表", "见刊"))):
        for it in data.get(blk) or []:
            if (it.get("evidence") or "pending") != "pending":
                continue
            if _title_ok(it.get("title")) and it.get("status") in ok_status:
                soft.append(f"{it.get('id', '?')}（{blk}）")
    if soft:
        warn(f"[pending 二分] {'、'.join(soft)} 看起来是「未采集」型而非「存疑」型："
             f"事实已确定（status 已授权/已录用），缺的只是编号与位次。"
             f"按规则应转 evidence: self_reported + needs_confirm: true 放行入稿，"
             f"而不是等补齐 —— 藏掉硬通货的代价大于位次答不上来的代价。"
             f"详见 rewrite-rules.md →「pending 有两种」")

    # ---- 包装级别与证据的交叉风险 ----
    if polish == "bold":
        n = _count_pending(data)
        if n:
            warn(f"polish=bold（酥化）但母版里有 {n} 条 pending —— 强化包装无证据内容等于编造。"
                 f"pending 在 bold 下同样隐藏；且 bold 的 G5 需追问 5 层而非 3 层")
    return profile, polish


def check_master(data):
    m = data.get("master") or {}
    if not m:
        err("缺少 master 节点")
        return
    for k in ("version", "updated_at", "locale"):
        if k not in m:
            err(f"master.{k} 缺失")

    check_profile_and_polish(data)

    exps = data.get("experiences") or []
    ach_ids, exp_ids = set(), set()

    for e in exps:
        eid = e.get("id", "<无 id>")
        if not e.get("id"):
            err("存在无 id 的经历条目")
            continue
        if eid in exp_ids:
            err(f"经历 ID 重复: {eid}")
        exp_ids.add(eid)

        if e.get("type") and e["type"] not in VALID_TYPES:
            err(f"{eid} type 非法: {e['type']}")
        if not e.get("org") or not e.get("title"):
            warn(f"{eid} 缺少 org 或 title")
        if not e.get("raw_input"):
            warn(f"{eid} 缺少 raw_input（原始描述，防漂移锚点）")

        achs = e.get("achievements") or []
        if not achs and e.get("type") in ("work", "project"):
            warn(f"{eid} 还没有任何成就条目")

        for a in achs:
            aid = a.get("id", f"{eid}-<?>")
            if not a.get("id"):
                err(f"{eid} 下存在无 id 的成就")
                continue
            if aid in ach_ids:
                err(f"成就 ID 重复: {aid}")
            ach_ids.add(aid)

            ev = a.get("evidence")
            if ev not in VALID_EVIDENCE:
                err(f"{aid} evidence 非法: {ev!r}（应为 {sorted(VALID_EVIDENCE)}）")
            st = a.get("strength", "normal")
            if st not in VALID_STRENGTH:
                err(f"{aid} strength 非法: {st!r}")

            # G2 核心规则：强主张必须挂证据
            if ev == "inferred":
                err(f"[G2] {aid} evidence=inferred —— 推断内容禁止进入母版")
            elif ev == "unusable":
                if a.get("acknowledged"):
                    info(f"[G2] {aid} evidence=unusable（已确认）—— 仅存档，不进入任何定制版")
                else:
                    err(f"[G2] {aid} evidence=unusable —— 证据存在但不可对外使用（权属/涉密），禁止进入任何定制版。确认后加 acknowledged: true 可降为提示")
            elif st == "strong":
                if not a.get("evidence_note"):
                    err(f"[G2] {aid} 标记为 strong 但无 evidence_note，强主张必须有依据")
                elif ev == "verified":
                    pass  # 有第三方证据，强主张可保留
                elif ev == "self_reported":
                    info(f"[G2] {aid} 强主张来自本人陈述（无第三方验证）—— 面试必追问细节，确认讲得清")
                else:
                    warn(f"[G2] {aid} 是强主张但 evidence={ev}，渲染时须降级为「参与」")
            if ev == "pending" and not a.get("evidence_note"):
                warn(f"[G2] {aid} 是 pending 但未说明缺什么（evidence_note）")
            if ev == "self_reported" and a.get("source_docs") is None and not a.get("from_doc"):
                info(f"{aid} 建议标注 source_docs，便于回溯到原始材料")

            # result 是 dict（metric/value/baseline/scope）。填成字符串时不能抛裸
            # traceback —— 换个人填母版就会看到满屏 Python 堆栈，那是劝退不是报错。
            r = a.get("result")
            if r is None:
                info(f"{aid} 暂无量化结果，可触发 R3 深度补强")
            elif not isinstance(r, dict):
                err(f"{aid} 的 result 应为字典（metric / value / baseline / scope），"
                    f"当前填成了 {type(r).__name__}：{str(r)[:40]!r}")
            elif not r.get("value"):
                info(f"{aid} 暂无量化结果，可触发 R3 深度补强")
            if not a.get("difficulty"):
                info(f"{aid} 未填 difficulty（抗追问能力的主要来源）")

    # G1 技能必须能挂到经历
    for s in data.get("skills") or []:
        name = s.get("name", "<?>")
        if s.get("level") and s["level"] not in VALID_LEVELS:
            err(f"技能 {name} level 非法: {s['level']}")
        kind = s.get("kind") or "capability"
        if kind not in VALID_KINDS:
            err(f"技能 {name} kind 非法: {kind!r}（应为 {sorted(VALID_KINDS)}）")
        # 归档技能根本不渲染，拿它刷告警纯属噪音
        if (s.get("status") or "active") == "archived":
            continue
        refs = s.get("evidence_refs") or []
        if not refs and not s.get("keep"):
            warn(f"[G1] 技能「{name}」无 evidence_refs，出片时自动降权")
        # 范式校验：commodity 若不挂任何成就，就彻底失去了存在理由 ——
        # 它既不单列，又没藏进任何交付物，等于只在母版里占位
        if kind == "commodity" and not refs and not s.get("keep"):
            warn(f"[范式] 技能「{name}」标为 commodity 却无 evidence_refs —— "
                 f"它既不单列、又没藏进任何交付物 bullet，等于只在母版里占位。"
                 f"要么挂到交付物，要么归档")
        for r in refs:
            if r not in ach_ids:
                err(f"[G1] 技能「{name}」引用了不存在的成就 ID: {r}")

    # ---- AI 原生能力（leverage 层）----
    for a in data.get("ai_native") or []:
        aid = a.get("id", "<?>")
        if not a.get("capability"):
            err(f"[G1] ai_native {aid} 缺少 capability —— 主句必须是能力，工具名只能作附注")
        ev = a.get("evidence")
        if ev and ev not in VALID_EVIDENCE:
            err(f"[G2] ai_native {aid} evidence 非法: {ev!r}")
        for r in (a.get("evidence_refs") or []):
            if r not in ach_ids:
                err(f"[G1] ai_native {aid} 引用了不存在的成就 ID: {r}")
        # 只有工具名、没有能力描述 = 又变成工具清单，违背 leverage 层的写法铁律
        if a.get("capability") and not a.get("detail") and not a.get("evidence_refs"):
            warn(f"[范式] ai_native {aid} 只有 capability —— 建议补 detail（工具/场景）"
                 f"或挂 evidence_refs，否则读起来像口号")
        # v10：ai_native 渲染为「专业技能」的一个分组，group 缺失时落进默认组
        if not a.get("group"):
            info(f"[v10] ai_native {aid} 未指定 group —— 会落进默认分组「AI 原生能力」，"
                 f"建议显式指定（AI 原生工作流 / 本地模型与生成）")

    # ---- 摘要（v10）----
    sm = data.get("summary") or {}
    if sm.get("text"):
        if not sm.get("enabled"):
            info("[v10] 母版里有摘要候选但 summary.enabled=false —— 成稿不会出现。"
                 "确认无误后改为 true 即启用（它是全篇唯一新增概括性表述的段落，须本人确认）")
        for kw in ("待确认", "待补", "TODO"):
            if kw in sm["text"]:
                err(f"[G5] summary 文本里含占位符「{kw}」—— 摘要是首屏，占位符会直接毁掉观感")
        # 摘要是概括性表述，最容易偷偷引入 pending 事实
        pend_names = [p.get("name", "") for p in (data.get("certifications") or [])
                      if p.get("evidence") == "pending"]
        for n in pend_names:
            core = n.split("·")[-1].split("（")[0].strip()
            if core and core in sm["text"]:
                err(f"[G2] summary 提到了 pending 内容「{core}」—— "
                    f"摘要只能由已确认事实组成，pending 内容在出片时会被隐藏")

    # 账本引用校验
    for c in data.get("claim_ledger") or []:
        b = c.get("basis")
        if b and b not in ach_ids:
            err(f"[账本] basis 引用不存在的成就 ID: {b}")

    return exp_ids, ach_ids


def check_tailored(data, master_data):
    t = data.get("tailored") or {}
    if not t:
        err("缺少 tailored 节点")
        return
    if t.get("master_version") != (master_data.get("master") or {}).get("version"):
        warn(
            f"[版本] 定制版引用 master_version={t.get('master_version')}，"
            f"当前母版为 {(master_data.get('master') or {}).get('version')}，建议重新生成"
        )
    tg = t.get("target") or {}
    if not tg.get("company") or not tg.get("role"):
        err("target 缺少 company 或 role")
    js = tg.get("jd_snapshot") or {}
    if not js.get("text"):
        err("缺少 jd_snapshot.text —— JD 会下线，必须存原文快照")
    elif not js.get("fetched_at"):
        warn("jd_snapshot 未记录 fetched_at")

    # 置信度红线
    for f in (t.get("company_brief") or {}).get("facts", []):
        if not f.get("source_url"):
            err(f"[红线] company_brief 事实「{f.get('claim')}」无 source_url，不得进正文")
        if f.get("confidence") != "high":
            warn(f"[红线] 置信度 {f.get('confidence')} 的条目不应出现在 facts（只允许 high）")
    for i in (t.get("company_brief") or {}).get("inferences", []):
        if i.get("used_for") not in ("ordering", "tone", "weight"):
            warn(f"[红线] inference「{i.get('claim')}」未声明 used_for（ordering|tone|weight）")

    m_exps, m_achs = set(), set()
    for e in master_data.get("experiences") or []:
        m_exps.add(e.get("id"))
        for a in e.get("achievements") or []:
            m_achs.add(a.get("id"))

    sel = t.get("selection") or {}
    for i in sel.get("experiences", []):
        if i not in m_exps:
            err(f"[G1] 定制版引用了母版不存在的经历 ID: {i}")
    for i in sel.get("achievements", []):
        if i not in m_achs:
            err(f"[G1] 定制版引用了母版不存在的成就 ID: {i}")

    lvl = (t.get("rewrite_policy") or {}).get("level")
    if lvl == "L4":
        err("[G4层] rewrite_policy.level=L4（新增母版外内容）默认禁用，需显式转回母版")
    if not sel.get("achievements"):
        warn("selection.achievements 为空")

    gaps = t.get("gaps") or []
    if gaps:
        info(f"待补清单 {len(gaps)} 条，出片时应渲染给用户")


# ---------------- 预览 ----------------
def render_preview(data, out):
    m = data.get("master") or {}
    o = data.get("owner") or {}
    L = []
    L.append(f"# {o.get('name','')} — 简历母版 v{m.get('version','')}")
    L.append("")
    L.append("> 本文件由 master.yaml 自动生成，**请勿直接编辑**。")
    L.append("> 需要修改请用自然语言告知，修改后本文件会重新生成。")
    L.append("")
    c = o.get("contact") or {}
    L.append(" | ".join(x for x in [c.get("phone"), c.get("email"), c.get("city")] if x))
    L.append("")
    pref = data.get("preferences") or {}
    profile = pref.get("profile") or "experienced"
    polish = pref.get("polish") or "balanced"
    plabel = VALID_PROFILES.get(profile, {}).get("label", profile)
    L.append(f"*更新于 {m.get('updated_at','')} · 共 {len(data.get('experiences') or [])} 段经历*")
    L.append("")
    L.append(f"> **画像 {plabel}**（`{profile}`，管写什么） · "
             f"**包装 {POLISH_LABEL.get(polish, polish)}**（`{polish}`，管怎么写）")
    L.append(">")
    L.append("> 两者正交，都不能解锁 evidence 限制 —— `pending` 在任何包装级别下都会被隐藏。")
    L.append("")

    sm = data.get("summary") or {}
    if sm.get("text"):
        state = "**已启用**，会出现在成稿首屏" if sm.get("enabled") else \
                "未启用（成稿不出现，需本人确认后把 enabled 改为 true）"
        L.append(f"## 摘要（个人简述）— {state}")
        L.append("")
        L.append("> " + sm["text"].strip().replace("\n", " "))
        L.append("")

    for e in data.get("experiences") or []:
        p = e.get("period") or {}
        span = f"{p.get('start','')} – {'至今' if p.get('current') else (p.get('end') or '')}"
        L.append(f"<!-- id: {e.get('id')} -->")
        L.append("")
        head = f"## {e.get('org','')} · {e.get('title','')}"
        if not e.get("period_confirmed", True):
            head += "　**【时间待确认】**"
        L.append(head)
        L.append(f"*{span}*")
        L.append("")
        if e.get("note"):
            L.append(f"> {e['note']}")
            L.append("")
        achs = e.get("achievements") or []
        if not achs:
            L.append("*（成就待采集）*")
            L.append("")
        for a in achs:
            mark = {
                "verified": "✔",
                "self_reported": "○",
                "pending": "**【待补】**",
                "inferred": "⚠",
                "unusable": "🚫**【禁用】**",
            }.get(a.get("evidence"), "")
            r = a.get("result") or {}
            bullet = " · ".join(
                x for x in [a.get("action"), a.get("object"), a.get("method"), r.get("value")] if x
            )
            L.append(f"- {mark} {bullet}")
            if a.get("evidence_note"):
                L.append(f"  - 证据备注：{a['evidence_note']}")
            if a.get("difficulty"):
                L.append(f"  - 难点：{a['difficulty']}")
        L.append("")

    notes = data.get("career_notes") or []
    if notes:
        L.append("## 时间线备注")
        L.append("")
        for n in notes:
            tag = {
                "gap": "空窗", "risk": "风险点", "transition": "转折",
                "context": "背景", "goal": "目标", "asset": "优势",
            }.get(n.get("kind"), n.get("kind"))
            L.append(f"- **[{tag}]** {n.get('fact','')}")
            if n.get("motive"):
                L.append(f"  - 真实动机（简历不写，仅用于设计面试口径）：{n['motive']}")
            if n.get("note"):
                L.append(f"  - {n['note']}")
        L.append("")

    edu = data.get("education") or []
    if edu:
        L.append("## 教育经历")
        L.append("")
        for e in edu:
            p = e.get("period") or {}
            span = f"{p.get('start','')} – {p.get('end','')}"
            mark = "" if e.get("confirmed", True) else "**【待确认】**"
            line = f"- {mark} {e.get('school','')} · {e.get('major','')} · {e.get('degree','')}"
            if span.strip(" –"):
                line += f"　*{span}*"
            L.append(line)
            if e.get("note"):
                L.append(f"  - {e['note']}")
            for h in e.get("highlights") or []:
                L.append(f"  - {h}")
        L.append("")

    sk = data.get("skills") or []
    if sk:
        L.append("## 技能")
        L.append("")
        for s in sk:
            refs = s.get("evidence_refs") or []
            archived = (s.get("status") or "active") == "archived"
            tags = []
            if not refs and not archived:   # 归档的根本不渲染，再提示降权是噪音
                tags.append("无证据，出片降权")
            if archived:
                tags.append("**已归档**（默认不显示，换方向可复活）")
            if s.get("needs_confirm"):
                tags.append("**待本人确认**")
            if s.get("keep"):
                tags.append("keep：无佐证也强制显示")
            kind = s.get("kind") or "capability"
            if kind == "commodity" and not archived:
                tags.append("**商品化能力**（真实但无区分度，不单列 —— 藏在交付物里）")
            if s.get("stack") and not archived:
                tags.append(f"注脚`{s['stack']}`")
            # v10：level 仅供内部收敛决策，成稿不显示 —— 预览里标出来免得以为丢了
            L.append(f"- {s.get('name','')}　*level={s.get('level','') or '—'}（母版内部用，成稿不显示）*"
                     + (f"　*{' · '.join(tags)}*" if tags else ""))
        L.append("")

    ain = data.get("ai_native") or []
    if ain:
        L.append("## AI 原生能力（leverage）— 渲染为「专业技能」的分组")
        L.append("")
        L.append("> v10：不再单独成段，按 `group` 并入专业技能。")
        L.append("> 写法铁律：主句是能力 / 工作流，工具名只作附注。")
        L.append("")
        by_group = {}
        for a in ain:
            by_group.setdefault(a.get("group") or "AI 原生能力", []).append(a)
        for g, items in by_group.items():
            L.append(f"**{g}**")
            for a in items:
                line = f"- {a.get('capability','')}"
                if a.get("detail"):
                    line += f"：{a['detail']}"
                if a.get("evidence_refs"):
                    line += f"　`{','.join(a['evidence_refs'])}`"
                L.append(line)
                if a.get("evidence_note"):
                    note = a["evidence_note"].strip()
                    L.append(f"  - {note.splitlines()[0]}")
            L.append("")

    # 论文 / 专利 / 荣誉 —— 三段都是 v7 新增，不渲染就是静默丢失
    pubs = data.get("publications") or []
    if pubs:
        L.append("## 论文")
        L.append("")
        for p in pubs:
            mark = {"verified": "✔", "self_reported": "○", "pending": "**【待补】**",
                    "inferred": "⚠", "unusable": "🚫**【禁用】**"}.get(p.get("evidence"), "")
            L.append(f"- {mark} {p.get('title','')}")
            L.append(f"  - {p.get('venue','')}（{p.get('venue_level','')}）· {p.get('authorship','')} · {p.get('status','')}")
            if p.get("evidence_note"):
                L.append(f"  - {p['evidence_note']}")
        L.append("")

    pats = data.get("patents") or []
    if pats:
        L.append("## 专利")
        L.append("")
        for p in pats:
            mark = {"verified": "✔", "self_reported": "○", "pending": "**【待补】**",
                    "inferred": "⚠", "unusable": "🚫**【禁用】**"}.get(p.get("evidence"), "")
            L.append(f"- {mark} {p.get('title','')}　*{p.get('type','')} · {p.get('status','')}*")
            L.append(f"  - 权利人：{p.get('assignee','')}　发明人位次：{p.get('role','')}　{p.get('period','')}")
            if p.get("evidence_note"):
                L.append(f"  - {p['evidence_note']}")
        L.append("")

    hons = data.get("honors") or []
    if hons:
        L.append("## 荣誉")
        L.append("")
        for h in hons:
            mark = {"verified": "✔", "self_reported": "○", "pending": "**【待补】**",
                    "inferred": "⚠", "unusable": "🚫**【禁用】**"}.get(h.get("evidence"), "")
            tag = "　*校园内容（社招画像下自动过滤）*" if h.get("student_era") else ""
            L.append(f"- {mark} {h.get('name','')}　*{h.get('period','')}*{tag}")
            if h.get("evidence_note"):
                L.append(f"  - {h['evidence_note']}")
        L.append("")

    certs = data.get("certifications") or []
    if certs:
        L.append("## 证书与职称")
        L.append("")
        for p in certs:
            mark = {"verified": "✔", "self_reported": "○", "pending": "**【待补】**",
                    "inferred": "⚠", "unusable": "🚫**【禁用】**"}.get(p.get("evidence"), "")
            L.append(f"- {mark} {p.get('name','')}　*{p.get('issuer','')} · {p.get('level','')}*")
            if p.get("evidence_note"):
                L.append(f"  - {p['evidence_note']}")
        L.append("")

    gaps = [
        (e.get("id"), a)
        for e in (data.get("experiences") or [])
        for a in (e.get("achievements") or [])
        if a.get("evidence") == "pending"
    ]
    unconfirmed_edu = [e for e in edu if not e.get("confirmed", True)]
    if gaps or unconfirmed_edu:
        L.append("## 待补清单")
        L.append("")
        for eid, a in gaps:
            L.append(f"- **{a.get('id')}**（{eid}）：{a.get('evidence_note') or '需补充证据'}")
        for e in unconfirmed_edu:
            L.append(f"- **{e.get('id')}**（教育）：{e.get('note') or '待确认'}")
        L.append("")

    out.write_text("\n".join(L).rstrip() + "\n", encoding="utf-8")
    info(f"预览已生成: {out}")


# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["check", "lint", "preview"])
    ap.add_argument("path")
    ap.add_argument("--master", default="master/master.yaml")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    p = (WORKSPACE / args.path) if not Path(args.path).is_absolute() else Path(args.path)
    if not p.exists():
        print(f"文件不存在: {p}")
        return 1
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    grouped, replace = load_terms(ROOT / "config" / "forbidden_terms.txt")

    if args.action == "check":
        if "tailored" in data:
            mp = WORKSPACE / args.master
            if not mp.exists():
                print(f"找不到母版: {mp}")
                return 1
            mdata = yaml.safe_load(mp.read_text(encoding="utf-8")) or {}
            check_master(mdata)
            check_tailored(data, mdata)
        else:
            check_master(data)
        for e in data.get("experiences") or []:
            lint_text(e.get("raw_input"), e.get("id"), grouped, replace)
            for a in e.get("achievements") or []:
                txt = " ".join(
                    str(x)
                    for x in [
                        a.get("action"), a.get("object"), a.get("method"),
                        (a.get("result") or {}).get("value"), a.get("difficulty"),
                    ]
                    if x
                )
                lint_text(txt, a.get("id"), grouped, replace)

    elif args.action == "lint":
        for e in data.get("experiences") or []:
            lint_text(e.get("raw_input"), e.get("id"), grouped, replace)
            for a in e.get("achievements") or []:
                txt = " ".join(
                    str(x)
                    for x in [
                        a.get("action"), a.get("object"), a.get("method"),
                        (a.get("result") or {}).get("value"),
                    ]
                    if x
                )
                lint_text(txt, a.get("id"), grouped, replace)

    elif args.action == "preview":
        out = Path(args.out) if args.out else p.parent / "master.preview.md"
        render_preview(data, out)

    for x in errors:
        print(f"  ERROR   {x}")
    for x in warnings:
        print(f"  WARNING {x}")
    for x in infos:
        print(f"  INFO    {x}")
    print(f"\n{len(errors)} error / {len(warnings)} warning / {len(infos)} info")
    return 1 if errors else (2 if warnings else 0)


if __name__ == "__main__":
    sys.exit(main())

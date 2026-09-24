#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
篇幅引擎 density.py —— 把「一页 A4 装得下吗」变成可计算的量。

为什么需要它：
    简历短是**结果**不是原因。素材采集不足、bullet 缺结果、段落缺失，
    最后都表现为「成稿只有半页」。靠肉眼判断「好像有点短」永远改不干净，
    因为没有人知道该补多少、补在哪一段。

    本脚本按 render_resume.py 的真实排版参数（A4 / padding 15mm×18mm /
    正文 14px / line-height 1.7）累加每个块的高度，估算成稿页数，
    并指出缺口集中在哪一段 —— 从而把「补内容」变成一个可指派的动作。

交付什么：
    1. 容量模型        —— 一页 A4 到底能装多少
    2. 分段落占用      —— 每段吃了多少高度
    3. 页数与填充率    —— 现在是几页、填满了百分之几
    4. 扩写优先级      —— 还差多少、该往哪一段补、用什么方式补

重要边界：
    **本脚本只诊断，不生产内容。** 缺口一律转成「追问 / 展开 / 补段落」三类动作，
    绝不自行生成一条 bullet 填进去 —— 那是编造，不是补篇幅。

用法：
    python scripts/density.py --person 张三
    python scripts/density.py --person 张三 --mode final
    python scripts/density.py --person 张三 --json
"""

import argparse
import io
import json
import os
import re
import sys
import unicodedata

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 包根：config/
WORKSPACE = os.environ.get("RESUME_WORKSPACE") or os.getcwd()        # 工作区：people/ 所在目录
PEOPLE = os.path.join(WORKSPACE, "people")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ───────────────────────────────────────────────────────────
# 1. 容量模型 —— 与 render_resume.py 的 CSS 严格对应
# ───────────────────────────────────────────────────────────
# 改 render_resume.py 的 .page / body 样式时，这里的常量必须同步改。
# 不同步的后果：页数估算漂移，扩写建议给错量。

MM = 3.7795  # 1mm = 3.7795px

PAGE = {
    "width_mm": 210,
    "height_mm": 297,
    "pad_y_mm": 15,      # .page padding: 15mm 18mm（2026-09-23 由 16mm 收紧 1mm：
                         #   伯克希尔+巴菲特合伙这种巨型经历块在 A4 上只差 ~1mm 塞不下、
                         #   被整块外推留下 ~74mm 首页空白；收紧 1mm 让首页填满，
                         #   预览/打印/模型仍严格一致）
    "pad_x_mm": 18,
    "body_px": 14,       # body font-size:14px
    "line_h": 1.7,       # body line-height:1.7
}

CONTENT_W_PX = (PAGE["width_mm"] - 2 * PAGE["pad_x_mm"]) * MM     # 174mm
CONTENT_H_PX = (PAGE["height_mm"] - 2 * PAGE["pad_y_mm"]) * MM    # 267mm (15mm 边距)
CONTENT_H_MM = PAGE["height_mm"] - 2 * PAGE["pad_y_mm"]           # 267mm，供多处复用，避免硬编码漂移
LINE_PX = PAGE["body_px"] * PAGE["line_h"]                        # 23.8px
LINES_PER_PAGE = int(CONTENT_H_PX // LINE_PX)                     # 42 行

# 各块的高度权重（px）。取自 render_resume.py 的 CSS margin/padding。
# ⚠ 以下常量经 scripts/measure_pages.js --detail 实测校准（2026-08-30）。
#    校准前模型对单页简历高估 13~20 个百分点 —— 不准的篇幅引擎比没有更糟，
#    因为它会给出「再补 5 条 bullet」这种错误指令。改 render 的 CSS 后必须重跑校准。
BLOCK = {
    # h1 未单独设 line-height，继承 body 的 1.7 → 26*1.7=44.2（实测 44.2）
    "name":        26 * 1.7 + 4,
    "contact":     13 * 1.7 + 16 + 10 + 2,       # .contact 含 border 与 padding
    "intent":      14 * 1.7 + 6,
    "summary_line":13 * 1.8,                     # .summary font-size:13px lh:1.8
    "h2":          15 * 1.7 + 18 + 8,            # 段标题（含上下 margin）
    "item_hd":     14 * 1.7,                     # 经历标题行
    "item_gap":    13,                           # .item margin-bottom
    "ul_top":      5,                            # ul margin-top
    "li_gap":      3,                            # li margin-bottom
    "li_indent":   19,                           # ul padding-left
    "skill_line":  LINE_PX + 4,
    # 每条教育实测 47.9px ≈ 2 行（学校+时间 / 学位+专业），另加 .item 的 margin-bottom
    "edu_line":    2 * (13 * 1.7 + 2) + 13,
    "cert_line":   LINE_PX + 4,      # 实测证书行按 .skill-line 渲染，含 margin-bottom 4
    "honor_line":  LINE_PX + 4,
    "pub_line":    LINE_PX + 2,
    # 页脚：final 模式带 noprint，打印时不占空间，故不计入打印高度
    "footer":      18 + 8 + 11 * 1.7,
}

# 填充率目标。低于 min 触发扩写，高于 safe_max 触发「过满」警告。
#
# ⚠ 为什么上限是 0.96 而不是 1.00 —— 踩过的坑：
#   填充率按「内容总量 ÷ 页容量」算，但分页是**按块边界切**的。
#   总量 97% 时，最后一个块（往往是教育背景，需 5 行）放不下，
#   会被整块挤到第二页 —— 于是「0.97 页」打印出来是两页，第二页 8%。
#   所以「填满」的目标区间是 [min_fill, safe_max]，不是越高越好。
#   留 4%~12% 余量，才是真的能装进一页。
TARGET = {
    "campus":      {"pages": 1, "min_fill": 0.88, "safe_max": 0.96},
    "junior":      {"pages": 1, "min_fill": 0.88, "safe_max": 0.96},
    "experienced": {"pages": 1, "min_fill": 0.85, "safe_max": 0.96},
    "expert":      {"pages": 2, "min_fill": 0.80, "safe_max": 0.96},
}


def em_width(text):
    """视觉宽度（单位 em）。CJK = 1em，其余按全角/半角折算。

    14px 下 CJK 字宽恰为 14px，故 1 个汉字 = 1em，1 个 ASCII ≈ 0.5em。
    """
    if text is None:
        return 0.0
    w = 0.0
    for ch in str(text):
        if unicodedata.east_asian_width(ch) in ("W", "F", "A"):
            w += 1.0
        else:
            w += 0.52
    return w


def wrap_lines(text, width_em):
    """按宽度折行。中文可任意断行，故直接用累计宽度切。"""
    if not text:
        return 0
    w = em_width(text)
    return max(1, int(w // width_em) + (1 if w % width_em else 0))


def content_width_em(indent_px=0, font_px=None):
    """给定缩进与字号，返回该区域一行能放多少 em。"""
    font_px = font_px or PAGE["body_px"]
    px = CONTENT_W_PX - indent_px
    em = font_px  # 1em = font_px
    return px / em


class Ruler:
    """高度累加器。所有 add_* 统一走这里，便于换排版参数。"""

    def __init__(self):
        self.total = 0.0
        self.sections = []   # [(段名, 高度px, 明细dict)]

    def _push(self, sec, px, detail=None):
        self.total += px
        self.sections.append((sec, px, detail or {}))

    def add(self, sec, px, detail=None):
        self._push(sec, px, detail)


# ───────────────────────────────────────────────────────────
# 2. 素材 → 高度
# ───────────────────────────────────────────────────────────

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _bullet_text(a):
    """复刻 render_resume.py 的 bullet 拼装（简化版，只为量高度）。"""
    parts = []
    act = (a.get("action") or "").strip()
    obj = (a.get("object") or "").strip()
    meth = (a.get("method") or "").strip()
    diff = (a.get("difficulty") or "").strip()
    res = a.get("result") or {}
    if isinstance(res, dict):
        metric = (res.get("metric") or "").strip()
        value = (res.get("value") or "").strip()
        scope = (res.get("scope") or "").strip()
        r = " ".join(x for x in [metric, value] if x)
        if scope:
            r = (r + "（范围：" + scope + "）") if r else "范围：" + scope
    else:
        r = str(res or "").strip()

    if act and obj:
        parts.append(act.rstrip("，, ") + ("" if act.endswith(("了", "过")) else "") + obj)
    elif obj:
        parts.append(obj)
    if meth:
        parts.append(meth)
    if r:
        parts.append(r)
    if diff:
        parts.append("（难点：" + diff + "）")
    return "，".join(p for p in parts if p)


def _visible(ev, mode):
    """evidence 在出片模式下的可见性（与 render_resume.py 同规则）。"""
    if mode == "final":
        return ev not in ("pending", "inferred", "unusable")
    return ev not in ("inferred", "unusable")


def measure(master, mode="final"):
    """估算成稿高度，返回 (Ruler, 统计dict)。"""
    owner = master.get("owner") or {}
    pref = master.get("preferences") or {}
    profile = pref.get("profile", "experienced")
    r = Ruler()
    stat = {
        "profile": profile,
        "mode": mode,
        "n_exp": 0, "n_bullet": 0, "n_skill_line": 0,
        "empty_result": 0, "empty_diff": 0,
        "hidden_pending": 0,
    }

    # ── 头部
    r.add("头部", BLOCK["name"], {"姓名": owner.get("name", "")})
    if pref.get("show_intention"):
        t = (master.get("targeting") or {}).get("intention", "")
        if t:
            r.add("头部", BLOCK["intent"])
    r.add("头部", BLOCK["contact"])

    # ── 摘要
    sm = master.get("summary") or {}
    if sm.get("enabled") and sm.get("text"):
        w = content_width_em(font_px=13)
        n = wrap_lines(sm["text"].strip(), w)
        r.add("摘要", BLOCK["h2"] + n * BLOCK["summary_line"], {"行数": n})

    # ── 经历
    exps = master.get("experiences") or []
    li_w = content_width_em(indent_px=BLOCK["li_indent"])
    exp_h = 0.0
    for e in exps:
        stud = bool(e.get("student_era"))
        if stud and profile in ("experienced", "expert"):
            continue
        achs = [a for a in (e.get("achievements") or [])
                if _visible(a.get("evidence"), mode)]
        stat["hidden_pending"] += len(e.get("achievements") or []) - len(achs)
        if not achs:
            continue
        stat["n_exp"] += 1
        h = BLOCK["item_hd"] + BLOCK["ul_top"]
        for a in achs:
            txt = _bullet_text(a)
            n = wrap_lines(txt, li_w)
            h += n * LINE_PX + BLOCK["li_gap"]
            stat["n_bullet"] += 1
            if not (a.get("result") or {}).get("value" if isinstance(a.get("result"), dict) else None):
                stat["empty_result"] += 1
            if not (a.get("difficulty") or "").strip():
                stat["empty_diff"] += 1
        h += BLOCK["item_gap"]
        exp_h += h
    if stat["n_exp"]:
        exp_h += BLOCK["h2"]          # 段标题只在有内容时出现，且只算一次
    else:
        exp_h = 0.0
    r.add("工作经历", exp_h, {"段数": stat["n_exp"], "bullet 数": stat["n_bullet"]})

    # ── 技能（按分组折行，与 render 同：一行放不下就拆行）
    skills = [s for s in (master.get("skills") or [])
              if s.get("status") != "archived"]
    ai = master.get("ai_native") or []
    groups = {}
    for s in skills + ai:
        g = s.get("group") or s.get("category") or "其他"
        if _visible(s.get("evidence"), mode) and s.get("evidence") in ("pending", "inferred", "unusable") and mode == "final":
            continue
        groups.setdefault(g, []).append(s.get("name", ""))
    sk_h = 0.0
    if groups:
        sk_h += BLOCK["h2"]
        sk_w = content_width_em(indent_px=0)
        for g, names in groups.items():
            line = g + "：" + "、".join(n for n in names if n)
            n = wrap_lines(line, sk_w)
            # 拆行时次行用 .skill-cont 缩进 6.2em
            first_w = content_width_em(indent_px=0)
            cont_w = content_width_em(indent_px=6.2 * PAGE["body_px"])
            w = em_width(line)
            if w > first_w:
                rest = max(0.0, w - first_w)
                n = 1 + max(1, int(rest // cont_w) + (1 if rest % cont_w else 0))
            sk_h += n * LINE_PX + 4
            stat["n_skill_line"] += n
    r.add("专业技能", sk_h, {"分组数": len(groups)})

    # ── 证书 / 荣誉 / 论文 / 专利
    # 论文与专利合并为一段（渲染器也是同一段渲染），段标题只算一次。
    def _count(key, predicate):
        return len([x for x in (master.get(key) or []) if predicate(x)])

    vis = lambda x: _visible(x.get("evidence"), mode)

    n_cert = _count("certifications", vis)
    n_honor = _count("honors", lambda x: vis(x) and not (
        x.get("student_era") and profile in ("experienced", "expert")))
    # 复刻渲染器的荣誉门控：剩下的全是 relevance: low 就整段不出现。
    # 漏掉这条会让模型凭空多算一整段（实测在王五母版上多算了 99px ≈ 23% 误差）。
    honors = [x for x in (master.get("honors") or [])
              if vis(x) and not (x.get("student_era") and profile in ("experienced", "expert"))]
    if honors and not any(
            (str(x.get("relevance") or "low").lower() in ("high", "medium", "mid"))
            for x in honors):
        n_honor = 0
    n_pub = _count("publications", vis)
    n_pat = _count("patents", vis)

    if n_cert:
        r.add("证书与职称", BLOCK["h2"] + n_cert * BLOCK["cert_line"], {"条数": n_cert})
    if n_honor:
        r.add("荣誉奖励", BLOCK["h2"] + n_honor * BLOCK["honor_line"], {"条数": n_honor})
    n_pp = n_pub + n_pat
    if n_pp:
        r.add("论文与专利", BLOCK["h2"] + n_pp * BLOCK["pub_line"],
              {"论文": n_pub, "专利": n_pat})

    # ── 教育
    edus = master.get("education") or []
    if edus:
        campus = profile == "campus"
        h = BLOCK["h2"] + sum(BLOCK["edu_line"] for _ in edus)
        r.add("教育背景", h, {"条数": len(edus), "位置": "置顶" if campus else "沉底"})

    return r, stat


# ───────────────────────────────────────────────────────────
# 3. 诊断与扩写建议
# ───────────────────────────────────────────────────────────

# 残页阈值：最后一页填充低于此比例即视为「残页」。
# 为什么是 0.55：残页比内容少更糟 —— HR 翻到第二页只看到三行教育背景，
# 读到的是「这人没东西可写」，而不是「这人经验多到要两页」。
ORPHAN_FILL = 0.55
# 实测通道下的最小安全余量（mm）。低于这个值，字体回退、换机打印、
# 或用户往里再加一句话，都会把最后一个块挤到下一页形成残页。
SLACK_MM = 3.0


def diagnose(ruler, stat, pref):
    """自适应页数诊断。

    目标页数**由素材量决定，profile 只给上限** —— 这是修过的一个坑：
    死按 profile 定目标页数，会让一个只有 3 条 bullet 的资深人士
    被要求「再补 26 条」，而这个建议没人会执行。

    两件事分别判：
      1. 总填充率 fill     —— 整体够不够
      2. 末页填充 last_fill —— 有没有残页（1.4 页是最差状态，不是「内容多」）
    """
    profile = stat["profile"]
    tgt = TARGET.get(profile, TARGET["experienced"])
    max_pages = int((pref or {}).get("max_pages") or tgt["pages"]) or 1

    page_cap = LINES_PER_PAGE * LINE_PX          # 单页净容量
    # 页脚带 noprint，打印时不占空间；只有校对模式（页脚会显示）才计入。
    used = ruler.total + (BLOCK["footer"] if stat.get("mode") == "draft" else 0)
    raw_pages = used / page_cap

    want = min(max_pages, max(1, int(-(-raw_pages // 1))))   # ceil
    total_cap = page_cap * want
    fill = used / total_cap
    last_fill = (used - page_cap * (want - 1)) / page_cap
    orphan = want > 1 and last_fill < ORPHAN_FILL

    # 补满当前页数还差多少行
    deficit_lines = max(0.0, (total_cap - used) / LINE_PX)
    # 残页时：把最后一页的内容砍掉，退回上一页，需要减掉多少行
    trim_lines = max(0.0, (used - page_cap * (want - 1)) / LINE_PX) if want > 1 else 0.0

    li_w = content_width_em(indent_px=BLOCK["li_indent"])

    return {
        "profile": profile,
        "max_pages": max_pages,
        "want_pages": want,
        "used_px": round(used, 1),
        "capacity_px": round(total_cap, 1),
        "pages": round(raw_pages, 2),
        "fill": round(fill, 3),
        "last_fill": round(last_fill, 3),
        "orphan": orphan,
        "min_fill": tgt["min_fill"],
        "deficit_lines": round(deficit_lines, 1),
        "deficit_chars": int(deficit_lines * li_w),
        "trim_lines": round(trim_lines, 1),
        "safe_max": tgt["safe_max"],
        # 过满：总量贴着页容量，下一个块随时会被挤出去形成残页
        "tight": fill > tgt["safe_max"] and want >= max_pages,
        "ok": (not orphan) and fill >= tgt["min_fill"] and fill <= tgt["safe_max"],
        "overflow": want > max_pages or raw_pages > max_pages + 0.02,
        "bullet_equiv": round(deficit_lines / 2, 1),
    }


def suggest(diag, stat, master):
    """把缺口翻译成**可指派的动作**。

    三条铁律：
      1. 只输出「去问用户什么」「去展开哪个已有点」，不输出新事实
      2. 优先级按「单位提问能换来多少字数」排序
      3. 缺口大时必须先问「有没有漏掉的经历/项目」，而不是硬拆已有 bullet
    """
    out = []
    deficit_lines = diag["deficit_lines"]

    # ── 残页分支：给出两条互斥路径，让用户选，而不是替他决定。
    #
    # 残页和「内容不足」是不同状态：
    #   · 内容不足 = 只有 1 页，且这页没满。可以建议按 2 页写，也可以补到 1 页满。
    #   · 残页     = 已经需要 2 页，但第 2 页只填了 <55%。
    #
    # 所以残页的选项永远是：A 砍回 want_pages-1 页，或 B 把 want_pages 这页补到
    # 合理填充。和「还能不能扩到更多页」无关——扩页只会让更多页变空，更糟。
    if diag["orphan"]:
        ask = ("二选一，你定：\n"
               "       【A 砍回 %d 页】删掉约 %d 行 —— 优先砍与 JD 无关的 bullet、"
               "commodity 技能、学生期荣誉"
               % (diag["want_pages"] - 1, round(diag["trim_lines"])))
        # 把末页从当前 last_fill 补到 min_fill 所需行数
        need_fill = diag["min_fill"] - diag["last_fill"]
        if need_fill > 0:
            need_mm = need_fill * PAGE["height_mm"]
            need_lines = round(need_mm * 3.7795 / LINE_PX, 1)
            need_chars = int(need_lines * content_width_em(indent_px=BLOCK["li_indent"]))
            ask += ("\n       【B 补满 %d 页】再补约 %.1f 行 ≈ %d 字，"
                    "把末页填充从 %.0f%% 提到 %.0f%%（下限）"
                    % (diag["want_pages"], need_lines, need_chars,
                       diag["last_fill"] * 100, diag["min_fill"] * 100))
        if diag["want_pages"] >= diag["max_pages"]:
            ask += ("\n       （页数上限已是 %d 页，不能再扩更多页，"
                    "只能在当前页数内砍或补）" % diag["max_pages"])
        out.append({
            "pri": 0, "type": "残页",
            "action": "末页只填了 %.0f%%，打印出来是「两页但第二页几乎空着」"
                      % (diag["last_fill"] * 100),
            "detail": "当前 %.2f 页；末页 %d 行 / 满页 %d 行"
                      % (diag["pages"], round(diag["trim_lines"]), LINES_PER_PAGE),
            "ask": ask,
            "gain": "—— 残页是比内容少更糟的状态，必须处理，没有第三条路",
        })
    elif diag.get("tight"):
        # 过满但还没掉块：这是最后的预警窗口，此时砍最省事
        out.append({
            "pri": 0, "type": "过满",
            "action": "填充 %.0f%% 已贴住页边界 —— 再来一个块就会被挤成残页"
                      % (diag["fill"] * 100),
            "detail": "建议区间 %.0f%%–%.0f%%"
                      % (diag["min_fill"] * 100, diag["safe_max"] * 100),
            "ask": "建议砍掉约 %d 行留余量：优先砍与 JD 无关的 bullet、"
                   "commodity 技能、学生期荣誉。\n"
                   "       也可以先 render 后用 --measure 实测确认是否真的没掉块"
                   % max(1, round((diag["fill"] - diag["safe_max"]) * LINES_PER_PAGE)),
            "gain": "—— 现在砍 2 行，胜过出片后发现第二页只有 4 行",
        })

    if deficit_lines <= 1:
        return sorted(out, key=lambda x: x["pri"])

    # 第一优先：漏采的段落（一次提问换一整段）
    if deficit_lines > 6:
        missing_sections = []
        if not (master.get("experiences") or []):
            missing_sections.append("工作经历")
        if stat["n_exp"] and not (master.get("skills") or []):
            missing_sections.append("专业技能")
        if not (master.get("certifications") or []):
            missing_sections.append("证书与职称")
        if not (master.get("education") or []):
            missing_sections.append("教育背景")
        if missing_sections:
            out.append({
                "pri": 1, "type": "缺段",
                "action": "整段缺失，先补结构再谈润色",
                "detail": "、".join(missing_sections),
                "ask": "这些段落一条都没有 —— 是真的没有，还是还没采集？",
                "gain": "高（一次提问换一整段）",
            })
        out.append({
            "pri": 1, "type": "漏采经历",
            "action": "追问有没有没写进去的经历",
            "detail": "兼职 / 外包 / 实训 / 课程设计 / 竞赛 / 开源 / 志愿 / 内部专项",
            "ask": "除了已经写的几段，还有没有其他干过、但觉得『不算正式工作』就没写的事？"
                   "（这类往往是最能撑篇幅的）",
            "gain": "高",
        })

    # 第二优先：给已有 bullet 补「结果 / 难点」（一次提问换一行）
    if stat["empty_result"]:
        out.append({
            "pri": 2, "type": "补结果",
            "action": "给没有 result 的 bullet 补量化结果",
            "detail": "%d / %d 条 bullet 没有结果" % (stat["empty_result"], stat["n_bullet"]),
            "ask": "这件事做完之后，什么变了？"
                   "（耗时 / 错误率 / 人数 / 金额 / 频次 —— 哪怕是个大概范围）",
            "gain": "中高（每条 +0.5~1 行，且直接提升抗追问能力）",
        })
    if stat["empty_diff"]:
        out.append({
            "pri": 2, "type": "补难点",
            "action": "给没有 difficulty 的 bullet 补难点",
            "detail": "%d / %d 条 bullet 没有难点" % (stat["empty_diff"], stat["n_bullet"]),
            "ask": "这件事里最卡你的是哪一步？换个人来做，他可能卡在哪？",
            "gain": "中（每条 +0.5 行，且是最难编造、最能抗追问的一项）",
        })

    # 第三优先：加 bullet（每段经历 2-3 条是标准密度）
    if stat["n_exp"]:
        avg = stat["n_bullet"] / max(1, stat["n_exp"])
        if avg < 2.5:
            out.append({
                "pri": 3, "type": "加 bullet",
                "action": "每段经历补足 2-3 条 bullet",
                "detail": "当前平均 %.1f 条 / 段" % avg,
                "ask": "这段工作里，除了已经写的，还有哪件事是你独立扛下来的？",
                "gain": "中",
            })

    # 第四优先：可开的段落
    sm = master.get("summary") or {}
    if not sm.get("enabled"):
        out.append({
            "pri": 4, "type": "开摘要",
            "action": "开启 3 行摘要（社招最强去 low 手段）",
            "detail": "当前关闭",
            "ask": "要不要加一段 3 行摘要？需本人确认措辞",
            "gain": "中（约 3 行，且让首屏立刻成立）",
        })

    out.sort(key=lambda x: x["pri"])
    return out


# ───────────────────────────────────────────────────────────
# 4. CLI
# ───────────────────────────────────────────────────────────

def load_master(person):
    p = os.path.join(PEOPLE, person, "master.yaml")
    if not os.path.exists(p):
        raise SystemExit("母版不存在：%s" % p)
    with io.open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# 实测通道：调 scripts/measure_pages.js 用真实浏览器量页数
#
# 估算模型给快速反馈（毫秒级，可反复跑）；实测给最终确认（秒级，出片前跑一次）。
# 两者并存是因为它们解决不同问题：
#   采集过程中要的是「现在够不够」的方向感 —— 估算够用
#   出片前要的是「打印出来是几页」的确定性 —— 必须实测
#
# 实测通道不可用时回落到估算，但**必须把原因说清楚**：
#   静默回落会让使用者以为「已经实测确认过了」，而实际上拿到的只是估算值。
#   估算与实测在本项目里曾相差 15%（王五：估算 109% / 实测 94%），
#   把估算当实测用，等于在残页问题上自欺欺人。
# ---------------------------------------------------------------------------


def _find_node():
    """动态定位 node 解释器，绝不硬编码某个用户的 home 目录。

    优先级：NODE_BIN 环境变量 → PATH 里的 node → workbuddy 托管目录 → 常见安装位。
    """
    import shutil
    candidates = [os.environ.get("NODE_BIN", "")]
    found = shutil.which("node")
    if found:
        candidates.append(found)

    home = os.path.expanduser("~")
    managed = os.path.join(home, ".workbuddy", "binaries", "node", "versions")
    if os.path.isdir(managed):
        try:
            for ver in sorted(os.listdir(managed), reverse=True):
                for sub in ("node.exe", os.path.join("bin", "node")):
                    p = os.path.join(managed, ver, sub)
                    if os.path.exists(p):
                        candidates.append(p)
        except OSError:
            pass

    for p in (r"C:\Program Files\nodejs\node.exe",
              r"C:\nodejs\node.exe"):
        if os.path.exists(p):
            candidates.append(p)

    return next((c for c in candidates if c and os.path.exists(c)), None)


def _find_node_modules():
    """动态定位装了 playwright 的 node_modules。"""
    env_nm = os.environ.get("NODE_PATH", "")
    if env_nm and os.path.isdir(env_nm):
        return env_nm

    home = os.path.expanduser("~")
    for p in (os.path.join(home, ".workbuddy", "binaries", "node", "workspace", "node_modules"),
              os.path.join(home, ".workbuddy", "node", "node_modules"),
              os.path.join(ROOT, "node_modules")):
        if os.path.isdir(p):
            return p
    return None


def _probe_playwright(node, node_modules):
    """确认 playwright 真的可用（装了包但没下浏览器也要报出来）。"""
    import subprocess
    env = os.environ.copy()
    if node_modules:
        env["NODE_PATH"] = node_modules
    try:
        r = subprocess.run([node, "-e", "require('playwright')"],
                           capture_output=True, env=env, timeout=60)
        if r.returncode != 0:
            detail = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
            return False, (detail[-1] if detail else "playwright 未安装")
        return True, ""
    except Exception as e:
        return False, str(e)


def measure_real(person, mode="final"):
    """返回 (实测字典, 失败原因)。成功时 reason 为 None，失败时 data 为 None。"""
    html = os.path.join(PEOPLE, person, "output",
                        "resume-draft.html" if mode == "draft" else "resume-final.html")
    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure_pages.js")

    if not os.path.exists(html):
        return None, "还没出片（找不到 %s），先跑 render" % os.path.basename(html)
    if not os.path.exists(js):
        return None, "缺少 scripts/measure_pages.js"

    node = _find_node()
    if not node:
        return None, "找不到 node 解释器（可设 NODE_BIN 环境变量指定）"

    node_modules = _find_node_modules()
    ok, why = _probe_playwright(node, node_modules)
    if not ok:
        return None, "playwright 不可用：%s" % why

    env = os.environ.copy()
    if node_modules:
        env["NODE_PATH"] = node_modules
    try:
        import subprocess
        r = subprocess.run([node, js, html, "--json"],
                           capture_output=True, env=env, timeout=180)
        if r.returncode != 0:
            detail = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
            tail = detail[-1] if detail else "退出码 %d" % r.returncode
            return None, "measure_pages.js 执行失败：%s" % tail
        data = json.loads(r.stdout.decode("utf-8", "replace"))
        return (data[0] if data else None), None
    except json.JSONDecodeError:
        return None, "measure_pages.js 输出不是合法 JSON"
    except Exception as e:
        return None, "实测异常：%s" % e


def fmt(ruler, diag, sug, stat):
    L = []
    a = L.append
    a("=" * 62)
    a("篇幅诊断  ·  profile=%s  mode=%s" % (diag["profile"], stat["mode"]))
    a("=" * 62)
    a("")
    a("【容量模型】A4 210×297mm，边距 15/18mm，正文 14px / 行高 1.7")
    a("  正文区   %.0fmm 宽 × %.0fmm 高  →  %d 行 / 页"
      % ((PAGE["width_mm"] - 36), (PAGE["height_mm"] - 32), LINES_PER_PAGE))
    a("  每行约   %.0f 个汉字（正文）" % content_width_em(indent_px=BLOCK["li_indent"]))
    a("")
    a("【分段落占用】")
    for sec, px, detail in ruler.sections:
        if px <= 0:
            continue
        d = "  ".join("%s=%s" % (k, v) for k, v in detail.items() if v not in ("", None))
        a("  %-8s %7.0f px  %5.1f 行   %s" % (sec, px, px / LINE_PX, d))
    a("  %-8s %7.0f px  %5.1f 行" % ("页脚", BLOCK["footer"], BLOCK["footer"] / LINE_PX))
    a("  " + "-" * 56)
    a("  %-8s %7.0f px  %5.1f 行" % ("合计", ruler.total, ruler.total / LINE_PX))
    a("")
    a("【结论】")
    a("  素材量 %.2f 页  →  建议按 %d 页出（profile 上限 %d 页）"
      % (diag["pages"], diag["want_pages"], diag["max_pages"]))
    a("  整体填充 %.0f%%  末页填充 %.0f%%（下限 %.0f%%，残页线 %.0f%%）"
      % (diag["fill"] * 100, diag["last_fill"] * 100,
         diag["min_fill"] * 100, ORPHAN_FILL * 100))
    if diag["overflow"]:
        a("  ⚠ 超出 profile 页数上限，必须收敛")
    elif diag.get("tight"):
        if diag.get("_source", "").startswith("实测"):
            a("  ⚠ 过满：末页只剩 %.1fmm 余量（安全余量 %.1fmm）"
              % (diag.get("slack_mm", 0), SLACK_MM))
            a("     实测没有估算误差要吸收，但字体回退或换机打印就会溢出 —— 建议砍 1 行")
        else:
            a("  ⚠ 过满：%.0f%% 已贴住页边界（安全上限 %.0f%%）"
              % (diag["fill"] * 100, diag["safe_max"] * 100))
            a("     分页按块边界切 —— 再来一个块就会被整块挤到下一页，形成残页")
    elif diag["orphan"]:
        a("  ❌ 残页：第二页只有 %.0f%% 内容 —— 比只有一页更糟" % (diag["last_fill"] * 100))
        a("     砍回 1 页需减约 %d 行；填满 2 页需补约 %d 行 ≈ %d 字"
          % (round(diag["trim_lines"]), round(diag["deficit_lines"]), diag["deficit_chars"]))
    elif diag["ok"]:
        a("  ✅ 篇幅达标")
    else:
        a("  ❌ 篇幅不足：还差 %.1f 行 ≈ %d 字"
          % (diag["deficit_lines"], diag["deficit_chars"]))
        a("     （按「一条 bullet ≈ 2 行」折算，约需再补 %.1f 条）" % diag["bullet_equiv"])
    a("")
    if sug:
        a("【扩写优先级】—— 只给动作，不给内容")
        a("")
        for s in sug:
            a("  P%d  [%s] %s" % (s["pri"], s["type"], s["action"]))
            a("      现状：%s" % s["detail"])
            a("      追问：%s" % s["ask"])
            a("      收益：%s" % s["gain"])
            a("")
    a("  注：以上全部是「去问用户什么」。篇幅缺口不通过生成内容来填，")
    a("      只通过采集到更多真实素材来填 —— 这是硬边界。")
    return "\n".join(L)


def merge_real(diag, real):
    """实测优先：用浏览器量出的真实值覆盖估算值。

    估算可以给错方向，实测不会 —— 出片前以实测为准。
    """
    if not real or "rows" not in real or not real["rows"]:
        return diag, None
    total_mm = sum(r["height_mm"] for r in real["rows"])
    pages = len(real["rows"])
    last_fill = real["rows"][-1]["fill"]
    diag = dict(diag)
    diag["_source"] = "实测（playwright）"
    diag["want_pages"] = pages
    diag["pages"] = round(total_mm / CONTENT_H_MM, 2)
    diag["last_fill"] = last_fill
    diag["fill"] = round(total_mm / (CONTENT_H_MM * pages), 3)
    diag["orphan"] = pages > 1 and last_fill < ORPHAN_FILL
    diag["overflow"] = bool(real.get("overflow")) or pages > diag["max_pages"]
    diag["ok"] = (not diag["orphan"]) and diag["fill"] >= diag["min_fill"]
    # 实测下重算缺口
    page_cap_px = LINES_PER_PAGE * LINE_PX
    used_px = total_mm * 3.7795
    diag["deficit_lines"] = round(max(0.0, (CONTENT_H_MM * pages - total_mm) * 3.7795 / LINE_PX), 1)
    diag["deficit_chars"] = int(diag["deficit_lines"] * content_width_em(
        indent_px=BLOCK["li_indent"]))
    diag["trim_lines"] = round(real["rows"][-1]["height_mm"] * 3.7795 / LINE_PX, 1) \
        if pages > 1 else 0.0
    diag["bullet_equiv"] = round(diag["deficit_lines"] / 2, 1)
    # tight 在实测下的含义和估算下不同，别混用同一个阈值：
    #   估算有 ±12% 误差 —— safe_max 0.96 是为吸收这个误差留的垫子；
    #   实测是浏览器真排过一遍，pages=1 就是 1 页，没有误差要吸收。
    # 再垫一层就会把「实测 98% 的单页」误判成过满（李四：实测 259mm 单页，
    # 被 0.96 判失败）。实测只剩一个真实风险：末页余量太小，字体回退或
    # 换一台机器打印就可能溢出。所以改用毫米余量判定，而不是百分比。
    slack_mm = CONTENT_H_MM - real["rows"][-1]["height_mm"]
    diag["slack_mm"] = round(slack_mm, 1)
    diag["tight"] = (0 <= slack_mm < SLACK_MM) or (pages > 1 and last_fill > 0.98)
    diag["ok"] = (not diag["orphan"]) and diag["fill"] >= diag["min_fill"] \
        and not diag["tight"] and not diag["overflow"]
    return diag, real


def main():
    ap = argparse.ArgumentParser(description="简历篇幅诊断")
    ap.add_argument("--person", required=True)
    ap.add_argument("--mode", default="final", choices=["draft", "final"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--measure", action="store_true",
                    help="用真实浏览器实测页数（需先 render，较慢但准确）")
    args = ap.parse_args()

    master = load_master(args.person)
    ruler, stat = measure(master, args.mode)
    diag = diagnose(ruler, stat, master.get("preferences") or {})
    diag.setdefault("_source", "估算模型")

    real = None
    if args.measure:
        real, reason = measure_real(args.person, args.mode)
        if real and "rows" in real:
            diag, real = merge_real(diag, real)
        elif not args.json:
            # 必须说清原因：静默回落会让使用者以为页数已被实测确认。
            print("[!] 实测未执行 —— %s" % reason)
            print("    下方为估算值，不是实测值。估算与实测可能相差 15% 以上，")
            print("    出片前请以实测为准。\n")

    sug = suggest(diag, stat, master)

    if args.json:
        print(json.dumps({
            "person": args.person, "diag": diag, "stat": stat,
            "sections": [{"sec": s, "px": round(p, 1), "detail": d} for s, p, d in ruler.sections],
            "real": real, "suggest": sug,
        }, ensure_ascii=False, indent=2))
    else:
        print(fmt(ruler, diag, sug, stat))
        if real and real.get("rows"):
            print("【浏览器实测】")
            for r in real["rows"]:
                bar = "█" * max(0, round(r["fill"] * 20))
                print("  第%d页 %s %3.0f%%  %dmm/%dmm"
                      % (r["page"], bar.ljust(20, "·"), r["fill"] * 100, r["height_mm"], CONTENT_H_MM))
                      % (r["page"], bar.ljust(20, "·"), r["fill"] * 100, r["height_mm"]))
            if real.get("overflow"):
                print("  ⚠ 有页内容超出 A4 内容区，分页未兜住")
            else:
                # 余量是「还能往里加多少」的预算，比百分比直观得多
                print("  末页余量 %.1fmm（安全余量 %.1fmm）"
                      % (diag.get("slack_mm", 0), SLACK_MM))
            print("")

    return 0 if diag["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

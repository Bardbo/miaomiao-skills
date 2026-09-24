#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
母版 YAML → 可投递的 HTML 简历

出片环节落实防造假规则（这是与 render_preview 的本质区别）：
  evidence=unusable  → 完全不渲染（权属/涉密，禁止对外）
  evidence=inferred  → 完全不渲染（推断内容）
  evidence=pending   → 强主张动词降级（主导→参与）；校对模式标【待补】，出片模式默认隐藏
  evidence=verified  → 正常渲染

两种模式：
  --mode draft   校对模式：显示【待补】标记与缺口清单，给用户看还差什么
  --mode final   出片模式：干净成稿，可直接打印/存 PDF 投递

用法：
  python scripts/render_resume.py master/master.yaml -o output/resume.html
  python scripts/render_resume.py master/master.yaml --mode final -o output/resume_final.html
  python scripts/render_resume.py master/master.yaml --target targets/xxx/tailored.yaml -o out.html
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tailored_io import load_tailored   # noqa: E402  兼容新旧两种 tailored schema

ROOT = Path(__file__).resolve().parent.parent

# 强主张动词 —— evidence 未达 verified 时降级
STRONG_VERBS = {
    "主导": "参与",
    "独立开发": "参与开发",
    "独立搭建": "参与搭建",
    "独立负责": "参与负责",
    "独立设计": "参与设计",
    "牵头": "参与",
    "负责": "参与",
    "首创": "尝试",
    "首次": "初次尝试",
}

PERIOD_JOIN = " – "


def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def md_inline(s):
    """草稿里的 why / evidence_note 是按 markdown 写的（**强调**）。

    先 esc 再转 ** → <b>：只放行加粗一种语法，其余一律当纯文本。
    之前直接 esc 输出，成稿上留下一串裸露的 ** —— 校对稿自己low，说服力就没了。
    """
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))


def clean_val(v):
    """字段值占位符一律不渲染 —— 「待确认（第几发明人）」出现在成稿上是最典型的 low。

    只滤「待确认 / 待补」开头的**字段值**，不过滤 title：
    「（题目待补）」是给草稿看的待办提醒，滤掉它等于把提醒也一起删了。
    """
    v = str(v or "").strip()
    if not v or v.startswith("待确认") or v.startswith("待补"):
        return ""
    return v


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def period_str(p, current=False):
    if not p:
        return ""
    s = p.get("start") or ""
    if current or p.get("current"):
        return f"{s}{PERIOD_JOIN}至今"
    e = p.get("end") or ""
    return f"{s}{PERIOD_JOIN}{e}" if (s or e) else ""


def downgrade(text, evidence, stats=None):
    """证据不足时把强主张动词降级。

    只降级句首动词，但句中残留的强主张词会被记录告警 ——
    因为「半生效」比「不生效」更危险：看起来改过了，实际还留着。
    """
    # self_reported = 本人明确陈述（来自用户给的材料或回答），不是推断，
    # 不降级 —— 否则会把用户自己写的东西改掉，那不是防造假，是篡改。
    if evidence in ("verified", "self_reported"):
        return text
    # 长键优先，避免「独立开发」被「独立」抢先匹配
    for k, v in sorted(STRONG_VERBS.items(), key=lambda x: -len(x[0])):
        if text.startswith(k):
            text = v + text[len(k):]
            break
    return text


def render_bullets(exp, mode, stats, show_ach=None, hide_ach=None):
    """渲染一条经历的成就列表，返回 (html_lines, pending_ids)

    show_ach: 白名单（非 None 时只渲染列表内的）
    hide_ach: 黑名单（渲染时跳过）
    """
    out, pending = [], []
    for a in exp.get("achievements") or []:
        ev = a.get("evidence") or "pending"
        aid = a.get("id", "")

        if show_ach is not None and aid not in show_ach:
            stats.setdefault("cropped", []).append(aid)
            continue
        if hide_ach and aid in hide_ach:
            stats.setdefault("cropped", []).append(aid)
            continue

        if ev in ("unusable", "inferred"):
            stats["dropped"].append((aid, ev))
            continue

        action = downgrade(a.get("action") or "", ev)
        obj = a.get("object") or ""
        method = a.get("method") or ""
        r = a.get("result") or {}
        result = ""
        if isinstance(r, dict):
            # ⚠ 全部经 _s() 转字符串：YAML 里写 `baseline: 3` 是极自然的写法，
            #   直接 .strip() 会抛 AttributeError，用户看到的是一屏 Python 堆栈。
            #   类型容错的成本是零，崩溃的成本是用户放弃。
            metric = _s(r.get("metric"))
            value = _s(r.get("value"))
            # metric 与 value 直接拼接会粘成一坨（「月结对账耗时3 天」）
            result = f"{metric} {value}".strip() if metric else value
            # baseline 只在有结果时才有意义 —— 没有「现在」，就谈不上「原来」。
            # 另外要挡掉占位性空值：填「无」会印出「（原 无）」，比不写更糟。
            #
            # 还要挡掉**重复**：value 写成「3 天 → 1 天」时，baseline 已经是句子的一部分，
            # 再追加「（原 3 天）」就变成「3 天 → 1 天（原 3 天）」——
            # 同一件事说两遍，读起来啰嗦，是「low 感」的直接来源。
            bl = _s(r.get("baseline"))
            if result and bl and bl not in EMPTY_BASELINES and not _baseline_already_shown(value, bl):
                result += f"（原 {bl}）"
            # scope 是限定语，依附于结果存在；单独出现信息量低且句子碎
            # ⚠ 「范围：」是**内部字段名**，与 ✔ / 难点 同类：只在校对稿出现，不进投递稿。
            #   投递稿要的是把它写进句子（如「1965–2025 共 61 年间」），而不是挂一个字段标签。
            sc = _s(r.get("scope"))
            if result and sc and mode == "draft":
                result += f"（范围：{sc}）"
        elif isinstance(r, str):
            result = r

        # 拼句：动作 + 对象 + 方法 + 结果
        # 中英相邻要补空格，否则粘成「自学并应用SQL 取数」
        _cn = bool(action) and not action[-1].isascii()
        _en = bool(obj) and obj[0].isascii() and obj[0].isalnum()
        seg = action + (" " if (_cn and _en) else "") + obj
        if method:
            seg += "，" + method
        if result:
            seg += "，" + result

        # 整句复查：句首动词降级后，句中/宾语里可能还残留强主张词
        if ev not in ("verified", "self_reported"):
            for k in STRONG_VERBS:
                if k in seg:
                    stats.setdefault("residual_strong", []).append((aid, k, seg))

        diff = a.get("difficulty") or ""
        note = a.get("evidence_note") or ""

        # 先转义正文，再拼 HTML 标签 —— 顺序反了会把标签也转义掉
        seg_html = esc(seg)
        if ev == "pending":
            pending.append(aid)
            if mode == "final":
                # 出片模式：默认隐藏无证据条目（宁缺毋滥）
                stats["hidden_pending"].append(aid)
                continue
            seg_html += f'　<span class="pending">【待补：{esc(note or "需补充证据")}】</span>'
        elif ev == "verified" and mode == "draft":
            # ⚠ 与两个兄弟分支对齐：○本人陈述(self_reported) 与【待补】(pending) 都只在
            #   draft 出现，唯独 ✔(verified) 漏了 mode 守卫 —— 证据档位标记被印进投递稿，
            #   雇主看到一颗没有图例的绿勾，不知道它代表「此条可第三方查证」。
            seg_html += '　<span class="ok">✔</span>'
        elif ev == "self_reported" and mode == "draft":
            seg_html += '　<span class="selfrep">○本人陈述</span>'

        html = f"      <li>{seg_html}"
        # ⚠ 同上：「难点：」是字段名不是简历语言。难点的**内容**有价值（抗追问），
        #   正确姿势是改写时织进正文，而不是挂个括号标签 —— 故只在校对稿显示。
        if diff and mode == "draft":
            html += f'<span class="diff">（难点：{esc(diff)}）</span>'
        html += "</li>"
        out.append(html)
    return out, pending


CSS = """
:root{
  --ink:#1a1a1a; --sub:#555; --line:#d8d8d8; --accent:#1f4e79;
  --pending:#b26a00; --pending-bg:#fff7e6; --ok:#1a7f37; --muted:#999;
}
*{box-sizing:border-box}
body{
  margin:0; padding:0; background:#f0f0f0;
  font-family:"PingFang SC","Microsoft YaHei","Hiragino Sans GB",sans-serif;
  color:var(--ink); line-height:1.7; font-size:14px;
}
.page{
  width:210mm; min-height:297mm; margin:20px auto; padding:15mm 18mm;
  background:#fff; box-shadow:0 2px 12px rgba(0,0,0,.12);
}
h1{font-size:26px; margin:0 0 4px; letter-spacing:2px; font-weight:600}
.intent{color:var(--accent); font-size:14px; margin-bottom:6px}
.contact{color:var(--sub); font-size:13px; margin-bottom:16px;
  border-bottom:2px solid var(--accent); padding-bottom:10px}
.contact span{margin-right:14px; white-space:nowrap}
.contact .sep{margin:0 6px; color:#d0d4da}
.contact .empty{color:var(--muted); font-style:italic}
h2{
  font-size:15px; margin:18px 0 8px; padding-left:9px;
  border-left:4px solid var(--accent); font-weight:600; letter-spacing:1px;
}
.item{margin-bottom:13px; page-break-inside:avoid}
/* 超长经历被拆到下一页时的续块：顶掉上边距（它是同一段的延续，不是新段），
   标题压淡一档 —— 让翻页的人一眼看出「还是同一段」，而不是两段同名经历 */
.item-cont{margin-top:0}
.item-cont .item-hd{opacity:.62}
.item-hd{display:flex; justify-content:space-between; align-items:baseline; gap:12px}
.item-org{font-weight:600; font-size:14px}
.item-role{color:var(--accent); font-size:13px; font-weight:500; margin-left:8px}
.item-time{color:var(--sub); font-size:12px; white-space:nowrap}
.item-note{color:var(--muted); font-size:12px; font-style:italic; margin-top:2px}
ul{margin:5px 0 0; padding-left:19px}
li{margin-bottom:3px}
.pending{color:var(--pending); background:var(--pending-bg);
  font-size:12px; padding:1px 5px; border-radius:3px}
.ok{color:var(--ok); font-size:12px}
.selfrep{color:#8a8f98; font-size:11px; font-weight:400}
.ai-detail{color:#5a6270; font-size:12px; font-weight:400}
.diff{color:var(--sub); font-size:12px}
.flag{font-size:11px; color:var(--pending); border:1px dashed var(--pending);
  padding:0 4px; border-radius:3px; margin-left:6px; font-weight:400}
.skill-line{margin-bottom:4px}
.skill-k{font-weight:600; margin-right:6px}
/* 拆行后的次行：缩进到与首行正文对齐（约等于最长分组名 + 冒号） */
.skill-cont{padding-left:6.2em}
.summary{font-size:13px; line-height:1.8; color:#333; margin:0 0 2px}
.edu-line{display:flex; align-items:baseline; gap:10px; font-size:13px; margin-top:2px}
.edu-deg{font-weight:600; min-width:34px}
.edu-major{color:#333}
.edu-line .item-time{margin-left:auto}
.edu-hl{color:var(--sub); font-size:12px}
.gaps{margin-top:22px; padding:12px 14px; background:#fafafa;
  border:1px dashed var(--line); border-radius:4px; page-break-inside:avoid}
.gaps h3{margin:0 0 8px; font-size:13px; color:var(--pending)}
.gaps ul{margin:0; padding-left:18px; font-size:12px; color:var(--sub)}
.empty{color:var(--muted)}
.footer{margin-top:18px; padding-top:8px; border-top:1px solid var(--line);
  font-size:11px; color:var(--muted)}
/* 打印padding必须与屏幕一致（原为 12mm/14mm，导致「预览2页、打印1.5页」）。
   所见即所得是硬要求：篇幅引擎按 15/18mm 算，打印若另用一套就等于白算。 */
@page{size:A4; margin:0}
@media print{
  html,body{margin:0; padding:0; background:#fff}
  .page{margin:0; box-shadow:none; width:210mm; min-height:297mm;
        padding:15mm 18mm; page-break-after:always; break-after:page}
  .page:last-of-type{page-break-after:auto; break-after:auto}
  .src-host{display:none}
  .noprint{display:none}
}
"""

# ---------------------------------------------------------------------------
# 真分页 JS —— 为什么必须有
#
# 单 .page div 装全部内容时，超出一页的部分在屏幕上溢出、在打印时
# 被浏览器硬切成第二页且**丢掉 padding**（内容贴边），更糟的是
# 「1.4 页」这种残页状态：翻过来第二页只有三行，读到的是「没东西可写」。
#
# 浏览器端分页是唯一准确的做法：Python 侧无法测量真实文本布局，
# 用字数估算分配页码必然漂移。故在 DOM 就绪后按实测高度重排到多个 .page。
# ---------------------------------------------------------------------------
PAGINATE_JS = """
(function(){
  function paginate(){
    var MM = 3.779528;               // 1mm = 3.779528px
    var H  = 267 * MM;               // 内容区高 = 297 - 上下 padding 15*2
    var p0 = document.getElementById('page0');
    if(!p0) return;

    // 单块「占高」= 自身高度 + 与下一块之间的有效间距（margin 折叠取较大者）。
    // 关键修复：所有块的高度先**一次性测完**，再开始搬运。旧实现边搬边用
    // getBoundingClientRect 实时测「本块顶→下块顶」，但 appendChild 改变 DOM
    // 会触发重排，使后续测量失真（实测表现为第一页只剩表头、其余全挤到第二页
    // 溢出成 4 页）。先测后搬可彻底规避搬运过程中的实时测量抖动。
    function advOf(el, nextEl){
      var h  = el.getBoundingClientRect().height;
      var cs = getComputedStyle(el);
      var mb = parseFloat(cs.marginBottom) || 0;
      if (nextEl){
        var nm = parseFloat(getComputedStyle(nextEl).marginTop) || 0;
        return h + Math.max(mb, nm);
      }
      return h + mb;
    }
    var kids = Array.prototype.slice.call(p0.children)
                   .filter(function(n){
                     return !(n.classList && n.classList.contains('noprint'));
                   });
    var adv = kids.map(function(n, i){ return advOf(n, kids[i + 1] || null); });
    // 「净高」= 不含尾随 margin 的自身高度，用于判断「这块放不放得下」。
    // 页底最后一块的 margin-bottom 会落进 15mm 的下留白里，不占版面 ——
    // 把它算进预算，等于凭空少给一页 3~13mm。实测一份 260mm 的简历因此被
    // 挤成两页（末页只剩一条教育经历）。断页判定用净高，累加仍用 adv。
    var tight = kids.map(function(n){ return n.getBoundingClientRect().height; });

    function newPage(){
      var d = document.createElement('div');
      d.className = 'page';
      p0.parentNode.appendChild(d);
      return d;
    }

    // ---- 超长经历块内拆分 ----
    // .item 带 page-break-inside:avoid，一整段经历不能被拆开。
    // 一段 200mm 的经历（巴菲特伯克希尔那段）撞上只剩 185mm 的页面时，
    // 只能整块推到下一页 —— 结果首页只放了姓名+摘要，白掉 75% 的版面。
    // 拆法：只搬 <li>，标题留在上半页，续页复制一份标题并标「（续）」。
    // 这是中文简历里处理长经历的通行写法，不产生任何新事实。
    function trySplit(item, budget){
      if (!item.classList || !item.classList.contains('item')) return null;
      var ul = item.querySelector('ul');
      if (!ul) return null;
      var lis = Array.prototype.slice.call(ul.children)
                  .filter(function(n){ return n.tagName === 'LI'; });
      if (lis.length < 4) return null;             // 少于 4 条不值得拆

      function h(el){
        var cs = getComputedStyle(el);
        return el.getBoundingClientRect().height +
               (parseFloat(cs.marginBottom) || 0);
      }
      // 拆分前先量：此刻 li 都还在文档里，量完再搬才准
      var liH = lis.map(h);
      var hd  = item.querySelector('.item-hd');
      var hdH = hd ? h(hd) : 0;
      var cs  = getComputedStyle(item);
      var itemMb = parseFloat(cs.marginBottom) || 0;
      var avail = budget - hdH - itemMb - 6;       // 6px 安全余量

      var acc = 0, k = 0;
      // 至少留 2 条给续页，否则不如不拆（一页挂 1 条比白页更刺眼）
      while (k < lis.length - 2 && acc + liH[k] <= avail) { acc += liH[k]; k++; }
      if (k < 2) return null;

      var cont = document.createElement('div');
      cont.className = 'item item-cont';
      if (hd){
        var c = hd.cloneNode(true);
        var role = c.querySelector('.item-role');
        if (role) role.textContent = (role.textContent || '') + '（续）';
        else c.appendChild(document.createTextNode('（续）'));
        cont.appendChild(c);
      }
      var cul = document.createElement('ul');
      cont.appendChild(cul);
      for (var j = k; j < lis.length; j++) cul.appendChild(lis[j]);
      return cont;
    }

    var cur = p0, used = 0, moved = 0;
    for (var i = 0; i < kids.length; i++) {
      var n  = kids[i], eh = adv[i];

      if (used + tight[i] > H && used > 0) {
        // 本页剩得下「半个块」才拆；剩得太少（<35%）拆了也是碎渣
        var budget = H - used;
        var cont = (budget > 0.35 * H && eh > 0.5 * H) ? trySplit(n, budget) : null;
        if (cont) {
          cur.appendChild(n);
          used = used + advOf(n, null);
          cur = newPage(); used = 0; moved++;
          cur.appendChild(cont);
          used = advOf(cont, null);
          continue;
        }
        var prev = cur;
        cur = newPage(); used = 0; moved++;
        // 孤儿标题：上一页最后一个节点是 H2 时，把它一起搬过来 ——
        // 段标题孤零零留在页底，比换页本身更刺眼。
        var last = prev.lastElementChild;
        if (last && last.tagName === 'H2') {
          used = advOf(last, n); cur.appendChild(last);
        }
        // 单个块高于整页（超长 item）：不拆，直接放，交由 page-break-inside 处理
      }
      cur.appendChild(n);            // appendChild 会移动节点，首页内为 no-op
      used += eh;
    }

    // ---- 残页均衡 ----
    // 末页过短（<45%）时，从上一页回拉若干块，直到末页够看或上一页开始塌陷。
    // 宁可两页都半满，也不要「一页满 + 一页只有两行」：翻到最后一页只剩两行，
    // 读出来的是「他没东西可写了」，比换页本身更伤。
    // 注意此刻已搬完，DOM 稳定，逐块移动后实时测量是准确的（与贪心阶段不同）。
    // 末页目标 55%（measure_pages 的残页线），上一页底线 45%：
    // 两个阈值不能取同一个值，否则「两页都 ≥55%」在内容不够时永远不成立，
    // 均衡会直接停在起始状态。末页优先，上一页只要不塌就行。
    var LAST_MIN   = 0.55;
    var PREV_FLOOR = 0.45;
    var pages = Array.prototype.slice.call(
                    p0.parentNode.querySelectorAll('.page'))
                    .filter(function(p){ return p.children.length; });
    // ⚠ 必须是 >= 2，不是 >= 3。两页简历恰恰是残页最刺眼的形态：
    // 「第 1 页满 + 第 2 页只有两行」读出来就是「他没东西可写了」。
    // 旧实现写 >= 3 是为了躲开 lastP===prevP 的下标越界，
    // 但 pages[length-2] 在 length>=2 时完全合法 —— 等于为一个不存在的问题
    // 放弃了最高频的场景。1 页时 length-2 = -1，才真的会拿到 undefined，
    // 所以下界就是 2。
    if (pages.length >= 2) {
      function contentH(p){
        var ks = Array.prototype.slice.call(p.children).filter(function(n){
          return !(n.classList && n.classList.contains('noprint'));
        });
        if (!ks.length) return 0;
        var top = ks[0].getBoundingClientRect().top, bot = -Infinity;
        ks.forEach(function(el){
          var r = el.getBoundingClientRect();
          if (r.bottom > bot) bot = r.bottom;
        });
        return bot - top;
      }
      function blockH(el){
        var cs = getComputedStyle(el);
        return el.getBoundingClientRect().height +
               (parseFloat(cs.marginBottom) || 0);
      }
      var lastP = pages[pages.length - 1], prevP = pages[pages.length - 2];
      var guard = 0;
      while (contentH(lastP) < LAST_MIN * H &&
             prevP.children.length > 1 && guard++ < 40) {
        var blk = prevP.lastElementChild;
        if (!blk) break;
        // 上一页再拉就塌了，停手 —— 均衡不是把上一页掏空
        if (contentH(prevP) - blockH(blk) < PREV_FLOOR * H) break;
        lastP.insertBefore(blk, lastP.firstElementChild);
      }
    }

    // ---- 打印安全兜底（防「硬切空页」+ 防「半空页」）----
    // ① 防硬切：上面的贪心断页用「净高」(tight) 判断放不放得下，允许页面内容比
    //    内容区高一点点（尾块 margin-bottom 不参与判断）。屏幕上看不出来，但只要
    //    .page 超过 A4(297mm)，打印时 Chromium 就硬切一刀 —— 溢出的内容掉到一张
    //    **没有 padding** 的空页上（实测：王五 J6 校对稿的第 2 页只有 4% 填充、
    //    正文贴纸边 1mm 处）。这里改用「整页真实内容高」复核：超了就把尾部整块
    //    （连同会被孤立的段标题）顺延到下一页，保证打印不出现硬切空页。
    // ② 防半空：① 顺延后或均衡后仍可能出现「只有两三行」的页（同样刺眼）。做一轮
    //    回填：某页内容不足 45% 时，从下一页顶部把整块拉回来，直到够看或会溢出。
    (function printSafety(){
      var A4      = 297 * MM;                        // 纸张高（px）：.page 超过它就会被硬切
      var CONTENT = (297 - 30) * MM;                 // 内容区高 = A4 - 上下 padding(15mm*2)
      var FLOOR   = 0.45 * H;                        // 低于此视为「半空页」
      function kids(p){
        return Array.prototype.slice.call(p.children).filter(function(n){
          return !(n.classList && n.classList.contains('noprint'));
        });
      }
      function blockH(el){
        var cs = getComputedStyle(el);
        return el.getBoundingClientRect().height + (parseFloat(cs.marginBottom) || 0);
      }
      function contentH(p){
        var ks = kids(p);
        if (!ks.length) return 0;
        var top = ks[0].getBoundingClientRect().top, bot = -Infinity;
        ks.forEach(function(el){
          var r = el.getBoundingClientRect();
          if (r.bottom > bot) bot = r.bottom;
        });
        return bot - top;
      }
      // 这一页打印出来会有多高（= 上下 padding + 首块上边距 + 内容跨度 + 末块下边距）。
      // 关键：末块 margin-bottom 不会与父级 padding 折叠，会实打实把 .page 撑高 ——
      // 这就是「屏幕 263mm / 打印 298mm」那 3.4mm 的来源，也是硬切的真凶。
      function pageH(p){
        var ks = kids(p);
        if (!ks.length) return 0;
        var cs = getComputedStyle(p);
        var padT = parseFloat(cs.paddingTop) || 0;
        var padB = parseFloat(cs.paddingBottom) || 0;
        var firstMt = parseFloat(getComputedStyle(ks[0]).marginTop) || 0;
        var lastMb  = parseFloat(getComputedStyle(ks[ks.length - 1]).marginBottom) || 0;
        return padT + firstMt + contentH(p) + lastMb + padB;
      }
      function allPages(){
        return Array.prototype.slice.call(p0.parentNode.querySelectorAll('.page'))
                 .filter(function(p){ return p.children.length; });
      }
      function nextOf(p){
        var ps = allPages(), i = ps.indexOf(p);
        var nxt = ps[i + 1];
        if (!nxt) {
          nxt = document.createElement('div'); nxt.className = 'page';
          p.parentNode.insertBefore(nxt, p.nextSibling);
        }
        return nxt;
      }
      // 尾部整块顺延到下一页；顺延后若本页以段标题(H2)结尾，标题也一起走（防孤标题）
      function pushLast(p){
        var ks = kids(p);
        if (ks.length <= 1) return false;            // 只剩一块：单块即超一页，交由打印自行处理
        var nxt = nextOf(p);
        nxt.insertBefore(ks[ks.length - 1], nxt.firstElementChild);
        var hop = 0;
        while (hop++ < 8) {
          if (kids(p).length <= 1) break;
          if (p.lastElementChild && p.lastElementChild.tagName === 'H2')
            nxt.insertBefore(p.lastElementChild, nxt.firstElementChild);
          else break;
        }
        return true;
      }
      // ⓪ 去掉「无效留白」：每页最后一块的 margin-bottom 后面紧跟的就是 15mm 下
      //    padding，再留 3~13mm 段间距纯属浪费，还会把整页顶到 A4 之外
      //    （实测：263mm 内容的页因此变成 298.4mm → 打印时被硬切出一张空页）。
      function zeroTail(){
        Array.prototype.slice.call(p0.parentNode.querySelectorAll('.page')).forEach(function(p){
          var ks = kids(p);
          if (ks.length) ks[ks.length - 1].style.marginBottom = '0';
        });
      }

      // ① 防硬切
      var g1 = 0;
      while (g1++ < 100) {
        zeroTail();
        var ps = allPages(), bad = -1;
        for (var i = 0; i < ps.length; i++) {
          if (pageH(ps[i]) > A4 + 1) { bad = i; break; }
        }
        if (bad < 0) break;
        if (!pushLast(ps[bad])) break;
      }
      zeroTail();
      // ② 半空页回填（保守：只回填、不掏空下一页、不制造孤标题）
      var g2 = 0;
      while (g2++ < 100) {
        var ps2 = allPages(), did = false;
        for (var j = 0; j < ps2.length - 1; j++) {
          if (contentH(ps2[j]) >= FLOOR) continue;
          var nk = kids(ps2[j + 1]);
          if (nk.length <= 1) continue;              // 下一页只剩一块，拉走会掏空它
          var blk = nk[0];
          if (blk.tagName === 'H2') continue;        // 不把段标题拉到上页页底（孤标题）
          if (pageH(ps2[j]) + blockH(blk) > A4) continue;           // 拉回来会溢出
          ps2[j].appendChild(blk);
          did = true;
          break;
        }
        if (!did) break;
      }
      // 清掉可能出现的空页（避免打印出一张全白页）
      Array.prototype.slice.call(p0.parentNode.querySelectorAll('.page')).forEach(function(p){
        if (!p.children.length) p.parentNode.removeChild(p);
      });
    })();

    // 首页若被搬空（极端情况），移除空页
    if (moved && !p0.children.length) p0.parentNode.removeChild(p0);
  }
  // 等布局稳定（含字体/图片加载）后再分页，避免用草稿态高度分页导致溢出。
  if (document.readyState === 'complete') paginate();
  else window.addEventListener('load', paginate);
})();
"""


# ---------------------------------------------------------------------------
# 人群画像（写什么）与包装级别（怎么写）
# 两者正交，且都**不能解锁 evidence 限制** —— 包装只调表达，不产生事实
#   skill:      all=全部列出 / converge=收敛 / none=不列技能段（能力写进经历）
#   student:    keep=保留校园内容 / top=只留高含金量 / drop=全部删除
#   require_evidence: 无项目佐证的技能默认隐藏（社招技能堆叠是负分项）
# ---------------------------------------------------------------------------
PROFILES = {
    "campus": {"label": "校招", "edu_first": True, "student": "keep",
               "skill": "all", "skill_cap": 0, "require_evidence": False},
    "junior": {"label": "初级", "edu_first": False, "student": "top",
               "skill": "converge", "skill_cap": 14, "require_evidence": False},
    "experienced": {"label": "社招", "edu_first": False, "student": "drop",
                    "skill": "converge", "skill_cap": 10, "require_evidence": True},
    # 资深画像**也要列技能**（v12 改）。原设定是「不列技能清单，能力写进经历」，
    # 实测在中文招聘环境不成立：初筛靠 ATS 关键词 + HR 按条款勾选，
    # 一位 15 年架构师的成稿在 JD 的 9 个技术名词里只命中 1 个。
    # 而且「能力写进经历」与资深人群的工作性质结构性互斥 ——
    # 越资深，做的事越难压进一条 bullet。改为严格收敛：只留有佐证的核心能力。
    "expert": {"label": "资深", "edu_first": False, "student": "drop",
               "skill": "converge", "skill_cap": 6, "require_evidence": True},
}
POLISH_LEVELS = {"sincere": "真诚", "balanced": "适度包装", "bold": "酥化"}

# ---------------------------------------------------------------------------
# v10「low 感」门控 —— 详见 references/rewrite-rules.md「『low 感』禁用清单」
# 这几条不改事实，只改观感；但它们必须进脚本，靠提示词约束会在第 N 次改写时被忘掉。
# ---------------------------------------------------------------------------

# ① 熟练度自评（了解 / 熟悉 / 精通）不出现在成稿里：
#    - 自评不可查证，写「精通」等于邀请对方追问到崩
#    - 「熟悉」在 HR 的默认读法里 ≈ 不精 —— 越描越黑
#    - 区分度来自交付物，不是自我打分
#    level 字段仍保留在母版里，只用于内部收敛决策（「了解」级优先归档）。
SHOW_SKILL_LEVEL = False

# ② 技能分组顺序：按能力域（做什么），不按技术类型（是什么）。
#    旧分类（编程语言 / AI 框架 / 人工智能 / 工具与环境）读起来是零件清单，
#    且「AI 框架」与「人工智能」互相打架 —— 这是「分类杂乱」的根因。
#
#    ⚠ 这里只能放**跨行业通用**的能力域。原表里的「智能交通与仿真」是
#    第一个用户的职业身份，硬编码进引擎后，会计 / 销售 / 架构师的分类
#    会全部掉到末尾 —— 等于把一个人的简历结构强加给所有人。
#    行业特定的分类由母版用 preferences.category_order 自己声明。
CATEGORY_ORDER = ["算法与建模", "工程与交付", "数据与工具",
                  "管理与协作", "AI 原生工作流", "本地模型与生成"]

# ④ AI 能力组一行最多放几条。超过就拆行 —— 每条都是完整句子，不是单词，
#    挤在一起读起来是一坨，比技能堆叠还糟。
AI_LINE_MAX = 2

# ③ 荣誉段门控：剩下的全是 relevance: low 就整段不出现。
#    一条「优秀团员」挂在简历上不是加分，是告诉对方「我没有更硬的东西可写」。
HONOR_MIN_RELEVANCE = True

# baseline 的占位性空值：填了等于没填，印出来是「（原 无）」这种事故
EMPTY_BASELINES = {"", "无", "无记录", "未记录", "未知", "不详", "-", "--",
                   "N/A", "n/a", "NA", "无 baseline"}

# ⑤ 技能段保底条数。删掉商品化能力后若少于此数，把有佐证的放回来。
#    「装个工具就能获得 = 无区分度」这条规则隐含一个前提：
#    候选人有比它更硬的东西可放。入门岗 / 转行者没有。
COMMODITY_FLOOR = 3


# 经历类型分档：正式工作在前，其余在后。
# 纯时间倒序会让「2024 年帮亲属做的兼职」压过「2020 年至今的正式工作」，
# HR 翻开简历第一眼看到的是困惑而不是资历。
EXP_RANK = {"work": 3, "internship": 2, "project": 1, "opensource": 1, "award": 0}


def _sort_experiences(exps):
    """两级排序：先类型分档，档内时间倒序。

    用两次稳定排序而不是复合键 —— 复合键里一个升一个降，
    只能靠 negate 字符串（做不到）或反转后回翻（易错）。
    """
    by_time = sorted(exps,
                     key=lambda x: (x.get("period") or {}).get("start", "") or "",
                     reverse=True)
    return sorted(by_time,
                  key=lambda x: -EXP_RANK.get(str(x.get("type") or "work").lower(), 1))


def _s(v):
    """字段值转字符串 —— result / object / method 等字段用户常填数字。

    一个 `baseline: 3` 引发的 AttributeError 会让整份简历渲染失败，
    用户看到的是 Python 堆栈而不是简历。这类容错不产生任何语义损失。
    """
    if v is None:
        return ""
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _baseline_already_shown(value, baseline):
    """value 里是否已经写出了 baseline。

    覆盖三种常见写法：
      「3 天 → 1 天」      —— 箭头左边就是原值
      「从 1 周缩短至 3 天」—— 「从 X …」句式
      「由 800 万增长到 1200 万」
    判断基准用**去空格后的子串匹配**：中英混排时空格位置不稳定，
    而宁可漏判（多一个「（原 X）」）也不能误判（把该有的对比吃掉）。
    """
    if not value or not baseline:
        return False
    v = re.sub(r"\s+", "", str(value))
    b = re.sub(r"\s+", "", str(baseline))
    if not v or not b:
        return False
    if b in v:
        return True
    # 「从 X 到 Y」「由 X 增长至 Y」：X 出现且句子里有转换标记
    markers = ("→", "->", "至", "到", "降", "升", "增长", "缩短", "提升", "减少")
    return b in v or (any(m in v for m in markers) and b in v)


def _pick(data, target, key, table, default):
    """定制版可覆盖母版设置；取值非法时静默回落到默认（不因配置错误中断出片）"""
    v = ((target or {}).get(key) or (data.get("preferences") or {}).get(key) or default)
    return v if v in table else default


def build_html(data, mode="draft", target=None):
    stats = {"dropped": [], "hidden_pending": [], "pending": [], "unbacked": [],
             "honors_dropped": []}
    o = data.get("owner") or {}
    c = o.get("contact") or {}
    tg = data.get("targeting") or {}
    profile = _pick(data, target, "profile", PROFILES, "experienced")
    polish = _pick(data, target, "polish", POLISH_LEVELS, "balanced")
    pr = PROFILES[profile]

    S = {}

    def sec(name):
        return S.setdefault(name, [])

    L = []
    L.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
    L.append("<title>简历</title>")
    L.append(f"<style>{CSS}</style></head><body><div class='page' id='page0'>")

    # ---- 抬头 ----
    name = o.get("name") or ""
    L.append(f"<h1>{esc(name) if name else '<span class=\"empty\">（姓名待填）</span>'}</h1>")

    # 求职意向默认不写 —— 招聘系统里已有投递岗位，简历里再写既占首屏黄金位置，
    # 又暗示"海投 / 没想好"。目标岗位的正确载体是文件名 + 投递语。
    # 仅内部转岗、猎头推荐等确实需要时显式开启 show_intention。
    if (target or {}).get("show_intention") or (data.get("preferences") or {}).get("show_intention"):
        intent = tg.get("direction") or ""
        tgt_role = ((target or {}).get("target") or {}).get("role") or ""
        tgt_company = ((target or {}).get("target") or {}).get("company") or ""
        if tgt_role:
            intent = tgt_role + (f" · {tgt_company}" if tgt_company else "")
        if intent:
            L.append(f'<div class="intent">求职意向：{esc(intent)}</div>')

    parts = []
    for key, label in [("phone", "电话"), ("email", "邮箱")]:
        v = c.get(key)
        parts.append(f"<span>{esc(v)}</span>" if v else f'<span class="empty">{label}待填</span>')
    city = c.get("city")
    district = c.get("district")
    if city:
        loc = city + (f" · {district}" if district else "")
        parts.append(f"<span>现居：{esc(loc)}</span>")
    links = c.get("links") or []
    for lk in links:
        # 模板里 links 是 {label, url}，早期母版也有直接写字符串的 —— 两种都接住。
        # 不判类型会把 dict 原样印到抬头，成稿上出现 {'label': 'GitHub'} 这种事故。
        if isinstance(lk, dict):
            lb, url = lk.get("label") or "", lk.get("url") or ""
            parts.append(f"<span>{esc(lb)}：{esc(url)}</span>" if url
                         else f"<span>{esc(lb)}</span>")
        else:
            parts.append(f"<span>{esc(lk)}</span>")
    L.append('<div class="contact">' + '<span class="sep">|</span>'.join(parts) + "</div>")

    # ---- 摘要（个人简述）----
    # 社招简历最有效的「去 low」手段：首屏三行告诉对方你是谁、能交付什么。
    # 默认关闭（show_summary），因为摘要是**唯一会新增概括性表述**的段落 ——
    # 它必须由本人确认后才能开启，母版不能替用户做定位表态。
    sm = data.get("summary") or {}
    sm_enabled = (target or {}).get("show_summary", sm.get("enabled", False))
    sm_text = ((target or {}).get("summary_text") or sm.get("text") or "").strip()
    if sm_enabled and sm_text:
        L.append(f'<div class="summary">{esc(sm_text)}</div>')
    elif sm_text and mode == "draft":
        L.append('<div class="item-note noprint">ⓘ 母版里已有摘要候选，'
                 '确认无误后把 summary.enabled 改为 true 即出现在成稿</div>')

    # ---- 教育经历 ----
    edu = data.get("education") or []
    if edu:
        E = sec("edu")
        E.append("<h2>教育背景</h2>")
        # 同一所学校拆成两个块（本硕各一块）会让版面显得碎，且读不出「7 年在同一所学校」。
        # 合并成一个块、学位各占一行 —— 事实一条没变，观感完全不同。
        merged = {}
        for e in sorted(edu, key=lambda x: (x.get("period") or {}).get("start", ""), reverse=True):
            merged.setdefault(e.get("school", ""), []).append(e)
        for school, items in merged.items():
            E.append('<div class="item"><div class="item-hd">')
            # 同工作经历：时间已填就不报「待确认」，且只在草稿出现
            _has_t = all(bool((x.get("period") or {}).get("start")) for x in items)
            flag = "" if (_has_t or mode == "final") else \
                '<span class="flag noprint">时间待确认</span>'
            E.append(f'<div><span class="item-org">{esc(school)}</span>{flag}</div>')
            # items 已按开始时间倒序：[-1] 最早，[0] 最晚
            first = (items[-1].get("period") or {}).get("start", "")
            last = (items[0].get("period") or {}).get("end", "") or "至今"
            E.append(f'<div class="item-time">{esc(first)}{PERIOD_JOIN}{esc(last)}'
                     f'</div></div>')
            for e in items:
                # 只有一个学位时，头部已显示过起止时间，此处再显示一遍是冗余
                p = period_str(e.get("period")) if len(items) > 1 else ""
                E.append('<div class="edu-line">'
                         f'<span class="edu-deg">{esc(e.get("degree",""))}</span>'
                         f'<span class="edu-major">{esc(e.get("major",""))}</span>'
                         f'<span class="item-time">{esc(p)}</span></div>')
                hl = e.get("highlights") or []
                for h in hl:
                    E.append(f'<div class="edu-line edu-hl">{esc(h)}</div>')
            E.append("</div>")

    # ---- 工作经历 ----
    exps = data.get("experiences") or []

    # ---- 定制版筛选 ----
    # selection.experiences      白名单 + 顺序（只显示列出的，按给定顺序）
    # selection.hidden_experiences 黑名单（显示其余，按时间倒序）
    # selection.achievements     成就白名单（裁剪单条 bullet）
    # selection.hidden_achievements 成就黑名单
    # selection.hidden_skills    技能黑名单（按 id 或 name）
    order = None
    show_ach = None
    hide_ach = set()
    hidden_skills = set()
    hidden_pubs = set()
    hidden_pats = set()
    hidden_hons = set()
    hidden_ai = set()
    hidden_os = set()
    honor_force = False
    if target:
        sel = target.get("selection") or {}
        ids = sel.get("experiences") or sel.get("entry_ids")
        hid_exp = set(sel.get("hidden_experiences") or [])
        if ids:
            idx_all = {e.get("id"): e for e in exps}
            exps = [idx_all[i] for i in ids if i in idx_all]
            order = ids
        # 黑名单在白名单之后生效：先按白名单定范围与顺序，再剔除隐藏项。
        # 文档语义是「白名单优先、黑名单兜底」；原 elif 写法使二者互斥、黑名单静默失效。
        if hid_exp:
            exps = [e for e in exps if e.get("id") not in hid_exp]
        show_ach = set(sel.get("achievements") or []) or None
        hide_ach = set(sel.get("hidden_achievements") or [])
        hidden_skills = set(sel.get("hidden_skills") or [])
        hidden_pubs = set(sel.get("hidden_publications") or [])
        hidden_pats = set(sel.get("hidden_patents") or [])
        hidden_hons = set(sel.get("hidden_honors") or [])
        hidden_ai = set(sel.get("hidden_ai") or [])
        hidden_os = set(sel.get("hidden_opensource") or [])
        honor_force = bool(sel.get("force_honors"))

    if exps:
        X = sec("exp")
        X.append("<h2>工作经历</h2>")
        # 定制版显式指定顺序时必须尊重它 —— 之前无条件按时间重排，等于定制顺序失效
        #
        # 默认排序：先按类型分档（正式工作 > 实习 > 项目/开源），档内按时间倒序。
        # 纯时间倒序会把「2024 年帮亲属做的兼职」排到「2020 年至今的正式工作」前面 ——
        # HR 看到简历第一项是个淘宝店，第一反应是困惑，不是欣赏。
        seq = exps if order else _sort_experiences(exps)
        for e in seq:
            p = period_str(e.get("period"), e.get("period", {}).get("current"))
            title = e.get("title") or ""
            title_cls = "item-role" if "待补" not in title else "item-role empty"
            # 「时间待确认」：只在时间**真的残缺**时提示，且只出现在校对稿。
            # 旧逻辑靠 period_confirmed 字段 —— 而这个字段模板里从未定义过，
            # 于是除了手写过它的人，所有人的成稿都顶着一枚橙色徽章，还会被打印出来。
            _pd = e.get("period") or {}
            _has_time = bool(_pd.get("start")) and bool(_pd.get("end") or _pd.get("current"))
            tflag = "" if (_has_time or mode == "final") else \
                '<span class="flag noprint">时间待确认</span>'
            X.append('<div class="item"><div class="item-hd">')
            X.append(f'<div><span class="item-org">{esc(e.get("org",""))}</span>'
                     f'<span class="{title_cls}">{esc(title)}</span>{tflag}</div>')
            X.append(f'<div class="item-time">{esc(p)}</div></div>')

            bullets, pend = render_bullets(e, mode, stats, show_ach, hide_ach)
            stats["pending"].extend(pend)
            if bullets:
                X.append("<ul>")
                X.extend(bullets)
                X.append("</ul>")
            else:
                hint = "（成就待采集）" if not (e.get("achievements") or []) else \
                       "（现有条目证据不足，出片已隐藏 —— 补齐证据后会显示）"
                X.append(f'<div class="item-note">{hint}</div>')
            X.append("</div>")

    # ---- 技能 ----
    # schema: {name, category, level, evidence_refs, status, keep}
    # 社招画像下技能堆叠是负分项：只留有项目佐证的，且不超过 skill_cap
    sk = data.get("skills") or []
    sk = [s for s in sk if (s.get("status") or "active") != "archived"]
    # v9 范式：commodity（装个工具 / 问一句 AI 就能获得的能力）默认不单列。
    # 它是真的，但没有区分度 —— 写了等于占版面，还会让整段被读成「凑数」。
    # 正确位置是交付物 bullet 的 tech_tags。JD 点名时用 keep: true 强制出现。
    def _is_cmd(s):
        return (s.get("kind") or "capability") == "commodity"

    stats["commodity"] = [s.get("name", "?") for s in sk if _is_cmd(s) and not s.get("keep")]
    # 有项目佐证的商品化能力 —— 删空时的回补池
    cmd_back = [s for s in sk
                if _is_cmd(s) and not s.get("keep") and (s.get("evidence_refs") or [])]
    sk = [s for s in sk if not _is_cmd(s) or s.get("keep")]

    # ---- 兜底：绝不能把技能段删空 ----
    # 「商品化能力不单列」隐含的前提是「候选人有比它更硬的东西可放」。
    # 入门岗 / 转行者没有 —— 实测一位大专转行者的 SQL、Excel、PowerBI 被全部删掉，
    # 而她投的 JD 原文写着「必须掌握 SQL 取数」。执行结果不是精练，是自废武功。
    if len(sk) < COMMODITY_FLOOR and cmd_back:
        back = cmd_back[:COMMODITY_FLOOR - len(sk)]
        sk.extend(back)
        stats["commodity_restored"] = [s.get("name", "?") for s in back]
    if hidden_skills:
        sk = [s for s in sk
              if s.get("id") not in hidden_skills and s.get("name") not in hidden_skills]
    if pr["require_evidence"]:
        kept, unbacked = [], []
        for s in sk:
            (kept if ((s.get("evidence_refs") or []) or s.get("keep")) else unbacked).append(s)
        stats["unbacked"] = unbacked
        sk = kept
    # ---- AI 原生能力：先筛选，再作为「专业技能」的分组并入 ----
    # v10：不再单独开段。理由有二 ——
    #   ① 单独开段等于在简历上宣告「我的 AI 能力和专业能力是两回事」
    #   ② 多出一个只有三行的碎段落，版面观感更碎、更像凑数
    # 它本来就是专业技能的一类，写进同一段、占一个能力域分组即可。
    ai_groups = {}
    for a in data.get("ai_native") or []:
        ev = a.get("evidence") or "pending"
        if a.get("id") in hidden_ai:
            stats.setdefault("cropped", []).append(a.get("id", "?"))
            continue
        if ev in ("unusable", "inferred"):
            stats["dropped"].append((a.get("id", "?"), ev))
            continue
        if ev == "pending" and mode == "final":
            stats["hidden_pending"].append(a.get("id", "?"))
            continue
        cap = esc(a.get("capability", ""))
        det = esc(a.get("detail") or "")
        # 主句是能力，工具名只作附注 —— 用「：」而非括号，避免双层括号
        seg = f"{cap}：{det}" if det else cap
        if ev == "pending":
            seg += '　<span class="pending">【待补】</span>'
        elif ev == "self_reported" and mode == "draft":
            seg += '　<span class="selfrep">○本人陈述</span>'
        ai_groups.setdefault(a.get("group") or "AI 原生能力", []).append(seg)

    if pr["skill"] != "none":
        K = sec("skill")
        K.append("<h2>专业技能</h2>")
        if pr["skill_cap"] and len(sk) > pr["skill_cap"]:
            stats["skill_over"] = (len(sk), pr["skill_cap"])
            if mode == "draft":
                K.append(f'<div class="item-note noprint">⚠ 技能 {len(sk)} 项，'
                         f'超过{pr["label"]}画像建议上限 {pr["skill_cap"]} 项 —— '
                         f'技能堆叠会让 HR 读成「泛而不精」，建议收敛</div>')

        groups = {}
        for s in sk:
            nm = esc(s.get("name", ""))
            stk = esc(s.get("stack") or "")
            # 工具名降级为注脚 —— 与 ai_native 同一条铁律：主句是能力
            seg = f"{nm}（{stk}）" if stk else nm
            if SHOW_SKILL_LEVEL and s.get("level"):
                seg += f"（{esc(s['level'])}）"
            groups.setdefault(s.get("category") or "其他", []).append((seg, s))

        # 母版可声明自己的分类顺序（行业特定分类必须走这条路）
        cat_order = ((data.get("preferences") or {}).get("category_order")
                     or CATEGORY_ORDER)

        def _cat_key(c):
            return (cat_order.index(c) if c in cat_order else len(cat_order), c)

        cats = sorted(set(list(groups) + list(ai_groups)), key=_cat_key)
        for cat in cats:
            if cat in groups:
                # 无佐证的排到本组末尾，标签只标一次，插在首个无佐证项之前
                items = sorted(groups[cat],
                               key=lambda x: (not (x[1].get("evidence_refs") or []), x[0]))
                segs = [x[0] for x in items]
                tag_at = next((i for i, x in enumerate(items)
                               if not (x[1].get("evidence_refs") or [])), None)
                if mode == "draft" and tag_at is not None:
                    head = "、".join(segs[:tag_at]) + "、" if tag_at else ""
                    body = head + '<span class="selfrep">○无项目佐证：</span>' + "、".join(segs[tag_at:])
                else:
                    body = "、".join(segs)
                K.append(f'<div class="skill-line"><span class="skill-k">{esc(cat)}：</span>{body}</div>')
            else:
                # AI 原生分组：每条是「能力：工具」的完整陈述，不是单词。
                # 三条以上挤成一行会糊成一坨（比堆叠还难读）—— 改为一行一条，
                # 分组名只在首行标一次，次行起缩进对齐。
                head = f'<span class="skill-k">{esc(cat)}：</span>'
                segs = ai_groups[cat]
                if len(segs) <= AI_LINE_MAX:
                    K.append(f'<div class="skill-line">{head}{"；".join(segs)}</div>')
                else:
                    K.append(f'<div class="skill-line">{head}{segs[0]}</div>')
                    for seg in segs[1:]:
                        K.append(f'<div class="skill-line skill-cont">{seg}</div>')

        if not cats:
            K.append('<div class="item-note">（技能清单未录入 —— 缺它无法做任何岗位匹配）</div>')

    # ---- 论文 / 专利 / 荣誉 / 证书 ----
    # 与成就同一套证据规则：unusable/inferred 拦截，pending 在出片模式隐藏
    def render_evidence_block(out, title, rows, fmt, hidden=None):
        if not rows:
            return
        shown = []
        for p in rows:
            ev = p.get("evidence") or "pending"
            pid = p.get("id", "?")
            if hidden and (pid in hidden or p.get("title") in hidden or p.get("name") in hidden):
                stats.setdefault("cropped", []).append(pid)
                continue
            if ev in ("unusable", "inferred"):
                stats["dropped"].append((pid, ev))
                continue
            if ev == "pending" and mode == "final":
                stats["hidden_pending"].append(pid)
                continue
            shown.append((p, ev))
        if not shown:
            return
        out.append(f"<h2>{title}</h2>")
        for p, ev in shown:
            line = esc(fmt(p))
            if ev == "pending":
                line += f'　<span class="pending">【待补：{esc(p.get("evidence_note") or "需补充信息")}】</span>'
            elif ev == "verified" and mode == "draft":
                line += '　<span class="ok">✔</span>'
            elif ev == "self_reported" and mode == "draft":
                line += '　<span class="selfrep">○本人陈述</span>'
            out.append(f'<div class="skill-line">{line}</div>')

    def _pub_fmt(p):
        src, lvl = clean_val(p.get("venue")), clean_val(p.get("venue_level"))
        venue = f"{src}（{lvl}）" if src and lvl else (src or lvl)
        tail = "，".join(b for b in (venue, clean_val(p.get("authorship")),
                                    clean_val(p.get("status"))) if b)
        return f'{p.get("title","")}' + (f'　—　{tail}' if tail else "")

    def _pat_fmt(p):
        tail = "，".join(b for b in (clean_val(p.get("type")), clean_val(p.get("status"))) if b)
        role = clean_val(p.get("role"))
        if role:
            tail = f'{tail}，发明人位次：{role}' if tail else f'发明人位次：{role}'
        return f'{p.get("title","")}' + (f'　—　{tail}' if tail else "")

    render_evidence_block(
        sec("pub"), "论文成果", data.get("publications") or [], _pub_fmt, hidden_pubs)

    render_evidence_block(
        sec("pat"), "专利", data.get("patents") or [], _pat_fmt, hidden_pats)

    def _os_fmt(p):
        bits = [p.get("title", "")]
        tail = "，".join(b for b in (clean_val(p.get("repo")),
                                      clean_val(p.get("desc"))) if b)
        if tail:
            bits.append(f"　—　{tail}")
        return "".join(bits)

    render_evidence_block(
        sec("os"), "开源与技术影响力", data.get("opensource") or [], _os_fmt, hidden_os)

    # 校园内容按画像过滤 —— 社招写「三好学生」不是假，是稀释信号
    hons = data.get("honors") or []
    if pr["student"] == "drop":
        hons = [h for h in hons if not h.get("student_era")]
    elif pr["student"] == "top":
        hons = [h for h in hons if not h.get("student_era") or h.get("high_value")]

    # ---- 荣誉段门控：没有硬通货就整段不出现 ----
    # 「优秀团员」「积极参与活动」这类无竞争性荣誉上简历不是加分 ——
    # 它传递的信号是「我把能找到的都写上了」。宁可没有这一段。
    # 硬通货 = 有竞争性 / 有第三方背书的：竞赛名次、政府或行业奖、奖学金级别、
    #         以及本就另有段落承载的专利与论文。
    if hons and HONOR_MIN_RELEVANCE:
        # force: true = 本人显式要求保留（如投国企/体制内，这类荣誉确为正信号）
        # 定制版可用 force_honors: true 整体开启 —— 安稳岗里「优秀团员」是「听话、稳定」的正信号
        force_all = bool(honor_force)
        solid = [h for h in hons
                 if force_all or (h.get("relevance") or "normal") != "low" or h.get("force")]
        if not solid:
            stats["honors_dropped"] = [h.get("name", "?") for h in hons]
            if mode == "draft":
                sec("hon").append(
                    '<div class="item-note noprint">ⓘ 荣誉段已整体隐藏：剩下的全是低价值条目'
                    f'（{"、".join(stats["honors_dropped"])}）—— '
                    '与其挂一条「优秀团员」，不如不放这一段</div>')
            hons = []

    render_evidence_block(
        sec("hon"), "荣誉奖励", hons,
        lambda p: f'{p.get("name","")}（{p.get("period","")}）',
        hidden_hons)

    def _cert_fmt(p):
        bits = [p.get("name", "")]
        tail = "，".join(b for b in (clean_val(p.get("issuer")), clean_val(p.get("date"))) if b)
        if tail:
            bits.append(f'　—　{tail}')
        return "".join(bits)

    # ---- 证书段弱信号提示（只提示，不拦截）----
    # 证书是可查证的事实，比自评硬，所以不像荣誉那样整段门控。
    # 但如果整段只剩 CET-4/6、计算机等级这类「人人都有」的通用证书，
    # 对硕士 + 工作 5 年的人是反向信号 —— 学历本身已经覆盖它了。
    certs = data.get("certifications") or []
    if certs and mode == "draft":
        shown_certs = [p for p in certs
                       if (p.get("evidence") or "pending") not in ("unusable", "inferred", "pending")]
        weak_marks = ("CET-4", "CET-6", "大学英语", "全国计算机等级", "普通话", "机动车驾驶")
        if shown_certs and all(any(w in (p.get("name") or "") for w in weak_marks)
                               for p in shown_certs):
            sec("cert").append(
                '<div class="item-note noprint">ⓘ 证书段目前只有通用类证书'
                f'（{"、".join(p.get("name","?") for p in shown_certs)}）—— '
                '对硕士学历者，CET-6 已被学历覆盖，单独列出反而显得没什么可写。'
                '补齐中级职称后本段会自动变强</div>')

    render_evidence_block(sec("cert"), "证书与职称",
                          certs, _cert_fmt, set())

    # ---- 按画像组装段落顺序 ----
    # 校招：教育置顶（没工作经历，教育就是主战场）
    # 社招：教育沉底（HR 先看你能干什么，学历只是门槛）
    order_secs = (["edu", "exp", "skill", "hon", "pub", "pat", "cert", "os"]
                  if pr["edu_first"] else
                  # 荣誉沉到最后：社招下它本来就 weakest，且现在还会被门控整段隐藏
                  ["exp", "skill", "os", "pub", "pat", "cert", "edu", "hon"])
    for sname in order_secs:
        L.extend(S.get(sname) or [])

    # ---- 缺口清单（仅校对模式）----
    if mode == "draft":
        gaps = []
        for q in data.get("content_gaps") or []:
            if q.get("priority") in ("P0", "P1"):
                gaps.append((q.get("priority"), q.get("question", ""), q.get("why", "")))
        if gaps:
            L.append('<div class="gaps noprint"><h3>补齐这些，简历会强很多</h3><ul>')
            for gpr, q, why in sorted(gaps):
                L.append(f"<li><b>[{gpr}]</b> {esc(q)}<br><span class='empty'>{md_inline(why)}</span></li>")
            L.append("</ul></div>")

    # ---- 页脚统计（仅校对模式）----
    if mode == "draft":
        d = stats["dropped"]
        h = stats["hidden_pending"]
        L.append('<div class="footer noprint">')
        L.append(f"母版 v{data.get('master',{}).get('version','?')} · 校对模式 · "
                 f"画像 {pr['label']}（{profile}） · 包装 {POLISH_LEVELS[polish]}（{polish}） · "
                 f"已拦截 {len(d)} 条不可对外条目"
                 + (f"（{'、'.join(x[0] for x in d)}）" if d else ""))
        if h:
            L.append(f"<br>出片时会隐藏 {len(h)} 条无证据条目：{'、'.join(h)}")
        if stats.get("unbacked"):
            L.append(f"<br>已按{pr['label']}画像隐藏 {len(stats['unbacked'])} 项无项目佐证的技能："
                     f"{'、'.join(s.get('name','?') for s in stats['unbacked'])}")
        if stats.get("commodity"):
            L.append(f"<br>已按范式隐藏 {len(stats['commodity'])} 项商品化能力（真实但无区分度）："
                     f"{'、'.join(stats['commodity'])} —— 它们已藏进交付物 bullet")
        if stats.get("honors_dropped"):
            L.append(f"<br>荣誉段已整体隐藏 {len(stats['honors_dropped'])} 条低价值条目："
                     f"{'、'.join(stats['honors_dropped'])}"
                     f" —— 无硬通货时，这一段不如不放")
        if polish == "bold":
            L.append("<br>⚠ 酥化模式下 G5 需追问 5 层（其余级别 3 层）—— 写得越满，被追问越狠")
        L.append("<br>切换到 --mode final 生成干净成稿。</div>")
    else:
        # ⚠ 必须 noprint：这是内部元信息，印在投递稿底部等于告诉对方
        #   「这份简历是某个系统批量生成的」。且「均已过证据校验」原本是句假话 ——
        #   成稿里含 self_reported（本人陈述）条目，它们未经第三方核实。
        # 只报 needs_confirm 的：成稿里 self_reported 有十几条，全报数字会麻木。
        # 真正需要面试前准备的，是「已写入但细节没填」的那些 —— 它们才是暴露点。
        n_confirm = sum(1 for blk in ("publications", "patents", "certifications", "ai_native")
                        for it in (data.get(blk) or []) if it.get("needs_confirm"))
        n_confirm += sum(1 for e in (data.get("experiences") or [])
                         for a in (e.get("achievements") or []) if a.get("needs_confirm"))
        d, h = stats["dropped"], stats["hidden_pending"]
        L.append(f'<div class="footer noprint">母版 v{data.get("master",{}).get("version","?")} · '
                 f'出片模式 · 已剔除 {len(d)} 条不可对外内容'
                 + (f'，并隐藏 {len(h)} 条未核实内容' if h else "")
                 + (f'　⚠ 成稿含 {n_confirm} 条「已写入但细节待补」的条目，'
                    f'面试可被追问（见草稿标注）' if n_confirm else "")
                 + "</div>")

    L.append("</div>")
    L.append(f"<script>{PAGINATE_JS}</script>")
    L.append("</body></html>")
    return "\n".join(L), stats


def main():
    ap = argparse.ArgumentParser(description="母版 YAML → 可投递 HTML 简历")
    ap.add_argument("master", help="master.yaml 路径")
    ap.add_argument("-o", "--out", required=True, help="输出 HTML 路径")
    ap.add_argument("--mode", choices=["draft", "final"], default="draft",
                    help="draft=校对模式（显示待补） / final=出片模式（干净成稿）")
    ap.add_argument("--target", help="定制版 tailored.yaml（决定条目筛选与排序）")
    args = ap.parse_args()

    data = load(args.master)
    # 定制版文件顶层是 `tailored:` 包裹，必须解包一层才能正确读取
    # selection / target / proposals 等字段，否则筛选会静默失效。
    # 兼容两种 schema（早期文件把 selection/target 写在顶层）—— 见 tailored_io.py
    tgt = load_tailored(args.target) if args.target else None

    html, stats = build_html(data, args.mode, tgt)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    print(f"[OK] 已生成：{out}  （模式：{args.mode}）")
    if stats["dropped"]:
        print("\n已拦截（禁止对外）：")
        for aid, ev in stats["dropped"]:
            print(f"  - {aid}  [{ev}]")
    if args.mode == "final" and stats["hidden_pending"]:
        print(f"\n已隐藏无证据条目 {len(stats['hidden_pending'])} 条（宁缺毋滥）")
    if stats.get("residual_strong"):
        print("\n⚠ 句中仍残留强主张词（证据不足，需人工改写或补证据）：")
        for aid, word, seg in stats["residual_strong"]:
            print(f"  - {aid} 含「{word}」→ {seg[:60]}")
    if args.mode == "draft" and stats["pending"]:
        print(f"\n待补条目 {len(stats['pending'])} 条：{'、'.join(stats['pending'])}")
        print("提示：补齐后用 --mode final 出片。")


if __name__ == "__main__":
    sys.exit(main())

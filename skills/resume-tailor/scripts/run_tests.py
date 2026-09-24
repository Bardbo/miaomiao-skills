#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""resume-tailor 回归测试

用法:
    python resume-tailor/scripts/run_tests.py            # 全跑
    python resume-tailor/scripts/run_tests.py -v         # 显示子命令输出

为什么要有它：
    下面每一条都对应一个**已经真实发生过**的静默 bug —— 它们的共同点是
    「看起来通过、其实没生效」，靠肉眼 review 报告发现不了：
      1. 白名单与 hidden_experiences 互斥 → 黑名单静默失效
      2. gaps 脚注 / 【待补】批注被算进覆盖率 → 缺失的硬性要求判成命中
      3. 分页器边搬边测高 → 内容溢出成 4 破页
      4. 沙箱里 chromium 起不来 → 导出卡死
      5. G3 数字在同输入下漂移

测试分两类：
    · 夹具测试：临时生成 master/tailored，验证筛选语义（不需要真实人物数据）
    · 真实数据测试：用 people/沃伦·巴菲特 的产物验证分页与 G3（数据缺失则跳过）
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent          # resume-tailor/scripts/
ROOT = HERE.parent                              # resume-tailor/
WS = ROOT.parent                                # 工作区根

RENDER = HERE / "render_resume.py"
GATES = HERE / "check_gates.py"
MEASURE = HERE / "measure_pages.js"
EXPORT_PDF = HERE / "export_pdf.js"

# 分页修复的「不变量」直接钉死在源码里，避免有人把 >=2 改回 >=3、
# 或把净高判定改回 adv —— 这些改动会让两页简历重新出现残页却不报错。
RENDER_SRC = RENDER.read_text(encoding="utf-8")
MEASURE_SRC = MEASURE.read_text(encoding="utf-8")

# node / playwright：优先环境变量，其次 PATH，最后回落到本机已知的托管路径
# ⚠ 兜底值必须是**真实路径**，不能是占位符：NODE_PATH 指不到 node_modules 时
#   playwright 解析失败、测量脚本静默崩溃、输出为空 —— 而 test_pagination 里
#   「无溢出 / 无残页」两条断言在空输出下会**全部通过**，逐文件的末页与页数断言
#   则一条都不执行。结果：分页回归覆盖率归零，报告却一片绿（实测 2026-09-21 中招）。
# node / playwright：优先环境变量，其次 PATH，最后回落到用户主目录下已知的托管路径
# ⚠ 兜底值必须是**真实路径**，不能是占位符：NODE_PATH 指不到 node_modules 时
#   playwright 解析失败、测量脚本静默崩溃、输出为空 —— 而 test_pagination 里
#   「无溢出 / 无残页」两条断言在空输出下会**全部通过**，逐文件的末页与页数断言
#   则一条都不执行。结果：分页回归覆盖率归零，报告却一片绿（实测 2026-09-21 中招）。
# 兜底路径通过 Path.home() 动态拼接（如 ~/.workbuddy/binaries/node/...），不硬编码用户名。
def _managed_node():
    """探测托管 node（WorkBuddy 布局：~/.workbuddy/binaries/node/versions/<ver>/node.exe）。"""
    base = Path.home() / ".workbuddy" / "binaries" / "node"
    versions = sorted((base / "versions").glob("*/node.exe"), key=lambda p: p.name, reverse=True) \
        if (base / "versions").is_dir() else []
    return str(versions[0]) if versions else ""

def _managed_node_modules():
    """探测托管 playwright（WorkBuddy 布局：~/.workbuddy/binaries/node/workspace/node_modules）。"""
    p = Path.home() / ".workbuddy" / "binaries" / "node" / "workspace" / "node_modules"
    return str(p) if p.is_dir() else ""

NODE = os.environ.get("NODE_BIN") or shutil.which("node") or _managed_node() or "node"
NODE_PATH = os.environ.get("NODE_MODULES") or _managed_node_modules() or ""


class Results:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def ok(self, name, detail=""):
        self.passed.append((name, detail))
        print(f"  ✅ {name}" + (f" —— {detail}" if detail else ""))

    def bad(self, name, detail=""):
        self.failed.append((name, detail))
        print(f"  ❌ {name}" + (f" —— {detail}" if detail else ""))

    def skip(self, name, why=""):
        self.skipped.append((name, why))
        print(f"  ⚠ {name}（跳过：{why}）")

    def check(self, cond, name, detail=""):
        (self.ok if cond else self.bad)(name, detail)
        return cond


def run(cmd, **kw):
    env = dict(os.environ)
    env["NODE_PATH"] = NODE_PATH
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, **kw)


# ---------------------------------------------------------------------------
# 夹具
# ---------------------------------------------------------------------------
MASTER_YAML = """
master:
  version: 1
  updated_at: 2026-09-10
  locale: zh-CN

owner:
  name: 测试候选人
  contact:
    phone: "13800000000"
    email: "test@example.com"
    city: 上海
    links: []
  profile:
    photo: false
    show_age: false
    show_political_status: false

preferences:
  profile: experienced
  polish: sincere
  show_intention: false
  tone: 克制
  max_pages: 2

summary:
  enabled: true
  text: |
    测试摘要：具备权益投研与组合管理经验。

experiences:
  - id: e1
    type: work
    org: 甲公司
    title: 投资经理
    period: { start: "2020-01", end: null, current: true }
    achievements:
      - id: e1-a1
        action: 管理
        object: 权益组合
        method: ZZMARK_E1A1
        result: {metric: 年化, value: "12%", baseline: "", scope: "2020-2024"}
        evidence: verified
        strength: strong
  - id: e2
    type: work
    org: 乙公司
    title: 分析师
    period: { start: "2017-01", end: "2019-12", current: false }
    achievements:
      - id: e2-a1
        action: 完成
        object: 行业研究
        method: 上市公司调研
        result: {metric: 报告数, value: "30 篇", baseline: "", scope: "2017-2019"}
        evidence: verified
        strength: normal
  - id: e3
    type: work
    org: 丙公司
    title: 研究员
    period: { start: "2014-01", end: "2016-12", current: false }
    achievements:
      - id: e3-a1
        action: 建立
        object: 股票池
        method: 财务建模
        result: {metric: 覆盖, value: "200 只", baseline: "", scope: "2014-2016"}
        evidence: verified
        strength: normal

education:
  - school: 某大学
    degree: 硕士
    major: 金融学
    period: { start: "2011-09", end: "2014-06" }

skills:
  - { id: sk-1, name: 权益投资, category: 投资研究, level: 精通,
      kind: capability, status: active, evidence_refs: [e1-a1] }
"""

# 关键：白名单写了 e1/e2/e3，黑名单又写了 e2 ——
# 旧实现里二者互斥，黑名单会静默失效，e2 会照样出现在成稿里。
TAILORED_YAML = """
tailored:
  id: t-test
  master_version: 1
  created_at: 2026-09-10
  target:
    company: 测试公司
    role: 测试岗
    jd_snapshot: {}
    analysis:
      # 「基金从业资格」故意**只**出现在 gaps 脚注里 ——
      # 若覆盖率把它算成命中，说明脚注污染了统计。
      p1_critical: [基金从业资格, 硕士]
      p2_important: [股票池, 上市公司调研]
      p3_nice: [CFA]
  selection:
    experiences: [e1, e2, e3]
    hidden_experiences:
      - e2
    achievements: []
    hidden_achievements:
      - e1-a1
    hidden_skills: []
    rationale: "测试用"
  rewrite_policy:
    level: L2
  gaps:
    - ref: ""
      question: "是否持有基金从业资格？"
      impact: "这是注册前置条件。"
  output:
    format: html
    path: "output/resume-test-final.html"
"""


def build_fixture(tmp):
    mdir = Path(tmp)
    (mdir / "output").mkdir(parents=True, exist_ok=True)
    mp = mdir / "master.yaml"
    tp = mdir / "targets" / "J" / "tailored.yaml"
    tp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(MASTER_YAML, encoding="utf-8")
    tp.write_text(TAILORED_YAML, encoding="utf-8")
    return mp, tp, mdir / "output" / "resume-test-final.html"


# ---------------------------------------------------------------------------
# 测试
# ---------------------------------------------------------------------------
def test_selection_blacklist_after_whitelist(R, verbose):
    """白名单 + 黑名单必须叠加生效（黑名单不能因白名单存在而失效）。"""
    print("\n【1】筛选语义：白名单优先、黑名单兜底")
    tmp = tempfile.mkdtemp(prefix="rt-")
    try:
        mp, tp, out_html = build_fixture(tmp)
        r = run([sys.executable, str(RENDER), str(mp), "-o", str(out_html),
                 "--mode", "final", "--target", str(tp)])
        if verbose and (r.stdout or r.stderr):
            print(r.stdout, r.stderr)
        if not R.check(r.returncode == 0 and out_html.exists(),
                       "渲染成功", f"exit={r.returncode}"):
            return
        html = out_html.read_text(encoding="utf-8")

        # 白名单生效：e1 / e3 都在
        R.check("甲公司" in html, "白名单命中：e1（甲公司）在成稿里")
        R.check("丙公司" in html, "白名单命中：e3（丙公司）在成稿里")
        # 黑名单生效：e2 虽在白名单里，但被 hidden_experiences 剔除
        R.check("乙公司" not in html,
                "黑名单生效：e2（乙公司）虽在白名单仍被剔除")
        # 成就级黑名单
        R.check("ZZMARK_E1A1" not in html,
                "成就黑名单生效：e1-a1 的标记文本未出现")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gates_on_fixture(R, verbose):
    """闸门：0 引用错误；生效经历数 = 白名单 − 黑名单；gaps 不污染覆盖率。"""
    print("\n【2】闸门：引用错误 / 生效条目 / gaps 不污染覆盖率")
    tmp = tempfile.mkdtemp(prefix="rt-")
    try:
        mp, tp, out_html = build_fixture(tmp)
        run([sys.executable, str(RENDER), str(mp), "-o", str(out_html),
             "--mode", "final", "--target", str(tp)])
        r = run([sys.executable, str(GATES), "--master", str(mp),
                 "--target", str(tp)])
        if verbose and (r.stdout or r.stderr):
            print(r.stdout, r.stderr)
        out = r.stdout or ""

        R.check("引用错误 0 处" in out, "G1 无引用错误")
        m = re.search(r"生效 (\d+) 段经历", out)
        n = int(m.group(1)) if m else -1
        R.check(n == 2, "G1 生效经历数 = 2（3 条白名单 − 1 条黑名单）",
                f"实际 {n}")

        # 覆盖率必须按成稿算，而不是按「生效经历」估算
        R.check("命中基于成稿文本" in out, "G3 命中基于成稿文本")
        # 基金从业资格只出现在 gaps 脚注 → 必须判未命中
        R.check("P1「基金从业资格」未命中" in out,
                "G3 完整性：仅存在于 gaps 脚注的词判为未命中")
        # 硕士在教育段 → 必须命中（防「生效条目不含教育」的假阴性）
        R.check("P1「硕士」未命中" not in out,
                "G3 无假阴性：成稿里的硕士学历被判为命中")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_g3_stable(R, verbose):
    """同一输入跑两次，G3 数字必须一致。"""
    print("\n【3】G3 稳定性：同输入同结果")
    real = WS / "people" / "沃伦·巴菲特"
    mp, tp = real / "master.yaml", real / "targets" / "J7-权益基金经理" / "tailored.yaml"
    if not (mp.exists() and tp.exists()):
        R.skip("G3 稳定性", "缺少巴菲特案例数据")
        return
    hits = []
    for _ in range(2):
        r = run([sys.executable, str(GATES), "--master", str(mp), "--target", str(tp)])
        m = re.search(r"命中 (\d+)/(\d+)", r.stdout or "")
        hits.append(m.group(0) if m else "?")
    R.check(hits[0] != "?" and hits[0] == hits[1],
            "两次运行覆盖率一致", f"{hits[0]} vs {hits[1]}")


def test_pagination(R, verbose):
    """分页：无溢出、无残页（用真实案例产物，覆盖 2 页均衡与净高断页）。"""
    print("\n【4】分页：无溢出 / 无残页 / 末页达标")
    cases = [
        ("沃伦·巴菲特", "resume-J7-权益基金经理-final.html", None),
        ("沃伦·巴菲特", "resume-J7-权益基金经理-draft.html", None),
        ("张三",       "resume-方向A-技术向-final.html",      None),  # 2 页均衡
        ("王五",       "resume-J6-数据分析-draft.html",       1),     # 净高修复：1 页
    ]
    targets = []
    for person, fn, _ in cases:
        p = WS / "people" / person / "output" / fn
        if p.exists():
            targets.append((p, _))
    if not targets:
        R.skip("分页检查", "缺少真实案例渲染产物")
        return
    if not Path(NODE).exists() and not shutil.which(NODE):
        R.skip("分页检查", f"找不到 node（{NODE}）")
        return
    r = run([NODE, str(MEASURE)] + [str(p) for p, _ in targets])
    if verbose and (r.stdout or r.stderr):
        print(r.stdout, r.stderr)
    out = r.stdout or ""
    # ⚠ 先确认测量**真的跑起来了**，再谈结论。
    #   测量脚本一旦崩（playwright 解析不到等），out 为空 —— 下面两条断言在空字符串
    #   上会全部 trivially 通过，逐文件的末页/页数断言一条都不执行。分页覆盖率归零
    #   而报告全绿，正是本文件开头点名要防的那种「看起来通过、其实没生效」。
    R.check("页数" in out, "分页实测真的跑起来了（防止空输出让断言空过）",
            (r.stderr or "").strip()[:120])
    R.check("⚠ 有页内容超出" not in out, "无页面溢出（分页器兜住了）")
    # 可修残页（内容量够却没均衡）绝不能出现
    R.check("残页（内容量够" not in out, "无『内容量够却未均衡』的可修残页")
    # 逐文件解析页数 + 末页填充
    for blk in out.split("=" * 58):
        m = re.search(r"(\S+\.html)", blk)
        if not m:
            continue
        name = Path(m.group(1)).name
        pn = re.search(r"页数 (\d+)", blk)
        pages = int(pn.group(1)) if pn else 0
        fills = [int(x) for x in re.findall(r"(\d+)%  \d+mm", blk)]
        last = fills[-1] if fills else 0
        R.check(last >= 55, f"末页不是残页：{name}", f"末页填充 {last}%")
    # 期望页数断言（如王五草稿应为 1 页）
    expect1 = {fn: e for _, fn, e in cases if e is not None}
    for blk in out.split("=" * 58):
        m = re.search(r"(\S+\.html)", blk)
        if not m:
            continue
        name = Path(m.group(1)).name
        if name in expect1:
            pn = re.search(r"页数 (\d+)", blk)
            pages = int(pn.group(1)) if pn else 0
            R.check(pages == expect1[name],
                    f"页数符合预期：{name}", f"实际 {pages} 页，期望 {expect1[name]} 页")


def test_sandbox_flags(R, verbose):
    """沙箱：chromium 启动必须带 --no-sandbox，且退出不阻塞。"""
    print("\n【5】沙箱适配：--no-sandbox / 不阻塞退出")
    for js in (EXPORT_PDF, MEASURE):
        if not js.exists():
            R.skip(js.name, "文件不存在")
            continue
        src = js.read_text(encoding="utf-8")
        R.check("--no-sandbox" in src, f"{js.name} 带 --no-sandbox")
        R.check("browser.close().catch" in src,
                f"{js.name} 非阻塞 browser.close()")


def test_pagination_js_invariants(R, verbose):
    """静态锁定分页修复，防止回退（>=2 均衡、净高断页、续块、测量区分）。"""
    print("\n【6】分页 JS 不变量（防回退）")
    # 修复一：均衡逻辑对 2 页生效（曾经写成 >=3，两页简历直接跳过均衡）
    R.check("pages.length >= 2" in RENDER_SRC,
            "均衡触发条件为 >=2（两页简历不再被跳过）")
    R.check("pages.length >= 3" not in RENDER_SRC,
            "均衡不再以 >=3 为门槛")
    # 修复二：断页判定用净高 tight[i]，否则页底 margin 占版面挤多一页
    R.check("used + tight[i] > H" in RENDER_SRC,
            "断页判定用净高 tight[i]（含尾随 margin 会多断一页）")
    # 修复三：超长 item 块内拆分为续块
    R.check("item-cont" in RENDER_SRC and "trySplit" in RENDER_SRC,
            "超长经历块内拆分（续块）已实现")
    # 测量脚本区分「可修残页」与「内容量不足」，避免误报
    R.check("orphan_fixable" in MEASURE_SRC,
            "测量脚本区分可修残页与内容量不足")
    R.check("slim_gap" in MEASURE_SRC,
            "测量脚本给出压到 N-1 页还差多少的提示")
    # 修复四（2026-09-22）：分页 JS 在**屏幕媒体**运行，用净高判定；而 page.pdf()
    #   在**打印媒体**渲染，同一 .page 两者高度不同（.item 尾随 margin 不折叠、
    #   把整页撑过 A4）——Chromium 会硬切出一张无 padding 的幽灵空页（用户报的
    #   「第一页满、第二页大半空白」正是它）。printSafety() 用整页真实打印高复核：
    #   ① 防硬切（超 A4 就把尾部整块顺延到下一页）；② 防半空（回填下一页顶部整块）。
    #   zeroTail() 先去掉页底那段无效 margin（把整页顶过 A4 的真凶），否则顺延会
    #   把本该 1 页的内容拆成 2 页半空。
    R.check("printSafety" in RENDER_SRC,
            "打印安全兜底 printSafety() 已接入（防硬切空页）")
    R.check("function pageH" in RENDER_SRC,
            "溢出判定用整页真实高 pageH()（非内容净高，否则漏判硬切）")
    R.check("pageH(ps[i]) > A4 + 1" in RENDER_SRC,
            "防硬切：整页真实高 > A4 才顺延（净高会漏判 1mm 级溢出）")
    R.check("function zeroTail" in RENDER_SRC,
            "防硬切前先 zeroTail()（去页底无效 margin，避免拆出半空页）")


# G4/G5 专用夹具：摘要里同时放 A 级（闭环）/B 级（显著提升）/C 级（主导）词；
# 成就里放 pending（扛不住）、int 型 baseline（曾把 G5 打崩）、带难点（抗追问底子）。
MASTER_G45 = """
master:
  version: 1
  updated_at: 2026-09-10
  locale: zh-CN
owner:
  name: 测试候选人
  contact: { phone: "13800000000", email: "t@example.com", city: 上海, links: [] }
  profile: { photo: false, show_age: false, show_political_status: false }
preferences:
  profile: experienced
  polish: sincere
  show_intention: false
  tone: 克制
  max_pages: 2
summary:
  enabled: true
  text: |
    测试摘要：主导过闭环项目，显著提升交付效率。
experiences:
  - id: g1
    type: work
    org: 甲公司
    title: 投资经理
    period: { start: "2020-01", end: null, current: true }
    achievements:
      - id: g1-a1
        action: 负责
        object: 研究
        method: 调研
        result: { metric: 报告, value: "", baseline: "", scope: "" }
        evidence: pending
        strength: normal
      - id: g1-a2
        action: 搭建
        object: 分析模板
        method: Excel
        result: { metric: 耗时, value: "3 天→1 天", baseline: 3, scope: "全厂" }
        evidence: self_reported
        strength: normal
      - id: g1-a3
        action: 建设
        object: 内网平台
        difficulty: 内网隔离无外网，无第三方组件源
        result: { metric: 覆盖, value: "200 人", baseline: "", scope: "全公司" }
        evidence: verified
        strength: strong
"""

TAILORED_G45 = """
tailored:
  id: t-g45
  master_version: 1
  created_at: 2026-09-10
  target:
    company: 测试公司
    role: 测试岗
    jd_snapshot: {}
    analysis:
      p1_critical: [研究]
      p2_important: []
      p3_nice: []
  selection:
    experiences: [g1]
    achievements: [g1-a1, g1-a2, g1-a3]
    rationale: "测试用"
  rewrite_policy:
    level: L2
  gaps: []
  output:
    format: html
    path: "output/resume-g45-final.html"
"""


def build_fixture_g45(tmp):
    mdir = Path(tmp)
    (mdir / "output").mkdir(parents=True, exist_ok=True)
    mp = mdir / "master.yaml"
    tp = mdir / "targets" / "J" / "tailored.yaml"
    tp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(MASTER_G45, encoding="utf-8")
    tp.write_text(TAILORED_G45, encoding="utf-8")
    return mp, tp


def _run_gates_g45(verbose):
    """渲染 final 后跑门禁（不传 --draft，验证 G4 默认开启）。返回 stdout。"""
    tmp = tempfile.mkdtemp(prefix="rt-g45-")
    try:
        mp, tp = build_fixture_g45(tmp)
        out_html = Path(tmp) / "output" / "resume-g45-final.html"
        run([sys.executable, str(RENDER), str(mp), "-o", str(out_html),
             "--mode", "final", "--target", str(tp)])
        r = run([sys.executable, str(GATES), "--master", str(mp),
                 "--target", str(tp)])
        if verbose and (r.stdout or r.stderr):
            print(r.stdout, r.stderr)
        return (r.stdout or "") + (r.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_g4_default_and_grading(R, verbose):
    """G4 必须默认跑（不传 --draft），且**尊重 A/B/C 分级**。"""
    print("\n【7】G4 去 AI 味：默认开启 + 分级正确")
    out = _run_gates_g45(verbose)
    R.check("Traceback" not in out, "G4 运行不崩溃")
    # 默认开启：以前不传 --draft 会打印「跳过」，现在应直接给结论
    R.check("G4 AI 味：" in out and "跳过" not in out,
            "G4 默认执行（无需手动传 --draft）")
    # A 级 = 硬拦
    R.check("A 级 AI 味词：「闭环」" in out, "A 级词「闭环」被硬拦")
    # B 级 = 硬拦
    R.check("B 级 AI 味词：「显著提升」" in out, "B 级词「显著提升」被硬拦")
    # C 级 = 不硬拦（这是曾经的 bug：扁平词表把 C 级当 A 级，逼作者删真实主张）
    R.check("A 级 AI 味词：「主导」" not in out,
            "C 级词「主导」未被误判为 A 级硬拦")
    R.check("B 级 AI 味词：「主导」" not in out,
            "C 级词「主导」未被误判为 B 级硬拦")
    R.check("「主导」" in out, "C 级词「主导」仍被提示（只是不硬拦）")


def test_g5_interview(R, verbose):
    """G5 反向面试：脚本化 + 类型容错（baseline 为 int 不能崩）。"""
    print("\n【8】G5 反向面试（静态代理）")
    out = _run_gates_g45(verbose)
    R.check("Traceback" not in out, "G5 运行不崩溃（含 int 型 baseline）")
    R.check("G5 反向面试（静态代理）" in out, "G5 已脚本化执行")
    # pending 条目在 final 里根本不会出片 → 不该算「扛不住追问」（假警报），
    # 应单独提示「已隐藏」。口径与 G3「只测成稿」一致。
    R.check("g1-a1 证据待确认，出片已隐藏" in out,
            "pending 条目按「已隐藏」处理，不算扛不住追问")
    R.check("g1-a1 扛不住反向面试" not in out,
            "pending 条目未被误判为扛不住追问")
    # g1-a2 的 baseline 是数字 3（旧实现在这里 AttributeError 崩掉）；
    # 且它 value/baseline/scope 齐全，不该被列入「可加固」
    R.check("g1-a2 可加固" not in out,
            "int 型 baseline 正常处理且不误报软项")
    R.check("条填了「难点」" in out, "填了难点的条目计入正面指标")


def _run_gates_real(person, target, extra=()):
    """跑真实案例门禁，返回 stdout。缺数据返回 None。"""
    d = WS / "people" / person
    mp = d / "master.yaml"
    tp = d / "targets" / target / "tailored.yaml"
    rd = d / "output" / f"resume-{target}-final.html"
    if not (mp.exists() and tp.exists() and rd.exists()):
        return None
    r = run([sys.executable, str(GATES), "--master", str(mp),
             "--target", str(tp), "--rendered", str(rd)] + list(extra))
    return (r.stdout or "") + (r.stderr or "")


def test_g3_verdict(R, verbose):
    """G3 必须给出**硬结论**，且 P1 全灭 = 不建议投（ERROR）。"""
    print("\n【9】G3 匹配结论：硬判据（P1 定生死）")
    # 李四：JD 要 Oracle/JavaScript，他是 Go/Python → P1 应 0 命中 → 不建议投
    out = _run_gates_real("李四", "J1-校招软件研发")
    if out is None:
        R.skip("G3 结论（不建议投）", "缺李四案例产物")
    else:
        if verbose:
            print(out)
        R.check("G3 结论：不建议投" in out, "P1 全灭时给出「不建议投」结论")
        R.check("不建议投" in out and "[ERROR] G3" in out,
                "「不建议投」是硬 ERROR（不只是 warn）")
    # 钱七：P1 2/2 → 不该被判「不建议投」
    out2 = _run_gates_real("钱七", "J3-大客户销售")
    if out2 is None:
        R.skip("G3 结论（可投）", "缺钱七案例产物")
    else:
        R.check("不建议投" not in out2, "P1 达标时不会误报「不建议投」")
        R.check("G3 结论：" in out2, "G3 始终输出结论行")
    # 巴菲特：P1 里过半是描述性长句（「5 年以上权益投研经验」这类 JD 条款）
    # → 覆盖率被系统性低估，必须判「待定」而不是冤枉候选人「不建议直接投」
    out3 = _run_gates_real("沃伦·巴菲特", "J7-权益基金经理")
    if out3 is None:
        R.skip("G3 词表质量", "缺巴菲特案例产物")
    else:
        R.check("描述性长句" in out3, "识别出 P1 里的描述性长句（词表质量提示）")
        R.check("G3 结论：待定" in out3,
                "过半 P1 是不可匹配长句时判「待定」，不误判为不匹配")
        R.check("不建议直接投" not in out3,
                "坏词表下不给出「不建议直接投」的错误结论")


def test_g6_layout(R, verbose):
    """G6 版式：内部标记不得泄漏进成稿；分页实测无溢出/残页。"""
    print("\n【10】G6 版式：泄漏检查 + 实测分页")
    # 成稿不应含校对标记
    d = WS / "people" / "沃伦·巴菲特" / "output"
    fin = d / "resume-J7-权益基金经理-final.html"
    if fin.exists():
        body = fin.read_text(encoding="utf-8")
        sys.path.insert(0, str(HERE))
        from check_gates import _html_text          # noqa: E402
        vis = _html_text(body)
        for mark in ("【待补", "○本人陈述", "校对模式"):
            R.check(mark not in vis, f"成稿正文不含校对标记「{mark}」")
    else:
        R.skip("G6 泄漏检查", "缺巴菲特成稿")
    out = _run_gates_real("李四", "J1-校招软件研发")
    if out is None:
        R.skip("G6 实测分页", "缺李四案例产物")
        return
    R.check("G6 版式：" in out, "G6 已执行并输出结论")
    R.check("超出 A4" not in out, "G6 未报分页溢出")


def test_internal_markers_guarded(R, verbose):
    """内部字段名（✔ / 难点 / 范围）只能出现在校对稿，不得印进投递稿。

    事故（2026-09-21）：这三者都没有 mode 守卫，12/12 份 final 稿全被印了出来 ——
    雇主会看到一颗没有图例的绿勾（✔ = 证据档位 verified）和一堆字段标签。
    紧挨着的「○本人陈述」(self_reported) 与「【待补】」(pending) 都正确带了 mode 守卫，
    唯独 ✔ 漏了 —— 说明意图本来就是「内部标记不进投递稿」，这三条是漏网而非设计。
    """
    print("\n【11】内部字段名不得印进投递稿")
    sys.path.insert(0, str(HERE))
    from check_gates import _html_text          # noqa: E402
    marks = ("✔", "（难点：", "（范围：")
    pdir = WS / "people"
    if not pdir.is_dir():
        R.skip("内部标记守卫", "无 people/ 工作区（clone 后未 init）")
        return
    finals, drafts = [], []
    for d in sorted(pdir.iterdir()):
        od = d / "output"
        if not od.is_dir():
            continue
        for f in sorted(od.glob("*.html")):
            vis = _html_text(f.read_text(encoding="utf-8"))
            if f.name.endswith("-final.html"):
                finals.append((f, vis))
            elif f.name.endswith("-draft.html"):
                drafts.append((f, vis))
    if not finals:
        R.skip("内部标记守卫", "无 final 成稿")
        return
    bad = [f.name for f, vis in finals if any(m in vis for m in marks)]
    R.check(not bad,
            f"全部 {len(finals)} 份 final 稿不含 ✔ /（难点：/（范围：",
            "；".join(bad[:3]))
    # 反向锁定：校对稿必须**仍然**保留这些审计信息 ——
    # 只为让闸门变绿而把草稿里的难度/证据标记一并删掉，是另一种自欺。
    kept = [f.name for f, vis in drafts if any(m in vis for m in marks)]
    R.check(bool(kept),
            "draft 稿仍保留内部标记（审计信息未被误删）",
            f"{len(kept)}/{len(drafts)} 份")
    # 闸门本身要能拦住：G6 泄漏清单必须含这三个标记，否则回归网仍有洞
    src = (HERE / "check_gates.py").read_text(encoding="utf-8")
    R.check(all(m in src for m in marks),
            "G6 泄漏清单已含这三个标记（否则闸门形同虚设）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    print("=" * 58)
    print("resume-tailor 回归测试")
    print("=" * 58)
    R = Results()
    test_selection_blacklist_after_whitelist(R, args.verbose)
    test_gates_on_fixture(R, args.verbose)
    test_g3_stable(R, args.verbose)
    test_pagination(R, args.verbose)
    test_sandbox_flags(R, args.verbose)
    test_pagination_js_invariants(R, args.verbose)
    test_g4_default_and_grading(R, args.verbose)
    test_g5_interview(R, args.verbose)
    test_g3_verdict(R, args.verbose)
    test_g6_layout(R, args.verbose)
    test_internal_markers_guarded(R, args.verbose)

    print("\n" + "=" * 58)
    print(f"通过 {len(R.passed)} · 失败 {len(R.failed)} · 跳过 {len(R.skipped)}")
    if R.failed:
        print("\n失败明细：")
        for name, detail in R.failed:
            print(f"  - {name} {detail}")
    print("=" * 58)
    return 1 if R.failed else 0


if __name__ == "__main__":
    sys.exit(main())

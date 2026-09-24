#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_docx.py —— 把渲染后的简历 HTML 转成**可投递的 .docx**

为什么走 HTML 而不是直接从 YAML 生成：
    render_resume.py 里塞了全部出片规则 —— pending 隐藏、unusable 拦截、
    profile 画像过滤、commodity 技能收敛、荣誉段整段消失、摘要门控……
    这些规则写在一处，docx 若另起炉灶，必然出现「HTML 对、docx 错」的双写漂移。

    所以本脚本只做一件事：**把已经过全部规则的 HTML 忠实地序列化成 Word**。
    规则仍只有一份，docx 只是另一个下游出口。

ATS 兼容性（帮别人做简历，过不了机器初筛等于白做）：
    - 纯段落 + 悬挂缩进，不用文本框、不用表格排版、不用页眉页脚
    - 文字是**真文字**，不是图片 —— 可被 ATS 提取
    - 中西文分设字体，避免中文变方框

排版参数与 render_resume.py 的 CSS 严格对齐（15mm/18mm 边距、14px 正文、1.7 行距），
否则 density.py 算出的页数/填充率在 docx 上就不作数了。

用法:
    python scripts/export_docx.py --person 王五
    python scripts/export_docx.py --person 张三 --mode draft
    python scripts/export_docx.py --person 张三 --target targets/方向A-技术向/tailored.yaml
    python scripts/export_docx.py --html people/王五/output/resume-final.html
"""
import argparse
import html as html_mod
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 包根：config/
WORKSPACE = os.environ.get("RESUME_WORKSPACE") or os.getcwd()        # 工作区：people/ 所在目录
PEOPLE = os.path.join(WORKSPACE, "people")
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# 极简 DOM：只需要标签名、class、文本
# ---------------------------------------------------------------------------
SKIP_TAGS = {"script", "style", "head", "meta", "title", "link", "br"}


class Node:
    __slots__ = ("tag", "attrs", "children", "texts", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.texts = []
        self.parent = parent

    @property
    def cls(self):
        return (self.attrs.get("class") or "").split()

    def has(self, c):
        return c in self.cls

    def text(self):
        """递归取纯文本，跳过 noprint。"""
        if self.has("noprint"):
            return ""
        parts = list(self.texts)
        for ch in self.children:
            if ch.tag in SKIP_TAGS:
                continue
            parts.append(ch.text())
        s = "".join(parts)
        s = html_mod.unescape(s)
        return re.sub(r"\s+", " ", s).strip()

    def find_all(self, tag=None, cls=None):
        out = []
        for ch in self.children:
            if ch.has("noprint"):
                continue
            ok = True
            if tag and ch.tag != tag:
                ok = False
            if cls and cls not in ch.cls:
                ok = False
            if ok:
                out.append(ch)
            out.extend(ch.find_all(tag, cls))
        return out


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        if tag in ("meta", "link", "br", "img", "hr"):
            return
        n = Node(tag, dict(attrs), self.cur)
        self.cur.children.append(n)
        if tag not in ("span", "b", "strong", "i", "em", "a", "u"):
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.texts.append(data)


def parse(html_text):
    b = Builder()
    b.feed(html_text)
    return b.root


# ---------------------------------------------------------------------------
# 版式常量：与 render_resume.py 的 CSS 对齐
# ---------------------------------------------------------------------------
FONT_CJK = "微软雅黑"
FONT_LAT = "Calibri"


def _mm(v):
    from docx.shared import Mm
    return Mm(v)


def _pt(v):
    from docx.shared import Pt
    return Pt(v)


def set_font(run, size_pt, bold=False, color=None, name_cjk=FONT_CJK,
             name_lat=FONT_LAT):
    from docx.oxml.ns import qn
    run.font.size = _pt(size_pt)
    run.font.bold = bold
    run.font.name = name_lat
    if color:
        from docx.shared import RGBColor
        run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name_lat)
    rfonts.set(qn("w:hAnsi"), name_lat)
    rfonts.set(qn("w:eastAsia"), name_cjk)


def para_spacing(p, before=0, after=0, line=1.0):
    pf = p.paragraph_format
    pf.space_before = _pt(before)
    pf.space_after = _pt(after)
    pf.line_spacing = line


def add_right_tab(p, doc, right_mm):
    """在右边距处打一个右对齐制表位 —— 用于「公司名 …… 时间」的经典排版。"""
    from docx.enum.text import WD_TAB_ALIGNMENT
    from docx.shared import Mm
    width = doc.sections[0].page_width - doc.sections[0].left_margin \
        - doc.sections[0].right_margin
    pf = p.paragraph_format
    pf.tab_stops.add_tab_stop(Mm(right_mm), WD_TAB_ALIGNMENT.RIGHT)
    return width


# ---------------------------------------------------------------------------
# 块识别
# ---------------------------------------------------------------------------
def _first_text(node, cls):
    for n in node.find_all(cls=cls):
        t = n.text()
        if t:
            return t
    return ""


def walk_blocks(page):
    """把 .page 下的内容切成有序块。"""
    blocks = []
    for ch in page.children:
        if ch.has("noprint") or ch.tag in SKIP_TAGS:
            continue
        c = ch.cls
        if ch.tag == "h1":
            blocks.append(("name", ch.text()))
        elif "contact" in c:
            blocks.append(("contact", _join_spans(ch)))
        elif "summary" in c:
            blocks.append(("summary", ch.text()))
        elif ch.tag == "h2":
            blocks.append(("section", ch.text()))
        elif "skill-line" in c:
            blocks.append(("skill", _skill_line(ch)))
        elif "edu-line" in c:
            blocks.append(("edu", _edu_line(ch)))
        elif "item" in c:
            blocks.append(("item", ch))
        elif "footer" in c:
            continue  # 内部标注，不进成稿
        elif ch.tag in ("div", "ul", "p"):
            t = ch.text()
            if t:
                blocks.append(("para", t))
    return blocks


def _join_spans(node):
    """contact 里的 span 是「电话 | 邮箱 | 现居」，sep 单独一个 span。"""
    parts = []
    for sp in node.find_all("span"):
        if sp.has("sep"):
            continue
        t = sp.text()
        if t:
            parts.append(t)
    return "  |  ".join(parts)


def _skill_line(node):
    k = _first_text(node, "skill-k")
    cont = _first_text(node, "skill-cont")
    if not cont:
        whole = node.text()
        cont = whole[len(k):].strip() if k and whole.startswith(k) else whole
    return (k.rstrip("：: "), cont)


def _edu_line(node):
    deg = _first_text(node, "edu-deg")
    major = _first_text(node, "edu-major")
    time = _first_text(node, "item-time")
    rest = _first_text(node, "edu-hl")
    return (deg, major, time, rest)


# ---------------------------------------------------------------------------
# 写 docx
# ---------------------------------------------------------------------------
def build_docx(page, out_path):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Mm, Pt

    doc = Document()

    sec = doc.sections[0]
    sec.page_width = Mm(210)
    sec.page_height = Mm(297)
    # 与 CSS .page{padding:15mm 18mm} 严格一致 —— density 的页数模型据此成立
    sec.top_margin = Mm(15)
    sec.bottom_margin = Mm(15)
    sec.left_margin = Mm(18)
    sec.right_margin = Mm(18)

    st = doc.styles["Normal"]
    st.font.name = FONT_LAT
    st.font.size = Pt(10.5)

    def new_p(before=0, after=0, line=1.0, align=None):
        p = doc.add_paragraph()
        para_spacing(p, before, after, line)
        if align is not None:
            p.alignment = align
        return p

    for kind, val in walk_blocks(page):
        if kind == "name":
            p = new_p(after=2, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
            set_font(p.add_run(val), 19.5, bold=True)

        elif kind == "contact":
            p = new_p(after=2, line=1.2, align=WD_ALIGN_PARAGRAPH.CENTER)
            set_font(p.add_run(val), 9.5, color="555555")

        elif kind == "summary":
            p = new_p(after=6, line=1.5)
            set_font(p.add_run(val), 10)

        elif kind == "section":
            p = new_p(before=10, after=4, line=1.2)
            pPr = p._element.get_or_add_pPr()
            # 同 h2 的左侧色条：用段落边框近似（不影响 ATS 取词）
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
            pbdr = OxmlElement("w:pBdr")
            left = OxmlElement("w:left")
            left.set(qn("w:val"), "single")
            left.set(qn("w:sz"), "18")
            left.set(qn("w:space"), "4")
            left.set(qn("w:color"), "1F4E79")
            pbdr.append(left)
            pPr.append(pbdr)
            set_font(p.add_run(val), 11.5, bold=True, color="1F4E79")

        elif kind == "skill":
            k, cont = val
            if not (k or cont):
                continue
            p = new_p(after=1, line=1.35)
            if k:
                set_font(p.add_run(k + "："), 10.5, bold=True)
            if cont:
                set_font(p.add_run(cont), 10.5)

        elif kind == "edu":
            deg, major, time, rest = val
            p = new_p(after=1, line=1.35)
            add_right_tab(p, doc, 174)
            head = "  ".join(x for x in (deg, major) if x)
            set_font(p.add_run(head), 10.5, bold=bool(deg))
            if time:
                set_font(p.add_run("\t" + time), 9.5, color="555555")
            if rest:
                p2 = new_p(after=1, line=1.35)
                set_font(p2.add_run(rest), 9.5, color="555555")

        elif kind == "item":
            org = _first_text(val, "item-org")
            role = _first_text(val, "item-role")
            time = _first_text(val, "item-time")
            note = _first_text(val, "item-note")

            if org or role or time:
                p = new_p(before=6, after=2, line=1.3)
                add_right_tab(p, doc, 174)
                if org:
                    set_font(p.add_run(org), 10.5, bold=True)
                if role:
                    set_font(p.add_run("  " + role), 10.5, color="1F4E79")
                if time:
                    set_font(p.add_run("\t" + time), 9.5, color="555555")
            if note:
                p = new_p(after=2, line=1.3)
                set_font(p.add_run(note), 9.5, color="888888")

            for li in val.find_all("li"):
                t = li.text()
                if not t:
                    continue
                p = new_p(after=1, line=1.45)
                pf = p.paragraph_format
                pf.left_indent = Mm(5)
                pf.first_line_indent = Mm(-5)
                set_font(p.add_run("• "), 10.5)
                set_font(p.add_run(t), 10.5)

        elif kind == "para":
            p = new_p(after=2, line=1.4)
            set_font(p.add_run(val), 10.5)

    doc.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--person", help="people/ 下的姓名")
    ap.add_argument("--mode", default="final", choices=["draft", "final"])
    ap.add_argument("--target", default=None, help="定制版 yaml（相对该人目录）")
    ap.add_argument("--html", default=None, help="直接指定 HTML 文件")
    ap.add_argument("--out", default=None, help="输出 .docx 路径")
    args = ap.parse_args()

    if args.html:
        html_path = args.html
    elif args.person:
        if args.target:
            # 与 scripts/resume.py 的 render 命名保持一致：用定制版所在目录名
            tname = os.path.basename(os.path.dirname(args.target)) or "custom"
            html_path = os.path.join(PEOPLE, args.person, "output",
                                     "resume-%s-%s.html" % (tname, args.mode))
        else:
            html_path = os.path.join(PEOPLE, args.person, "output",
                                     "resume-%s.html" % args.mode)
    else:
        ap.error("需要 --html 或 --person")

    if not os.path.exists(html_path):
        sys.exit("找不到成稿 HTML：%s\n先跑：python scripts/resume.py render --person <姓名> [--target <定制版>] --mode %s"
                 % (html_path, args.mode))

    if args.out:
        out_path = args.out
    else:
        out_path = re.sub(r"\.html$", ".docx", html_path)

    with open(html_path, encoding="utf-8") as f:
        html_text = f.read()

    root = parse(html_text)
    pages = [n for n in root.find_all("div") if n.has("page")]
    if not pages:
        sys.exit("HTML 里找不到 .page 容器，渲染产物可能已损坏：%s" % html_path)

    # 只取第一个 .page 的子内容：分页 JS 会在运行时把内容重新分配到 page1/page2，
    # 但**原始 DOM 已经包含全部内容**，重复导出会造成内容翻倍。
    page = pages[0]

    build_docx(page, out_path)

    txt = page.text()
    print("[OK] 已生成：%s" % os.path.relpath(out_path, WORKSPACE))
    print("     来源：%s" % os.path.relpath(html_path, WORKSPACE))
    print("     字符数：%d（含标点，用于快速核对是否漏内容）" % len(txt))
    if args.mode == "final":
        for bad in ("母版", "出片模式", "待补", "待确认", "noprint"):
            if bad in txt and bad not in ("noprint",):
                print("     ⚠ 成稿里出现内部标注「%s」，投递前请检查" % bad)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成公众号「往期精选」SVG 横向滚动卡片墙

用法：
  python gen_featured.py featured_config.json featured_list.html
  python gen_featured.py featured_config.json --append 目标.html

配置格式（JSON）：
  {
    "title": "往期精选",
    "urls": ["https://mp.weixin.qq.com/s/xxx", ...]
  }

特性：
- 取配置中「最后」9 个链接（新链接往后加，取最新9篇）
- 封面图做卡片背景 + 半透明蒙版保证标题可读
- 3 行 × 每行 3 张，横向无缝滚动（参考微信 E2.COOL 卡片墙）
- 标题长度统一截断
- 爬取结果缓存到 featured_cache.json，避免重复抓取
"""
import argparse
import json
import os
import re
import sys
import urllib.request

VIEW_W = 677            # SVG 宽度（微信正文实际宽度）
CARD_W = 196            # 卡片宽
CARD_H = 92             # 卡片高
GAP = 8                 # 卡片间距
PAD_TOP = 96            # 顶部留白（标题区）
PAD_BOTTOM = 24         # 底部留白
ROWS = 3                # 行数
COLS = 3                # 每行卡片数
MAX_ITEMS = 9           # 最多取 9 篇
SWING = 26              # 每行摆动幅度（px），左右各留该余量防出界
BG_COLOR = "#1F2937"    # 备用深色背景
ACCENT = "#E8C877"      # 备用金色
TEXT_COLOR = "#FFFFFF"
SUB_COLOR = "#9CA3AF"
MASK_COLOR = "rgba(0,0,0,0.45)"  # 蒙版：封面图上加半透明黑
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.48"
CACHE_FILE = "featured_cache.json"  # 缓存文件（与配置同目录）


def load_cache(cache_path):
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(cache_path, cache):
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_article(url, timeout=10):
    """抓取微信文章标题+封面图（og:title / og:image）。

    安全策略：只抓短链接（https://mp.weixin.qq.com/s/xxx）。
    长链接（带 ?__biz= 等参数的分享追踪链接）不抓取。
    本地 HTML 文件直接用文件名当标题。
    返回 (title, cover_url) 或 (None, None)
    """
    # 本地 HTML 文件：文件名即标题，无封面
    if url.endswith(".html") and os.path.exists(url):
        base = os.path.basename(url)
        return os.path.splitext(base)[0], ""
    # 只允许短链接
    if not re.match(r'^https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+$', url):
        return None, None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        title = ""
        m = re.search(r'<meta property="og:title"\s+content="([^"]+)"', html)
        if m:
            title = m.group(1).strip()
        else:
            m = re.search(r'<title>(.*?)</title>', html, re.S)
            if m:
                title = m.group(1).strip().replace("\n", " ").replace("\r", " ")
        cover = ""
        m = re.search(r'<meta property="og:image"\s+content="([^"]+)"', html)
        if m:
            cover = m.group(1).strip()
        return title, cover
    except Exception:
        return None, None


def truncate(s, max_chars=20):
    """按显示宽度截断标题（中文算2，英文算1），加省略号"""
    s = s.strip()
    if not s:
        return s
    width = 0
    out = []
    for ch in s:
        w = 2 if ord(ch) > 0x2E80 else 1
        if width + w > max_chars * 2 - 1:
            out.append("…")
            break
        out.append(ch)
        width += w
    return "".join(out)


def split_title(s, max_per_line_chars=16):
    """把标题按显示宽度拆成最多 2 行（中文算2，英文算1），
    优先在标点（，。、！？；：—·空格）后断行，避免从中硬切。

    返回 (lines, is_two_rows)：
      lines: 拆行后的文本列表（最多2行）
      is_two_rows: 是否需要两行
    """
    s = s.strip()
    if not s:
        return [""], False
    # 单行能放下则直接单行
    single = truncate(s, max_chars=max_per_line_chars)
    if single == s:
        return [s], False

    def width_of(t):
        return sum(2 if ord(c) > 0x2E80 else 1 for c in t)

    limit = max_per_line_chars * 2 - 1  # 每行宽度上限（units）
    lines = []
    remaining = s
    for _ in range(2):
        if not remaining:
            break
        # 取第一行最大宽度内可容纳的文本
        acc = ""
        for ch in remaining:
            if width_of(acc + ch) > limit:
                break
            acc += ch
        if not acc:
            break
        # 在宽度限制内找最后一个标点位置（优先断在标点后）
        puncts = "，。、！？；：—·…（）()~-—_  "
        cut = len(acc)
        for i in range(len(acc) - 1, -1, -1):
            if acc[i] in puncts:
                cut = i + 1
                break
        # 断点太靠前（< 1/3 宽度）就放弃标点断行，按满宽度截
        if cut < len(acc) // 3:
            cut = len(acc)
        line = acc[:cut]
        lines.append(line)
        remaining = remaining[len(line):]
    if remaining:
        if lines:
            last = lines[-1]
            if last:
                lines[-1] = last[:-1] + "…"
            else:
                lines[-1] = "…"
        else:
            lines = ["…"]
    return lines, True


def esc(s):
    """XML 转义"""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


# 卡片无封面时的纯色底（按序号轮换颜色，本地演示也好看）
FALLBACK_COLORS = ["#3B4D61", "#4A3F5E", "#5E3A4A", "#3A5E4E", "#4D5E3A", "#5E4A3A",
                   "#394A6B", "#6B394A", "#4A6B39"]


def gen_card_inner(idx, title, cover, url):
    """生成一张卡片内容（0,0 基准）。

    采用参考文章 E2.COOL 超链接组件的官方结构：
    - foreignObject 内嵌 svg，封面用 CSS background-image 铺背景
    - CSS border-radius:10px 真正裁剪圆角（不是 image rx 的视觉欺骗）
    - 底部半透明黑条保证标题可读
    - 无封面时用纯色底
    """
    x, y = 0, 0
    R = 10
    effective_cover = cover
    if cover and not cover.startswith(("http://", "https://")):
        if not os.path.exists(cover):
            effective_cover = ""
    if effective_cover:
        bg_style = (f'display:block;width:100%;height:100%;border-radius:{R}px;'
                    f'background-image:url(\'{esc(effective_cover)}\');'
                    f'background-size:cover;background-position:center;')
    else:
        bg_style = (f'display:block;width:100%;height:100%;border-radius:{R}px;'
                    f'background-color:{FALLBACK_COLORS[idx % len(FALLBACK_COLORS)]};')
    # 标题智能换行：单行 or 双行
    lines, is_two = split_title(title)
    if is_two:
        # 双行：黑条加高，两行文字
        bar_h = 44
        bar_y = CARD_H - bar_h  # 48
        ts = ""
        for i, ln in enumerate(lines):
            ty = bar_y + 16 + i * 15
            ts += (f'<text x="8" y="{ty}" fill="{TEXT_COLOR}" font-size="11" font-weight="bold" '
                   f'font-family="-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Microsoft YaHei\',sans-serif">'
                   f'<tspan leaf="">{esc(ln)}</tspan></text>\n')
    else:
        # 单行：矮黑条，一行文字垂直居中
        bar_h = 30
        bar_y = CARD_H - bar_h  # 62
        ts = (f'<text x="8" y="{bar_y + 19}" fill="{TEXT_COLOR}" font-size="11" font-weight="bold" '
              f'font-family="-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Microsoft YaHei\',sans-serif">'
              f'<tspan leaf="">{esc(lines[0])}</tspan></text>\n')
    title_bar = f'<rect x="0" y="{bar_y}" width="{CARD_W}" height="{bar_h}" fill="#000000" opacity="0.5"/>'
    card = f'''<foreignObject x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}">
<svg style="{bg_style}" viewbox="0 0 {CARD_W} {CARD_H}" width="100%">
{title_bar}
{ts}<foreignObject x="0" y="0" width="{CARD_W}" height="{CARD_H}">
<a xmlns="http://www.w3.org/1999/xhtml" linktype="image" href="{esc(url)}" style="display:block;width:{CARD_W}px;height:{CARD_H}px;">
<svg style="pointer-events:visible" viewbox="0 0 {CARD_W} {CARD_H}" width="100%"></svg>
</a></foreignObject>
</svg></foreignObject>'''
    return card


def gen_card(idx, title, cover, url, x, y):
    """兼容旧接口：定位 + 内容（静态卡片，无节拍动画）"""
    return f'<g transform="translate({x},{y})">\n{gen_card_inner(idx, title, cover, url)}\n</g>'


def gen_svg(items, title_text):
    """items: [(标题, 封面, url), ...] 生成 3×3 横向滚动卡片墙"""
    n = len(items)
    if n == 0:
        return ""
    row_h = CARD_H
    view_w = VIEW_W
    view_h = PAD_TOP + ROWS * row_h + (ROWS - 1) * GAP + PAD_BOTTOM
    step = CARD_W + GAP
    dur = max(12, n * 2.5)

    rows_html = []
    # 每行一个组，行内3张卡片整齐排列（静态 transform 定位，间隙固定）；
    # 整行一个 animatetransform 做小幅左右错位摆动，行内永远整齐。
    # 三行 begin 负偏移不同 → 各行相位不同 → 整体"不整齐但有序"的动态。
    # 注意：列起始 x 从 SWING 开始（左右各留摆动余量，防止卡片摆出视口被裁切）
    for r in range(ROWS):
        # 本行3张卡片（静态定位，行内整齐）
        row_cards = []
        for c in range(COLS):
            idx = r * COLS + c
            if idx >= n:
                break
            title, cover, url = items[idx]
            x = SWING + c * step
            card = gen_card_inner(idx, title, cover, url)
            row_cards.append(f'<g transform="translate({x},0)">\n{card}\n</g>')
        row_cards_html = "\n".join(row_cards)

        base_y = PAD_TOP + r * (row_h + GAP)
        # begin 按 r 错开 1/3 周期：三行分别落在 右移/居中/左移 三个相位
        # （values 4 帧均分 dur，每帧 dur/3；负 begin 让加载瞬间三行位置不同）
        begin = f"{-dur * r / ROWS:.1f}s"
        # 小幅摆动：右移 → 回中 → 左移 → 回中（spline 缓动）
        values = f"{SWING} {base_y};0 {base_y};-{SWING} {base_y};0 {base_y}"
        rows_html.append(
            f'<g>\n'
            f'<animatetransform attributename="transform" type="translate" '
            f'repeatcount="indefinite" values="{values}" '
            f'fill="freeze" begin="{begin}" dur="{dur}s" '
            f'calcmode="spline" keysplines="0.8 0 0.2 1.0;0.8 0 0.2 1.0;0.8 0 0.2 1.0"/>'
            f'\n{row_cards_html}\n</g>'
        )
    rows_all = "\n".join(rows_html)

    running_text = f"{n} 篇精选 · 点击阅读"
    # 白底版：无深色背景框，标题用深色文字（公众号编辑器默认白色底）
    svg = f'''<section style="max-width:100%;margin:18px auto 8px;padding:0;">
<svg viewbox="0 0 {view_w} {view_h}" xmlns="http://www.w3.org/2000/svg">
<text x="0" y="40" fill="#333333" font-size="20" font-weight="bold" font-family="-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif" letter-spacing="1"><tspan leaf="">{esc(title_text)}</tspan></text>
<text x="0" y="62" fill="#9CA3AF" font-size="12" font-family="-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif"><tspan leaf="">{running_text}</tspan></text>
{rows_all}
</svg>
</section>'''
    return svg


def main():
    ap = argparse.ArgumentParser(description="生成公众号往期精选SVG卡片墙")
    ap.add_argument("config", help="配置文件路径 (JSON)")
    ap.add_argument("output", nargs="?", help="输出HTML路径")
    ap.add_argument("--append", metavar="TARGET", help="追加到目标HTML文件末尾")
    args = ap.parse_args()

    cfg_path = args.config
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    urls = cfg.get("urls", [])
    title_text = cfg.get("title", "往期精选")

    if not urls:
        print("错误：配置中无 urls")
        sys.exit(1)

    # 倒序取最新 9 篇（配置往后加，取最后 9 个）
    urls = urls[-MAX_ITEMS:]
    n = len(urls)

    # 缓存：同目录 featured_cache.json
    cache_dir = os.path.dirname(os.path.abspath(cfg_path))
    cache_path = os.path.join(cache_dir, CACHE_FILE)
    cache = load_cache(cache_path)

    # 收集 items
    items = []
    local = 0
    cached = 0
    fresh = 0
    fails = 0
    for i, entry in enumerate(urls):
        # 支持对象格式：{"url": "...", "cover": "..."} 或字符串
        if isinstance(entry, dict):
            url = entry.get("url", "").strip()
            manual_cover = entry.get("cover", "")
        else:
            url = str(entry).strip()
            manual_cover = ""
        if not url:
            continue
        key = url
        # 本地文件：文件名即标题，可指定封面图
        if url.endswith(".html") and os.path.exists(url):
            title, _ = fetch_article(url)
            cover = manual_cover if manual_cover else ""
            items.append((title, cover, url))
            local += 1
            print(f"  [{i+1}/{n}] [本地] {title[:30]}")
            continue
        if key in cache and cache[key].get("title"):
            title = cache[key]["title"]
            cover = cache[key].get("cover", "")
            if manual_cover:
                cover = manual_cover
            cached += 1
        else:
            title, cover = fetch_article(url)
            if title:
                cache[key] = {"title": title, "cover": cover}
                if manual_cover:
                    cover = manual_cover
                fresh += 1
            else:
                fails += 1
                m = re.search(r"sn=([a-f0-9]{6,8})", url)
                title = f"文章 {m.group(1)}" if m else "往期推荐"
                cover = manual_cover if manual_cover else ""
        items.append((title, cover, url))
        print(f"  [{i+1}/{n}] {title[:30]}")

    save_cache(cache_path, cache)
    print(f"统计: 本地 {local}, 缓存命中 {cached}, 新增抓取 {fresh}, 失败 {fails}")

    svg_html = gen_svg(items, title_text)
    if not svg_html:
        print("错误：生成的SVG为空")
        sys.exit(1)

    # 输出
    if args.append:
        with open(args.append, "r", encoding="utf-8") as f:
            target = f.read()
        pattern = re.compile(r'<!-- FEATURED-START -->.*?<!-- FEATURED-END -->', re.S)
        target = pattern.sub("", target)
        target = target.rstrip() + "\n\n<!-- FEATURED-START -->\n" + svg_html + "\n<!-- FEATURED-END -->\n"
        with open(args.append, "w", encoding="utf-8") as f:
            f.write(target)
        print(f"已追加到: {args.append}")
    else:
        out = args.output or "featured_list.html"
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg_html)
        print(f"已生成: {out}")


if __name__ == "__main__":
    main()
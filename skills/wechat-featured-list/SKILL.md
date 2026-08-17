---
name: wechat-featured-list
description: 生成公众号底部"往期精选"SVG卡片墙。当用户说"文章精选/往期精选/底部推荐"时触发。
version: 2.0.0
author: Hermes Agent
license: MIT
tags: [wechat, svg, featured, links, gzh]
related_skills:
  - wechat-svg
  - gzh-design
needs:
  - 配置文件（包含文章链接列表）
  - 目标HTML文件（追加精选列表用，可选）
composes_with:
  - wechat-svg
  - gzh-design
---

# 公众号「往期精选」SVG 卡片墙生成技能

## When to Use

用户写公众号文章，需要在底部加"往期精选/相关文章"墙时使用。用户只需提供文章链接，脚本自动抓标题+封面、生成 **白底 3×3 圆角卡片墙（三行错开小幅摆动）**，追加到文章 HTML 末尾。

## 工作流程

1. **配置**：`公众号/scripts/featured_config.json`（活跃配置，与运维脚本 `pool_maintain.py` 并列）写入链接列表；模板见本技能 `templates/featured_config.json`
2. **生成**：`python scripts/gen_featured.py [config路径] --append [目标.html]`（或输出独立HTML）
3. **验证**：脚本输出统计（本地/缓存/新增/失败）
4. **交付**：`--append` 自动加到文章末尾；独立文件则复制内容粘贴到文章底部

> ⚠️ 配置文件**不要放** `公众号/AI生成/`——那是文章成品目录。

## 配置文件格式

```json
{
  "title": "往期精选",
  "urls": [
    "https://mp.weixin.qq.com/s/oxFNBxRlXikGLmfI85C_Ag",
    {"url": "https://mp.weixin.qq.com/s/xxx", "cover": "https://mmbiz.qpic.cn/..."}
  ]
}
```

- `title`: 列表标题（可选，默认"往期精选"）
- `urls`: 支持两种元素：
  - **字符串** = 链接，自动抓取 og:title + og:image
  - **对象** = `{"url": "...", "cover": "..."}`，可手动指定封面（本地演示/无封面时用）
- 取**最后 9 篇**（配置往后加新链接，自动取最新 9 个）

⚠️ **安全策略：只放短链接**（`https://mp.weixin.qq.com/s/xxx`）。脚本只抓短链接；长链接（带 `?__biz=`、`chksm=` 参数的分享追踪链接）**跳过不抓**，避免微信风控封号（有封号风险）。长链接降级显示"文章 sn短码"。

## 生成脚本用法

```bash
# 生成独立 HTML 文件
python scripts/gen_featured.py featured_config.json featured_list.html

# 直接追加到文章 HTML 末尾（重复运行自动替换旧的精选区）
python scripts/gen_featured.py featured_config.json --append 文章.html
```

## 输出结构

```
<section>                    ← 外层包裹
  <svg viewbox="0 0 677 高">
    <text/>                   ← "往期精选"深灰标题 + "N篇精选·点击阅读"灰色副标题（白底深字）
    <g> × 3                   ← 3 行，整行一个 animatetransform 小幅摆动
      <animatetransform translate values="26 y;0 y;-26 y;0 y" begin="负偏移" .../>
      <g transform="translate(x,0)"> × 3   ← 行内 3 张卡片（静态定位，行内整齐）
        <foreignObject>            ← 卡片容器（0,0 基准）
          <svg style="background-image:url(封面); border-radius:10px; background-size:cover">
            <rect y=底部 fill=#000 opacity=0.5/>   ← 底部标题黑条（被 border-radius 裁圆角）
            <text/>                ← 白色加粗标题（智能换行 1~2 行）
            <foreignObject><a linktype="image">  ← 透明链接热区
          </svg>
        </foreignObject>
      </g>
    </g>
  </svg>
</section>
```

## 关键实现要点

### 白底视觉（v2 定稿）
- **整体白底，无背景框**（公众号编辑器默认白色）
- 标题用深灰 `#333333`，副标题灰色 `#9CA3AF`
- 卡片 = 封面圆角矩形直接悬浮白底上，**不要**在图片下叠加深色背景框

### 卡片圆角（CSS border-radius 渲染级裁剪）
```html
<foreignObject x="0" y="0" width="196" height="92">
  <svg style="display:block;width:100%;height:100%;border-radius:10px;
             background-image:url('封面');background-size:cover;background-position:center;"
       viewbox="0 0 196 92" width="100%">
```
- ⚠️ **不要用 `<image rx="10">`**：SVG image 的 rx 只是视觉裁剪，底边像素仍是方形，会透过半透明蒙版露出来（实测坑）
- ⚠️ **不要在图片四角盖背景色小矩形**：会显示成黑圈（实测坑）
- ✅ CSS `border-radius` + `background-image` 是**真正渲染级裁剪**，过微信实测

### 标题智能换行
- 短标题单行（底部黑条 30px 高），长标题两行（黑条 44px 高）
- **断行优先在标点后**（`，。、！？；：—·…空格`），找不到标点才按宽度切
- 两行放不下 → 第二行加省略号
- 字号 11px 加粗白字，覆盖黑条上

### 3×3 卡片墙（三行错开）
- **每行整行一个 `animatetransform`**（行内 3 张用静态 `translate(x,0)` 定位，行内永远整齐）
- values = `"26 行y;0 行y;-26 行y;0 行y"`（小幅左右摆动，不滑出视口）
- **begin 负偏移三档**：行0=`-0s`(右26)、行1=`-dur/3`(中0)、行2=`-2dur/3`(左-26) → 加载瞬间三行错开
- `dur = max(12, n*2.5)`，spline 缓动（`0.8 0 0.2 1.0`）
- **防裁切余量**：列起始 x = SWING(26) + c*step，卡片 196px、间距 8px，总宽 656 < 677（微信正文宽），左右各留 26px

### 标题+封面抓取（带缓存）
- 只抓短链接 `og:title` / `og:image`，失败降级 `<title>`
- 本地 HTML 文件直接用文件名当标题（cover 可在配置对象里手动指定）
- **缓存**：`featured_cache.json`（与配置同目录），URL → {title, cover}，重复运行命中缓存不请求

### 每行可点击（微信官方超链接组件）
```html
<foreignObject x="0" y="0" width="196" height="92">
<a xmlns="http://www.w3.org/1999/xhtml" linktype="image" href="URL"
   style="display:block;width:196px;height:92px;">
  <svg style="pointer-events:visible" viewbox="0 0 196 92" width="100%"></svg>
</a></foreignObject>
```

## 微信兼容性提醒（来自 wechat-svg 技能）

- 属性全小写：`viewbox`、`animatetransform`、`attributename`
- `foreignObject` 内嵌 `<a xmlns="http://www.w3.org/1999/xhtml" linktype="image">` 是 E2.COOL 官方做法，微信可用
- 禁用 `id`/`class`/`defs`/`clipPath` 依赖
- 文字节点用 `<tspan leaf="">` 包裹

## 排错

| 现象 | 原因 | 修法 |
|------|------|------|
| 卡片不摆动 | animatetransform 属性拼写错/驼峰 | 确认 `attributename="transform"` 全小写 |
| 图片方形角露出 | 用了 `<image rx>` 或蒙版半透明 | 改用 foreignObject+CSS background-image+border-radius |
| 四角黑圈 | 用背景色小矩形盖图片角 | 去掉盖板，用 CSS border-radius 裁剪 |
| 卡片摆出视口被裁 | 列 x 从 0 开始，无摆动余量 | 列 x = SWING + c*step，左右各留 26px |
| 标题中间硬切 | split 逻辑按宽度硬切 | 优先标点断行（`，。、！？——空格`） |
| 抓不到标题/封面 | 微信反爬/链接带参数 | 用短链接格式；缓存避免重复爬 |
| 取的篇数不对 | urls 顺序 | 固定取最后 9 篇，新链接往后加 |

## 常用参数速查

- 卡片：196×92px，圆角 `border-radius:10px`
- 三列 x：26 / 230 / 434（步进 204）
- 三行 y：96 / 196 / 296
- 摆动：±26px，dur 22.5s（9篇）

## 参考

- 参考文章底部 E2.COOL 超链接组件：`https://mp.weixin.qq.com/s/oxFNBxRlXikGLmfI85C_Ag`
- wechat-svg 技能（微信 SVG 兼容性铁律）
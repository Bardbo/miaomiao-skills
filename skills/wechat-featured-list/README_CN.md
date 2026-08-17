# 公众号往期精选卡片墙

<p align="center">
  <a href="../README.zh.md">🇨🇳 中文</a> · <a href="README.md">🇬🇧 English</a>
</p>

在公众号文章底部生成「往期精选」卡片墙。自动抓取标题和封面图，排成 3×3 网格，三行错开小幅摆动。

## 功能

- **自动抓取** — 给定文章链接，自动抓取标题（`og:title`）和封面图（`og:image`）
- **3×3 网格** — 9 篇文章排成 3 行 × 3 列
- **错开摆动** — 每行有 ±26px 的小幅水平摆动，三行相位不同，自然错落
- **圆角** — CSS `border-radius:10px` 真正裁剪圆角，无方形像素露出
- **智能换行** — 短标题单行，长标题换两行（优先在标点后断行）
- **标题可读** — 卡片底部半透明黑条 + 白色加粗标题
- **缓存** — 抓取的标题和封面缓存到本地，重复运行不重新请求
- **白底** — 干净白底，配公众号编辑器默认底色
- **可点击** — 每张卡片都是全区域可点击链接

## 安全

- **只爬短链接**（`https://mp.weixin.qq.com/s/xxx`）。长链接（带 `?__biz=`、`chksm=` 参数的分享追踪链接）**跳过不抓**，避免微信风控封号。
- **本地 HTML 文件** — 直接用文件名当标题，不发起网络请求。

## 使用方法

```bash
# 配置 JSON：把文章链接丢进 featured_config.json
# {"title": "往期精选", "urls": ["https://mp.weixin.qq.com/s/xxx", ...]}

# 生成独立 HTML
python scripts/gen_featured.py featured_config.json featured_list.html

# 或追加到已有文章 HTML 末尾
python scripts/gen_featured.py featured_config.json --append 文章.html
```

## 关于

由 [Bardbo](https://github.com/Bardbo) 基于 [Hermes Agent](https://hermes-agent.nousresearch.com) 构建。
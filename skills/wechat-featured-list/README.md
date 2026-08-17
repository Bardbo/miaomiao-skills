# 公众号往期精选卡片墙 · WeChat Featured Articles Card Wall

<p align="center">
  <a href="#readme">🇨🇳 中文</a> · <a href="README_EN.md">🇬🇧 English</a>
</p>

生成公众号文章底部的「往期精选」卡片墙。你把文章链接丢进去，脚本自动抓标题和封面，排成 3×3 圆角卡片墙，三行错开小幅摆动，白底适配公众号编辑器。

## 功能

- 自动抓取链接的标题（og:title）和封面图（og:image）
- 3 行 × 3 列共 9 篇，取配置里最后 9 篇（新链接往后加）
- 三行各自 ±26px 错开摆动，相位不同，动起来错落有致
- CSS border-radius 真正裁剪圆角，方形像素不会漏出
- 标题智能换行：短标题单行，长标题拆两行（优先在标点后断开）
- 底部半透明黑条保证白色标题在任何封面图上可读
- 抓取结果缓存到 featured_cache.json，重复运行不重新请求
- 白底，与公众号编辑器默认底色一致

## 使用

```bash
# 1. 配置链接（JSON）
# 新建 featured_config.json：
# {"title": "往期精选", "urls": ["https://mp.weixin.qq.com/s/xxx", ...]}

# 2. 生成独立 HTML
python scripts/gen_featured.py featured_config.json featured_list.html

# 或直接追加到文章 HTML 末尾
python scripts/gen_featured.py featured_config.json --append article.html
```

## 安全

- 只爬短链接（https://mp.weixin.qq.com/s/xxx）
- 长链接（带 ?__biz= 等参数的分享追踪链接）跳过不抓，避免微信风控
- 本地 HTML 文件直接用文件名当标题，不发网络请求

## About

Built with [Hermes Agent](https://hermes-agent.nousresearch.com) by [Bardbo](https://github.com/Bardbo).
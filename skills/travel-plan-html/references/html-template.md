# HTML 模板参考

## 完整的 HTML 结构参考

写好 Skill 后生成 HTML 时，直接参考以下结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>行程名称</title>
<style>
  /* CSS 变量 */
  :root {
    --primary: #8B5CF6;
    --primary-light: #EDE9FE;
  }
  /* 响应式布局，表格，卡片，时间线，标签样式 */
  /* 完整 CSS 参见已生成的云南7日逛吃之旅.html */
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <h1>🗺️ 行程标题</h1>
  <div class="meta">人数 · 房间 · 日期 · 预算</div>
</div>

<!-- Summary Bar -->
<div class="summary-bar">城市数 · 车次数 · 住宿晚数 · 必吃数</div>

<!-- 逐日卡片 -->
<div class="day-card">
  <div class="day-header day-colors-N">
    <div class="day-num">N</div>
    <div class="day-title">当天标题</div>
    <div class="day-date">日期</div>
  </div>
  <div class="day-body">
    <!-- Timeline -->
    <ul class="timeline">
      <li><span class="time">时间</span><div class="content">...</div></li>
    </ul>
    <!-- 酒店表格 -->
    <table class="info-table">...</table>
    <!-- 餐厅卡片 -->
    <div class="rest-card">...</div>
    <!-- 提示框 -->
    <div class="tip-box">...</div>
  </div>
</div>

<!-- 费用总表 -->
<div class="day-card" style="border: 2px solid var(--primary);">...</div>

<div class="footer">数据来源</div>

</body>
</html>
```

## 每天的颜色渐变

| Day | Class | 渐变 |
|-----|-------|------|
| 1 | `day-colors-1` | #6366F1 → #8B5CF6 (靛→紫) |
| 2 | `day-colors-2` | #EC4899 → #F43F5E (粉→红) |
| 3 | `day-colors-3` | #F59E0B → #F97316 (橙) |
| 4 | `day-colors-4` | #10B981 → #059669 (绿) |
| 5 | `day-colors-5` | #3B82F6 → #2563EB (蓝) |
| 6 | `day-colors-6` | #8B5CF6 → #6366F1 (紫→靛) |
| 7 | `day-colors-7` | #EF4444 → #DC2626 (红) |
| — | `day-colors-xhs` | #FF2442 → #FF6B81 (小红书红) |

> 如果行程超过7天，循环使用颜色

## 标签（tag）样式

```css
.tag-train { background: #EDE9FE; color: #7C3AED; }  /* 🚄 火车 */
.tag-hotel { background: #FEF3C7; color: #D97706; }   /* 🏨 酒店 */
.tag-food  { background: #FCE7F3; color: #EC4899; }    /* 🍜 美食 */
.tag-walk  { background: #D1FAE5; color: #059669; }    /* 🚶 步行 */
.tag-xhs   { background: #FFF0F0; color: #FF2442; }    /* 🫘 小红书 */
```

## 天气徽章（weather-badge）

放在每天 day-body 的顶部，紧跟在 day-header 下方：

```html
<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
  <span class="weather-badge" style="background:#DBEAFE;color:#1D4ED8;">🌧️ 小雨 19~23°C</span>
  <span style="font-size:12px;color:var(--text-light);">天气影响说明</span>
</div>
```

天气颜色规则：🔵 `#DBEAFE`(小雨/阴) · 🟡 `#FEF3C7`(多云) · 🔴 `#FEE2E2`(大雨)

**不要**在页面底部添加单独的天气总览卡片——天气信息已嵌入每一天。

## 跳转链接嵌入规则

每个车次、酒店、餐厅必须在时间线（timeline）项中嵌入可点击的链接，不能只放在表格里。

```html
<!-- 🚄 火车票链接 -->
<li><span class="time">09:13</span>
  <div class="content"><span class="tag tag-train">🚄</span> 
    <strong>D8693</strong> 昆明南站→楚雄站（¥8x/人）
    <a href="{jumpUrl}" target="_blank" style="color:#7C3AED;font-weight:600;text-decoration:none;">购票→</a>
  </div>
</li>

<!-- 🏨 酒店链接 -->
<li><span class="time">10:36</span>
  <div class="content"><span class="tag tag-hotel">🏨</span> 
    🚕10min→<a href="{detailUrl}" target="_blank" style="color:#D97706;font-weight:600;text-decoration:none;">酒店名</a>
  </div>
</li>

<!-- 🍜 美食链接（用高德搜索） -->
<li><span class="time">18:00</span>
  <div class="content"><span class="tag tag-food">🍄</span> 
    <a href="https://www.amap.com/search?query=餐厅名" target="_blank" style="color:#EC4899;font-weight:600;text-decoration:none;">餐厅名</a>
  </div>
</li>
```

链接颜色规则：🚄紫色 `#7C3AED` · 🏨黄色 `#D97706` · 🍜粉色 `#EC4899`

## 信息表格

酒店表列：`酒店名 | 星级 | 价格/间 | 飞猪预订`
车次表列：`车次 | 时间 | 用时 | 到达站 | 飞猪预订`

预订链接格式：
```html
<a href="{detailUrl}" target="_blank">预订→</a>
```

## 数据处理

`flyai` CLI 输出中的 `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)` 是 Windows 上 Node.js 的底层错误，不影响数据。处理方式：

```python
import json
raw = command_output
# 截取 Assertion 之前的有效 JSON
json_str = raw.split('Assertion')[0]
data = json.loads(json_str)
items = data.get('data', {}).get('itemList', [])
```

体验模式下价格字段如 `¥3xx`，原因标注即可。
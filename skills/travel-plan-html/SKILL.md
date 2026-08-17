---
name: travel-plan-html
display_name: "Travel Plan HTML Generator（云南逛吃版）"
description: "根据用户输入的旅行需求，调用飞猪FlyAI CLI查询实时价格，生成一份带酒店预订链接、火车票购票链接的完整HTML旅行规划文件。支持导入小红书笔记/链接，提取旅行灵感和图片。"
version: 2.0.0
metadata:
  hermes:
    tags: [travel, html, flyai, fliggy, trip-planning, xiaohongshu]
    category: productivity
---

# Travel Plan HTML Generator

根据用户的旅行需求（目的地、人数、日期、预算、口味偏好），自动：
1. 用 `flyai` CLI 查实时酒店和火车票价格（飞猪官方数据源）
2. 整合生成一份美观的 HTML 文件
3. 每个酒店/车次都附带可点击的飞猪预订链接

## 前置条件

需要安装 `flyai-cli`（npm 全局包）：
```bash
npm i -g @fly-ai/flyai-cli
```

## 用户偏好的格式风格（必须遵守）

### 每条信息都必须有可点击的跳转链接
- **火车票**：每条车次附带 `购票→` 链接（来源：FlyAI CLI 的 `jumpUrl`）
- **酒店**：每家酒店附带飞猪预订链接（来源：`detailUrl`）
- **美食**：每家餐厅附带高德搜索链接（`https://www.amap.com/search?query=餐厅名+城市`）
- 链接颜色规则：🚄 紫色 `#7C3AED` · 🏨 黄色 `#D97706` · 🍜 粉色 `#EC4899`
- 链接放在时间线（timeline）项中，而非仅放在表格中

### 天气信息嵌入每一天（不单独汇总）
- 不使用单独的天气总览卡片在页面底部
- 在每天的 day-header 下方显示天气徽章（weather-badge）
- 天气数据来源：`https://www.tianqi.com/{城市}/15/`（天气网15天预报）
- 天气徽章样式：🔵蓝色底(小雨) · 🟡黄色底(阴/多云) · 🔴红色底(大雨)
- 根据天气调整当日行程（如大雨天改室内活动）
- 出发前2天建议用户复查最新预报

### 飞猪 CLI 输出解析
Windows 上 `flyai` CLI 输出末尾可能混有 `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)`（Node.js 底层问题），不影响数据：
```python
json_str = raw_output.split('Assertion')[0]  # 截取有效 JSON
data = json.loads(json_str)
```
未配置 API Key 时价格显示为 `¥1xx`、`¥2xx` 等形式。

## 用户偏好的格式风格（必须遵守）

### 每条信息都必须有可点击的跳转链接
- **火车票**：每条车次附带 `购票→` 链接（来源：FlyAI CLI 的 `jumpUrl`）
- **酒店**：每家酒店附带飞猪预订链接（来源：`detailUrl`）
- **美食**：每家餐厅附带高德搜索链接（`https://www.amap.com/search?query=餐厅名+城市`）
- 链接颜色规则：🚄 紫色 `#7C3AED` · 🏨 黄色 `#D97706` · 🍜 粉色 `#EC4899`
- 链接放在时间线（timeline）项中，而非仅放在表格中

### 天气信息嵌入每一天（不单独汇总）
- 不使用单独的天气总览卡片在页面底部
- 在每天的 day-header 下方显示天气徽章（weather-badge）
- 天气数据来源：`https://www.tianqi.com/{城市}/15/`（天气网15天预报）
- 天气徽章样式：🔵蓝色底(小雨) · 🟡黄色底(阴/多云) · 🔴红色底(大雨)
- 根据天气调整当日行程（如大雨天改室内活动）
- 出发前2天建议用户复查最新预报

### 飞猪 CLI 输出解析
Windows 上 `flyai` CLI 输出末尾可能混有 `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)`（Node.js 底层问题），不影响数据：
```python
json_str = raw_output.split('Assertion')[0]  # 截取有效 JSON
data = json.loads(json_str)
```
未配置 API Key 时价格显示为 `¥1xx`、`¥2xx` 等形式。

## 核心工作流

### Step 1：收集用户需求

必须收集的信息：
- **出发地/目的地**（城市名）
- **人数** 和 **房间数**
- **日期范围**（几号到几号，每日行程安排）
- **预算**（每间房/每人/总预算）
- **口味偏好**（想吃什么特色美食）
- **特殊需求**（少景点多逛吃、中转方式等）

### Step 2：查询天气信息（天气网15天预报）

查询各城市在行程具体日期的天气预报：
```
访问 https://www.tianqi.com/{城市}/15/ 获取15天预报
```

提取每日数据（天气状况 + 温度范围），嵌入到对应日期的卡片中。
根据天气调整行程：大雨天建议室内活动（市场/咖啡馆），小雨不影响户外。

### Step 3：使用 FlyAI CLI 查询实时数据

**查询酒店**：
```bash
flyai search-hotel \
  --dest-name "<城市>" \
  --check-in-date <YYYY-MM-DD> \
  --check-out-date <YYYY-MM-DD> \
  --hotel-bed-types "双床房" \
  --max-price <预算上限>
```

**查询火车票**：
```bash
flyai search-train \
  --origin "<出发城市>" \
  --destination "<到达城市>" \
  --dep-date <YYYY-MM-DD> \
  --seat-class-name "second class"
```

**查询餐馆/POI**（可选）：
```bash
flyai search-poi \
  --dest-name "<城市>" \
  --key-words "<美食关键词>"
```

> ⚠️ 飞猪体验模式下价格显示为 `¥1xx`、`¥2xx` 等形式。获取正式 API Key 可看到精确价格。

### 可选：生成高德行程地图

使用高德LBS Skill的旅行规划API，生成可视化地图：

```python
import urllib.parse, json

# 构建POI和路线数据
trip_data = [
    {"type": "poi", "lnglat": [经度, 纬度], "sort": "分类", "text": "名称", "remark": "描述"},
    {"type": "route", "routeType": "driving", "start": [经度, 纬度], "end": [经度, 纬度], "remark": "路线描述"},
]

# 编码生成URL
json_str = json.dumps(trip_data, ensure_ascii=False)
encoded = urllib.parse.quote(json_str)
map_url = f"https://a.amap.com/jsapi_demo_show/static/openclaw/travel_plan.html?data={encoded}"
```

然后在HTML中插入 iframe：
```html
<iframe src="{map_url}" width="100%" height="450" style="border:none;" allowfullscreen loading="lazy"></iframe>
```

同时生成各城市的高德搜索直达按钮：
```html
<a href="https://www.amap.com/search?query={关键词}" target="_blank">搜索按钮</a>
```

### 可选：从小红书导入旅行灵感

支持从小红书笔记中提取旅行灵感，包括景点推荐、餐厅推荐、路线建议和图片。

### ⚠️ 重要：信息真实性规则

旅行攻略必须保证信息准确，不能编造：
1. **不允许编造具体店名、价格、营业时间** — 除非从可访问的原文中提取
2. **小红书笔记如果打不开（404/被屏蔽），不能脑补内容**
3. **只能用搜索结果的标题作为参考**，标注「具体信息建议自行在小红书确认」
4. **酒店和火车票必须用 flyai CLI 实时查询**，获取带跳转链接的真实数据
5. **所有推荐标注来源**：🫘 小红书参考 / 🚄 飞猪实时 / 🍜 通用推荐
6. **宁缺毋滥** — 不确定的信息就不写

## 飞猪 CLI 使用要点

### 输出解析
Windows 上 `flyai` CLI 输出末尾可能混有 `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)`，截取处理：
```python
import json
raw = command_output
json_str = raw.split('Assertion')[0]
data = json.loads(json_str)
```

### 查询酒店
```bash
flyai search-hotel --dest-name "<城市>" --check-in-date <YYYY-MM-DD> --check-out-date <YYYY-MM-DD> --max-price <预算上限>
```
关键字段：`name`, `price`, `star`, `detailUrl`（飞猪预订链接）
体验模式下价格显示 `¥1xx`、`¥2xx` 等形式，标注即可。

### 查询火车票
```bash
flyai search-train --origin "<出发城市>" --destination "<到达城市>" --dep-date <YYYY-MM-DD> --seat-class-name "二等座"
```
关键字段：`journeys[0].segments[0]`（含 `trainNumber`, `depDateTime`, `arrDateTime`）, `price`, `jumpUrl`（购票链接）
注意：不指定座型时可能返回飞机票（transportType=飞机），需用 `--seat-class-name "二等座"` 过滤。

### 查询餐馆/POI（可选）
```bash
flyai search-poi --dest-name "<城市>" --key-words "<美食关键词>"
```

## 高德地图集成

在 HTML 中插入行程地图 iframe：

1. 构建各城市的 POI 坐标（lnglat）和路线数据
2. 编码成 URL 参数
3. 嵌入 `https://a.amap.com/jsapi_demo_show/static/openclaw/travel_plan.html?data=...`
4. 附带各城市的高德搜索直达按钮

## 链接嵌入规则

每条信息都要有可点击的跳转链接，颜色规则：
- 🚄 火车票 → `#7C3AED`（紫色）
- 🏨 酒店 → `#D97706`（金色）
- 🍜 美食 → `#EC4899`（粉色）
- 🫘 小红书 → `#FF2442`（小红书红，display:inline-block button 样式）

小红书的链接格式：`https://www.xiaohongshu.com/search_result?keyword={关键词}`（搜索结果页，不需要登录也能访问）

#### 方式 A：导入小红书笔记链接

用户提供小红书笔记 URL，从中提取旅行信息：

```
https://www.xiaohongshu.com/explore/{note_id}
```

提取策略（按优先级试）：
1. **OpenCLI 适配器**（最优）：`opencli xiaohongshu note {note_id}` — 返回结构化数据（标题、标签、正文、图片列表）
2. **BrowserAct 浏览器**（备选）：打开链接，提取页面内容
3. **Hermes 内置浏览器**（兜底）：`browser_navigate` → `browser_snapshot`

提取的关键字段：
- 笔记标题（如「大理4天3夜人均800攻略」）
- 正文内容中的景点/餐厅/路线描述
- 图片 URL（游记中的实拍图）
- 标签/话题（#大理旅游 #小众打卡）

提取后自动整合到旅行计划中：
- 标注 "🫘 小红书推荐" 来源标签
- 在对应日期的 timeline 中插入小红书推荐的景点/餐厅
- 引用小红书图片（添加来源标注）

#### 方式 B：搜索小红书旅行笔记

用户提供「目的地 + 关键词」，搜索相关笔记：

```bash
# 通过 OpenCLI 搜索
opencli xiaohongshu search "大理 旅游攻略" --limit 10 -f json

# 或通过 OpenCLI 获取热门
opencli xiaohongshu note --hot --limit 5 -f json
```

搜索结果处理：
1. 精选高赞/高收藏的笔记
2. 提取笔记中的实用信息（景点名、营业时间、避坑提示）
3. 汇总成「小红书推荐清单」加入 HTML 底部
4. 标注每条推荐对应的笔记链接

#### 方式 C：用户直接贴小红书的图片

用户提供小红书图片链接或本地的截图，执行：
1. 用 OCR 工具提取图中文字（店铺名、地址、营业时间等）
2. 用 vision_analyze 识别图片内容
3. 提取的信息自动填入行程

#### 小红书数据在 HTML 中的展示

- 小红书引入的推荐用 🫘 标签标记，颜色 `#FF2442`（小红书品牌红）
- 每条推荐附带笔记链接（`<a href="..." target="_blank" style="color:#FF2442;">查看原文→</a>`）
- 在页面底部添加「灵感来源」区块，列出所有引用的小红书笔记
- 小红书图片用 `lazy loading` 加载，宽高比保持原图比例

#### 前置条件

- OpenCLI 已安装并配置 Chrome 扩展
- 小红书平台需要在 Chrome 中已登录
- OpenCLI 适配器策略为 PUBLIC（无需登录可搜索），但查看笔记详情需要登录态

### Step 3：生成 HTML 文件

HTML 模板结构（配色、卡片布局参考下方）：

- **Header**：渐变背景，显示行程标题、日期、人数
- **Summary Bar**：显示城市数、车次数、住宿晚数
- **Day Cards**（逐日排列）：
  - 每天不同颜色（紫/粉/橙/绿/蓝/靛/红）
  - 时间线（timeline）展示当日行程
  - 信息表格展示酒店（含预订链接）
  - 餐厅卡片（含具体名称地址）
  - 提示/警告框（注意事项）

- **费用总表**：紫色边框卡片，汇总所有支出
- **Footer**：数据来源标注

### Step 4：保存并提示用户

文件保存到桌面：`用户桌面/<行程名称>.html`

提示用户双击打开即可查看，并给出几条立即要做的事项（订酒店、候补火车票等）。

## HTML 设计要点

### 配色方案
- 背景文字色：#1F2937 / #6B7280
- 卡片阴影：0 1px 3px rgba(0,0,0,0.06)
- 每天渐变色：参见 SKILL.md 中 day-colors-1~7 class
- 标签(tag)：紫色（火车）、黄色（酒店）、粉色（美食）、绿色（步行）
- 提示框：蓝色背景（技巧）、红色背景（警告）

### 表格列
酒店表：酒店名 | 星级 | 价格/间 | 飞猪预订（链接）
车次表：车次 | 时间 | 用时 | 到达站 | 飞猪预订（链接）

### 预订链接
每个酒店和车次都附带 `detailUrl` 或 `jumpUrl` 作为 `href`，用 `<a href="..." target="_blank">预订→</a>` 格式

## 文件写入路径
```python
desktop = "用户桌面路径"
filename = f"{行程名称}.html"
path = f"{desktop}\\{filename}"
```

## 注意事项
1. `flyai` CLI 输出中可能混有 `Assertion failed` 等 Node.js 底层错误，需要用 `.split('Assertion')[0]` 截取有效 JSON
2. 体验模式下价格不精确，标注"体验模式"提示
3. C396（楚雄→普洱）这类班次少的线路要特别提醒用户提前候补
4. 返回的 `detailUrl` / `jumpUrl` 是从飞猪拿到的真实预订链接，可以直接嵌入 HTML
5. 对于普洱→昆明这类终点站问题，注意区分"昆明站"和"昆明南站"
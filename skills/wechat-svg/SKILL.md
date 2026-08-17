---
name: wechat-svg
description: 生成公众号可粘贴的交互式SVG动画代码。当用户说砸金蛋/刮刮卡/点击交互/SVG动画/序列帧/错层滑动时触发。
version: 1.0.0
author: Hermes
license: MIT
tags: [wechat, svg, animation, interaction, gzh]
related_skills:
  - gzh-design
  - wechat-article-formatting
needs:
  - 需求描述（交互类型 + 内容 + 视觉风格）
  - 参考素材（可选：图片URL、配色方案）
composes_with:
  - gzh-design
  - wechat-article-formatting
---

# 公众号 SVG 交互图文生成技能

## When to Use

当用户需要为公众号文章生成**交互式 SVG 动画**时使用本技能。触发场景：
- 用户说「做个SVG」「公众号交互」「砸金蛋」「刮刮卡」「翻页卡片」「点击揭秘」「SVG动画」「序列帧」「错层滑动」「进度条动画」
- 用户想给公众号文章加互动效果（点击触发、自动动画、抽奖、游戏化交互）
- 用户描述一个交互需求，想要可直接粘贴到公众号的 SVG 代码

不用于：普通网页 SVG、静态图标、非公众号场景的矢量图形。

> 基于 763 个真实公众号 SVG 交互案例（1.2MB 样本代码）分析提炼，覆盖 E2.COOL 黑科技编辑器主流交互模式。

## 微信 SVG 兼容性铁律（实战验证，E2.COOL + CozeSkill 双重确认）

> 以下规则来自 E2.COOL 黑科技编辑器官方教程（已发布公众号案例）和 CozeSkill 实战验证，踩坑总结。

### 关键：SVG 标签上不要写 style 属性

这是最容易忽略的坑。微信编辑器在粘贴时，如果 `<svg>` 标签上带有 `style` 属性，可能会把 SVG 当作普通 HTML 块处理，导致内部的 `<animate>` 动画元素被过滤。

**错误写法：**
```svg
<svg viewbox="..." xmlns="...">
```

**正确写法：** 把 style 移到外层 `<section>` 包裹层：
```html
<section style="max-width:100%;margin:16px auto;text-align:center;">
  <svg viewbox="..." xmlns="...">
    ...
  </svg>
</section>
```

### 关键：属性名和标签名必须全小写

微信的 SVG 解析器只认全小写属性名和标签名。E2.COOL 官方教程（71 处 `attributename`、134 处 `animatetransform`）全部用全小写。

| 项目 | 驼峰（❌ 微信不支持） | 全小写（✅ 微信支持） |
|:---|:---|:---|
| 属性名 | `attributename="opacity"` | `attributename="opacity"` |
| 标签名 | `<animateTransform>` | `<animatetransform>` |
| viewBox | `viewBox` | `viewbox` |
| repeatCount | `repeatCount` | `repeatcount` |
| calcMode | `calcMode` | `calcmode` |
| keyTimes | `keyTimes` | `keytimes` |
| keySplines | `keySplines` | `keysplines` |

### 触发事件：begin="mousedown" 或 begin="mousedown"

两者在微信中均验证可用。E2.COOL 官方教程用 `begin="mousedown"`，CozeSkill 实战用 `begin="mousedown"`。建议统一用 `begin="mousedown"` 与 E2.COOL 保持一致。

### 自闭合标签

微信编辑器对 `<animate />` 自闭合标签支持良好，不需要写单独的结束标签。

### ✅ 可以使用的技术

| 技术 | 用法 | 案例数 |
|------|------|:------:|
| `<animate>` | 透明度/颜色/尺寸动画 | 153 |
| `<animatetransform>` | 位移/缩放/旋转动画（全小写） | 124 |
| `begin="mousedown"` | 点击触发（E2.COOL 官方使用） | — |
| `fill="freeze"` | 动画结束后保持最终状态 | 153 |
| `restart="never"` | 一次性触发，不重复 | 59 |
| `repeatcount` | 循环动画（进度条、光标闪烁，全小写） | 114 |
| `keytimes` + `keysplines` | 动画曲线控制（全小写） | 158 |
| `calcmode="spline"` | 更精细的动画曲线（全小写） | 73 |
| `values="..."` | 关键帧数值序列 | 277 |
| `<tspan leaf="">` | SVG 文字节点包裹 | — |

### ❌ 禁用边界（不支持的写法）

- **JavaScript** — `<script>`、`onclick`、`onmouseover` 全部失效
- **CSS 动画** — `@keyframes`、`transition`、`animation` 全部失效
- **`id` / `class`** — 全部禁用，不用 `url(#id)` 引用
- **`begin="elementId.event"`** — 不支持通过元素ID引用事件，如 `begin="s.mousedown"` 在微信中无效
- **`href` / `xlink:href`** — 禁用作为样式/结构依赖；`set href="#id"` 引用其他元素也无效
- **`defs`** — 禁用（marker 箭头、渐变、clipPath 依赖都会失效）
- **`foreignObject`** — 兼容性差，文字错位
- **`embed`** — 禁用
- **clipPath 裁剪图片** — 图片圆角会溢出

### ⚠️ 注意

- **图片圆角**：不能用 `clipPath` 裁圆角，用 `pattern` 方式：先定义 `<pattern>` 内含 `<rect rx="...">`，再填充圆角矩形
- **静态图表（Mermaid 等）**：
  - 箭头消失 → `<defs>`+`<marker>`+`url(#id)` 被过滤，将 marker 展开为内联 `<path>`/`<polygon>`，移除 `marker-end`
  - 图表过大 → `width="100%"` 被忽略按 viewBox 1:1 渲染，设置显式像素 `width`/`height` 并保留 `viewBox`
  - 文字错位 → `foreignObject` 兼容性差，转为 `<text>`/`<tspan>`
- **交互统一**：所有交互动画统一 `begin="mousedown"` + `fill="freeze"` + `restart="never"`，删除所有旧 `touchend;mouseup` 回位链，全链统一
- **动画顺序**：用 `begin="click; click+0.3s"` 实现序列动画

## ⚠️ 关键行为差异：`set` vs `animate` 的事件监听机制

这是微信SVG中最容易被忽略的核心差异，直接影响多层交互的正确性。

| 元素 | `begin="mousedown"` 监听目标 | 行为 |
|------|---------------------------|------|
| `set` | **父元素**（局部） | 事件必须到达 `set` 的父元素才能触发 |
| `animate` | **SVG 根元素**（全局） | SVG 内任意点击都能触发 |
| `animatetransform` | **SVG 根元素**（全局） | SVG 内任意点击都能触发 |

**实战验证：** 在"翻牌子"多目标交互（10块牌子各自对应不同肖像）中，`set attributename="visibility"` 在父子结构下只响应被点击元素自身的事件冒泡，而 `animate attributename="opacity"` 在同一结构下响应 SVG 内任意点击。这意味着：

- **`set` 用于控制 visibility 时，只能影响被点击元素自身**，无法通过全局事件控制其他兄弟元素
- **`animate` 用于控制 opacity 时，可以影响所有同类型元素**，因为监听 SVG 根

### 影响：多目标点击交互的限制

如果你需要实现"点击A → 隐藏B，点击B → 隐藏A"这种互斥切换（"翻牌子"类交互：点击不同卡片显示不同内容，且不依赖点击顺序），**微信SVG有天然限制**：

1. 点击卡片B时，无法触发卡片A的 `set visibility="hidden"`（因为 `set` 是局部监听）
2. 卡片A的 `animate` 虽然会触发，但 `visibility` 仍为 `visible`
3. 如果两个卡片的内容都可见，DOM顺序决定谁在上层（后渲染的覆盖前面）

**但可以做到顺序点击切换**（按DOM顺序从前往后翻）：用父子结构（肖像组为父级 `visibility="hidden"`，卡片组为子级 `visibility="visible"`），点击卡片 → 事件冒泡到父级肖像组 → `set to="visible"` 显示肖像，卡片组 `set to="hidden"` 隐藏卡片。因为DOM顺序靠后的肖像渲染在更上层，所以后点击的牌子能正确显示在顶层。已验证：10块牌子的顺序翻牌全部正常。

**无法做到无顺序依赖的互斥**（即"点谁谁置顶，不依赖点击顺序"）：因为点击靠前的牌子时，无法隐藏DOM顺序靠后的、已显示的肖像。

**可行的替代方案：**
- **顺序翻牌**（v12父子结构）：按DOM顺序点击，每个牌子正常显示对应肖像
- **单次触发式交互**（砸金蛋、刮刮卡、翻页）：每个卡片只触发一次，不依赖隐藏其他内容
- **简单两状态切换**：用 `animate` 控制 opacity（全局），`set` 控制 visibility（局部），配合 `keytimes` 时序

### 验证过但微信不支持的方案

| 方案 | 浏览器表现 | 微信表现 | 原因 |
|------|-----------|---------|------|
| `begin="s.mousedown"`（id引用） | ✅ 全局触发 | ❌ 不触发 | 微信不支持 `begin="elementId.event"` 语法 |
| `set href="#id" to="hidden"` | ✅ 跨元素控制 | ❌ 不触发 | 微信不支持 `set` 的 `href` 属性引用 |
| 兄弟结构（平级`g`） | ✅ 各触发各的 | ❌ 所有同时触发 | `animate` 全局监听 SVG 根 |

**总结：`begin="mousedown"` 在微信中，`animate` 总是全局触发，`set` 总是局部触发**，不因 DOM 结构变化而改变。

## 五大交互模式

### 模式一：点击触发动画（Click-to-Animate）

最常用的交互模式，点击后触发元素的状态变化。

**核心结构：**
```svg
<g>
  <!-- 点击后隐藏的初始状态 -->
  <rect ...>
    <animate attributename="opacity" begin="mousedown" dur="0.2s" 
             fill="freeze" restart="never" values="1;0"/>
  </rect>
  <!-- 点击后显示的最终状态 -->
  <rect opacity="0" ...>
    <animate attributename="opacity" begin="mousedown" dur="0.2s" 
             fill="freeze" restart="never" values="0;1"/>
  </rect>
</g>
```

**典型应用：** 砸金蛋、刮刮卡、翻页卡片、点击揭秘、点击展开/收缩

**参数说明：**
- `begin="mousedown"` — 点击时触发（微信唯一可靠的点击事件）
- `dur="0.2s"` — 动画时长
- `fill="freeze"` — 保持最终状态
- `restart="never"` — 仅触发一次
- `values="1;0"` — 从 1 到 0 的透明度变化

### 模式二：点击位移（Click-to-Fly-Out）

元素点击后飞出屏幕，用于消失/切换效果。

**核心结构：**
```svg
<g>
  <animatetransform attributename="transform" begin="mousedown" dur="0.01s" 
                    fill="freeze" restart="never" type="translate" 
                    values="0 0;2000 0"/>
  <!-- 原始元素内容 -->
  <rect .../>
  <text ...><tspan leaf="">文字</tspan></text>
</g>
```

**变体：**
- 飞入：`values="-2000 0;0 0"`（从左侧飞入）
- 上移消失：`values="0 0;0 -2000"`
- 缩放消失：用 `type="scale"` + `values="1;0"`

### 模式三：脉冲/闪烁动画（Auto-Animation）

无需交互，自动循环的动画效果。

**核心结构：**
```svg
<circle ...>
  <animate attributename="opacity" begin="0s" dur="1.5s" 
           repeatcount="indefinite" values="0.3;1;0.3" 
           keytimes="0;0.5;1" keysplines="0.4 0 0.6 1;0.4 0 0.6 1" 
           calcmode="spline"/>
</circle>
```

**典型应用：** 光标闪烁、脉冲按钮、呼吸灯、进度条动画

### 模式四：序列帧动画（Sequence Animation）

多个元素按顺序依次出现或变化，常用于展示流程、步骤、列表。

**核心结构：**
```svg
<g>
  <!-- 步骤 1：立即出现 -->
  <rect opacity="0" ...>
    <animate attributename="opacity" begin="0s" dur="0.5s" fill="freeze" values="0;1"/>
  </rect>
  <!-- 步骤 2：延迟 0.3s 后出现 -->
  <rect opacity="0" ...>
    <animate attributename="opacity" begin="1s" dur="0.5s" fill="freeze" values="0;1"/>
  </rect>
  <!-- 步骤 3：延迟 0.6s -->
  <rect opacity="0" ...>
    <animate attributename="opacity" begin="2s" dur="0.5s" fill="freeze" values="0;1"/>
  </rect>
</g>
```

**变体：** 点击序列用 `begin="click; click+0.3s; click+0.6s"`

### 模式五：复杂动画曲线（Spline Animation）

使用 `calcmode="spline"` + `keySplines` 实现更自然的缓动效果。

```svg
<rect ...>
  <animatetransform attributename="transform" begin="0s" dur="0.8s" 
                    fill="freeze" type="translate" 
                    values="-200 0;0 0;10 0;-5 0;0 0" 
                    keytimes="0;0.6;0.8;0.95;1" 
                    keysplines="0.2 0 0.4 1;0.2 0 0.4 1;0.4 0 0.6 1;0.2 0 0.4 1" 
                    calcmode="spline"/>
</rect>
```

## 模板库

### 模板 1：砸金蛋（9 个金蛋，点击碎裂）

```svg
<svg viewbox="0 0 750 980" xmlns="http://www.w3.org/2000/svg">
  <rect fill="#1a1a2e" width="750" height="980"/>
  <text fill="#fbbf24" font-size="48" font-weight="bold" text-anchor="middle" x="375" y="90">
    <tspan leaf="">点击砸蛋</tspan>
  </text>
  <text fill="#ffd700" font-size="24" opacity="0.8" text-anchor="middle" x="375" y="135">
    <tspan leaf="">好运等你来</tspan>
  </text>
  <!-- 金蛋 1：点击飞走，显示奖品 -->
  <g transform="translate(175, 340)">
    <animatetransform attributename="transform" begin="mousedown" dur="0.01s" fill="freeze" restart="never" type="translate" values="0 0;2000 0"/>
    <ellipse fill="#fbbf24" rx="80" ry="95"/>
    <ellipse fill="#f59e0b" rx="60" ry="75"/>
    <text fill="#fff" font-size="20" text-anchor="middle" x="0" y="8"><tspan leaf="">敲</tspan></text>
  </g>
  <g transform="translate(175, 340)" opacity="0">
    <animate attributename="opacity" begin="mousedown" dur="0.3s" fill="freeze" restart="never" values="0;1"/>
    <rect fill="#ff6b6b" width="140" height="70" rx="12" x="-70" y="-35"/>
    <text fill="#fff" font-size="22" font-weight="bold" text-anchor="middle" x="0" y="5"><tspan leaf="">🎁 大奖</tspan></text>
    <text fill="#fff" font-size="16" opacity="0.9" text-anchor="middle" x="0" y="28"><tspan leaf="">iPhone 15</tspan></text>
  </g>
  <!-- 重复以上 g 结构，共 9 个金蛋，分布在 3x3 网格: (175,340)(375,340)(575,340)(175,550)(375,550)(575,550)(175,760)(375,760)(575,760) -->
</svg>
```

### 模板 2：刮刮卡（点击擦除涂层）

```svg
<svg viewbox="0 0 500 400" xmlns="http://www.w3.org/2000/svg">
  <rect fill="#fff" width="500" height="400" rx="16"/>
  <text fill="#ff6b6b" font-size="36" font-weight="bold" text-anchor="middle" x="250" y="200">
    <tspan leaf="">🎉 一等奖</tspan>
  </text>
  <text fill="#666" font-size="20" text-anchor="middle" x="250" y="240">
    <tspan leaf="">iPhone 15 Pro Max</tspan>
  </text>
  <!-- 涂层 -->
  <rect fill="#ddd" width="500" height="400" rx="16">
    <animate attributename="opacity" begin="mousedown" dur="0.5s" fill="freeze" restart="never" values="1;0"/>
  </rect>
  <text fill="#999" font-size="24" text-anchor="middle" x="250" y="200">
    <tspan leaf="">👆 刮开查看</tspan>
  </text>
</svg>
```

### 模板 3：点击翻页/翻转卡片

```svg
<svg viewbox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
  <g>
    <animate attributename="opacity" begin="mousedown" dur="0.3s" fill="freeze" restart="never" values="1;0"/>
    <rect fill="#7C3AED" width="400" height="300" rx="16"/>
    <text fill="#fff" font-size="24" font-weight="bold" text-anchor="middle" x="200" y="160"><tspan leaf="">点击翻页</tspan></text>
  </g>
  <g opacity="0">
    <animate attributename="opacity" begin="mousedown" dur="0.3s" fill="freeze" restart="never" values="0;1"/>
    <rect fill="#06B6D4" width="400" height="300" rx="16"/>
    <text fill="#fff" font-size="24" text-anchor="middle" x="200" y="160"><tspan leaf="">翻页成功！</tspan></text>
  </g>
</svg>
```

### 模板 4：脉冲/呼吸按钮

```svg
<svg viewbox="0 0 300 100" xmlns="http://www.w3.org/2000/svg">
  <rect fill="#7C3AED" width="280" height="60" rx="30" x="10" y="20">
    <animate attributename="opacity" begin="0s" dur="1.5s" repeatcount="indefinite" 
             values="0.6;1;0.6" keytimes="0;0.5;1" keysplines="0.4 0 0.6 1;0.4 0 0.6 1" calcmode="spline"/>
  </rect>
  <text fill="#fff" font-size="20" font-weight="bold" text-anchor="middle" x="150" y="60">
    <tspan leaf="">点 击 体 验</tspan>
  </text>
</svg>
```

### 模板 5：进度条动画

```svg
<svg viewbox="0 0 500 40" xmlns="http://www.w3.org/2000/svg">
  <rect fill="#E5E7EB" width="480" height="24" rx="12" x="10" y="8"/>
  <rect fill="#7C3AED" width="0" height="24" rx="12" x="10" y="8">
    <animate attributename="width" begin="0s" dur="2s" fill="freeze" values="0;432" 
             keytimes="0;1" keysplines="0.4 0 0.2 1" calcmode="spline"/>
  </rect>
  <text fill="#fff" font-size="14" font-weight="bold" text-anchor="middle" x="250" y="25"><tspan leaf="">加载中...</tspan></text>
</svg>
```

### 模板 6：错层滑动

```svg
<svg viewbox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <rect fill="#8B5CF6" width="560" height="360" rx="16" x="20" y="20"/>
  <text fill="#fff" font-size="20" text-anchor="middle" x="300" y="210"><tspan leaf="">底层内容</tspan></text>
  <g>
    <animatetransform attributename="transform" begin="mousedown" dur="0.6s" fill="freeze" restart="never" 
                      type="translate" values="0 0;-200 0" 
                      keytimes="0;1" keysplines="0.4 0 0.2 1" calcmode="spline"/>
    <rect fill="#F59E0B" width="560" height="360" rx="16" x="20" y="20"/>
    <text fill="#fff" font-size="20" text-anchor="middle" x="300" y="210"><tspan leaf="">👆 滑动查看</tspan></text>
  </g>
</svg>
```

### 模板 7：序列帧依次出现

```svg
<svg viewbox="0 0 500 400" xmlns="http://www.w3.org/2000/svg">
  <rect fill="#1E293B" width="500" height="400" rx="12"/>
  <g>
    <animate attributename="opacity" begin="0s" dur="0.4s" fill="freeze" values="0;1"/>
    <rect fill="#7C3AED" width="440" height="50" rx="8" x="30" y="30"/>
    <text fill="#fff" font-size="16" x="50" y="62"><tspan leaf="">步骤一：数据采集</tspan></text>
  </g>
  <g opacity="0">
    <animate attributename="opacity" begin="0.3s" dur="0.4s" fill="freeze" values="0;1"/>
    <rect fill="#7C3AED" width="440" height="50" rx="8" x="30" y="100"/>
    <text fill="#fff" font-size="16" x="50" y="132"><tspan leaf="">步骤二：AI 处理</tspan></text>
  </g>
  <g opacity="0">
    <animate attributename="opacity" begin="0.6s" dur="0.4s" fill="freeze" values="0;1"/>
    <rect fill="#7C3AED" width="440" height="50" rx="8" x="30" y="170"/>
    <text fill="#fff" font-size="16" x="50" y="202"><tspan leaf="">步骤三：结果输出</tspan></text>
  </g>
</svg>
```

## 生成工作流

### 交互模式选择矩阵

| 用户需求 | 交互模式 | 推荐模板 |
|---------|---------|---------|
| 砸金蛋、刮刮卡、翻页 | 点击触发动画 | 模板 1/2/3 |
| 按钮闪光、光标闪烁 | 脉冲/闪烁 | 模板 4 |
| 进度条、加载动画 | 自动动画 | 模板 5 |
| 滑动切换、展开收缩 | 点击位移 | 模板 6 |
| 步骤展示、列表依次出现 | 序列帧动画 | 模板 7 |
| 结合多种效果 | 组合模式 | 自定义 |

### 平台约束检查清单

生成后逐条检查：

- [ ] 无 `<script>`、`onclick`、`onmouseover` 等 JS 元素
- [ ] 无 `@keyframes`、`transition`、`animation` CSS 属性
- [ ] 无 `begin="id.click"`（全部改为 `begin="mousedown"`）
- [ ] 无 `<clipPath>` 用于图片圆角（用 `<pattern>` 替代）
- [ ] 无 `linearGradient`/`radialGradient`（用纯色替代）
- [ ] 文字节点存在 `<tspan leaf="">` 包裹
- [ ] 所有样式内联
- [ ] 点击触发使用 `begin="mousedown"` + `restart="never"` 防止多次触发
- [ ] 使用 `fill="freeze"` 保持动画结束状态

## 设计原则

1. **无外部依赖** — 不依赖外部 CSS、JS、字体、图片
2. **纯内联** — 所有样式写在元素上
3. **一次触发** — 点击交互默认 `restart="never"`
4. **微信优先** — 以微信编辑器实际表现为准
5. **渐进增强** — 即使动画失效，内容仍可读

## 参考

- 桌面文件夹 `SVG文章/` — 763 个真实公众号 SVG 案例
- gzh-design 技能 `references/svg-wechat-guidelines.md`
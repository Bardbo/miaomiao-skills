# 14个Skill合集对照评估报告

> 评估日期：2026-06-06 | 评估方法：delegate_task并行读取+逐skill分析
> 来源：桌面 skill合集 文件夹（14个项目目录）
> 注意：这是快照式评估，内容会随时间过时。建议每月重新评估。

---

## 1. Baoyu Skills（21个）

**来源**：`baoyu-skills-main/skills/` | **特点**：Alipay生态，Type×Style二维设计系统，依赖baoyu-image-gen后端

### 建议安装

| 技能 | 功能 | 优先级 | 原因 |
|------|------|--------|------|
| baoyu-article-illustrator | 文章配图分析（Type×Style×Palette三维） | P0 | 写作流程缺配图功能 |
| baoyu-cover-image | 封面生成（5维度×9调色板×6风格） | P0 | 公众号封面专用 |
| baoyu-infographic | 信息图（21布局×22风格） | P0 | 公众号加分利器 |
| baoyu-diagram | SVG图表纯代码生成 | P0 | 技术文章必备 |
| baoyu-comic | 知识漫画生成器 | P1 | 条漫替代方案 |
| baoyu-slide-deck | 幻灯片（17种预设风格） | P1 | PPT需求 |
| baoyu-xhs-images | 小红书图片卡片系列 | P1 | 社交平台内容 |
| baoyu-translate | 三模式翻译引擎 | P1 | 高质量翻译 |
| baoyu-youtube-transcript | YouTube字幕下载 | P1 | 内容采集 |
| baoyu-url-to-markdown | Chrome CDP网页抓取 | P1 | 内容采集 |
| baoyu-markdown-to-html | WeChat兼容HTML生成 | P1 | 与wechat-article-formatting互补 |
| baoyu-post-to-wechat | 微信发布自动化 | P2 | 发布管道 |
| baoyu-wechat-summary | 微信群聊精华提取 | 按需 | 需wx-cli |
| baoyu-post-to-x / baoyu-post-to-weibo | X/微博发布 | 按需 | 跨平台发布 |

### 可学习方法论

- **Type×Style二维设计系统**：适用于内容生成场景
- **封面5维系统**（类型/调色板/渲染/文字/氛围）
- **流水线架构**：文章→插图→封面→HTML→发布

---

## 2. Canghe Skills（29个）

**来源**：`canghe-skills-master/skills/` | **特点**：最丰富合集，含Obsidian知识/视频生成/文档解析

### 建议安装

| 技能 | 功能 | 优先级 |
|------|------|--------|
| canghe-slide-deck | 16种视觉预设幻灯片 | P1 |
| canghe-comic | 5艺术风格×7色调×6布局漫画 | P1 |
| canghe-infographic | 20布局×17风格信息图 | P1 |
| canghe-article-illustrator | 文章插图（Type×Style系统） | P1 |
| canghe-cover-image | 封面5维度 | P1 |
| canghe-compress-image | 图片压缩自动选工具 | 轻量 |
| paddleocr-doc-parsing | PDF/图片文档解析 | 按需 |
| obsidian-markdown | Obsidian语法完整参考 | 按需（已有obsidian skill） |

### 可学习方法论

- **Runtime-neutrality**：所有skill不绑定单一runtime
- **角色一致性系统**：canghe-comic的角色reference chain
- **20×17兼容矩阵**：布局×风格的最优组合

---

## 3. Huashu Skills（21个）

**来源**：`huashu-skills-master/` | **特点**：「花叔」个人技能集，方法论质量极高

### 建议深入学习

| 技能 | 核心价值 | 优先级 |
|------|---------|--------|
| proofreading | 6大类AI腔识别体系 | P0 方法论 |
| data-pro | 数据分析+报告生成+PPT | P1 实用 |
| design | 20种设计哲学+评审框架 | P1 方法论 |
| slides | 18种设计风格PPT生成 | P1 |
| speech-coach | Winston演讲方法论 | P1 知识 |
| video-check | MrBeast标题/封面工程化 | P1 方法论 |
| image-upload | 配图自动上传 | 按需 |
| wechat-image | 公众号配图工作流 | 按需 |
| xhs-image | 小红书配图 | 按需 |
| md-to-pdf | Markdown→PDF | 按需 |

### 可学习方法论

- **6大类AI腔**：套话/AI句式/书面词/结构机械/态度中立/细节缺失
- **5种标题公式**：对比/痛点/结果/揭秘/清单
- **Assertion-Evidence规则**：每页一个主张+证据
- **防会话截断策略**：「先建文件再搜索」

---

## 4. LJG Skills（21个）

**来源**：`ljg-skills-master/skills/` | **特点**：李继刚认知工具集 — **最值得学习**

### 建议安装

| 技能 | 功能 | 优先级 | 核心价值 |
|------|------|--------|---------|
| ljg-think | "追本之箭"多学科钻探 | P0 | 最深层的认知工具 |
| ljg-rank | 降维归因引擎 | P0 | 找到不可变生成力 |
| ljg-writes | 写作即思考认知框架 | P0 | 约束系统最佳 |
| ljg-paper | 论文阅读→7段叙事 | P0 | 学术内容利器 |
| ljg-learn | 8维概念解剖 | P0 | 学习框架 |
| ljg-book | 书籍解构→"取景器"提取 | P0 | 阅读方法论 |
| ljg-read | 翻译+结构标注+深度提问 | P0 | 阅读方法论 |
| ljg-qa | 问答链→思想几何 | P0 | 提问方法论 |
| ljg-paper-river | 反向追溯引用链 | P0 | 研究方法论 |
| ljg-present | 宣言风格HTML演示 | P2 | 特定场景 |
| ljg-card | 7种视觉卡片 | P2 | 已有类似 |

### 可学习方法论

- **禁止词表**（禁用词清单）— 写作skill的核心约束
- **句子长度≤25字** — 硬核可读性约束
- **org-mode/纯ASCII输出风格**
- **"思想的几何"** — 抽象概念形式化为关系公式

---

## 5. Khazix Skills（5个）

**来源**：`khazix-skills-main/` | **特点**：卡兹克个人实用技能

| 技能 | 功能 | 优先级 |
|------|------|--------|
| khazix-writer | 公众号长文写作（HKR质检） | P1 学习方法论 |
| khazix-neat-freak | 自动对齐改动与文档/记忆 | P1 实用 |
| hv-analysis | 深度调研→万字PDF报告 | P2 |
| aihot | AI HOT日报查询 | 轻量 |
| storage-analyzer | 磁盘分析HTML报告 | 轻量 |

**关键方法论**：HKR质检（Happy有趣+Knowledge信息量+Resonance共鸣）

---

## 6. 独立Skills

| 项目 | 评估 | 建议 |
|------|------|------|
| guizang-ppt-skill | 单HTML横向翻页PPT（杂志/瑞士风格） | 按需安装 |
| guizang-social-card-skill | 社交媒体卡片+公众号封面 | 按需安装 |
| Humanizer-zh | 10种AI模式检测+改写 | P1 直接可用 |
| md2book | Markdown→专业PDF（3种主题） | 按需 |
| ppt-master | 567行高复杂度PPT pipeline | 过于复杂，学习方法论 |
| html-anything | 75可组合模板×9模式 | 学习架构（太大了不适合安装） |
| huashu-bookwriter | 书籍写作框架（3种书型） | 按需 |

---

## 7. 对我们现有技能的优化映射

| 我们的skill | 可借鉴来源 | 改进方向 |
|------------|-----------|----------|
| wechat-article-formatting | baoyu-format-markdown, huashu-design | CJK自动修正、设计哲学体系 |
| tiaoman-creation | canghe-comic, baoyu-comic | 角色一致性系统、PDF合并、风格兼容矩阵 |
| shui-bing-yue-perspective | khazix-writer, huashu-proofreading | HKR质检流程、AI腔检查 |
| agnes-ai-integration | canghe-image-gen | 多provider fallback |
|| **(新)** 文章配图 | baoyu-article-illustrator | ✅ 已安装到 creative/ | P0 ✓ |
|| **(新)** 信息图 | baoyu-infographic | ✅ 已安装到 creative/ | P0 ✓ |
|| **(新)** SVG图表 | baoyu-diagram | ✅ 已安装到 creative/ | P0 ✓ |
|| **(新)** AI去味 | huashu-proofreading + Humanizer-zh | ✅ 已安装 Humanizer-zh 到 writing/ | P0 ✓ |
|| **(新)** 深度思考 | ljg-think / ljg-rank | ✅ 已安装4个到 philosophy/ | P0 ✓ |

---

## 8. 自动优化记录

评估日期：2026-06-06（第二轮）
评估方法：darwin-skill 9维评分
评分详情见 `references/baseline-methodology.md`

### 基线评分

| 技能 | 总分 | 等级 | 关键发现 |
|------|------|------|---------|
| wechat-article-formatting | **78.5** | 🟡 良好 | 流程清晰但缺质检门控 |
| tiaoman-creation | **64.3** | 🟠 需改进 | 缺 checkpoint 和失败处理链 |
| shui-bing-yue-perspective | **84.4** | 🟢 优秀 | 反模式清单最佳，已成标杆 |

### 已完成优化

| 技能 | 优化内容 | 来源 |
|------|---------|------|
| wechat-article-formatting | + HKR选题质检（STEP 4） | khazix-writer |
| | + AI腔6类检测（STEP 6） | huashu-proofreading |
| | + S级/及格选题评分标准 | — |
| tiaoman-creation | + frontmatter（name/description/version/triggers） | darwin-skill dim1 |
| | + 7种布局模板表 | baoyu-skills |
| | + 角色一致性流程 + 🔴 CHECKPOINT | canghe-comic |
| | + 反模式清单表（7项） | darwin-skill dim9 |
| | + 失败处理表（3项） | darwin-skill dim3 |
| | + 输出路径规范 | 标准化 |
| | + 多角色条漫创作指南 | — |
| shui-bing-yue-perspective | + HKR质检（STEP 2写作任务） | khazix-writer |
| | + AI腔检测自检列表 | huashu-proofreading |

### 新安装技能（11个）

| 分类 | 技能 | 来源 |
|------|------|------|
| creative/ | baoyu-article-illustrator, baoyu-cover-image, baoyu-infographic, baoyu-diagram, baoyu-image-gen | Baoyu |
| philosophy/ | ljg-think, ljg-rank, ljg-writes, ljg-paper, ljg-learn | LJG |
| writing/ | humanizer-zh, khazix-writer | Humanizer/Khazix |
| devops/ | neat-freak | Khazix |

### 后续优先级

| 优先级 | 事项 | 预期收益 |
|--------|------|---------|
| P1 | 运行 dim8 实测验证（subagent跑测试prompt） | 确认优化是否真正提升质量 |
| P1 | 评估新版装baoyu技能（article-illustrator等） | 利用 Type×Style 体系 |
| P2 | 评估新版LJG认知技能 | 长期认知提升 |
| P2 | 创建公众号完整管线 MetaSkill | 一次加载所有相关技能 |
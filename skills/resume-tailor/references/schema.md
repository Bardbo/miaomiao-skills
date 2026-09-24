# 数据字段规范

## 母版 `master/master.yaml`

母版是**唯一真源**。Markdown 预览是只读产物，用户不直接编辑。

### 顶层

```yaml
master:
  version: 7              # 每次内容变更 +1
  updated_at: 2026-08-29
  locale: zh-CN
```

### `owner`

```yaml
owner:
  name: 张三
  contact: { phone, email, city, links: [] }
  profile:
    photo: true           # 中文互联网惯例放证件照；英文场景 false
    show_age: false
    show_political_status: false   # 国企/事业单位场景可开
```

**本地化差异必须注意**：英文简历规范普遍要求"不放照片、不写年龄婚姻"（规避歧视诉讼），但中国互联网简历不放证件照反而显得不完整。`locale` 决定默认值，不要照搬英文规范。

### `preferences`

```yaml
preferences:
  # ---- 人群画像：管「写什么」----
  # campus 校招（应届/实习/毕业<1年）教育置顶，校园内容保留，技能可全列
  # junior 初级（1-3年）          教育次位，校园内容只留高含金量，技能收敛
  # experienced 社招（3年+，默认）教育沉底，校园内容全删，技能≤10且需佐证
  # expert 资深（8年+或有代表作）  技能**也要列**，但严格收敛（≤6 且需佐证）
  #   ⚠ v12 推翻了原设定「不列技能清单，能力写进经历」——
  #     中文招聘初筛靠 ATS 关键词 + HR 按条款勾选，不列技能会在初筛阶段失配；
  #     且它与资深人群结构性互斥：越资深，做的事越难压进一条 bullet。
  profile: experienced

  # ---- 技能分类顺序（可选，v12）----
  # 引擎默认只含**跨行业通用**能力域：算法与建模 / 工程与交付 / 数据与工具 /
  # 管理与协作 / AI 原生工作流 / 本地模型与生成。
  # 行业特定的分类（如「智能交通与仿真」）**必须由母版在这里声明**，
  # 否则会掉到技能段末尾 —— 引擎默认值里不能写进某个人的职业身份。
  # category_order: ["算法与建模", "工程与交付", "智能交通与仿真"]

  # ---- 包装级别：管「怎么写」----
  # sincere 真诚    用本人原话，不升级动词，禁止上位概括
  # balanced 适度包装（默认） 动词升到证据支持的最高级，允许上位概括一次
  # bold 酥化       主动叙事重构，成果前置；G5需追问5层
  # 三者都**不能解锁 evidence 限制** —— pending 在 bold 下同样隐藏
  polish: balanced

  # ---- 求职意向默认不写 ----
  # 招聘系统里已有投递岗位，简历里再写既占首屏黄金位置，又暗示「海投/没想好」。
  # 目标岗位的正确载体是：文件名 + 投递邮件正文 + 打招呼语。
  # 仅内部转岗、猎头推荐等确实需要时置 true。
  show_intention: false

  forbidden_terms: [赋能, 驱动, 闭环, 抓手, 沉淀, 打法, 组合拳, 从0到1, 深度参与, 全面负责]
  # ⚠ 本字段当前【不被渲染器读取】。AI 味硬校验统一读共享文件 config/forbidden_terms.txt
  #   （多人共享，不随人复制；validate_master.py lint 与 check_gates G4 都读它）。
  #   母版里保留默认列表仅作提示，真实生效以共享文件为准。
  tone: 克制              # 克制 | 自信 | 技术极客
  max_pages: 2
```

`profile` 与 `polish` 是正交的两个维度，**都不影响 evidence 判定**：

| | 作用层 | 能做什么 | 不能做什么 |
|---|---|---|---|
| `profile` | 筛选器 | 决定保留哪些素材、段落顺序、技能收敛度 | 不能把 `pending` 变成可写 |
| `polish` | 放大器 | 决定保留下来的素材说到什么程度 | 不能放大 `inferred` / `unusable` |

定制版可在顶层写 `profile` / `polish` / `show_intention` 覆盖母版设置。

### `experiences[]` 经历池

```yaml
experiences:
  - id: exp-007           # 全局唯一，永不复用（即使条目删除）
    type: work            # work | project | internship | opensource | award
    org: 某某科技
    title: 后端工程师
    period: { start: 2023-04, end: null, current: true }
    raw_input: |          # 【永不修改】用户原话，只追加不覆盖
      负责用户增长系统，做一些数据处理的工作
    achievements:
      - id: exp-007-a1
        action: 重构
        object: 用户增长归因链路
        method: 引入 Flink 实时计算替代 T+1 离线任务
        result:
          metric: 归因延迟
          value: 从 24 小时降至 5 分钟
          baseline: 24 小时
          scope: 全量 300 万 DAU
        evidence: pending          # verified | self_reported | pending | inferred | unusable
        evidence_note: 用户口述，未见到监控截图；需确认是否独立完成
        strength: normal          # strong = 含主导/从0到1/首次，须挂证据
        tech_tags: [Flink, 实时计算]
        difficulty: 需在不中断服务前提下做双写迁移   # 选填但最值钱
        rewrite_candidates: []    # 表述优化回流处，不覆盖 raw_input
    tech_tags: [Flink, Kafka, Go]
    source_docs: [原始简历_2026-08.docx]
```

#### 关键字段说明

**`raw_input` 永不修改**

防漂移的锚。定制过程中表述会一轮轮"进化"，几个月后用户自己也分不清哪句是真的。任何时候能回溯到原话，才做得到真实性审计。

**`evidence` 是数据字段，不是提示词**

这是全案最重要的决定。写在提示词里的"不要编造"会被 LLM 绕过；做成字段后：

- 它会一路渲染到最终产物（灰色 + `【待补：需确认是否独立完成】`）
- 它逼着用户去补，而不是让 AI 悄悄编一个合理数字
- 可以设硬 Gate：`inferred` 的条目禁止渲染成确定语气

| 值 | 含义 | 出片表现 |
|---|---|---|
| `verified` | 过完证据三问，用户能说清来源与边界 | 正常渲染 |
| `self_reported` | 本人确认可写，但无第三方佐证 | 渲染；草稿标「○本人陈述」 |
| `pending` | 见下方二分 | 草稿标 `【待补】`，**出片隐藏** |
| `inferred` | AI 推断填充 | **禁止出现在成品中** |

**⚠ pending 的二分 —— 判错会误伤简历里最硬的内容。**

| | ① 存疑 | ② 未采集 |
|---|---|---|
| 问句 | 这事到底成没成？ | 编号 / 位次 / 日期是多少？ |
| 待遇 | 隐藏，补的是事实本身 | **本人确认后转 `self_reported`**，补的只是可查证编号 |
| 判据 | 删掉缺失字段后，句子是否还成立？不成立 → ① | 成立 → ② |

②类的标准写法：`evidence: self_reported` + `needs_confirm: true` +
`confirm_what: [...]`。渲染用 `clean_val()` 滤掉「待确认 / 待补」字段值，
成稿只留成立的部分。完整论证见 `rewrite-rules.md` →「pending 有两种」。

**`strength`**

含"主导""从 0 到 1""首次""负责"等强主张时设为 `strong`，Gate G2 会检查其 `evidence` 是否为 `verified`。强主张配弱证据 = 面试必崩。

**`difficulty`（难点）**

选填，但价值最高。结果可以注水，难点很难编——追问三层时编的结果会崩，编的难点崩得更彻底。它是简历"抗追问能力"的主要来源。

### `skills[]`

```yaml
skills:
  - id: sk-01
    name: BERT 微调
    category: 算法与建模     # 按能力域（做什么），不按技术类型（是什么）
    level: 熟练           # 了解|熟悉|熟练|精通|待确认 —— **仅供内部收敛决策，成稿不显示**
    stack: "PyTorch / Transformers"   # 工具名降级为注脚，渲染为「BERT 微调（…）」
    kind: capability      # commodity | capability | leverage（见下）
    status: active        # active 显示 / archived 默认不显示
    evidence_refs: [exp-003-a1]
  - id: sk-02
    name: SQL
    category: 工程与交付
    level: 熟悉
    kind: commodity       # 装个工具 / 问一句 AI 就能获得 → 不单列
    status: active
    evidence_refs: [exp-012-a2]
    keep: false           # true = JD 点名时强制显示
  - id: sk-03
    name: RAG
    level: 待确认          # level 未知时写「待确认」，不得凭空给级别
    kind: commodity       # 框架开箱即用 → 无区分度
    status: archived      # 候选技能：待本人确认后再转 active
    needs_confirm: true
```

**两个 v10 字段：**

| 字段 | 作用 |
|---|---|
| `stack` | 技术栈注脚。工具名**只能**出现在这里 —— 主句必须是能力。渲染为 `name（stack）` |
| `category` | 按能力域取值，不按技术类型。参考顺序：算法与建模 / 工程与交付 / 智能交通与仿真 / AI 原生工作流 / 本地模型与生成。未在顺序表中的分类排在后面 |

**`level` 不渲染（见「low 感」禁用清单）：** 自评不可查证，且「熟悉」在 HR 默认读法里 ≈ 不精。
它只用于内部决策（如「了解」级优先归档）。

技能栏最易注水。写了"精通 K8s"但经历里一条相关经验都没有，一问就崩。**技能必须能挂到经历上**，挂不上的自动降权。

#### `kind`：该不该列（范式层）

收敛管"列几项"，`kind` 管"该不该列"。判断问句：**装个工具、问一句 AI 就能获得吗？**

| kind | 定义 | 渲染行为 |
|---|---|---|
| `commodity` | 已商品化，人人可得（SQL、RAG、多数框架） | **默认不单列**，只作交付物 bullet 的注脚。`keep: true` 可强制（JD 点名时） |
| `capability` | 能独立从 0 做到 1 并交付给人用 | 正常显示，必须有 `evidence_refs` |
| `leverage` | 放大产出效率（AI 原生、受限环境交付） | 建议放进 `ai_native` 段而非这里 |

**`commodity` 不是"假"，是"没区分度"。** 它应该藏进交付物里——
写"搭建了自助查询平台"比写"熟悉 SQL"强得多，而 SQL 一个字都不用出现。

### `ai_native[]`（v9 新增 / v10 并入专业技能）

```yaml
ai_native:
  - id: ai-001
    group: "AI 原生工作流"                      # 渲染为「专业技能」的一个分组
    capability: "AI 辅助开发（vibe coding）"    # 主句必须是能力
    detail: "Claude Code / WorkBuddy / Hermes"  # 工具名只作附注，渲染为「能力：工具」
    evidence: self_reported
    evidence_refs: [exp-004-a4]
  - id: ai-004
    group: "本地模型与生成"                      # 与上面不是一回事：自己动手训/部署模型
    capability: "图像生成模型定制"
    detail: "ComfyUI 本地部署，自建数据集并训练 LoRA"
```

**v10：不再单独成段，按 `group` 并入「专业技能」。** 单独开段等于宣告"我的 AI 能力和专业能力是两回事"，
还会多出一个只有三行的碎段落。

| group | 放什么 |
|---|---|
| `AI 原生工作流` | 人机协作方式：vibe coding、自建记忆体系、skills 与工作流工程化、受限环境交付 |
| `本地模型与生成` | 自建算力与模型定制：本地推理部署、数据集构建与微调 |

**写法铁律：主句是能力 / 工作流，工具名只作附注。** 工具清单人人可装，
列出来是另一种凑数——和 `commodity` 同一个陷阱。校验器会拦截只有口号没有 detail 的条目。

**判定仍是那句问句：装个工具就能获得吗？** 据此「装 ComfyUI」是 commodity，
「自建数据集 + 训练 LoRA 并调到可用」是 capability；「用 Hermes」是 commodity，
「把重复工作封装为可复用 skill 再串成工作流」是 capability。

**技能堆叠是负分项，不是加分项。** 三个字段控制收敛：

| 字段 | 作用 |
|---|---|
| `status: archived` | 默认不显示。**归档不是删除**——母版是超集，换方向时可复活 |
| `keep: true` | 无佐证也强制显示。用于岗位刚需（如数据岗的 SQL），但应在 note 里说明理由 |
| `needs_confirm: true` | 候选技能待本人确认。**不确认就不能写成 active**——母版不能替用户表态 |

社招画像下由渲染器自动执行：过滤 `archived` → 过滤无佐证且非 `keep` → 超过 10 项告警。

### `honors[]` / `certifications[]`

```yaml
honors:
  - id: hon-001
    name: 三好学生
    period: 本硕期间
    student_era: true     # 校园内容：社招/资深画像下自动过滤
    relevance: low        # 无竞争性荣誉。过滤后若**全是 low → 整段不渲染**
    force: false          # true = 本人显式要求保留（投国企/体制内时）

certifications:
  - id: cert-001
    name: 中级工程师（电子信息）
    issuer: XX市人力资源和社会保障局
    level: 中级
    date: "2025-06"
    evidence: pending
```

`student_era` 的过滤逻辑：社招写"三好学生"不是因为它假，而是**它会稀释「能立刻干活」的信号**。工作多年还写校园荣誉，HR 的读法是"没东西可写了"。校招时反之，校园内容就是主战场，全删等于自废武功。

**荣誉段整段门控：** 过滤后若剩下的全是 `relevance: low`，**整段不渲染**（连标题都不出）。
无竞争性荣誉（优秀团员、积极参与、文明个人）上简历不是加分 —— 它传递的信号是
"我把能找到的都写上了"。硬通货 = 竞赛名次、政府或行业奖、奖学金级别，以及专利与论文。
确有需要时用 `force: true` 显式开启。

**证书优先于技能自评。** "英语（熟练）"是自评，"CET-6"是可查证的事实——同类内容应尽量放进 `certifications`。职称在国企/事业单位常是**准入门槛**而非加分项，分量高于多数技能项。

**弱证书提示：** 整段只剩 CET-4/6、计算机等级这类通用证书时，对硕士学历者是反向信号
（学历本身已覆盖它）。校验器会提示，但**不拦截** —— 证书是可查证事实，性质与荣誉不同。

### `summary{}`（v10）

```yaml
summary:
  enabled: false      # 默认关闭 —— 须本人确认后才出现在成稿
  text: |
    5 年算法与数据方向经验，覆盖车路协同仿真、NLP 算法落地与政务数据平台建设；
    具备在受限环境下从需求到交付独立闭环的能力。
```

社招最强去 low 手段，但它是全篇唯一会新增**概括性表述**的段落，故约束比正文更严：

1. 只能由已确认事实组成 —— **校验器会拦截摘要里出现 `pending` 内容**（如未确认完整名称的职称）
2. 不写自我评价形容词（"学习能力强""踏实肯干"）—— 那是另一类 low
3. 不含占位符（"待确认""待补"）—— 首屏出现占位符直接毁掉观感，是 ERROR
4. `enabled: false` 时只在 draft 模式提示，不进成稿

### `claim_ledger[]` 主张-证据账本

```yaml
claim_ledger:
  - date: 2026-08-29
    target: 字节跳动-后端
    claim: 主导了归因链路重构
    basis: exp-007-a1
    verdict: 降级为"参与"
    reason: 团队 4 人，用户负责 Flink 算子部分
```

记录每次定制中，AI 对哪些强主张做了降级或质疑。防止按岗位反复定制时表述逐步失真。

### `changelog[]`

```yaml
changelog:
  - version: 7
    date: 2026-08-29
    changes: ["新增 exp-012", "exp-007-a1 证据 pending→verified"]
```

---

## 定制版 `targets/<公司>-<岗位>-<日期>/tailored.yaml`

```yaml
tailored:
  id: t-20260829-字节-后端
  master_version: 7       # 母版升版后据此算出受影响的定制版

target:
  company: 字节跳动
  role: 后端工程师（增长方向）
  jd_snapshot:            # 【必存】JD 会下线
    source_url: https://...
    fetched_at: 2026-08-29T11:00
    text: |
      （JD 原文，逐字保存）
  analysis:
    p1_critical: [Go, 高并发, 分布式系统]
    p2_important: [Flink, 增长系统经验]
    p3_nice: [开源贡献, 大厂背景]

company_brief:            # 同公司跨岗位可复用
  fetched_at: 2026-08-29T11:05
  facts:                  # high → 可进正文
    - claim: 增长中台使用 Flink + ClickHouse
      source_url: https://...
      confidence: high
  inferences:             # mid/low → 只影响排序与语气
    - claim: 团队规模约 30 人
      confidence: mid
      used_for: ordering
  failed_queries: ["未找到公开的团队组织结构"]

selection:                # 只存 ID，不存内容副本
  # —— 白名单（只显示列出的，按给定顺序）——
  experiences: [exp-007, exp-012]        # 空 = 全部保留（按时间倒序）
  achievements: [exp-007-a1, exp-012-a2] # 成就白名单：裁剪单条 bullet；空 = 不裁剪
  # —— 黑名单（隐藏列出的，其余保留）——
  hidden_experiences: []     # 按 id 隐藏整段经历
  hidden_achievements: []    # 按 id 隐藏单条 bullet
  hidden_skills: [Kubernetes]  # 按 id 或 name 隐藏技能
  hidden_publications: []    # 隐藏论文
  hidden_patents: []         # 隐藏专利
  hidden_honors: []          # 隐藏荣誉
  hidden_ai: []              # 隐藏 AI 原生能力
  force_honors: false        # true = 强制显示荣誉段（投国企/体制内）
  # ⚠ 白名单与黑名单可共存：先按白名单裁，再按黑名单裁。
  #   render_resume.py 与 check_gates.py 复刻同一语义，必须保持一致（本项目踩过的坑）。
  #   减法语义下，拼错的 ID 会**静默失效**（既不报错也不生效），故 check_gates G1 会拦。

rewrite_policy:
  level: L2               # L1 | L2 | L3（L4 拦截）
  length_pages: 1

gaps:                     # 出片时一并交付给用户
  - ref: exp-007-a1
    question: 团队 4 人中你具体负责哪部分？
    impact: 该 bullet 目前只能写"参与"，无法写"主导"

proposals: []             # 见 writeback.md
dismissed_proposals: []   # 被用户拒绝的回流提案存档（防重复提议）
gate_report: {}           # check_gates 最新报告缓存（G1-G6 结论）

output:
  format: docx
  path: 张三-字节跳动-后端工程师.docx
  rendered_at: 2026-08-29T11:40
```

---

## ID 规范

- 经历：`exp-` + 三位数字（`exp-007`），全局递增，**永不复用**
- 成就：`<经历id>-a` + 序号（`exp-007-a1`）
- 定制版：`t-` + 日期 + `-` + 公司简称 + `-` + 岗位简称

ID 复用会导致定制版引用错条目，删除条目时 ID 也不回收。

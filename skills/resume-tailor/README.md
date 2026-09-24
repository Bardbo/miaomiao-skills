# resume-tailor · AI 简历优化与按岗定制 Skill

> 🌐 双语：[English](README.en.md)

帮用户把**真实经历**沉淀成一份可长期维护的**母版**，再从母版派生出**针对具体公司与岗位**的投递版本。在不脱离真实描述的前提下，把简历写得更有竞争力——**只筛选、不编造**。

---

## 它能做什么（三种能力）

| 能力 | 说明 | 当前状态 |
|---|---|---|
| **① 查简历问题** | 诊断事实缺失、AI 味、抗追问弱、版式差 | ✅ 随时可用（全项目最强） |
| **② 优化润色** | 改写法、去 AI 味、强化量化与抗追问能力 | 🟡 可用，出片补 docx 后即可交付 |
| **③ 按岗定制** | 依据真实 JD 做条目筛选、排序、侧重 | ✅ 李四→J1 已端到端跑通 |

**唯一交付物是简历本身**。考公/考编（不投简历）、岗位检索、面试辅导、职业规划不在主线范围内。

---

## 核心立场

> **只筛选、不编造。** 母版里没有的东西，不会出现在任何定制版上。

"高大上"不靠编事实，靠三种**不产生新事实**的手段：**翻译**（土话→行业术语）、**聚焦**（做了什么→解决了什么）、**层级提升**（执行层→方案层）。事实没变，读法变了——这是合法包装空间，也是本 Skill 的全部价值。

防造假靠 **Gate 链 G1–G6**（见下文），六道闸门**全部由脚本默认执行**，写在提示词里的规则会被 LLM 绕过，写在脚本里的不会。闸门会给出**硬结论**：P1 硬性要求全灭时直接判「不建议投」，而不是在一片警告里让你自己猜。

---

## 目录结构

```
<你的工作区>/                     # 用户数据所在层（升级 skill 不会动这里）
└── people/
    ├── _template/               # 模板（init 生成，复制用，勿改）
    ├── _jd/                     # JD 库（多类岗位原文）
    └── <姓名>/
        ├── master.yaml          # 母版——唯一事实源
        ├── sources/             # 原始材料存档（只追加不修改）
        ├── targets/<方向>/       # 按岗定制（tailored.yaml + jd_snapshot）
        └── output/              # 出片产物（html/docx/pdf）

resume-tailor/                   # Skill 本体（自包含，整体拷走即可）
├── SKILL.md                     # 完整方法论与工作流
├── requirements.txt             # 依赖清单
├── assets/                      # 模板 + 扁平禁用词表（G4 用）
├── config/                      # 跨人共享配置（不随人复制）
│   ├── forbidden_terms.txt      # 中文 AI 味禁用词表（分级，lint 用）
│   └── tech_terms.txt           # 技术词词典
├── references/                  # 9 份细则：schema / 采集 / 挖掘 / 润色 / JD / 公司 / 改写 / Gate / 回流
└── scripts/
    ├── resume.py                # 统一入口（init/people/new/check/lint/preview/render）
    ├── validate_master.py       # 校验 + 预览
    ├── density.py               # 篇幅引擎（A4 容量模型）
    ├── polish.py                # bullet 体检（L0–L3）
    ├── render_resume.py         # 出片：YAML → HTML（单一来源）
    ├── analyze_jd.py            # JD 解析与缺口比对
    ├── check_gates.py           # G1–G4 硬校验
    ├── export_docx.py           # HTML → 带文字层 .docx（ATS 可解析）
    ├── export_pdf.py            # HTML → 带文字层 .pdf
    ├── export_pdf.js            # node playwright + chromium 真实打印
    └── measure_pages.js         # 浏览器实测页数
```

> **包 / 工作区分离**：`resume-tailor/` 是可整体拷走的**只读包**（scripts / config / assets / references 全在包内，按脚本自身位置自解析）；
> `people/` 是**用户数据**，留在你自己的工作区。**升级或重装 skill 不会冲掉客户简历**，一份 skill 可服务多个工作区。

---

## 安装

### 1. 放好 skill 包
`resume-tailor/` 自包含（脚本、config、assets、references 都在包内，按脚本自身位置解析路径），拷到哪都能跑。
```bash
# 方式 A：作为 WorkBuddy Skill 安装
cp -r resume-tailor ~/.workbuddy/skills/

# 方式 B：留在项目里直接用（当前仓库即此形态）
```

### 2. 装依赖
```bash
pip install -r resume-tailor/requirements.txt     # PyYAML + python-docx（必需）

# 可选：PDF 出片 / 实测页数，需要 node + playwright
npm install playwright && npx playwright install chromium
# playwright 不在默认位置时：export NODE_PATH=<node_modules 所在目录>
```
> 不装 playwright 也能用：docx 出片、估算版篇幅诊断都不依赖它。

### 3. 初始化工作区
在你想放简历的目录里执行一次（会建出 `people/` 并把包内模板落进 `people/_template/`）：
```bash
python <包路径>/resume-tailor/scripts/resume.py init
```

### 统一解释器（已装 PyYAML / python-docx）
```
# Windows（隔离 venv）
%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe
# macOS / Linux
~/.workbuddy/binaries/python/envs/default/bin/python
```
从 PDF 旧简历提取原文（Phase 0 材料导入）另需 `pip install pymupdf`；路径动态取，禁止硬编码用户名。

> **路径约定**：在**含 `people/` 的工作区目录**执行命令，用 `resume-tailor/scripts/xxx.py`（相对或绝对路径）调用脚本。
> `people/` 默认取当前目录下的 `./people`，可用环境变量 `RESUME_WORKSPACE` 指向别处。
> **绝不把他人母版路径写死进脚本或文档默认值。**

---

## 快速开始

```bash
# —— 统一入口（--person 省略时若仅一人则自动选中）——
python resume-tailor/scripts/resume.py people                      # 列出所有人及母版版本
python resume-tailor/scripts/resume.py new     --person 张三        # 从模板创建新人
python resume-tailor/scripts/resume.py check   --person 张三      # 校验（G1/G2/G4）
python resume-tailor/scripts/resume.py lint    --person 张三      # 只扫中文 AI 味
python resume-tailor/scripts/resume.py preview --person 张三      # 生成 Markdown 只读预览
python resume-tailor/scripts/resume.py render  --person 张三 --mode draft|final

# —— 篇幅与润色（先跑 density，再跑 polish，最后才谈定制）——
python resume-tailor/scripts/density.py --person 张三             # 篇幅诊断（估算）
python resume-tailor/scripts/density.py --person 张三 --measure   # 篇幅诊断（浏览器实测，出片前跑）
python resume-tailor/scripts/polish.py  --person 张三             # bullet 体检与改写方向

# —— 按岗定制（Phase 2 → Phase 4 校验 → 出片）——
python resume-tailor/scripts/analyze_jd.py people/_jd/J1-校招技术.md \
    --master people/李四/master.yaml --emit targets/J1-校招软件研发/analysis.yaml
python resume-tailor/scripts/check_gates.py \
    --master people/李四/master.yaml \
    --target people/李四/targets/J1-校招软件研发/tailored.yaml \
    --rendered people/李四/output/resume-J1-校招软件研发-draft.html

# —— 出片（均带文字层、ATS 可解析）——
python resume-tailor/scripts/export_docx.py --person 李四 --target targets/J1-校招软件研发/tailored.yaml --mode draft
python resume-tailor/scripts/export_pdf.py  --person 李四 --target targets/J1-校招软件研发/tailored.yaml --mode draft
```

> 不要交付 HTML 截图 PNG——没有文字层，ATS 解析不了。

---

## 闸门体系（Gate 链 G1–G6）

| Gate | 检查 | 失败处理 |
|---|---|---|
| **G1 溯源** | 每个 bullet 能否追到 master 条目 ID | 追不到 = L4 违规，打回 |
| **G2 证据** | `pending`/`inferred` 是否写成确定语气 | 降级为"参与"或标 `【待补】` |
| **G3 覆盖** | P1/P2/P3 关键词在**成稿**命中率 **+ 匹配结论** | **P1 全灭 = 不建议投（硬拦）**；P1 不足半数 = 不建议直接投 |
| **G4 去 AI 味** | 成稿正文命中分级禁用词（A/B 硬拦，C 只提示）+ 标点/量化率 | A/B 强制改写，C 挂证据 |
| **G5 反向面试** | **出片条目**扛得住三层追问吗（**静态代理**） | 扛不住的降级或删除（硬拦） |
| **G6 版式** | 内部标记泄漏 + **实测分页**（调 `measure_pages.js`） | 泄漏/溢出/可修残页 = 打回 |

G1–G6 **全部由 `check_gates.py` 默认执行**（G4 自动解析成稿，无需手动传 `--draft`；
G6 有 node+playwright 时实测分页，没有则退化为静态检查并明说）。

**G3 的「匹配结论」是硬判据，不是提示。** 覆盖率只报数字不够用——22% 和 47% 在报告里
长得差不多，但一个该投、一个不该投。判据用 **P1（准入门槛）** 而非总覆盖率
（总覆盖率会被 P2/P3 长尾稀释）：P1 全灭 → **不建议投（ERROR）**；P1 不足半数 →
不建议直接投；P1 过关但总量 <30% → 说明是**措辞没对上 JD 的语言**，按 JD 用词重写即可，
不必换岗位。

**G5 是脚本化的静态代理**，且只审**真正出片的条目** —— `pending`/`inferred` 在 final
模式本来就会被整条隐藏，对一条不进成稿的经历问「扛不扛得住追问」是假警报（与 G3
「只测成稿文本」同一口径）。判据：出片条目里**无量化结果且主张弱** → 扛不住（ERROR）；
有结果无基线/无范围、纯定性 → 可加固；量化率 <30% → 触发深度补强提示；
填了 `difficulty`（难点）的条目计入正面指标。

G4 读的是 `config/forbidden_terms.txt`（**带 A/B/C 分级**）。曾经的坑：误用
`assets/forbidden_terms.txt`——那是剥掉分级的扁平镜像，会把 C 级「强主张」（主导/牵头/
独立完成）当 A 级「必删」硬拦，逼作者删掉真实主张。

**`evidence` 五档（render 强制执行，不受 profile/polish 影响）**

| 档位 | 含义 | 能否进简历 |
|---|---|---|
| `verified` | 第三方可查证（专利/论文/公开记录） | ✅ 强主张可保留 |
| `self_reported` | 本人明确陈述（旧简历/口述） | ✅ 可写，不降级 |
| `pending` | 信息不全待补 | ⚠️ 出片隐藏，宁缺毋滥 |
| `inferred` | AI 推断 | ❌ 禁止进母版 |
| `unusable` | 涉密/权属归他方 | ❌ 禁止进任何定制版 |

---

## 两个前置参数

| 维度 | 管什么 | 取值 |
|---|---|---|
| **`profile`** 人群画像 | 保留哪些素材、段落顺序、技能收敛 | `campus` / `junior` / `experienced`(默认) / `expert` |
| **`polish`** 包装级别 | 同一事实说到几成 | `sincere` / `balanced`(默认) / `bold` |

profile 是筛选器，polish 是放大器——放大器不能放大没被选中的东西；polish 不能解锁 evidence 限制。

---

## 发布状态

**自用接单已就绪。** 本仓库为通用 skill 发布形态：不含任何真实简历数据（`people/` 为使用者工作区数据，由 `init` 命令创建，不随仓库发布）。

---

## 参考文件速查

| 文件 | 内容 |
|---|---|
| `resume-tailor/SKILL.md` | 完整方法论与工作流（必读） |
| `resume-tailor/references/schema.md` | 母版与定制版字段规范 |
| `resume-tailor/references/gate-checklist.md` | G1–G6 逐条检查项 |
| `resume-tailor/references/polish-playbook.md` | bullet 四级模型与改写 |
| `resume-tailor/references/mining-playbook.md` | 素材挖掘 |
| `resume-tailor/references/rewrite-rules.md` | 人群画像/包装级别/中文写作规范 |

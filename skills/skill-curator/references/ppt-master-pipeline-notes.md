# ppt-master Pipeline 执行实践笔记

> 发现时间: 2026-06-08
> 来源: 用户 Obsidian 技能库
> 状态: 已实际执行一次端到端 pipeline（20页PPT重设计）

## 1. ppt-master 是什么

ppt-master 是一个 **SVG→PPTX** 的 PPT 生成系统。与已安装的 guizang-ppt-skill（HTML 网页 PPT）不同，ppt-master 生成的是**原生 PPTX 文件**，包含可编辑的原生绘图 ML 和演讲备注。

核心路径：
1. Extract PPT → MD（提取原始内容）
2. Convert MD → SVG（按设计规格逐页生成矢量 SVG）
3. Quality check SVGs（XML 结构校验）
4. Fix errors（修复重复属性等）
5. Export SVG → PPTX（原生绘图 ML 格式导出）

## 2. SVG 质量检查器

ppt-master 自带 SVG 质量检查脚本，在生成 SVG 后、导出 PPTX 前运行：

```bash
python <SKILL_ROOT>/scripts/svg_quality_check.py svg_output/
```

**检查内容**：
- XML 重复属性（`font-weight` 重复、`x` 属性重复）→ ERROR
- 字体栈差异 → WARN（不影响导出）
- 颜色值格式 → WARN
- 标签闭合 → ERROR

**实际经验**：
- 每次生成 20 个 SVG 文件，初始有 3 个 ERROR（重复属性 bug）
- 常见重复属性：`font-weight="600"` 在 `<text>` 标签中出现两次
- 常见重复属性：`x="100"` 在 `<text>` 标签中出现两次（复制粘贴后忘记删旧值）
- 修复后再次运行，全部 PASS（仅 WARN 字体栈差异）

**关键教训**：在导出 PPTX 前必须运行 quality check 并修复所有 ERROR。跳过这步会导致导出 PPTX 包含损坏的 XML。

## 3. spec_lock.md 漂移警告

ppt-master 的 `spec_lock.md` 在导出时会与 SVG 的 font-family 做比对。发现以下漂移模式：

| SVG 中的字体栈 | spec_lock 预期 | 漂移原因 |
|----------------|---------------|---------|
| `"MiSans, Microsoft YaHei, sans-serif"` | `MiSans` | 只写了第一个 |
| `"MiSans, PingFang SC, Microsoft YaHei, sans-serif"` | `MiSans` | 只写了第一个 |

**根因**：PPTX 的 `font-family` 字段只保留字体栈的第一个值。当 spec_lock 记录完整栈但 PPTX 只写第一个时，drift checker 会报错。

**处理方式**：这些不是真正的视觉漂移——PPTX 渲染时会自动 fallback 到字体栈的后续值。可以安全忽略，或在 spec_lock 中只记录第一个字体来避免误报。

## 4. Free Design 模式

ppt-master 使用 `--free-design` 路径时：
- 所有页面都是自由设计（没有 template 继承）
- 每个页面需要独立设计版式
- 不支持 `--template-path` 的布局约束
- 这意味所有页面都是 Free Design，no template inheritance

**适用场景**：旁门左道方法论的"少即是多"、"克制配色"、"数据大字报"等设计原则最适合 Free Design。

## 5. 与 guizang-ppt-skill 的对比

| 维度 | ppt-master | guizang-ppt-skill |
|------|-----------|------------------|
| 输出格式 | 原生 PPTX | 单 HTML 文件 |
| 编辑性 | PowerPoint 内可编辑 | 浏览器预览 |
| 设计自由度 | 高（自由 SVG 绘图） | 中（layout 骨架约束） |
| 旁门左道适配 | 高（原生矢量设计） | 高（瑞士风极简） |
| 安装位置 | 用户 Obsidian 库 | ~/.hermes/skills/ |
| 是否安装 | ❌ 尚未 | ✅ 已安装 |

## 6. 关键文件结构

```
ppt-master-main/
├── skills/
│   └── ppt-master/
│       ├── SKILL.md           ← 主技能定义
│       ├── pipeline.py        ← pipeline 执行
│       ├── svg_generator.py   ← SVG 生成
│       └── svg_to_pptx.py     ← SVG→PPTX 导出
├── scripts/
│   └── svg_quality_check.py   ← SVG 质量检查器
└── ...
```

技能根目录变量：`SKILL_ROOT` → `<SKILL.md 所在目录>`

## 7. 值得记录的实践经验

- **颜色替换 vs 版式重组**：仅替换颜色（python-pptx 编程式修改）→ 版式不变，被用户评价为"很乱"。真正的版式重组需要 SVG 级设计。
- **旁门左道 PPT 方法论**：克制配色（海军蓝+琥珀）、少即是多、数据大字报、线条分隔 → 在 ppt-master 的 Free Design 模式下最容易落实。
- **Twenty Pages 全部用同一版式**：原 PPT 20 页全部是"标题幻灯片"版式，这是"很乱"的主因。需要 10 种不同版式来解决。

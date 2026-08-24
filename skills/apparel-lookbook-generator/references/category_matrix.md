# Apparel Lookbook v8 — 分析引擎 & 推导矩阵

本文件是 `apparel-lookbook-generator` v8 的**操作参考**。SKILL.md 负责工作流编排，本文负责**产品分析框架、场景推导引擎、姿势推荐库、品牌故事矩阵、自我审查机制、相机滤镜系统、提示词构造指南**。

---

## 一、Engine 1: 产品深度分析框架（Step 2 必执行）

### 1.1 单品提取模板

读取参考图后，按此表格逐项提取：

| 字段 | 说明 | 示例 |
|------|------|------|
| 序号 | 1-N | 1 |
| 品名 | 是什么 | cream ivory camisole tank top |
| 类别 | top/bottom/outerwear/footwear/bag/jewelry/accessory/hosiery/headwear | top |
| 颜色 | 精确色名 | cream ivory |
| 材质 | 可见纹理 | cotton-modal ribbed knit |
| **标志性特征** | 让这件单品独一无二的外观细节（**最重要字段**） | thin straps, scoop neckline, slight sheen |
| 参考图中的位置/状态 | 怎么摆的 | worn on model, tucked into shorts |

### 1.2 风格族分类决策树

```
参考图 → 主导色调？
├─ 中性色为主（米/白/灰/棕/黑）→ 材质感强？
│   ├─ 是（丝绸/羊毛/精纺棉）→ 剪裁修身？→ old money / 静奢
│   └─ 否（宽松/基础款）→ 极简图案？→ minimal Scandinavian / 极简
├─ 大胆色彩/图案 → 廓形？
│   ├─ 宽松/Oversized → streetwear / 街头潮酷
│   └─ 修身/女性化 → 有蕾丝/镂空？→ sweet-spicy / 甜辣约会
├─ 格纹/学院元素 → preppy / 学院风
├─ 大地色/层叠纹理/流苏 → boho / 波西米亚
├─ 运动面料/卫衣/leggings → athleisure / 运动休闲
└─ 西装元素/锐利剪裁 → commute / 通勤职场
```

> **只选一个主风格族。** 如果产品跨风格（如"极简+通勤"），选主导的那个，次要风格作为氛围词补充。

### 1.3 季节与正式度推断

| 观察指标 | 夏季信号 | 冬季信号 | 春秋信号 | 正式度↑ | 正式度↓ |
|---------|---------|---------|---------|--------|--------|
| 面料 | 亚麻、薄棉、雪纺 | 羊毛、粗纺、天鹅绒 | 针织、精纺棉、真皮 | 丝绸、精纺羊毛、结构化剪裁 | 棉T恤、牛仔、运动面料 |
| 覆盖 | 无袖、短裙、短裤 | 长袖、长裤、大衣 | 七分袖、中长裙、 layered | 高跟(>5cm)、结构包、西装外套 | 平鞋、托特包、开衫 |
| 配色 | pastel 亮色、白色系 | 深色、暖棕、酒红 | 大地色、莫兰迪 | 金属色配饰多、单色系 | 彩色配饰、印花 |
| 鞋履 | 凉鞋、草编鞋、裸靴 | 长靴、牛津鞋、厚底乐福鞋 | 乐福鞋、短靴、切尔西 | 细高跟、尖头、漆皮 | 运动鞋、帆布鞋、平底 |

### 1.4 标志性单品标记规则

从完整清单中选出 **1-3 件最独特** 的单品：

**入选标准（满足任一即标记）：**
- 有复杂图案（蕾丝花纹、提花、刺绣）
- 有特殊五金（异形扣、链条、金属件）
- 是整套造型的视觉焦点（颜色对比最强/设计最突出）
- 材质与其他单品差异大（整套棉质中一件皮革）

**标记后的处理：**
- 在每个 prompt 中对这些单品用 **2× 详细度** 描述
- 在 Details 类目中优先拍这些单品的特写
- 在 artifact_guard 中特别提及这些单品不能丢失

---

## 二、Engine 2: 场景推导引擎（Step 4）

### 2.1 推导公式

```
场景池 = f(风格族, 季节, 正式度, 鞋履类型, 配色温度) × 场景候选库
```

每个场景必须通过 **3 个过滤器**：

| 过滤器 | 问题 | 通过标准 |
|--------|------|---------|
| **风格兼容** | 这个场景和风格族搭吗？ | old money ↔ 画廊/酒廊 ✓；old money ↔ 滑板公园 ✗ |
| **季节合理** | 这个季节在这个场景自然吗？ | 夏天 ↔ 海边 ✓；夏天 ↔ 壁炉前 ✗ |
| **鞋履可行** | 穿这双鞋在这个场景合理吗？ | 细高跟 ↔ 室内铺地毯 ✓；细高跟 ↔ 公园草地 ✗ |

### 2.2 场景候选库（按风格族索引）

#### Old Money / 静奢
| 场景 | 光线 | 活动 | 适合类目 | 氛围词 |
|------|------|------|----------|--------|
| 当代艺术画廊开幕 | 画廊射灯 + 自然侧光 | 边走边看展品 | Outfit, Lifestyle | refined |
| 屋顶露台酒廊黄昏 | 金色时刻暖光 | 手持香槟杯望城市 | Outfit, Couple, Lifestyle | romantic |
| 精品酒店大堂 | 温暖环境光 + 吊灯 | 走向电梯/在大堂等车 | Outfit, Brand Story | poised |
| 私人俱乐部图书室 | 柔和台灯光 | 坐在皮沙发翻杂志 | Lifestyle, Brand Story | intimate |
| 秋日花园派对 | 自然散射日光 | 站着与人交谈手持小盘子 | Outfit, Couple | social |

#### Minimal Scandinavian / 极简
| 场景 | 光线 | 活动 | 适合类目 | 氛围词 |
|------|------|------|----------|--------|
| 独立书店晨光 | 清晨窗光 | 伸手取下层书架的书 | Outfit, Lifestyle | peaceful |
| 白墙工作室/家居一角 | 明亮漫射自然光 | 坐在窗边喝咖啡/整理花瓶 | Lifestyle, Brand Story | serene |
| 周末早午餐咖啡馆 | 明亮自然光 | 笑着和对桌人交谈 | Couple, Lifestyle | warm |
| 空旷美术馆白墙空间 | 顶部自然光 | 站在作品前凝视 | Outfit, Details(env) | contemplative |

#### Sweet-Spicy / 甜辣约会
| 场景 | 光线 | 活动 | 适合类目 | 氛围词 |
|------|------|------|----------|--------|
| 天台酒吧夜景 | 温暖氛围灯 + 城市灯光虚化 | 靠栏杆举杯大笑 | Outfit, Couple, Lifestyle | alluring |
| 约会餐厅卡座 | 暖烛光 + 环境柔光 | 转身对镜头笑/与对面人互动 | Outfit, Couple, Lifestyle | flirtatious |
| 泳池边午后 | 明亮阳光 + 水面反光 | 靠泳池边腿伸直 | Outfit, Lifestyle | confident |
| 夜店入口/ valet 站 | 霓虹 + 街灯 | 刚下车走向入口 | Outfit, Lifestyle | edgy |

#### Preppy / 学院风
| 场景 | 光线 | 活动 | 适合类目 | 氛围词 |
|------|------|------|----------|--------|
| 校园图书馆 | 台灯 + 窗光 | 坐在木桌前翻书/写字 | Outfit, Lifestyle, Brand Story | scholarly |
| 秋日公园长椅（落叶） | 柔和秋日散射光 | 坐着抱书/看手机 | Outfit, Lifestyle | nostalgic |
| 砖墙咖啡馆内 | 暖室内光 | 和朋友坐在角落聊天 | Couple, Lifestyle | cozy |
| 复古精品店浏览 | 混合室内光 | 翻看衣架上的衣服 | Outfit, Lifestyle | curious |

#### Streetwear / 街头潮酷
| 场景 | 光线 | 活动 | 适合类目 | 氛围词 |
|------|------|------|----------|--------|
| 涂鸦墙前 | 强烈方向性日光（带阴影） | 靠墙站立手插口袋/做手势 | Outfit, Details(env) | bold |
| 滑板公园 | 自然午间光 | 站在滑板上/旁边 | Outfit, Lifestyle | energetic |
| 霓虹街角夜景 | 霓虹灯彩色光 | 走过路口回头看 | Outfit, Lifestyle | urban |
| 夜市摊位间 | 暖串灯 + 人造光 | 边走边看摊位 | Outfit, Lifestyle | vibrant |

#### Commute / 通勤职场
| 场景 | 光线 | 活动 | 适合类目 | 氛围词 |
|------|------|------|----------|--------|
| 写字楼落地窗前 | 日间明亮自然光 | 站在窗边看城市 | Outfit, Lifestyle | powerful |
| 地铁/站台 | 站台顶灯 + 透过棚的自然光 | 等车/看手机 | Outfit, Lifestyle | efficient |
| 商业区人行道 | 城市建筑反射漫射光 | 快步走/边走边说话 | Outfit, Lifestyle | dynamic |
| 机场贵宾室 | 柔和环境光 | 坐着看笔记本/喝咖啡 | Outfit, Lifestyle, Brand Story | polished |

### 2.3 为每张图选择场景的规则

1. **Outfit**: 选场景池中最有视觉冲击力的 1 个（通常是户外或特色室内）
2. **Lifestyle**: 选场景池中最生活化的 1–2 个（咖啡馆/家/街道）
3. **Couple**: 选允许近距离互动的场景（餐厅/酒吧/居家/公园长椅），避免开阔空间
4. **Brand Story**: 选能讲故事的场景（幕后/准备/归家/设计师桌面）
5. **Flat Lay / Details**: 场景 = 表面材质（木/亚麻/大理石），不需要完整场景

---

## 三、Engine 3: 姿势推荐库（Step 5）

### 3.1 按鞋履类型选姿势（核心查找表）

这是 **v8 最关键的改进之一**。之前所有产品都用同一个 "candid mid-step looking aside" —— v8 根据鞋履类型选姿势。

| 鞋履类型 | Outfit 全身姿势 | Lifestyle 姿势 | Couple 姿势 | ⚠️ 避免 |
|---------|---------------|--------------|------------|--------|
| **高跟鞋/细跟 (>5cm)** | 站立重心在后脚，一手轻触头发，头转四分之三侧面；或靠墙优雅站立 | 坐在吧台椅上双腿交叠转向镜头笑；或站在落地窗前看外面 | 两人坐吧台相邻，她身体微向他倾斜 | 蹲下、跳跃、弯腰系鞋（触发脱鞋伪影）、手靠近脚部 |
| **乐福鞋/平底鞋/芭蕾舞鞋** | 自然漫步中途停步，手臂放松两侧，微微抬头笑；或坐姿一条腿盘起另一条垂下 | 盘腿坐在地板/沙发上翻杂志；或倚靠柜台看手机 | 两人并坐咖啡桌，她笑着指窗外某物给他看 | 正式站姿手插腰（太僵硬）、高踢腿 |
| **运动鞋/板鞋** | 随意靠墙一只脚蹬墙后、双手插兜；或走路中大步迈出 | 坐台阶上双腿伸展；或滑板旁单脚踩板 | 两人一起走她突然拉他胳膊指某方向 | 正式端坐、优雅手抚发 |
| **短靴/踝靴** | 重心偏一脚另一脚稍后，一手插兜头微仰；或大步走回头望 | 坐桌子边缘双腿自然下垂晃动 | 两人同靠栏杆肩挨肩看同一方向 | 优雅交叠脚踝（靴子不这么弯）、蹲下 |
| **凉鞋/露趾** | 海滩/池边边缘站立一条腿微屈；或走在草地上 | 腿悬空坐着（阳台/码头边缘）；或坐在野餐毯上 | 两人坐在野餐毯上她递他东西 | 寒冷场景、正式室内 |
| **图中无鞋履** (平铺/细节) | N/A — 关注物品排列/拍摄角度 | N/A | N/A | N/A |

### 3.2 按服装类型微调姿势

| 服装特征 | 姿势调整 | 原因 |
|---------|---------|------|
| **长裙/ maxi** | 多用站姿+转身/走动，展示裙摆流动 | 坐姿会堆积裙子看不到版型 |
| **超短裙/ mini** | 多用坐姿交叉腿或站姿重心偏移 | 站立全身可能过于暴露不适合种草图 |
| **长款大衣/风衣** | 走动中、掀开衣襟动作、靠风飘动 | 静态站姿看不出大衣轮廓 |
| **layered 叠穿** (开衫+吊带) | 自然动作展示层次（抬手整理头发露出吊带、脱下开衫搭臂弯） | 静态姿势可能遮住内搭 |
| **紧身/ body-con** | 多用坐姿三角度或靠姿，避免全身正面僵硬 | 全身正面太像证件照 |

### 3.3 Flat Lay 排列风格库

| 风格名 | 排列方式 | 适用产品风格 | 氛围 |
|--------|---------|-------------|------|
| **Lived-in casual** | 物品略微散乱像刚脱下放在床上 | 日常休闲、通勤 | 真实、亲切 |
| **Curated editorial** | 物品精确间距排列、有呼吸感 | 极简、静奢、高端 | 专业、品牌感 |
| **In-use hint** | 一件物品半展开/打开暗示刚用过（开衫敞开、包带散开） | 所有风格 | 动态、叙事性 |
| **Color-blocked** | 按色块分组排列 | 多色搭配、撞色造型 | 视觉冲击力强 |
| **Diagonal flow** | 物品沿对角线摆放引导视线 | 所有风格 | 动感、时尚编辑感 |

### 3.4 Details 微距拍摄角度库

| 角度类型 | 描述 | 适合拍什么 |
|---------|------|-----------|
| **Texture shot (45°)** | 45°侧光打在材料表面，看到编织/颗粒/光泽 | 针织纹路、皮革纹理、缎面光泽 |
| **Hardware straight-on** | 正面对焦五金件（扣、链、铆钉） | 金属扣、拉链头、链条款、表盘 |
| **Construction detail** | 微斜角展示缝线/拼接/褶皱工艺 | 袖口罗纹、下摆收边、拼接处、褶裥 |
| **Edge-finish** | 极浅角度沿边缘拍摄，展示包边/滚边/锁边 | 领口、袖口、下摆、袋口边缘 |
| **Wear-and-drape** | 自然悬挂/折叠状态下的面料垂坠感 | 软垂材料（丝绸、针织、薄棉） |

---

## 四、品牌故事角度矩阵（Engine 2 续）

### 4.1 从产品属性→故事角度

| 产品特征组合 | 推荐故事角度 | Brand Story prompt 方向 |
|-------------|-------------|----------------------|
| 高品质材料 + 中性色 + 精致剪裁 | **"Less but Better"** | 精选衣橱理念，每件都是经过考虑的选择，晨光中慢慢挑选今天穿什么 |
| 蕾丝/镂空 + 修身 + heel | **"Date Night Ritual"** | 约会前的准备过程——化妆、挑首饰、最后穿上那件关键单品 |
| 层叠穿搭 + 舒适面料 + 平鞋 | **"Weekend Rhythm"** | 周末早晨不赶时间的节奏，慢悠悠泡咖啡、翻杂志、换上舒适但好看的一套 |
| 大胆配色 + Oversized + 运动鞋 | **"City Canvas"** | 城市就是画布，服装是自我表达的笔触，街头随拍的自信感 |
| 格纹 + 学院风单品 + 及膝袜 | **"Campus Memory"** | 怀旧学术氛围，图书馆的安静、秋日校园的小径、老书店的灰尘味 |
| 西装元素 + 锐利线条 + 结构包 | **"Desk to Dinner"** | 一套衣服两个场合——办公室的专业到晚餐的从容转换 |
| 大地色 + 流苏/层叠 + 宽檐帽 | **"Wanderlust Soul"** | 自由的灵魂永远在路上的感觉，复古市场的淘宝、公路旅行的停靠 |
| 单色系 + 极简设计 + 无图案 | **"Conscious Living"** | 有意识的生活方式的视觉表达——少买精选、可持续、 mindful consumption |

### 4.2 Brand Story prompt 构造公式

```
[Story angle name] narrative scene:
[key items] arranged in [arrangement style],
[environmental props that tell the story] nearby,
[lighting that matches mood],
[brand story angle expressed visually through composition],
{filter: Contax G2 moody},
{avoid}, {artifact_guard}
```

**示例（Minimal Scandinavian → "Conscious Living"）：**
> "Conscious living narrative: beige knit cardigan draped over wooden chair back, cream camisole folded neatly beside it, tan loafers placed on floor below as if just slipped off, a single white peony in ceramic vase and an open book about mindful consumption on side table, soft overcast morning light through sheer curtains, each item given space to breathe suggesting intentional curation, shot on Contax G2 with Planar 45mm f/2 at f/2 Kodak Tri-X 400 B&W emulation visible grain vignette selective focus moody ambient morning light editorial narrative feel"

---

## 五、v8 反伪影正向约束 `{artifact_guard}` （更新版）

**加到每一个 prompt 里**（Lifestyle 和 E-com 都要），放在 F-TECH 之后：

> `neck is bare with no mask or face covering, both shoes worn on both feet, no footwear being held in hands or placed on tables or floors or surfaces, all items from the reference set are present and correctly worn or placed, hands are empty or naturally resting at sides or on table, no phantom accessories beyond the listed items, no extra objects being carried or held`

### v8 新增条款 vs v7 对比

| 条目 | v7 | v8 | 修复的问题 |
|------|----|----|-----------|
| 脖子无异物 | `neck is bare, no mask` | 不变 | 口罩挂脖 ✅ |
| 鞋子在脚上 | `both shoes worn on both feet` | 不变 | 鞋子脱了 ✅ |
| 鞋子不放桌上 | `no footwear on tables or surfaces` | 不变 | 鞋放桌上 ✅ |
| **不能手拿着鞋子** | ❌ 没有 | **`no footwear being held in hands`** | **手提鞋子 ❌→✅** |
| **手不能拿奇怪的东西** | ❌ 没有 | **`hands are empty or naturally resting`** | 手拿不明物体 |
| **不能有额外配饰** | `all items present`（隐含） | **`no phantom accessories beyond listed items`** | 凭空发明项链/帽子/手机 |
| **不能拿着/携带额外物品** | ❌ 没有 | **`no extra objects being carried or held`** | 拿着包以外的物品 |

---

## 六、Engine 4: 自我审查机制（Step 7.5）

### 6.1 审查流程

```
ImageGen 输出 → Read(输出图片) → 8项检查清单 →
├─ 全部 PASS → 加入 approved 集合 → 继续下一张
├─ 有 FAIL 项 → 调整 prompt（加强失败项约束）→ 重生成 1 次 → 再审
└─ 连续 2 次 FAIL → 跳过该图 → 记录失败原因 → 通知用户
```

### 6.2 八项检查清单（详细版）

| # | 检查项 | PASS 标准 | 常见 FAIL 表现 | 调整策略 |
|---|--------|----------|---------------|---------|
| **1** | **单品完整性** | `{items_full}` 中每件都在（或裁切图中合理省略） | 缺 1+ 件 | 在 F-SUBJ 重新加入缺失单品+精确描述 |
| **2** | **鞋履位置** | 双脚都穿着鞋。不在手里、不在桌上、不在地上 | 手里提着鞋；鞋在桌上；鞋在地上；该穿鞋却光脚 | 加强：`shoes worn on both feet, not holding any footwear, no shoes on any surface` |
| **3** | **无幽灵配饰** | 只有 `{items_full}` 里的物品 | 脖子上口罩/围巾；头上多了帽子；手上多了手机；多了项链 | 加强：`no additional accessories, neck bare, no items in hands` |
| **4** | **人数正确** | exactly 1 或 exactly 2 人 | 背景多出半个人影；第三只手；多余肢体 | 加强人数约束 + 考虑裁切构图 |
| **5** | **手部正常** | 每只手 4-5 指、位置自然、无融合 | 多指；手指融合；缺手；手在奇怪位置 | **换姿势**（用手部不可见/自然的姿势）+ fidelity +0.05 |
| **6** | **产品一致性** | 颜色/材质/款式匹配参考图 | 裙子颜色错；普通袜代替蕾丝袜；包款不同 | 重新更精确描述标志性单品（加更多视觉细节） |
| **7** | **场景准确** | 场景/光线/氛围符合计划 | 计划画廊却变成咖啡馆；白天变夜晚 | 重写 F-ENV 更具体描述场景 |
| **8** | **真实感** | 皮肤自然、光线真实、无 CGI 塑料感 | 塑料皮肤；过曝高光；过饱和；水印 | 加强 F-TECH 相机滤镜语言；删 oversaturated 词 |

### 6.3 重生成规则

- **每张图最多重生成 1 次**
- **重生成时只修改失败的约束**，不改整个 prompt
- **连续 2 次失败 → 放弃该类别**，用替代方案（如 Couple 失败→改 solo Lifestyle）
- **最终汇总时列出所有失败记录**

---

## 七、两种输出模式

| 模式 | 视觉语言 | 默认 fidelity | 适用类目 |
|------|---------|--------------|---------|
| **Lifestyle Cinematic** (默认) | 按类目相机滤镜 + 胶片模拟 + 自然光 + 抓拍 | Char 0.62–0.75; flat 0.78; detail 0.65–0.75; couple 0.78 | Outfit / Lifestyle / Couple / Brand |
| **E-commerce Natural** | 有纹理表面 + 自然窗光 + 相机色彩科学暖调 | Char 0.78; flat 0.85; detail 0.82 | Outfit(真人) / Flat Lay / Details |

> E-com Natural 不是无菌白底。白底只在用户明确要求时用。

### `{avoid}` 块（仅 Lifestyle）
> `real photography not illustration not 3d render not CGI not anime, natural human skin visible pores, soft daylight not studio flash, candid natural moment, no stiff posed stock-photo look, no oversaturated colors, no watermark, no text overlay, no plastic waxy skin, no over-sharpened hyperreal CGI crispness, no AI smoothing, no glossy studio sheen, no artificial symmetric catalog framing, no floating composite look, exactly N people no other figures in frame`

### `{ecom_natural}` 辅助语（仅 E-com 用户要求时）
> `natural-light product photography on textured linen or wood surface, soft window light, shallow depth of field, camera color-science warmth, all items clearly visible and correctly placed, authentic e-commerce lookbook quality`

---

## 八、Fidelity 速查表

| Category | Lifestyle | E-com Natural |
|----------|-----------|---------------|
| Outfit | 0.62–0.75 | 0.78 |
| Flat Lay | 0.78 | 0.85 |
| Details | 0.65–0.75 | 0.82 |
| Lifestyle | 0.62–0.75 | (skip) |
| Couple·Friends | **0.78** | (skip) |
| Brand Story | 0.65 | (skip) |

---

## 九、防膨胀纪律

- 每个 prompt **80–140 词**
- 绝不堆 `8k/hyperrealistic/sharp focus/DSLR`
- 绝不含解剖学负面词
- 含 v8 完整 `{artifact_guard}`
- Flat Lay 含全部 `{items_full}`
- 含类目专属相机滤镜字符串
- **姿势来自 Pose Library（不是通用 "candid mid-step"）**
- **场景来自 Scene Pool（不是写死咖啡馆）**

---

## 十、命名与归档

- 目录：`{style}_{YYYYMMDD}/`
- 文件：`{NN}_{category}_{variant}.png`
- 尺寸：XHS `1080x1440` / Pinterest `1024x1536` / E-com `1024x1024`

---

## 十一、v9 参考图真实感升级（来自 31 张反推研究）

对 31 张高分真实样张做 AI 反推后确认：生成图"丑/像渲染"的主因是**场景假、光太硬、摆太正**。v9 强制 8 条规则（与 SKILL.md 同步）：

1. **真实地点，不要"白墙工作室"** —— 场景必须是带真实生活痕迹的具体场所（书店要有书、咖啡馆要有大理石小桌和虚化车流、布鲁克林褐石台阶要有盆栽绣球），描述环境真实细节。
2. **人物在"做事"，不是站着摆拍** —— 永远给主体一个与场景契合的动作：伸手取下层书架的书、走路中途停步看橱窗、笑着回应同伴、端冰咖啡望窗外。环境互动 > 姿势。
3. **胶片颗粒 + 自然光，永远有** —— 每个类目 F-TECH 收尾都带 `Kodak Portra 400 emulation, warm skin tones, gentle visible film grain, soft natural falloff`。禁止 "8k/hyperrealistic/sharp focus"。
4. **克制配色（最多 2–3 族）** —— 从参考图取色，写进 prompt（如 cream+burgundy+navy 或 blush+brown+olive）。
5. **平铺要"生活过"，不要冷白** —— 永远在带纹理表面 + 窗光 + 1–2 件日常道具（皱亚麻床单、翻开的书、陶瓷咖啡杯、时尚杂志、干蒲苇）上平铺。绝不用纯白无缝背景。
6. **抓拍亲密感 > 对称** —— 偏中心构图、浅景深、看向画外或同伴、排列带轻微不完美。
7. **真实皮肤与材质纹理** —— `natural skin with visible pores`, `authentic knit/leather/satin texture`, 禁 `glossy studio sheen / AI smoothing`。
8. **整套统一签名影调** —— 6 张用同一胶片模拟 + 同一色彩科学，像同一个摄影师拍的；除非 Brand Story 有意破调。

> 这 8 条是提升"像真照片"感知的最强杠杆，与旧"干净目录"默认值冲突时以这 8 条为准。

## 十二、v8 样例：动态构造演示

以下展示 **同一套产品（米色极简北欧 8 件单品）** 如何通过分析驱动产生不同于模板填空的 prompt。

### 产品分析结果（Step 2 输出）

```
风格族: Minimal Scandinavian
季节: Spring/Fall transitional
正式度: Casual-Smart (loafers elevate it slightly)
标志性单品: ①针织开衫(细腻针法+罗纹) ②乐福鞋(皮带横杠装饰)
配色: cream ivory / beige / camel monochromatic warm neutrals
鞋履类型: Penny loafers (flat) → 姿势库选「自然漫步/盘腿坐」
```

### 场景池（Step 4 输出）

| # | 场景 | 理由 | 光线 | 最佳类目 |
|---|------|------|------|---------|
| 1 | 独立书店晨光 | 极简×知性空间的天然匹配 | 清晨东窗柔光 | Outfit, Lifestyle |
| 2 | 明亮公寓窗边 | 居家极简生活方式 | 上午漫射光 | Lifestyle, Brand |
| 3 | 周末早午餐咖啡馆 | 社交场景但保持干净 | 明亮自然光 | Couple |
| 4 | 白墙工作室 | 产品展示级干净 | 顶部均匀自然光 | Flat Lay, Detail |

### 姿势分配（Step 5 输出）

| 类目 | 选定姿势 | 为什么 |
|------|---------|--------|
| Outfit | 「自然漫步中途停步，手臂放松，微微抬头笑」 | 乐福鞋=平底鞋→漫步姿势最自然 |
| Lifestyle | 「坐在窗边腿盘起，手持咖啡杯看外面」 | 乐福鞋→盘腿坐舒适且自然 |
| Couple | 「两人并坐咖啡桌，她笑着指窗外给他看」 | 坐姿+近距离互动=安全双人构图 |
| Flat Lay | 「Curated editorial 精确间距排列」 | 极简风格=整洁排列最有品牌感 |
| Detail | 「Texture shot 45°侧光→针织纹路」 | 标志性单品=开衫纹理 |
| Brand | 「Conscious living 叙事→椅上随手搭放+白牡丹」 | 极简× mindful living 故事角度 |

### 动态构造的 Outfit prompt（Step 6 输出）

注意这个 prompt 与 v7 模板填充版的区别——**场景、姿势、光线都来自分析而非默认值**：

```
Chinese female model natural makeup genuine candid expression wearing
cream ivory camisole tank top with thin straps scoop neckline tucked in,
beige fine-gauge knit cardigan with open front button closure long sleeves ribbed cuffs worn loosely over shoulders,
beige khaki high-waisted tailored shorts pleated front belt loops,
tan camel leather penny loafers with strap detail across vamp WORN ON BOTH FEET,
beige plain ankle crew socks WORN ON BOTH FEET,
gold-tone watch round white dial brown leather strap on wrist,
gold chain necklace small round disc coin pendant,
beige leather structured tote bag slung casually over one shoulder,

inside a bright minimalist independent bookstore with white walls and tall wooden shelves,
soft early morning window light streaming through large east-facing windows casting gentle long shadows,
minimal Scandinavian style with quiet intellectual warmth,
Xiaohongshu style natural soft daylight filmic muted tones intimate lifestyle feel authentic,

candid walking-pause shot she stopped mid-step looking up ahead with a gentle relaxed smile arms hanging naturally at her sides,
exactly one person no other figures in frame,
cream ivory beige camel monochromatic warm neutrals palette,

shot on Fujifilm X-T5 with XF35mm f/1.4 at f/2 Classic Chrome film simulation
natural morning side window light soft falloff shallow depth of field
warm skin tones visible pores authentic knit fabric texture subtle vignette
genuine unposed moment,

real photography not illustration not 3d render not CGI not anime
natural human skin visible pores soft daylight candid natural moment
no stiff posed no oversaturated no watermark no text overlay
exactly one person no other figures in frame
neck is bare no mask no face covering
both shoes worn on both feet
no footwear being held in hands or placed on tables or floors or surfaces
all items from reference set present and correctly worn
hands empty or naturally resting
no phantom accessories beyond listed items,
lifestyle photography
```

**vs v7 模板填充版的关键区别：**
- 姿势：v7 用通用 `mid-step looking aside` → v8 用 `walking-pause shot arms hanging naturally`（适合乐福鞋）
- 场景：v7 可能复用之前的 `art gallery` → v8 用分析的 `independent bookstore`（匹配极简知性）
- 光线：v7 用 generic `soft natural daylight` → v8 用 `early morning east-facing window light with long shadows`（具体到时间和方向）
- 鞋履约束：v7 用 `both shoes worn on both feet` → v8 加了 `WORN ON BOTH FEET` 在单品列表中和 `no footwear being held in hands` 在 guard 中

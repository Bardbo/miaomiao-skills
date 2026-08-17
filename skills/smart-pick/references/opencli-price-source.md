<<<<<<< HEAD
# OpenCLI 跨平台实时比价（smzdm 适配器）

## 背景

Smart-Pick 的 Step 4（外部方案搜索）默认用 `scripts/search_external.py`，但那只是个 mock。  
**真正的实时价格数据**可以通过 OpenCLI 的 `smzdm`（什么值得买）适配器获取——**PUBLIC 策略，无需登录**。

## 适配器信息

| 属性 | 值 |
|------|-----|
| 命令 | `opencli smzdm search <关键词> -f json` |
| 策略 | PUBLIC（纯 HTTP，无浏览器/登录需求） |
| 数据源 | 什么值得买（smzdm.com）聚合的京东/拼多多/天猫/抖音商城价格 |
| 返回字段 | title, price, mall（平台名）, url, comments, rank |

## 使用方式

```bash
# 搜索 RTX 5070 Ti
opencli smzdm search "RTX 5070 Ti 显卡" -f json

# 搜索更具体的商品
opencli smzdm search "耕升 5070Ti 追风" -f json
```

返回 JSON 数组，每条含 `mall`（平台来源）、`price`（价格文本）、`title`（商品名）、`url`（详情链接）、`comments`（评论数）。

## 输出处理

smzdm 的输出尾部会附带 OpenCLI 的更新提示（非 JSON），需要用 Python 提取纯 JSON 部分：

```python
import json
lines = output  # terminal 返回的 stdout
jstart = lines.index('[')
jend = lines.rindex(']') + 1
data = json.loads(lines[jstart:jend])
```

## 平台去重

同一商品可能出现在多个平台。以 `mall` 字段区分：

| mall 值 | 对应平台 | 备注 |
|---------|---------|------|
| `京东` | 京东自营/京东店铺 | 品牌授权，售后好 |
| `京东全球购` | 京东国际 | 跨境，可能有税 |
| `拼多多` | 拼多多百亿补贴 | 价格低，售后一般 |
| `抖音商城` | 抖音电商 | 第三方店铺，价格波动大，核实后再采信 |
| `天猫精选`/`天猫国际` | 天猫/天猫国际 | 品牌旗舰店为主 |
| `淘宝` | 淘宝C店 | 个人店铺 |

## 注意事项

1. **价格是文本**——包含"¥"、"元"、"需用券"、"百亿补贴"等修饰，需要清洗后转为数值
2. **结果可能有整机**——搜索显卡时会混入组装电脑整机，需按标题关键词过滤（排除"主机/电脑/台式/组装/整机/DIY"）
3. **抖音商城价格可能不实**——部分商家用低价引流标价，实际非该型号，需用"⚠️"标注提醒用户核实
4. **smzdm 搜索结果非全量**——只聚合了值得买站内的好价爆料，不是平台全量商品库
5. **闲鱼需要登录**——`opencli xianyu` 是 COOKIE 策略，需要用户已在 Chrome 登录闲鱼
=======
# OpenCLI 跨平台实时比价（smzdm 适配器）

## 背景

Smart-Pick 的 Step 4（外部方案搜索）默认用 `scripts/search_external.py`，但那只是个 mock。  
**真正的实时价格数据**可以通过 OpenCLI 的 `smzdm`（什么值得买）适配器获取——**PUBLIC 策略，无需登录**。

## 适配器信息

| 属性 | 值 |
|------|-----|
| 命令 | `opencli smzdm search <关键词> -f json` |
| 策略 | PUBLIC（纯 HTTP，无浏览器/登录需求） |
| 数据源 | 什么值得买（smzdm.com）聚合的京东/拼多多/天猫/抖音商城价格 |
| 返回字段 | title, price, mall（平台名）, url, comments, rank |

## 使用方式

```bash
# 搜索 RTX 5070 Ti
opencli smzdm search "RTX 5070 Ti 显卡" -f json

# 搜索更具体的商品
opencli smzdm search "耕升 5070Ti 追风" -f json
```

返回 JSON 数组，每条含 `mall`（平台来源）、`price`（价格文本）、`title`（商品名）、`url`（详情链接）、`comments`（评论数）。

## 输出处理

smzdm 的输出尾部会附带 OpenCLI 的更新提示（非 JSON），需要用 Python 提取纯 JSON 部分：

```python
import json
lines = output  # terminal 返回的 stdout
jstart = lines.index('[')
jend = lines.rindex(']') + 1
data = json.loads(lines[jstart:jend])
```

## 平台去重

同一商品可能出现在多个平台。以 `mall` 字段区分：

| mall 值 | 对应平台 | 备注 |
|---------|---------|------|
| `京东` | 京东自营/京东店铺 | 品牌授权，售后好 |
| `京东全球购` | 京东国际 | 跨境，可能有税 |
| `拼多多` | 拼多多百亿补贴 | 价格低，售后一般 |
| `抖音商城` | 抖音电商 | 第三方店铺，价格波动大，核实后再采信 |
| `天猫精选`/`天猫国际` | 天猫/天猫国际 | 品牌旗舰店为主 |
| `淘宝` | 淘宝C店 | 个人店铺 |

## 注意事项

1. **价格是文本**——包含"¥"、"元"、"需用券"、"百亿补贴"等修饰，需要清洗后转为数值
2. **结果可能有整机**——搜索显卡时会混入组装电脑整机，需按标题关键词过滤（排除"主机/电脑/台式/组装/整机/DIY"）
3. **抖音商城价格可能不实**——部分商家用低价引流标价，实际非该型号，需用"⚠️"标注提醒用户核实
4. **smzdm 搜索结果非全量**——只聚合了值得买站内的好价爆料，不是平台全量商品库
5. **闲鱼需要登录**——`opencli xianyu` 是 COOKIE 策略，需要用户已在 Chrome 登录闲鱼
>>>>>>> 75cadf3 (feat: Smart-Pick（慧选）v2.1 — 通用多方案权衡助手)

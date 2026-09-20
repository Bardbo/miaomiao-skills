# TypeSafe jev API 浓缩参考

> 官方文档为 source of truth：索引 `https://docs.typesafe.ai/llms.txt`；本文档如有出入以官方为准。

## 端点与认证

```
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <TYPESAFE_API_KEY>
Content-Type: application/json
```

模型：`jev-latest`（别名，当前解析到 jev-1.13.0）；响应 `model` 字段报告实际版本。
`GET /v1/models` 可列别名。

## 请求体

```json
{
  "state": "要评估的内容（字符串或对象/数组）",
  "model": "jev-latest",
  "questions": {
    "q1": { "type": "choice", "instructions": "题干", "criteria": {"A": "选项A", "B": "选项B"} },
    "q2": { "type": "score", "instructions": "题干", "criteria": ["等级0描述", "等级1描述", "等级2描述"] },
    "q3": { "type": "noul", "instructions": "是非陈述" }
  }
}
```

- questions 的 key 自选，仅代码用，**模型看不到**
- `instructions`/`criteria` 可为字符串、对象或数组（结构化描述+示例可显著提升判别力）
- choice 最多 **255** 个选项；score 2~10 个等级
- 所有问题并行评估（fan-out）：一次调用塞满整份问卷是官方推荐形态，加题几乎不加耗时

## 响应体

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "q1": { "type": "choice", "choice": "A", "probabilities": {"A": 0.91, "B": 0.09}, "confidence": 0.83 },
    "q2": { "type": "score", "score": 1.43, "legend": {"0": "...", "1": "...", "2": "..."}, "probabilities": {"0": 0, "1": 0.57, "2": 0.43}, "confidence": 0.35 },
    "q3": { "type": "noul", "noul": 0.999, "confidence": 0.99 }
  },
  "usage": { "input_tokens": 7601, "output_tokens": 2784 }
}
```

- choice：`choice` 为最高概率选项；`probabilities` 和为 1；`confidence` 由分布形状决定（单峰=高）
- score：`score` = 各等级编号×概率加权均值（0~N，可落两档之间）；`legend` 为编号→描述映射
- noul：`noul` 为「是」的概率；**接近 0.5 是「拿不准」，不是中等强度**

## 价格与限流（2026-09 实测）

- 按**输入 token** 计费，输出免费：$42 / 十亿 token（$0.042 / 百万 token）
- 限流：250,000 tokens/s、1,200 请求/分钟，超限 429
- 实测：93 题中文 choice（7.6K input tokens）一次调用 2.1s、约 $0.32——多 state 总成本 ≈ N_image×$0.3 量级
- SDK 默认带退避重试；手写 HTTP 时 429 需读 retry-after

## 错误码应对

| 状态 | 含义 | 应对 |
|---|---|---|
| 401 | key 无效 | 提示用户检查 key |
| 402 | 余额不足 | 提示充值；询问是否走兜底 |
| 429 | 限流 | 退避重试（指数退避，尊重 retry-after） |
| 5xx/网络 | 服务故障 | 重试后仍失败→提示并走兜底链 |

## 官方链接

- 文档索引: https://docs.typesafe.ai/llms.txt
- API 参考: https://docs.typesafe.ai/api.md
- Choice: https://docs.typesafe.ai/primitives/choice.md
- Score: https://docs.typesafe.ai/primitives/score.md
- Noul: https://docs.typesafe.ai/primitives/noul.md
- 官方 agent skill: https://github.com/typesafe-ai/skills （`skills/typesafe-ai/SKILL.md`）

<<<<<<< HEAD
#!/usr/bin/env python3
"""
Smart-Pick 外部搜索脚本（Mock 示例版）

使用方法：
    python search_external.py --query "空气炸锅 500-800元 推荐" --limit 3

如需真实搜索，请在以下API中选择一个接入：
- SerpAPI (https://serpapi.com) — Google Shopping 搜索
- 淘宝客API — 淘宝商品搜索
- 京东联盟API — 京东商品搜索
- DuckDuckGo — 免费，但搜索结果较粗糙

返回格式：JSON 数组
[
  {
    "name": "商品/方案名称",
    "price": 金额(float),
    "dimensions": {"核心价值": "描述", "风险": "描述"},
    "source": "来源网址"
  }
]
"""

import json
import argparse
import sys

MOCK_DATA = {
    "空气炸锅": [
        {
            "name": "山本 SB-6 空气炸锅",
            "price": 599.00,
            "dimensions": {
                "核心价值": "5.5L大容量，1500W功率，360度热风循环",
                "风险": "品牌知名度低于飞利浦，售后网点较少"
            },
            "source": "https://example.com/shanben-sb6"
        },
        {
            "name": "九阳 KL55-VF517",
            "price": 429.00,
            "dimensions": {
                "核心价值": "5.5L容量，可视窗口，不粘内胆",
                "风险": "塑料外壳质感一般"
            },
            "source": "https://example.com/jiuyang-kl55"
        }
    ],
    "手机": [
        {
            "name": "一加 13",
            "price": 4499.00,
            "dimensions": {
                "核心价值": "骁龙8至尊版，6000mAh电池，100W快充",
                "风险": "系统更新周期相对较短"
            },
            "source": "https://example.com/oneplus-13"
        }
    ]
}


def search(query: str, limit: int = 3) -> list:
    """Mock search - 在实际使用时替换为真实API调用"""
    query_lower = query.lower()

    # 尝试匹配已知类别
    for keyword, results in MOCK_DATA.items():
        if keyword in query_lower:
            return results[:limit]

    # 未匹配到任何已知类别，返回空
    return []


def main():
    parser = argparse.ArgumentParser(description="Smart-Pick 外部搜索")
    parser.add_argument("--query", required=True, help="搜索关键词")
    parser.add_argument("--limit", type=int, default=3, help="返回结果数量上限")
    args = parser.parse_args()

    results = search(args.query, args.limit)

    if not results:
        print(json.dumps([], ensure_ascii=False))
        print("[提示] 未配置外部搜索API，请手动提供候选方案。", file=sys.stderr)
        return

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
=======
#!/usr/bin/env python3
"""
Smart-Pick 外部搜索脚本（Mock 示例版）

使用方法：
    python search_external.py --query "空气炸锅 500-800元 推荐" --limit 3

如需真实搜索，请在以下API中选择一个接入：
- SerpAPI (https://serpapi.com) — Google Shopping 搜索
- 淘宝客API — 淘宝商品搜索
- 京东联盟API — 京东商品搜索
- DuckDuckGo — 免费，但搜索结果较粗糙

返回格式：JSON 数组
[
  {
    "name": "商品/方案名称",
    "price": 金额(float),
    "dimensions": {"核心价值": "描述", "风险": "描述"},
    "source": "来源网址"
  }
]
"""

import json
import argparse
import sys

MOCK_DATA = {
    "空气炸锅": [
        {
            "name": "山本 SB-6 空气炸锅",
            "price": 599.00,
            "dimensions": {
                "核心价值": "5.5L大容量，1500W功率，360度热风循环",
                "风险": "品牌知名度低于飞利浦，售后网点较少"
            },
            "source": "https://example.com/shanben-sb6"
        },
        {
            "name": "九阳 KL55-VF517",
            "price": 429.00,
            "dimensions": {
                "核心价值": "5.5L容量，可视窗口，不粘内胆",
                "风险": "塑料外壳质感一般"
            },
            "source": "https://example.com/jiuyang-kl55"
        }
    ],
    "手机": [
        {
            "name": "一加 13",
            "price": 4499.00,
            "dimensions": {
                "核心价值": "骁龙8至尊版，6000mAh电池，100W快充",
                "风险": "系统更新周期相对较短"
            },
            "source": "https://example.com/oneplus-13"
        }
    ]
}


def search(query: str, limit: int = 3) -> list:
    """Mock search - 在实际使用时替换为真实API调用"""
    query_lower = query.lower()

    # 尝试匹配已知类别
    for keyword, results in MOCK_DATA.items():
        if keyword in query_lower:
            return results[:limit]

    # 未匹配到任何已知类别，返回空
    return []


def main():
    parser = argparse.ArgumentParser(description="Smart-Pick 外部搜索")
    parser.add_argument("--query", required=True, help="搜索关键词")
    parser.add_argument("--limit", type=int, default=3, help="返回结果数量上限")
    args = parser.parse_args()

    results = search(args.query, args.limit)

    if not results:
        print(json.dumps([], ensure_ascii=False))
        print("[提示] 未配置外部搜索API，请手动提供候选方案。", file=sys.stderr)
        return

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
>>>>>>> 75cadf3 (feat: Smart-Pick（慧选）v2.1 — 通用多方案权衡助手)

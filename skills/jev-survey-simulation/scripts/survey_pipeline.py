#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jev-survey 管道：每 state 一次调用填整份问卷 → 按比例复制(带噪声) → 汇总统计。

用法:
    TYPESAFE_API_KEY=xxx python survey_pipeline.py spec.json [--out DIR]

spec.json 结构:
{
  "total_n": 100,
  "items": [
    {"id": "q1", "type": "choice", "question": "题干", "criteria": {"A": "选项A", "B": "选项B"}},
    {"id": "q2", "type": "score",  "question": "题干", "levels": ["低...", "中...", "高..."]},
    {"id": "q3", "type": "noul",   "question": "是非陈述"},
    {"id": "q4", "type": "open",   "question": "开放题(不走jev)"}
  ],
  "states": [
    {"id": "s1", "label": "大四机械男生", "proportion": 0.5, "state": "...", "open_answers": {"q4": "..."}}
  ]
}

产物(默认写到 spec 同目录): responses.json(逐份) / responses.csv(长表) / summary.json(总体统计+置信度)
天然按 probabilities 加权采样生成逐份副本(种子=state+副本号，可复现)。
"""
import csv, json, os, random, sys, time, urllib.request, urllib.error

API = "https://api.typesafe.ai/v1/systemone"

def call(body, key):
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429 and attempt < 3:
                time.sleep(min(2 ** attempt * 5, 30)); continue
            raise RuntimeError(f"HTTP {e.code}: {err}")
        except (urllib.error.URLError, TimeoutError):
            if attempt < 3:
                time.sleep(2 ** attempt * 3); continue
            raise
    raise RuntimeError("retries exhausted")

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        print("错误: 缺少 TYPESAFE_API_KEY 环境变量（无法调用 jev）。")
        print("兜底选项: 1) 提供 key 重试  2) 宿主 agent 代填  3) 无AI规则引擎(需要 spec 含 per-profile 模板答案)")
        sys.exit(2)

    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    outdir = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--out" else os.path.dirname(os.path.abspath(sys.argv[1]))
    os.makedirs(outdir, exist_ok=True)

    items = spec["items"]; states = spec["states"]; N = int(spec["total_n"])
    jev_items = [it for it in items if it["type"] != "open"]
    total_in = 0; results = []  # (state, base_answer_map)

    # --- jev 批填: 每 state 一次调用 ---
    for st in states:
        questions = {}
        for it in jev_items:
            if it["type"] == "choice":
                questions[it["id"]] = {"type": "choice", "instructions": it["question"], "criteria": it["criteria"]}
            elif it["type"] == "score":
                questions[it["id"]] = {"type": "score", "instructions": it["question"], "criteria": it["levels"]}
            elif it["type"] == "noul":
                questions[it["id"]] = {"type": "noul", "instructions": it["question"]}
        body = {"state": st["state"], "model": "jev-latest", "questions": questions}
        resp = call(body, key)
        total_in += resp.get("usage", {}).get("input_tokens", 0)
        results.append((st, resp["answers"]))
        print(f"  {st['id']} [{st['label']}]: {len(resp['answers'])} 题, "
              f"in_tokens={resp['usage']['input_tokens']}, model={resp.get('model')}")

    cost = total_in / 1e9 * 42
    print(f"jev 调用于 {len(states)} 个 state，共 {total_in} input tokens，估算成本 ${cost:.4f}")

    # --- 按比例分配份数（最大余数法） ---
    raw = [N * st["proportion"] for st in states]
    floors = [int(x) for x in raw]
    remain = N - sum(floors)
    order = sorted(range(len(states)), key=lambda i: raw[i] - floors[i], reverse=True)
    for i in order[:remain]:
        floors[i] += 1

    # --- 逐份采样生成 ---
    rows = []
    for si, (st, ans) in enumerate(results):
        base = {it["id"]: ans[it["id"]] for it in jev_items}
        for k in range(floors[si]):
            rng = random.Random(f"{st['id']}-{k}")
            copy = {"copy_id": f"{st['id']}_{k+1:03d}", "state_id": st["id"], "state_label": st["label"]}
            for it in items:
                wid = it["id"]
                if it["type"] == "open":
                    copy[wid] = st.get("open_answers", {}).get(wid, "")
                    continue
                a = base[wid]
                if it["type"] == "choice":
                    opts = list(it["criteria"].keys())
                    probs = [a["probabilities"].get(o, 0) for o in opts]
                    copy[wid] = rng.choices(opts, weights=probs, k=1)[0]
                elif it["type"] == "score":
                    lv = list(range(len(it["levels"])))
                    probs = [a["probabilities"].get(str(i), 0) for i in lv]
                    copy[wid] = rng.choices(lv, weights=probs, k=1)[0]
                elif it["type"] == "noul":
                    copy[wid] = "是" if rng.random() < a["noul"] else "否"
            rows.append(copy)

    # --- 汇总统计 ---
    summary = {"total_n": N, "states": [{"id": st["id"], "label": st["label"], "proportion": st["proportion"], "copies": c}
               for st, c in zip(states, floors)]}
    for it in items:
        counts = {}
        for r in rows:
            v = r[it["id"]]
            counts[v] = counts.get(v, 0) + 1
        summary[it["id"]] = {"type": it["type"], "question": it["question"], "counts": counts}

    # --- 置信度统计（SKILL.md 承诺的质量指标） ---
    summary["confidence"] = {}
    for si, (st, ans) in enumerate(results):
        for it in jev_items:
            a = ans[it["id"]]
            if it["type"] == "noul":
                # noul 不返回单独 confidence；用 |noul-0.5|*2 折算（越接近0.5越不确定）
                c = abs(a.get("noul", 0.5) - 0.5) * 2
            else:
                c = a.get("confidence")
            summary["confidence"].setdefault(it["id"], {})[st["id"]] = c
    low = {}
    for it in jev_items:
        bad = [st["id"] for st in states
               if (summary["confidence"][it["id"]].get(st["id"]) or 0) < 0.6]
        if bad:
            low[it["id"]] = bad
    summary["low_confidence_items"] = low
    if low:
        for qid, stlist in low.items():
            print(f"  低置信度(<0.6): [{qid}] 在 state {stlist} 中模型判断模糊，答案可信度较低")

    base = os.path.join(outdir, "responses")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"已生成 {N} 份 -> {base}.json / {base}.csv / summary.json")

if __name__ == "__main__":
    main()
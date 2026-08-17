"""
按场景批次生成 — 每个话题生成一轮完整的两人对话（巴菲特+芒格各一句）。
14句 = 7次API调用。每次调用携带完整历史。
"""

import json, requests, yaml, re, time

config = yaml.safe_load(open('config.yaml'))
api_key = config['model']['api_key']
base_url = config['model']['base_url'].rstrip('/')
model = "deepseek-v4-flash"

OUTPUT = "output.md"

SCENES = [
    {
        "topic": "中介思维",
        "guide": "巴菲特以弹子球机故事开场（他什么都没生产，只是把机器放理发店当中间人），强调信息差+服务=差价。芒格回应并延伸——点出中介的天花板及如何突破。"
    },
    {
        "topic": "产品思维",
        "guide": "芒格先指出中介的天花板（信息差会消失），巴菲特用See's Chocolate接上——定价权来自'非你不可'。产品不是做最好的东西，是让人不得不买。禁止再用farm/棒球类比。"
    },
    {
        "topic": "平台思维（中介+产品=平台）",
        "guide": "巴菲特用美国运通举例：旅行支票是产品，兑付网络是中介，既是抽成又是入驻费。芒格剖析平台本质和陷阱。禁止再用farm/棒球/修鞋类比。"
    },
    {
        "topic": "杠杆思维",
        "guide": "巴菲特从保险浮存金说起（品牌/声誉/系统杠杆），芒格延伸出技术杠杆和自身优势发掘。核心：不用还的杠杆。禁止再用farm/棒球类比。"
    },
    {
        "topic": "耐心：钱是坐着等来的",
        "guide": "巴菲特用Ted Williams击球区理论切入——不是每球都挥。芒格用反例点出多数人在等死不是在等机会。核心：选对之后不动摇。禁止再用farm/棒球类比。"
    },
    {
        "topic": "坚持，不要脸，坚持不要脸",
        "guide": "芒格用自己做律师被拒三次第四次成功的经历开场。巴菲特接上自己不怕问问题不怕丢脸的故事。核心：扛得住拒绝，承认自己不会不是丢人。"
    },
    {
        "topic": "初心：善良、真诚、认真地活",
        "guide": "巴菲特用'愿不愿意把女儿嫁给他'的标准收束，芒格总结所有赚钱思维模式归结到'靠谱'。核心：不骗人不偷工减料不杀鸡取卵，诚信是一切的基础。"
    }
]

SYSTEM_TEMPLATE = """你正在模拟一段巴菲特和芒格之间的自然对话。用第一人称「我」说话，称呼对方用「你」。

【当前话题】{topic}
【场景引导】{guide}

【角色规则】
巴菲特：短句口语，自嘲干燥幽默，用类比（但不是farm/棒球/修鞋，换新类比）。
芒格：简短锐利，讽刺但不用粗俗词。
句式：两人都要变换句式开头。禁止「你说得对，查理」「你发现没有」「说到这个，让我想起」「我记得有一回」「我讲个例子」「你猜怎么着」等已用句式。

【严格禁令】
- 禁止使用farm/农场/棒球/修鞋铺等本次对话已用过的类比。
- 禁止以「你说得对，查理」开头。
- 禁止以「你发现没有」开头。
- 禁止以「说到XX，让我想起」开头。
- 每个话题用完全不同的故事类别。

【格式】输出格式严格如下，不要加额外文字：
**巴菲特：** （台词）
**芒格：** （台词）

【对话历史】
{history}

请生成第 {num} 轮对话（两人各一句）："""

print("Testing API...")
resp = requests.post(f"{base_url}/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={"model": model, "messages": [{"role": "user", "content": "Say 42"}], "max_tokens": 10}, timeout=15)
assert 'choices' in resp.json(), f"API error: {resp.json()}"
print("API OK.\n")

history = []
used_openers = []

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("# 巴菲特与芒格谈赚钱的思维模式\n\n")

for i, scene in enumerate(SCENES, 1):
    hist_text = "\n".join(history[-8:]) if history else "（对话刚开始）"
    
    prompt = SYSTEM_TEMPLATE.format(
        topic=scene["topic"],
        guide=scene["guide"],
        history=hist_text,
        num=i
    )

    for attempt in range(3):
        try:
            resp = requests.post(f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 600, "temperature": 0.85}, timeout=60)
            data = resp.json()
            if 'choices' not in data:
                if 'rpm' in str(data).lower():
                    print(f"  [场景{i}] RPM, 等待10s..."); time.sleep(10); continue
                print(f"  [场景{i}] skip: {str(data)[:100]}"); break

            raw = data['choices'][0]['message']['content'].strip()
            # Parse out lines
            lines = raw.split('\n')
            buffett_line = ""
            munger_line = ""
            for line in lines:
                line = line.strip()
                if line.startswith("**巴菲特：**") or line.startswith("**巴菲特：") or line.startswith("巴菲特："):
                    buffett_line = re.sub(r'^[*]*巴菲特[：:]**?\s*', '', line)
                elif line.startswith("**芒格：**") or line.startswith("**芒格：") or line.startswith("芒格："):
                    munger_line = re.sub(r'^[*]*芒格[：:]**?\s*', '', line)
            
            if not buffett_line or not munger_line:
                print(f"  [场景{i}] bad format, retry...")
                print(f"  Raw: {raw[:100]}")
                time.sleep(2); continue

            with open(OUTPUT, "a", encoding="utf-8") as f:
                f.write(f"**巴菲特：** {buffett_line}\n\n")
                f.write(f"**芒格：** {munger_line}\n\n")
            
            history.append(f"巴菲特：{buffett_line}")
            history.append(f"芒格：{munger_line}")
            print(f"[场景{i}/7] ✅ 中介→产品→平台→杠杆→耐心→坚持→初心")
            time.sleep(1)
            break
        except Exception as e:
            print(f"  [场景{i}] {e}"); time.sleep(3); continue

with open(OUTPUT, "a", encoding="utf-8") as f:
    f.write("\n> *对话中部分内容为基于角色公开信息的合理推断，不代表角色实际说过或做过。*\n")

print(f"\n✅ Done! {len(history)} lines -> {OUTPUT}")
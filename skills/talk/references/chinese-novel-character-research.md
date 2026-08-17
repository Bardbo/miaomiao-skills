# 中文网文角色调研（Baidu Baike 提取）

当对话角色来自中文网文（如《十日终焉》《诡秘之主》《道诡异仙》等），且无现成 persona skill 时，用此方法快速获取角色特征。

## 优先级链（从 talk.skill Step 1）

1. 本地已安装 skills → `persona_detector.py detect`
2. 仓库搜索 → 同上
3. **nuwa 蒸馏 → 必须询问用户，不可跳过**
4. Fallback 构建（本方法的下游）

## Baidu Baike 信息来源

百度百科通常包含以下信息结构（以《十日终焉》为例）：
- **H2: 主要角色介绍**
- **H3: 角色名** — 性格特征及描述 / 角色语录 / 关联角色

## 提取方法（推荐用 browser 工具，勿用 delegate_task）

**🔥 不要用 delegate_task 搜索中文网文角色资料。** delegate_task 对于中文小说角色搜索存在两个致命问题：
1. 超时频繁（搜索 + 解析通常在 20s+，远超子代理默认超时）
2. 无法可靠提取百度百科的动态 DOM（子代理无 browser 工具）

**正确做法：在主会话中直接用 browser 工具** — browser_navigate 到百度百科页面，然后用 browser_console 执行 JS DOM 遍历提取。

### 1. 找到百度百科页面的角色章节

```javascript
// 在 browser_console 中运行
Array.from(document.querySelectorAll('h2,h3')).map(h => ({
  tag: h.tagName,
  text: h.textContent.trim(),
  id: h.id
})).filter(h => h.text.includes('角色') || h.text.includes('人物') || h.text.includes('主角'))
```

### 2. 提取每个角色的完整描述

```javascript
let s={},k=null;
let w=document.createTreeWalker(document.body,NodeFilter.SHOW_ALL);
while(w.nextNode()){
  let n=w.currentNode;
  if(n.nodeType==1&&n.tagName=='H3'){
    let t=n.textContent.trim();
    // 根据实际角色名调整匹配
    if(t=='齐夏'||t=='齐夏「白羊」'){k='齐夏'}
    else if(t=='陈俊南'){k='陈俊南'}
    else if(t=='乔家劲'){k='乔家劲'}
    else{k=null}
  }
  if(k&&n.nodeType==3){
    let t=n.textContent.trim();
    if(t&&!['SCRIPT','STYLE','SUP'].includes(n.parentElement.tagName)){
      if(!s[k]) s[k]=[];
      s[k].push(t)
    }
  }
}
JSON.stringify(s)
```

### 3. 从提取结果中构建硬约束表

从「性格特征及描述」「角色语录」「关联角色」中抓取关键信号：

| 角色 | 句数上限 | 禁止句式 | 必须出现 | 开头规则 | 情绪基调 |
|------|---------|---------|---------|---------|---------|
| 齐夏 | ≤3句 | 禁长篇解释/激动语气 | 每4轮一次逻辑分析 | 判断句或沉默接话 | 冷静漠然 |
| 陈俊南 | ≤4句 | 禁文艺煽情 | 每3轮一次口禅/京腔 | 「嘿」「我操」「小爷」 | 混不吝 |
| 乔家劲 | ≤4句 | 禁文绉绉 | 每3轮一次绰号 | 「我丢」「大脑」 | 热情单纯 |

## 注意事项

- Bilibili/知乎角色分析文章也可能有有用信息，但 Baidu Baike 结构最统一
- 提取的"角色语录"直接作为对话风格参考
- 昵称/绰号体系（如乔家劲叫齐夏"骗人仔"、陈俊南"俊男仔"）是保持神似的重要细节
- 百度百科的可能含剧透，标注给用户

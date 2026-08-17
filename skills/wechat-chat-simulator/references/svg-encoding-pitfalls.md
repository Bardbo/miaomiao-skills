# SVG Encoding Pitfalls for WeChat Chat Simulator

## Problem: SVG Gradient Double-Encoding

When avatar SVGs use `<linearGradient id="gb">` referenced via `fill="url(#gb)"`, the `encodeURIComponent()` call double-encodes the `#`:

```
Original SVG: fill="url(#gb)"
After encodeURIComponent: fill="url(%2523gb)"
```

The browser sees `url(%2523gb)` and does NOT recognize `%2523` as `#`. The gradient fails silently → avatar renders as a flat gray/black circle.

**Fix:** Use solid `fill="#RRGGBB"` instead of `url(#gradientId)`.

## Problem: SVG Quote Collision in JS Strings

SVG attributes must use double quotes (`xmlns="..."`) because the JS variable wrapping the SVG uses single quotes:

```javascript
// WRONG — single quotes in SVG break JS string:
var svg = '<svg xmlns='http://www.w3.org/2000/svg'>...';  // JS error!

// CORRECT — double quotes in SVG:
var svg = '<svg xmlns="http://www.w3.org/2000/svg">...';
```

## Correct Pattern (2026-06-18 verified)

```javascript
var buffettAvatarSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#667eea"/><text x="50" y="68" text-anchor="middle" font-size="52" fill="white" font-weight="bold" font-family="sans-serif">巴</text></svg>';
var jobsAvatarSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#4facfe"/><text x="50" y="68" text-anchor="middle" font-size="52" fill="white" font-weight="bold" font-family="sans-serif">乔</text></svg>';

function getAvatarUrl(speaker) {
    if (speaker === '巴菲特') return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(buffettAvatarSvg);
    if (speaker === '乔布斯') return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(jobsAvatarSvg);
    // fallback
}
```

Key rules:
1. SVG attributes: double quotes
2. JS string wrapper: single quotes
3. Fill color: direct hex (`#RRGGBB`), NOT gradient `url(#id)`
4. Encoding: `encodeURIComponent()` NOT `btoa()`

## MD Parsing — Two Possible Formats (2026-06-18)

Source dialogue MD from `talk.skill` uses `**角色名：** 内容` — colon INSIDE bold markers:

```markdown
**巴菲特：** 我认识一个做软件的人...
**乔布斯：** 你刚才说的那番话...
```

**Correct regex:** `\*\*(.+?)：\*\*\s*(.*)` — captures speaker inside the `**...**` group (before the closing `**`), then the colon is literal after `**`.

**Wrong regex:** `\*\*(.+?)\*\*[:：]\s*(.*)` — this looks for colon AFTER `**...**` but the colon is BEFORE it. Result: 0 matches, empty dialogues array.

**Alternative format** (some older conversations): `**角色名**: 内容` — colon OUTSIDE bold. The paragraph-split + `\*\*(.+?)：\*\*\s*(.*)` pattern handles BOTH because the colon character `：` is consumed by the greedy `.+?` in the first case, and in the second case the colon is a literal separator.

**Robust approach:** Split by `\n\n` (paragraphs), then match each paragraph with `\*\*(.+?)[:：]\*\*\s*(.*)` — the `[:：]` character class handles both `:` and `：`.

## Screenshot Limitation — DOM Verification Required (2026-06-18)

Browser screenshot tool always captures the **bottom of the page** (scroll position stuck at bottom due to `scrollToBottom()` on load). For long conversations (>10 messages), you cannot see the first messages in screenshots.

**Verification method:** Always use `browser_console` to check:
```javascript
// Total message count
document.querySelectorAll('.message-row').length
// First message text
document.querySelectorAll('.message-row')[0]?.querySelector('.message-bubble')?.textContent?.substring(0, 60)
// Avatar count
document.querySelectorAll('.avatar').length
```

If total count matches expected dialogue count, the rendering is correct regardless of what the screenshot shows.

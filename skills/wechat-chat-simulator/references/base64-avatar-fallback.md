# Base64 Avatar Generation for WeChat Chat Simulator

## Problem
External dicebear URLs (`https://api.dicebear.com/7.x/avataaars/svg?seed=...`) may fail to render when the HTML is opened via `file://` protocol. The image element exists in DOM (checked via `getComputedStyle` and `naturalWidth`) but appears invisible in screenshots.

## Fix: Inline SVG Data URIs with encodeURIComponent

**Use `encodeURIComponent()`, NOT `btoa()`.** `btoa()` throws on special characters and silently breaks the page.

```javascript
// WRONG - will throw JS exception silently:
var svg = '<svg>...</svg>';
var src = 'data:image/svg+xml;base64,' + btoa(svg);

// CORRECT - safe for all SVG content:
var svg = '<svg>...</svg>';
var src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
```

### Why encodeURIComponent over btoa?
- `btoa()` only works with ASCII characters. SVG contains `<`, `>`, `&`, `#`, quotes, etc.
- `encodeURIComponent()` safely encodes all characters for URI embedding
- `btoa()` failure causes a silent JS exception → page stops loading → no messages render

## Avatar Color: Solid vs Gradient (CRITICAL — 2026-06-18)

**Always use solid colors (`fill="#RRGGBB"`), NEVER gradients (`fill="url(#id)"`) in avatar SVGs.**

### Why gradients fail:
1. Original SVG: `<circle fill="url(#gb)"/>`
2. Passed to `encodeURIComponent()`: `fill="url(%2523gb)"` — the `#` is encoded to `%23`, but `%23` itself gets encoded AGAIN to `%2523`
3. Browser sees `url(%2523gb)` — this is NOT recognized as a gradient reference
4. Gradient silently fails → circle renders as flat gray/black

### Example:
```javascript
// WRONG — gradient (will render as gray):
var svg = '<svg><circle fill="url(#myGrad)"/></svg>';

// CORRECT — solid color (always works):
var svg = '<svg><circle fill="#667eea"/></svg>';
```

### Verified working avatar pattern:
```javascript
var buffettAvatarSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">' +
  '<circle cx="50" cy="50" r="50" fill="#667eea"/>' +
  '<text x="50" y="68" text-anchor="middle" font-size="52" fill="white" font-weight="bold" font-family="sans-serif">巴</text>' +
'</svg>';
```

## SVG Quote Rules (CRITICAL)

SVG attributes MUST use double quotes because JS wraps the SVG in single quotes:

```javascript
// WRONG — single quotes in SVG terminate the JS string:
var svg = '<svg xmlns='http://...'>';  // SyntaxError!

// CORRECT — double quotes in SVG:
var svg = '<svg xmlns="http://...'>';   // Works
```

## SVG Structure
- Outer circle: colored background (`fill=%23XXXXXX` — `%23` = `#` URL-encoded)
- Head: smaller circle at top
- Body: ellipse at bottom
- Colors: blue (`b6e3f4`) for left speaker, purple (`c0aede`) for right speaker

## Debugging Checklist
1. Check DOM: `document.querySelectorAll('.message-row.bot .avatar').length` — should match message count
2. Check CSS: `getComputedStyle(av).display` should be `block`, `visibility` should be `visible`
3. Check dimensions: `naturalWidth` should be > 0
4. Check innerHTML: avatar element should be first child of `.message-row`
5. If all pass but invisible → file:// protocol issue → switch to base64 SVG

## Alternative: Better Dicebear Seeds
If you prefer external URLs, use SHORTER alphanumeric seeds:
- Bad: `BerkshireBuffett` (too long, may fail)
- Good: `Warren` or `Buffett` (short, reliable)
- Bad: `CharlieMungerWithGlasses` 
- Good: `Charlie`

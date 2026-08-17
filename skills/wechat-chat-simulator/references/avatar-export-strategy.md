# Avatar Source Strategy — Local File vs Base64 (Tainted Canvas Trade-off)

> This reference documents the fundamental tension between HTML file size and html2canvas exportability when embedding avatar photos in `file://` protocol.

## The Core Problem

html2canvas in `file://` protocol cannot export a canvas that contains images from local file paths. The error:

```
Failed to execute 'toDataURL' on 'HTMLCanvasElement': Tainted canvases may not be exported.
```

**Why:** The browser treats `file://` as an opaque origin. Loading `<img src="巴菲特.jpeg">` — even from the same directory — creates a cross-origin image. The canvas is "tainted" and `toDataURL()` / `toBlob()` are blocked.

**Fix:** Use `useCORS: false` + data URIs (base64 or inline SVG) for avatar sources. Data URIs are same-origin and never taint the canvas.

## The Trade-off

| Approach | HTML Size | Export Works | Load Speed | Use When |
|----------|-----------|-------------|------------|----------|
| **Local file path** | ~15KB | ❌ No | Instant | Only display needed, no export |
| **Base64 data URI (photo)** | 300-400KB+ | ✅ Yes | Fast (local file) | Export needed + photo avatar |
| **Inline SVG data URI** | ~1KB per avatar | ✅ Yes | Instant | Character avatars without photos |

## Decision Tree

```
User wants HTML output
├── Only for preview/screenshot (no export needed)
│   └── Use local file paths → 15KB HTML, instant load
│
├── User wants "导出长图" button → export IS needed
│   ├── Avatar is a real photo (JPEG/PNG, 100KB+)
│   │   └── Convert to base64 → embed in HTML
│   │       HTML will be 300-500KB but local load is still fast
│   │
│   └── Avatar is a character/illustration (no photo)
│       └── Use inline SVG data URI → ~1KB each
```

## Emitting: Two Approaches

### Approach A: Embed full-res base64 (reliable, ~400KB HTML)

```python
import base64
with open('avatar.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
data_uri = 'data:image/jpeg;base64,' + b64
# -> embed in avatarMap['角色名'] = data_uri
```

Use this when export reliability is the priority and the HTML is served from local disk (file:// load is instant regardless of size).

### Approach B: Embed resized thumbnail (~3KB base64, ~17KB HTML)

If PIL/Pillow is available, resize to 40×40 before encoding:

```python
from PIL import Image
import base64, io

img = Image.open('photo.jpg').resize((40, 40), Image.LANCZOS)
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85)
b64 = base64.b64encode(buf.getvalue()).decode()
# ~2-3KB instead of 300-400KB
```

Best of both worlds: small HTML + exportable canvas. Use when PIL is available.

## html2canvas Config (Critical)

```javascript
// ❌ WRONG for file:// — causes Tainted canvases error
html2canvas(app, { useCORS: true, ... })

// ✅ CORRECT for file:// — useCORS: false + data URI avatars
html2canvas(app, {
    scale: 2,
    useCORS: false,       // don't proxy — data URIs are same-origin
    backgroundColor: '#ededed',
    ...
})
```

**Important:** `useCORS: false` is only correct when ALL avatar sources are data URIs (base64 or inline SVG). If any avatar uses a local file path, the canvas will be tainted regardless of this setting.

## Verdict

- For **character avatars** (no real photo): always use inline SVG data URI. Small, fast, exportable.
- For **real photo avatars** with export needed: embed base64. Yes the HTML gets big (~400KB), but local file:// loading is still instant. The real slowness was always the setTimeout animation, not the file size.
- For **real photo avatars** without export: use local file path reference. 15KB HTML.

**TL;DR:** If the user says "导出" or "长图", you MUST use data URIs for ALL avatars. If they only want the HTML for preview, local file paths are fine.

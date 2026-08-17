---
name: wechat-chat-simulator
description: "Convert dialogue-style markdown (talk.skill output or similar) into a standalone WeChat-style chat HTML page for screenshots or preview."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# WeChat Chat Simulator Generator

Convert a dialogue-style markdown (talk.skill output or similar) into a standalone WeChat-style chat HTML page.

## Trigger

When the user asks to:
- Turn a dialogue/conversation into a WeChat chat screenshot or preview
- Make a chat-style HTML from any dialogue content
- Convert talk.skill output into a chat simulator

## Steps

1. **Read the source markdown** — extract speaker names and message content.
   - Bold text (`**text**`) should be preserved as the chat bubbles.
   - Keep the original dialogue flow; don't summarize or truncate.
   - **Parsing:** Source MD uses `**角色名：** 内容` (colon INSIDE bold). Split by `\n\n` (paragraphs), then match `\*\*(.+?)[:：]\*\*\s*(.*)` — the `[:：]` character class handles both `:` and `：`. **Never** use `\*\*(.+?)\*\*[:：]\s*` (colon after `**`) — it matches zero times because the colon is before the closing `**`.
   - **Verify:** After extraction, check match count ≥ 1. If 0, the regex is wrong — fall back to paragraph split + looser pattern.

2. **Build the HTML** — use the template at `references/wechat-chat-template.html` as the base.
   - Replace the hardcoded `dialogues` array with extracted content.
   - Set `avatarMap` with per-speaker avatar URIs.
   - **Avatar source priority:**
     1. **Base64 data URI** (required for html2canvas export to succeed in file:// protocol) — generate via `execute_code` with Python `base64.b64encode(open(path, 'rb').read()).decode()`. Local file paths like `巴菲特.jpeg` cause `Tainted canvases` on export in file:// protocol.
     2. **Inline SVG data URI** (for character avatars without photos) — use `svgAvatar(ch, color)` helper with `encodeURIComponent` (see Step 3).
   - Set the header title (`chatTitle.textContent`):
     - 2 speakers: `<Speaker1> & <Speaker2>`
     - 3+ speakers (group chat): `<Topic>群` (e.g. `科技峰会后台群`)
   - **Header layout:** Title is centered (`justify-content: center`). No rename button inside the header — put it in the toolbar outside the chat app, next to the export button.
   - **Layout mode detection (auto):**
     - **2 speakers (dual mode)** — alternating left-right. First speaker in dialogue list = self (right side, green bubble `#95ec69`). Second speaker = other (left side, white bubble). Sender name visible on both sides. Arrow triangle on each bubble's avatar-facing edge.
     - **3+ speakers (group chat)** — all messages left-aligned with per-speaker avatars. NO member-list banner. All bubbles white. Sender name above each bubble.
   - The template auto-detects based on distinct speaker count. You only need to fill `dialogues` and `avatarMap`.

   - **Avatar click-to-upload (required interactive feature):** Add a hidden `<input type="file" id="avatarUpload">` element and JavaScript that:
     - Tracks which speaker's avatar was clicked (`currentAvatarSpeaker` variable)
     - On file selection, reads as data URL via `FileReader.readAsDataURL()`
     - Updates `avatarMap[currentAvatarSpeaker]` with the new data URL
     - Updates ALL existing avatar `<img>` elements where `img.title === currentAvatarSpeaker`
     - Calls `setupAvatarClicks()` after both `loadDialogues()` (batch render) and after sending new messages
     - CSS: `.avatar { cursor: pointer; }` so users see avatars are clickable

3. **Avatar handling:**

   **Priority order for avatar sources:**
   1. **Base64 data URI** (required when export is needed) — generate via `execute_code` with Python `base64.b64encode(open(path, 'rb').read()).decode()`. Use `useCORS: false` in html2canvas config. See Step 2 for the trade-off vs local files.
   2. **Inline SVG data URI** (for character avatars without photos) — see rules below.
   3. **Local file path** (use ONLY when no export needed) — keeps HTML ~15KB but breaks html2canvas export.

   **SVG data URI construction (for character avatars without photos):**
   - Left side (白气泡/bot): use `backgroundColor=b6e3f4` (blue)
   - Right side (绿气泡/user): use `backgroundColor=c0aede` (purple)
   - ⚠️ Pitfall: some seed names may not render — use simple alphanumeric seeds only. If an avatar fails, the `onerror` handler falls back to a valid dicebear URL.
   - 🔥 CRITICAL: External dicebear URLs (`https://api.dicebear.com/...`) may FAIL to render in `file://` protocol context — the image element exists in DOM but is invisible in screenshots. FIX: use inline SVG data URIs as primary avatar source. Generate simple SVG circles with the speaker's first Chinese character or initial letter.
   - 🔥 CRITICAL: Use `encodeURIComponent()` NOT `btoa()` for SVG data URIs. `btoa()` fails with special characters in SVG. Pattern: `'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgString)`. This avoids JS exceptions that silently break the page.
   - 🔥 CRITICAL: Avatar SVG MUST use solid colors (`fill="#RRGGBB"`), NOT gradients (`fill="url(#id)"`). When SVG contains `url(#gradientId)` and passes through `encodeURIComponent()`, the `#` gets double-encoded to `%2523`. Browser sees `url(%2523id)` → gradient fails silently → avatar renders as gray/black. Simple circle + text + solid fill is the only reliable approach.
   - 🔥 SVG attributes MUST use double quotes (`xmlns="..."`) because the JS variable wrapper uses single quotes. Single quotes in SVG (`xmlns='...'`) cause JS string termination → script crashes → no messages render at all.

4. **Message layout (CRITICAL):**
   - Each message row = avatar + content-column
   - content-column = [sender-name (small gray text above)] + [bubble (message text only)]
   - **Sender name goes ABOVE the bubble**, styled as `font-size: 12px; color: #999;`
   - **Bubble contains ONLY the message text** — NO speaker name prefix inside the bubble
   - **NEVER put the speaker name inside the bubble text** — this is the most common error
   - Left messages: name aligned left above bubble; Right messages: name aligned right above bubble
   - **Dual mode (2 speakers):** first speaker gets `right` (green bubble, self), second gets `left` (white bubble, other). Arrow triangle on each bubble's avatar-facing edge — right messages point right, left messages point left.
   - Arrow triangle on bubble edge pointing toward avatar

5. **Output** — write the HTML file to the user's specified path (default: desktop or current working directory).
   - Filename: `<Topic>聊天模拟器.html` or user-specified.

5. **Verify** — open in browser via `browser_navigate` (file://) and take a screenshot to confirm rendering.
   - Check: all avatars visible, no content truncation, bubbles styled correctly.
   - ⚠️ **Screenshot limitation:** Browser screenshot tool captures only the visible area (usually the bottom of the page due to auto-scroll). For long conversations, you CANNOT see the first messages in screenshots.
   - **DOM verification is mandatory:** Always run `browser_console` checks:
     ```javascript
     // Total message rows (should match dialogue count)
     document.querySelectorAll('.message-row').length
     // First message preview
     document.querySelectorAll('.message-row')[0]?.querySelector('.message-bubble')?.textContent?.substring(0, 60)
     // Avatar count (should match message count)
     document.querySelectorAll('.avatar').length
     // Check sender-name elements exist (names above bubbles, not inside)
     document.querySelectorAll('.sender-name').length
     // JS errors
     ```
   - If total row count equals expected dialogue count, rendering is correct regardless of screenshot visibility.
   - **Group chat check:** In group mode (3+ speakers), verify all messages are left-aligned with per-speaker avatars and no green bubbles exist:

6. **Export as long image (optional)** — the template includes a built-in "📷 导出长图" button that uses html2canvas. The user can click it in-browser. Alternatively, you can trigger export programmatically:
   - Click the export button via `browser_click` on the button
   - Or call html2canvas via `browser_console` with expression:
     ```javascript
     html2canvas(document.getElementById('chatApp'), {scale: 2, backgroundColor: '#ededed'})
       .then(c=>c.toDataURL('image/png'))
     ```
   - **Extracting the canvas data URL:** For long chats, the canvas data URL can be 1.5MB+ — `browser_console` may truncate or fail. Alternative: persist the result to the DOM or a file.
   - After extraction, decode the base64 data URL and save as `.png` via `execute_code` (not `terminal` — terminal truncates large outputs).

## Template Location

Reference: `references/wechat-chat-template.html` — the full working HTML skeleton with WeChat styling, avatar upload, rename modal, and scroll-to-bottom. Use this as a base: copy it, then replace the `dialogues` array and header title with extracted content.

## Reference Files

- `references/wechat-chat-template.html` — the full working HTML skeleton with WeChat styling, avatar upload, rename modal, group chat auto-detection (3+ speakers all-left), scroll-to-bottom, and html2canvas export button. Use as a base: replace `dialogues` array, `avatarMap`, and header title.
- `references/svg-encoding-pitfalls.md` — SVG avatar encoding gotchas: gradient double-encoding, JS quote collision, correct pattern.
- `references/base64-avatar-fallback.md` — Avatar SVG construction: solid vs gradient, quote rules, SVG structure, debugging checklist.
- `references/avatar-export-strategy.md` — Avatar source decision tree: local file vs base64 vs SVG, tainted canvas fix, html2canvas config. Load when export fails.

## Pitfalls

- **🔥 HTML FILE SIZE vs EXPORT — TRADE-OFF:** Local file paths (`<img src=\"巴菲特.jpeg\">`) keep HTML ~15KB and load instantly, but **break html2canvas export** — file:// + `useCORS: false` still produces blank images, while `useCORS: true` throws `Tainted canvases`. To support BOTH fast loading and export, use **base64 data URIs** generated via `execute_code` (Python `base64.b64encode()`), then embed in the HTML. The 400KB HTML downloads in one pass and the export button works immediately. Skip local file paths entirely if the user wants export capability.
- **🔥 setTimeout 动画导致逐条缓慢出现:** 30 条消息 × 50ms = 1.5 秒的排队延迟。改为一次性 `appendChild` 批量渲染（或使用 `DocumentFragment`），瞬间全部显示。动画可以用 CSS `animation-delay` 渐进式出现，不阻塞 DOM 渲染。
- **🔥 导出长图失败 — Tainted canvases:** file:// 协议下，html2canvas 的 `useCORS: true` 会导致本地图片跨域标记，`toDataURL()` 抛出 `Tainted canvases may not be exported`。修复方案：使用 `useCORS: false`，并将所有本地图片源改为 base64 data URI 或内联 SVG。data URI 视为同源，canvas 不会被污染。
- **🔥 NAMES INSIDE BUBBLES (most common error):** NEVER put speaker name inside the bubble text. The name goes ABOVE the bubble as small gray text (`.sender-name` class). The bubble contains ONLY message content. The updated template now has a `sender-name` div above `message-bubble` — verify the output has no `**Speaker:**` prefix inside bubble text.
- **🔥 GROUP CHAT vs 2-SPEAKER LAYOUT:** The template auto-detects. But if multiple speakers share the same `side` (e.g. you want all-left for 2 people), override the detection by setting `var forcedGroup = true;` in the JS.
- **🔥 DUAL MODE SIDE MAPPING:** In dual mode, the **first** speaker in the dialogue list = self (right, green bubble `#95ec69`), the **second** = other (left, white bubble). This is a deliberate UI choice to match real WeChat screenshots where the account holder's messages appear on the right. Do NOT invert this — first ≠ left.
- **🔥 AVATARMAP MUST BE POPULATED:** If `avatarMap[speaker]` is undefined, the template falls back to a generic `?` SVG. Set `avatarMap["角色名"] = "data:image/..."` for EVERY distinct speaker before `loadDialogues()`. For local images (photo files), encode as base64 via Python `base64.b64encode()` in `execute_code`, NOT via `terminal("cat file | base64")` — terminal truncates large (300KB+) outputs. Write the base64 to a JS variable directly in the template.
- **🔥 Export right-side extra whitespace**: html2canvas captures CSS `box-shadow` which extends ~20px beyond the element's right edge. Fix: (1) temporarily clear `element.style.boxShadow = 'none'` before capture, restore after; (2) do NOT pass explicit `width`/`height`/`windowWidth`/`windowHeight` to html2canvas — let it auto-detect element dimensions naturally; (3) use `backgroundColor` matching the element's own background color.
- **🔥 BASE64 IMAGE EMBEDDING — TERMINAL TRUNCATION:** When embedding large images (300KB+ JPEG/PNG) as base64, do NOT use `terminal("base64 -w0 photo.jpg")` or `cat` — these truncate at ~50KB in tool output. Instead, use `execute_code` with Python's `base64.b64encode(open(path, 'rb').read()).decode()` and assign the result to a JS variable directly. Or use `skill_manage(action='write_file')` to write the complete base64 into the template.
- **🔥 CANVAS DATA URL EXTRACTION FOR LONG IMAGES:** When exporting via html2canvas, the canvas data URL can be 1.5MB+. `browser_console` with expression may silently truncate. Safer approach: write the canvas data URL to a hidden `<a>` download link, or use `browser_console` to persist it as a DOM element's `innerText`, then extract via `execute_code`.
- **🔥 MARKDOWN SPLITTER TRAP — `**角色名：**`:** When source MD uses `**角色名：** 内容` (colon inside bold markers, like `**巴菲特：** 我……`), regex patterns like `\*\*(.+?)\*\*[:：]\s*` will MATCH ZERO because the colon is inside the `**`. FIX: split by paragraphs first, then use pattern `\*\*(.+?)：\*\*\s*(.*)` — the colon is BEFORE the closing `**`, not after. Always verify your regex finds ≥1 match before generating output.
- **🔥 SVG GRADIENT DOUBLE-ENCODING:** When building avatar SVG data URIs via `encodeURIComponent(svgString)`, any `url(#gradientId)` reference inside the SVG gets double-encoded: `#` → `%23` → `%2523`. The browser sees `url(%2523id)` and does NOT recognize it as a gradient reference → gradient silently fails → avatar renders as flat gray/black. FIX: use solid colors (`fill="#667eea"`) instead of gradients, or avoid `url()` references in SVG data URIs entirely.
- **🔥 SVG ATTRIBUTES IN JS STRINGS — quote collision:** SVG attributes must use double quotes (`xmlns="..."`) because the JS variable wrapping the SVG uses single quotes (`var svg = '<svg ...>'`). If you accidentally use single quotes in SVG attributes (`xmlns='...'`), the JS string terminates early and the entire script throws — no messages render at all.
- **🔥 SVG ENCODING:** Use `encodeURIComponent()` NOT `btoa()` for SVG data URIs. `btoa()` throws on special characters and silently breaks the page. Pattern: `'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgString)`.
- **🔥 AVATAR VISIBILITY IN SCREENSHOTS:** SVG avatars may exist in DOM but not render in screenshots. Always verify with `browser_console` check: `document.querySelectorAll('.avatar').length` should match expected count. If 0, the JS failed to load.
- **📸 SCREENSHOT MISLEADING FOR LONG CONVERSATIONS:** The browser screenshot tool always captures the bottom of the page (scroll position). For conversations with 10+ messages, the first messages are off-screen and invisible in screenshots. This does NOT mean they didn't render. Always use DOM verification (`document.querySelectorAll('.message-row').length`) instead of relying on screenshots for correctness.
- **🔥 FORGOT setupAvatarClicks() — avatars not clickable:** After batch render (`loadDialogues()`) and after sending new messages, you MUST call `setupAvatarClicks()` to attach click listeners to avatar `<img>` elements. If avatars look right but don't respond to clicks, this call is missing. The hidden `<input type="file">` must also be present in the HTML — without it, clicking does nothing.
- **Avatar seed names**: Use simple alphanumeric seeds. Some names (like "BerkshireBuffett") may fail to render on dicebear API. If avatar is missing, try a shorter seed or use the onerror fallback.
- **Long messages**: Bubbles have `max-width: 70%`. If a message is very long, it may wrap awkwardly. Consider splitting long paragraphs.
- **File:// protocol**: The HTML works standalone but `browser_navigate` with `file://` may not capture screenshots properly in some browsers. Verify with a browser snapshot first.
- **Bold text preservation**: The template converts `**bold**` to `<strong>` tags. Ensure source markdown uses `**text**` format, not `_text_`.

## Notes

- The output is a single HTML file with all CSS/JS inline. When using base64 data URIs for real photo avatars (required for html2canvas export), the HTML grows to ~400KB but loads in one pass and export works reliably.
- Works in any modern browser. Mobile-responsive (max-width 430px).
- Interactive features: click avatars to upload custom images, "改名" button to rename chat, send button to add messages.
- The bottom input is functional — users can type and send messages after viewing the dialogue.

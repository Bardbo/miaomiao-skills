---
name: apparel-lookbook-generator
description: Generates a coordinated, authentic-looking set of social-commerce fashion images (小红书 / Xiaohongshu / Pinterest) from a single apparel product photo — built for Chinese users and the 种草 aesthetic. **Analysis-driven workflow**: reads the reference image → extracts product inventory / style family / seasonality / formality / materials → deduces fitting scenes, brand story angles, and natural poses → constructs dynamic prompts (NOT template-fill) → generates via ImageGen with per-category camera-filter presets → **self-reviews every output** for artifacts (phantom accessories, misplaced footwear, dropped items, anatomy errors) and regenerates if needed. Two output modes: Lifestyle Cinematic (film-stock candid look) and E-commerce Natural (textured-surface product photography). Trigger for: 小红书穿搭图, 社媒种草图, 服装平铺图, 电商产品细节图, 电商主图, 详情页, 穿搭 lookbook, OOTD, 小红书笔记配图, Pinterest pin, 情侣穿搭, 品牌故事图.
agent_created: true
---

# Apparel Lookbook Generator v9

## Overview

This skill turns one apparel reference photo into a full coordinated image set for **Xiaohongshu (primary) and Pinterest (secondary)**, with a separate optimized mode for **e-commerce detail pages**.

**v9 core philosophy: Analysis-driven prompts (v8 engines) + Reference-Style Realism Upgrade (v9, 8 rules).**
Every prompt is built from product analysis (not template-fill) AND applies the v9 realism rules so the output reads as **real photography shot in a real location with film grain** — not clean CGI.

The old approach (v1–v7) used fixed templates with `{items_full}` / `{scene_description}` placeholders. That produced "good enough" results but suffered from:
- **Template blindness**: prompts felt generic regardless of the actual product
- **No pose intelligence**: same "mid-step looking aside" pose for heels, sneakers, AND loafers
- **No brand story logic**: Brand Story always used "velvet armchair + tea" regardless of product personality
- **No quality gate**: artifacts (holding shoes, phantom masks, dropped items) reached the user unchecked
- **AI-render look**: even good prompts read as plastic CGI because scenes were generic and light was too hard

v8 added four analysis engines; v9 adds the realism upgrade on top:

| Engine | What it does | Replaces |
|--------|-------------|----------|
| **Product Analysis** | Reads reference image → structured inventory + style/season/formality/material extraction | Template `{items_full}` manual entry |
| **Scene & Story Deduction** | From product attributes → scene pool + brand narrative angle + activity suggestions | Hardcoded style→scene table |
| **Pose Library** | Recommends natural poses per product type / footwear / occasion | Generic "candid mid-step" for everything |
| **Self-Review Gate** | After each generation: read image → checklist → regenerate if artifact found | No post-generation check at all |

All generation runs through WorkBuddy's built-in `ImageGen`; no external API key required.

This skill is **oriented to Chinese users (国人)**:
- **Model**: default **Chinese / East-Asian model** ("Chinese female model, natural makeup"). Override freely.
- **Platform & aesthetic**: default target **Xiaohongshu** — natural daylight, filmic muted tones, candid, intimate lifestyle feel.

## Why images look "AI" — and how this skill avoids it

| # | The "AI tell" | Why it happens | This skill's fix |
|---|---------------|----------------|------------------|
| 1 | **Polished commercial-CGI look** | "hyperrealistic / 8k uhd / sharp focus / DSLR" pushes render-like crispness | Replace with **per-category camera filter presets** (specific gear = specific look) |
| 2 | **Stiff, centered "product" framing** | "full body shot, professional fashion photography" yields stock symmetry | Use **pose library** — different poses for heels vs sneakers vs loafers |
| 3 | **Generic scene regardless of product** | Template fills `{scene}` from a fixed list | **Scene deduction engine** analyzes product → derives scenes from style/season/formality |
| 4 | **Pasted-on person / composite artifact** | Too-high fidelity forces same face/pose everywhere | Moderate fidelity (lifestyle 0.62–0.78); reference anchors PRODUCT not face |
| 5 | **Prompt bloat / contradictions** | Long rambling prompts confuse model | Dynamic construction: 80–140 words, analysis-driven, no bloat |
| 6 | **Multi-hand / multi-leg artifacts** | Anatomy-negative words paradoxically cause them; no pose guidance | Remove negative words; use **pose library** for anatomically-safe poses; self-review catches failures |
| 7 | **Phantom accessories / misplaced items** | Model invents things in "empty space"; no post-generation check | **`{artifact_guard}` + Self-Review Gate** catches and regenerates |
| 8 | **Same pose for every product type** | Template uses generic "candid mid-step looking aside" | **Pose library**: 20+ poses mapped to product type / footwear / category |

> Rule of thumb: **analyze the product first, then write the prompt. Never use a generic template as-is.**

## Two output modes

| Mode | When to use | Visual language | Default fidelity |
|------|-------------|-----------------|------------------|
| **Lifestyle Cinematic** (default) | 种草笔记 / Pinterest / 社媒 | Per-category camera filter + film emulation, natural light, candid | Char 0.62–0.75; flat 0.78; detail 0.65–0.75; couple 0.78 |
| **E-commerce Natural** | 电商主图 / 详情页 | Textured surface + natural window light + camera color-science warmth | Char 0.78; flat 0.85; detail 0.82 |

> Default = Lifestyle Cinematic. Pick mode up front. **Never mix modes in one prompt.**
>
> E-com Natural uses textured surfaces (linen/wood/marble), NOT sterile white background. White BG invites phantom artifacts. Only use white BG if user explicitly requests 淘宝纯白底.

## Target platform & visual language

| Item | Xiaohongshu (default) | Pinterest (secondary) | E-commerce |
|------|-----------------------|------------------------|------------|
| Aspect ratio | **3:4** → `1080x1440` | **2:3** → `1024x1536` | **1:1** → `1024x1024` (主图) or **3:4** (详情页) |
| Light | natural soft daylight, filmic | natural / editorial | even softbox or overcast daylight |
| Color | muted filmic tones, warm | cohesive, save-worthy | accurate, true-to-product |
| Mood | candid, intimate, everyday-authentic | aspirational, searchable | clean, professional |
| Composition | off-center, environmental | clean, scene-driven | centered, all items visible |
| Model | Chinese / East-Asian (default) | same | same |

## Engine 1: Product Analysis (Step 2 — MANDATORY, runs before any prompt)

**Before writing a single word of prompt, analyze the reference image thoroughly.** This is the foundation of everything else.

### 2.1 Extract: Complete Product Inventory

Read the reference image and list EVERY item visible:

```
{items_full} = [item 1], [item 2], [item 3], ...

For EACH item, note:
- Category: top / bottom / outerwear / footwear / bag / jewelry / accessory / hosiery / headwear
- Color: exact color name
- Material: visible texture (satin / knit / leather / cotton / lace / wool blend / etc.)
- Distinctive feature: what makes THIS item unique (buckle shape / lace pattern / strap type / print / etc.)
- Position in reference: how it's arranged (worn on model / laid flat / folded)
```

**Example output format:**

| # | Item | Category | Color | Material | Distinctive Feature |
|---|------|----------|-------|----------|-------------------|
| 1 | camisole tank top | top | cream ivory | cotton-modal ribbed knit | thin straps, scoop neckline |
| 2 | knit cardigan | outerwear | beige | fine-gauge wool blend | open front, button closure, ribbed cuffs |
| 3 | tailored shorts | bottom | beige khaki | cotton twill | high-waisted, pleated front, belt loops |
| 4 | penny loafers | footwear | tan camel | leather | strap detail across vamp |
| 5 | ankle socks | hosiery | beige | plain cotton crew | ankle height, plain (no pattern) |
| 6 | tote bag | bag | beige | leather | structured, top handles, minimalist |
| 7 | watch | jewelry | gold-tone | metal | round white dial, brown leather strap |
| 8 | necklace | jewelry | gold | metal chain | small round disc coin pendant |

### 2.2 Classify: Style Family

Match the product to ONE primary style family (this drives ALL subsequent deductions):

| Style Family | Visual Cues | Scene Vibe | Brand Story Angle |
|-------------|------------|-----------|-------------------|
| **old money / 静奢** | Neutral palette, quality materials, minimal logos, tailored silhouettes | Gallery, wine bar, hotel lobby, penthouse | Heritage craftsmanship, quiet confidence, "less is more" luxury |
| **streetwear / 街头潮酷** | Bold colors, oversized fits, graphics, sneakers, caps | Graffiti wall, skate park, night market, rooftop neon, urban street corner | Self-expression, urban culture, breaking rules |
| **preppy / 学院风** | Plaids, blazers, loafers, knee-highs, neat layering | Library, campus lawn, independent bookstore, brick cafe | Academic charm, timeless sophistication, collegiate nostalgia |
| **sweet-spicy / 甜辣约会** | Body-conscious silhouettes, lace, heels, contrast elements | Cocktail bar, date restaurant, poolside, rooftop night | Confident femininity, date-night energy, girl-power allure |
| **resort / 度假田园** | Linens, florals, flowy cuts, sandals, straw accessories | Beach, flower field, garden courtyard, picnic lawn | Escapism, effortless beauty, vacation state of mind |
| **minimal Scandinavian / 极简** | Monochromatic neutrals, clean lines, no patterns, quality basics | White-wall studio, home interior, minimal cafe, gallery | Conscious living, sustainability, "less but better" philosophy |
| **commute / 通勤职场** | Tailored pieces, neutral base + one accent, polished shoes | Office with view, subway platform, business district sidewalk, airport lounge | Professional poise, city efficiency, modern career woman |
| **boho / 波西米亚** | Earth tones, layered textures, fringe, wide-brim hats, boots | Desert road, vintage market, music festival field, sunlit balcony | Free spirit, wanderlust, artistic soul |
| **athleisure / 运动休闲** | Technical fabrics, sneakers, hoodies, leggings, sports bras | Gym studio, jogging path, juice bar, yoga studio rooftop | Active wellness, strength, balance |

### 2.3 Determine: Seasonality & Formality

| Attribute | How to deduce from product | Impact |
|-----------|--------------------------|--------|
| **Season** | Materials (linen=summer, wool=winter), coverage (sleeveless=warm, layered=cold), color (pastel=spring, earth=autumn) | Scene lighting (golden hour vs overcast), environment (outdoor vs indoor) |
| **Formality** | Heels > flats; structured bag > tote; blazer > cardigan; silk > cotton | Venue selection (gallery vs cafe vs park), pose elegance level |

### 2.4 Identify: Key Distinctive Items

From the inventory, flag 1–3 items that are MOST visually distinctive — these get extra-precise description in EVERY prompt:

```
{distinctive_items} = [
  {item_name}: {precise_visual_description_as_seen_in_reference}
]
```

Example: `sheer black lace thigh-high stockings with garter straps, small bows, and floral lace pattern at top band`

These distinctive items are the #1 source of "product doesn't match reference" complaints. Describe them EXACTLY as they appear.

## Engine 2: Scene & Story Deduction (Step 4 — from analysis, NOT hardcoded)

### 4.1 Scene Pool Generation

Given the style family + season + formality from Engine 1, generate a **custom scene pool** of 4–6 specific scene concepts. Each concept includes:

| Field | Description | Example |
|-------|-------------|---------|
| Scene name | One-line venue description | "bright independent bookstore with white walls and wooden shelves" |
| Rationale | Why this scene matches THIS product | "Minimal Scandinavian style pairs with quiet intellectual spaces; morning light flatters neutral palette" |
| Lighting | Specific light condition | "soft morning window light streaming through large east-facing windows" |
| Activity | What the subject is naturally doing | "reaching for a book on a lower shelf" |
| Best for categories | Which of the 6 types this scene suits | Outfit, Lifestyle |
| Mood word | Single emotional adjective | "peaceful" |

**Scene mapping is PRODUCT-SPECIFIC.** Examples:

| Product profile | Scene pool (examples) |
|---------------|----------------------|
| Cream satin + black skirt + Mary Janes (old money, evening) | Art gallery opening, wine bar terrace, hotel lobby piano corner, evening garden party |
| Beige cami + cardigan + shorts + loafers (minimal, casual) | Independent bookstore morning, bright apartment window, weekend brunch cafe, white-wall studio with plants |
| Plaid blazer + pleated skirt + knee-highs (preppy, fall) | Campus library, autumn park bench with fallen leaves, brick cafe interior, vintage shop browsing |
| Body-con dress + heels + clutch (sweet-spicy, evening) | Rooftop cocktail bar golden hour, date restaurant booth, nightclub entrance, valet stand |

### 4.2 Brand Story Angle Deduction

From the style family + distinctive items, derive 1–3 brand story angles for the Brand Story category:

| Style Family | Story Angle A | Story Angle B | Story Angle C |
|-------------|-------------|-------------|--------------|
| Old money | "The morning ritual" — getting dressed slowly, quality over quantity | "Heritage piece" — item passed down, craftsmanship detail | "Quiet confidence" — entering a room without announcing |
| Minimal Scandinavian | "Less but better" — curated wardrobe, each piece intentional | "Morning light" — simple beauty in ordinary moments | "Conscious choice" — sustainable materials, mindful consumption |
| Sweet-spicy | "Date night prep" — the transformation ritual | "Own the room" — confidence through style | "Duality" — sweet exterior, spicy edge (lace + leather combo) |
| Streetwear | "City canvas" — urban landscape as backdrop | "Rule breaker" — mixing unexpected elements | "Tribal signal" — outfit as identity marker |
| Preppy | "Campus memory" — nostalgic academic setting | "Weekend tradition" — Sunday brunch uniform | "Library quiet" — intellect meets style |
| Commute | "City rhythm" — power walk through business district | "Transition moment" — office to evening | "Desk-to-dinner" — one outfit, two contexts |

**Pick the angle that best matches the product's distinctive items.** The Brand Story prompt should VISUALIZE this narrative, not just show clothes on a chair.

## Engine 3: Pose Library (Step 5 — per-product-type recommendations)

**Different products need different poses.** Using "candid mid-step looking aside" for heels AND sneakers AND loafers is why poses look AI-generic. The pose library maps natural poses to product characteristics.

### 3.1 Pose Selection Matrix

| Footwear Type | Recommended Poses | Avoid (artifact-prone) |
|--------------|------------------|----------------------|
| **Heels / pumps / stilettos** (3"+) | Seated cross-legged; standing one hand on hip; leaning against wall; walking toward camera (full-body); sitting on bar stool turning to look back | Running; jumping; squatting; hands near feet (triggers shoe-removal artifact) |
| **Flats / loafers / ballet flats** | Sitting cross-legged on chair; walking casually; one foot slightly forward (contrapposto); leaning on railing; sitting on floor legs extended | High kick; running; anything where feet leave frame |
| **Sneakers / trainers** | Walking mid-stride; sitting on steps; jumping (landed); leaning against wall one leg bent; skateboard/bike adjacent | Formal seated pose; elegant hand-on-hip |
| **Boots (ankle/knee)** | Standing with weight on one leg; walking away looking back; sitting on edge of table; straddling chair backward | Dainty crossed-ankles pose (boots don't bend that way) |
| **Sandals / open-toe** | Beach/pool edge; sitting with legs dangling; walking on grass/path; barefoot-adjacent poses | Snow/cold scenes; formal indoor poses |
| **No visible footwear** (flat lay / detail only) | N/A — focus on item arrangement | N/A |

### 3.2 Pose Per Category (with product-type awareness)

**Outfit (全身/中景):**
- If **heels**: `standing elegantly one hand lightly touching hair, weight shifted to back foot, head turned three-quarter view`
- If **flats/loafers**: `walking naturally mid-stride, arms relaxed at sides, slight smile looking ahead`
- If **sneakers**: `leaning casually against a wall, one leg bent foot resting on wall behind, relaxed posture`
- If **boots**: `standing with weight on one leg, other foot slightly behind, one hand in pocket`
- **Universal safe pose** (fallback): `seated naturally, one arm resting on table/chair back, looking slightly off-camera with genuine expression`

**Lifestyle (场景互动):**
- Cafe/restaurant: `seated at table, holding cup/gaze out window/turning to speak, natural upper body movement`
- Outdoor/walking: `mid-walk pause, looking at something in environment (shop window/phone/sign), natural body language`
- Home/interior: `casual domestic movement — adjusting hair/reaching for something/sitting on sofa edge`
- **Key rule**: the pose must involve an ACTIVITY that makes sense in the scene. No "standing stiffly in the middle of a cafe."

**Couple·Friends (双人):**
- **Always seated or close-interaction** (avoids hand-zone ambiguity):
  - `seated across small table, she laughing at something he said, leaning slightly forward`
  - `both leaning on same railing, looking at same direction, shoulders almost touching`
  - `walking side by side close, her hand briefly touching his arm while pointing at something`
- **Never**: both standing facing camera symmetrically; full-body shots showing all limbs; poses requiring complex hand positioning

**Flat Lay (俯拍):**
- Pose = arrangement style, not human pose:
  - **Casual lived-in**: items slightly scattered like just taken off (`naturally imperfect tidy arrangement`)
  - **Curated editorial**: items precisely spaced with intentional gaps (`clean organized arrangement with breathing room`)
  - **In-use hint**: one item slightly unfolded/open to suggest recent wear (`cardigan draped open showing buttons`)

**Details (微距):**
- Pose = camera angle + focal point:
  - **Texture shot**: 45° angle showing material weave/light interaction (`fine knit texture catching soft daylight`)
  - **Hardware shot**: straight-on focusing on buckle/button/clasp (`gold-tone buckle detail with visible screw heads`)
  - **Construction shot**: slight angle showing seam/stitching (`ribbed cuff detail with visible stitch line`)

**Brand Story (叙事):**
- Pose = narrative staging:
  - **"Getting ready"**: items half-dressed on chair/bed, mirror reflection implied
  - **"Just came home"**: items draped over furniture, bag still on shoulder strap, shoes kicked off nearby (but described as "placed neatly beside")
  - **"Designer's table"**: items artfully arranged with sketchbook/coffee/fabric swatch
  - **"Packing for trip"**: items partially packed in open suitcase or laid on bed with travel items

## Engine 4: Self-Review Gate (Step 7.5 — after EVERY generation)

**Every generated image MUST be reviewed before presenting to the user.** This catches artifacts that prompt-level guards can't prevent.

### 7.1 Review Process

After each `ImageGen` call completes:

1. **Read the output image** using multimodal vision (the agent can see images)
2. **Run the Artifact Checklist** below
3. **If ANY item FAILS** → adjust the prompt (add/ strengthen the relevant constraint) → regenerate ONCE
4. **If second attempt also fails** → skip this image, note the failure, inform the user
5. **If ALL PASS** → add to approved set, continue to next image

### 7.2 Artifact Checklist (PASS / FAIL per item)

| # | Check | What to look for | PASS criteria | Common failure | Fix (add to next prompt) |
|---|-------|------------------|---------------|----------------|------------------------|
| 1 | **Item completeness** | Count items from `{items_full}` | All items present (or reasonably implied for cropped shots) | Missing 1+ items | Re-add missing item to F-SUBJ with precise description |
| 2 | **Footwear placement** | Where are the shoes? | Shoes worn on BOTH feet. Not in hands, not on tables, not on floor beside | Holding shoes / shoes on table / shoes on floor / barefoot when shoes expected | Add: `shoes are worn on both feet, she is not holding any footwear, no shoes on tables or floors` |
| 3 | **Phantom accessories** | Any item NOT in reference? | No masks, scarves, hats, extra jewelry, phones, etc. that weren't in `{items_full}` | Mask on neck; random hat; extra necklace | Add: `no additional accessories beyond those listed, neck is bare` |
| 4 | **Person count** | How many people? | Exactly as specified (1 or 2). No partial third person, no ghost figures | Extra limb looks like person; 3rd face in background | Strengthen: `exactly N people, no other figures anywhere in frame` |
| 5 | **Hand anatomy** | Are hands normal? | Correct number of fingers (4-5 visible per hand), natural position, no fusion | Extra fingers; fused fingers; missing hands; hands in wrong place | Change pose to one where hands are less visible/resting naturally; raise fidelity 0.05 |
| 6 | **Product matching** | Do items match reference? | Colors, materials, styles match the reference photo | Wrong color skirt; plain stockings instead of lace; different bag style | Re-describe distinctive item with MORE precision from reference |
| 7 | **Scene accuracy** | Does scene match intent? | Venue, lighting, atmosphere match the planned scene | Wrong venue (cafe instead of gallery); wrong time of day | Re-write F-ENV with more specific scene description |
| 8 | **Overall realism** | Does it look like a real photo? | Natural skin texture, authentic lighting, no CGI/plastic/sheen | Plastic skin; blown-out highlights; oversaturated; watermark present | Adjust F-TECH: strengthen camera-filter language; reduce saturation keywords |

### 7.3 Regeneration Rules

- **Max 1 regeneration per image** (don't burn credits endlessly)
- **Regeneration prompt adjustment**: add ONLY the failed constraint, don't rewrite entire prompt
- **If 2 consecutive failures on same category**: drop that category, replace with alternative solo shot, inform user
- **Log all failures** in the final summary so user knows what was problematic

## Camera Filter System (from v7, validated — keep as-is)

Each category gets a specific camera + lens + film/color-science preset:

| Category | Camera + Lens | Film / Color Science | Light | DoF |
|----------|--------------|---------------------|-------|-----|
| **Outfit** | Fujifilm X-T5 + XF35mm f/1.4 | **Classic Chrome** simulation | Natural side window light | f/2–f/2.8 shallow |
| **Flat Lay** | Canon EOS R6 + RF50mm f/1.2L | **Canon DPP warm tone**, amber cast | Side window light | f/2.8 |
| **Details** | Sony A7R IV + FE90mm f/2.8 Macro | **Neutral with warm lift** | Soft diffused daylight | f/4–f/5.6 deep |
| **Lifestyle** | Leica Q2/Q3, 28mm Summilux | **Kodak Portra 400** emulation | Golden hour / overcast | f/1.7–f/2.8 shallow |
| **Couple·Friends** | Fujifilm GFX 50S II + GF63mm f/2.8 | **Pro Neg. Hi** | Warm ambient | f/2.8 both in focus |
| **Brand Story** | Contax G2 + Planar 45mm f/2 | **Kodak Tri-X 400 B&W** or moody Portra 400 | Moody ambient / morning | f/2 selective |

> **Rule**: pick ONE filter string per prompt. Never combine cameras.

## v9 Reference-Style Realism Upgrade (from 31-image reverse-engineering study)

We reverse-engineered 31 real photos from a top-performing Pinterest/XHS fashion article. The generated images consistently feel "AI" because they miss what those 31 photos DO. Apply these 8 rules to close the gap — they are now MANDATORY, not optional.

| # | Rule | What it fixes | Concrete instruction |
|---|------|---------------|----------------------|
| 1 | **Real-location, never "studio white"** | Generic "white-wall studio / minimalist space" reads as CGI. Reference photos are shot in *actual lived-in places* | Scene = a specific real venue with authentic clutter/atmosphere: a bookstore **with actual books on the shelves**, a **sidewalk café with a marble bistro table and blurred passing cars**, a **sunlit Brooklyn brownstone stoop with potted hydrangeas**, a **seaside wooden boardwalk with white beach houses**. Describe the environment's real details. |
| 2 | **Subject is mid-activity, not standing centered** | "Standing in the middle of a café" = stock. Real photos catch a *genuine moment* | Always give the subject an ACTION tied to the scene: reaching for a book on a lower shelf, mid-walk pause looking at a shop window, laughing at something a companion said, sipping iced coffee gazing out the window. Environmental interaction, not a pose. |
| 3 | **Film grain + natural light, always** | Plastic, over-crisp, blown-out look | End F-TECH with a film-stock + grain clause on EVERY category: e.g. `Kodak Portra 400 emulation, warm skin tones, gentle visible film grain, soft natural falloff`. Never "8k / hyperrealistic / sharp focus". |
| 4 | **Restrained palette (2–3 families max)** | Muddy or chaotic color = AI | Derive palette from the reference; keep it tight. e.g. cream + burgundy + navy (preppy) or blush + brown + oat + olive (soft). State the exact palette in the prompt. |
| 5 | **Flat Lay must feel "lived-in", not sterile** | Cold white-bg e-com flat lay = render | Always shoot flat lays on a **textured surface with window light and 1–2 everyday props**: rumpled cream linen bedsheet, an open book, a ceramic coffee mug, a fashion magazine, dried pampas/eucalyptus. Soft morning daylight, gentle creases, warm cozy mood. Never pure-white seamless. |
| 6 | **Candid intimacy over symmetry** | Centered symmetric framing = catalog | Off-center composition, shallow DoF, subject looking off-camera or at a companion. Slight imperfection in arrangement is GOOD. |
| 7 | **Authentic skin & material texture** | Waxy/plastic skin, fake sheen | `natural human skin with visible pores`, `authentic knit/leather/satin texture`, `no glossy studio sheen`, `no AI smoothing`. |
| 8 | **Consistent signature look per set** | Mixed incoherent styles | Pick ONE film emulation + ONE color science for the whole 6-image set (so it looks like one photographer shot it). Don't swap Portra for Tri-X between categories unless Brand Story intentionally breaks tone. |

> These 8 rules are the single biggest lever on perceived quality. They override the older "clean catalog" defaults wherever they conflict.

## Anti-Artifact Positive Constraints `{artifact_guard}` (ALL modes, mandatory)

Add to EVERY prompt, after F-TECH:

> `neck is bare with no mask or face covering, both shoes worn on both feet, no footwear being held in hands or placed on tables or floors or surfaces, all items from the reference set are present and correctly worn or placed, hands are empty or naturally resting, no phantom accessories beyond the listed items`

**Why each clause exists:**

| Clause | Fixes |
|--------|-------|
| `neck is bare, no mask or face covering` | Phantom mask/scarf on neck (v6 bug) |
| `both shoes worn on both feet` | Shoes removed, placed elsewhere (v6/v7 bug) |
| `no footwear being held in hands` | **Holding shoes in hand** (v8 bug — the image you flagged) |
| `no footwear on tables or floors or surfaces` | Shoes placed on table (v6 bug) |
| `all items from reference set present` | Dropped items (v6 Detail bug) |
| `hands are empty or naturally resting` | Hands doing weird things with objects |
| `no phantom accessories beyond listed items` | Model inventing extra jewelry/hat/phone |

## Avoidance Block `{avoid}` (lifestyle mode only)

> `real photography not illustration not 3d render not CGI not anime, natural human skin with visible pores, soft daylight not studio flash, candid natural moment, no stiff posed stock-photo look, no oversaturated colors, no watermark, no text overlay, no plastic waxy skin, no over-sharpened hyperreal CGI crispness, no AI smoothing, no glossy studio sheen, no artificial symmetric catalog framing, no floating composite look`

> Append: `, exactly one person, no other figures in frame` (single) or `, exactly two people, no other figures in frame` (couple)
>
> **Never**: anatomy-negative words (`no extra limbs`, `no deformed hands`, etc.)

## Multi-Human Rules (unchanged from v7 — these work)

1. Remove all anatomy-negative words
2. Second person: 5–10 words max
3. Fidelity 0.78–0.85
4. Seated/close-interaction framing ONLY
5. Explicit person count every time
6. Crop second person partially if needed
7. Drop after 2 failures

## Workflow (v8 restructured)

### Step 1 — Collect inputs
- Reference photo(s) (preferred, up to 3 angles). OR text brief.
- Confirm platform/ratio (default XHS 1080x1440), model (default Chinese/East-Asian), output mode (default Lifestyle Cinematic).

### Step 2 — **Product Analysis** (Engine 1 — NEW, MANDATORY)
1. Read reference image carefully
2. Extract complete product inventory (table format: item / category / color / material / distinctive feature)
3. Classify style family (pick ONE from 9 families)
4. Determine seasonality + formality level
5. Flag 1–3 distinctive items for extra-precise description
6. Output: structured analysis document (present to user for confirmation)

### Step 3 — (Optional) Auto-brief with vision_analyze
Only if user has photo but no written brief. Fill `{style}` and `{palette}`. Skip if brief exists.

### Step 4 — **Scene & Story Deduction** (Engine 2 — NEW)
1. From style family + season + formality → generate custom scene pool (4–6 concepts with rationale/lighting/activity/mood)
2. From style family + distinctive items → derive brand story angles (1–3 narratives)
3. Present to user for confirmation/selection

### Step 5 — **Pose Selection** (Engine 3 — NEW)
1. From footwear type + category → select appropriate pose(s) from Pose Library
2. Map each of the 6 categories to specific pose descriptions
3. Ensure poses are **anatomically safe** (avoid hand-zone ambiguity for couple shots)

### Step 6 — **Dynamic Prompt Construction** (not template-fill)
For each of the 6 categories, construct the prompt using:
- **F-SUBJ**: `{model}` + `{items_full}` (all items, distinctive ones with extra precision)
- **F-ENV**: selected scene from deduced pool (specific, not generic)
- **F-STYL**: style family + aesthetic keywords
- **F-COMP**: selected pose from Pose Library (product-appropriate, not generic)
- **F-LIGHT**: scene-specific lighting (matched to scene concept)
- **F-COLOR**: extracted palette from reference
- **F-TECH**: per-category camera filter string
- **Guards**: `{avoid}` (lifestyle) + `{artifact_guard}` (always)

**Present the full prompt set to user BEFORE generating.** Show all 6 (or selected subset) with:
- Category, mode, scene, pose, item count, fidelity, and full prompt text.
- User confirms or adjusts.

### Step 6.5 — Pre-generation Self-check
- [ ] All prompts 80–140 words, focused
- [ ] Per-category `{filter}` present and correct for category
- [ ] No anatomy-negative words anywhere
- [ ] `{artifact_guard}` present with updated v8 clauses (including "no holding footwear")
- [ ] Poses are product-appropriate (from Pose Library, not generic)
- [ ] Scenes are deduced from product (not hardcoded)
- [ ] Reference image attached to every call
- [ ] Fidelity per mode table

### Step 7 — Generate
Call `ImageGen` sequentially for each confirmed prompt. Reference image on every call.

### Step 7.5 — **Self-Review Gate** (Engine 4 — NEW, MANDATORY)
For EACH generated image:
1. Read the output image
2. Run 8-item Artifact Checklist
3. PASS → approve, continue
4. FAIL → adjust prompt (add specific constraint for failed item) → regenerate once
5. FAIL again → skip, log, inform user

### Step 8 — Summarize and hand off
List all APPROVED files with paths. Note any skipped/regenerated images. Remind user of platform-specific usage tips.

## Key Principles (v8 updated)

1. **Analyze first, prompt later** — never skip Product Analysis (Step 2)
2. **Every prompt is unique** — driven by the specific product's attributes, not filled templates
3. **Poses match products** — heels ≠ sneakers ≠ loafers, each gets its own pose language
4. **Scenes are earned** — derived from style/season/formality, never assumed
5. **Brand stories have angles** — matched to product personality, not generic "clothes on chair"
6. **Self-review every output** — artifacts caught before they reach the user
7. **Reference image on every call** — anchors product consistency
8. **Full item checklist always** — distinctive items described precisely
9. **Per-category camera filters** — specific gear creates specific looks
10. **No anatomy-negative words** — ever
11. **Anti-artifact positive constraints** — including v8's "no holding footwear"
12. **Two modes, never mixed** — Lifestyle Cinematic or E-com Natural
13. **Chinese model + XHS aesthetic** by default
14. **Preview prompts before generating**
15. **80–140 words per prompt** — anti-bloat
16. **Drop failing categories gracefully** — don't burn credits

## Critical Reminders

- **Credit cost**: ~5–10 credits per image. Full 16-image matrix ~80–160 credits. State cost before generating.
- **Platform ratio**: XHS `1080x1440` (default); Pinterest `1024x1536`; E-com `1024x1024` (主图).
- **English prompts** + mode booster, even when brief is Chinese.
- **Self-review is mandatory** — not optional. Every image gets checked.

## Reference Source

1. **「松鼠AIGC」** public materials:
   - Original skill `pinterest-pin-image` (provided as `原始SKILL.md`) — preview-before-generate principle, structured prompt format.
   - WeChat article 「WorkBuddy + Pinterest 社媒作图 Skill」(2026-08-02) — content distribution %, funnel, item-checklist method, **per-campaign item-list analysis approach**, **scene variety per product style**.
2. **「提示词生成大师 / Prompt Master」** skill — field decomposition (F-SUBJ/F-ENV/etc.), anti-bloat discipline, image-to-image parameters.
3. **Iterative field testing** (Aug 2026, 2 campaigns × 7 versions) — surfaced: anatomy-negative words cause artifacts, e-com white-bg invites phantom items, generic poses look AI, template-filling loses product specificity, **post-generation self-review is essential**.

## Resources

- `references/category_matrix.md` — Scene deduction engine, pose library, brand story matrix, camera filters, artifact guard, self-review checklist, prompt construction guidelines, worked examples. **Load before generating.**

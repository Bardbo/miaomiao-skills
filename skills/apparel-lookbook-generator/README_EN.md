# Apparel Lookbook Generator · 穿搭种草图生成器

<p align="center">
  <a href="README.md">🇨🇳 中文</a> · <a href="#readme">🇬🇧 English</a>
</p>

> WorkBuddy skill | technical name `apparel-lookbook-generator` | batch fashion imagery for Xiaohongshu / Pinterest
>
> One apparel reference photo → 6 coordinated social-commerce image types (Outfit / Flat Lay / Details / Lifestyle / Couple / Brand Story)

## One-liner

Upload one apparel / item reference photo (or a text brief) and get a **coordinated, authentic-looking set of 6 social-commerce fashion image types** for Xiaohongshu-style content: outfit looks, flat lays, product details, lifestyle scenes, couple/friend pairings, and brand-story stills.

**Runtime**: this skill is used inside **WorkBuddy** and relies on WorkBuddy's built-in ImageGen capability.

## What it does

- **Image-anchored consistency**: every image is generated image-to-image from the same reference photo, so the clothes, colors, materials and model stay consistent across the set — no more "same shirt, different shirt in every picture".
- **Scene deduction**: derives fitting scenes from the product itself (style / formality / season) — gallery, fine-dining, rooftop lounge, seaside — instead of the default coffee-shop cliché.
- **Forced full item inventory**: every garment and accessory in the reference is itemized into the prompt; nothing gets dropped (e.g. the stockings).
- **Realism enhancement**: per-category camera/film presets, real skin texture, fabric folds, plus a hard avoid-block that kills the AI-plastic look.
- **China-first**: default Chinese/East-Asian model and the Xiaohongshu "clean, premium" aesthetic; 3:4 for Xiaohongshu, 2:3 optional for Pinterest.
- **Preview before generating**: full prompt matrix + estimated credit cost shown and confirmed before any image is made.

## Differentiators

1. **Consistency anchored on the original image** — image-to-image beats "re-describe the clothes in text".
2. **No dropped items** — full inventory + distinctive-item descriptions fix "stockings missing / product looks wrong".
3. **Scenes derived from the product** — no more identical cafe street-shots.
4. **Real human texture** — realism rules + negative constraints against AI-render feel.
5. **Zero external dependency** — WorkBuddy's built-in ImageGen only; no third-party API or image-hosting account.
6. **Built for Chinese creators** — Chinese models + Xiaohongshu ins-style visual language.

## Who it's for

- Xiaohongshu / Douyin e-commerce bloggers and 种草 account operators
- Indie apparel brands, Taobao / Weidian shop owners making product imagery
- E-commerce / social-media operators producing outfit content in bulk
- Anyone who needs a coordinated set of fashion visuals

## Trigger phrases

小红书穿搭图, 社媒种草图, 服装平铺图, 电商产品细节图, 穿搭 lookbook, OOTD, 小红书笔记配图, Pinterest pin, 情侣穿搭, 品牌故事图, 服装生图, AI 穿搭, 电商详情图, outfit photography, flat lay, fashion lookbook

## Usage flow

1. Collect input: one apparel reference photo (recommended) or a text brief; confirm platform ratio (default Xiaohongshu 3:4) and Chinese-model preference.
2. Build the full item inventory (item by item, distinctive items described precisely).
3. (Optional) use vision_analyze to extract style / palette automatically.
4. Deduce 3–4 candidate scenes from the product; confirm with the user.
5. Create the output folder.
6. Preview the 6-type prompt matrix + estimated credit cost; user confirms.
7. Call ImageGen per image (all image-to-image, input_fidelity per category).
8. Collate files; give Xiaohongshu / Pinterest posting suggestions (title / hashtags / product link).

## Example user inputs

- "Use this photo to generate a set of Xiaohongshu outfit images"
- "Make flat lay + outfit + detail shots for this black dress"
- "Generate a preppy lookbook matrix for Pinterest"
- "Turn this outfit into 6 types of social-commerce images"

## Default parameters

- Sizes: Xiaohongshu 1080×1440 (3:4), Pinterest 1024×1536 (2:3)
- Model: Chinese / East-Asian female (changeable)
- input_fidelity: people / scenes 0.75–0.85, flat lay 0.78, details 0.65–0.75
- Credits: approx. 5–10 per image; a full 16-image set ≈ 80–160

## Prerequisites

- WorkBuddy's built-in ImageGen capability (included)
- Generation consumes credits; cost is previewed before generating
- Best practice: provide a clear apparel / item reference photo for best consistency

## Notes / known limitations

- Without a reference photo, cross-image identity of person/product cannot be guaranteed — you'll be told up front.
- Detail shots are extreme close-ups of the *original product*; fidelity is kept ≥ 0.65 so they never drift into generic studio still-lifes.
- Prompts default to English for best generation results; the skill handles this automatically.

## Attribution (transparent)

This skill is an original implementation — its name and mechanics are independent of the sources — but its methodology builds on and credits:

1. 松鼠AIGC's `pinterest-pin-image` skill and WeChat article (preview-before-generate, full item inventory, Pinterest content-type ratios / conversion funnel).
2. The "Prompt Master" skill's field-structured prompt decomposition, realism enhancement and negative-constraint techniques.


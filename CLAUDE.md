# Amazon → Pinterest Affiliate Bot — Project Rules

## What This Bot Does
Fetches Amazon.com (US) bestsellers across categories, generates designed pin images,
and posts them as organic Pinterest pins with affiliate links to drive outbound clicks
and commissions.

---

## Market
- **Amazon:** amazon.com (US) — never amazon.ca
- **Pinterest:** US account
- **Affiliate program:** Amazon Associates US
- **Associate tag:** stored in env var `AMAZON_ASSOCIATE_TAG`

---

## Save-Worthy Pin Rules (Non-Negotiable)

A pin must meet ALL of the following before it is posted. These exist because
0 saves = content not resonating. Every pin must earn its place.

### Image Design
1. **Aspect ratio:** 2:3 exactly — 1000×1500px output
2. **Price on image:** The product price must be visually present on the pin graphic itself
3. **Trust badge:** An "Amazon Find" or "🛒 Amazon Pick" label must appear on the image
4. **Product title:** Bold, readable at thumbnail size (min 36px font), never truncated
5. **CTA:** A visible "Shop on Amazon →" or equivalent call-to-action line
6. **Background:** Clean white or soft gradient — no busy/cluttered backgrounds
7. **Source image quality:** Amazon product image must be ≥400px on shorter side
8. **Text contrast:** All text must pass WCAG AA (4.5:1 contrast ratio minimum)

### Iterative Refinement Loop
The image generator (`image_generator.py`) must evaluate each generated pin before
accepting it. Run up to 3 refinement iterations per pin:

- Check: text contrast ratio ≥ 4.5:1
- Check: price string is present and rendered
- Check: output file dimensions are exactly 1000×1500
- Check: product image occupies 40–70% of pin height
- If any check fails → adjust parameters → regenerate → re-check
- Log which iteration passed or mark pin as skipped if all 3 fail

### Pin Description (SEO First)
- Lead sentence must be keyword-rich natural language (Pinterest is a search engine)
- Price must appear in the description text as well
- Max **5 hashtags** at the end — not 10+
- No filler phrases like "Check this out!" or "Amazing deal!"
- Never use #AmazonCA — wrong market

---

## Category Rules
- Current categories are revenue-weighted (commission rate × Pinterest search volume)
- Pinterest-native categories get priority: Beauty, Home, Fashion, Pets, Baby, Arts & Crafts
- Each category maps 1:1 to a Pinterest board — board name in config must match exactly
- Seasonal boosts in `config.py` must be reviewed each quarter

## Do Not
- Post raw Amazon product images without the designed pin treatment
- Post if price is unknown/missing (skip the product, don't fake a price)
- Post to `.ca` URLs or use Canadian affiliate tags
- Use `#AmazonCA` anywhere
- Hardcode credentials — all secrets via env vars / GitHub Secrets

---

## File Map
| File | Role |
|---|---|
| `config.py` | All category config, URLs, commission rates, seasonal boosts |
| `amazon_fetcher.py` | Scrapes amazon.com bestseller pages |
| `image_generator.py` | Generates designed 1000×1500 pin images (Pillow) |
| `pinterest_poster.py` | Playwright automation — uploads image, fills pin form |
| `sheet_logger.py` | Google Sheets deduplication + run logging |
| `main.py` | Orchestrator — ties everything together |

---

## Roadmap (in order)
- [x] CA → US market migration (config + fetcher)
- [ ] Image generator with save-worthy pin rules
- [ ] Expand categories: Pets, Baby, Arts & Crafts, Outdoor & Patio, Office
- [ ] Improve pin descriptions (SEO-first, less hashtag-stuffing)
- [ ] Monitoring: alert when a run posts 0 pins

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

## The Core Goal: Save-Worthy Pins

A pin must feel like content, not an advertisement.
Pinterest users save things they want to revisit — inspiration, solutions, discoveries.
A product card with a "Shop on Amazon" button reads as an ad and gets scrolled past.
0 saves = algorithm buries it = no reach = no commissions.

Every design and copy decision must ask: **"Would a real Pinterest user save this?"**

---

## Image Design Rules (Non-Negotiable)

### Background
- **Category-specific soft gradient** — not white, not solid colour. Gradient runs top
  to bottom from a saturated-but-soft tone to near-white. Each category has its own
  palette (see `image_generator.py → _CATEGORY_GRADIENTS`). This makes pins look like
  editorial content, not Amazon listings.
- The white product card sits on top of the gradient, creating a lifted card effect.
- **No lifestyle AI backgrounds for now** — gradients are reliable and fast.

### Category gradient palette (top → bottom):
| Category | Top colour (RGB) | Bottom colour (RGB) |
|---|---|---|
| Beauty & Personal Care | (253, 220, 220) blush | (255, 248, 248) near-white |
| Home & Kitchen | (255, 243, 220) warm cream | (255, 252, 245) near-white |
| Arts & Crafts | (237, 220, 255) soft lavender | (250, 245, 255) near-white |
| Pet Supplies | (220, 245, 235) mint | (245, 255, 250) near-white |
| Clothing & Fashion | (255, 220, 230) rose | (255, 248, 252) near-white |
| Baby & Nursery | (220, 235, 255) soft blue | (245, 250, 255) near-white |
| Sports & Fitness | (220, 235, 255) light blue | (240, 248, 255) near-white |
| Tools & Home Improvement | (235, 230, 220) warm grey | (250, 248, 245) near-white |
| Outdoor & Patio | (220, 240, 220) sage | (245, 255, 245) near-white |
| Electronics | (215, 228, 245) cool blue | (240, 246, 255) near-white |
| Health & Household | (220, 245, 235) sage | (245, 255, 250) near-white |
| Office & Desk | (240, 235, 225) warm cream | (252, 250, 248) near-white |
| Toys & Games | (255, 240, 200) warm yellow | (255, 252, 235) near-white |

### Layout requirements
1. **Aspect ratio:** 2:3 exactly — 1000×1500px output
2. **Trust badge:** Small "Amazon Find" pill badge — top left, Amazon orange, no emoji
3. **Product image:** Centred on white card, occupies 40–65% of pin height
4. **Product title:** Bold, min 42px font, max 3 lines, never truncated
5. **Price:** Large (min 52px), firebrick red, prominently placed
6. **NO "Shop on Amazon →" button on the image** — this signals advertisement to both
   humans and Pinterest's algorithm. It kills save rate. The description handles the CTA.
7. **Source image quality:** Amazon product image must be ≥400px on the longer side
8. **Text contrast:** All text on white card passes WCAG AA (4.5:1 minimum)

### Quality gate (runs automatically, up to 3 iterations)
- Dimensions exactly 1000×1500 ✓
- Price string rendered on image ✓
- If price missing → hard stop, skip product (never fake a price)
- Log iteration number that passed, or mark skipped if all 3 fail

---

## Pin Title Rules

**Formula: Hook first, product second.**

Pinterest titles should stop the scroll and create curiosity or signal value.
"Product Name | Amazon Category Find" is a product label — it does not create desire.

### Title templates by price tier
These are guides, not rigid strings. Rotate variants. Keep under 100 characters.

**Under $15 (budget hook):**
- `{price} Amazon {category_short} find — {short_title}`
- `Under {price}: {short_title}`
- `{short_title} — only {price} on Amazon`

**$15–$50 (value hook):**
- `{short_title} — the {category_short} upgrade worth every penny`
- `Amazon's most-repurchased {category_short}: {short_title}`
- `{short_title} | {price} · Amazon bestseller`

**No price / price unknown → skip product (CLAUDE.md rule — never fake price)**

### Category short labels for titles:
Beauty → "beauty" | Kitchen → "kitchen" | Pets → "pet" | Fashion → "fashion"
Baby → "baby" | Sports → "fitness" | Tools → "home" | Outdoor → "outdoor"
Electronics → "tech" | Health → "wellness" | Office → "desk" | Toys → "gift"

---

## Pin Description Rules

**Structure (in order):**
1. **Search-intent opener** — A phrase people actually type into Pinterest search.
   Examples: "best Amazon beauty finds", "amazon kitchen must haves", "gift ideas for pet lovers"
2. **Product sentence** — What it is and why it matters. One sentence, natural language.
3. **Price mention** — "Only $X." or "Priced at $X."
4. **Aesthetic/trend line** — One short phrase that connects to a Pinterest identity or trend.
   Examples: "Clean girl routine essential." / "Cottagecore kitchen staple." /
   "Minimalist desk upgrade." / "Coastal grandmother approved."
   Match to the category's Pinterest aesthetic — see notes per category in `pinterest_poster.py`.
5. **Seasonal angle** — When the month matches a seasonal moment, weave it in naturally.
   May = Mother's Day, spring refresh, outdoor season. Do not force it every pin.
6. **Soft CTA** — "Shop the link below." — one line, no exclamation marks.
7. **Hashtags** — Max 5, search-volume hashtags only. No brand hashtags except #AmazonFinds.

### What NOT to write in descriptions:
- "Check this out!" / "Amazing deal!" / "You need this!" — filler
- #AmazonCA — wrong market
- More than 5 hashtags
- Sentences that repeat what the title already said

---

## Human Behaviour Rules (Why People Save and Click)

These inform every design and copy decision:

1. **People save aspirational content** — they pin the life they want, not product specs
2. **Curiosity > information** — "Why this sells out every week" outperforms "$12.99 mascara"
3. **Identity/aesthetic connection drives saves** — a pin that fits a user's aesthetic board
   gets saved even if they don't buy immediately. Saves build reach.
4. **Price as a hook, not just data** — "$8" is a hook when positioned as surprising value.
   "Priced at $8.99" is just information.
5. **No visible ads** — any pin that looks like a sponsored post gets scrolled past.
   Remove all ad signals from the image: no CTA buttons, no "Buy now" language on the graphic.
6. **Gift framing converts** — people searching for gifts have buying intent and click affiliate
   links. Weave gift language into descriptions for high-gifting categories
   (Beauty, Pets, Baby, Toys, Electronics).

---

## Category Rules
- Revenue-weighted order: commission rate × Pinterest search volume drives `daily_posts`
- Pinterest-native categories get priority: Beauty, Home, Fashion, Pets, Baby, Outdoor
- Each category maps 1:1 to a Pinterest board — `board_name` in config must match exactly
- Seasonal boosts in `config.py` reviewed quarterly
- Arts & Crafts main bestsellers page is JavaScript-rendered — use subcategory node URL

## Do Not
- Post raw Amazon product images without the designed pin treatment
- Post if price is unknown/missing — skip the product, never fake a price
- Use "Shop on Amazon →" or any CTA button on the pin image itself
- Make the pin look like an ad (badge spam, button spam, cluttered layout)
- Post to `.ca` URLs or use Canadian affiliate tags
- Use `#AmazonCA` anywhere
- Hardcode credentials — all secrets via env vars / GitHub Secrets

---

## File Map
| File | Role |
|---|---|
| `config.py` | All category config, URLs, commission rates, seasonal boosts, account start date |
| `amazon_fetcher.py` | Scrapes amazon.com bestseller pages |
| `image_generator.py` | Generates designed 1000×1500 pin images (Pillow) |
| `pinterest_poster.py` | Playwright automation — uploads image, fills pin form |
| `sheet_logger.py` | Google Sheets deduplication + run logging |
| `main.py` | Orchestrator — account-age ramp, seasonal boosts, category loop |

---

## Roadmap (in order)
- [x] CA → US market migration (config + fetcher)
- [x] Image generator with quality gate
- [x] Single Pinterest session (no repeated logins)
- [x] Account-age posting ramp (auto-scales over 60 days)
- [x] All 13 boards shown in run summary
- [x] Category gradient backgrounds (remove white bg + CTA button from image)
- [x] Hook-first pin titles (price-led / curiosity-led)
- [x] Aesthetic/trend line in descriptions
- [ ] Fix Arts & Crafts scraper (JS-rendered page)
- [ ] Monitoring: alert when a run posts 0 pins

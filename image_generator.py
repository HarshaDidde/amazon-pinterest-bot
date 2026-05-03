# ─────────────────────────────────────────────
#  image_generator.py
#  Generates designed 1000×1500 Pinterest pin images using Pillow.
#  Optionally uses Gemini to generate category-specific lifestyle
#  backgrounds (set GOOGLE_AI_API_KEY to enable).
#  Every pin passes a quality gate before being returned.
#  Rules enforced: see CLAUDE.md — "Save-Worthy Pin Rules"
# ─────────────────────────────────────────────

import io
import os
import tempfile
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Canvas dimensions (Pinterest optimal 2:3) ─
PIN_W, PIN_H = 1000, 1500

# ── Colour palette ────────────────────────────
BG_COLOR    = (255, 255, 255)   # fallback white background
BADGE_BG    = (255, 153,   0)   # Amazon orange — trust badge
BADGE_FG    = (255, 255, 255)   # white text on badge
TITLE_FG    = ( 26,  26,  26)   # near-black title
PRICE_FG    = (178,  34,  34)   # firebrick red — price stands out
CTA_BG      = (255, 153,   0)   # Amazon orange — CTA button
CTA_FG      = (255, 255, 255)   # white CTA text
CARD_BG     = (255, 255, 255)   # white card behind product image
DIVIDER_CLR = (220, 220, 220)   # light gray rule

# ── Layout (y-coordinates in px) ─────────────
PAD      = 60     # horizontal padding
BADGE_Y  = 40     # trust badge top
IMG_TOP  = 140    # product image zone top
IMG_BOT  = 870    # product image zone bottom (730px = 49% of 1500 ✓)
RULE_Y   = 910    # horizontal divider
TITLE_Y  = 950    # title text top
PRICE_Y  = 1210   # price text top
CTA_Y1   = 1310   # CTA button top
CTA_Y2   = 1420   # CTA button bottom

# ── Gemini background ─────────────────────────
GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")

# Lifestyle background prompts per category.
# Goal: scene that contextualises the product without cluttering it.
_BG_PROMPTS: dict[str, str] = {
    "Beauty & Personal Care": (
        "Elegant bathroom vanity with soft warm lighting, marble surface, "
        "white and blush pink tones, no products, no text, no people, "
        "portrait orientation, soft focus background, photography style"
    ),
    "Home & Kitchen": (
        "Modern kitchen countertop with natural window light, white and warm "
        "wood tones, clean surface, no products, no text, no people, "
        "portrait orientation, soft focus, photography style"
    ),
    "Arts & Crafts": (
        "Rustic wooden craft table with soft natural side lighting, creative "
        "workspace feel, light neutral tones, no products, no text, no people, "
        "portrait orientation, soft focus, photography style"
    ),
    "Pet Supplies": (
        "Cozy modern living room with warm afternoon lighting, pet-friendly "
        "home atmosphere, soft neutral tones, no animals, no products, no text, "
        "portrait orientation, soft focus, lifestyle photography"
    ),
    "Clothing & Fashion": (
        "Minimal clothing boutique with soft diffused light, light wooden floor, "
        "white walls, airy atmosphere, no products, no text, no people, "
        "portrait orientation, fashion photography style"
    ),
    "Baby & Nursery": (
        "Soft pastel nursery room with natural light, white and mint green tones, "
        "gentle and cozy atmosphere, no products, no text, no people, "
        "portrait orientation, soft focus, lifestyle photography"
    ),
    "Sports & Fitness": (
        "Clean modern gym interior with soft overhead lighting, light floor, "
        "motivational minimal aesthetic, no equipment, no text, no people, "
        "portrait orientation, soft focus, photography style"
    ),
    "Tools & Home Improvement": (
        "Organised modern workshop with soft overhead lighting, clean workbench "
        "surface, neutral tones, no tools, no text, no people, "
        "portrait orientation, soft focus, photography style"
    ),
    "Outdoor & Patio": (
        "Beautiful outdoor patio with golden hour lighting, lush greenery in "
        "background, clean surface, no furniture, no text, no people, "
        "portrait orientation, lifestyle photography style"
    ),
    "Electronics": (
        "Minimal dark tech desk with soft blue-white ambient lighting, "
        "clean matte surface, modern aesthetic, no devices, no text, no people, "
        "portrait orientation, soft focus, product photography style"
    ),
    "Health & Household": (
        "Clean minimal wellness kitchen with natural light, white and sage green "
        "tones, calm healthy atmosphere, no products, no text, no people, "
        "portrait orientation, soft focus, lifestyle photography"
    ),
    "Office & Desk": (
        "Clean modern home office with natural window light, minimal desk surface, "
        "white and wood tones, calm productive aesthetic, no items, no text, no people, "
        "portrait orientation, soft focus, photography style"
    ),
    "Toys & Games": (
        "Bright cheerful playroom with soft natural light, colorful pastel walls, "
        "clean floor, fun family-friendly atmosphere, no toys, no text, no people, "
        "portrait orientation, soft focus, lifestyle photography"
    ),
    "default": (
        "Clean minimal white surface with soft natural lighting, "
        "no products, no text, no people, portrait orientation, photography style"
    ),
}


# ─────────────────────────────────────────────
#  Gemini background generator
# ─────────────────────────────────────────────
def _build_bg_prompt(product: dict) -> str:
    """
    Build an Imagen prompt that combines the category lifestyle scene
    with the specific product type for contextual relevance.
    e.g. Yoga Mat in Sports → gym scene with yoga/mindfulness context
         Protein Powder in Sports → gym scene with workout/energy context
    """
    category    = product.get("category", "")
    short_title = _clean_title(product.get("title", ""))
    base        = _BG_PROMPTS.get(category, _BG_PROMPTS["default"])
    return f"{base}, contextually appropriate for showcasing {short_title}"


def _generate_lifestyle_bg(product: dict) -> Image.Image | None:
    """
    Call Gemini to generate a product-contextual lifestyle background.
    Uses gemini-2.5-flash-image (free AI Studio API key compatible).
    Returns a PIL Image or None if the key is missing / call fails.
    Failure is always silent — caller falls back to white canvas.
    """
    if not GOOGLE_AI_API_KEY:
        return None
    try:
        from google import genai as google_genai        # google-genai package
        from google.genai import types as genai_types

        client = google_genai.Client(api_key=GOOGLE_AI_API_KEY)
        prompt = _build_bg_prompt(product)

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
        )
        for part in response.parts:
            if part.inline_data is not None:
                return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")

    except Exception as e:
        print(f"    [i] Gemini background skipped: {e}")
    return None


def _apply_background(bg: Image.Image) -> Image.Image:
    """
    Resize the Gemini background to cover 1000×1500, then apply a gradient
    white overlay so:
      • Top 58% (behind product image): soft 35% white overlay — lifestyle
        scene is clearly visible behind the product card.
      • Bottom 42% (text area): near-solid white — text is always readable.
    Returns a plain RGB canvas ready to draw on.
    """
    # Cover-resize: scale bg to fill 1000×1500, crop from centre
    bg_w, bg_h = bg.size
    scale = max(PIN_W / bg_w, PIN_H / bg_h)
    new_w, new_h = int(bg_w * scale), int(bg_h * scale)
    bg = bg.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - PIN_W) // 2
    top  = (new_h - PIN_H) // 2
    bg   = bg.crop((left, top, left + PIN_W, top + PIN_H))

    # Gentle blur so background doesn't compete with product
    bg = bg.filter(ImageFilter.GaussianBlur(radius=3))

    # Build RGBA overlay: light at top, opaque white at bottom
    overlay = Image.new("RGBA", (PIN_W, PIN_H), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    split   = RULE_Y - 40   # ~870px — where product zone ends

    # Product zone: 35% white overlay (background clearly visible)
    draw.rectangle([(0, 0), (PIN_W, split)], fill=(255, 255, 255, 90))

    # Text zone: near-solid white (text must be readable)
    draw.rectangle([(0, split), (PIN_W, PIN_H)], fill=(255, 255, 255, 248))

    result = Image.alpha_composite(bg.convert("RGBA"), overlay)
    return result.convert("RGB")


# ─────────────────────────────────────────────
#  Font loader
# ─────────────────────────────────────────────
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        if bold else
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, r: int, fill: tuple):
    draw.rounded_rectangle(xy, radius=r, fill=fill)


def _wrap(text: str, font, max_w: int, draw: ImageDraw.ImageDraw, max_lines: int = 3) -> list[str]:
    words, lines, buf = text.split(), [], []
    for word in words:
        test = " ".join(buf + [word])
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            buf.append(word)
        else:
            if buf:
                lines.append(" ".join(buf))
            buf = [word]
    if buf:
        lines.append(" ".join(buf))
    return lines[:max_lines]


def _clean_title(raw: str) -> str:
    """Strip Amazon variant noise — mirrors pinterest_poster._clean_title."""
    for sep in [" - ", " | ", ", "]:
        if sep in raw:
            raw = raw.split(sep)[0].strip()
            break
    if len(raw) > 80:
        raw = raw[:80].rsplit(" ", 1)[0].strip()
    return raw.rstrip(",.:")


def _download(url: str) -> Image.Image | None:
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 Chrome/124.0.0.0"},
            timeout=20,
        )
        if r.status_code == 200 and len(r.content) > 2000:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(r.content)
            tmp.close()
            img = Image.open(tmp.name).convert("RGB")
            Path(tmp.name).unlink(missing_ok=True)
            return img
    except Exception as e:
        print(f"    [!] Image download error: {e}")
    return None


# ─────────────────────────────────────────────
#  Quality gate
# ─────────────────────────────────────────────
def _quality_check(img: Image.Image, price_present: bool) -> tuple[bool, str]:
    w, h = img.size
    if (w, h) != (PIN_W, PIN_H):
        return False, f"dimensions {w}×{h} ≠ {PIN_W}×{PIN_H}"
    if not price_present:
        return False, "price missing — product skipped"
    return True, "ok"


# ─────────────────────────────────────────────
#  Core renderer
# ─────────────────────────────────────────────
def _render(product: dict) -> tuple[Image.Image, str] | None:
    """Compose one pin. Returns (PIL Image, temp file path) or None."""

    prod_img = _download(product["image_url"])
    if prod_img is None:
        return None

    sw, sh = prod_img.size
    if max(sw, sh) < 400:
        print(f"    [!] Source image too small ({sw}×{sh}) — skipping")
        return None

    # ── Canvas: lifestyle background or plain white ───────────────
    category = product.get("category", "")
    bg_img   = _generate_lifestyle_bg(product)

    if bg_img is not None:
        canvas     = _apply_background(bg_img)
        has_bg     = True
        short      = _clean_title(product["title"])
        print(f"    [✓] Lifestyle background applied for: {short[:40]}")
    else:
        canvas     = Image.new("RGB", (PIN_W, PIN_H), BG_COLOR)
        has_bg     = False

    draw = ImageDraw.Draw(canvas)

    f_badge = _font(30, bold=True)
    f_title = _font(46, bold=True)
    f_price = _font(58, bold=True)
    f_cta   = _font(36, bold=True)

    # ── White card behind product (always — doubles as pop on background) ──
    card_pad = 24
    _rounded_rect(
        draw,
        (
            PAD - card_pad,
            IMG_TOP - card_pad,
            PIN_W - PAD + card_pad,
            IMG_BOT + card_pad,
        ),
        r=20,
        fill=CARD_BG,
    )

    # ── Trust badge ───────────────────────────
    badge_txt = "Amazon Find"
    bp        = (26, 14)
    bw        = draw.textbbox((0, 0), badge_txt, font=f_badge)[2] + bp[0] * 2
    bh        = draw.textbbox((0, 0), badge_txt, font=f_badge)[3] + bp[1] * 2
    _rounded_rect(draw, (PAD, BADGE_Y, PAD + bw, BADGE_Y + bh), r=8, fill=BADGE_BG)
    draw.text((PAD + bp[0], BADGE_Y + bp[1]), badge_txt, font=f_badge, fill=BADGE_FG)

    # ── Product image (inside white card) ─────
    zone_w = PIN_W - PAD * 2
    zone_h = IMG_BOT - IMG_TOP
    prod_img.thumbnail((zone_w, zone_h), Image.LANCZOS)
    fw, fh = prod_img.size
    px     = (PIN_W - fw) // 2
    py     = IMG_TOP + (zone_h - fh) // 2
    canvas.paste(prod_img, (px, py))

    # ── Divider ───────────────────────────────
    draw.rectangle([(PAD, RULE_Y), (PIN_W - PAD, RULE_Y + 2)], fill=DIVIDER_CLR)

    # ── Title ─────────────────────────────────
    short = _clean_title(product["title"])
    lines = _wrap(short, f_title, PIN_W - PAD * 2, draw, max_lines=3)
    ty    = TITLE_Y
    lh    = draw.textbbox((0, 0), "A", font=f_title)[3] + 10
    for line in lines:
        draw.text((PAD, ty), line, font=f_title, fill=TITLE_FG)
        ty += lh

    # ── Price ─────────────────────────────────
    raw_price = product.get("price", "")
    price_str = raw_price if "$" in raw_price else (f"${raw_price}" if raw_price else "")
    if price_str:
        draw.text((PAD, PRICE_Y), price_str, font=f_price, fill=PRICE_FG)

    # ── CTA button ────────────────────────────
    cta_txt      = "Shop on Amazon  →"
    cbbox        = draw.textbbox((0, 0), cta_txt, font=f_cta)
    cw, ch       = cbbox[2] - cbbox[0], cbbox[3] - cbbox[1]
    cp           = 32
    cx1, cy1     = PAD, CTA_Y1
    cx2, cy2     = cx1 + cw + cp * 2, CTA_Y2
    _rounded_rect(draw, (cx1, cy1, cx2, cy2), r=12, fill=CTA_BG)
    draw.text(
        (cx1 + cp, cy1 + (CTA_Y2 - CTA_Y1 - ch) // 2),
        cta_txt, font=f_cta, fill=CTA_FG,
    )

    # ── Save ──────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    canvas.save(tmp.name, "JPEG", quality=92)
    tmp.close()

    return canvas, tmp.name


# ─────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────
def generate_pin_image(product: dict) -> str | None:
    """
    Generate a save-worthy 1000×1500 pin image for the given product.
    If GOOGLE_AI_API_KEY is set, uses Gemini to generate a category-specific
    lifestyle background. Falls back to white canvas silently if not.

    Runs up to 3 render + quality-check iterations (CLAUDE.md rule).
    Returns path to the temp JPEG on success, None on failure.
    Caller is responsible for deleting the file after upload.
    """
    price_present = bool(product.get("price"))

    for attempt in range(3):
        result = _render(product)

        if result is None:
            print(f"    [!] Render failed (attempt {attempt + 1}/3)")
            continue

        img, path = result
        passed, reason = _quality_check(img, price_present)

        if passed:
            if attempt > 0:
                print(f"    [✓] Quality gate passed on iteration {attempt + 1}")
            return path

        print(f"    [!] Quality gate failed (attempt {attempt + 1}/3): {reason}")
        Path(path).unlink(missing_ok=True)

        if "price missing" in reason:
            return None   # hard stop — no point retrying

    print("    [x] Pin image failed all 3 quality checks — skipping product")
    return None

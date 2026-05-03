# ─────────────────────────────────────────────
#  pinterest_poster.py  —  Browser automation via Playwright
#  Logs into Pinterest with email+password and creates pins
#  through the web UI. No API approval needed.
# ─────────────────────────────────────────────

import os
import re
import time
import random
from contextlib import contextmanager
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from image_generator import generate_pin_image

PINTEREST_EMAIL    = os.environ.get("PINTEREST_EMAIL", "")
PINTEREST_PASSWORD = os.environ.get("PINTEREST_PASSWORD", "")
POST_DELAY_SECONDS = 8

# ─────────────────────────────────────────────────────────────────────────────
#  Pin title suffix per category.
#  Pinterest title = cleaned product name + suffix.
#  Keeps it keyword-rich and short enough to read at a glance.
# ─────────────────────────────────────────────────────────────────────────────
_TITLE_SUFFIX = {
    "Beauty & Personal Care":   "| Amazon Beauty Find",
    "Home & Kitchen":           "| Amazon Home Find",
    "Arts & Crafts":            "| Amazon Craft Find",
    "Pet Supplies":             "| Amazon Pet Find",
    "Clothing & Fashion":       "| Amazon Fashion Find",
    "Baby & Nursery":           "| Amazon Baby Find",
    "Sports & Fitness":         "| Amazon Fitness Find",
    "Tools & Home Improvement": "| Amazon Tool Find",
    "Outdoor & Patio":          "| Amazon Outdoor Find",
    "Electronics":              "| Amazon Tech Find",
    "Health & Household":       "| Amazon Wellness Find",
    "Office & Desk":            "| Amazon Office Find",
    "Toys & Games":             "| Amazon Gift Idea",
}

# ─────────────────────────────────────────────────────────────────────────────
#  Description templates — 3 variants per category.
#  Rules (per CLAUDE.md):
#   • Lead sentence = keyword phrase people actually type into Pinterest search
#   • Price must appear in the description
#   • Max 5 hashtags
#   • No filler ("Amazing!", "Shop now!", "Tap to shop!")
#   • Natural language throughout
# ─────────────────────────────────────────────────────────────────────────────
_TEMPLATES = {
    "Beauty & Personal Care": [
        "Best Amazon beauty finds right now — {short_title}. {price_text}{aesthetic} Thousands of five-star reviews. A simple addition that actually delivers.\nShop the link below.\n\n{tags}",
        "Amazon skincare must haves — {short_title}. {price_text}{aesthetic} One of the most loved picks in beauty right now. Worth every penny.\nShop the link below.\n\n{tags}",
        "Amazon beauty finds that actually work — {short_title}. {price_text}{aesthetic} Real results, honest reviews, and a price that makes sense.\nShop the link below.\n\n{tags}",
    ],
    "Home & Kitchen": [
        "Amazon kitchen must haves — {short_title}. {price_text}{aesthetic} One of the highest-rated home picks right now. A small upgrade that makes a real difference.\nShop the link below.\n\n{tags}",
        "Amazon home finds worth buying — {short_title}. {price_text}{aesthetic} Practical, well-reviewed, and priced right. Exactly the upgrade you didn't know you needed.\nShop the link below.\n\n{tags}",
        "Best Amazon home gadgets right now — {short_title}. {price_text}{aesthetic} Trusted by thousands. Fast shipping and easy returns.\nShop the link below.\n\n{tags}",
    ],
    "Arts & Crafts": [
        "Best craft supplies on Amazon for DIY projects — {short_title}. {price_text}{aesthetic} Top-rated by makers and beginners alike. Ships fast.\nShop the link below.\n\n{tags}",
        "Amazon craft finds that makers love — {short_title}. {price_text}{aesthetic} Thousands of crafters rate this one highly. Stock your creative space right.\nShop the link below.\n\n{tags}",
        "Amazon art supplies worth buying — {short_title}. {price_text}{aesthetic} Whether you're starting a new hobby or restocking, this one delivers.\nShop the link below.\n\n{tags}",
    ],
    "Pet Supplies": [
        "Best Amazon finds for dog and cat owners — {short_title}. {price_text}{aesthetic} One of the top-rated pet picks on Amazon. Your fur baby will love it.\nShop the link below.\n\n{tags}",
        "Amazon pet essentials owners swear by — {short_title}. {price_text}{aesthetic} Trusted by thousands of pet parents. Makes daily pet care genuinely easier.\nShop the link below.\n\n{tags}",
        "Amazon pet finds worth every penny — {short_title}. {price_text}{aesthetic} Pet owners keep coming back to this one. Great quality, great price.\nShop the link below.\n\n{tags}",
    ],
    "Clothing & Fashion": [
        "Affordable Amazon fashion finds people are obsessed with — {short_title}. {price_text}{aesthetic} Top-rated, stylish, and ships fast.\nShop the link below.\n\n{tags}",
        "Amazon wardrobe essentials worth adding — {short_title}. {price_text}{aesthetic} Thousands of shoppers love this one. Great quality for any budget.\nShop the link below.\n\n{tags}",
        "Amazon fashion finds that actually look good — {short_title}. {price_text}{aesthetic} Versatile, well-reviewed, and genuinely worth it.\nShop the link below.\n\n{tags}",
    ],
    "Baby & Nursery": [
        "Amazon baby must haves new parents swear by — {short_title}. {price_text}{aesthetic} Thousands of five-star reviews. Makes a perfect baby shower gift.\nShop the link below.\n\n{tags}",
        "Best baby shower gift ideas on Amazon — {short_title}. {price_text}{aesthetic} One of the best-selling baby picks on Amazon. Parents buy it again and again.\nShop the link below.\n\n{tags}",
        "Nursery essentials from Amazon every new parent needs — {short_title}. {price_text}{aesthetic} Practical, top-rated, and actually makes early parenthood easier.\nShop the link below.\n\n{tags}",
    ],
    "Sports & Fitness": [
        "Amazon fitness finds worth the investment — {short_title}. {price_text}{aesthetic} One of the top-rated workout picks on Amazon. Level up without breaking the bank.\nShop the link below.\n\n{tags}",
        "Best workout gear on Amazon right now — {short_title}. {price_text}{aesthetic} Thousands of fitness lovers rate this highly. Practical and built to last.\nShop the link below.\n\n{tags}",
        "Amazon home gym essentials that actually deliver — {short_title}. {price_text}{aesthetic} A top seller in fitness for good reason. Reliable gear at the right price.\nShop the link below.\n\n{tags}",
    ],
    "Tools & Home Improvement": [
        "Best Amazon tools for DIY and home repairs — {short_title}. {price_text}{aesthetic} Top-rated by homeowners and weekend warriors. Practical and priced right.\nShop the link below.\n\n{tags}",
        "Amazon home improvement finds worth having — {short_title}. {price_text}{aesthetic} Thousands of verified reviews. Every homeowner needs this in their kit.\nShop the link below.\n\n{tags}",
        "Amazon DIY finds worth every penny — {short_title}. {price_text}{aesthetic} Renovating or doing quick repairs — this tool delivers every time.\nShop the link below.\n\n{tags}",
    ],
    "Outdoor & Patio": [
        "Amazon outdoor finds for your backyard upgrade — {short_title}. {price_text}{aesthetic} One of the top-rated patio picks right now. Transform your space for less.\nShop the link below.\n\n{tags}",
        "Amazon patio essentials worth buying this season — {short_title}. {price_text}{aesthetic} Thousands of happy customers. Great quality at a price that works.\nShop the link below.\n\n{tags}",
        "Best outdoor finds on Amazon right now — {short_title}. {price_text}{aesthetic} A top seller in patio and garden. Perfect for any outdoor space.\nShop the link below.\n\n{tags}",
    ],
    "Electronics": [
        "Best Amazon tech finds worth buying — {short_title}. {price_text}{aesthetic} Top-rated with thousands of verified reviews. Genuinely worth the price.\nShop the link below.\n\n{tags}",
        "Amazon gadgets that are worth adding to your setup — {short_title}. {price_text}{aesthetic} One of the highest-rated electronics on Amazon. Real upgrade, fair price.\nShop the link below.\n\n{tags}",
        "Amazon tech finds people actually love — {short_title}. {price_text}{aesthetic} Loved for its performance and value. A tech pick you won't regret.\nShop the link below.\n\n{tags}",
    ],
    "Health & Household": [
        "Amazon wellness finds actually worth trying — {short_title}. {price_text}{aesthetic} Thousands of five-star reviews. A simple addition with real results.\nShop the link below.\n\n{tags}",
        "Amazon health finds that live up to the hype — {short_title}. {price_text}{aesthetic} One of the best-selling wellness picks right now. Trusted for daily use.\nShop the link below.\n\n{tags}",
        "Daily wellness must haves from Amazon — {short_title}. {price_text}{aesthetic} Quality you can feel, price that makes sense. Worth keeping stocked.\nShop the link below.\n\n{tags}",
    ],
    "Office & Desk": [
        "Amazon home office finds people love — {short_title}. {price_text}{aesthetic} Top-rated for anyone working from home or upgrading their desk setup.\nShop the link below.\n\n{tags}",
        "Amazon desk setup finds worth buying — {short_title}. {price_text}{aesthetic} One of the highest-rated office picks. A workspace upgrade that actually delivers.\nShop the link below.\n\n{tags}",
        "Work from home essentials on Amazon — {short_title}. {price_text}{aesthetic} Thousands of remote workers love this. Real impact on your daily routine.\nShop the link below.\n\n{tags}",
    ],
    "Toys & Games": [
        "Best Amazon gift ideas for kids parents actually recommend — {short_title}. {price_text}{aesthetic} Thousands of happy reviews. Perfect for birthdays or holidays.\nShop the link below.\n\n{tags}",
        "Amazon kids gift ideas they will actually use — {short_title}. {price_text}{aesthetic} One of the best-selling toys on Amazon. Fun, engaging, worth every penny.\nShop the link below.\n\n{tags}",
        "Top-rated Amazon toys and games — {short_title}. {price_text}{aesthetic} A family favourite with five-star reviews. Great for all ages, ships fast.\nShop the link below.\n\n{tags}",
    ],
}

_DEFAULT_TEMPLATES = [
    "Top-rated Amazon find worth knowing — {short_title}. {price_text}{aesthetic} Thousands of verified reviews.\nShop the link below.\n\n{tags}",
    "Amazon find worth buying — {short_title}. {price_text}{aesthetic} Highly rated, practical, priced right.\nShop the link below.\n\n{tags}",
    "Best-selling Amazon essential — {short_title}. {price_text}{aesthetic} Trusted by thousands of shoppers.\nShop the link below.\n\n{tags}",
]


def _clean_title(raw: str) -> str:
    """Strip Amazon variant/model noise, return a short readable product name."""
    for sep in [" - ", " | ", ", "]:
        if sep in raw:
            raw = raw.split(sep)[0].strip()
            break
    if len(raw) > 60:
        raw = raw[:60].rsplit(" ", 1)[0].strip()
    return raw.rstrip(",.:")


# ── Category short labels used in hook titles ──────────────────────────────
_CAT_SHORT = {
    "Beauty & Personal Care":   "beauty",
    "Home & Kitchen":           "kitchen",
    "Arts & Crafts":            "craft",
    "Pet Supplies":             "pet",
    "Clothing & Fashion":       "fashion",
    "Baby & Nursery":           "baby",
    "Sports & Fitness":         "fitness",
    "Tools & Home Improvement": "home",
    "Outdoor & Patio":          "outdoor",
    "Electronics":              "tech",
    "Health & Household":       "wellness",
    "Office & Desk":            "desk",
    "Toys & Games":             "gift",
}


def _parse_price_dollars(price_str: str) -> float | None:
    """Extract numeric dollar amount from a price string like '$12.99'."""
    import re as _re
    m = _re.search(r"[\d]+\.?\d*", price_str.replace(",", ""))
    return float(m.group()) if m else None


def _build_pin_title(product: dict, template_key: str) -> str:
    """
    Hook-first title formula (per CLAUDE.md):
    - Under $15: price-led hook — "$9 Amazon beauty find everyone is buying"
    - $15–$50:   value hook    — "Amazon's most-repurchased kitchen find: {title}"
    - No price:  search hook  — "Most-saved Amazon {cat} find right now"
    Keeps title under 100 characters.
    """
    short    = _clean_title(product["title"])
    cat      = _CAT_SHORT.get(template_key, "find")
    price    = product.get("price", "")
    dollars  = _parse_price_dollars(price) if price else None

    if dollars is not None and dollars < 15:
        templates = [
            f"{price} Amazon {cat} find everyone is buying — {short}",
            f"Under {price}: {short}",
            f"{short} — only {price} on Amazon",
        ]
    elif dollars is not None:
        templates = [
            f"{short} — the {cat} upgrade worth every penny",
            f"Amazon's most-repurchased {cat} find: {short}",
            f"{short} | {price} · Amazon bestseller",
        ]
    else:
        templates = [
            f"Most-saved Amazon {cat} find right now — {short}",
            f"{short} | Top-rated Amazon {cat} pick",
        ]

    return random.choice(templates)[:100]


# ── Aesthetic/trend lines per category ────────────────────────────────────
# One phrase per pin that connects the product to a Pinterest identity.
# Rotated randomly. Keeps pins feeling human, not algorithmic.
_AESTHETICS: dict[str, list[str]] = {
    "Beauty & Personal Care": [
        "Clean girl routine essential.",
        "Your glow-up starts here.",
        "Minimal skincare, maximum results.",
        "That girl approved.",
        "Self-care shelf staple.",
    ],
    "Home & Kitchen": [
        "Cosy kitchen upgrade.",
        "Cottagecore kitchen staple.",
        "That organized home aesthetic.",
        "Clean kitchen, clear mind.",
        "Neutral home essentials.",
    ],
    "Arts & Crafts": [
        "Crafty girl must-have.",
        "Creative space essential.",
        "DIY season starts now.",
        "For the maker in you.",
        "Aesthetic craft supplies.",
    ],
    "Pet Supplies": [
        "Because they deserve the best.",
        "Pet parent approved.",
        "Fur baby essentials.",
        "Dog mom / cat mom must-have.",
        "Spoil them a little.",
    ],
    "Clothing & Fashion": [
        "Quiet luxury vibes.",
        "Old money wardrobe essential.",
        "Effortless everyday style.",
        "That put-together look.",
        "Coastal grandmother approved.",
    ],
    "Baby & Nursery": [
        "Nursery aesthetic goals.",
        "New mama must-have.",
        "Soft life for your little one.",
        "Boho nursery essential.",
        "Perfect baby shower gift idea.",
    ],
    "Sports & Fitness": [
        "That girl workout essential.",
        "Fitness era starts now.",
        "Home gym must-have.",
        "Healthy girl lifestyle.",
        "Move more, stress less.",
    ],
    "Tools & Home Improvement": [
        "DIY home era.",
        "Weekend project ready.",
        "That handyman aesthetic.",
        "Home renovation essential.",
        "Fix it, own it.",
    ],
    "Outdoor & Patio": [
        "Backyard goals.",
        "Outdoor living aesthetic.",
        "Al fresco season essential.",
        "Patio glow-up incoming.",
        "Garden girl approved.",
    ],
    "Electronics": [
        "Minimal tech setup.",
        "Dark academia desk essential.",
        "Clean tech aesthetic.",
        "Work smarter, not harder.",
        "Tech that actually makes sense.",
    ],
    "Health & Household": [
        "Wellness era essentials.",
        "Healthy home, healthy life.",
        "Clean living staple.",
        "Gut health girl approved.",
        "Soft life wellness pick.",
    ],
    "Office & Desk": [
        "Aesthetic desk setup.",
        "That girl home office.",
        "Productive space, clear mind.",
        "Work from home upgrade.",
        "Minimal desk, maximum focus.",
    ],
    "Toys & Games": [
        "The gift they'll actually use.",
        "Screen-free fun approved.",
        "Birthday gift sorted.",
        "Kids will love it, parents will too.",
        "Holiday gift idea locked in.",
    ],
}


def _build_description(product: dict, hashtags: list[str], template_key: str) -> str:
    price_text  = f"Only {product['price']}. " if product.get("price") else ""
    tags        = " ".join(hashtags[:5])          # max 5 per CLAUDE.md rules
    short_title = _clean_title(product["title"])
    aesthetic   = random.choice(_AESTHETICS.get(template_key, ["Amazon find worth knowing."]))
    variants    = _TEMPLATES.get(template_key, _DEFAULT_TEMPLATES)
    return random.choice(variants).format(
        short_title=short_title,
        price_text=price_text,
        tags=tags,
        aesthetic=aesthetic,
    )


def _dismiss_popups(page):
    """Close any Pinterest modals/banners that block interaction."""
    for selector in [
        'button[aria-label="Close"]',
        'button:has-text("Not now")',
        'button:has-text("Skip")',
        'button:has-text("Dismiss")',
        '[data-test-id="close-button"]',
    ]:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=800):
                el.click()
                time.sleep(0.5)
        except Exception:
            pass


def _login(page):
    """Log into Pinterest with email + password."""
    page.goto("https://www.pinterest.com/login/", wait_until="domcontentloaded")
    time.sleep(2)
    _dismiss_popups(page)

    page.fill('input[name="id"]', PINTEREST_EMAIL)
    time.sleep(random.uniform(0.3, 0.7))

    page.fill('input[name="password"]', PINTEREST_PASSWORD)
    time.sleep(random.uniform(0.3, 0.7))

    page.click('button[type="submit"]')

    try:
        page.wait_for_url(lambda url: "/login/" not in url, timeout=20000)
        time.sleep(3)
        print("    [✓] Logged in to Pinterest")
        return True
    except PWTimeout:
        print("    [x] Pinterest login timed out — check credentials")
        try:
            page.screenshot(path="debug-login-failure.png", full_page=True)
            print("    [debug] Screenshot saved: debug-login-failure.png")
        except Exception:
            pass
        return False


def _fill_field(page, selectors: list[str], value: str, timeout: int = 2000):
    """Try each selector in order, fill the first visible one."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=timeout):
                el.click()
                time.sleep(0.3)
                el.fill(value)
                return True
        except Exception:
            continue
    return False


def _click_first(page, selectors: list[str], timeout: int = 2000) -> bool:
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=timeout):
                el.click()
                return True
        except Exception:
            continue
    return False


def _create_pin(page, product: dict, board_name: str, pin_title: str, description: str) -> str | None:
    """Create one pin. Returns pin URL on success, None on failure."""
    image_path = generate_pin_image(product)
    if not image_path:
        print(f"  [x] Skipping — image generation failed for: {product['title'][:50]}")
        return None

    try:
        for attempt in range(3):
            try:
                page.goto(
                    "https://www.pinterest.com/pin-creation-tool/",
                    wait_until="domcontentloaded",
                    timeout=90000,
                )
                break
            except PWTimeout:
                if attempt < 2:
                    print(f"    Navigation timeout (attempt {attempt+1}/3) — retrying...")
                    time.sleep(8)
                else:
                    raise
        time.sleep(3)
        _dismiss_popups(page)

        # ── Upload image ──────────────────────────────────────────
        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(image_path)
        print(f"    Uploading image...")
        try:
            page.locator('[data-test-id="pin-draft-title"], input[placeholder*="title" i]').first.wait_for(
                state="visible", timeout=15000
            )
        except PWTimeout:
            time.sleep(6)
        _dismiss_popups(page)

        # ── Title (Pinterest-optimised, not raw Amazon title) ─────
        _fill_field(page, [
            '[data-test-id="pin-draft-title"]',
            'input[placeholder*="title" i]',
            'input[aria-label*="title" i]',
        ], pin_title)
        time.sleep(0.5)

        # ── Description ───────────────────────────────────────────
        _fill_field(page, [
            '[data-test-id="pin-draft-description"]',
            'textarea[placeholder*="description" i]',
            'div[contenteditable][aria-label*="description" i]',
            'div[data-test-id="pin-description"] div[contenteditable]',
        ], description[:500])
        time.sleep(0.5)

        # ── Destination link ──────────────────────────────────────
        _fill_field(page, [
            '[data-test-id="pin-draft-link"]',
            'input[placeholder*="destination link" i]',
            'input[placeholder*="Add a link" i]',
            'input[aria-label*="link" i]',
        ], product["affiliate_link"])
        time.sleep(0.5)

        # ── Board selector ────────────────────────────────────────
        time.sleep(1.5)

        board_opened = False
        for board_attempt in range(3):
            board_opened = _click_first(page, [
                '[data-test-id="board-dropdown-select-button"]',
                'button[aria-label*="board" i]',
                'button:has-text("Choose a board")',
                'button:has-text("Select")',
                '[data-test-id="pin-draft-board"] button',
                'div[data-test-id="board-selection"] button',
            ], timeout=4000)
            if board_opened:
                break
            print(f"    Board selector attempt {board_attempt+1}/3 — retrying...")
            time.sleep(2)

        if not board_opened:
            print(f"  [x] Could not open board selector for: {product['title'][:50]}")
            return None

        try:
            page.get_by_text("All boards").first.wait_for(state="visible", timeout=8000)
        except PWTimeout:
            time.sleep(3)

        try:
            search = page.locator('input[placeholder*="Search" i]').first
            if search.is_visible(timeout=2000):
                search.fill("")
                time.sleep(0.3)
                search.type(board_name, delay=80)
                time.sleep(2.0)
        except Exception:
            pass

        try:
            page.get_by_text(board_name, exact=True).first.click(timeout=5000)
            print(f"    Board '{board_name}' selected")
        except Exception:
            try:
                page.get_by_text(board_name).first.click(timeout=3000)
                print(f"    Board '{board_name}' selected (partial match)")
            except Exception:
                print(f"  [x] Board '{board_name}' not found in dropdown")
                return None

        time.sleep(1.5)

        # ── Publish ───────────────────────────────────────────────
        published = _click_first(page, [
            '[data-test-id="board-dropdown-save-button"]',
            'button:has-text("Publish")',
            'button[aria-label="Publish pin"]',
            'button:has-text("Save")',
        ])
        if not published:
            print(f"  [x] Could not find Publish button for: {product['title'][:50]}")
            return None

        time.sleep(3)

        # Layer 1: wait for Pinterest to redirect to the pin page
        try:
            page.wait_for_url(
                lambda url: bool(re.search(r'/pin/\d+', url)),
                timeout=8000,
            )
            return page.url
        except PWTimeout:
            pass

        # Layer 2: look for "View pin" link in success notification
        for sel in [
            'a:has-text("View pin")',
            'a:has-text("View Pin")',
            'a[data-test-id*="view"] [href*="/pin/"]',
        ]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    href = el.get_attribute("href") or ""
                    if re.search(r'/pin/\d{10,}', href):
                        return f"https://www.pinterest.com{href}" if href.startswith("/") else href
            except Exception:
                pass

        # Layer 3: scan all pin links visible on the page
        try:
            for link in page.locator('a[href*="/pin/"]').all():
                href = link.get_attribute("href") or ""
                if re.search(r'/pin/\d{10,}', href):
                    return f"https://www.pinterest.com{href}" if href.startswith("/") else href
        except Exception:
            pass

        # Layer 4: give it a few more seconds and re-check
        time.sleep(5)
        current_url = page.url
        if re.search(r'/pin/\d{10,}', current_url):
            return current_url

        # Layer 5: pin posted but URL not captured
        return f"posted_no_url_{int(time.time())}"

    except Exception as e:
        print(f"  [x] Pin creation error: {e}")
        return None
    finally:
        Path(image_path).unlink(missing_ok=True)


_BROWSER_CONTEXT = dict(
    user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    viewport={"width": 1280, "height": 900},
)


@contextmanager
def pinterest_session():
    """
    Context manager yielding a single logged-in Pinterest page.
    Use this to share one login across all category posts — avoids
    repeated logins that trigger Pinterest's security checks.

    Usage in main.py:
        with pinterest_session() as page:
            post_pins_for_category(..., page=page)
    """
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        raise RuntimeError("PINTEREST_EMAIL or PINTEREST_PASSWORD not set")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(**_BROWSER_CONTEXT)
        pg      = ctx.new_page()
        if not _login(pg):
            browser.close()
            raise RuntimeError("Pinterest login failed — check credentials")
        try:
            yield pg
        finally:
            browser.close()


def _post_batch(
    page,
    products: list[dict],
    board_name: str,
    hashtags: list[str],
    template_key: str,
    limit: int,
) -> list[dict]:
    """
    Inner posting loop — iterates all candidates until `limit` pins are
    successfully posted or the list is exhausted. A failed product (no price,
    image error, etc.) does NOT count against the limit — the next candidate
    is tried instead.
    """
    posted = []
    for product in products:
        if len(posted) >= limit:
            break
        print(f"  [{len(posted)+1}/{limit}] {product['title'][:60]}")
        pin_title   = _build_pin_title(product, template_key)
        description = _build_description(product, hashtags, template_key)
        pin_url     = _create_pin(page, product, board_name, pin_title, description)
        if pin_url:
            product["pin_url"] = pin_url
            posted.append(product)
            print(f"  [✓] Posted → {pin_url}")
            if len(posted) < limit:
                time.sleep(POST_DELAY_SECONDS)
        else:
            print(f"  [!] Failed — trying next product")
    return posted


def post_pins_for_category(
    products: list[dict],
    board_name: str,
    hashtags: list[str],
    template_key: str = "",
    limit: int = 10,
    page=None,
) -> list[dict]:
    """
    Posts up to `limit` products for one category.
    Pass `page` from pinterest_session() to reuse an existing login.
    If page is None, opens its own browser session (legacy / standalone use).
    """
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("  [x] PINTEREST_EMAIL or PINTEREST_PASSWORD env var not set — skipping")
        return []

    if page is not None:
        return _post_batch(page, products, board_name, hashtags, template_key, limit)

    # Standalone fallback — opens its own session
    posted = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(**_BROWSER_CONTEXT)
        pg      = ctx.new_page()
        if not _login(pg):
            browser.close()
            return []
        posted = _post_batch(pg, products, board_name, hashtags, template_key, limit)
        browser.close()
    return posted

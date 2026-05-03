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
        "Top-rated Amazon skincare find — {short_title}. {price_text}Thousands of five-star reviews and a staple in beauty routines across the US. A simple addition that actually delivers results.\nShop the link below.\n\n{tags}",
        "Best-selling Amazon beauty essential — {short_title}. {price_text}One of the most loved picks in Beauty & Personal Care right now. Whether for yourself or as a gift, this one is worth it.\nShop the link below.\n\n{tags}",
        "Affordable Amazon beauty find that lives up to the hype — {short_title}. {price_text}High-quality formula, real results, and a price that makes sense. This keeps selling out for a reason.\nShop the link below.\n\n{tags}",
    ],
    "Home & Kitchen": [
        "Kitchen organization find from Amazon worth every penny — {short_title}. {price_text}One of the highest-rated picks in Home & Kitchen right now. A small upgrade that makes a real difference.\nShop the link below.\n\n{tags}",
        "Amazon home essential everyone is buying right now — {short_title}. {price_text}Practical, well-reviewed, and priced right. Exactly the home upgrade you didn't know you needed.\nShop the link below.\n\n{tags}",
        "Best-selling Amazon home find — {short_title}. {price_text}Trusted by thousands of happy customers. Fast shipping and easy returns make this a no-brainer.\nShop the link below.\n\n{tags}",
    ],
    "Arts & Crafts": [
        "Best craft supplies on Amazon for your next DIY project — {short_title}. {price_text}A top-rated pick for anyone who loves art, crafting, or creative projects. Ships fast and worth every penny.\nShop the link below.\n\n{tags}",
        "Amazon craft find that makers actually love — {short_title}. {price_text}Thousands of crafters rate this one highly. Great for beginners and experienced makers alike.\nShop the link below.\n\n{tags}",
        "Top-rated art supply on Amazon — {short_title}. {price_text}Whether you're starting a new hobby or stocking your craft space, this is a must-have. Real reviews, real results.\nShop the link below.\n\n{tags}",
    ],
    "Pet Supplies": [
        "Best Amazon find for dog and cat owners — {short_title}. {price_text}One of the top-rated pet products on Amazon right now. Your fur baby will love it — and your wallet will too.\nShop the link below.\n\n{tags}",
        "Amazon pet essential that owners swear by — {short_title}. {price_text}Trusted by thousands of pet parents with rave reviews. A practical pick that makes pet care genuinely easier.\nShop the link below.\n\n{tags}",
        "Top-selling Amazon pet find right now — {short_title}. {price_text}Pet owners keep coming back to this one. Quality product at a price that makes sense for everyday use.\nShop the link below.\n\n{tags}",
    ],
    "Clothing & Fashion": [
        "Affordable Amazon fashion find people are obsessed with — {short_title}. {price_text}One of the top-rated clothing picks on Amazon right now. Stylish, comfortable, and ships fast.\nShop the link below.\n\n{tags}",
        "Amazon wardrobe essential worth adding right now — {short_title}. {price_text}Thousands of shoppers love this one. Great quality at a price that works for any budget.\nShop the link below.\n\n{tags}",
        "Best-selling Amazon fashion find — {short_title}. {price_text}A versatile piece that works for everyday wear. High ratings, honest reviews, fast delivery.\nShop the link below.\n\n{tags}",
    ],
    "Baby & Nursery": [
        "Newborn must-have from Amazon that parents swear by — {short_title}. {price_text}A top-rated pick for new parents with thousands of five-star reviews. Makes a perfect baby shower gift too.\nShop the link below.\n\n{tags}",
        "Best baby shower gift idea on Amazon right now — {short_title}. {price_text}One of the best-selling baby products on Amazon. Trusted by thousands of new moms and dads who buy it again and again.\nShop the link below.\n\n{tags}",
        "Nursery essential from Amazon every new parent needs — {short_title}. {price_text}A practical, top-rated pick that actually makes early parenthood easier. High quality and great value.\nShop the link below.\n\n{tags}",
    ],
    "Sports & Fitness": [
        "Home gym essential from Amazon worth the investment — {short_title}. {price_text}One of the top-rated fitness products on Amazon right now. Level up your workouts without breaking the bank.\nShop the link below.\n\n{tags}",
        "Best workout gear find on Amazon — {short_title}. {price_text}Thousands of fitness lovers rate this one highly. Practical, durable, and worth adding to your routine.\nShop the link below.\n\n{tags}",
        "Amazon fitness find that delivers on its promise — {short_title}. {price_text}A top seller in Sports & Fitness for good reason. Reliable gear at a price that makes sense.\nShop the link below.\n\n{tags}",
    ],
    "Tools & Home Improvement": [
        "Best Amazon tool for DIY projects and home repairs — {short_title}. {price_text}A top-rated pick for homeowners and weekend warriors. Practical, reliable, and priced right.\nShop the link below.\n\n{tags}",
        "Home improvement essential from Amazon — {short_title}. {price_text}One of the highest-rated tools on Amazon with thousands of verified reviews. Every homeowner needs this in their kit.\nShop the link below.\n\n{tags}",
        "Amazon DIY find worth every penny — {short_title}. {price_text}Whether you're renovating or doing quick repairs, this tool delivers. Highly rated, fast shipping.\nShop the link below.\n\n{tags}",
    ],
    "Outdoor & Patio": [
        "Backyard upgrade find from Amazon people love — {short_title}. {price_text}One of the top-rated outdoor and patio products right now. Transform your outdoor space without spending a fortune.\nShop the link below.\n\n{tags}",
        "Amazon outdoor essential worth buying this season — {short_title}. {price_text}Thousands of happy customers love this patio and garden pick. Great quality at a price that works.\nShop the link below.\n\n{tags}",
        "Best patio find on Amazon right now — {short_title}. {price_text}A top seller in Outdoor & Patio for a reason. Perfect for upgrading your backyard or balcony.\nShop the link below.\n\n{tags}",
    ],
    "Electronics": [
        "Best Amazon tech find worth buying right now — {short_title}. {price_text}A top-rated gadget with thousands of verified reviews. Practical, well-designed, and genuinely worth the price.\nShop the link below.\n\n{tags}",
        "Amazon gadget that's worth adding to your setup — {short_title}. {price_text}One of the highest-rated electronics on Amazon right now. A real upgrade without the premium price tag.\nShop the link below.\n\n{tags}",
        "Smart home and tech find from Amazon — {short_title}. {price_text}Loved by thousands for its performance and value. A tech upgrade you won't regret.\nShop the link below.\n\n{tags}",
    ],
    "Health & Household": [
        "Wellness essential from Amazon that's actually worth trying — {short_title}. {price_text}A top-rated health and household pick with thousands of five-star reviews. Simple addition, real results.\nShop the link below.\n\n{tags}",
        "Amazon health find that lives up to the hype — {short_title}. {price_text}One of the best-selling wellness products on Amazon right now. Trusted by thousands for daily use.\nShop the link below.\n\n{tags}",
        "Daily wellness must-have from Amazon — {short_title}. {price_text}High ratings, quality ingredients, and a price that makes sense. A household essential worth keeping stocked.\nShop the link below.\n\n{tags}",
    ],
    "Office & Desk": [
        "Home office essential from Amazon people love — {short_title}. {price_text}A top-rated pick for anyone working from home or leveling up their desk setup. Practical and well-reviewed.\nShop the link below.\n\n{tags}",
        "Amazon desk setup find worth buying — {short_title}. {price_text}One of the highest-rated office products on Amazon. Boost your productivity with a workspace upgrade that actually delivers.\nShop the link below.\n\n{tags}",
        "Work from home essential from Amazon — {short_title}. {price_text}Thousands of remote workers love this pick. A desk upgrade that has a real impact on your daily routine.\nShop the link below.\n\n{tags}",
    ],
    "Toys & Games": [
        "Best Amazon toy for kids that parents actually recommend — {short_title}. {price_text}A top-rated pick with thousands of happy reviews. Perfect for birthdays, holidays, or just because.\nShop the link below.\n\n{tags}",
        "Kids gift idea from Amazon they'll actually use — {short_title}. {price_text}One of the best-selling toys on Amazon right now. Fun, engaging, and worth every penny.\nShop the link below.\n\n{tags}",
        "Top-rated Amazon toy and game find — {short_title}. {price_text}A family favorite with thousands of five-star reviews. Great for kids of all ages, ships fast.\nShop the link below.\n\n{tags}",
    ],
}

_DEFAULT_TEMPLATES = [
    "Top-rated Amazon find worth knowing about — {short_title}. {price_text}One of the best-selling products on Amazon right now with thousands of verified reviews.\nShop the link below.\n\n{tags}",
    "Amazon find worth buying — {short_title}. {price_text}Highly rated, practical, and priced right. A product that delivers on its promise every time.\nShop the link below.\n\n{tags}",
    "Best-selling Amazon essential — {short_title}. {price_text}Trusted by thousands of shoppers with top-rated reviews. Fast shipping and easy returns.\nShop the link below.\n\n{tags}",
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


def _build_pin_title(product: dict, template_key: str) -> str:
    """Build a Pinterest-optimised title: clean product name + category suffix."""
    short = _clean_title(product["title"])
    suffix = _TITLE_SUFFIX.get(template_key, "| Amazon Find")
    return f"{short} {suffix}"[:100]


def _build_description(product: dict, hashtags: list[str], template_key: str) -> str:
    price_text  = f"Only {product['price']}. " if product.get("price") else ""
    tags        = " ".join(hashtags[:5])          # max 5 per CLAUDE.md rules
    short_title = _clean_title(product["title"])
    variants    = _TEMPLATES.get(template_key, _DEFAULT_TEMPLATES)
    return random.choice(variants).format(
        short_title=short_title,
        price_text=price_text,
        tags=tags,
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

# ─────────────────────────────────────────────
#  pinterest_poster.py  —  Browser automation via Playwright
#  Logs into Pinterest with email+password and creates pins
#  through the web UI. No API approval needed.
# ─────────────────────────────────────────────

import os
import re
import time
import random
import tempfile
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PINTEREST_EMAIL    = os.environ.get("PINTEREST_EMAIL", "")
PINTEREST_PASSWORD = os.environ.get("PINTEREST_PASSWORD", "")
POST_DELAY_SECONDS = 8

# ─────────────────────────────────────────────────────────────────────────────
#  Description templates — 3 variants per category, picked randomly each post.
#  This prevents Pinterest from flagging pins as duplicate content.
# ─────────────────────────────────────────────────────────────────────────────
_TEMPLATES = {
    "Beauty & Personal Care": [
        "✨ {title} — one of Amazon Canada's best-selling beauty products right now. {price_text}Loved by thousands of shoppers across Canada. Shop with free shipping 👇\n\n{tags}",
        "Your next skincare obsession 💄 {title} is trending on Amazon Canada's best sellers. {price_text}Thousands of glowing reviews. Tap the link to shop!\n\n{tags}",
        "Beauty find of the day 🌟 {title} — top-rated in Beauty & Personal Care on Amazon Canada. {price_text}Perfect gift or everyday essential. Free delivery available 👇\n\n{tags}",
    ],
    "Home & Kitchen": [
        "Every home needs this ✨ {title} is Amazon Canada's best-selling home essential right now. {price_text}Upgrade your space for less — ships fast. Tap to shop 👇\n\n{tags}",
        "Home hack of the day 🏠 {title} — top-rated in Home & Kitchen on Amazon Canada. {price_text}Easy upgrade, big impact. Affordable and highly rated 👇\n\n{tags}",
        "Amazon Canada's top pick in Home & Kitchen ⭐ {title}. {price_text}Fast shipping, hassle-free returns. Tap to shop 👇\n\n{tags}",
    ],
    "Clothing & Fashion": [
        "Style find of the day 👗 {title} is trending in Clothing & Fashion on Amazon Canada. {price_text}Affordable fashion, fast shipping 👇\n\n{tags}",
        "Fashion hack alert 💅 {title} — one of Amazon Canada's best-selling fashion finds. {price_text}Look great for less. Prime shipping available 👇\n\n{tags}",
        "Your next wardrobe essential ✨ {title} is a top seller on Amazon Canada. {price_text}Tap to shop before it's gone 👇\n\n{tags}",
    ],
    "Sports & Fitness": [
        "💪 Level up your fitness routine! {title} is one of Amazon Canada's best-selling fitness products. {price_text}Perfect for home workouts or the gym 👇\n\n{tags}",
        "Your next fitness essential 🏃 {title} — top seller in Sports & Fitness on Amazon Canada. {price_text}High ratings, fast delivery. Crush your goals!\n\n{tags}",
        "Build your home gym for less 🔥 {title} is trending on Amazon Canada best sellers. {price_text}Trusted by fitness lovers across Canada 👇\n\n{tags}",
    ],
    "Tools & Home Improvement": [
        "🔧 DIY essential — {title} is one of Amazon Canada's best-selling tools. {price_text}Perfect for home projects. Highly rated, ships fast 👇\n\n{tags}",
        "Home upgrade hack 🏠 {title} — top-rated in Tools & Home Improvement on Amazon Canada. {price_text}Every homeowner needs this 👇\n\n{tags}",
        "Best-selling DIY tool on Amazon Canada ⭐ {title}. {price_text}Trusted by thousands of Canadians. Tap to shop 👇\n\n{tags}",
    ],
    "Electronics": [
        "⚡ Tech deal of the day — {title} is one of Amazon Canada's best-selling electronics. {price_text}Must-have gadget, top-rated. Tap to shop 👇\n\n{tags}",
        "Smart tech find 💻 {title} — currently a top seller in Electronics on Amazon Canada. {price_text}Great reviews, fast delivery 👇\n\n{tags}",
        "Upgrade your tech game 🔌 {title} is trending on Amazon Canada electronics best sellers. {price_text}Highly rated, ships fast!\n\n{tags}",
    ],
    "Health & Household": [
        "💚 Health essential everyone needs — {title} is a top-selling product on Amazon Canada. {price_text}Trusted by thousands. Ships fast 👇\n\n{tags}",
        "Daily wellness essential 🌿 {title} — best seller in Health & Household on Amazon Canada. {price_text}Simple upgrade, big impact 👇\n\n{tags}",
        "Amazon Canada's top pick for healthy living ✨ {title}. {price_text}Thousands of 5-star reviews. Fast delivery 👇\n\n{tags}",
    ],
    "Toys & Games": [
        "🎁 Perfect gift idea! {title} is one of Amazon Canada's best-selling toys. {price_text}Kids absolutely love it! Fast shipping 👇\n\n{tags}",
        "Top-rated toy on Amazon Canada 🌟 {title}. {price_text}A must-have for kids! Thousands of happy customers 👇\n\n{tags}",
        "Gift idea found 🎉 {title} — best selling in Toys & Games on Amazon Canada. {price_text}Fast shipping. Tap the link to order 👇\n\n{tags}",
    ],
}

_DEFAULT_TEMPLATES = [
    "🌟 {title} — one of Amazon Canada's best-selling products. {price_text}Highly rated, fast shipping 👇\n\n{tags}",
    "Top-rated Amazon Canada find ✨ {title}. {price_text}Loved by thousands. Free delivery available 👇\n\n{tags}",
    "Amazon Canada's best seller 🔥 {title}. {price_text}Fast shipping, easy returns 👇\n\n{tags}",
]


def _build_description(product: dict, hashtags: list[str], template_key: str) -> str:
    price_text = f"Only {product['price']}. " if product.get("price") else ""
    tags       = " ".join(hashtags[:15])
    title      = product["title"][:120]
    variants   = _TEMPLATES.get(template_key, _DEFAULT_TEMPLATES)
    return random.choice(variants).format(title=title, price_text=price_text, tags=tags)


def _download_image(url: str) -> str | None:
    """Download Amazon product image to a temp file. Returns file path or None."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 2000:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        print(f"    [!] Image download failed: {e}")
    return None


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

    # Email
    page.fill('input[name="id"]', PINTEREST_EMAIL)
    time.sleep(random.uniform(0.3, 0.7))

    # Password
    page.fill('input[name="password"]', PINTEREST_PASSWORD)
    time.sleep(random.uniform(0.3, 0.7))

    # Submit
    page.click('button[type="submit"]')

    try:
        # Wait until we land somewhere other than /login/
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


def _create_pin(page, product: dict, board_name: str, description: str) -> str | None:
    """Create one pin. Returns pin URL on success, None on failure."""
    image_path = _download_image(product["image_url"])
    if not image_path:
        print(f"  [x] Skipping — could not download image for: {product['title'][:50]}")
        return None

    try:
        page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        _dismiss_popups(page)

        # ── Upload image ──────────────────────────────────────────
        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(image_path)
        print(f"    Uploading image...")
        time.sleep(5)   # wait for Pinterest to process and show the editing panel
        _dismiss_popups(page)

        # ── Title ─────────────────────────────────────────────────
        _fill_field(page, [
            '[data-test-id="pin-draft-title"]',
            'input[placeholder*="title" i]',
            'input[aria-label*="title" i]',
        ], product["title"][:100])
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
        opened = _click_first(page, [
            '[data-test-id="board-dropdown-select-button"]',
            'button[aria-label*="board" i]',
            'button:has-text("Choose a board")',
            'button:has-text("Select")',
        ])

        if not opened:
            print(f"  [x] Could not open board selector for: {product['title'][:50]}")
            return None

        # Wait for "All boards" header — confirms the dropdown loaded
        try:
            page.get_by_text("All boards").first.wait_for(state="visible", timeout=8000)
        except PWTimeout:
            time.sleep(3)   # fallback wait

        # Type board name to filter the list
        try:
            search = page.locator('input[placeholder*="Search" i]').first
            if search.is_visible(timeout=2000):
                search.fill("")
                time.sleep(0.3)
                search.type(board_name, delay=80)
                time.sleep(2.0)
        except Exception:
            pass

        # Click the board by its visible text — most reliable after Pinterest's UI changes
        try:
            page.get_by_text(board_name, exact=True).first.click(timeout=5000)
            print(f"    Board '{board_name}' selected")
        except Exception:
            # Fallback: partial text match
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

        time.sleep(6)   # give Pinterest time to save and redirect

        # Layer 1: redirected directly to the pin page
        current_url = page.url
        if re.search(r'/pin/\d{10,}', current_url):
            return current_url

        # Layer 2: scan all links on the page for a real pin URL
        # Works for both www.pinterest.com and ca.pinterest.com
        try:
            for link in page.locator('a[href*="/pin/"]').all():
                href = link.get_attribute("href") or ""
                if re.search(r'/pin/\d{10,}', href):
                    if href.startswith("http"):
                        return href
                    return f"https://ca.pinterest.com{href}"
        except Exception:
            pass

        # Layer 3: wait a bit more and re-check URL (some redirects are slow)
        time.sleep(4)
        current_url = page.url
        if re.search(r'/pin/\d{10,}', current_url):
            return current_url

        # Layer 4: pin was posted but Pinterest didn't give us the URL
        # Mark clearly so the sheet is honest — not a fake pinterest.com URL
        return f"posted_no_url_{int(time.time())}"

    except Exception as e:
        print(f"  [x] Pin creation error: {e}")
        return None
    finally:
        Path(image_path).unlink(missing_ok=True)


def post_pins_for_category(
    products: list[dict],
    board_name: str,
    hashtags: list[str],
    template_key: str = "",
    limit: int = 10,
) -> list[dict]:
    """
    Posts up to `limit` products for one category using browser automation.
    Returns list of successfully posted products with pin_url set.
    """
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("  [x] PINTEREST_EMAIL or PINTEREST_PASSWORD env var not set — skipping")
        return []

    posted = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Login once per category batch
        if not _login(page):
            browser.close()
            return []

        for i, product in enumerate(products[:limit]):
            print(f"  [{i+1}/{min(len(products), limit)}] {product['title'][:60]}")
            description = _build_description(product, hashtags, template_key)

            pin_url = _create_pin(page, product, board_name, description)

            if pin_url:
                product["pin_url"] = pin_url
                posted.append(product)
                print(f"  [✓] Posted → {pin_url}")
            else:
                print(f"  [!] Failed — continuing to next product")

            if i < min(len(products), limit) - 1:
                time.sleep(POST_DELAY_SECONDS)

        browser.close()

    return posted

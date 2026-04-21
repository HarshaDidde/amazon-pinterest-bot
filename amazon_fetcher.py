# ─────────────────────────────────────────────
#  amazon_fetcher.py  (CRAWLER VERSION)
#  Crawls Amazon.ca Best Sellers pages
#  No API key needed — uses httpx + BeautifulSoup
# ─────────────────────────────────────────────

import re
import time
import random
import json
import httpx
from bs4 import BeautifulSoup

from config import AMAZON_ASSOCIATE_TAG

PRODUCTS_PER_CATEGORY = 10   # fallback default; callers pass n= to override

BASE_URL = "https://www.amazon.ca"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


def _get_headers() -> dict:
    return {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept-Language": "en-CA,en;q=0.9",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer":         "https://www.amazon.ca/",
        "DNT":             "1",
    }


def _build_affiliate_link(asin: str) -> str:
    return f"https://www.amazon.ca/dp/{asin}?tag={AMAZON_ASSOCIATE_TAG}"


def _fetch_page(url: str, retries: int = 3) -> BeautifulSoup | None:
    """Fetch a page with retries and random delay."""
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(2.5, 5.0))

            with httpx.Client(
                headers=_get_headers(),
                follow_redirects=True,
                timeout=30,
            ) as client:
                response = client.get(url)

            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            elif response.status_code == 503:
                wait = (attempt + 1) * 10
                print(f"    [!] 503 — waiting {wait}s before retry {attempt+1}/{retries}")
                time.sleep(wait)
            else:
                print(f"    [!] HTTP {response.status_code} for {url}")
                return None

        except Exception as e:
            print(f"    [!] Fetch error (attempt {attempt+1}): {e}")
            time.sleep(5)

    print(f"    [x] Failed after {retries} attempts: {url}")
    return None


def _extract_asin(url: str) -> str:
    for pattern in [r"/dp/([A-Z0-9]{10})", r"/product/([A-Z0-9]{10})", r"/gp/product/([A-Z0-9]{10})"]:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return ""


def _parse_bestsellers_page(soup: BeautifulSoup, category_name: str, limit: int = PRODUCTS_PER_CATEGORY) -> list[dict]:
    products = []

    items = soup.select("div.zg-grid-general-faceout, div[data-asin]")
    if not items:
        items = soup.select("li.zg-item-immersion, div.zg-item")

    for item in items:
        if len(products) >= limit:
            break
        try:
            # ASIN
            asin = item.get("data-asin", "")
            if not asin:
                a = item.select_one("a[href*='/dp/']")
                if a:
                    asin = _extract_asin(a.get("href", ""))
            if not asin or len(asin) != 10:
                continue

            # Title
            title = ""
            for sel in [
                "div._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y",
                "div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1",
                "span.zg-bdg-text", "span.a-size-small",
                "a.a-link-normal span", "img[alt]",
            ]:
                el = item.select_one(sel)
                if el:
                    title = el.get_text(strip=True) or el.get("alt", "")
                    if title:
                        break
            if not title:
                continue

            # Price
            price = ""
            for sel in ["span.p13n-sc-price", "span._cDEzb_p13n-sc-price_3mJ9Z",
                        "span.a-price-whole", "span.a-offscreen"]:
                el = item.select_one(sel)
                if el:
                    candidate = el.get_text(strip=True)
                    if "$" in candidate or re.search(r"\d", candidate):
                        price = candidate
                        break

            # Image
            image_url = ""
            img = item.select_one("img")
            if img:
                image_url = img.get("data-src") or img.get("src") or img.get("data-a-dynamic-image", "")
                if image_url and image_url.startswith("{"):
                    try:
                        img_dict = json.loads(image_url)
                        image_url = max(img_dict, key=lambda u: img_dict[u][0])
                    except Exception:
                        image_url = ""

            if not image_url or "loading" in image_url or image_url.endswith(".gif"):
                continue

            # Upgrade to high-res
            image_url = re.sub(r"\._[A-Z0-9_,]+_\.", "._AC_SL500_.", image_url)

            products.append({
                "asin":           asin,
                "title":          title,
                "price":          price,
                "image_url":      image_url,
                "affiliate_link": _build_affiliate_link(asin),
                "category":       category_name,
            })

        except Exception as e:
            print(f"    [!] Parse error: {e}")
            continue

    return products


def fetch_best_sellers(bestseller_url: str, category_name: str, n: int = None) -> list[dict]:
    """
    Crawls the given Amazon.ca Best Sellers URL.
    Returns up to n products (defaults to PRODUCTS_PER_CATEGORY).
    """
    limit = n or PRODUCTS_PER_CATEGORY
    print(f"    Crawling: {bestseller_url}  (want {limit})")
    soup = _fetch_page(bestseller_url)

    if not soup:
        print(f"    [x] Could not load page for '{category_name}'")
        return []

    products = _parse_bestsellers_page(soup, category_name, limit=limit)

    # Try page 2 if we still need more products
    if len(products) < limit:
        page2_url = bestseller_url.rstrip("/") + "/?pg=2"
        soup2 = _fetch_page(page2_url)
        if soup2:
            existing_asins = {p["asin"] for p in products}
            for p in _parse_bestsellers_page(soup2, category_name, limit=limit):
                if p["asin"] not in existing_asins:
                    products.append(p)
                if len(products) >= limit:
                    break

    products = products[:limit]
    print(f"    [+] Extracted {len(products)} products for '{category_name}'")
    return products

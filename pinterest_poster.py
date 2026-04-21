# ─────────────────────────────────────────────
#  pinterest_poster.py
#  Posts pins to Pinterest using API v5
#  Uses the product's Amazon image URL directly
# ─────────────────────────────────────────────

import os
import time
import random
import requests

from config import PINTEREST_ACCESS_TOKEN

PINTEREST_API_BASE  = "https://api.pinterest.com/v5"
POST_DELAY_SECONDS  = 5   # polite gap between posts (Pinterest rate-limit safety)

# ─────────────────────────────────────────────────────────────────────────────
#  Description templates
#
#  Each category has 3 variants — one is picked at random each post.
#  This prevents Pinterest from treating every pin as duplicate content.
#
#  Placeholders:  {title}      product title (already truncated)
#                 {price_text} e.g. "Only $24.99." or "" if no price
#                 {tags}       space-joined hashtags
# ─────────────────────────────────────────────────────────────────────────────

_TEMPLATES = {
    "Beauty & Personal Care": [
        "✨ {title} — one of Amazon Canada's best-selling beauty products right now. {price_text}Loved by thousands of shoppers across Canada. Shop with free shipping 👇\n\n{tags}",
        "Your next skincare obsession 💄 {title} is trending on Amazon Canada's best sellers. {price_text}Thousands of glowing reviews. Tap the link to shop before it sells out!\n\n{tags}",
        "Beauty find of the day 🌟 {title} — top-rated in Beauty & Personal Care on Amazon Canada. {price_text}Perfect gift or everyday essential. Free delivery available. Click to shop 👇\n\n{tags}",
    ],
    "Home & Kitchen": [
        "Every home needs this ✨ {title} is Amazon Canada's best-selling home essential right now. {price_text}Upgrade your space for less — ships fast. Tap to shop 👇\n\n{tags}",
        "Home hack of the day 🏠 {title} — top-rated in Home & Kitchen on Amazon Canada. {price_text}Easy upgrade, big impact. Affordable and highly rated. Shop now 👇\n\n{tags}",
        "Amazon Canada's top pick in Home & Kitchen ⭐ {title}. {price_text}Perfect for any home — fast shipping, hassle-free returns. Tap to shop 👇\n\n{tags}",
    ],
    "Clothing & Fashion": [
        "Style find of the day 👗 {title} is trending in Clothing & Fashion on Amazon Canada. {price_text}Affordable fashion, fast shipping. Tap to see this look 👇\n\n{tags}",
        "Fashion hack alert 💅 {title} — one of Amazon Canada's best-selling fashion finds. {price_text}Look great for less. Prime shipping available 👇\n\n{tags}",
        "Your next wardrobe essential ✨ {title} is a top seller on Amazon Canada right now. {price_text}Loved by Canadian shoppers. Tap to shop before it's gone 👇\n\n{tags}",
    ],
    "Sports & Fitness": [
        "💪 Level up your fitness routine! {title} is one of Amazon Canada's best-selling fitness products. {price_text}Perfect for home workouts or the gym. Free shipping 👇\n\n{tags}",
        "Your next fitness essential 🏃 {title} — top seller in Sports & Fitness on Amazon Canada. {price_text}High ratings, fast delivery. Crush your goals — tap to shop!\n\n{tags}",
        "Build your home gym for less 🔥 {title} is trending on Amazon Canada best sellers. {price_text}Trusted by fitness lovers across Canada. Shop now 👇\n\n{tags}",
    ],
    "Tools & Home Improvement": [
        "🔧 DIY essential — {title} is one of Amazon Canada's best-selling tools right now. {price_text}Perfect for home projects. Highly rated, ships fast. Tap to shop 👇\n\n{tags}",
        "Home upgrade hack 🏠 {title} — top-rated in Tools & Home Improvement on Amazon Canada. {price_text}Every homeowner needs this. Fast shipping available 👇\n\n{tags}",
        "Best-selling DIY tool on Amazon Canada ⭐ {title}. {price_text}Trusted by thousands of Canadians. Tap to shop now 👇\n\n{tags}",
    ],
    "Electronics": [
        "⚡ Tech deal of the day — {title} is one of Amazon Canada's best-selling electronics. {price_text}Must-have gadget, top-rated by thousands. Tap to shop 👇\n\n{tags}",
        "Smart tech find 💻 {title} — currently a top seller in Electronics on Amazon Canada. {price_text}Great reviews, fast delivery. Don't sleep on this one 👇\n\n{tags}",
        "Upgrade your tech game 🔌 {title} is trending on Amazon Canada electronics best sellers. {price_text}Highly rated, ships fast. Tap the link to shop now!\n\n{tags}",
    ],
    "Health & Household": [
        "💚 Health essential everyone needs — {title} is a top-selling product on Amazon Canada. {price_text}Trusted by thousands. Ships fast 👇\n\n{tags}",
        "Daily wellness essential 🌿 {title} — best seller in Health & Household on Amazon Canada. {price_text}Simple upgrade, big impact. Tap to shop now 👇\n\n{tags}",
        "Amazon Canada's top pick for healthy living ✨ {title}. {price_text}Thousands of 5-star reviews. Fast delivery across Canada. Click to shop 👇\n\n{tags}",
    ],
    "Toys & Games": [
        "🎁 Perfect gift idea! {title} is one of Amazon Canada's best-selling toys right now. {price_text}Kids absolutely love it! Fast shipping, great reviews. Tap to shop 👇\n\n{tags}",
        "Top-rated toy on Amazon Canada 🌟 {title}. {price_text}A must-have for kids! Thousands of happy customers. Free delivery available. Shop now 👇\n\n{tags}",
        "Gift idea found 🎉 {title} — best selling in Toys & Games on Amazon Canada. {price_text}Perfect present, fast shipping. Tap the link to order 👇\n\n{tags}",
    ],
}

_DEFAULT_TEMPLATES = [
    "🌟 {title} — one of Amazon Canada's best-selling products right now. {price_text}Highly rated, fast shipping. Tap to shop 👇\n\n{tags}",
    "Top-rated Amazon Canada find ✨ {title}. {price_text}Loved by thousands of shoppers. Free delivery available. Shop now 👇\n\n{tags}",
    "Amazon Canada's best seller 🔥 {title}. {price_text}See why everyone's buying this! Fast shipping, easy returns 👇\n\n{tags}",
]


def _headers() -> dict:
    token = os.environ.get("PINTEREST_ACCESS_TOKEN") or PINTEREST_ACCESS_TOKEN
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }


def _build_description(product: dict, hashtags: list[str], template_key: str) -> str:
    price_text = f"Only {product['price']}. " if product.get("price") else ""
    tags       = " ".join(hashtags[:15])   # Pinterest cap is ~20 hashtags
    title      = product["title"][:120]

    variants = _TEMPLATES.get(template_key, _DEFAULT_TEMPLATES)
    template = random.choice(variants)

    return template.format(title=title, price_text=price_text, tags=tags)


def post_pin(product: dict, board_id: str, hashtags: list[str], template_key: str = "") -> str | None:
    """
    Creates a Pinterest pin for the given product.
    Returns the pin URL on success, None on failure.
    """
    title       = product["title"][:100]   # Pinterest title hard limit
    description = _build_description(product, hashtags, template_key)
    image_url   = product["image_url"]
    link        = product["affiliate_link"]

    payload = {
        "board_id":    board_id,
        "title":       title,
        "description": description,
        "link":        link,
        "media_source": {
            "source_type": "image_url",
            "url":          image_url,
        },
    }

    try:
        response = requests.post(
            f"{PINTEREST_API_BASE}/pins",
            headers=_headers(),
            json=payload,
            timeout=30,
        )

        if response.status_code in (200, 201):
            pin_id  = response.json().get("id", "")
            pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
            print(f"  [✓] Posted: {product['title'][:60]}")
            print(f"       → {pin_url}")
            return pin_url

        else:
            print(f"  [x] Pinterest {response.status_code}: {response.text[:200]}")
            return None

    except requests.RequestException as e:
        print(f"  [x] Request failed: {e}")
        return None


def post_pins_for_category(
    products: list[dict],
    board_id: str,
    hashtags: list[str],
    template_key: str = "",
    limit: int = 10,
) -> list[dict]:
    """
    Posts up to `limit` products for a category.
    Returns list of successfully posted products (with pin_url set).
    """
    posted = []

    for i, product in enumerate(products[:limit]):
        print(f"  [{i+1}/{min(len(products), limit)}] {product['title'][:60]}")

        pin_url = post_pin(product, board_id, hashtags, template_key)

        if pin_url:
            product["pin_url"] = pin_url
            posted.append(product)

        if i < min(len(products), limit) - 1:
            time.sleep(POST_DELAY_SECONDS)

    return posted

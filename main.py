# ─────────────────────────────────────────────
#  main.py  —  Orchestrator
#  Daily cycle:
#    1. Load deduplication list from Google Sheets
#    2. Apply seasonal boost to daily_posts per category
#    3. Crawl Amazon.com best sellers per category
#    4. Post new products as Pinterest pins (revenue-priority order)
#    5. Log results back to Google Sheet
#    6. Guarantee: if 0 pins posted, retry top-priority category once
# ─────────────────────────────────────────────

import math
from datetime import datetime

from config import CATEGORIES, SEASONAL_BOOSTS, MAX_PINS_PER_RUN
from amazon_fetcher import fetch_best_sellers
from pinterest_poster import post_pins_for_category, pinterest_session
from sheet_logger import get_posted_asins, log_posted_product


def _seasonal_posts(category: dict, month: int) -> int:
    """Return the seasonally adjusted daily_posts for a category."""
    base       = category["daily_posts"]
    multiplier = SEASONAL_BOOSTS.get(month, {}).get(category["name"], 1.0)
    return max(1, math.ceil(base * multiplier))


def _category_summary(name: str, fetched: int, skipped: int, posted: int):
    status = f"+{posted} posted" if posted else "0 posted"
    print(f"  {name:<28}  fetched={fetched}  skipped={skipped}  {status}")


def run():
    now   = datetime.now()
    month = now.month

    print("=" * 65)
    print(f"  Amazon.com → Pinterest Bot  |  {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Seasonal month: {now.strftime('%B')}  |  Max pins this run: {MAX_PINS_PER_RUN}")
    print("=" * 65)

    # ── Step 1: Load deduplication list ──────────────────────────────
    print("\n[1] Loading deduplication list from Google Sheets...")
    try:
        posted_asins = get_posted_asins()
        print(f"    {len(posted_asins)} ASINs in cooldown window — will skip these.")
    except Exception as e:
        print(f"    [!] Could not load sheet ({e}). Proceeding without deduplication.")
        posted_asins = set()

    # ── Step 2: Process categories in revenue-priority order ─────────
    print(f"\n[2] Processing {len(CATEGORIES)} categories (revenue-priority order)...\n")

    total_posted = 0
    run_results  = []   # (category_name, posted_count)

    with pinterest_session() as page:
        for cat in CATEGORIES:
            if total_posted >= MAX_PINS_PER_RUN:
                print(f"  [!] Reached MAX_PINS_PER_RUN ({MAX_PINS_PER_RUN}) — stopping early.")
                break

            limit = _seasonal_posts(cat, month)
            remaining_budget = MAX_PINS_PER_RUN - total_posted
            limit = min(limit, remaining_budget)

            print(f"[→] {cat['name']}  (target: {limit} pins, commission: {cat['commission_rate']}%)")

            # Crawl Amazon.com — fetch extra to cover cooldown skips and dupes
            fetch_n  = limit + 15
            products = fetch_best_sellers(cat["bestseller_url"], cat["name"], n=fetch_n)

            if not products:
                print("    No products fetched — skipping.\n")
                run_results.append((cat["name"], 0))
                continue

            # Deduplicate: remove already-posted ASINs, within-batch ASIN dupes,
            # and title-prefix dupes (catches same product with different variant ASINs)
            seen_asins  = set(posted_asins)
            seen_titles = set()
            new_products = []
            for p in products:
                title_key = p["title"].lower()[:45]
                if p["asin"] not in seen_asins and title_key not in seen_titles:
                    new_products.append(p)
                    seen_asins.add(p["asin"])
                    seen_titles.add(title_key)
            skipped = len(products) - len(new_products)

            if not new_products:
                print("    All products in cooldown — skipping.\n")
                run_results.append((cat["name"], 0))
                continue

            print(f"    {len(new_products)} new  |  {skipped} skipped (cooldown)")
            print(f"    Posting up to {limit} pins...")

            # Tag each product with the category's commission rate for sheet logging
            for p in new_products:
                p["commission_rate"] = cat["commission_rate"]

            # Post to Pinterest — reuse the shared logged-in session
            successfully_posted = post_pins_for_category(
                products     = new_products,
                board_name   = cat["board_name"],
                hashtags     = cat["hashtags"],
                template_key = cat["description_template"],
                limit        = limit,
                page         = page,
            )

            # Log to Google Sheet
            for product in successfully_posted:
                try:
                    log_posted_product(product, product.get("pin_url", ""))
                    posted_asins.add(product["asin"])
                except Exception as e:
                    print(f"    [!] Sheet log failed for {product['asin']}: {e}")

            cat_count     = len(successfully_posted)
            total_posted += cat_count
            run_results.append((cat["name"], cat_count))
            print()

        # ── Step 3: Guarantee at least 1 pin ─────────────────────────────
        if total_posted == 0:
            print("[!] Zero pins posted in main run. Retrying top-priority category...")
            top_cat = CATEGORIES[0]
            products = fetch_best_sellers(top_cat["bestseller_url"], top_cat["name"], n=10)
            if products:
                # Skip cooldown filter on retry — something must be posted
                print(f"    Bypassing cooldown filter for retry on '{top_cat['name']}'")
                retry_posted = post_pins_for_category(
                    products     = products[:1],
                    board_name   = top_cat["board_name"],
                    hashtags     = top_cat["hashtags"],
                    template_key = top_cat["description_template"],
                    limit        = 1,
                    page         = page,
                )
                for product in retry_posted:
                    try:
                        log_posted_product(product, product.get("pin_url", ""))
                    except Exception:
                        pass
                total_posted = len(retry_posted)
            else:
                print("    [x] Retry also failed to fetch products. Check Amazon crawler.")

    # ── Summary ───────────────────────────────────────────────────────
    print("=" * 65)
    print(f"  Run complete  |  {total_posted} pins posted  |  {now.strftime('%Y-%m-%d %H:%M')}")
    print()
    print("  Per-category breakdown:")
    for name, count in run_results:
        bar = "█" * count
        print(f"    {name:<28}  {bar} ({count})")
    print("=" * 65)

    return total_posted


if __name__ == "__main__":
    run()

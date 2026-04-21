# ─────────────────────────────────────────────
#  config.py  —  All settings in one place
#  Target: Amazon.ca (Canada)
# ─────────────────────────────────────────────

import os

# ── Amazon Associates (Canada) ────────────────
AMAZON_ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG", "hd217-20")

# ── Pinterest ─────────────────────────────────
PINTEREST_ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "YOUR_PINTEREST_ACCESS_TOKEN")

# ── Google Sheets ─────────────────────────────
GOOGLE_SHEET_ID         = os.environ.get("GOOGLE_SHEET_ID", "YOUR_GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = "google_credentials.json"

# ── Bot behaviour ─────────────────────────────
REPOST_COOLDOWN_DAYS = 28     # days before a product can be reposted
MAX_PINS_PER_RUN     = 30     # hard cap on total pins per run (Pinterest safety)

# ─────────────────────────────────────────────────────────────────────────────
#  Category config
#
#  Revenue priority = commission_rate × pinterest_search_volume (1–10 scale)
#  This drives the daily_posts allocation — higher score gets more posts.
#
#  commission_rate    : Amazon.ca affiliate commission % for this category
#  daily_posts        : max pins to post per daily run (revenue-weighted)
#  description_template: key into _DESCRIPTION_TEMPLATES in pinterest_poster.py
#  bestseller_url     : Amazon.ca Best Sellers page for this category
#  board_id           : Your Pinterest board ID (from board Settings URL)
#  hashtags           : used in pin description (Pinterest allows up to 20)
#
#  Revenue score order (commission × volume):
#    1. Beauty        8.0% × 9  = 72  → 5 posts/day
#    2. Home&Kitchen  4.5% × 9  = 40  → 5 posts/day
#    3. Fashion       4.0% × 8  = 32  → 4 posts/day
#    4. Sports        4.5% × 7  = 31  → 4 posts/day
#    5. Tools         5.5% × 5  = 27  → 3 posts/day
#    6. Electronics   4.0% × 6  = 24  → 3 posts/day
#    7. Health        2.5% × 8  = 20  → 3 posts/day
#    8. Toys          3.0% × 5  = 15  → 2 posts/day
#  ──────────────────────────────────────────────
#  Total per day: 29 pins  (safe for Pinterest algorithm)
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIES = [
    {
        "name":                 "Beauty & Personal Care",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/beauty",
        "board_name":           "Beauty & Personal Care",
        "commission_rate":      8.0,
        "daily_posts":          5,
        "description_template": "Beauty & Personal Care",
        "hashtags": [
            "#AmazonBeauty", "#SkincareFinds", "#BeautyHacks",
            "#GlowUp", "#AffordableBeauty", "#SkincareRoutine",
            "#AmazonCA", "#BeautyFinds", "#MakeupFinds", "#SkincareTips",
        ],
    },
    {
        "name":                 "Home & Kitchen",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/kitchen",
        "board_name":           "Home & Kitchen",
        "commission_rate":      4.5,
        "daily_posts":          5,
        "description_template": "Home & Kitchen",
        "hashtags": [
            "#HomeDecor", "#KitchenFinds", "#HomeEssentials",
            "#AmazonFinds", "#AmazonCA", "#HomeHacks",
            "#KitchenOrganization", "#HomeShopping", "#InteriorDesign", "#HomeInspo",
        ],
    },
    {
        "name":                 "Clothing & Fashion",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/fashion",
        "board_name":           "Clothing & Fashion",
        "commission_rate":      4.0,
        "daily_posts":          4,
        "description_template": "Clothing & Fashion",
        "hashtags": [
            "#AmazonFashion", "#FashionFinds", "#OOTD",
            "#StyleInspo", "#AffordableFashion", "#AmazonCA",
            "#FashionHacks", "#WardrobeEssentials", "#StyleFinds", "#FashionDeals",
        ],
    },
    {
        "name":                 "Sports & Fitness",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/exercise-and-fitness",
        "board_name":           "Sports & Fitness",
        "commission_rate":      4.5,
        "daily_posts":          4,
        "description_template": "Sports & Fitness",
        "hashtags": [
            "#FitnessFinds", "#WorkoutGear", "#HomeGym",
            "#FitnessMotivation", "#AmazonFitness", "#AmazonCA",
            "#WorkoutEssentials", "#GymFinds", "#FitLife", "#SportEssentials",
        ],
    },
    {
        "name":                 "Tools & Home Improvement",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/hi",
        "board_name":           "Tools & Home Improvement",
        "commission_rate":      5.5,
        "daily_posts":          3,
        "description_template": "Tools & Home Improvement",
        "hashtags": [
            "#HomeImprovement", "#DIYFinds", "#ToolsAndHardware",
            "#AmazonTools", "#AmazonCA", "#DIYProjects",
            "#HomeRenovation", "#DIYHome", "#HomeRepair", "#FixItUp",
        ],
    },
    {
        "name":                 "Electronics",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/electronics",
        "board_name":           "Electronics",
        "commission_rate":      4.0,
        "daily_posts":          3,
        "description_template": "Electronics",
        "hashtags": [
            "#TechFinds", "#Gadgets", "#Electronics",
            "#AmazonTech", "#AmazonCA", "#TechDeals",
            "#SmartHome", "#GadgetFinds", "#TechLife", "#MustHaveTech",
        ],
    },
    {
        "name":                 "Health & Household",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/hpc",
        "board_name":           "Health & Household",
        "commission_rate":      2.5,
        "daily_posts":          3,
        "description_template": "Health & Household",
        "hashtags": [
            "#HealthyLiving", "#WellnessFinds", "#AmazonHealth",
            "#SelfCare", "#AmazonCA", "#HealthTips",
            "#WellnessRoutine", "#HealthEssentials", "#CleanLiving", "#NaturalHealth",
        ],
    },
    {
        "name":                 "Toys & Games",
        "bestseller_url":       "https://www.amazon.ca/gp/bestsellers/toys",
        "board_name":           "Toys & Games",
        "commission_rate":      3.0,
        "daily_posts":          2,
        "description_template": "Toys & Games",
        "hashtags": [
            "#ToysAndGames", "#KidsFinds", "#GiftIdeas",
            "#AmazonToys", "#AmazonCA", "#KidsGifts",
            "#FamilyFinds", "#ToyFinds", "#BestToys", "#KidApproved",
        ],
    },
]

# ── Seasonal boosts ────────────────────────────────────────────────────────────
# Applied in main.py to temporarily increase daily_posts for relevant categories.
# Multiplier is floored at 1 post minimum and capped by MAX_PINS_PER_RUN.
SEASONAL_BOOSTS = {
    1:  {"Sports & Fitness": 2.0, "Health & Household": 1.5},              # Jan: New Year resolutions
    2:  {"Beauty & Personal Care": 1.5, "Clothing & Fashion": 1.5},        # Feb: Valentine's Day
    3:  {"Sports & Fitness": 1.5, "Home & Kitchen": 1.3},                  # Mar: Spring cleaning
    4:  {"Tools & Home Improvement": 1.5, "Home & Kitchen": 1.3},          # Apr: Spring projects
    5:  {"Home & Kitchen": 1.3, "Clothing & Fashion": 1.3},                # May
    6:  {"Sports & Fitness": 1.5, "Clothing & Fashion": 1.3},              # Jun: Summer
    7:  {"Sports & Fitness": 1.5, "Electronics": 1.3},                     # Jul: Summer tech
    8:  {"Electronics": 1.5, "Home & Kitchen": 1.2},                       # Aug: Back to school
    9:  {"Home & Kitchen": 1.3, "Tools & Home Improvement": 1.5},          # Sep: Fall home projects
    10: {"Toys & Games": 1.5, "Home & Kitchen": 1.3},                      # Oct: Pre-holiday
    11: {"Toys & Games": 2.0, "Electronics": 2.0, "Beauty & Personal Care": 1.5},  # Nov: Black Friday
    12: {"Toys & Games": 2.0, "Electronics": 1.8, "Beauty & Personal Care": 1.5},  # Dec: Holiday gifts
}

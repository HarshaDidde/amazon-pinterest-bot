# ─────────────────────────────────────────────
#  config.py  —  All settings in one place
#  Target: Amazon.com (United States)
# ─────────────────────────────────────────────

import os

# ── Amazon Associates (United States) ────────
AMAZON_ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG", "hd2170e-20")

# ── Pinterest ─────────────────────────────────
PINTEREST_ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "YOUR_PINTEREST_ACCESS_TOKEN")

# ── Google Sheets ─────────────────────────────
GOOGLE_SHEET_ID         = os.environ.get("GOOGLE_SHEET_ID", "YOUR_GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = "google_credentials.json"

# ── Bot behaviour ─────────────────────────────
REPOST_COOLDOWN_DAYS = 28     # days before a product can be reposted
MAX_PINS_PER_RUN     = 15     # new US account: start conservative, ramp after 2 weeks

# ─────────────────────────────────────────────────────────────────────────────
#  Category config
#
#  Revenue priority = commission_rate × pinterest_search_volume (1–10 scale)
#  This drives the daily_posts allocation — higher score gets more posts.
#
#  commission_rate    : Amazon.com affiliate commission % for this category
#  daily_posts        : max pins to post per daily run (revenue-weighted)
#  description_template: key into _TEMPLATES in pinterest_poster.py
#  bestseller_url     : Amazon.com Best Sellers page for this category
#  hashtags           : max 5 used in pin description (per CLAUDE.md rules)
#
#  Revenue score order (commission × volume):
#    1.  Beauty          8.0% × 9  = 72  → 4 posts/day
#    2.  Home & Kitchen  4.5% × 9  = 40  → 4 posts/day
#    3.  Arts & Crafts   4.5% × 8  = 36  → 3 posts/day  (Pinterest-native)
#    4.  Pet Supplies    4.0% × 8  = 32  → 3 posts/day  (Pinterest-native)
#    5.  Fashion         4.0% × 8  = 32  → 3 posts/day
#    6.  Baby & Nursery  4.5% × 7  = 31  → 3 posts/day
#    7.  Sports          4.5% × 7  = 31  → 3 posts/day
#    8.  Tools           5.5% × 5  = 27  → 2 posts/day
#    9.  Outdoor & Patio 4.5% × 6  = 27  → 2 posts/day
#    10. Electronics     4.0% × 6  = 24  → 2 posts/day
#    11. Health          2.5% × 8  = 20  → 2 posts/day
#    12. Office & Desk   4.0% × 5  = 20  → 2 posts/day
#    13. Toys            3.0% × 5  = 15  → 1 post/day
#  ──────────────────────────────────────────────
#  Total per run: 34 pins → capped at 30 by MAX_PINS_PER_RUN
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIES = [
    {
        "name":                 "Beauty & Personal Care",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/beauty",
        "board_name":           "Beauty & Personal Care",
        "commission_rate":      8.0,
        "daily_posts":          4,
        "description_template": "Beauty & Personal Care",
        "hashtags": [
            "#AmazonBeauty", "#SkincareFinds", "#BeautyFinds",
            "#GlowUp", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Home & Kitchen",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/kitchen",
        "board_name":           "Home & Kitchen",
        "commission_rate":      4.5,
        "daily_posts":          4,
        "description_template": "Home & Kitchen",
        "hashtags": [
            "#HomeDecor", "#KitchenFinds", "#HomeEssentials",
            "#AmazonHome", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Arts & Crafts",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/arts-and-crafts",
        "board_name":           "Arts & Crafts",
        "commission_rate":      4.5,
        "daily_posts":          3,
        "description_template": "Arts & Crafts",
        "hashtags": [
            "#CraftSupplies", "#ArtFinds", "#DIYCrafts",
            "#CraftIdeas", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Pet Supplies",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/pet-supplies",
        "board_name":           "Pet Supplies",
        "commission_rate":      4.0,
        "daily_posts":          3,
        "description_template": "Pet Supplies",
        "hashtags": [
            "#PetFinds", "#DogFinds", "#CatFinds",
            "#PetEssentials", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Clothing & Fashion",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/fashion",
        "board_name":           "Clothing & Fashion",
        "commission_rate":      4.0,
        "daily_posts":          3,
        "description_template": "Clothing & Fashion",
        "hashtags": [
            "#AmazonFashion", "#FashionFinds", "#OOTD",
            "#AffordableStyle", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Baby & Nursery",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/baby-products",
        "board_name":           "Baby & Nursery",
        "commission_rate":      4.5,
        "daily_posts":          3,
        "description_template": "Baby & Nursery",
        "hashtags": [
            "#BabyFinds", "#NurseryIdeas", "#BabyEssentials",
            "#NewMom", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Sports & Fitness",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/sporting-goods",
        "board_name":           "Sports & Fitness",
        "commission_rate":      4.5,
        "daily_posts":          3,
        "description_template": "Sports & Fitness",
        "hashtags": [
            "#FitnessFinds", "#WorkoutGear", "#HomeGym",
            "#FitnessMotivation", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Tools & Home Improvement",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/hi",
        "board_name":           "Tools & Home Improvement",
        "commission_rate":      5.5,
        "daily_posts":          2,
        "description_template": "Tools & Home Improvement",
        "hashtags": [
            "#HomeImprovement", "#DIYFinds", "#AmazonTools",
            "#DIYProjects", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Outdoor & Patio",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/lawn-garden",
        "board_name":           "Outdoor & Patio",
        "commission_rate":      4.5,
        "daily_posts":          2,
        "description_template": "Outdoor & Patio",
        "hashtags": [
            "#OutdoorFinds", "#PatioDecor", "#BackyardGoals",
            "#GardenFinds", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Electronics",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/electronics",
        "board_name":           "Electronics",
        "commission_rate":      4.0,
        "daily_posts":          2,
        "description_template": "Electronics",
        "hashtags": [
            "#TechFinds", "#Gadgets", "#SmartHome",
            "#TechDeals", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Health & Household",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/hpc",
        "board_name":           "Health & Household",
        "commission_rate":      2.5,
        "daily_posts":          2,
        "description_template": "Health & Household",
        "hashtags": [
            "#HealthyLiving", "#WellnessFinds", "#SelfCare",
            "#HealthEssentials", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Office & Desk",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/office-products",
        "board_name":           "Office & Desk",
        "commission_rate":      4.0,
        "daily_posts":          2,
        "description_template": "Office & Desk",
        "hashtags": [
            "#OfficeFinds", "#DeskSetup", "#HomeOffice",
            "#WorkFromHome", "#AmazonFinds",
        ],
    },
    {
        "name":                 "Toys & Games",
        "bestseller_url":       "https://www.amazon.com/gp/bestsellers/toys-and-games",
        "board_name":           "Toys & Games",
        "commission_rate":      3.0,
        "daily_posts":          1,
        "description_template": "Toys & Games",
        "hashtags": [
            "#ToysAndGames", "#GiftIdeasForKids", "#KidsFinds",
            "#BestToys", "#AmazonFinds",
        ],
    },
]

# ── Seasonal boosts ────────────────────────────────────────────────────────────
# Applied in main.py to temporarily increase daily_posts for relevant categories.
# Multiplier is floored at 1 post minimum and capped by MAX_PINS_PER_RUN.
SEASONAL_BOOSTS = {
    1:  {"Sports & Fitness": 2.0, "Health & Household": 1.5, "Office & Desk": 1.5},           # Jan: New Year resolutions + productivity
    2:  {"Beauty & Personal Care": 1.5, "Clothing & Fashion": 1.5, "Baby & Nursery": 1.3},    # Feb: Valentine's Day
    3:  {"Sports & Fitness": 1.5, "Home & Kitchen": 1.3, "Outdoor & Patio": 1.5},             # Mar: Spring cleaning + outdoor prep
    4:  {"Tools & Home Improvement": 1.5, "Outdoor & Patio": 2.0, "Home & Kitchen": 1.3},     # Apr: Peak outdoor + spring projects
    5:  {"Outdoor & Patio": 2.0, "Home & Kitchen": 1.3, "Baby & Nursery": 1.3,
         "Pet Supplies": 1.3, "Clothing & Fashion": 1.3},                                      # May: Outdoor peak + Mother's Day
    6:  {"Sports & Fitness": 1.5, "Outdoor & Patio": 1.5, "Pet Supplies": 1.5},               # Jun: Summer
    7:  {"Sports & Fitness": 1.5, "Electronics": 1.3, "Pet Supplies": 1.5},                   # Jul: Summer tech + outdoor pets
    8:  {"Electronics": 1.5, "Home & Kitchen": 1.2, "Office & Desk": 1.5},                    # Aug: Back to school
    9:  {"Home & Kitchen": 1.3, "Tools & Home Improvement": 1.5,
         "Arts & Crafts": 1.5, "Office & Desk": 1.5},                                         # Sep: Fall home projects + back to work
    10: {"Toys & Games": 1.5, "Home & Kitchen": 1.3, "Arts & Crafts": 1.5},                   # Oct: Pre-holiday + Halloween crafts
    11: {"Toys & Games": 2.0, "Electronics": 2.0, "Beauty & Personal Care": 1.5,
         "Arts & Crafts": 1.5, "Pet Supplies": 1.5},                                          # Nov: Black Friday
    12: {"Toys & Games": 2.0, "Electronics": 1.8, "Beauty & Personal Care": 1.5,
         "Baby & Nursery": 1.3, "Pet Supplies": 1.5},                                         # Dec: Holiday gifts
}

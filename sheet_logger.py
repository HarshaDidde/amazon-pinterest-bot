# ─────────────────────────────────────────────
#  sheet_logger.py
#  Reads & writes to Google Sheets
#  Used for deduplication and run history
# ─────────────────────────────────────────────

import os
import json
import tempfile
from datetime import datetime, timedelta

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE, REPOST_COOLDOWN_DAYS

SHEET_NAME = "PostedProducts"
HEADERS    = ["ASIN", "Title", "Category", "CommissionRate", "DatePosted", "PinURL", "AffiliateLink"]

_client = None
_sheet  = None


def _get_sheet():
    global _client, _sheet
    if _sheet:
        return _sheet

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_source = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_source:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(creds_source)
        tmp.flush()
        creds = ServiceAccountCredentials.from_json_keyfile_name(tmp.name, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_CREDENTIALS_FILE, scope
        )

    _client = gspread.authorize(creds)
    spreadsheet = _client.open_by_key(GOOGLE_SHEET_ID)

    try:
        _sheet = spreadsheet.worksheet(SHEET_NAME)
        # Migrate: add CommissionRate column if it was created without it
        existing_headers = _sheet.row_values(1)
        if "CommissionRate" not in existing_headers and existing_headers:
            insert_col = len(existing_headers) + 1
            _sheet.update_cell(1, 4, "CommissionRate")
    except gspread.WorksheetNotFound:
        _sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=10000, cols=len(HEADERS))
        _sheet.append_row(HEADERS)

    return _sheet


def get_posted_asins() -> set[str]:
    """
    Returns the set of ASINs posted within the cooldown window.
    Products outside the window are eligible for reposting.
    """
    sheet   = _get_sheet()
    records = sheet.get_all_records()
    cutoff  = datetime.now() - timedelta(days=REPOST_COOLDOWN_DAYS)

    recent_asins = set()
    for row in records:
        try:
            date_posted = datetime.strptime(str(row["DatePosted"]), "%Y-%m-%d")
            if date_posted >= cutoff:
                recent_asins.add(str(row["ASIN"]))
        except (ValueError, KeyError):
            continue

    return recent_asins


def log_posted_product(product: dict, pin_url: str):
    """Append a row to the tracking sheet after a successful pin post."""
    sheet = _get_sheet()
    sheet.append_row([
        product["asin"],
        product["title"][:200],
        product["category"],
        product.get("commission_rate", ""),
        datetime.now().strftime("%Y-%m-%d"),
        pin_url,
        product["affiliate_link"],
    ])
    print(f"  [✓] Logged: {product['asin']} — {product['title'][:55]}")

# Amazon.ca → Pinterest Affiliate Bot

Crawls Amazon.ca Best Sellers, posts products as organic Pinterest pins with your affiliate link, and logs everything to Google Sheets to avoid duplicates. Runs automatically every Sunday via GitHub Actions.

---

## Setup

### 1. Amazon.ca Associate Tag

Sign up at [associates.amazon.ca](https://associates.amazon.ca) if you haven't already. Once approved, your tag looks like `yourname-20`. Add it to `config.py`:

```python
AMAZON_ASSOCIATE_TAG = "yourname-20"
```

---

### 2. Pinterest Access Token

1. Go to [developers.pinterest.com](https://developers.pinterest.com) and create an app
2. Under your app, generate an access token with these scopes enabled:
   - `boards:read`
   - `pins:write`
   - `pins:read`
3. Add it to `config.py`:

```python
PINTEREST_ACCESS_TOKEN = "your_token_here"
```

**Note:** Tokens expire periodically. If pins stop posting, regenerate and update.

---

### 3. Pinterest Board IDs

Create one Pinterest board per category (e.g. "Amazon Finds — Home & Kitchen"). To find a board's ID:

1. Open the board → click the pencil/Settings icon
2. The numeric ID is in the URL:
   `pinterest.com/yourname/board-name/**123456789012345678**`

Add each board ID to the matching category in `config.py`.

---

### 4. Google Sheets (for deduplication)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create a project
2. Enable **Google Sheets API** and **Google Drive API**
3. Go to **IAM → Service Accounts** → create one → download the JSON key
4. Create a blank Google Sheet at [sheets.google.com](https://sheets.google.com)
5. Share the sheet with the service account email from the JSON file (give it Editor access)
6. Copy the Sheet ID from the URL:
   `docs.google.com/spreadsheets/d/**YOUR_SHEET_ID**/edit`
7. Add to `config.py`:

```python
GOOGLE_SHEET_ID = "your_sheet_id_here"
```

---

### 5. GitHub Secrets

Push the project to a GitHub repo, then go to **Settings → Secrets and variables → Actions** and add these secrets:

| Secret | Value |
|---|---|
| `AMAZON_ASSOCIATE_TAG` | e.g. `yourname-20` |
| `PINTEREST_ACCESS_TOKEN` | Your Pinterest bearer token |
| `GOOGLE_SHEET_ID` | Your sheet ID |
| `GOOGLE_CREDENTIALS_JSON` | Paste the **entire contents** of your service account JSON file |

> Never commit real credentials into the code — always use GitHub Secrets.

---

## Running

**Test locally:**
```bash
pip install -r requirements.txt
python main.py
```

**Trigger manually on GitHub:**
Actions tab → Weekly Amazon → Pinterest Post → Run workflow

**Automatic schedule:**
Runs every Sunday at 9:00 AM IST (3:30 AM UTC) — no action needed.

---

## Customising the schedule

Edit the cron line in `.github/workflows/weekly_post.yml`:

```yaml
- cron: "30 3 * * 0"    # Sunday 9AM IST  (default)
- cron: "30 3 * * 1"    # Monday 9AM IST
- cron: "30 3 1 * *"    # 1st of every month
```

---

## Customising categories

Add, remove, or edit entries in the `CATEGORIES` list in `config.py`. Each entry needs a `bestseller_url`, `board_id`, and `hashtags` list.

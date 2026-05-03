# Google Sheets CRM — 5-minute setup

The bot writes every qualified lead as one row in a Google Sheet your sales team already uses. No proprietary CRM, no extra licence, agents collaborate live.

## Step 1 — Create the sheet

1. Open <https://sheets.google.com> → **Blank**
2. Name it `Casa Verde Leads` (or whatever)
3. Rename the first tab to `Leads`
4. Copy the spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/<THIS_LONG_STRING>/edit
   ```
5. Paste it into `.env` as `GOOGLE_SHEETS_ID`

The bot will auto-populate the header row on first startup. To seed it manually:

```bash
python scripts/setup_sheets.py
```

## Step 2 — Create a service account

A *service account* is a robot Google identity. It can be granted access to your sheet without using your personal account, and it doesn't count against any seat licence.

1. Go to <https://console.cloud.google.com/projectcreate>
2. Project name: `casa-verde-bot` → **Create**
3. Enable the Google Sheets API:
   <https://console.cloud.google.com/apis/library/sheets.googleapis.com> → **Enable**
4. Create the service account:
   <https://console.cloud.google.com/iam-admin/serviceaccounts>
   → **Create Service Account**
   → Name: `casa-verde-bot-sheets` → skip optional roles → **Done**
5. Generate a key:
   - Click the service account → **Keys** tab → **Add Key → Create new key → JSON**
   - A JSON file downloads — rename it to `google_credentials.json` and place it at the project root
   - Reference it in `.env`: `GOOGLE_CREDENTIALS_JSON=./google_credentials.json`

## Step 3 — Share the sheet with the service account

1. Open the JSON key file, find the `client_email` field. It looks like
   `casa-verde-bot-sheets@casa-verde-bot.iam.gserviceaccount.com`
2. In your Google Sheet → **Share** → paste that email → **Editor** → **Send**
3. The bot can now read and write the sheet

## Step 4 — Verify

```bash
python scripts/setup_sheets.py
```

Expected output:

```
→ Connecting to sheet ID: 1XXXXXXXXXXXXXXXXXX
✓ Connected to sheet: Casa Verde Leads
✓ Tab 'Leads' found
✓ Headers ensured (sheet has 16 columns)
```

Open the sheet — row 1 should now have bold headers:
`timestamp_utc | score | score_value | name | phone | email | …`

## Header reference

| Column | Type | Notes |
|---|---|---|
| `timestamp_utc` | ISO datetime | When the lead was qualified |
| `score` | enum | `HOT` / `WARM` / `COLD` |
| `score_value` | int | 0–100, useful for sorting |
| `name` | string | Prospect's first name (minimum) |
| `phone` | string | E.164 format |
| `email` | string | Optional |
| `intent` | enum | `buy` / `rent` |
| `budget_min_usd` | int | Optional lower bound |
| `budget_max_usd` | int | USD total (buy) or USD/mo (rent) |
| `neighborhoods` | string | Comma-separated (e.g. `Santa Monica, Brentwood`) |
| `bedrooms` | int | Optional |
| `timeline_months` | int | Months until move-in / closing |
| `financing` | enum | `cash` / `conventional` / `jumbo` / `foreign_national` / `rental` |
| `must_haves` | string | Comma-separated (e.g. `parking, pool, ocean view`) |
| `language` | enum | `en` / `es` |
| `summary` | string | 1–2 sentence agent-facing brief |

## Pro tips

- **Conditional formatting:** highlight `HOT` rows red, `WARM` yellow. Format → Conditional formatting → custom formula `=$B2="HOT"` → fill colour.
- **Data validation:** put a dropdown on a "status" column (`new`, `contacted`, `met`, `won`, `lost`) so agents can update from inside the sheet without leaving.
- **Daily digest:** add a sheet-attached Apps Script that emails Diana a summary at 7 AM. The bot doesn't need to know.
- **Backup:** `File → Make a copy` weekly. Or pipe the sheet to BigQuery via Google Sheets connector if you want analytics.

## Optional — HubSpot / Pipedrive / Salesforce mirror

The same `_record_lead` hook in [`app/services/conversation.py`](../app/services/conversation.py) can fan out to other CRMs. Add a new client module under `app/services/` and call it after `sheets_client.append_lead`. Each CRM is ~50 LoC.

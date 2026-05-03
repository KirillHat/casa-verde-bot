"""Seed the Google Sheet with 28 realistic demo leads (for portfolio screenshot).

Idempotent in spirit — running it twice will duplicate rows. Designed to be
run once on a fresh sheet (or after the existing 2 real leads).

Usage:
    python scripts/seed_sheet_demo.py
"""
from __future__ import annotations

import gspread
from google.oauth2.service_account import Credentials

from app.config import get_settings
from app.services.scoring import LeadFacts, score_lead

# (timestamp, name, lang, intent, budget_min|None, budget_max, neighborhoods,
#  bedrooms|None, timeline_months, financing|None, must_haves, email|"", summary)
LEADS: list[tuple] = [
    # ---- HOT buyers --------------------------------------------------------
    ("2026-04-20T11:42:13", "Wei Zhang",         "en", "buy", 3_800_000, 4_200_000, ["Beverly Hills"],                   5, 2, "cash",             ["security gate", "guest house"], "wei.zhang@example.com",
     "Chinese investor, $4.2M Beverly Hills, all-cash, 2-month timeline. Wants guest house + gated."),

    ("2026-04-21T22:18:09", "Hiroshi Yamamoto",  "en", "buy", 5_000_000, 5_500_000, ["Bel Air"],                          6, 3, "foreign_national", ["privacy", "tennis court"],      "h.yamamoto@example.jp",
     "Japanese executive relocating, $5.5M Bel Air, FN pre-approved, wants privacy + tennis court."),

    ("2026-04-22T09:14:51", "Maria Hernandez",   "es", "buy", 1_700_000, 1_850_000, ["Venice"],                           3, 1, "cash",             ["walkable to beach"],            "",
     "Cash buyer from CDMX, $1.85M Venice 3BR, urgent 1-month close, walkable to the beach is a must."),

    ("2026-04-23T15:33:27", "James Reynolds",    "en", "buy", 2_800_000, 3_100_000, ["Pacific Palisades"],                4, 2, "jumbo",            ["ocean view", "modern"],         "jreynolds@example.com",
     "SF tech exec relocating for new role, jumbo pre-approved $3.1M, modern Palisades home with ocean view."),

    ("2026-04-25T08:09:42", "Sofia Rivera",      "es", "buy", 1_400_000, 1_600_000, ["West Hollywood"],                   2, 2, "jumbo",            ["walk score", "rooftop"],        "",
     "Argentine entrepreneur, $1.6M WeHo 2BR, jumbo, prefers high walk-score and rooftop."),

    ("2026-04-27T19:47:05", "Lauren Kim",        "en", "buy", 1_950_000, 2_200_000, ["Westwood"],                         3, 3, "jumbo",            ["good schools"],                 "lauren.k@example.com",
     "UCLA faculty, family with kids, $2.2M Westwood 3BR, good public schools priority."),

    ("2026-04-29T13:21:18", "Carlos Reyes",      "es", "buy", 2_300_000, 2_500_000, ["Santa Monica", "Brentwood"],        3, 4, "foreign_national", ["pool", "ocean view"],           "carlos@example.com",
     "Mexican buyer with FN pre-approval, 3BR Westside up to $2.5M, move-in 4 months."),

    # ---- WARM buyers -------------------------------------------------------
    ("2026-04-20T17:05:31", "David Chen",        "en", "buy", 1_750_000, 1_950_000, ["Brentwood"],                        3, 4, "conventional",     ["yard", "garage 2-car"],         "dchen@example.com",
     "Local family upgrading from condo, $1.95M Brentwood SFH, conventional, wants yard + 2-car garage."),

    ("2026-04-22T20:54:12", "Klaus Mueller",     "en", "buy", 2_500_000, 2_800_000, ["Santa Monica"],                     4, 8, "foreign_national", ["mid-century"],                  "k.mueller@example.de",
     "German design enthusiast, $2.8M Santa Monica mid-century, FN, flexible 8-month window."),

    ("2026-04-23T07:38:46", "Min-jun Park",      "en", "buy", 1_200_000, 1_400_000, ["Culver City"],                      3, 5, "jumbo",            ["new construction"],             "minjun.park@example.kr",
     "Korean tech worker H1-B, $1.4M Culver City 3BR, jumbo, prefers newer build."),

    ("2026-04-24T11:11:55", "Olga Petrova",      "en", "buy",   850_000,   950_000, ["Silver Lake"],                      2, 4, "conventional",     ["original character"],           "",
     "Designer relocating from NY, $950k Silver Lake 2BR, conventional, loves Craftsman/Spanish character."),

    ("2026-04-25T16:29:08", "Jean-Pierre Dubois","en", "buy", 3_000_000, 3_500_000, ["Beverly Hills"],                    5,12, "foreign_national", ["pool", "office"],               "jp.dubois@example.fr",
     "French film producer, $3.5M Beverly Hills, FN, looking 12 months out, needs pool + home office."),

    ("2026-04-26T10:47:33", "Yuki Tanaka",       "en", "buy", 1_150_000, 1_300_000, ["Los Feliz"],                        2, 6, "jumbo",            ["walkable", "view"],             "yuki.t@example.jp",
     "Japanese designer, $1.3M Los Feliz 2BR with view, jumbo, walkable Hillhurst preferred."),

    ("2026-04-27T22:33:14", "Diego Santos",      "es", "buy",   950_000, 1_100_000, ["Mar Vista"],                        3, 6, "conventional",     ["yard for dog"],                 "",
     "Brazilian family, $1.1M Mar Vista 3BR, conventional, needs yard for dog."),

    ("2026-04-28T14:02:51", "Priya Patel",       "en", "buy",   780_000,   875_000, ["Echo Park"],                        2, 5, "conventional",     ["walkable cafes"],               "ppatel@example.com",
     "First-time buyer from Bay Area, $875k Echo Park 2BR, conventional, wants walkable cafes."),

    ("2026-04-29T09:55:27", "Rafael Costa",      "es", "buy", 1_300_000, 1_500_000, ["West Hollywood", "Mid-City"],       2, 8, "conventional",     ["modern"],                       "",
     "Brazilian exec relocating, $1.5M WeHo or Mid-City modern condo, 8-month timeline."),

    ("2026-04-30T18:22:09", "Amelia Foster",     "en", "buy", 1_050_000, 1_200_000, ["Atwater Village"],                  3, 6, "conventional",     ["EV charging", "yard"],          "amelia.f@example.com",
     "Family of 4 from Bay Area, $1.2M Atwater Village 3BR with EV charging + small yard."),

    ("2026-05-01T13:18:44", "Hannah Goldberg",   "en", "buy",   900_000, 1_050_000, ["Mid-City", "Koreatown"],            2, 8, "conventional",     ["pre-war character"],            "",
     "Comedy writer, $1.05M Mid-City or K-town 2BR, conventional, pre-war character preferred."),

    # ---- COLD buyers -------------------------------------------------------
    ("2026-04-22T01:14:38", "Anna Schmidt",      "en", "buy",         0,   700_000, ["DTLA"],                             1,24, None,               [],                                "",
     "Browsing $700k DTLA loft, no firm timeline, no financing pre-approval yet."),

    ("2026-04-26T23:48:19", "Ricardo Vega",      "es", "buy",         0,   450_000, ["Koreatown"],                        1,18, None,               [],                                "",
     "Looking $450k K-town studio/1BR, 18-month horizon, no financing yet."),

    ("2026-04-30T03:12:55", "Emily Park",        "en", "buy",         0,   600_000, ["Mid-City"],                         2,12, "conventional",     ["any"],                          "",
     "Recent grad, $600k Mid-City 2BR, conventional pre-qual, 12-month browse."),

    # ---- HOT renters -------------------------------------------------------
    ("2026-04-24T16:51:02", "Aisha Williams",    "en", "rent",     6500,     7200, ["West Hollywood"],                   2, 2, "rental",           ["concierge", "gym"],             "aisha.w@example.com",
     "Entertainment exec relocating from NY, $7.2k/mo WeHo 2BR with concierge + gym, 2-month."),

    ("2026-04-26T11:38:29", "Liam O'Brien",      "en", "rent",     5000,     5500, ["Santa Monica"],                     2, 1, "rental",           ["unfurnished", "parking"],       "liam.o@example.ie",
     "Irish startup founder, $5.5k/mo Santa Monica 2BR unfurnished + parking, urgent."),

    ("2026-04-30T09:43:18", "Tom Martinez",      "en", "rent",     6000,     6500, ["Venice"],                           3, 1, "rental",           ["walk to beach", "yard"],        "tom.m@example.com",
     "Family of 3 relocating from Austin, $6.5k/mo Venice 3BR walk-to-beach with yard, urgent."),

    ("2026-05-01T20:09:51", "Nadia Hassan",      "en", "rent",     4800,     5200, ["Silver Lake"],                      2, 1, "rental",           ["pet-friendly", "view"],         "n.hassan@example.com",
     "PR director from Toronto, $5.2k/mo Silver Lake 2BR pet-friendly with view, 1-month."),

    ("2026-05-02T15:26:37", "Sarah Chen",        "en", "rent",     4500,     5000, ["Venice"],                           2, 2, "rental",           ["walkable to coffee", "unfurnished"], "schen@example.com",
     "NYC tech mover, Google offer, 2BR Venice $5k/mo, Sept 1, walkable + unfurnished."),

    # ---- WARM renters ------------------------------------------------------
    ("2026-04-23T19:47:12", "Pablo Mendez",      "es", "rent",     4000,     4500, ["Culver City"],                      2, 3, "rental",           ["parking 2"],                    "",
     "Mexican family, $4.5k/mo Culver City 2BR with 2-car parking, 3-month."),

    ("2026-04-25T22:14:08", "Marcus Johnson",    "en", "rent",     4200,     4800, ["Mar Vista"],                        2, 1, "rental",           ["yard for dog"],                 "marcus.j@example.com",
     "Marketing director from Chicago, $4.8k/mo Mar Vista 2BR yard for dog, 1-month."),

    ("2026-04-28T08:32:44", "Chloe Bennett",     "en", "rent",     2900,     3200, ["Echo Park"],                        1, 2, "rental",           ["walkable", "in-unit laundry"],  "",
     "Recent UCLA grad, $3.2k/mo Echo Park 1BR walkable + in-unit laundry."),

    ("2026-04-29T17:55:29", "Isabella Rossi",    "en", "rent",     3500,     3800, ["Los Feliz"],                        1, 4, "rental",           ["pet-friendly", "balcony"],      "isabella.r@example.it",
     "Italian designer, $3.8k/mo Los Feliz 1BR pet-friendly with balcony, 4-month."),

    # ---- COLD renters ------------------------------------------------------
    ("2026-04-21T02:38:46", "Kenji Tanaka",      "en", "rent",     2500,     2800, ["Koreatown"],                        1, 6, "rental",           ["budget"],                       "",
     "Student, $2.8k/mo K-town 1BR, 6-month, tight budget."),

    ("2026-05-02T04:51:33", "Rebecca Ng",        "en", "rent",     2200,     2400, ["DTLA"],                             1,12, "rental",           ["under budget"],                 "",
     "Browsing $2.4k/mo DTLA 1BR, 12-month, just exploring."),
]

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def main() -> None:
    settings = get_settings()
    if not settings.google_sheets_id:
        raise SystemExit("GOOGLE_SHEETS_ID is empty — set it in .env first.")

    creds = Credentials.from_service_account_file(
        str(settings.google_credentials_json), scopes=_SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(settings.google_sheets_id).worksheet(
        settings.google_sheets_tab
    )

    rows: list[list] = []
    score_counts: dict[str, int] = {"HOT": 0, "WARM": 0, "COLD": 0}

    for lead in LEADS:
        (
            ts, name, lang, intent, b_min, b_max, hoods, beds, tl, fin,
            must_haves, email, summary,
        ) = lead

        facts = LeadFacts(
            intent=intent,
            budget_max=b_max,
            timeline_months=tl,
            financing=fin,
        )
        score, val = score_lead(facts)
        score_counts[score] += 1

        # Phone numbers — fictional 555 reserved range, varied LA area codes
        # (deterministic per-lead so re-runs produce identical row layout)
        area_codes = ["213", "310", "323", "424", "818"]
        ac = area_codes[hash(name) % len(area_codes)]
        last4 = (hash(name) % 9000 + 1000) % 9000 + 1000
        phone = f"+1{ac}555{last4:04d}"

        rows.append([
            ts + "+00:00",
            score,
            val,
            name,
            phone,
            email,
            intent,
            b_min if b_min else "",
            b_max,
            ", ".join(hoods),
            beds if beds else "",
            tl,
            fin or "",
            ", ".join(must_haves),
            lang,
            summary,
        ])

    sheet.append_rows(rows, value_input_option="USER_ENTERED")

    print(f"✓ Seeded {len(rows)} demo leads to '{sheet.spreadsheet.title}' / '{sheet.title}'")
    print(f"  \U0001f525 HOT  : {score_counts['HOT']}")
    print(f"  \U0001f7e1 WARM : {score_counts['WARM']}")
    print(f"  \U0001f535 COLD : {score_counts['COLD']}")


if __name__ == "__main__":
    main()

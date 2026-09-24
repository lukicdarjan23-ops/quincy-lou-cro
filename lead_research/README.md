# evie.design lead research tool

Finds agencies that sell website design (US and Canada, roughly 5 to 20 people), identifies the decision-maker, finds a sourced email, and drafts a personal outreach email. State lives in `leads.csv` (one row per agency, deduped by domain) and is saved after every agency.

## Setup
```
pip install requests python-dotenv beautifulsoup4 openpyxl
```
Credentials go in `lead_research/.env` (git-ignored): `ICYPEAS_API_KEY`, `ICYPEAS_API_SECRET`, `ICYPEAS_USER_ID`.

## Commands (run from `lead_research/`)
| command | what it does |
|---|---|
| `python -m leadtool test-icypeas` | one credential check, result stored in `icypeas_state.json` |
| `python -m leadtool add batches/batchNN.json` | add or update researched agencies, prints progress every 10 |
| `python -m leadtool crawl domain.com` | robots.txt-aware crawl for emails and web-design service pages |
| `python -m leadtool known` | domains already in `leads.csv` |
| `python -m leadtool progress` | one-line status including Icypeas credits used |
| `python -m leadtool export` | writes `leads.xlsx` (ready rows first) and `SUMMARY.md` |

`add` enforces the sourcing rules. A name needs a source URL. An email needs a source URL and has to be on the agency's domain (or published by the agency). A guessed address can only become the email if Icypeas confirms it; otherwise it stays in `guessed_unverified`. An `exclude.csv` (domains or names) is honoured if present.

See `DECISIONS.md` for how the first run was done and its limits, and `candidates_backlog.csv` for where to pick up.

## Live Google Sheet
Set two environment variables and every save also updates the sheet (ready rows first):
- `GOOGLE_SA_EMAIL` and `GOOGLE_SA_PRIVATE_KEY`: `client_email` and `private_key` from the key file, each on one line (or `GOOGLE_SERVICE_ACCOUNT_JSON` with the whole file on one line)
- `GOOGLE_SHEET_ID`: the long id in the sheet URL, `docs.google.com/spreadsheets/d/<ID>/edit`

Share the sheet (Editor) with the service account's email. `python -m leadtool sheet-sync` pushes on demand. Extra packages: `pip install gspread google-auth`.

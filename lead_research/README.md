# evie.design lead research tool

Finds agencies that sell website design (US and Canada, roughly 5 to 20 people), identifies the decision-maker, finds the decision-maker's own sourced email, and holds the personal opening line for the outreach app. State lives in `leads.csv` (one row per agency, deduped by domain, with a source for every fact) and is saved after every agency.

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
| `python -m leadtool openings file.json` | add opening lines to known agencies: `[{"domain", "angle", "opening_line", "opening_source_url"}]` |
| `python -m leadtool restatus` | recompute every status and resync the sheet |
| `python -m leadtool export` | writes `leads.xlsx` (ready rows first) and `SUMMARY.md` |

`add` enforces the sourcing rules. A name needs a source URL. An email needs a source URL and has to be on the agency's domain (or published by the agency). A guessed address can only become the email if Icypeas confirms it; otherwise it stays in `guessed_unverified`. An `exclude.csv` (domains or names) is honoured if present.

See `DECISIONS.md` for how the first run was done and its limits, and `candidates_backlog.csv` for where to pick up.

## Live Google Sheet
Every save also rewrites the sheet with the nine columns the outreach app reads (agency_name, website, contact_name, email, city, angle, opening_line, opening_source_url, status), ready rows first. `angle` is one of hiring, award, project or industry (see DECISIONS.md); the app sends version D to `hiring`. `status` is `ready` only when the owner's name, the owner's own address, a "City, ST" and a sourced opening line with its angle are all there; otherwise it says what is missing. Agencies without the owner's own address go to a second tab, "missing owner email", which the app never reads. Rows added to either tab by hand are kept. Set two environment variables to turn it on:
- `GOOGLE_SA_EMAIL` and `GOOGLE_SA_PRIVATE_KEY`: `client_email` and `private_key` from the key file, each on one line (or `GOOGLE_SERVICE_ACCOUNT_JSON` with the whole file on one line)
- `GOOGLE_SHEET_ID`: the long id in the sheet URL, `docs.google.com/spreadsheets/d/<ID>/edit`

Share the sheet (Editor) with the service account's email. `python -m leadtool sheet-sync` pushes on demand. Extra packages: `pip install gspread google-auth`.

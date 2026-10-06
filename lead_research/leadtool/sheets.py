"""Live mirror of leads.csv into one Google Sheet.

Turned on when both environment variables are set:
  GOOGLE_SERVICE_ACCOUNT_JSON  the service account key (file contents, or a path to the file)
  GOOGLE_SHEET_ID              the id from the sheet URL, docs.google.com/spreadsheets/d/<ID>/edit
The sheet must be shared (Editor) with the service account's client_email.
Every save rewrites the "leads" tab: qualified agencies only, ready rows first,
and only the columns the outreach app needs (store.SHEET_COLUMNS). leads.csv stays
the source of truth with every source URL, so a failed sync never loses data.
Rows added by hand to the sheet (a website that is not in leads.csv) are kept.
"""
import json
import os

from .store import SHEET_COLUMNS

_client = None
TAB = "leads"


def _key_info():
    """Service account key, either as full JSON or as two one-line variables
    (GOOGLE_SA_EMAIL + GOOGLE_SA_PRIVATE_KEY), which fit .env format."""
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw:
        return json.load(open(raw)) if not raw.startswith("{") else json.loads(raw)
    email, key = os.getenv("GOOGLE_SA_EMAIL", ""), os.getenv("GOOGLE_SA_PRIVATE_KEY", "")
    if email and key:
        return {"type": "service_account", "client_email": email.strip(),
                "private_key": key.strip().strip('"').replace("\\n", "\n"),
                "token_uri": "https://oauth2.googleapis.com/token"}
    return None


def enabled():
    has_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or (
        os.getenv("GOOGLE_SA_EMAIL") and os.getenv("GOOGLE_SA_PRIVATE_KEY"))
    return bool(has_key and os.getenv("GOOGLE_SHEET_ID"))


def _sheet():
    global _client
    import gspread
    if _client is None:
        _client = gspread.service_account_from_dict(_key_info())
    book = _client.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    try:
        return book.worksheet(TAB)
    except gspread.WorksheetNotFound:
        return book.add_worksheet(TAB, rows=1000, cols=20)


def sheet_row(r):
    """One leads.csv row as the sheet shows it."""
    from .store import lead_status, owner_email
    out = {c: r.get(c, "") for c in SHEET_COLUMNS}
    out["email"] = owner_email(r)
    out["status"] = lead_status(r)
    return out


def sync(rows, columns=None):
    """Rewrite the leads tab. Returns an error string, or '' on success."""
    if not enabled():
        return "not configured"
    from .export import _rank
    from .store import is_qualified, normalize_domain
    try:
        ws = _sheet()
        ours = {r["domain"] for r in rows}
        # Keep rows someone added by hand, mapped by header name.
        current = ws.get_all_values()
        kept = []
        if current:
            header = current[0]
            for values in current[1:]:
                old = dict(zip(header, values))
                domain = old.get("domain") or normalize_domain(old.get("website", ""))
                if domain and domain not in ours:
                    kept.append({c: old.get(c, "") for c in SHEET_COLUMNS})
        shown = [sheet_row(r) for r in rows if is_qualified(r)]
        data = [SHEET_COLUMNS] + [[r[c] for c in SHEET_COLUMNS] for r in sorted(shown, key=_rank) + kept]
        ws.clear()
        ws.update(data, "A1", value_input_option="RAW")
        ws.freeze(rows=1)
        return ""
    except Exception as e:  # never break the research run over a sync problem
        return f"{type(e).__name__}: {e}"[:200]

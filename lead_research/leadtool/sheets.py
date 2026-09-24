"""Live mirror of leads.csv into one Google Sheet.

Turned on when both environment variables are set:
  GOOGLE_SERVICE_ACCOUNT_JSON  the service account key (file contents, or a path to the file)
  GOOGLE_SHEET_ID              the id from the sheet URL, docs.google.com/spreadsheets/d/<ID>/edit
The sheet must be shared (Editor) with the service account's client_email.
Every save rewrites the "leads" tab with ready rows first. leads.csv stays the
source of truth, so a failed sync never loses data.
"""
import json
import os

_client = None
TAB = "leads"


def enabled():
    return bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and os.getenv("GOOGLE_SHEET_ID"))


def _sheet():
    global _client
    import gspread
    if _client is None:
        raw = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"].strip()
        info = json.load(open(raw)) if not raw.startswith("{") else json.loads(raw)
        _client = gspread.service_account_from_dict(info)
    book = _client.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    try:
        return book.worksheet(TAB)
    except gspread.WorksheetNotFound:
        return book.add_worksheet(TAB, rows=1000, cols=20)


def sync(rows, columns):
    """Rewrite the leads tab. Returns an error string, or '' on success."""
    if not enabled():
        return "not configured"
    from .export import _rank
    try:
        ws = _sheet()
        data = [columns] + [[r.get(c, "") for c in columns] for r in sorted(rows, key=_rank)]
        ws.clear()
        ws.update(data, "A1", value_input_option="RAW")
        ws.freeze(rows=1)
        return ""
    except Exception as e:  # never break the research run over a sync problem
        return f"{type(e).__name__}: {e}"[:200]

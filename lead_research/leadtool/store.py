"""leads.csv state: load, dedupe by domain, save after every agency."""
import csv
import os
import re
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_CSV = os.path.join(ROOT, "leads.csv")
EXCLUDE_CSV = os.path.join(ROOT, "exclude.csv")

COLUMNS = [
    "agency_name", "website", "domain", "country", "city", "team_size_estimate",
    "why_fit", "contact_name", "contact_title", "contact_source_url", "email",
    "email_source", "email_confidence", "guessed_unverified", "subject",
    "email_body", "research_note", "status",
]


def normalize_domain(value):
    value = (value or "").strip().lower()
    if not value:
        return ""
    if "://" not in value:
        value = "http://" + value
    host = urlparse(value).hostname or ""
    return re.sub(r"^www\d?\.", "", host)


def load_leads():
    if not os.path.exists(LEADS_CSV):
        return []
    with open(LEADS_CSV, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def save_leads(rows):
    tmp = LEADS_CSV + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    os.replace(tmp, LEADS_CSV)
    from . import sheets
    if sheets.enabled():
        err = sheets.sync(rows, COLUMNS)
        if err:
            print(f"  google sheet sync failed (leads.csv is saved): {err}")


def load_exclusions():
    """exclude.csv may hold domains or agency names, one per row, any column."""
    domains, names = set(), set()
    if not os.path.exists(EXCLUDE_CSV):
        return domains, names
    with open(EXCLUDE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            for cell in row:
                cell = cell.strip()
                if not cell or cell.lower() in ("domain", "agency_name", "name", "website"):
                    continue
                if "." in cell and " " not in cell:
                    domains.add(normalize_domain(cell))
                else:
                    names.add(cell.lower())
    return domains, names


def is_excluded(domain, name):
    domains, names = load_exclusions()
    return normalize_domain(domain) in domains or (name or "").strip().lower() in names


def known_domains():
    return {r["domain"] for r in load_leads()}


def upsert(row):
    """Insert or replace by domain, then save. Returns 'added' or 'updated'."""
    rows = load_leads()
    for i, r in enumerate(rows):
        if r["domain"] == row["domain"]:
            rows[i] = row
            save_leads(rows)
            return "updated"
    rows.append(row)
    save_leads(rows)
    return "added"


def is_qualified(row):
    return not row.get("status", "").startswith("skip")

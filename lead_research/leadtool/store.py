"""leads.csv state: load, dedupe by domain, save after every agency."""
import csv
import os
import re
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_CSV = os.path.join(ROOT, "leads.csv")
EXCLUDE_CSV = os.path.join(ROOT, "exclude.csv")

# leads.csv keeps the full research record, with a source for every fact.
COLUMNS = [
    "agency_name", "website", "domain", "country", "city", "team_size_estimate",
    "why_fit", "contact_name", "contact_title", "contact_source_url", "email",
    "email_source", "email_confidence", "guessed_unverified",
    "angle", "opening_line", "opening_source_url", "research_note", "status",
]

# The Google Sheet shows only what the outreach app needs to send.
SHEET_COLUMNS = [
    "agency_name", "website", "contact_name", "email", "city",
    "angle", "opening_line", "opening_source_url", "status",
]

# What the opening line is about, and so which email the outreach app sends (Darjan, 7 Oct 2026):
#   hiring    an open designer job, posted in the last 30 days            -> D
#   valley    the agency is in California's Central Valley (set by the tool, see apply_valley) -> F, no line
#   award     an award or listing from the last 30 days                   -> B1 or B2
#   owner     something the owner said or wrote about running the business, at most 12 months old -> A
#   industry  the agency says on its site it builds for one or two industries Darjan knows;
#             the tool writes the line (leadtool/industry.py)              -> E
#   none      nothing real to open with                                   -> C1 or C2, no line
# "project" is no longer used; an old project line gets C1 or C2 without it.
ANGLES = ("hiring", "valley", "award", "owner", "project", "industry", "none")
NO_LINE_ANGLES = ("none", "valley")

# The app reads the recipient's time zone from "City, ST".
STATE_CODE = re.compile(r",\s*[A-Z]{2}\b")

REGIONS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "district of columbia": "DC", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
    "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "alberta": "AB", "british columbia": "BC", "manitoba": "MB", "new brunswick": "NB",
    "newfoundland": "NL", "nova scotia": "NS", "ontario": "ON", "prince edward island": "PE",
    "quebec": "QC", "saskatchewan": "SK", "yukon": "YT",
}


def with_state_code(city):
    """'Rhode Island' -> 'Rhode Island, RI', so the app can tell the time zone. Only a state or
    province name already in the text is used; nothing is guessed."""
    city = (city or "").strip()
    if not city or STATE_CODE.search(city.upper()):
        return city
    low = city.lower()
    # Longest names first, so "west virginia" wins over "virginia".
    for name in sorted(REGIONS, key=len, reverse=True):
        if re.search(rf"\b{name}\b", low):
            return f"{city}, {REGIONS[name]}"
    return city


# Darjan worked four years for an agency in Fresno, so agencies anywhere in the Central Valley get
# version F. The valley's 18 counties (Wikipedia, "Central Valley (California)"): Butte, Colusa, Glenn,
# Fresno, Kern, Kings, Madera, Merced, Placer, San Joaquin, Sacramento, Shasta, Stanislaus, Sutter,
# Tehama, Tulare, Yolo, Yuba. Below are the towns on the valley floor in those counties (foothill and
# desert towns such as Paradise, Auburn, Tehachapi and Ridgecrest left out), plus the county names.
CENTRAL_VALLEY = [
    "chico", "oroville", "gridley", "biggs", "colusa", "williams", "orland", "willows",
    "fresno", "clovis", "sanger", "selma", "reedley", "kingsburg", "fowler", "parlier", "kerman", "coalinga",
    "firebaugh", "mendota", "orange cove", "huron",
    "bakersfield", "delano", "wasco", "shafter", "mcfarland", "arvin", "taft",
    "hanford", "lemoore", "corcoran", "avenal", "madera", "chowchilla",
    "merced", "atwater", "los banos", "livingston", "gustine", "dos palos",
    "roseville", "rocklin", "lincoln",
    "stockton", "tracy", "manteca", "lodi", "lathrop", "ripon", "escalon",
    "sacramento", "elk grove", "rancho cordova", "citrus heights", "folsom", "galt", "carmichael", "fair oaks",
    "redding", "anderson", "shasta lake",
    "modesto", "turlock", "ceres", "oakdale", "riverbank", "patterson", "newman", "hughson", "waterford",
    "yuba city", "live oak", "red bluff", "corning",
    "visalia", "tulare", "porterville", "dinuba", "lindsay", "exeter", "farmersville", "woodlake",
    "davis", "woodland", "west sacramento", "winters", "marysville", "wheatland",
    "butte county", "glenn county", "kern county", "kings county", "placer county", "san joaquin county",
    "stanislaus county", "sutter county", "tehama county", "yolo county", "yuba county", "central valley",
]
_VALLEY = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(CENTRAL_VALLEY, key=len, reverse=True)) + r")\b")


def in_central_valley(city):
    """True for a California town in the Central Valley ("Fresno, CA", "Rancho Cordova / Sacramento, CA")."""
    low = (city or "").lower()
    california = re.search(r",\s*ca\b", low) or "california" in low
    return bool(california and _VALLEY.search(low))


def apply_valley(row):
    """A Central Valley agency gets angle "valley" (version F) unless it is hiring a designer (D comes
    first). Its opening line is kept in leads.csv but not used. Returns True when the angle changed."""
    if in_central_valley(row.get("city")) and row.get("angle") not in ("hiring", "valley") and is_qualified(row):
        row["angle"] = "valley"
        return True
    return False


def owner_email(row):
    """The decision-maker's own address, published by the agency or confirmed by Icypeas.
    A general inbox (info@, hello@) is not one and is not kept."""
    if row.get("email_source", "").startswith("generic"):
        return ""
    return row.get("email", "")


def lead_status(row):
    """ready when everything the app needs is there, otherwise 'missing: ...'. Skipped rows keep their reason."""
    if not is_qualified(row):
        return row["status"]
    missing = []
    if not row.get("contact_name"):
        missing.append("owner name")
    if not owner_email(row):
        missing.append("owner email")
    if not STATE_CODE.search((row.get("city") or "").upper()):
        missing.append("city")
    if row.get("angle") in NO_LINE_ANGLES:
        pass  # no opening line on purpose
    elif not row.get("opening_line") or not row.get("opening_source_url"):
        missing.append("opening line")
    elif row.get("angle") not in ANGLES:
        missing.append("angle")
    return "missing: " + ", ".join(missing) if missing else "ready"


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

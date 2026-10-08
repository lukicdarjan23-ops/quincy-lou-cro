"""Checks a line has to pass before the tool accepts it. Hiring, award and industry lines go out without
Darjan's Ready (8 Oct 2026), so the mistakes found on 7 Oct must be impossible to make again:
  - an award line naming something the source page does not say (Big Red Jelly), or a directory badge
    sold as an award;
  - an industry line built from a sentence about the agency itself, not its clients (Branch Marketing);
  - a designer job that turned out to be years old (The Creative Momentum, 2020).
Each check returns an error message, or "" when the record is fine.
"""
import datetime as dt
import re

# Directory listings and review-site badges: not awards. A win must come from a judged competition
# (Webby, Davey, Awwwards, CSS Design Awards, ADDY, Communicator, MUSE, Telly, W3, Hermes and similar)
# or a named award from a real organisation (a chamber of commerce, a city, a trade body).
DIRECTORIES = ["clutch", "50pros", "designrush", "upcity", "the manifest", "themanifest", "goodfirms", "expertise.com",
               "threebestrated", "three best rated", "techreviewer", "sortlist", "topdevelopers", "top developers",
               "agency spotter", "agencyspotter", "bark.com", "yelp", "g2 ", "trustpilot"]

DESIGN_ROLE = re.compile(r"\b(designer|ui|ux|visual design|web design|graphic design|product design)\b", re.I)
NOT_DESIGN = re.compile(r"\b(developer|development|engineer|engineering|front[- ]?end|back[- ]?end|full[- ]?stack|"
                        r"marketing|seo|sales|account|project manager|copywriter|content writer)\b", re.I)


def check_award(d, today=None):
    year = str((today or dt.date.today()).year)
    name, evidence, line = ((d.get(k) or "").strip() for k in ("award_name", "award_evidence", "opening_line"))
    if not name or not evidence:
        return "award needs award_name and award_evidence (the award's exact words copied from the source page)"
    if name.lower() not in evidence.lower():
        return f"award_name {name!r} is not in award_evidence, copy it exactly as the page writes it"
    if name.lower() not in line.lower():
        return f"the line must name the award exactly as {name!r}"
    if year not in evidence:
        return f"award_evidence has no {year}, only awards from the current year count"
    hit = [x for x in DIRECTORIES if x in (name + " " + evidence + " " + line).lower()]
    if hit:
        return f"{hit[0].strip()} is a directory or review-site listing, not an award; use none"
    return ""


def check_hiring(d, today=None):
    today = today or dt.date.today()
    title, posted = (d.get("job_title") or "").strip(), (d.get("posted_date") or "").strip()
    if not title or not posted:
        return "hiring needs job_title and posted_date (YYYY-MM-DD, from the job page or the site's sitemap lastmod)"
    try:
        when = dt.date.fromisoformat(posted)
    except ValueError:
        return f"posted_date {posted!r} is not YYYY-MM-DD"
    if when > today or (today - when).days > 50:
        return f"the job was posted {posted}, more than 50 days ago (or in the future); use another angle"
    if not DESIGN_ROLE.search(title) or NOT_DESIGN.search(title):
        return f"{title!r} is not a design-only role (web, UI, UX, visual or graphic designer, no dev or marketing)"
    if title.lower() not in (d.get("opening_line") or "").lower():
        return f"the line must name the job exactly as {title!r}"
    return ""

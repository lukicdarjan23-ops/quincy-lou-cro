"""CLI.

  python -m leadtool test-icypeas        one credential check, result in icypeas_state.json
  python -m leadtool add batch.json      add or update agencies (list of dicts), saves after each
  python -m leadtool known               print domains already in leads.csv
  python -m leadtool progress            one-line progress
  python -m leadtool crawl example.com   direct site crawl (needs open web access)
  python -m leadtool export              leads.xlsx + SUMMARY.md
  python -m leadtool sheet-sync          push leads.csv to the Google Sheet now
  python -m leadtool openings file.json  set opening lines: [{"domain", "angle", "opening_line", "opening_source_url"}]
                                         angle "industry": give "industry_text" (the site's sentence naming its clients)
                                         and its page as opening_source_url; the tool writes the line
                                         angle "award": also "award_name" and "award_evidence" (exact words from the page)
                                         angle "hiring": also "job_title" and "posted_date" (YYYY-MM-DD)
                                         records that fail a check are printed as REJECTED and left unchanged
                                         angle "hobby": only opening_source_url (where the owner mentions it),
                                         no line; Darjan writes the line and subject in the app
  python -m leadtool industry "TEXT"     show the industry line the tool would write for that text
  python -m leadtool restatus            recompute every status (ready / missing: ...) and save
"""
import json
import re
import sys

from . import icypeas, store
from .compose import clean_opening, guesses
from .checks import check_award, check_hiring
from .industry import opening_line as industry_line

TARGET = 200


def build_row(d):
    """Turn one research record into a leads.csv row, enforcing the sourcing rules."""
    domain = store.normalize_domain(d.get("domain") or d["website"])
    row = {c: "" for c in store.COLUMNS}
    row.update({
        "agency_name": d["agency_name"].strip(),
        "website": d["website"].strip(),
        "domain": domain,
        "country": d.get("country", ""),
        "city": d.get("city", ""),
        "team_size_estimate": d.get("team_size_estimate", ""),
        "why_fit": d.get("why_fit", ""),
        "research_note": d.get("research_note", ""),
    })
    if d.get("skip"):
        row["status"] = f"skip: {d['skip']}"
        return row

    name = (d.get("contact_name") or "").strip()
    if name and not d.get("contact_source_url"):
        raise ValueError(f"{domain}: contact name without source URL")
    if name:
        row["contact_name"] = name
        row["contact_title"] = d.get("contact_title", "")
        row["contact_source_url"] = d["contact_source_url"]

    email = (d.get("email") or "").strip().lower()
    email_type = d.get("email_type", "personal")
    if email:
        if not d.get("email_source_url"):
            raise ValueError(f"{domain}: email without source URL")
        if email.split("@")[-1] != domain and not d.get("published_by_agency"):
            raise ValueError(f"{domain}: {email} is off-domain and not published by the agency")

    if email and email_type == "personal":
        row["email"] = email
        row["email_source"] = d["email_source_url"]
        on_site = domain in d["email_source_url"]
        row["email_confidence"] = "high" if on_site else "medium"
    else:
        # Steps 1 and 2 found no personal address, so step 3: pattern guesses.
        cands = guesses(name, domain) if name else []
        verified = None
        if cands and icypeas.is_available():
            for c in cands:
                try:
                    if icypeas.verify(c):
                        verified = c
                        break
                except icypeas.IcypeasUnavailable as e:
                    icypeas.mark(False, str(e))
                    break
        if verified:
            row.update(email=verified, email_source="icypeas_verified", email_confidence="high")
        else:
            row["guessed_unverified"] = "; ".join(cands)
            if email:  # step 4: the agency's general address, kept as evidence but never sent to
                row.update(email=email, email_source=f"generic | {d['email_source_url']}",
                           email_confidence="medium")

    # The personal first paragraph must point at the agency's own page showing that work.
    opening = (d.get("opening_line") or "").strip()
    if opening and not d.get("opening_source_url"):
        raise ValueError(f"{domain}: opening line without source URL")
    row["opening_line"] = clean_opening(opening)
    row["opening_source_url"] = d.get("opening_source_url", "") if opening else ""
    row["angle"] = (d.get("angle") or "").strip().lower() if opening else ""
    store.apply_valley(row)
    row["status"] = store.lead_status(row)
    return row


def progress_line():
    rows = store.load_leads()
    q = [r for r in rows if store.is_qualified(r)]
    ready = sum(r["status"] == "ready" for r in q)
    no_owner = sum(not store.owner_email(r) for r in q)
    return (f"qualified {len(q)}/{TARGET} | ready {ready} | missing something {len(q) - ready} "
            f"(no owner email {no_owner}) | skipped {len(rows) - len(q)} | "
            f"icypeas credits used {icypeas.credits_used()}")


def cmd_openings(path):
    """Add opening lines to agencies already in leads.csv. Each line needs the page that shows that work."""
    with open(path) as f:
        records = json.load(f)
    rows = store.load_leads()
    by_domain = {r["domain"]: r for r in rows}
    for d in records:
        domain = store.normalize_domain(d["domain"])
        row = by_domain.get(domain)
        if not row:
            print(f"not in leads.csv, skipped: {domain}")
            continue
        line, url = clean_opening(d.get("opening_line", "")), (d.get("opening_source_url") or "").strip()
        angle = (d.get("angle") or "").strip().lower()
        # Hiring, award and industry lines go out without Darjan's Ready, so they must pass these checks.
        if angle == "industry":
            line = industry_line(row["agency_name"], d.get("industry_text") or "")
            if not line:
                print(f"REJECTED {domain}: industry needs industry_text naming one or two industries from the list as the agency's clients")
                continue
        problem = check_award({**d, "opening_line": line}) if angle == "award" else check_hiring({**d, "opening_line": line}) if angle == "hiring" else ""
        if problem:
            print(f"REJECTED {domain}: {problem}")
            continue
        evidence = {"award": d.get("award_evidence"), "hiring": f"{d.get('job_title')} posted {d.get('posted_date')}", "industry": d.get("industry_text")}.get(angle)
        if evidence:
            note = re.sub(r"\s*\| evidence \(\w+\): .*$", "", row.get("research_note", ""))
            row["research_note"] = f"{note} | evidence ({angle}): {evidence}".strip(" |")
        if line and not url:
            raise ValueError(f"{domain}: opening line without source URL")
        if (line or angle in ("none", "hobby")) and angle not in store.ANGLES:
            raise ValueError(f"{domain}: angle must be one of {', '.join(store.ANGLES)}")
        if angle == "hobby" and not url:
            raise ValueError(f"{domain}: hobby needs the source link in opening_source_url")
        if angle == "none":
            line, url = "", ""  # nothing real to open with, the app sends C1 or C2
        if angle == "hobby":
            line = ""  # Darjan writes the hobby line and its subject himself, in the app
        keep = bool(line) or angle in ("none", "hobby")
        row.update(opening_line=line, opening_source_url=url if (line or angle == "hobby") else "", angle=angle if keep else "")
        store.apply_valley(row)
        row["status"] = store.lead_status(row)
        print(f"{row['status']}: {domain}")
    store.save_leads(rows)
    print(progress_line())


def cmd_restatus():
    rows = store.load_leads()
    for r in rows:
        if store.apply_valley(r):
            print(f"Central Valley, angle valley (version F): {r['domain']} ({r['city']})")
        r["status"] = store.lead_status(r)
    store.save_leads(rows)
    print(progress_line())


def cmd_add(path):
    with open(path) as f:
        records = json.load(f)
    for i, d in enumerate(records, 1):
        domain = store.normalize_domain(d.get("domain") or d["website"])
        if store.is_excluded(domain, d["agency_name"]):
            print(f"excluded by exclude.csv: {domain}")
            continue
        print(f"{store.upsert(build_row(d))}: {domain}")
        if i % 10 == 0:
            print(progress_line())
    print(progress_line())


def main(argv):
    cmd = argv[0] if argv else "progress"
    if cmd == "test-icypeas":
        ok, msg = icypeas.test_connection()
        print(f"icypeas {'ok' if ok else 'unavailable'}: {msg}")
    elif cmd == "add":
        cmd_add(argv[1])
    elif cmd == "known":
        print("\n".join(sorted(store.known_domains())))
    elif cmd == "progress":
        print(progress_line())
    elif cmd == "crawl":
        from .crawler import crawl
        print(json.dumps(crawl(store.normalize_domain(argv[1])), indent=2))
    elif cmd == "openings":
        cmd_openings(argv[1])
    elif cmd == "industry":
        print(industry_line("{agency}", " ".join(argv[1:])) or "no industry from the list")
    elif cmd == "restatus":
        cmd_restatus()
    elif cmd == "sheet-sync":
        from . import sheets
        err = sheets.sync(store.load_leads())
        print(f"google sheet {'synced' if not err else 'not synced: ' + err}")
    elif cmd == "export":
        from .export import export
        export()
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])

"""CLI.

  python -m leadtool test-icypeas        one credential check, result in icypeas_state.json
  python -m leadtool add batch.json      add or update agencies (list of dicts), saves after each
  python -m leadtool known               print domains already in leads.csv
  python -m leadtool progress            one-line progress
  python -m leadtool crawl example.com   direct site crawl (needs open web access)
  python -m leadtool export              leads.xlsx + SUMMARY.md
  python -m leadtool sheet-sync          push leads.csv to the Google Sheet now
"""
import json
import sys

from . import icypeas, store
from .compose import compose, guesses

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

    needs = []
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
            if email:  # step 4: the agency's general address
                row.update(email=email, email_source=f"generic | {d['email_source_url']}",
                           email_confidence="medium")
            else:
                needs.append("no published email and guesses unverified")
    if not name:
        needs.append("no named decision-maker found")

    first = name.split()[0] if name else ""
    row["subject"], row["email_body"] = compose(row["agency_name"], domain, first, d["hook"], d.get("subject"))
    row["status"] = "needs_check: " + "; ".join(needs) if needs else "ready"
    return row


def progress_line():
    rows = store.load_leads()
    q = [r for r in rows if store.is_qualified(r)]
    ready = sum(r["status"] == "ready" for r in q)
    generic = sum(r["status"] == "ready" and r["email_source"].startswith("generic") for r in q)
    return (f"qualified {len(q)}/{TARGET} | ready {ready} (generic {generic}) | "
            f"needs_check {len(q) - ready} | skipped {len(rows) - len(q)} | "
            f"icypeas credits used {icypeas.credits_used()}")


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
    elif cmd == "sheet-sync":
        from . import sheets
        err = sheets.sync(store.load_leads(), store.COLUMNS)
        print(f"google sheet {'synced' if not err else 'not synced: ' + err}")
    elif cmd == "export":
        from .export import export
        export()
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])

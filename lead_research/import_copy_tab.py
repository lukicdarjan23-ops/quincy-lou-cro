"""One-off (2026-10-06): bring the agencies from the sheet tab "Copy of leads" into leads.csv,
and remove every general inbox (info@, hello@ ...) from leads.csv.

"Copy of leads" is a copy of the third research pass (2026-09-24). It holds agency, website,
city, contact, email, email_source, guessed_unverified and status. The contact's source page is
not in that tab, so research_note says where each imported row came from.
"""
from leadtool import sheets, store

NOTE = "Imported from the sheet tab 'Copy of leads' (third research pass, 2026-09-24)."


def main():
    rows = store.load_leads()
    known = {r["domain"] for r in rows}
    tab = sheets._sheet("Copy of leads").get_all_values()
    header, added = tab[0], 0
    for values in tab[1:]:
        src = dict(zip(header, values))
        domain = store.normalize_domain(src.get("website", ""))
        if not domain or domain in known:
            continue
        row = {c: "" for c in store.COLUMNS}
        row.update(agency_name=src["agency_name"].strip(), website=src["website"].strip(), domain=domain,
                   city=store.with_state_code(src.get("city", "")), contact_name=src.get("contact_name", "").strip(),
                   email=src.get("email", "").strip().lower(), email_source=src.get("email_source", "").strip(),
                   guessed_unverified=src.get("guessed_unverified", "").strip(), research_note=NOTE)
        if row["email_source"] == "icypeas_verified":
            row["email_confidence"] = "high"
        elif row["email"] and not row["email_source"].startswith("generic"):
            row["email_confidence"] = "high" if domain in row["email_source"] else "medium"
        status = src.get("status", "")
        row["status"] = status if status.startswith("skip") else ""
        rows.append(row)
        known.add(domain)
        added += 1

    removed = 0
    for r in rows:
        if r.get("email_source", "").startswith("generic"):
            r.update(email="", email_source="", email_confidence="")
            removed += 1
        r["city"] = store.with_state_code(r.get("city", ""))
        r["status"] = store.lead_status(r)
    store.save_leads(rows)
    print(f"added {added} agencies, removed {removed} general inboxes")


if __name__ == "__main__":
    main()

"""Second pass over qualified rows using direct site crawls plus Icypeas.

Order per row (same as the brief):
  1. address published on the agency's own site (crawl_results.json)
  2. address found earlier by web search: kept only if the site shows it or Icypeas confirms it
  3. pattern guesses verified one at a time with Icypeas, stop at the first valid one
  4. otherwise the agency's general address from the site
Writes leads.csv after every row and logs each decision to recheck_log.csv.
"""
import csv
import json
import os
import re
import sys

from leadtool import icypeas, store
from leadtool.compose import ascii_slug, guesses

GENERIC = {"info", "hello", "contact", "support", "sales", "team", "office", "admin", "studio",
           "ideas", "help", "marketing", "careers", "jobs", "billing", "privacy", "webmaster",
           "mail", "inquiries", "enquiries", "design", "seo", "projects", "accounts", "talent",
           "payments", "quote", "press", "media", "noreply", "no-reply", "hi", "howdy", "service",
           "web", "general", "connect", "start", "newbusiness", "work", "legal", "hr"}
LOG = "recheck_log.csv"


def on_domain(addr, domain):
    host = addr.split("@")[-1]
    return host == domain or host.endswith("." + domain)


def is_generic(addr):
    return addr.split("@")[0] in GENERIC


def matches_person(addr, name):
    parts = [ascii_slug(p) for p in name.split() if ascii_slug(p)]
    if not parts:
        return False
    local = re.sub(r"[^a-z]", "", addr.split("@")[0])
    first, last = parts[0], parts[-1] if len(parts) > 1 else ""
    cands = {first}
    if last:
        cands |= {first + last, first[0] + last, last, last + first[0], first + last[0], first[0] + last[0]}
    return local in cands



def verify(addr):
    """True/False from Icypeas, or None when Icypeas is unavailable."""
    try:
        return icypeas.verify(addr)
    except icypeas.IcypeasUnavailable as e:
        icypeas.mark(False, str(e))
        print(f"  icypeas unavailable: {e}")
        return None


def main():
    crawl = json.load(open("crawl_results.json"))
    done = set()
    if os.path.exists(LOG):
        done = {r["domain"] for r in csv.DictReader(open(LOG))}
    log_new = not os.path.exists(LOG)
    logf = open(LOG, "a", newline="")
    log = csv.writer(logf)
    if log_new:
        log.writerow(["domain", "before_status", "before_email", "after_status", "after_email", "how"])

    rows = store.load_leads()
    for r in rows:
        if not store.is_qualified(r) or r["domain"] in done:
            continue
        domain, name = r["domain"], r["contact_name"]
        before = (r["status"], r["email"])
        site = crawl.get(domain, {})
        site_emails = {e: u for e, u in site.get("emails", {}).items() if on_domain(e, domain)}
        # addresses on another domain the agency itself publishes (e.g. inbuilds.com)
        if r["email"] and r["email"] in site.get("emails", {}):
            site_emails.setdefault(r["email"], site["emails"][r["email"]])
        how = ""

        personal_on_site = [e for e in site_emails if name and matches_person(e, name)]
        generic_on_site = sorted(e for e in site_emails if is_generic(e))

        if personal_on_site:
            e = personal_on_site[0]
            r.update(email=e, email_source=site_emails[e], email_confidence="high", guessed_unverified="")
            how = "owner's address published on own site"
        elif r["email"] and not r["email_source"].startswith("generic") and r["email_source"] != "icypeas_verified":
            # personal address found earlier through search
            if r["email"] in site_emails:
                r.update(email_source=site_emails[r["email"]], email_confidence="high")
                how = "search-found address confirmed on own site"
            else:
                ok = verify(r["email"])
                if ok:
                    r.update(email_source="icypeas_verified", email_confidence="high")
                    how = "search-found address confirmed by Icypeas"
                elif ok is False:
                    r["guessed_unverified"] = r["email"]
                    r.update(email="", email_source="", email_confidence="")
                    how = "search-found address rejected by Icypeas"
                else:
                    how = "icypeas unavailable, left as is"
        if not how or how == "search-found address rejected by Icypeas":
            # step 3, pattern guesses with Icypeas
            cands = guesses(name, domain) if name else []
            verified, tried = None, []
            for c in cands:
                ok = verify(c)
                if ok is None:
                    break
                tried.append(c)
                if ok:
                    verified = c
                    break
            if verified:
                r.update(email=verified, email_source="icypeas_verified", email_confidence="high",
                         guessed_unverified="")
                how = (how + "; " if how else "") + f"Icypeas confirmed {verified} after {len(tried)} tries"
            else:
                r["guessed_unverified"] = "; ".join(c for c in cands if c not in tried) if tried else "; ".join(cands)
                if tried:
                    r["guessed_unverified"] = ("rejected by Icypeas: " + ", ".join(tried) +
                                               ("; untried: " + r["guessed_unverified"] if r["guessed_unverified"] else ""))
                # step 4, general address
                if generic_on_site:
                    g = next((x for x in generic_on_site if x.startswith(("hello", "info", "contact"))), generic_on_site[0])
                    r.update(email=g, email_source=f"generic | {site_emails[g]}", email_confidence="medium")
                    how = (how + "; " if how else "") + "general address from own site"
                elif r["email"]:
                    how = (how + "; " if how else "") + "kept general address found earlier (not seen on site)"
                else:
                    how = (how + "; " if how else "") + "no address found"

        needs = []
        if not r["email"]:
            needs.append("no published email and no Icypeas-confirmed address")
        if not name:
            needs.append("no named decision-maker found")
        r["status"] = "needs_check: " + "; ".join(needs) if needs else "ready"
        store.save_leads(rows)
        log.writerow([domain, before[0], before[1], r["status"], r["email"], how])
        logf.flush()
        print(f"{domain}: {how} -> {r['status']} {r['email']} | credits {icypeas.credits_used()}")
    logf.close()


if __name__ == "__main__":
    sys.exit(main())

"""Verify the pattern guesses left in guessed_unverified while Icypeas was unavailable.

For each qualified row whose guesses were never tried, check them one at a time
with Icypeas and stop at the first ultra_sure/sure result. A confirmed guess
becomes the email; the general address it replaces is noted in research_note.
Rows whose guesses Icypeas already rejected are left alone.
Writes leads.csv after every row and logs each decision to recheck_log.csv.
"""
import csv
import sys

from leadtool import icypeas, store
from recheck import verify

LOG = "recheck_log.csv"


def main():
    rows = store.load_leads()
    logf = open(LOG, "a", newline="")
    log = csv.writer(logf)
    for r in rows:
        g = r["guessed_unverified"].strip()
        if not store.is_qualified(r) or not g or g.startswith("rejected by Icypeas"):
            continue
        cands = [c.strip() for c in g.split(";") if "@" in c]
        before = (r["status"], r["email"])
        verified, tried, stopped = None, [], False
        for c in cands:
            ok = verify(c)
            if ok is None:
                stopped = True
                break
            tried.append(c)
            if ok:
                verified = c
                break
        if verified:
            if r["email"] and r["email"] != verified:
                note = f"general address {r['email']} replaced by Icypeas-confirmed {verified}"
                r["research_note"] = (r["research_note"] + "; " if r["research_note"] else "") + note
            r.update(email=verified, email_source="icypeas_verified", email_confidence="high",
                     guessed_unverified="")
            how = f"Icypeas confirmed {verified} after {len(tried)} tries"
        elif tried:
            rest = [c for c in cands if c not in tried]
            r["guessed_unverified"] = ("rejected by Icypeas: " + ", ".join(tried) +
                                       ("; untried: " + "; ".join(rest) if rest else ""))
            how = "Icypeas rejected all guesses, kept current address" if r["email"] else "Icypeas rejected all guesses"
        else:
            how = "icypeas unavailable, left as is"
        if r["email"] and r["contact_name"]:
            r["status"] = "ready"
        store.save_leads(rows)
        log.writerow([r["domain"], before[0], before[1], r["status"], r["email"], how])
        logf.flush()
        print(f"{r['domain']}: {how} -> {r['status']} {r['email']} | credits {icypeas.credits_used()}", flush=True)
        if stopped:
            print("stopping: Icypeas unavailable")
            break
    logf.close()


if __name__ == "__main__":
    sys.exit(main())

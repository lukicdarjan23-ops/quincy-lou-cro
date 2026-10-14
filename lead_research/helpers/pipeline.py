"""Domain list in, short table out. Does every free check so Claude (and Icypeas) only see what can still qualify.

  python helpers/pipeline.py LIST.txt            LIST has one domain per line
Writes /tmp/leadwork/pipeline.json (all facts) and /tmp/leadwork/guess_queue.txt ("Full Name|domain" for guess_names.py).
Order, cheapest first, and a domain is dropped at the first failure:
  known in leads.csv -> site opens -> sells web design -> not solo -> not big -> MX exists -> owner name -> owner address on site
Only the survivors are printed, one line each. Dropped domains are printed as one summary line per reason.
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from leadtool import store
from leadtool.compose import ascii_slug
from leadtool.crawler import UA
from mx import has_mx

W = "/tmp/leadwork"; OUT = f"{W}/out"; os.makedirs(OUT, exist_ok=True)
SOLO = re.compile(r"\b(one[- ]person|solo|freelanc\w+|one[- ]man|I'?m a (web )?designer|sole proprietor)\b", re.I)
TEAMLINK = re.compile(r"/(about|team|our-team|meet|people|who-we-are|leadership|our-story)[^/]*/?$", re.I)
ROLE = r"(?:Co-?)?(?:Founder|Owner|CEO|President|Principal|Managing Partner|Partner)"
NAME = r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-zA-Z'\-]+)"
BAD = re.compile(r"[“”\"]|testimonial|review|\bof [A-Z]|\bat [A-Z]|Owner,|CEO,|Founder,", re.I)


def triage(d):
    f = f"{OUT}/{d}.txt"
    if not os.path.exists(f):
        with open(f, "w") as fh:
            subprocess.run([sys.executable, f"{HERE}/triage.py", d], stdout=fh, stderr=subprocess.STDOUT, timeout=150)
    return open(f).read().splitlines()


def size_and_city(d):
    """(solo?, head count, city) from the team/about page and the home page."""
    heads, solo, city = 0, False, ""
    try:
        r = requests.get(f"https://{d}/", headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            r = requests.get(f"https://www.{d}/", headers={"User-Agent": UA}, timeout=20)
        s = BeautifulSoup(r.text, "html.parser")
        txt = re.sub(r"\s+", " ", s.get_text(" ", strip=True))
        m = re.findall(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?),? ((?:AL|AZ|AR|CA|CO|CT|DC|DE|FL|GA|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|ON|BC|AB|QC|NS|NB|SK|MB))[ ,]+\d?", txt)
        STOP = {"Ave", "Avenue", "Street", "St", "Road", "Rd", "Suite", "Blvd", "Company", "Review", "Full", "Plaza", "Drive", "Dr", "Way", "Lane", "Ln", "Ter", "Floor", "Markets", "Pros", "Design"}
        good = [(" ".join(w for w in c.split() if w not in STOP), st) for c, st in m]
        good = [g for g in good if g[0]]
        city = f"{good[0][0]}, {good[0][1]}" if good else ""
        team = [urljoin(r.url, a["href"]).split("#")[0] for a in s.select("a[href]")]
        team = [t for t in team if TEAMLINK.search(t) and d in t]
        if team:
            rr = requests.get(team[0], headers={"User-Agent": UA}, timeout=20)
            t = BeautifulSoup(rr.text, "html.parser")
            for x in t(["script", "style", "nav", "footer", "header"]): x.decompose()
            ttxt = re.sub(r"\s+", " ", t.get_text(" ", strip=True))
            heads = len(t.select("h2,h3,h4,h5"))
            solo = bool(SOLO.search(ttxt[:1500])) and heads < 8
    except Exception:
        pass
    return solo, heads, city


def owner_of(lines):
    cands = []
    for l in lines:
        if not l.startswith("  OWN") or BAD.search(l):
            continue
        for m in re.finditer(NAME + r"[,\s]+(" + ROLE + r")\b", l): cands.append((m.group(1), m.group(2)))
        for m in re.finditer(r"\b(" + ROLE + r")[\s:·|,-]{1,4}" + NAME, l): cands.append((m.group(2), m.group(1)))
    bad_first = {"Meet", "Call", "Email", "Contact", "Our", "Founder", "Owner", "President", "Hi", "About", "Team", "Learn", "More", "West", "East", "North", "South", "Full", "Read", "View", "Get", "Free", "Company", "Business", "Marketing", "Digital", "Web", "Design", "Click", "Book", "Schedule"}
    cands = [c for c in cands if c[0].split()[0] not in bad_first and c[0].split()[-1] not in bad_first]
    return cands[0] if cands else None


def run(d):
    if d in KNOWN: return d, "known", None
    lines = triage(d)
    if not lines or "HOME FAIL" in lines[0]: return d, "site does not open (or bot protection)", None
    svc = [l for l in lines if l.startswith(" svc:")]
    if not svc or svc[0].split("|")[0].strip() == "svc: []": return d, "no web design service page found", None
    solo, heads, city = size_and_city(d)
    if solo: return d, "looks solo (first person, one person)", None
    if heads > 40: return d, f"too big ({heads} headings on team page)", None
    mx = has_mx(d)
    if mx is False: return d, "domain has no MX record", None
    own = owner_of(lines)
    if not own: return d, "no owner name found on site", None
    pe = [l for l in lines if l.startswith(" personal")]
    emails = {}
    if pe:
        import ast
        try: emails = ast.literal_eval(pe[0].split(": ", 1)[1])
        except Exception: pass
    fn, ln = ascii_slug(own[0].split()[0]), ascii_slug(own[0].split()[-1])
    ok = {fn, fn + ln, fn[:1] + ln, fn + "." + ln, fn + ln[:1], ln}
    onsite = next((e for e in emails if e.split("@")[0].lower().replace("%20", "") in ok), "")
    flags = [l.strip()[:3] for l in lines if l.startswith(("  HOB", "  AWARD", "  JOB", "  IND"))]
    return d, "ok", dict(domain=d, owner=own[0], role=own[1], city=city, heads=heads, onsite=onsite,
                         svc=svc[0].split("[")[1].split("]")[0].split(",")[0].strip(" '"), flags=sorted(set(flags)))


if __name__ == "__main__":
    KNOWN = store.known_domains()
    doms = [x.strip() for x in open(sys.argv[1]).read().split() if x.strip()]
    with ThreadPoolExecutor(10) as ex: res = list(ex.map(run, doms))
    keep = [r[2] for r in res if r[1] == "ok"]
    drops = {}
    for d, why, _ in res:
        if why != "ok": drops.setdefault(why, []).append(d)
    json.dump(keep, open(f"{W}/pipeline.json", "w"), indent=1)
    with open(f"{W}/guess_queue.txt", "w") as q:
        for k in keep:
            if not k["onsite"]: q.write(f"{k['owner']}|{k['domain']}\n")
    print(f"{len(doms)} domains, {len(keep)} survive")
    for k in keep:
        print(f"{k['domain']} | {k['city'] or '?'} | {k['owner']} ({k['role']}) | heads {k['heads']} | "
              f"{'ONSITE ' + k['onsite'] if k['onsite'] else 'needs guess'} | {','.join(k['flags'])}")
    for why, ds in drops.items():
        print(f"dropped, {why}: {len(ds)}")

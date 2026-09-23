"""Direct site crawler: robots.txt aware, collects emails and service signals.

Used by `python -m leadtool crawl <domain>` when the machine has open web
access. In the sandbox this tool was built in, outbound HTTP was blocked, so
the research for the first run went through web search instead (see
DECISIONS.md).
"""
import re
import time
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "evie-lead-research/1.0 (+https://evie.design)"
PAGES = ["", "services", "contact", "about", "about-us", "team", "our-team",
         "privacy-policy", "privacy", "terms", "careers"]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
WEB_SERVICE_RE = re.compile(r"web(site)?\s*(design|redesign)|website development|web development", re.I)
NOT_EMAIL_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")


def _robots(base):
    rp = robotparser.RobotFileParser()
    try:
        r = requests.get(urljoin(base, "/robots.txt"), headers={"User-Agent": UA}, timeout=15)
        rp.parse(r.text.splitlines() if r.status_code == 200 else [])
    except requests.RequestException:
        rp.parse([])
    return rp


def crawl(domain, delay=1.0):
    base = f"https://{domain}/"
    rp = _robots(base)
    found = {"emails": {}, "services_url": "", "offers_websites": False, "pages": []}
    for path in PAGES:
        url = urljoin(base, path)
        if not rp.can_fetch(UA, url):
            continue
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        except requests.RequestException:
            continue
        if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
            continue
        found["pages"].append(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select('a[href^="mailto:"]'):
            addr = a["href"][7:].split("?")[0].strip().lower()
            if addr:
                found["emails"].setdefault(addr, url)
        for addr in EMAIL_RE.findall(soup.get_text(" ")):
            addr = addr.lower()
            if not addr.endswith(NOT_EMAIL_SUFFIX):
                found["emails"].setdefault(addr, url)
        if WEB_SERVICE_RE.search(soup.get_text(" ")):
            found["offers_websites"] = True
            if "service" in urlparse(url).path and not found["services_url"]:
                found["services_url"] = url
        time.sleep(delay)
    return found

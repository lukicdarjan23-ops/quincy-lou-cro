"""Email guesses and the house style for opening lines.

The email itself (versions, subjects, signature) lives in the evie outreach app,
which fills in each agency's opening line. Copy rules from Darjan: no em dashes,
no colons, plain conversational tone, one specific reference per agency.
"""
import re
import unicodedata


def ascii_slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def guesses(full_name, domain, limit=2):
    parts = [ascii_slug(p) for p in full_name.split() if ascii_slug(p)]
    if len(parts) < 2:
        return [f"{parts[0]}@{domain}"] if parts else []
    first, last = parts[0], parts[-1]
    # 14 Oct 2026 sample of 24 confirmed addresses: 19 were first@, 5 were flast@, none first.last@ or firstlast@.
    # So only these two are tried by default (2 credits for a miss instead of 5).
    formats = [f"{first}", f"{first[0]}{last}", f"{first}.{last}", f"{first}{last}", f"{first[0]}.{last}"]
    return [f"{f}@{domain}" for f in formats[:limit]]


def clean_opening(text):
    """House style for the personal line: no em dashes, no colons."""
    text = (text or "").replace("\u2014", ",").replace("\u2013", "-").replace(":", ",")
    return re.sub(r"\s+", " ", re.sub(r"\s+,", ",", text)).strip()

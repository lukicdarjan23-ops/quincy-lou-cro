"""Email guesses and outreach copy.

Copy rules from Darjan: no em dashes, no colons in the subject or the personal
opening line, plain conversational tone, one specific reference per agency.
"""
import hashlib
import re
import unicodedata

SUBJECTS = [
    "Design help for {agency} client sites",
    "Extra design capacity for {agency}",
    "White-label web design for {agency}",
]


def _pick(options, key):
    return options[int(hashlib.md5(key.encode()).hexdigest(), 16) % len(options)]


def ascii_slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def guesses(full_name, domain, limit=5):
    parts = [ascii_slug(p) for p in full_name.split() if ascii_slug(p)]
    if len(parts) < 2:
        return [f"{parts[0]}@{domain}"] if parts else []
    first, last = parts[0], parts[-1]
    formats = [f"{first}", f"{first}.{last}", f"{first}{last}", f"{first[0]}{last}", f"{first[0]}.{last}"]
    return [f"{f}@{domain}" for f in formats[:limit]]


def clean(text):
    text = text.replace("—", ",").replace("–", "-").replace(":", ",")
    return re.sub(r"\s+,", ",", text)


# Same text as the intro template in the evie outreach app (Settings), which is
# what actually gets sent. email_body here is a preview for the sheet.
INTRO_TEMPLATE = """Hey {first_name},

{opening}

That's actually why I'm emailing. I run evie.design, a white label partner for agencies. Design only, no dev, and everything's made to match your client's brand rather than pulled from a template. You get clean Figma files your team can build straight from. Your client never even knows we exist, it's all under your name.

Some agencies bring me in just for the overflow weeks. Some keep me running alongside their own designer so nobody's drowning. A few just let me handle design entirely so they're not stuck hiring for it. Whatever setup works for you, I'll fit into it.

I've been doing this for years now. Here's what Chris Castillo, SEO Specialist and CEO of PDMS, had to say after a few years of working together.

"Darjan makes my job so much easier, five years in and we're still working with him. He knows our clients, our voice, our standards, and his attention to detail is exactly why we keep coming back. Our clients' results have noticeably improved with the conversion-focused work he produces."

If it's worth 20 minutes, [grab a slot here](https://cal.com/evie.design/20min), or just hit reply and we'll figure out a time.

Cheers,
Darjan

P.S. You can see my work [here](https://evie.design)"""

MISSING_OPENING = "[OPENING LINE MISSING, write one sentence about their work]"


def clean_opening(text):
    """House style for the personal line: no em dashes, no colons."""
    text = (text or "").replace("\u2014", ",").replace("\u2013", "-").replace(":", ",")
    return re.sub(r"\s+", " ", re.sub(r"\s+,", ",", text)).strip()


def compose(agency, domain, first_name, opening="", subject=None):
    """Subject plus a preview of the intro. Links stay as [text](url); the app turns them into real links."""
    greeting_name = first_name or f"{agency} team"
    body = (INTRO_TEMPLATE
            .replace("{first_name}", greeting_name)
            .replace("{opening}", clean_opening(opening) or MISSING_OPENING))
    subj = subject or _pick(SUBJECTS, domain + "s").format(agency=agency)
    return clean(subj), body

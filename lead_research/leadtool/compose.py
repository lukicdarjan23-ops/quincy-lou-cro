"""Email guesses and outreach copy.

Copy rules from Darjan: no em dashes, no colons anywhere in subject or body,
plain conversational tone, one specific reference per agency.
"""
import hashlib
import re
import unicodedata

PITCHES = [
    (
        "I run evie.design. We're a white-label design partner for agencies, so we design "
        "fully custom websites under your name and hand over clean Figma files your own "
        "developers build from. No templates, and we stay out of development entirely."
    ),
    (
        "I'm Darjan from evie.design. We work behind the scenes for agencies, designing "
        "custom websites that go out under your brand. You get organized Figma files and "
        "your developers take it from there. Everything is designed from scratch, no themes."
    ),
    (
        "Quick intro, I'm Darjan and I run evie.design. Agencies bring us in as their "
        "white-label design team. We design the site in Figma, fully custom, and your devs "
        "build it. We don't do development, so we never step on your team's toes."
    ),
]

OFFER = (
    "Most partners use a monthly retainer with no long-term contract, which works out "
    "cheaper per task than paying one-off. If you'd rather go project by project, that "
    "works too."
)

CLOSES = [
    "Would it help if I sent a couple of recent Figma files so you can see what your developers would get?",
    "Open to a quick look at some recent work? I can send a few Figma files over, no call needed.",
    "If extra design capacity would be useful this quarter, happy to send a few examples your way.",
]

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


def compose(agency, domain, first_name, hook, subject=None):
    greeting = f"Hi {first_name}," if first_name else f"Hi {agency} team,"
    body = "\n\n".join([
        greeting,
        hook.strip(),
        _pick(PITCHES, domain),
        OFFER,
        _pick(CLOSES, domain + "c"),
        "Darjan\nevie.design",
    ])
    subj = subject or _pick(SUBJECTS, domain + "s").format(agency=agency)
    return clean(subj), clean(body)

"""Industry angle (version E in the outreach app): the agency says on its own site that it builds
websites for one or two industries Darjan has designed for. The tool writes the opening line, so every
E lead reads the same way and only the industry changes.

Order, narrowest first (Darjan, 7 Oct 2026):
  1. one or two industries from the list below, in the agency's own words or any other name for them
  2. "home service businesses", when the agency says "home services", or names three or more
     industries that are all home services
  3. "small businesses", only when that is what the agency says it builds for
Anything else (three or more mixed industries, nothing from the list) is not a specialist: no E.
"""
import re

# (name used in the sentence, other names recognised on the agency's site, home service?)
INDUSTRIES = [
    ("construction companies", ["construction", "contractor", "contractors", "general contractor", "general contractors", "builders"], False),
    ("renovation companies", ["renovation", "renovations", "remodeling", "remodelling", "remodeler", "remodelers"], True),
    ("dental practices", ["dentist", "dentists", "dental", "dental practice", "dental practices", "dental clinic", "dental clinics",
                          "orthodontist", "orthodontists", "orthodontic", "orthodontics"], False),
    ("clinics", ["clinic", "clinics", "medical clinic", "medical clinics"], False),
    ("auto detailing businesses", ["auto detailing", "car detailing", "detailing", "detailer", "detailers", "auto detailer", "auto detailers"], False),
    ("law firms", ["lawyer", "lawyers", "law firm", "law firms", "attorney", "attorneys", "legal", "law practice", "law practices"], False),
    ("veterinary clinics", ["vet", "vets", "veterinarian", "veterinarians", "veterinary", "veterinary clinic", "veterinary clinics",
                            "animal hospital", "animal hospitals", "pet doctor", "pet doctors"], False),
    ("medical practices", ["doctor", "doctors", "physician", "physicians", "medical practice", "medical practices"], False),
    ("healthcare providers", ["healthcare", "health care", "healthcare provider", "healthcare providers"], False),
    ("heavy equipment companies", ["heavy machinery", "heavy equipment", "equipment dealer", "equipment dealers"], False),
    ("financial firms", ["financial", "finance", "financial advisor", "financial advisors", "wealth management", "credit union", "credit unions"], False),
    ("landscaping companies", ["landscaping", "landscaper", "landscapers", "landscape", "lawn care", "hardscaping"], True),
    ("real estate businesses", ["real estate", "realtor", "realtors", "real estate agent", "real estate agents", "brokerage", "brokerages"], False),
    ("home builders", ["home builder", "home builders", "homebuilder", "homebuilders", "housing"], False),
    ("education centers", ["education center", "education centers", "learning center", "learning centers", "tutoring", "training center", "training centers"], False),
    ("plumbing companies", ["plumber", "plumbers", "plumbing"], True),
    ("HVAC companies", ["hvac", "heating and cooling", "heating and air", "air conditioning", "ac repair"], True),
    ("restoration companies", ["restoration", "water damage", "fire damage", "mold remediation"], True),
    ("farms", ["farm", "farms", "agriculture", "agricultural", "ranch", "ranches"], False),
    ("internet providers", ["internet provider", "internet providers", "internet service provider", "internet service providers", "isp", "isps", "broadband"], False),
    ("gyms and fitness studios", ["gym", "gyms", "fitness", "fitness center", "fitness centers", "fitness studio", "fitness studios", "personal trainer", "personal trainers"], False),
    ("solar companies", ["solar", "solar installer", "solar installers"], True),
    ("lighting companies", ["lighting"], False),
    ("accounting firms", ["accountant", "accountants", "accounting", "cpa", "cpas", "bookkeeping", "bookkeeper", "bookkeepers"], False),
    ("pest control companies", ["pest control", "exterminator", "exterminators", "termite"], True),
    ("restaurants", ["restaurant", "restaurants"], False),
    ("insurance agencies", ["insurance", "insurance agent", "insurance agents", "insurance agency", "insurance agencies"], False),
]
HOME_SERVICES = "home service businesses"
SMALL_BUSINESS = "small businesses"
HOME_WORDS = ["home services", "home service", "home service businesses", "home service companies"]
SMALL_WORDS = ["small business", "small businesses"]


def _pattern(words):
    return re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r")\b", re.I)


_ALL = [(w, i) for i, (_, words, _) in enumerate(INDUSTRIES) for w in words]
_ANY = _pattern([w for w, _ in _ALL])
_OWNER = {w.lower(): i for w, i in _ALL}
_HOME = _pattern(HOME_WORDS)
_SMALL = _pattern(SMALL_WORDS)


def industries_in(text):
    """Industries named in the text, in order of first mention. The longest name wins, so
    "dental clinic" is dental practices, not clinics too."""
    found = []
    for m in _ANY.finditer(text or ""):
        i = _OWNER[m.group(1).lower()]
        if i not in found:
            found.append(i)
    return found


def detect(text):
    """What the agency says it builds for (a sentence from its own site) -> the name for the
    opening line, or "" when it is not a specialist in something Darjan has designed for."""
    found = industries_in(text)
    if 1 <= len(found) <= 2:
        return " and ".join(INDUSTRIES[i][0] for i in found)
    if found and all(INDUSTRIES[i][2] for i in found):
        return HOME_SERVICES
    if _HOME.search(text or ""):
        return HOME_SERVICES
    if not found and _SMALL.search(text or ""):
        return SMALL_BUSINESS
    return ""


def opening_line(agency, text):
    """The E opening line, or "" when the text shows no specialism from the list."""
    name = detect(text)
    return f"Noticed {agency.strip()} focuses on websites for {name}." if name else ""

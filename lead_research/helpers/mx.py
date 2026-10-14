"""Free MX check over DNS-over-HTTPS (plain DNS is blocked in the cloud sandbox). A domain with no MX cannot get mail,
so spending an Icypeas credit on it is wasted."""
import requests

def has_mx(domain, timeout=10):
    """True/False, or None when the lookup itself failed (then do not block the guess)."""
    try:
        r = requests.get("https://dns.google/resolve", params={"name": domain, "type": "MX"},
                         headers={"accept": "application/dns-json"}, timeout=timeout)
        j = r.json()
    except Exception:
        return None
    return bool(j.get("Answer"))

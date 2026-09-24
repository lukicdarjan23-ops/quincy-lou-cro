"""Icypeas email verification client.

Per the Icypeas API docs (api-doc.icypeas.com), requests only need the API key
in the Authorization header. The secret and user id are loaded but unused.
Endpoints:
  POST https://app.icypeas.com/api/email-verification   {"email": ...}
  POST https://app.icypeas.com/api/bulk-single-searchs/read   {"id": ...}
A search is finished once its status leaves NONE / SCHEDULED / IN_PROGRESS
(observed: FOUND).
We only treat an address as valid when Icypeas returns it with certainty
"ultra_sure" or "sure".
"""
import json
import os
import time

import requests

from .config import settings

BASE = "https://app.icypeas.com/api"
STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icypeas_state.json")
VALID_CERTAINTY = {"ultra_sure", "sure"}
# Anything outside these means the search has finished (FOUND, DEBITED, NOT_FOUND, ...).
PENDING_STATUSES = {"NONE", "SCHEDULED", "IN_PROGRESS"}


class IcypeasUnavailable(Exception):
    pass


def _state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"available": None, "credits_used": 0, "note": ""}


def _save_state(s):
    with open(STATE, "w") as f:
        json.dump(s, f, indent=2)


def credits_used():
    return _state().get("credits_used", 0)


def is_available():
    return _state().get("available") is True


def mark(available, note):
    s = _state()
    s["available"] = available
    s["note"] = note
    _save_state(s)


def _headers():
    key = settings()["ICYPEAS_API_KEY"]
    if not key:
        raise IcypeasUnavailable("ICYPEAS_API_KEY missing")
    return {"Authorization": key, "Content-Type": "application/json"}


def _post(path, payload):
    try:
        r = requests.post(f"{BASE}/{path}", headers=_headers(), json=payload, timeout=30)
    except requests.RequestException as e:
        # Never include headers in the message, they carry the key.
        raise IcypeasUnavailable(f"network error: {type(e).__name__}") from None
    if r.status_code in (401, 403):
        raise IcypeasUnavailable(f"HTTP {r.status_code} from Icypeas (auth or proxy)")
    if r.status_code == 402:
        raise IcypeasUnavailable("out of credits")
    if r.status_code >= 400:
        raise IcypeasUnavailable(f"HTTP {r.status_code}")
    return r.json()


def verify(email, poll_seconds=3, max_wait=90):
    """Return True if Icypeas confirms the address, False otherwise.

    Raises IcypeasUnavailable on network, auth or credit problems.
    """
    data = _post("email-verification", {"email": email})
    item = data.get("item") or {}
    search_id = item.get("_id")
    if not data.get("success") or not search_id:
        raise IcypeasUnavailable("unexpected response from email-verification")
    s = _state()
    s["credits_used"] = s.get("credits_used", 0) + 1
    _save_state(s)

    waited = 0
    while waited <= max_wait:
        res = _post("bulk-single-searchs/read", {"id": search_id})
        items = res.get("items") or []
        if items:
            status = items[0].get("status", "")
            if status == "INSUFFICIENT_FUNDS":
                raise IcypeasUnavailable("out of credits")
            if status not in PENDING_STATUSES:
                emails = (items[0].get("results") or {}).get("emails") or []
                return any(
                    e.get("email", "").lower() == email.lower()
                    and e.get("certainty") in VALID_CERTAINTY
                    for e in emails
                )
        time.sleep(poll_seconds)
        waited += poll_seconds
    return False


def test_connection():
    """One cheap call to confirm credentials work. Records the outcome."""
    try:
        # Reading an unknown id costs no credit but still exercises auth.
        _post("bulk-single-searchs/read", {"id": "credential-check"})
        mark(True, "test call ok")
        return True, "ok"
    except IcypeasUnavailable as e:
        mark(False, str(e))
        return False, str(e)

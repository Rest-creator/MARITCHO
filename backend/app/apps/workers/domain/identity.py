"""Identity-document rules (ADR-010). Pure functions, no framework."""

import hashlib
import hmac
import re
import uuid
from datetime import date, timedelta

# Zimbabwe national ID: 2-digit district of registration, 6 or 7 digits,
# one check letter, 2-digit district of origin (e.g. 08-2047823 Q 29).
_ZIM_ID = re.compile(r"^(\d{2})(\d{6,7})([A-Z])(\d{2})$")
_MEDIA_PATH = re.compile(r"^/media/([0-9a-fA-F-]{36})$")

POLICE_CLEARANCE_VALID_DAYS = 365


def normalize_zim_id_number(raw: str) -> str | None:
    """`08-2047823 q 29` -> `082047823Q29`, or None if it isn't that layout."""
    compact = re.sub(r"[\s\-/]", "", raw).upper()
    return compact if _ZIM_ID.match(compact) else None


def hash_id_number(normalized: str, key: bytes) -> str:
    """Keyed hash so a national ID can be matched for duplicates without
    the number itself ever being stored."""
    return hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def media_id_from_url(url: str) -> uuid.UUID | None:
    """`/media/<uuid>` (what POST /media/upload returns) -> the id; else None."""
    match = _MEDIA_PATH.match(url.strip())
    if match is None:
        return None
    try:
        return uuid.UUID(match.group(1))
    except ValueError:
        return None


def police_clearance_expiry(issued_on: date) -> date:
    return issued_on + timedelta(days=POLICE_CLEARANCE_VALID_DAYS)

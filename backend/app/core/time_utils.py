from datetime import datetime
from typing import Optional


def iso_utc(dt: Optional[datetime]) -> Optional[str]:
    """Serialize a naive UTC datetime (from datetime.utcnow()) with an explicit
    'Z' suffix, so JS `new Date(...)` on the frontend parses it as UTC instead
    of local time — without this, a value like "2026-11-22T13:19:44" gets
    misread as 13:19:44 in the browser's own timezone, silently shifting
    every deadline/timestamp by the browser's UTC offset.
    """
    if dt is None:
        return None
    return dt.isoformat() + "Z"

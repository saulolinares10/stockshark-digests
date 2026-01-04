from __future__ import annotations
from datetime import datetime
import pytz

def now_in_tz(tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)

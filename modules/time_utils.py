# modules/time_utils.py
from datetime import datetime, timezone
import pytz

ARMENIA_TZ = pytz.timezone("Asia/Yerevan")

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def parse_iso_or_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            # DB datetime → treat as UTC
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(ARMENIA_TZ)

    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(ARMENIA_TZ)
        except:
            return None

    return None

# modules/time_utils.py  (add or replace)

def format_armenia_date_only(dt) -> str:
    """Only date: DD.MM.YYYY"""
    local = parse_iso_or_datetime(dt)
    if local is None:
        return "—"
    return local.strftime("%d.%m.%Y")

def format_armenia_datetime(dt) -> str:
    """Date + time in Yerevan timezone"""
    local = parse_iso_or_datetime(dt)
    if local is None:
        return "—"
    return local.strftime("%d.%m.%Y %H:%M")

def format_armenia_datetime_short(dt) -> str:
    """Date + very short time if needed (but we won't use time anymore)"""
    return format_armenia_date_only(dt)
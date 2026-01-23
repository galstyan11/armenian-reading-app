from datetime import datetime, timezone
import pytz

# Armenia timezone (Asia/Yerevan = UTC+4, no DST since 2012)
ARMENIA_TZ = pytz.timezone("Asia/Yerevan")


# ── Creation / Storage ────────────────────────────────────────

def now_utc() -> datetime:
    """Current time in UTC (timezone-aware)"""
    return datetime.now(timezone.utc)


def iso_now_utc() -> str:
    """ISO 8601 string in UTC – ready for JSON"""
    return now_utc().isoformat()


# ── Parsing ────────────────────────────────────────────────────

def parse_iso(dt_str: str) -> datetime:
    """Parse ISO string → timezone-aware UTC datetime"""
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ── Conversion ─────────────────────────────────────────────────

def to_armenia(dt: datetime) -> datetime:
    """Convert datetime (aware or naive) → Asia/Yerevan"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ARMENIA_TZ)


# ── Formatting for UI ──────────────────────────────────────────

def format_armenia(dt: datetime, with_seconds: bool = False) -> str:
    """Format as YYYY-MM-DD HH:MM   (seconds optional)"""
    local = to_armenia(dt)
    if with_seconds:
        return local.strftime("%Y-%m-%d %H:%M:%S")
    return local.strftime("%Y-%m-%d %H:%M")


def format_armenia_date_only(dt: datetime) -> str:
    """Just date: YYYY-MM-DD"""
    return to_armenia(dt).strftime("%Y-%m-%d")
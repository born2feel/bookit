from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

type Clock = Callable[[], datetime]


def system_clock() -> datetime:
    return datetime.now(UTC)


def local_today(now: datetime, tz: ZoneInfo) -> date:
    return now.astimezone(tz).date()


def local_day_bounds(day: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """Bounds of a local day [00:00, next day 00:00) in UTC."""
    start = datetime.combine(day, time.min, tzinfo=tz)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)
    return start.astimezone(UTC), end.astimezone(UTC)

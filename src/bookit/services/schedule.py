import logging
from collections.abc import Sequence
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from bookit.config import ScheduleConfig
from bookit.db.models import DayOff
from bookit.repositories import BookingRepository, DayOffRepository
from bookit.services.exceptions import (
    DayHasBookingsError,
    DayOffExistsError,
    DayOffNotFoundError,
    ValidationError,
)
from bookit.services.time_utils import Clock, local_day_bounds, local_today, system_clock

logger = logging.getLogger(__name__)

REASON_MAX_LENGTH = 255


def parse_date(text: str, today: date) -> date:
    """Parses "DD.MM.YYYY" or "DD.MM" (the current year is assumed)."""
    value = text.strip()
    if value.count(".") == 1:
        # add the year before parsing, otherwise 29.02 fails (1900 is not a leap year)
        value = f"{value}.{today.year}"
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        raise ValidationError("validation.date_format") from None


class ScheduleService:
    def __init__(
        self, session: AsyncSession, cfg: ScheduleConfig, clock: Clock = system_clock
    ) -> None:
        self._session = session
        self._cfg = cfg
        self._clock = clock
        self._days_off = DayOffRepository(session)
        self._bookings = BookingRepository(session)

    def today(self) -> date:
        return local_today(self._clock(), self._cfg.tz)

    def upcoming_dates(self) -> list[date]:
        """All dates within the booking horizon starting today (for the admin view)."""
        today = self.today()
        return [today + timedelta(days=offset) for offset in range(self._cfg.horizon_days)]

    async def list_upcoming(self) -> Sequence[DayOff]:
        return await self._days_off.list_from(self.today())

    async def ensure_can_add_day_off(self, day: date) -> None:
        if day < self.today():
            raise ValidationError("validation.day_off_in_past")
        if await self._days_off.get_by_day(day) is not None:
            raise DayOffExistsError

        start, end = local_day_bounds(day, self._cfg.tz)
        bookings_count = await self._bookings.count_active_overlapping(start, end)
        if bookings_count:
            raise DayHasBookingsError(bookings_count)

    async def add_day_off(self, day: date, reason: str | None = None) -> DayOff:
        await self.ensure_can_add_day_off(day)

        cleaned_reason = " ".join((reason or "").split()) or None
        if cleaned_reason and len(cleaned_reason) > REASON_MAX_LENGTH:
            raise ValidationError("validation.reason_too_long", max=REASON_MAX_LENGTH)

        day_off = await self._days_off.add(DayOff(day=day, reason=cleaned_reason))
        await self._session.commit()
        logger.info("Day off added %s", day.isoformat())
        return day_off

    async def remove_day_off(self, day_off_id: int) -> None:
        day_off = await self._days_off.get(day_off_id)
        if day_off is None:
            raise DayOffNotFoundError
        await self._days_off.delete(day_off)
        await self._session.commit()
        logger.info("Day off removed %s", day_off.day.isoformat())

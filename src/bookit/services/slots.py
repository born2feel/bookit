from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from bookit.config import ScheduleConfig
from bookit.db.models import Service
from bookit.repositories import BookingRepository, DayOffRepository, ServiceRepository
from bookit.services.exceptions import (
    DateUnavailableError,
    ServiceInactiveError,
    ServiceNotFoundError,
)
from bookit.services.time_utils import Clock, local_today, system_clock

type Interval = tuple[datetime, datetime]


def bookable_dates(*, today: date, horizon_days: int, days_off: Iterable[date]) -> list[date]:
    """Dates open for booking at all: from today, horizon_days ahead."""
    excluded = set(days_off)
    candidates = (today + timedelta(days=offset) for offset in range(horizon_days))
    return [day for day in candidates if day not in excluded]


def compute_free_slots(
    *,
    day: date,
    duration_min: int,
    busy: Iterable[Interval],
    cfg: ScheduleConfig,
    now: datetime,
) -> list[datetime]:
    """Free slot start times for a day (in UTC).

    A slot qualifies if the whole service fits into working hours, starts
    strictly in the future and does not overlap any existing booking.
    Intervals are half-open: [start, end).
    """
    duration = timedelta(minutes=duration_min)
    step = timedelta(minutes=cfg.slot_step_minutes)
    work_start = datetime.combine(day, cfg.work_start, tzinfo=cfg.tz).astimezone(UTC)
    work_end = datetime.combine(day, cfg.work_end, tzinfo=cfg.tz).astimezone(UTC)
    busy_intervals = sorted(busy)

    slots: list[datetime] = []
    start = work_start
    while start + duration <= work_end:
        end = start + duration
        is_free = all(end <= b_start or start >= b_end for b_start, b_end in busy_intervals)
        if start > now and is_free:
            slots.append(start)
        start += step
    return slots


class SlotService:
    def __init__(
        self, session: AsyncSession, cfg: ScheduleConfig, clock: Clock = system_clock
    ) -> None:
        self._cfg = cfg
        self._clock = clock
        self._services = ServiceRepository(session)
        self._bookings = BookingRepository(session)
        self._days_off = DayOffRepository(session)

    async def available_dates(self) -> list[date]:
        today = local_today(self._clock(), self._cfg.tz)
        last_day = today + timedelta(days=self._cfg.horizon_days - 1)
        days_off = await self._days_off.list_between(today, last_day)
        return bookable_dates(
            today=today,
            horizon_days=self._cfg.horizon_days,
            days_off=(d.day for d in days_off),
        )

    async def free_slots(self, service_id: int, day: date) -> list[datetime]:
        service = await self.get_bookable_service(service_id)
        if day not in await self.available_dates():
            raise DateUnavailableError
        work_start = datetime.combine(day, self._cfg.work_start, tzinfo=self._cfg.tz)
        work_end = datetime.combine(day, self._cfg.work_end, tzinfo=self._cfg.tz)
        busy = await self._bookings.list_active_overlapping(work_start, work_end)
        return compute_free_slots(
            day=day,
            duration_min=service.duration_min,
            busy=((b.start_at, b.end_at) for b in busy),
            cfg=self._cfg,
            now=self._clock(),
        )

    async def get_bookable_service(self, service_id: int) -> Service:
        service = await self._services.get(service_id)
        if service is None:
            raise ServiceNotFoundError
        if not service.is_active:
            raise ServiceInactiveError
        return service

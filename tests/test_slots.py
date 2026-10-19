from datetime import UTC, date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.config import ScheduleConfig
from bookit.db.models import Service, User
from bookit.services import BookingService, CatalogService, ScheduleService, SlotService
from bookit.services.exceptions import (
    DateUnavailableError,
    ServiceInactiveError,
    ServiceNotFoundError,
)
from bookit.services.slots import bookable_dates, compute_free_slots
from tests.conftest import NOW, TODAY, FakeClock, at

TOMORROW = TODAY + timedelta(days=1)


def local_times(slots: list, cfg: ScheduleConfig) -> list[str]:
    return [f"{s.astimezone(cfg.tz):%H:%M}" for s in slots]


class TestComputeFreeSlots:
    def test_empty_day_gives_all_slots_that_fit(self, cfg: ScheduleConfig) -> None:
        slots = compute_free_slots(day=TOMORROW, duration_min=60, busy=[], cfg=cfg, now=NOW)

        times = local_times(slots, cfg)
        assert times[0] == "10:00"
        assert times[-1] == "17:00"  # 17:00 + 60 min = exactly the end of the day
        assert len(times) == 15

    def test_long_service_does_not_overflow_working_day(self, cfg: ScheduleConfig) -> None:
        slots = compute_free_slots(day=TOMORROW, duration_min=90, busy=[], cfg=cfg, now=NOW)

        assert local_times(slots, cfg)[-1] == "16:30"

    def test_service_longer_than_day_has_no_slots(self, cfg: ScheduleConfig) -> None:
        slots = compute_free_slots(day=TOMORROW, duration_min=9 * 60, busy=[], cfg=cfg, now=NOW)

        assert slots == []

    def test_busy_interval_blocks_overlapping_slots_only(self, cfg: ScheduleConfig) -> None:
        busy = [(at(TOMORROW, 12), at(TOMORROW, 13))]

        times = local_times(
            compute_free_slots(day=TOMORROW, duration_min=60, busy=busy, cfg=cfg, now=NOW), cfg
        )

        # touching boundaries is not an overlap
        assert "11:00" in times
        assert "13:00" in times
        assert {"11:30", "12:00", "12:30"}.isdisjoint(times)

    def test_past_slots_today_are_hidden(self, cfg: ScheduleConfig) -> None:
        now = at(TODAY, 13, 10).astimezone(UTC)

        times = local_times(
            compute_free_slots(day=TODAY, duration_min=30, busy=[], cfg=cfg, now=now), cfg
        )

        assert times[0] == "13:30"

    def test_slot_starting_exactly_now_is_hidden(self, cfg: ScheduleConfig) -> None:
        now = at(TODAY, 13, 0)

        times = local_times(
            compute_free_slots(day=TODAY, duration_min=30, busy=[], cfg=cfg, now=now), cfg
        )

        assert "13:00" not in times
        assert times[0] == "13:30"


class TestBookableDates:
    def test_returns_horizon_without_days_off(self) -> None:
        day_off = TODAY + timedelta(days=2)

        days = bookable_dates(today=TODAY, horizon_days=5, days_off=[day_off])

        assert days == [TODAY + timedelta(days=i) for i in (0, 1, 3, 4)]


class TestSlotService:
    async def test_free_slots_ignore_cancelled_bookings(
        self,
        session: AsyncSession,
        cfg: ScheduleConfig,
        clock: FakeClock,
        user: User,
        haircut: Service,
    ) -> None:
        bookings = BookingService(session, cfg, clock)
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 10))
        slots_service = SlotService(session, cfg, clock)
        assert at(TOMORROW, 10) not in await slots_service.free_slots(haircut.id, TOMORROW)

        await bookings.cancel_by_user(user, booking.id)

        assert at(TOMORROW, 10) in await slots_service.free_slots(haircut.id, TOMORROW)

    async def test_day_off_is_unavailable(
        self, session: AsyncSession, cfg: ScheduleConfig, clock: FakeClock, haircut: Service
    ) -> None:
        await ScheduleService(session, cfg, clock).add_day_off(TOMORROW)
        service = SlotService(session, cfg, clock)

        assert TOMORROW not in await service.available_dates()
        with pytest.raises(DateUnavailableError):
            await service.free_slots(haircut.id, TOMORROW)

    @pytest.mark.parametrize(
        "day", [TODAY - timedelta(days=1), TODAY + timedelta(days=14)], ids=["past", "too-far"]
    )
    async def test_dates_outside_horizon_are_unavailable(
        self,
        session: AsyncSession,
        cfg: ScheduleConfig,
        clock: FakeClock,
        haircut: Service,
        day: date,
    ) -> None:
        with pytest.raises(DateUnavailableError):
            await SlotService(session, cfg, clock).free_slots(haircut.id, day)

    async def test_hidden_service_cannot_be_booked(
        self, session: AsyncSession, cfg: ScheduleConfig, clock: FakeClock, haircut: Service
    ) -> None:
        await CatalogService(session).toggle_active(haircut.id)

        with pytest.raises(ServiceInactiveError):
            await SlotService(session, cfg, clock).free_slots(haircut.id, TOMORROW)

    async def test_unknown_service(
        self, session: AsyncSession, cfg: ScheduleConfig, clock: FakeClock
    ) -> None:
        with pytest.raises(ServiceNotFoundError):
            await SlotService(session, cfg, clock).free_slots(999, TOMORROW)

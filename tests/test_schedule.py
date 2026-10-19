from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.config import ScheduleConfig
from bookit.db.models import Service, User
from bookit.services import BookingService, ScheduleService
from bookit.services.exceptions import (
    DayHasBookingsError,
    DayOffExistsError,
    DayOffNotFoundError,
    ValidationError,
)
from bookit.services.schedule import parse_date
from tests.conftest import TODAY, FakeClock, at

TOMORROW = TODAY + timedelta(days=1)


@pytest.fixture
def schedule(session: AsyncSession, cfg: ScheduleConfig, clock: FakeClock) -> ScheduleService:
    return ScheduleService(session, cfg, clock)


class TestParseDate:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("31.12.2026", date(2026, 12, 31)),
            ("01.11", date(2026, 11, 1)),
            (" 5.1.2027 ", date(2027, 1, 5)),
        ],
    )
    def test_valid(self, text: str, expected: date) -> None:
        assert parse_date(text, TODAY) == expected

    @pytest.mark.parametrize("text", ["2026-10-10", "32.01.2026", "29.02", "tomorrow", ""])
    def test_invalid(self, text: str) -> None:
        with pytest.raises(ValidationError):
            parse_date(text, TODAY)

    def test_leap_day_without_year(self) -> None:
        assert parse_date("29.02", date(2028, 1, 10)) == date(2028, 2, 29)


class TestDaysOff:
    async def test_add_and_list(self, schedule: ScheduleService) -> None:
        added = await schedule.add_day_off(TOMORROW, "  Cleaning   day ")

        assert added.reason == "Cleaning day"
        assert [d.day for d in await schedule.list_upcoming()] == [TOMORROW]

    async def test_empty_reason_becomes_none(self, schedule: ScheduleService) -> None:
        added = await schedule.add_day_off(TOMORROW, "   ")

        assert added.reason is None

    async def test_duplicate_day_off(self, schedule: ScheduleService) -> None:
        await schedule.add_day_off(TOMORROW)

        with pytest.raises(DayOffExistsError):
            await schedule.add_day_off(TOMORROW)

    async def test_day_off_in_past(self, schedule: ScheduleService) -> None:
        with pytest.raises(ValidationError):
            await schedule.add_day_off(TODAY - timedelta(days=1))

    async def test_day_with_active_bookings_cannot_be_day_off(
        self,
        session: AsyncSession,
        cfg: ScheduleConfig,
        clock: FakeClock,
        schedule: ScheduleService,
        user: User,
        haircut: Service,
    ) -> None:
        bookings = BookingService(session, cfg, clock)
        await bookings.create(user, haircut.id, at(TOMORROW, 10))
        await bookings.create(user, haircut.id, at(TOMORROW, 15))

        with pytest.raises(DayHasBookingsError) as exc_info:
            await schedule.add_day_off(TOMORROW)
        assert exc_info.value.count == 2

    async def test_cancelled_bookings_do_not_block_day_off(
        self,
        session: AsyncSession,
        cfg: ScheduleConfig,
        clock: FakeClock,
        schedule: ScheduleService,
        user: User,
        haircut: Service,
    ) -> None:
        bookings = BookingService(session, cfg, clock)
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 10))
        await bookings.cancel_by_user(user, booking.id)

        added = await schedule.add_day_off(TOMORROW)

        assert added.day == TOMORROW

    async def test_remove(self, schedule: ScheduleService) -> None:
        added = await schedule.add_day_off(TOMORROW)

        await schedule.remove_day_off(added.id)

        assert await schedule.list_upcoming() == []

    async def test_remove_missing(self, schedule: ScheduleService) -> None:
        with pytest.raises(DayOffNotFoundError):
            await schedule.remove_day_off(999)

    async def test_past_days_off_are_not_listed(
        self, schedule: ScheduleService, clock: FakeClock
    ) -> None:
        await schedule.add_day_off(TOMORROW)
        clock.now += timedelta(days=2)

        assert await schedule.list_upcoming() == []

    def test_upcoming_dates_cover_horizon(self, schedule: ScheduleService) -> None:
        dates = schedule.upcoming_dates()

        assert dates[0] == TODAY
        assert len(dates) == 14

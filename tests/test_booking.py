from datetime import UTC, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.config import ScheduleConfig
from bookit.db.models import Booking, BookingStatus, Service, User
from bookit.repositories import BookingRepository
from bookit.services import BookingService, CatalogService
from bookit.services.exceptions import (
    BookingAlreadyCancelledError,
    BookingInPastError,
    BookingNotFoundError,
    ServiceInactiveError,
    SlotUnavailableError,
)
from tests.conftest import TODAY, FakeClock, at

TOMORROW = TODAY + timedelta(days=1)


@pytest.fixture
def bookings(session: AsyncSession, cfg: ScheduleConfig, clock: FakeClock) -> BookingService:
    return BookingService(session, cfg, clock)


class TestCreate:
    async def test_creates_active_booking_with_correct_end(
        self, bookings: BookingService, user: User, haircut: Service
    ) -> None:
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 11))

        assert booking.id is not None
        assert booking.status is BookingStatus.ACTIVE
        assert booking.start_at == at(TOMORROW, 11)
        assert booking.end_at == at(TOMORROW, 12)
        assert booking.start_at.tzinfo is not None

    async def test_same_slot_cannot_be_booked_twice(
        self, bookings: BookingService, user: User, other_user: User, haircut: Service
    ) -> None:
        await bookings.create(user, haircut.id, at(TOMORROW, 11))

        with pytest.raises(SlotUnavailableError):
            await bookings.create(other_user, haircut.id, at(TOMORROW, 11))

    async def test_overlapping_booking_with_other_start_is_rejected(
        self,
        bookings: BookingService,
        user: User,
        other_user: User,
        haircut: Service,
        beard: Service,
    ) -> None:
        await bookings.create(user, haircut.id, at(TOMORROW, 11))  # 11:00-12:00

        with pytest.raises(SlotUnavailableError):
            await bookings.create(other_user, beard.id, at(TOMORROW, 11, 30))

    async def test_adjacent_booking_is_allowed(
        self,
        bookings: BookingService,
        user: User,
        other_user: User,
        haircut: Service,
        beard: Service,
    ) -> None:
        await bookings.create(user, haircut.id, at(TOMORROW, 11))

        booking = await bookings.create(other_user, beard.id, at(TOMORROW, 12))

        assert booking.start_at == at(TOMORROW, 12)

    @pytest.mark.parametrize(
        ("hour", "minute"),
        [(10, 15), (9, 0), (17, 30)],
        ids=["off-grid", "before-opening", "ends-after-closing"],
    )
    async def test_invalid_start_is_rejected(
        self, bookings: BookingService, user: User, haircut: Service, hour: int, minute: int
    ) -> None:
        with pytest.raises(SlotUnavailableError):
            await bookings.create(user, haircut.id, at(TOMORROW, hour, minute))

    async def test_past_slot_is_rejected(
        self, bookings: BookingService, clock: FakeClock, user: User, haircut: Service
    ) -> None:
        clock.now = at(TODAY, 14).astimezone(UTC)

        with pytest.raises(SlotUnavailableError):
            await bookings.create(user, haircut.id, at(TODAY, 12))

    async def test_hidden_service_is_rejected(
        self, session: AsyncSession, bookings: BookingService, user: User, haircut: Service
    ) -> None:
        await CatalogService(session).toggle_active(haircut.id)

        with pytest.raises(ServiceInactiveError):
            await bookings.create(user, haircut.id, at(TOMORROW, 11))

    async def test_db_index_rejects_duplicate_active_start(
        self, session: AsyncSession, user: User, haircut: Service
    ) -> None:
        """Last line of defence: the partial unique index in the database."""
        repo = BookingRepository(session)
        start = at(TOMORROW, 11)
        for _ in range(2):
            session.add(
                Booking(
                    user=user, service=haircut, start_at=start, end_at=start + timedelta(hours=1)
                )
            )
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()
        assert await repo.count_active_overlapping(start, start + timedelta(hours=1)) == 0


class TestCancel:
    async def test_user_cancels_own_booking_and_slot_is_freed(
        self, bookings: BookingService, user: User, other_user: User, haircut: Service
    ) -> None:
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 11))

        cancelled = await bookings.cancel_by_user(user, booking.id)

        assert cancelled.status is BookingStatus.CANCELLED
        rebooked = await bookings.create(other_user, haircut.id, at(TOMORROW, 11))
        assert rebooked.status is BookingStatus.ACTIVE

    async def test_user_cannot_cancel_foreign_booking(
        self, bookings: BookingService, user: User, other_user: User, haircut: Service
    ) -> None:
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 11))

        with pytest.raises(BookingNotFoundError):
            await bookings.cancel_by_user(other_user, booking.id)

    async def test_unknown_booking(self, bookings: BookingService, user: User) -> None:
        with pytest.raises(BookingNotFoundError):
            await bookings.cancel_by_user(user, 12345)
        with pytest.raises(BookingNotFoundError):
            await bookings.cancel_by_admin(12345)

    async def test_double_cancel(
        self, bookings: BookingService, user: User, haircut: Service
    ) -> None:
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 11))
        await bookings.cancel_by_user(user, booking.id)

        with pytest.raises(BookingAlreadyCancelledError):
            await bookings.cancel_by_admin(booking.id)

    async def test_started_booking_cannot_be_cancelled(
        self, bookings: BookingService, clock: FakeClock, user: User, haircut: Service
    ) -> None:
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 11))
        clock.now = at(TOMORROW, 11, 10).astimezone(UTC)

        with pytest.raises(BookingInPastError):
            await bookings.cancel_by_user(user, booking.id)

    async def test_admin_cancels_any_booking(
        self, bookings: BookingService, user: User, haircut: Service
    ) -> None:
        booking = await bookings.create(user, haircut.id, at(TOMORROW, 11))

        cancelled = await bookings.cancel_by_admin(booking.id)

        assert cancelled.status is BookingStatus.CANCELLED


class TestListing:
    async def test_user_upcoming_excludes_cancelled_and_past(
        self,
        bookings: BookingService,
        clock: FakeClock,
        user: User,
        other_user: User,
        haircut: Service,
    ) -> None:
        clock.now = at(TODAY, 9).astimezone(UTC)
        today_booking = await bookings.create(user, haircut.id, at(TODAY, 10))
        cancelled = await bookings.create(user, haircut.id, at(TOMORROW, 10))
        await bookings.cancel_by_user(user, cancelled.id)
        upcoming = await bookings.create(user, haircut.id, at(TOMORROW, 15))
        await bookings.create(other_user, haircut.id, at(TOMORROW, 12))
        clock.now = at(TODAY, 11).astimezone(UTC)  # the 10:00 booking is in the past now

        result = await bookings.list_user_upcoming(user)

        assert [b.id for b in result] == [upcoming.id]
        assert today_booking.id not in {b.id for b in result}

    async def test_list_for_day_returns_only_that_day_sorted(
        self, bookings: BookingService, user: User, other_user: User, haircut: Service
    ) -> None:
        late = await bookings.create(user, haircut.id, at(TOMORROW, 16))
        early = await bookings.create(other_user, haircut.id, at(TOMORROW, 10))
        await bookings.create(user, haircut.id, at(TOMORROW + timedelta(days=1), 10))

        result = await bookings.list_for_day(TOMORROW)

        assert [b.id for b in result] == [early.id, late.id]
        assert result[0].user.full_name == "Maria"
        assert result[0].service.name == "Haircut"

import asyncio
import logging
from collections.abc import Sequence
from datetime import date, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.config import ScheduleConfig
from bookit.db.models import Booking, BookingStatus, User
from bookit.repositories import BookingRepository
from bookit.services.exceptions import (
    BookingAlreadyCancelledError,
    BookingInPastError,
    BookingNotFoundError,
    SlotUnavailableError,
)
from bookit.services.slots import SlotService
from bookit.services.time_utils import Clock, local_day_bounds, system_clock

logger = logging.getLogger(__name__)

# aiogram handles updates concurrently: the lock makes the "slot is free"
# check and the insert atomic within the process. The unique index in the
# database additionally guards against identical start times.
_booking_lock = asyncio.Lock()


class BookingService:
    def __init__(
        self, session: AsyncSession, cfg: ScheduleConfig, clock: Clock = system_clock
    ) -> None:
        self._session = session
        self._cfg = cfg
        self._clock = clock
        self._bookings = BookingRepository(session)
        self._slots = SlotService(session, cfg, clock)

    async def create(self, user: User, service_id: int, start_at: datetime) -> Booking:
        async with _booking_lock:
            service = await self._slots.get_bookable_service(service_id)
            local_day = start_at.astimezone(self._cfg.tz).date()
            free_slots = await self._slots.free_slots(service_id, local_day)
            if start_at not in free_slots:
                raise SlotUnavailableError

            booking = Booking(
                user=user,
                service=service,
                start_at=start_at,
                end_at=start_at + timedelta(minutes=service.duration_min),
                status=BookingStatus.ACTIVE,
            )
            try:
                await self._bookings.add(booking)
                await self._session.commit()
            except IntegrityError:
                await self._session.rollback()
                logger.warning("Unique index conflict when booking %s", start_at)
                raise SlotUnavailableError from None

        logger.info(
            "Booking created id=%s user_id=%s service_id=%s start=%s",
            booking.id,
            user.id,
            service.id,
            start_at.isoformat(),
        )
        return booking

    async def cancel_by_user(self, user: User, booking_id: int) -> Booking:
        booking = await self._bookings.get(booking_id)
        if booking is None or booking.user_id != user.id:
            raise BookingNotFoundError
        return await self._cancel(booking)

    async def cancel_by_admin(self, booking_id: int) -> Booking:
        booking = await self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFoundError
        return await self._cancel(booking)

    async def list_user_upcoming(self, user: User) -> Sequence[Booking]:
        return await self._bookings.list_user_active_from(user.id, self._clock())

    async def list_for_day(self, day: date) -> Sequence[Booking]:
        start, end = local_day_bounds(day, self._cfg.tz)
        return await self._bookings.list_active_overlapping(start, end)

    async def _cancel(self, booking: Booking) -> Booking:
        if booking.status is BookingStatus.CANCELLED:
            raise BookingAlreadyCancelledError
        if booking.start_at <= self._clock():
            raise BookingInPastError
        booking.status = BookingStatus.CANCELLED
        await self._session.commit()
        logger.info("Booking id=%s cancelled", booking.id)
        return booking

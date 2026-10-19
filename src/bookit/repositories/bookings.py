from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import Booking, BookingStatus


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, booking_id: int) -> Booking | None:
        return await self._session.get(Booking, booking_id)

    async def add(self, booking: Booking) -> Booking:
        self._session.add(booking)
        await self._session.flush()
        return booking

    async def list_active_overlapping(self, start: datetime, end: datetime) -> Sequence[Booking]:
        """Active bookings overlapping the half-open interval [start, end)."""
        stmt = (
            select(Booking)
            .where(
                Booking.status == BookingStatus.ACTIVE,
                Booking.start_at < end,
                Booking.end_at > start,
            )
            .order_by(Booking.start_at)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_active_overlapping(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count(Booking.id)).where(
            Booking.status == BookingStatus.ACTIVE,
            Booking.start_at < end,
            Booking.end_at > start,
        )
        return (await self._session.scalar(stmt)) or 0

    async def list_user_active_from(self, user_id: int, moment: datetime) -> Sequence[Booking]:
        stmt = (
            select(Booking)
            .where(
                Booking.user_id == user_id,
                Booking.status == BookingStatus.ACTIVE,
                Booking.start_at >= moment,
            )
            .order_by(Booking.start_at)
        )
        return (await self._session.scalars(stmt)).all()

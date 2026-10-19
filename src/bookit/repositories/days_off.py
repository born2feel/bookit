from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import DayOff


class DayOffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, day_off_id: int) -> DayOff | None:
        return await self._session.get(DayOff, day_off_id)

    async def get_by_day(self, day: date) -> DayOff | None:
        return await self._session.scalar(select(DayOff).where(DayOff.day == day))

    async def list_between(self, start: date, end: date) -> Sequence[DayOff]:
        """Days off within the inclusive range [start, end]."""
        stmt = select(DayOff).where(DayOff.day >= start, DayOff.day <= end).order_by(DayOff.day)
        return (await self._session.scalars(stmt)).all()

    async def list_from(self, start: date) -> Sequence[DayOff]:
        stmt = select(DayOff).where(DayOff.day >= start).order_by(DayOff.day)
        return (await self._session.scalars(stmt)).all()

    async def add(self, day_off: DayOff) -> DayOff:
        self._session.add(day_off)
        await self._session.flush()
        return day_off

    async def delete(self, day_off: DayOff) -> None:
        await self._session.delete(day_off)
        await self._session.flush()

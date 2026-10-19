from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import Service


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, service_id: int) -> Service | None:
        return await self._session.get(Service, service_id)

    async def list(self, *, only_active: bool) -> Sequence[Service]:
        stmt = select(Service).order_by(Service.name)
        if only_active:
            stmt = stmt.where(Service.is_active.is_(True))
        return (await self._session.scalars(stmt)).all()

    async def add(self, service: Service) -> Service:
        self._session.add(service)
        await self._session.flush()
        return service

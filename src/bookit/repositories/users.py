from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        return await self._session.scalar(select(User).where(User.tg_id == tg_id))

    async def list_by_tg_ids(self, tg_ids: Sequence[int]) -> Sequence[User]:
        if not tg_ids:
            return []
        return (await self._session.scalars(select(User).where(User.tg_id.in_(tg_ids)))).all()

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user

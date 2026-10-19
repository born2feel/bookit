import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import User
from bookit.repositories import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def register(self, tg_id: int, full_name: str, username: str | None) -> User:
        """Creates the user or updates their name if it changed in Telegram."""
        full_name = full_name[:255]
        user = await self._users.get_by_tg_id(tg_id)
        if user is None:
            user = await self._users.add(User(tg_id=tg_id, full_name=full_name, username=username))
            await self._session.commit()
            logger.info("New user tg_id=%s", tg_id)
        elif (user.full_name, user.username) != (full_name, username):
            user.full_name = full_name
            user.username = username
            await self._session.commit()
        return user

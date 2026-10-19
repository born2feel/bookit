import logging
from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import DEFAULT_LANGUAGE, Language, User
from bookit.repositories import UserRepository

logger = logging.getLogger(__name__)


def language_from_telegram(language_code: str | None) -> Language:
    """Default language for a new user, taken from their Telegram settings."""
    if language_code is None:
        return DEFAULT_LANGUAGE
    if language_code.lower().startswith("ru"):
        return Language.RU
    return Language.EN


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def register(
        self,
        tg_id: int,
        full_name: str,
        username: str | None,
        language_code: str | None = None,
    ) -> User:
        """Creates the user or updates their name if it changed in Telegram.

        The language is taken from Telegram only on the first visit — after that
        the user picks it themselves and we never overwrite it.
        """
        full_name = full_name[:255]
        user = await self._users.get_by_tg_id(tg_id)
        if user is None:
            user = await self._users.add(
                User(
                    tg_id=tg_id,
                    full_name=full_name,
                    username=username,
                    language=language_from_telegram(language_code),
                )
            )
            await self._session.commit()
            logger.info("New user tg_id=%s", tg_id)
        elif (user.full_name, user.username) != (full_name, username):
            user.full_name = full_name
            user.username = username
            await self._session.commit()
        return user

    async def set_language(self, user: User, language: Language) -> User:
        if user.language is not language:
            user.language = language
            await self._session.commit()
            logger.info("tg_id=%s switched language to %s", user.tg_id, language.value)
        return user

    async def languages_for(self, tg_ids: Iterable[int]) -> dict[int, Language]:
        """Users' languages by Telegram ID; unknown users get the default language."""
        ids = list(tg_ids)
        known = {user.tg_id: user.language for user in await self._users.list_by_tg_ids(ids)}
        return {tg_id: known.get(tg_id, DEFAULT_LANGUAGE) for tg_id in ids}

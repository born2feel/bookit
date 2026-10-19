from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bookit.bot.i18n import get_translator
from bookit.bot.notifier import Notifier
from bookit.config import ScheduleConfig
from bookit.services import (
    BookingService,
    CatalogService,
    ScheduleService,
    SlotService,
    UserService,
)

type Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class ServicesMiddleware(BaseMiddleware):
    """Opens a DB session per update and injects dependencies into handlers.

    Handlers receive services, the message translator (`tr`) and the notifier —
    they never touch the session or repositories directly.
    """

    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        schedule_cfg: ScheduleConfig,
        admin_ids: frozenset[int],
    ) -> None:
        self._sessionmaker = sessionmaker
        self._cfg = schedule_cfg
        self._admin_ids = admin_ids

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        async with self._sessionmaker() as session:
            data["catalog_service"] = CatalogService(session)
            data["slot_service"] = SlotService(session, self._cfg)
            data["booking_service"] = BookingService(session, self._cfg)
            data["schedule_service"] = ScheduleService(session, self._cfg)
            data["tr"] = get_translator()

            bot: Bot | None = data.get("bot")
            if bot is not None:
                data["notifier"] = Notifier(bot, self._admin_ids, self._cfg.tz)

            tg_user: TgUser | None = data.get("event_from_user")
            if tg_user is not None and not tg_user.is_bot:
                data["db_user"] = await UserService(session).register(
                    tg_id=tg_user.id,
                    full_name=tg_user.full_name,
                    username=tg_user.username,
                )
            return await handler(event, data)

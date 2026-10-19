import logging
from collections.abc import Callable
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bookit.bot.i18n import Translator, get_translator
from bookit.bot.texts import booking_line, client_name
from bookit.db.models import Booking
from bookit.services import UserService

logger = logging.getLogger(__name__)

type TextRenderer = Callable[[Translator], str]


class Notifier:
    """Notifications for admins and clients, each in their own language.

    A delivery failure never breaks the main flow.
    """

    def __init__(
        self, bot: Bot, admin_ids: frozenset[int], tz: ZoneInfo, user_service: UserService
    ) -> None:
        self._bot = bot
        self._admin_ids = admin_ids
        self._tz = tz
        self._users = user_service

    async def booking_created(self, booking: Booking) -> None:
        await self._to_admins(
            lambda tr: tr(
                "notify.new_booking",
                booking=booking_line(booking, self._tz, tr),
                client=client_name(booking),
            )
        )

    async def booking_cancelled_by_client(self, booking: Booking) -> None:
        await self._to_admins(
            lambda tr: tr(
                "notify.client_cancelled",
                booking=booking_line(booking, self._tz, tr),
                client=client_name(booking),
            )
        )

    async def booking_cancelled_by_admin(self, booking: Booking) -> None:
        tr = get_translator(booking.user.language)
        await self._send(
            booking.user.tg_id,
            tr("notify.admin_cancelled", booking=booking_line(booking, self._tz, tr)),
        )

    async def _to_admins(self, render: TextRenderer) -> None:
        languages = await self._users.languages_for(self._admin_ids)
        for admin_id, language in languages.items():
            await self._send(admin_id, render(get_translator(language)))

    async def _send(self, chat_id: int, text: str) -> None:
        try:
            await self._bot.send_message(chat_id, text)
        except TelegramAPIError as exc:
            logger.warning("Failed to send notification to chat_id=%s: %s", chat_id, exc)

import logging
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bookit.bot.i18n import get_translator
from bookit.bot.texts import booking_line, client_name
from bookit.db.models import Booking

logger = logging.getLogger(__name__)


class Notifier:
    """Notifications for admins and clients.

    A delivery failure never breaks the main flow.
    """

    def __init__(self, bot: Bot, admin_ids: frozenset[int], tz: ZoneInfo) -> None:
        self._bot = bot
        self._admin_ids = admin_ids
        self._tz = tz
        self._tr = get_translator()

    async def booking_created(self, booking: Booking) -> None:
        await self._to_admins(
            self._tr(
                "notify.new_booking",
                booking=booking_line(booking, self._tz, self._tr),
                client=client_name(booking),
            )
        )

    async def booking_cancelled_by_client(self, booking: Booking) -> None:
        await self._to_admins(
            self._tr(
                "notify.client_cancelled",
                booking=booking_line(booking, self._tz, self._tr),
                client=client_name(booking),
            )
        )

    async def booking_cancelled_by_admin(self, booking: Booking) -> None:
        await self._send(
            booking.user.tg_id,
            self._tr("notify.admin_cancelled", booking=booking_line(booking, self._tz, self._tr)),
        )

    async def _to_admins(self, text: str) -> None:
        for admin_id in self._admin_ids:
            await self._send(admin_id, text)

    async def _send(self, chat_id: int, text: str) -> None:
        try:
            await self._bot.send_message(chat_id, text)
        except TelegramAPIError as exc:
            logger.warning("Failed to send notification to chat_id=%s: %s", chat_id, exc)

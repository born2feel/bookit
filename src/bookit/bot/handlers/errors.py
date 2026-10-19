import logging

from aiogram.exceptions import TelegramAPIError
from aiogram.types import ErrorEvent

from bookit.bot.i18n import Translator, get_translator
from bookit.services.exceptions import BookItError

logger = logging.getLogger(__name__)


async def on_error(event: ErrorEvent, tr: Translator | None = None) -> bool:
    """Single place for errors: domain errors become friendly text, the rest goes to the log.

    `tr` may be missing if the error happened before the middleware ran.
    """
    tr = tr or get_translator()
    exc = event.exception
    if isinstance(exc, BookItError):
        logger.info("Domain error: %s %s", exc.key, exc.params)
        text = tr.error(exc)
    else:
        logger.exception("Unhandled error in update %s", event.update.update_id, exc_info=exc)
        text = tr("error.unexpected")

    update = event.update
    try:
        if update.callback_query is not None:
            await update.callback_query.answer(text, show_alert=True)
        elif update.message is not None:
            await update.message.answer(text)
    except TelegramAPIError:
        logger.warning("Failed to report the error to the user", exc_info=True)
    return True

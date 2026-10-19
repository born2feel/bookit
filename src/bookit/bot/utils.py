from datetime import date

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bookit.services.exceptions import ValidationError


async def show(
    callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None
) -> None:
    """Replaces the keyboard message with a new screen and stops the button spinner."""
    message = callback.message
    if isinstance(message, Message):
        try:
            await message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as exc:
            if "message is not modified" not in exc.message:
                raise
    elif callback.bot is not None:
        # the message is too old to be edited — send a new one instead
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=markup)
    await callback.answer()


def parse_iso_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError("validation.bad_date") from None

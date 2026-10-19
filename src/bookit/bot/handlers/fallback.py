from aiogram import Router
from aiogram.types import CallbackQuery, Message

from bookit.bot.i18n import Translator

router = Router(name="fallback")


@router.callback_query()
async def stale_callback(callback: CallbackQuery, tr: Translator) -> None:
    await callback.answer(tr("menu.stale_button"), show_alert=True)


@router.message()
async def unknown_message(message: Message, tr: Translator) -> None:
    await message.answer(tr("menu.unknown_input"))

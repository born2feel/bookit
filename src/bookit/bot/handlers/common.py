from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bookit.bot.callbacks import LanguageCb, MenuAction, MenuCb
from bookit.bot.i18n import Translator, get_translator
from bookit.bot.keyboards.client import language_picker, main_menu
from bookit.bot.utils import show
from bookit.db.models import User
from bookit.services import UserService

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, tr: Translator, admin_ids: frozenset[int]
) -> None:
    await state.clear()
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        tr("menu.welcome"), reply_markup=main_menu(tr, is_admin=user_id in admin_ids)
    )


@router.message(Command("help"))
async def cmd_help(message: Message, tr: Translator) -> None:
    await message.answer(tr("menu.help"))


@router.message(Command("cancel"))
async def cmd_cancel(
    message: Message, state: FSMContext, tr: Translator, admin_ids: frozenset[int]
) -> None:
    had_state = await state.get_state() is not None
    await state.clear()
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        tr("menu.cancelled" if had_state else "menu.nothing_to_cancel"),
        reply_markup=main_menu(tr, is_admin=user_id in admin_ids),
    )


@router.callback_query(MenuCb.filter(F.action == MenuAction.MAIN))
async def to_main_menu(
    callback: CallbackQuery, state: FSMContext, tr: Translator, admin_ids: frozenset[int]
) -> None:
    await state.clear()
    await show(
        callback, tr("menu.welcome"), main_menu(tr, is_admin=callback.from_user.id in admin_ids)
    )


# --- language selection ---


@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext, db_user: User, tr: Translator) -> None:
    await state.clear()
    await message.answer(tr("language.choose"), reply_markup=language_picker(db_user.language))


@router.callback_query(MenuCb.filter(F.action == MenuAction.LANGUAGE))
async def language_menu(
    callback: CallbackQuery, state: FSMContext, db_user: User, tr: Translator
) -> None:
    await state.clear()
    await show(callback, tr("language.choose"), language_picker(db_user.language))


@router.callback_query(LanguageCb.filter())
async def language_chosen(
    callback: CallbackQuery,
    callback_data: LanguageCb,
    db_user: User,
    user_service: UserService,
    admin_ids: frozenset[int],
) -> None:
    user = await user_service.set_language(db_user, callback_data.language)
    tr = get_translator(user.language)
    await show(
        callback,
        f"{tr('language.changed')}\n\n{tr('menu.welcome')}",
        main_menu(tr, is_admin=callback.from_user.id in admin_ids),
    )

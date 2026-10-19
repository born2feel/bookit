"""Admin panel: services, bookings by date, days off.

Validation errors (BookItError) raised by services are caught by the global
error handler: it shows the message to the user and leaves the FSM state
untouched, so the admin simply enters the value again.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bookit.bot import texts
from bookit.bot.callbacks import (
    AdminBookingAction,
    AdminBookingCb,
    AdminCb,
    AdminDateCb,
    AdminSection,
    AdminServiceAction,
    AdminServiceCb,
    DayOffAction,
    DayOffCb,
)
from bookit.bot.filters import IsAdmin
from bookit.bot.i18n import Translator
from bookit.bot.keyboards import admin as kb
from bookit.bot.notifier import Notifier
from bookit.bot.states import AddDayOff, AddService, EditService
from bookit.bot.utils import parse_iso_day, show
from bookit.config import ScheduleConfig
from bookit.db.models import Service
from bookit.services import BookingService, CatalogService, ScheduleService
from bookit.services.catalog import parse_duration, parse_price, validate_name
from bookit.services.exceptions import BookItError
from bookit.services.schedule import parse_date

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

SKIP_REASON = "-"


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.clear()
    await message.answer(tr("admin.menu"), reply_markup=kb.admin_menu(tr))


@router.callback_query(AdminCb.filter(F.section == AdminSection.MENU))
async def admin_menu(callback: CallbackQuery, state: FSMContext, tr: Translator) -> None:
    await state.clear()
    await show(callback, tr("admin.menu"), kb.admin_menu(tr))


# --- services ---


async def _services_screen(
    catalog_service: CatalogService, tr: Translator
) -> tuple[str, InlineKeyboardMarkup]:
    services = await catalog_service.list_all()
    if not services:
        return tr("admin.services_empty"), kb.services_list(services, tr)
    lines = "\n".join(
        f"{'✅' if s.is_active else '🙈'} {texts.service_line(s, tr)}" for s in services
    )
    return f"{tr('admin.services_title')}\n\n{lines}", kb.services_list(services, tr)


async def _answer_service_card(
    message: Message, service: Service, tr: Translator, title_key: str
) -> None:
    await message.answer(
        f"{tr(title_key)}\n\n{texts.service_card(service, tr)}",
        reply_markup=kb.service_actions(service, tr),
    )


@router.callback_query(AdminCb.filter(F.section == AdminSection.SERVICES))
async def services_section(
    callback: CallbackQuery, state: FSMContext, tr: Translator, catalog_service: CatalogService
) -> None:
    await state.clear()
    await show(callback, *await _services_screen(catalog_service, tr))


@router.callback_query(AdminServiceCb.filter(F.action == AdminServiceAction.VIEW))
async def service_view(
    callback: CallbackQuery,
    callback_data: AdminServiceCb,
    tr: Translator,
    catalog_service: CatalogService,
) -> None:
    service = await catalog_service.get(callback_data.service_id)
    await show(callback, texts.service_card(service, tr), kb.service_actions(service, tr))


@router.callback_query(AdminServiceCb.filter(F.action == AdminServiceAction.TOGGLE))
async def service_toggle(
    callback: CallbackQuery,
    callback_data: AdminServiceCb,
    tr: Translator,
    catalog_service: CatalogService,
) -> None:
    service = await catalog_service.toggle_active(callback_data.service_id)
    await show(callback, texts.service_card(service, tr), kb.service_actions(service, tr))


@router.callback_query(AdminServiceCb.filter(F.action == AdminServiceAction.ADD))
async def service_add_start(callback: CallbackQuery, state: FSMContext, tr: Translator) -> None:
    await state.set_state(AddService.name)
    await show(callback, tr("admin.ask_name"))


@router.message(AddService.name, F.text)
async def service_add_name(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.update_data(name=validate_name(message.text or ""))
    await state.set_state(AddService.duration)
    await message.answer(tr("admin.ask_duration"))


@router.message(AddService.duration, F.text)
async def service_add_duration(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.update_data(duration_min=parse_duration(message.text or ""))
    await state.set_state(AddService.price)
    await message.answer(tr("admin.ask_price"))


@router.message(AddService.price, F.text)
async def service_add_price(
    message: Message, state: FSMContext, tr: Translator, catalog_service: CatalogService
) -> None:
    price = parse_price(message.text or "")
    data = await state.get_data()
    service = await catalog_service.create(data["name"], data["duration_min"], price)
    await state.clear()
    await _answer_service_card(message, service, tr, "admin.service_added")


@router.callback_query(AdminServiceCb.filter(F.action == AdminServiceAction.EDIT_PRICE))
async def service_edit_price_start(
    callback: CallbackQuery, callback_data: AdminServiceCb, state: FSMContext, tr: Translator
) -> None:
    await state.set_state(EditService.price)
    await state.update_data(service_id=callback_data.service_id)
    await show(callback, tr("admin.ask_new_price"))


@router.message(EditService.price, F.text)
async def service_edit_price(
    message: Message, state: FSMContext, tr: Translator, catalog_service: CatalogService
) -> None:
    price = parse_price(message.text or "")
    data = await state.get_data()
    service = await catalog_service.update_price(data["service_id"], price)
    await state.clear()
    await _answer_service_card(message, service, tr, "admin.price_updated")


@router.callback_query(AdminServiceCb.filter(F.action == AdminServiceAction.EDIT_DURATION))
async def service_edit_duration_start(
    callback: CallbackQuery, callback_data: AdminServiceCb, state: FSMContext, tr: Translator
) -> None:
    await state.set_state(EditService.duration)
    await state.update_data(service_id=callback_data.service_id)
    await show(callback, tr("admin.ask_new_duration"))


@router.message(EditService.duration, F.text)
async def service_edit_duration(
    message: Message, state: FSMContext, tr: Translator, catalog_service: CatalogService
) -> None:
    duration = parse_duration(message.text or "")
    data = await state.get_data()
    service = await catalog_service.update_duration(data["service_id"], duration)
    await state.clear()
    await _answer_service_card(message, service, tr, "admin.duration_updated")


# --- bookings by date ---


@router.callback_query(AdminCb.filter(F.section == AdminSection.BOOKINGS))
async def bookings_section(
    callback: CallbackQuery, state: FSMContext, tr: Translator, schedule_service: ScheduleService
) -> None:
    await state.clear()
    await show(
        callback, tr("admin.choose_date"), kb.dates_list(schedule_service.upcoming_dates(), tr)
    )


async def _show_day(
    callback: CallbackQuery,
    day_iso: str,
    tr: Translator,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
    *,
    notice: str | None = None,
) -> None:
    day = parse_iso_day(day_iso)
    bookings = await booking_service.list_for_day(day)
    header = f"{notice}\n\n" if notice else ""
    if bookings:
        lines = "\n".join(texts.admin_booking_line(b, schedule_cfg.tz, tr) for b in bookings)
        body = f"{tr('admin.day_title', day=tr.day(day))}\n\n{lines}"
    else:
        body = tr("admin.day_empty", day=tr.day(day))
    await show(callback, header + body, kb.day_bookings(bookings, day, schedule_cfg.tz, tr))


@router.callback_query(AdminDateCb.filter())
async def day_bookings(
    callback: CallbackQuery,
    callback_data: AdminDateCb,
    tr: Translator,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
) -> None:
    await _show_day(callback, callback_data.day, tr, booking_service, schedule_cfg)


@router.callback_query(AdminBookingCb.filter(F.action == AdminBookingAction.ASK_CANCEL))
async def admin_ask_cancel(
    callback: CallbackQuery,
    callback_data: AdminBookingCb,
    tr: Translator,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
) -> None:
    day = parse_iso_day(callback_data.day)
    bookings = await booking_service.list_for_day(day)
    booking = next((b for b in bookings if b.id == callback_data.booking_id), None)
    if booking is None:
        await callback.answer(tr("error.booking_not_found"), show_alert=True)
        return
    await show(
        callback,
        tr("admin.ask_cancel", booking=texts.admin_booking_line(booking, schedule_cfg.tz, tr)),
        kb.confirm_admin_cancel(booking.id, day, tr),
    )


@router.callback_query(AdminBookingCb.filter(F.action == AdminBookingAction.CONFIRM_CANCEL))
async def admin_confirm_cancel(
    callback: CallbackQuery,
    callback_data: AdminBookingCb,
    tr: Translator,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
    notifier: Notifier,
) -> None:
    booking = await booking_service.cancel_by_admin(callback_data.booking_id)
    await notifier.booking_cancelled_by_admin(booking)
    await _show_day(
        callback,
        callback_data.day,
        tr,
        booking_service,
        schedule_cfg,
        notice=tr("admin.booking_cancelled"),
    )


# --- days off ---


async def _days_off_screen(
    schedule_service: ScheduleService, tr: Translator
) -> tuple[str, InlineKeyboardMarkup]:
    days_off = await schedule_service.list_upcoming()
    if days_off:
        body = "\n".join(texts.day_off_line(d, tr) for d in days_off)
    else:
        body = tr("admin.days_off_empty")
    return f"{tr('admin.days_off_title')}\n\n{body}", kb.days_off_list(days_off, tr)


@router.callback_query(AdminCb.filter(F.section == AdminSection.DAYS_OFF))
async def days_off_section(
    callback: CallbackQuery, state: FSMContext, tr: Translator, schedule_service: ScheduleService
) -> None:
    await state.clear()
    await show(callback, *await _days_off_screen(schedule_service, tr))


@router.callback_query(DayOffCb.filter(F.action == DayOffAction.REMOVE))
async def day_off_remove(
    callback: CallbackQuery,
    callback_data: DayOffCb,
    tr: Translator,
    schedule_service: ScheduleService,
) -> None:
    await schedule_service.remove_day_off(callback_data.day_off_id)
    text, markup = await _days_off_screen(schedule_service, tr)
    await show(callback, f"{tr('admin.day_off_removed')}\n\n{text}", markup)


@router.callback_query(DayOffCb.filter(F.action == DayOffAction.ADD))
async def day_off_add_start(callback: CallbackQuery, state: FSMContext, tr: Translator) -> None:
    await state.set_state(AddDayOff.day)
    await show(callback, tr("admin.ask_day_off"))


@router.message(AddDayOff.day, F.text)
async def day_off_add_day(
    message: Message, state: FSMContext, tr: Translator, schedule_service: ScheduleService
) -> None:
    day = parse_date(message.text or "", schedule_service.today())
    await schedule_service.ensure_can_add_day_off(day)
    await state.update_data(day=day.isoformat())
    await state.set_state(AddDayOff.reason)
    await message.answer(tr("admin.ask_reason", skip=SKIP_REASON))


@router.message(AddDayOff.reason, F.text)
async def day_off_add_reason(
    message: Message, state: FSMContext, tr: Translator, schedule_service: ScheduleService
) -> None:
    data = await state.get_data()
    reason = None if message.text == SKIP_REASON else message.text
    try:
        await schedule_service.add_day_off(parse_iso_day(data["day"]), reason)
    except BookItError as exc:
        # someone may have booked that day while the reason was typed — restart from the date step
        await state.clear()
        await message.answer(
            tr.error(exc),
            reply_markup=kb.to_section(AdminSection.DAYS_OFF, tr("btn.to_days_off")),
        )
        return
    await state.clear()
    text, markup = await _days_off_screen(schedule_service, tr)
    await message.answer(f"{tr('admin.day_off_added')}\n\n{text}", reply_markup=markup)

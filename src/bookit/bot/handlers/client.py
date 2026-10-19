"""Client flows: booking a service and managing one's own bookings."""

from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bookit.bot import texts
from bookit.bot.callbacks import (
    DateCb,
    FlowAction,
    FlowCb,
    MenuAction,
    MenuCb,
    MyBookingAction,
    MyBookingCb,
    ServiceCb,
    SlotCb,
)
from bookit.bot.i18n import Translator
from bookit.bot.keyboards import client as kb
from bookit.bot.notifier import Notifier
from bookit.bot.states import BookingFlow
from bookit.bot.utils import parse_iso_day, show
from bookit.config import ScheduleConfig
from bookit.db.models import User
from bookit.services import BookingService, CatalogService, SlotService
from bookit.services.exceptions import SlotUnavailableError

router = Router(name="client")


# --- step 1: choose a service ---


@router.callback_query(MenuCb.filter(F.action == MenuAction.BOOK))
@router.callback_query(
    StateFilter(BookingFlow), FlowCb.filter(F.action == FlowAction.BACK_TO_SERVICES)
)
async def choose_service(
    callback: CallbackQuery, state: FSMContext, tr: Translator, catalog_service: CatalogService
) -> None:
    services = await catalog_service.list_active()
    if not services:
        await state.clear()
        await show(callback, tr("booking.no_services"), kb.to_menu(tr))
        return
    await state.set_state(BookingFlow.choosing_service)
    await show(callback, tr("booking.choose_service"), kb.services_picker(services, tr))


# --- step 2: choose a date ---


async def _show_dates(
    callback: CallbackQuery, state: FSMContext, tr: Translator, slot_service: SlotService
) -> None:
    days = await slot_service.available_dates()
    await state.set_state(BookingFlow.choosing_date)
    if not days:
        await show(callback, tr("booking.no_dates"), kb.to_menu(tr))
        return
    await show(callback, tr("booking.choose_date"), kb.dates_picker(days, tr))


@router.callback_query(BookingFlow.choosing_service, ServiceCb.filter())
async def service_chosen(
    callback: CallbackQuery,
    callback_data: ServiceCb,
    state: FSMContext,
    tr: Translator,
    slot_service: SlotService,
) -> None:
    await slot_service.get_bookable_service(callback_data.service_id)
    await state.update_data(service_id=callback_data.service_id)
    await _show_dates(callback, state, tr, slot_service)


@router.callback_query(
    StateFilter(BookingFlow), FlowCb.filter(F.action == FlowAction.BACK_TO_DATES)
)
async def back_to_dates(
    callback: CallbackQuery, state: FSMContext, tr: Translator, slot_service: SlotService
) -> None:
    await _show_dates(callback, state, tr, slot_service)


# --- step 3: choose a time ---


async def _show_slots(
    callback: CallbackQuery,
    state: FSMContext,
    tr: Translator,
    slot_service: SlotService,
    schedule_cfg: ScheduleConfig,
    *,
    notice: str | None = None,
) -> None:
    data = await state.get_data()
    day = parse_iso_day(data["day"])
    slots = await slot_service.free_slots(data["service_id"], day)
    if not slots:
        await state.set_state(BookingFlow.choosing_date)
        await callback.answer(notice or tr("booking.no_slots", day=tr.day(day)), show_alert=True)
        return
    await state.set_state(BookingFlow.choosing_slot)
    header = f"{notice}\n\n" if notice else ""
    await show(
        callback,
        header + tr("booking.slots", day=tr.day(day)),
        kb.slots_picker(slots, schedule_cfg.tz, tr),
    )


@router.callback_query(BookingFlow.choosing_date, DateCb.filter())
async def date_chosen(
    callback: CallbackQuery,
    callback_data: DateCb,
    state: FSMContext,
    tr: Translator,
    slot_service: SlotService,
    schedule_cfg: ScheduleConfig,
) -> None:
    await state.update_data(day=parse_iso_day(callback_data.day).isoformat())
    await _show_slots(callback, state, tr, slot_service, schedule_cfg)


@router.callback_query(BookingFlow.confirming, FlowCb.filter(F.action == FlowAction.BACK_TO_SLOTS))
async def back_to_slots(
    callback: CallbackQuery,
    state: FSMContext,
    tr: Translator,
    slot_service: SlotService,
    schedule_cfg: ScheduleConfig,
) -> None:
    await _show_slots(callback, state, tr, slot_service, schedule_cfg)


# --- step 4: confirmation ---


@router.callback_query(BookingFlow.choosing_slot, SlotCb.filter())
async def slot_chosen(
    callback: CallbackQuery,
    callback_data: SlotCb,
    state: FSMContext,
    tr: Translator,
    slot_service: SlotService,
    schedule_cfg: ScheduleConfig,
) -> None:
    data = await state.get_data()
    service = await slot_service.get_bookable_service(data["service_id"])
    start = datetime.fromtimestamp(callback_data.ts, UTC)
    await state.update_data(ts=callback_data.ts)
    await state.set_state(BookingFlow.confirming)
    await show(
        callback,
        texts.booking_summary(service, start, schedule_cfg.tz, tr),
        kb.confirm_booking(tr),
    )


@router.callback_query(BookingFlow.confirming, FlowCb.filter(F.action == FlowAction.CONFIRM))
async def booking_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    tr: Translator,
    db_user: User,
    booking_service: BookingService,
    slot_service: SlotService,
    schedule_cfg: ScheduleConfig,
    notifier: Notifier,
) -> None:
    data = await state.get_data()
    start = datetime.fromtimestamp(data["ts"], UTC)
    try:
        booking = await booking_service.create(db_user, data["service_id"], start)
    except SlotUnavailableError as exc:
        # the slot was taken while the user was deciding — offer to choose again
        await _show_slots(callback, state, tr, slot_service, schedule_cfg, notice=tr.error(exc))
        return

    await state.clear()
    await show(
        callback,
        tr("booking.created", booking=texts.booking_line(booking, schedule_cfg.tz, tr)),
        kb.to_menu(tr),
    )
    await notifier.booking_created(booking)


# --- my bookings ---


async def _show_my_bookings(
    callback: CallbackQuery,
    tr: Translator,
    db_user: User,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
    *,
    notice: str | None = None,
) -> None:
    header = f"{notice}\n\n" if notice else ""
    bookings = await booking_service.list_user_upcoming(db_user)
    if not bookings:
        await show(callback, header + tr("my.empty"), kb.to_menu(tr))
        return
    lines = "\n".join(f"• {texts.booking_line(b, schedule_cfg.tz, tr)}" for b in bookings)
    await show(
        callback,
        f"{header}{tr('my.title')}\n\n{lines}",
        kb.my_bookings(bookings, schedule_cfg.tz, tr),
    )


@router.callback_query(MenuCb.filter(F.action == MenuAction.MY_BOOKINGS))
async def my_bookings(
    callback: CallbackQuery,
    state: FSMContext,
    tr: Translator,
    db_user: User,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
) -> None:
    await state.clear()
    await _show_my_bookings(callback, tr, db_user, booking_service, schedule_cfg)


@router.callback_query(MyBookingCb.filter(F.action == MyBookingAction.ASK_CANCEL))
async def ask_cancel(
    callback: CallbackQuery,
    callback_data: MyBookingCb,
    tr: Translator,
    db_user: User,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
) -> None:
    bookings = await booking_service.list_user_upcoming(db_user)
    booking = next((b for b in bookings if b.id == callback_data.booking_id), None)
    if booking is None:
        await callback.answer(tr("error.booking_not_found"), show_alert=True)
        return
    await show(
        callback,
        tr("my.ask_cancel", booking=texts.booking_line(booking, schedule_cfg.tz, tr)),
        kb.confirm_cancel(booking.id, tr),
    )


@router.callback_query(MyBookingCb.filter(F.action == MyBookingAction.CONFIRM_CANCEL))
async def confirm_cancel(
    callback: CallbackQuery,
    callback_data: MyBookingCb,
    tr: Translator,
    db_user: User,
    booking_service: BookingService,
    schedule_cfg: ScheduleConfig,
    notifier: Notifier,
) -> None:
    booking = await booking_service.cancel_by_user(db_user, callback_data.booking_id)
    await notifier.booking_cancelled_by_client(booking)
    await _show_my_bookings(
        callback, tr, db_user, booking_service, schedule_cfg, notice=tr("my.cancelled")
    )

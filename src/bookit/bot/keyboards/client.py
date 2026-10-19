from collections.abc import Sequence
from datetime import date, datetime
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bookit.bot.callbacks import (
    AdminCb,
    AdminSection,
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
from bookit.bot.texts import service_button
from bookit.db.models import Booking, Service


def main_menu(tr: Translator, *, is_admin: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr("btn.book"), callback_data=MenuCb(action=MenuAction.BOOK))
    builder.button(text=tr("btn.my_bookings"), callback_data=MenuCb(action=MenuAction.MY_BOOKINGS))
    if is_admin:
        builder.button(text=tr("btn.admin"), callback_data=AdminCb(section=AdminSection.MENU))
    builder.adjust(2, 1)
    return builder.as_markup()


def to_menu(tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr("btn.to_menu"), callback_data=MenuCb(action=MenuAction.MAIN))
    return builder.as_markup()


def services_picker(services: Sequence[Service], tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(
            text=service_button(service, tr), callback_data=ServiceCb(service_id=service.id)
        )
    builder.button(text=tr("btn.to_menu"), callback_data=MenuCb(action=MenuAction.MAIN))
    builder.adjust(1)
    return builder.as_markup()


def dates_picker(days: Sequence[date], tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day in days:
        builder.button(text=tr.day(day), callback_data=DateCb(day=day.isoformat()))
    builder.adjust(3)
    builder.row()
    builder.button(
        text=tr("btn.back_to_services"),
        callback_data=FlowCb(action=FlowAction.BACK_TO_SERVICES),
    )
    return builder.as_markup()


def slots_picker(slots: Sequence[datetime], tz: ZoneInfo, tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        builder.button(text=tr.hhmm(slot, tz), callback_data=SlotCb(ts=int(slot.timestamp())))
    builder.adjust(4)
    builder.row()
    builder.button(
        text=tr("btn.back_to_dates"), callback_data=FlowCb(action=FlowAction.BACK_TO_DATES)
    )
    return builder.as_markup()


def confirm_booking(tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr("btn.confirm"), callback_data=FlowCb(action=FlowAction.CONFIRM))
    builder.button(text=tr("btn.other_time"), callback_data=FlowCb(action=FlowAction.BACK_TO_SLOTS))
    builder.adjust(1)
    return builder.as_markup()


def my_bookings(bookings: Sequence[Booking], tz: ZoneInfo, tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for booking in bookings:
        builder.button(
            text=tr("btn.cancel_booking", when=tr.moment(booking.start_at, tz)),
            callback_data=MyBookingCb(action=MyBookingAction.ASK_CANCEL, booking_id=booking.id),
        )
    builder.button(text=tr("btn.to_menu"), callback_data=MenuCb(action=MenuAction.MAIN))
    builder.adjust(1)
    return builder.as_markup()


def confirm_cancel(booking_id: int, tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("btn.yes_cancel"),
        callback_data=MyBookingCb(action=MyBookingAction.CONFIRM_CANCEL, booking_id=booking_id),
    )
    builder.button(text=tr("btn.no_keep"), callback_data=MenuCb(action=MenuAction.MY_BOOKINGS))
    builder.adjust(2)
    return builder.as_markup()

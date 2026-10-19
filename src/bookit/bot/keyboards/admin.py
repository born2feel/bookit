from collections.abc import Sequence
from datetime import date
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    MenuAction,
    MenuCb,
)
from bookit.bot.i18n import Translator
from bookit.db.models import Booking, DayOff, Service


def admin_menu(tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, section in (
        ("btn.admin_services", AdminSection.SERVICES),
        ("btn.admin_bookings", AdminSection.BOOKINGS),
        ("btn.admin_days_off", AdminSection.DAYS_OFF),
    ):
        builder.button(text=tr(key), callback_data=AdminCb(section=section))
    builder.button(text=tr("btn.to_main_menu"), callback_data=MenuCb(action=MenuAction.MAIN))
    builder.adjust(1)
    return builder.as_markup()


def services_list(services: Sequence[Service], tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        icon = "✅" if service.is_active else "🙈"
        builder.button(
            text=f"{icon} {service.name}",
            callback_data=AdminServiceCb(action=AdminServiceAction.VIEW, service_id=service.id),
        )
    builder.button(
        text=tr("btn.add_service"), callback_data=AdminServiceCb(action=AdminServiceAction.ADD)
    )
    builder.button(text=tr("btn.to_admin"), callback_data=AdminCb(section=AdminSection.MENU))
    builder.adjust(1)
    return builder.as_markup()


def service_actions(service: Service, tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, action in (
        ("btn.edit_price", AdminServiceAction.EDIT_PRICE),
        ("btn.edit_duration", AdminServiceAction.EDIT_DURATION),
        (
            "btn.hide_service" if service.is_active else "btn.show_service",
            AdminServiceAction.TOGGLE,
        ),
    ):
        builder.button(
            text=tr(key), callback_data=AdminServiceCb(action=action, service_id=service.id)
        )
    builder.button(text=tr("btn.to_services"), callback_data=AdminCb(section=AdminSection.SERVICES))
    builder.adjust(1)
    return builder.as_markup()


def dates_list(days: Sequence[date], tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day in days:
        builder.button(text=tr.day(day), callback_data=AdminDateCb(day=day.isoformat()))
    builder.adjust(3)
    builder.row()
    builder.button(text=tr("btn.to_admin"), callback_data=AdminCb(section=AdminSection.MENU))
    return builder.as_markup()


def day_bookings(
    bookings: Sequence[Booking], day: date, tz: ZoneInfo, tr: Translator
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for booking in bookings:
        builder.button(
            text=f"❌ {tr.hhmm(booking.start_at, tz)} {booking.user.full_name}",
            callback_data=AdminBookingCb(
                action=AdminBookingAction.ASK_CANCEL,
                booking_id=booking.id,
                day=day.isoformat(),
            ),
        )
    builder.button(
        text=tr("btn.back_to_dates"), callback_data=AdminCb(section=AdminSection.BOOKINGS)
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_admin_cancel(booking_id: int, day: date, tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("btn.yes_cancel"),
        callback_data=AdminBookingCb(
            action=AdminBookingAction.CONFIRM_CANCEL, booking_id=booking_id, day=day.isoformat()
        ),
    )
    builder.button(text=tr("btn.no"), callback_data=AdminDateCb(day=day.isoformat()))
    builder.adjust(2)
    return builder.as_markup()


def days_off_list(days_off: Sequence[DayOff], tr: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day_off in days_off:
        builder.button(
            text=tr("btn.remove_day_off", day=f"{day_off.day:%m/%d/%Y}"),
            callback_data=DayOffCb(action=DayOffAction.REMOVE, day_off_id=day_off.id),
        )
    builder.button(text=tr("btn.add_day_off"), callback_data=DayOffCb(action=DayOffAction.ADD))
    builder.button(text=tr("btn.to_admin"), callback_data=AdminCb(section=AdminSection.MENU))
    builder.adjust(1)
    return builder.as_markup()


def to_section(section: AdminSection, text: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=AdminCb(section=section))
    return builder.as_markup()

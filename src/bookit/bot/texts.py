"""Builders for composite messages. User input is always HTML-escaped."""

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from bookit.bot.i18n import Translator
from bookit.db.models import Booking, DayOff, Service


def service_line(service: Service, tr: Translator) -> str:
    return tr(
        "service.line",
        name=escape(service.name),
        duration=tr.minutes(service.duration_min),
        price=tr.price(service.price),
    )


def service_button(service: Service, tr: Translator) -> str:
    # Telegram does not parse button text as HTML, so no escaping is needed
    return tr(
        "service.button",
        name=service.name,
        duration=tr.minutes(service.duration_min),
        price=tr.price(service.price),
    )


def service_card(service: Service, tr: Translator) -> str:
    return tr(
        "service.card",
        name=escape(service.name),
        duration=tr.minutes(service.duration_min),
        price=tr.price(service.price),
        status=tr("service.status_active" if service.is_active else "service.status_hidden"),
    )


def booking_summary(service: Service, start: datetime, tz: ZoneInfo, tr: Translator) -> str:
    return tr(
        "booking.summary",
        service=escape(service.name),
        when=tr.moment(start, tz),
        duration=tr.minutes(service.duration_min),
        price=tr.price(service.price),
    )


def booking_line(booking: Booking, tz: ZoneInfo, tr: Translator) -> str:
    return f"{tr.moment(booking.start_at, tz)} — {escape(booking.service.name)}"


def client_name(booking: Booking) -> str:
    name = escape(booking.user.full_name)
    if booking.user.username:
        name += f" (@{escape(booking.user.username)})"
    return name


def admin_booking_line(booking: Booking, tz: ZoneInfo, tr: Translator) -> str:
    return (
        f"🕐 {tr.hhmm(booking.start_at, tz)}–{tr.hhmm(booking.end_at, tz)} "
        f"{escape(booking.service.name)} — {client_name(booking)}"
    )


def day_off_line(day_off: DayOff, tr: Translator) -> str:
    reason = f" — {escape(day_off.reason)}" if day_off.reason else ""
    return f"🌴 {tr.full_day(day_off.day)}{reason}"

from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from bookit.db.models import Language


class MenuAction(StrEnum):
    MAIN = "main"
    BOOK = "book"
    MY_BOOKINGS = "my"
    LANGUAGE = "lang"


class MenuCb(CallbackData, prefix="menu"):
    action: MenuAction


class LanguageCb(CallbackData, prefix="setlang"):
    language: Language


# --- client booking ---


class ServiceCb(CallbackData, prefix="svc"):
    service_id: int


class DateCb(CallbackData, prefix="date"):
    day: str  # ISO date: CallbackData cannot hold a date directly


class SlotCb(CallbackData, prefix="slot"):
    ts: int  # unix timestamp of the slot start


class FlowAction(StrEnum):
    CONFIRM = "confirm"
    BACK_TO_SERVICES = "services"
    BACK_TO_DATES = "dates"
    BACK_TO_SLOTS = "slots"


class FlowCb(CallbackData, prefix="flow"):
    action: FlowAction


class MyBookingAction(StrEnum):
    ASK_CANCEL = "ask"
    CONFIRM_CANCEL = "confirm"


class MyBookingCb(CallbackData, prefix="mybk"):
    action: MyBookingAction
    booking_id: int


# --- admin panel ---


class AdminSection(StrEnum):
    MENU = "menu"
    SERVICES = "services"
    BOOKINGS = "bookings"
    DAYS_OFF = "daysoff"


class AdminCb(CallbackData, prefix="adm"):
    section: AdminSection


class AdminServiceAction(StrEnum):
    VIEW = "view"
    ADD = "add"
    EDIT_PRICE = "price"
    EDIT_DURATION = "duration"
    TOGGLE = "toggle"


class AdminServiceCb(CallbackData, prefix="admsvc"):
    action: AdminServiceAction
    service_id: int = 0


class AdminDateCb(CallbackData, prefix="admdate"):
    day: str


class AdminBookingAction(StrEnum):
    ASK_CANCEL = "ask"
    CONFIRM_CANCEL = "confirm"


class AdminBookingCb(CallbackData, prefix="admbk"):
    action: AdminBookingAction
    booking_id: int
    day: str  # to return to that day's booking list


class DayOffAction(StrEnum):
    ADD = "add"
    REMOVE = "remove"


class DayOffCb(CallbackData, prefix="dayoff"):
    action: DayOffAction
    day_off_id: int = 0

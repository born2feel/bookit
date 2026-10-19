"""User-facing texts: one message catalog plus US-style formatting.

All strings live in `en.py`, so the handlers contain no hard-coded text and
another language can be added later as one more catalog.
"""

from datetime import date, datetime
from decimal import Decimal
from functools import cache
from zoneinfo import ZoneInfo

from bookit.bot.i18n import en
from bookit.services.exceptions import BookItError

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


class Translator:
    def __init__(self, messages: dict[str, str]) -> None:
        self._messages = messages

    def __call__(self, key: str, /, **params: object) -> str:
        return self._messages[key].format(**params)

    def error(self, exc: BookItError) -> str:
        return self(exc.key, **exc.params)

    @staticmethod
    def day(value: date) -> str:
        """Compact date for buttons: "Wed 10/21"."""
        return f"{WEEKDAYS[value.weekday()]} {value.month}/{value.day}"

    @staticmethod
    def long_day(value: date) -> str:
        """Date in text: "Wed, Oct 21"."""
        return f"{WEEKDAYS[value.weekday()]}, {MONTHS[value.month - 1]} {value.day}"

    @classmethod
    def full_day(cls, value: date) -> str:
        """Date with year: "Wed, Oct 21, 2026"."""
        return f"{cls.long_day(value)}, {value.year}"

    @staticmethod
    def hhmm(moment: datetime, tz: ZoneInfo) -> str:
        """12-hour clock: "3:30 PM" (built manually to stay locale-independent)."""
        local = moment.astimezone(tz)
        hour = local.hour % 12 or 12
        suffix = "AM" if local.hour < 12 else "PM"
        return f"{hour}:{local.minute:02d} {suffix}"

    def moment(self, moment: datetime, tz: ZoneInfo) -> str:
        """Date and time: "Wed, Oct 21 at 3:30 PM"."""
        local = moment.astimezone(tz)
        return self("fmt.datetime", day=self.long_day(local.date()), time=self.hhmm(local, tz))

    def minutes(self, value: int) -> str:
        return self("fmt.minutes", n=value)

    @staticmethod
    def price(value: Decimal) -> str:
        """US dollars: "$1,500" or "$19.99"."""
        if value == value.to_integral_value():
            return f"${int(value):,}"
        return f"${value:,.2f}"


@cache
def get_translator() -> Translator:
    return Translator(en.MESSAGES)

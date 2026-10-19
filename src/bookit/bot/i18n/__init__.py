"""Dependency-free i18n: message dictionaries plus language-aware formatting."""

from datetime import date, datetime
from decimal import Decimal
from functools import cache
from zoneinfo import ZoneInfo

from bookit.bot.i18n import en, ru
from bookit.db.models import DEFAULT_LANGUAGE, Language
from bookit.services.exceptions import BookItError

CATALOGS: dict[Language, dict[str, str]] = {
    Language.RU: ru.MESSAGES,
    Language.EN: en.MESSAGES,
}

LANGUAGE_NAMES: dict[Language, str] = {
    Language.RU: "🇷🇺 Русский",
    Language.EN: "🇬🇧 English",
}


class Translator:
    def __init__(self, language: Language) -> None:
        self.language = language
        self._messages = CATALOGS[language]

    def __call__(self, key: str, /, **params: object) -> str:
        return self._messages[key].format(**params)

    def error(self, exc: BookItError) -> str:
        return self(exc.key, **exc.params)

    def day(self, value: date) -> str:
        return f"{value:%d.%m} ({self(f'weekday.{value.weekday()}')})"

    def full_day(self, value: date) -> str:
        return f"{value:%d.%m.%Y} ({self(f'weekday.{value.weekday()}')})"

    @staticmethod
    def hhmm(moment: datetime, tz: ZoneInfo) -> str:
        return f"{moment.astimezone(tz):%H:%M}"

    def moment(self, moment: datetime, tz: ZoneInfo) -> str:
        local = moment.astimezone(tz)
        return self("fmt.datetime", day=self.day(local.date()), time=f"{local:%H:%M}")

    def minutes(self, value: int) -> str:
        return self("fmt.minutes", n=value)

    @staticmethod
    def price(value: Decimal) -> str:
        if value == value.to_integral_value():
            text = f"{int(value):,}".replace(",", " ")
        else:
            text = f"{value:,.2f}".replace(",", " ").replace(".", ",")
        return f"{text} ₽"


@cache
def get_translator(language: Language = DEFAULT_LANGUAGE) -> Translator:
    return Translator(language)

import re
import string
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from bookit.bot.i18n import CATALOGS, get_translator
from bookit.db.models import Language
from bookit.services import exceptions
from tests.conftest import TZ

SRC = Path(__file__).resolve().parents[1] / "src" / "bookit"
KEY_PATTERN = re.compile(r"""["']((?:[a-z]+)\.[a-z_]+)["']""")
KNOWN_PREFIXES = (
    "admin.",
    "booking.",
    "btn.",
    "error.",
    "language.",
    "menu.",
    "my.",
    "notify.",
    "service.",
    "validation.",
)


def placeholders(template: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


def test_catalogs_have_same_keys() -> None:
    ru, en = CATALOGS[Language.RU], CATALOGS[Language.EN]

    assert set(ru) - set(en) == set(), "keys present in ru but missing in en"
    assert set(en) - set(ru) == set(), "keys present in en but missing in ru"


@pytest.mark.parametrize("key", sorted(CATALOGS[Language.RU]))
def test_translations_use_same_placeholders(key: str) -> None:
    assert placeholders(CATALOGS[Language.RU][key]) == placeholders(CATALOGS[Language.EN][key])


def test_every_domain_error_is_translated() -> None:
    error_classes = [
        obj
        for obj in vars(exceptions).values()
        if isinstance(obj, type) and issubclass(obj, exceptions.BookItError)
    ]
    for language, catalog in CATALOGS.items():
        for cls in error_classes:
            assert cls.key in catalog, f"{cls.__name__}: missing translation {cls.key} ({language})"


def test_every_key_used_in_code_exists() -> None:
    used = {
        key
        for path in SRC.rglob("*.py")
        if "i18n" not in path.parts
        for key in KEY_PATTERN.findall(path.read_text(encoding="utf-8"))
        if key.startswith(KNOWN_PREFIXES)
    }
    assert used, "the regex found nothing — the test is broken"
    for catalog in CATALOGS.values():
        assert used - set(catalog) == set()


def test_formatting_depends_on_language() -> None:
    moment = datetime(2026, 10, 20, 7, 30, tzinfo=UTC)  # 10:30 Moscow time, Tuesday
    ru, en = get_translator(Language.RU), get_translator(Language.EN)

    assert ru.moment(moment, TZ) == "20.10 (вт) в 10:30"
    assert en.moment(moment, TZ) == "20.10 (Tue) at 10:30"
    assert en.full_day(date(2026, 10, 20)) == "20.10.2026 (Tue)"
    assert ru.minutes(45) == "45 мин"
    assert en.minutes(45) == "45 min"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(Decimal("1500"), "1 500 ₽"), (Decimal("1499.90"), "1 499,90 ₽"), (Decimal("0"), "0 ₽")],
)
def test_price_format(value: Decimal, expected: str) -> None:
    assert get_translator(Language.EN).price(value) == expected


def test_domain_error_is_rendered_with_params() -> None:
    error = exceptions.DayHasBookingsError(3)

    assert "(3)" in get_translator(Language.EN).error(error)
    assert "(3)" in get_translator(Language.RU).error(error)

import re
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from bookit.bot.i18n import en, get_translator
from bookit.services import exceptions
from tests.conftest import TZ

SRC = Path(__file__).resolve().parents[1] / "src" / "bookit"
KEY_PATTERN = re.compile(r"""["']((?:[a-z]+)\.[a-z_]+)["']""")
KNOWN_PREFIXES = (
    "admin.",
    "booking.",
    "btn.",
    "cmd.",
    "error.",
    "menu.",
    "my.",
    "notify.",
    "service.",
    "validation.",
)


def test_every_domain_error_has_a_message() -> None:
    error_classes = [
        obj
        for obj in vars(exceptions).values()
        if isinstance(obj, type) and issubclass(obj, exceptions.BookItError)
    ]
    for cls in error_classes:
        assert cls.key in en.MESSAGES, f"{cls.__name__}: missing message {cls.key}"


def test_every_key_used_in_code_exists() -> None:
    used = {
        key
        for path in SRC.rglob("*.py")
        if "i18n" not in path.parts
        for key in KEY_PATTERN.findall(path.read_text(encoding="utf-8"))
        if key.startswith(KNOWN_PREFIXES)
    }
    assert used, "the regex found nothing — the test is broken"
    assert used - set(en.MESSAGES) == set()


@pytest.mark.parametrize(
    ("hour", "minute", "expected"),
    [(0, 5, "12:05 AM"), (9, 0, "9:00 AM"), (12, 0, "12:00 PM"), (15, 30, "3:30 PM")],
)
def test_twelve_hour_clock(hour: int, minute: int, expected: str) -> None:
    moment = datetime(2026, 10, 21, hour, minute, tzinfo=TZ)

    assert get_translator().hhmm(moment, TZ) == expected


def test_us_date_formats() -> None:
    tr = get_translator()
    moment = datetime(2026, 10, 21, 19, 30, tzinfo=UTC)  # 3:30 PM in New York, Wednesday

    assert tr.moment(moment, TZ) == "Wed, Oct 21 at 3:30 PM"
    assert tr.day(date(2026, 10, 21)) == "Wed 10/21"
    assert tr.full_day(date(2026, 10, 21)) == "Wed, Oct 21, 2026"
    assert tr.minutes(45) == "45 min"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("35"), "$35"),
        (Decimal("1500"), "$1,500"),
        (Decimal("19.90"), "$19.90"),
        (Decimal("1499.99"), "$1,499.99"),
        (Decimal("0"), "$0"),
    ],
)
def test_price_in_dollars(value: Decimal, expected: str) -> None:
    assert get_translator().price(value) == expected


def test_domain_error_is_rendered_with_params() -> None:
    assert "(3)" in get_translator().error(exceptions.DayHasBookingsError(3))
    assert "$1,000,000" in get_translator().error(
        exceptions.ValidationError("validation.price_range", max=Decimal("1000000"))
    )

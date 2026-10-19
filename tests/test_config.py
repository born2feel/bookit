import pytest
from pydantic import ValidationError

from bookit.config import Settings


def make(**env: str) -> Settings:
    return Settings(_env_file=None, **env)  # type: ignore[call-arg]


def test_admin_ids_are_parsed_from_comma_separated_string() -> None:
    settings = make(bot_token="123:abc", admin_ids="1, 2,3")

    assert settings.admin_ids == frozenset({1, 2, 3})


def test_empty_admin_ids() -> None:
    assert make(bot_token="123:abc", admin_ids="").admin_ids == frozenset()


def test_empty_token_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(bot_token="  ")


def test_working_hours_must_be_ordered() -> None:
    with pytest.raises(ValidationError):
        make(bot_token="123:abc", work_start="18:00", work_end="10:00")


def test_unknown_timezone_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(bot_token="123:abc", timezone="Mars/Olympus")

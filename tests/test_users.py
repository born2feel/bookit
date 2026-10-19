import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import DEFAULT_LANGUAGE, Language
from bookit.services import UserService
from bookit.services.users import language_from_telegram


async def test_register_is_idempotent_and_updates_profile(session: AsyncSession) -> None:
    users = UserService(session)

    first = await users.register(tg_id=42, full_name="Ivan", username="ivan")
    second = await users.register(tg_id=42, full_name="Ivan Petrov", username=None)

    assert first.id == second.id
    assert second.full_name == "Ivan Petrov"
    assert second.username is None


@pytest.mark.parametrize(
    ("code", "expected"),
    [("ru", Language.RU), ("ru-RU", Language.RU), ("en", Language.EN), ("de", Language.EN)],
)
def test_language_from_telegram(code: str, expected: Language) -> None:
    assert language_from_telegram(code) is expected


def test_language_from_telegram_without_code() -> None:
    assert language_from_telegram(None) is DEFAULT_LANGUAGE


async def test_first_visit_takes_language_from_telegram(session: AsyncSession) -> None:
    user = await UserService(session).register(42, "John", None, language_code="en-US")

    assert user.language is Language.EN


async def test_chosen_language_is_not_overwritten_by_telegram(session: AsyncSession) -> None:
    users = UserService(session)
    user = await users.register(42, "John", None, language_code="en")
    await users.set_language(user, Language.RU)

    again = await users.register(42, "John", None, language_code="en")

    assert again.language is Language.RU


async def test_languages_for_admins(session: AsyncSession) -> None:
    users = UserService(session)
    await users.register(1, "Admin EN", None, language_code="en")
    await users.register(2, "Admin RU", None, language_code="ru")

    languages = await users.languages_for([1, 2, 3])

    assert languages == {1: Language.EN, 2: Language.RU, 3: DEFAULT_LANGUAGE}

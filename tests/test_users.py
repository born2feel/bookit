from sqlalchemy.ext.asyncio import AsyncSession

from bookit.services import UserService


async def test_register_is_idempotent_and_updates_profile(session: AsyncSession) -> None:
    users = UserService(session)

    first = await users.register(tg_id=42, full_name="Ivan", username="ivan")
    second = await users.register(tg_id=42, full_name="Ivan Petrov", username=None)

    assert first.id == second.id
    assert second.full_name == "Ivan Petrov"
    assert second.username is None

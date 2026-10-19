from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message


class IsAdmin(Filter):
    """Lets through only users listed in ADMIN_IDS (admin_ids comes from workflow data)."""

    async def __call__(self, event: Message | CallbackQuery, admin_ids: frozenset[int]) -> bool:
        return event.from_user is not None and event.from_user.id in admin_ids

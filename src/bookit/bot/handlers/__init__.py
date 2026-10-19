from aiogram import Router

from bookit.bot.handlers import admin, client, common, errors, fallback


def build_root_router() -> Router:
    root = Router(name="root")
    root.errors.register(errors.on_error)
    # order matters: commands (/cancel) must work in any FSM state,
    # and fallback only catches what the other routers did not handle
    root.include_routers(common.router, client.router, admin.router, fallback.router)
    return root

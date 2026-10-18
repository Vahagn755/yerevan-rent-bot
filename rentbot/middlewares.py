from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class UserMiddleware(BaseMiddleware):
    """Registers the user on first contact and injects `lang` and `is_new_user` into handlers."""

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        user = data.get("event_from_user")
        if user and not user.is_bot:
            lang, is_new = await data["db"].ensure_user(user.id, user.language_code)
        else:
            lang, is_new = "hy", False
        data["lang"] = lang
        data["is_new_user"] = is_new
        return await handler(event, data)

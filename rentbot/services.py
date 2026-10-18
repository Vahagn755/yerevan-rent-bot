"""Sending new listings to every subscriber whose filter matches."""
import asyncio
import logging
from collections.abc import Coroutine, Mapping

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import LinkPreviewOptions

from .db import Database
from .keyboards import card_kb
from .matching import matches
from .render import format_card

log = logging.getLogger(__name__)

CAPTION_LIMIT = 1024
SEND_DELAY = 0.05  # stay well under Telegram's ~30 messages/second limit

_tasks: set[asyncio.Task] = set()


def spawn(coro: Coroutine) -> asyncio.Task:
    """Run in the background and keep a reference so the task isn't garbage-collected."""
    task = asyncio.create_task(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return task


class AlbumCollector:
    """Telegram delivers an album as separate messages sharing a media_group_id.
    Collect them for a moment, then hand over the caption and every photo at once."""

    def __init__(self, wait: float = 1.5):
        self.wait = wait
        self._groups: dict[str, dict] = {}

    def add(self, group_id: str, text: str | None, photo_id: str | None, first_message, on_done) -> None:
        g = self._groups.setdefault(group_id, {"text": "", "photos": [], "message": first_message,
                                               "on_done": on_done, "timer": None})
        if text and not g["text"]:
            g["text"], g["message"] = text, first_message
        if photo_id:
            g["photos"].append(photo_id)
        if g["timer"]:
            g["timer"].cancel()
        g["timer"] = asyncio.get_running_loop().call_later(self.wait, self._finish, group_id)

    def _finish(self, group_id: str) -> None:
        g = self._groups.pop(group_id, None)
        if g:
            spawn(g["on_done"](g["text"], g["photos"], g["message"]))


albums = AlbumCollector()


async def send_card(bot: Bot, chat_id: int, listing: Mapping, lang: str) -> None:
    text = format_card(listing, lang)
    kb = card_kb(lang, listing)
    if listing["photo_id"]:
        if len(text) <= CAPTION_LIMIT:
            await bot.send_photo(chat_id, listing["photo_id"], caption=text, reply_markup=kb)
            return
        await bot.send_photo(chat_id, listing["photo_id"])
    await bot.send_message(chat_id, text, reply_markup=kb,
                           link_preview_options=LinkPreviewOptions(is_disabled=True))


async def broadcast(bot: Bot, db: Database, listing: Mapping, exclude_user: int | None = None) -> int:
    sent = 0
    for sub in await db.subscribers():
        uid = sub["user_id"]
        if uid == exclude_user or not matches(sub, listing):
            continue
        for attempt in range(2):
            try:
                await send_card(bot, uid, listing, sub["lang"])
                sent += 1
                break
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except TelegramForbiddenError:
                await db.mark_blocked(uid)
                break
            except TelegramBadRequest as e:
                log.warning("send to %s failed: %s", uid, e)
                break
        await asyncio.sleep(SEND_DELAY)
    log.info("listing %s sent to %s users", listing["id"], sent)
    return sent

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

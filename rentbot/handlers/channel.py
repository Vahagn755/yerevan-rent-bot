"""Collect listings from partner channels where the bot is an admin."""
from aiogram import Bot, F, Router
from aiogram.types import Message

from ..actions import import_post
from ..config import Config
from ..db import Database
from ..services import albums

router = Router(name="channel")


@router.channel_post(F.text | F.caption | F.photo)
async def on_channel_post(message: Message, db: Database, cfg: Config, bot: Bot) -> None:
    if cfg.allowed_channels and message.chat.id not in cfg.allowed_channels:
        return
    photo = message.photo[-1].file_id if message.photo else None

    async def done(text: str, photos: list[str], first: Message) -> None:
        if not text:
            return
        link = f"https://t.me/{first.chat.username}/{first.message_id}" if first.chat.username else None
        await import_post(bot, db, cfg, text, photos, link)

    if message.media_group_id:
        albums.add(message.media_group_id, message.caption, photo, message, done)
    else:
        await done(message.text or message.caption or "", [photo] if photo else [], message)

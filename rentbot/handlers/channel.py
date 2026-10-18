"""Collect listings from partner channels where the bot is an admin."""
from aiogram import Bot, F, Router
from aiogram.types import Message

from ..actions import import_post
from ..config import Config
from ..db import Database

router = Router(name="channel")


@router.channel_post(F.text | F.caption)
async def on_channel_post(message: Message, db: Database, cfg: Config, bot: Bot) -> None:
    if cfg.allowed_channels and message.chat.id not in cfg.allowed_channels:
        return
    link = (f"https://t.me/{message.chat.username}/{message.message_id}"
            if message.chat.username else None)
    await import_post(bot, db, cfg, message.text or message.caption or "",
                      message.photo[-1].file_id if message.photo else None, link)

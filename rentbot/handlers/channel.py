"""Collect listings from partner channels where the bot is an admin."""
import time

from aiogram import Bot, F, Router
from aiogram.types import Message

from ..config import Config
from ..db import Database
from ..parser import parse_listing, text_hash
from ..services import broadcast, spawn

router = Router(name="channel")

DUPLICATE_WINDOW = 7 * 86400
DESC_MAX = 700


@router.channel_post(F.text | F.caption)
async def on_channel_post(message: Message, db: Database, cfg: Config, bot: Bot) -> None:
    if cfg.allowed_channels and message.chat.id not in cfg.allowed_channels:
        return
    text = message.text or message.caption or ""
    parsed = parse_listing(text, cfg.amd_per_usd)
    if not parsed:
        return
    if await db.is_blacklisted(parsed.phone):
        return
    h = text_hash(text)
    if await db.is_duplicate(h, int(time.time()) - DUPLICATE_WINDOW):
        return

    link = (f"https://t.me/{message.chat.username}/{message.message_id}"
            if message.chat.username else None)
    listing_id = await db.add_listing(
        source="channel", district=parsed.district, rooms=parsed.rooms,
        price_amount=parsed.price.amount, currency=parsed.price.currency,
        price_usd=parsed.price.usd, pets=parsed.pets, description=text[:DESC_MAX],
        phone=parsed.phone, photo_id=message.photo[-1].file_id if message.photo else None,
        link=link, text_hash=h,
    )
    spawn(broadcast(bot, db, await db.get_listing(listing_id)))

"""Business actions shared by the chat handlers and the Mini App API."""
import logging
import time
from dataclasses import dataclass

from aiogram import Bot

from .config import Config
from .db import Database
from .parser import format_phone, text_hash
from .services import broadcast, spawn

log = logging.getLogger(__name__)

DUPLICATE_WINDOW = 7 * 86400
DESC_MAX = 800


@dataclass
class NewListing:
    district: str
    rooms: int
    price_amount: float
    currency: str
    price_usd: float
    pets: int
    description: str
    phone: str
    photo_id: str | None = None


async def check_can_post(db: Database, cfg: Config, owner_id: int) -> str | None:
    """Returns an error code ('limit') or None."""
    n = await db.count_user_listings_since(owner_id, int(time.time()) - 86400)
    return "limit" if n >= cfg.daily_post_limit else None


def listing_hash(item: NewListing) -> str:
    return text_hash(f"{item.phone}|{item.district}|{item.rooms}|{round(item.price_usd)}")


async def precheck_listing(db: Database, cfg: Config, owner_id: int, item: NewListing) -> str | None:
    """Error code ('limit' | 'blacklisted' | 'duplicate') or None if the listing can be published."""
    if err := await check_can_post(db, cfg, owner_id):
        return err
    if await db.is_blacklisted(item.phone):
        return "blacklisted"
    if await db.is_duplicate(listing_hash(item), int(time.time()) - DUPLICATE_WINDOW):
        return "duplicate"
    return None


async def publish_listing(bot: Bot, db: Database, owner_id: int, item: NewListing,
                          on_sent=None) -> int:
    """Saves the listing and sends it to matching subscribers in the background."""
    listing_id = await db.add_listing(
        source="bot", owner_id=owner_id, district=item.district, rooms=item.rooms,
        price_amount=item.price_amount, currency=item.currency, price_usd=item.price_usd,
        pets=item.pets, description=item.description[:DESC_MAX], phone=item.phone,
        photo_id=item.photo_id, text_hash=listing_hash(item),
    )
    listing = await db.get_listing(listing_id)

    async def notify() -> None:
        n = await broadcast(bot, db, listing, exclude_user=owner_id)
        if on_sent:
            await on_sent(n)

    spawn(notify())
    return listing_id


async def report_listing(bot: Bot, db: Database, cfg: Config, listing_id: int, user_id: int,
                         kind: str) -> str:
    """Returns 'ok' | 'already' | 'own' | 'not_found'."""
    listing = await db.get_listing(listing_id)
    if not listing:
        return "not_found"
    if listing["owner_id"] == user_id:
        return "own"
    if not await db.add_report(listing_id, user_id, kind):
        return "already"

    count = await db.report_count(listing)
    if count >= cfg.report_limit and listing["status"] == "active":
        if listing["phone"]:
            await db.blacklist_phone(listing["phone"], f"{count} reports")
        else:
            await db.set_listing_status(listing_id, "blocked")
        note = (f"🚫 Listing #{listing_id} blocked after {count} reports ({kind}). "
                f"Phone: {format_phone(listing['phone'])}\nUndo: /unban {listing['phone'] or ''}")
        for admin_id in cfg.admin_ids:
            try:
                await bot.send_message(admin_id, note)
            except Exception as e:  # an admin who never started the bot
                log.warning("cannot notify admin %s: %s", admin_id, e)
    return "ok"

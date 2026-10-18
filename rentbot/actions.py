"""Business actions shared by the chat handlers and the Mini App API."""
import json
import logging
import time
from dataclasses import dataclass

from aiogram import Bot

from .config import Config
from .db import Database
from .parser import (format_phone, parse_district, parse_listing, parse_price, parse_rooms,
                     text_hash)
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
    details: dict | None = None


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
        photo_id=item.photo_id, details=json.dumps(item.details or {}, ensure_ascii=False),
        text_hash=listing_hash(item),
    )
    listing = await db.get_listing(listing_id)

    async def notify() -> None:
        n = await broadcast(bot, db, listing, exclude_user=owner_id)
        if on_sent:
            await on_sent(n)

    spawn(notify())
    return listing_id


IMPORT_DESC_MAX = 700


@dataclass
class ImportResult:
    status: str  # 'ok' | 'not_listing' | 'blacklisted' | 'duplicate'
    listing_id: int | None = None
    missing: tuple[str, ...] = ()


async def import_post(bot: Bot, db: Database, cfg: Config, text: str, photo_ids: list[str],
                      link: str | None, on_sent=None) -> ImportResult:
    """Turns a channel post (or a post an admin forwarded) into a listing and sends it out."""
    parsed = parse_listing(text, cfg.amd_per_usd)
    if not parsed:
        missing = []
        if not parse_price(text, cfg.amd_per_usd):
            missing.append("price")
        if parse_district(text) is None and parse_rooms(text) is None:
            missing.append("district_or_rooms")
        return ImportResult("not_listing", missing=tuple(missing))
    if await db.is_blacklisted(parsed.phone):
        return ImportResult("blacklisted")
    h = text_hash(text)
    if await db.is_duplicate(h, int(time.time()) - DUPLICATE_WINDOW):
        return ImportResult("duplicate")

    listing_id = await db.add_listing(
        source="channel", district=parsed.district, rooms=parsed.rooms,
        price_amount=parsed.price.amount, currency=parsed.price.currency,
        price_usd=parsed.price.usd, pets=parsed.pets, agent=int(parsed.agent),
        description=text[:IMPORT_DESC_MAX],
        phone=parsed.phone, photo_id=photo_ids[0] if photo_ids else None,
        photos=",".join(photo_ids[:10]), link=link, text_hash=h,
        details=json.dumps(parsed.details or {}, ensure_ascii=False),
    )
    listing = await db.get_listing(listing_id)

    async def notify() -> None:
        n = await broadcast(bot, db, listing)
        if on_sent:
            await on_sent(n)

    spawn(notify())
    return ImportResult("ok", listing_id)


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

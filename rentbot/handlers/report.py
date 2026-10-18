"""Users report agents and scams; after REPORT_LIMIT reports the phone number is blacklisted."""
import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from ..config import Config
from ..db import Database
from ..parser import format_phone
from ..texts import t

router = Router(name="report")
log = logging.getLogger(__name__)


@router.callback_query(F.data.regexp(r"^rep:(agent|fake):\d+$"))
async def on_report(cb: CallbackQuery, db: Database, lang: str, cfg: Config, bot: Bot) -> None:
    _, kind, raw_id = cb.data.split(":")
    listing = await db.get_listing(int(raw_id))
    if not listing:
        await cb.answer(t("not_found", lang))
        return
    if listing["owner_id"] == cb.from_user.id:
        await cb.answer(t("rep_own", lang))
        return
    if not await db.add_report(listing["id"], cb.from_user.id, kind):
        await cb.answer(t("rep_already", lang))
        return
    await cb.answer(t("rep_thanks", lang))

    count = await db.report_count(listing)
    if count < cfg.report_limit or listing["status"] != "active":
        return
    if listing["phone"]:
        await db.blacklist_phone(listing["phone"], f"{count} reports")
    else:
        await db.set_listing_status(listing["id"], "blocked")
    note = (f"🚫 Listing #{listing['id']} blocked after {count} reports "
            f"({kind}). Phone: {format_phone(listing['phone'])}\nUndo: /unban {listing['phone'] or ''}")
    for admin_id in cfg.admin_ids:
        try:
            await bot.send_message(admin_id, note)
        except Exception as e:  # an admin who never started the bot
            log.warning("cannot notify admin %s: %s", admin_id, e)

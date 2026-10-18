"""Users report agents and scams; after REPORT_LIMIT reports the phone number is blacklisted."""
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from ..actions import report_listing
from ..config import Config
from ..db import Database
from ..texts import t

router = Router(name="report")

REPLIES = {"ok": "rep_thanks", "already": "rep_already", "own": "rep_own", "not_found": "not_found"}


@router.callback_query(F.data.regexp(r"^rep:(agent|fake):\d+$"))
async def on_report(cb: CallbackQuery, db: Database, lang: str, cfg: Config, bot: Bot) -> None:
    _, kind, raw_id = cb.data.split(":")
    result = await report_listing(bot, db, cfg, int(raw_id), cb.from_user.id, kind)
    await cb.answer(t(REPLIES[result], lang))

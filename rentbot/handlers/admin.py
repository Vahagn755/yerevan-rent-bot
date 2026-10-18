from aiogram import Router
from aiogram.filters import Command, CommandObject, Filter
from aiogram.types import Message

from ..config import Config
from ..db import Database
from ..parser import format_phone, normalize_phone

router = Router(name="admin")


class IsAdmin(Filter):
    async def __call__(self, message: Message, cfg: Config) -> bool:
        return bool(message.from_user and message.from_user.id in cfg.admin_ids)


router.message.filter(IsAdmin())


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database) -> None:
    s = await db.stats()
    await message.answer(
        "📊 <b>Stats</b>\n"
        f"Users: {s['users']}\nSubscribed: {s['subscribers']}\n"
        f"Active listings: {s['active_listings']}\nNew in 24h: {s['listings_24h']}\n"
        f"Blacklisted numbers: {s['blacklist']}"
    )


@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject, db: Database) -> None:
    phone = normalize_phone(command.args or "")
    if not phone:
        await message.answer("Usage: /ban 091123456")
        return
    await db.blacklist_phone(phone, f"admin {message.from_user.id}")
    await message.answer(f"🚫 {format_phone(phone)} blacklisted")


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject, db: Database) -> None:
    phone = normalize_phone(command.args or "")
    if not phone:
        await message.answer("Usage: /unban 091123456")
        return
    await db.unblacklist_phone(phone)
    await message.answer(f"✅ {format_phone(phone)} removed from blacklist")


@router.message(Command("del"))
async def cmd_delete(message: Message, command: CommandObject, db: Database) -> None:
    if not (command.args or "").strip().isdigit():
        await message.answer("Usage: /del 123")
        return
    await db.set_listing_status(int(command.args.strip()), "deleted")
    await message.answer("🗑 Deleted")

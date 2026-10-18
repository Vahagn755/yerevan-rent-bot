from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, MessageOriginChannel

from ..actions import import_post
from ..config import Config
from ..db import Database
from ..parser import format_phone, normalize_phone
from ..render import format_card
from ..texts import t

router = Router(name="admin")


class IsAdmin(Filter):
    async def __call__(self, message: Message, cfg: Config) -> bool:
        return bool(message.from_user and message.from_user.id in cfg.admin_ids)


router.message.filter(IsAdmin())


def _source_link(message: Message) -> str | None:
    origin = message.forward_origin
    if isinstance(origin, MessageOriginChannel) and origin.chat.username:
        return f"https://t.me/{origin.chat.username}/{origin.message_id}"
    return None


@router.message(F.forward_origin, F.text | F.caption)
async def on_forward(message: Message, state: FSMContext, db: Database, cfg: Config, bot: Bot,
                     lang: str) -> None:
    """An admin forwards a post from any channel or chat: it becomes a listing."""
    await state.clear()
    text = message.text or message.caption or ""
    photo_id = message.photo[-1].file_id if message.photo else None

    async def on_sent(n: int) -> None:
        await bot.send_message(message.chat.id, t("sent_to", lang, n=n))

    res = await import_post(bot, db, cfg, text, photo_id, _source_link(message), on_sent)
    if res.status == "ok":
        listing = await db.get_listing(res.listing_id)
        await message.reply(f"{t('fwd_ok', lang, id=res.listing_id)}\n\n{format_card(listing, lang)}"
                            f"\n\n{t('fwd_undo', lang, id=res.listing_id)}")
    elif res.status == "not_listing":
        missing = ", ".join(t("miss_" + m, lang) for m in res.missing) or t("miss_offer", lang)
        await message.reply(t("fwd_not", lang, missing=missing))
    else:
        await message.reply(t({"duplicate": "duplicate", "blacklisted": "blacklisted"}[res.status], lang))


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

"""A landlord's own listings: view and take down once rented."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..db import Database
from ..keyboards import own_listing_kb
from ..render import format_card
from ..texts import t, variants

router = Router(name="own")


@router.message(Command("my"))
@router.message(F.text.in_(variants("btn_my")))
async def my_listings(message: Message, state: FSMContext, db: Database, lang: str) -> None:
    await state.clear()
    rows = await db.user_listings(message.from_user.id)
    if not rows:
        await message.answer(t("my_empty", lang))
        return
    for row in rows:
        await message.answer(format_card(row, lang), reply_markup=own_listing_kb(lang, row["id"]))


@router.callback_query(F.data.startswith("own:done:"))
async def mark_rented(cb: CallbackQuery, db: Database, lang: str) -> None:
    listing = await db.get_listing(int(cb.data.rsplit(":", 1)[1]))
    if not listing or listing["owner_id"] != cb.from_user.id:
        await cb.answer(t("not_found", lang))
        return
    await db.set_listing_status(listing["id"], "rented")
    await cb.message.edit_text(f"<s>{format_card(listing, lang)}</s>\n\n{t('removed', lang)}")
    await cb.answer()

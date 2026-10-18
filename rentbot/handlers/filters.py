from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from ..config import Config
from ..db import Database
from ..districts import DISTRICTS
from ..keyboards import districts_kb, filter_menu_kb, rooms_kb
from ..matching import join_set, parse_set
from ..parser import parse_price_range
from ..render import format_filter
from ..texts import t, variants

router = Router(name="filters")


class FilterStates(StatesGroup):
    price = State()


async def _edit(cb: CallbackQuery, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:  # "message is not modified"
        pass


@router.message(Command("filter"))
@router.message(F.text.in_(variants("btn_filter")))
async def open_filter(message: Message, state: FSMContext, db: Database, lang: str) -> None:
    await state.clear()
    flt = await db.get_filter(message.from_user.id)
    await message.answer(format_filter(flt, lang), reply_markup=filter_menu_kb(lang))


@router.callback_query(F.data == "flt:menu")
async def back_to_menu(cb: CallbackQuery, state: FSMContext, db: Database, lang: str) -> None:
    await state.clear()
    flt = await db.get_filter(cb.from_user.id)
    await _edit(cb, format_filter(flt, lang), filter_menu_kb(lang))
    await cb.answer()


# ---- price ----
@router.callback_query(F.data == "flt:price")
async def ask_price(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(FilterStates.price)
    await cb.message.answer(t("ask_price", lang))
    await cb.answer()


@router.message(FilterStates.price, F.text)
async def set_price(message: Message, state: FSMContext, db: Database, lang: str,
                    cfg: Config) -> None:
    rng = parse_price_range(message.text, cfg.amd_per_usd)
    if rng is None:
        await message.answer(t("price_bad", lang))
        return
    await state.clear()
    flt = await db.update_filter(message.from_user.id, price_min=rng[0], price_max=rng[1])
    await message.answer(format_filter(flt, lang), reply_markup=filter_menu_kb(lang))


# ---- rooms ----
@router.callback_query(F.data == "flt:rooms")
async def show_rooms(cb: CallbackQuery, db: Database, lang: str) -> None:
    flt = await db.get_filter(cb.from_user.id)
    await _edit(cb, t("choose_rooms", lang), rooms_kb(lang, parse_set(flt["rooms"]), "flt:room:", True))
    await cb.answer()


@router.callback_query(F.data.startswith("flt:room:"))
async def toggle_room(cb: CallbackQuery, db: Database, lang: str) -> None:
    n = cb.data.rsplit(":", 1)[1]
    if n not in {"1", "2", "3", "4", "5"}:
        await cb.answer()
        return
    flt = await db.get_filter(cb.from_user.id)
    rooms = parse_set(flt["rooms"]) ^ {n}
    await db.update_filter(cb.from_user.id, rooms=join_set(rooms))
    await _edit(cb, t("choose_rooms", lang), rooms_kb(lang, rooms, "flt:room:", True))
    await cb.answer()


# ---- districts ----
@router.callback_query(F.data == "flt:districts")
async def show_districts(cb: CallbackQuery, db: Database, lang: str) -> None:
    flt = await db.get_filter(cb.from_user.id)
    await _edit(cb, t("choose_districts", lang),
                districts_kb(lang, parse_set(flt["districts"]), "flt:d:", True))
    await cb.answer()


@router.callback_query(F.data.startswith("flt:d:"))
async def toggle_district(cb: CallbackQuery, db: Database, lang: str) -> None:
    key = cb.data.split(":", 2)[2]
    if key not in DISTRICTS:
        await cb.answer()
        return
    flt = await db.get_filter(cb.from_user.id)
    districts = parse_set(flt["districts"]) ^ {key}
    await db.update_filter(cb.from_user.id, districts=join_set(districts))
    await _edit(cb, t("choose_districts", lang), districts_kb(lang, districts, "flt:d:", True))
    await cb.answer()


# ---- pets / reset / done ----
@router.callback_query(F.data == "flt:pets")
async def toggle_pets(cb: CallbackQuery, db: Database, lang: str) -> None:
    flt = await db.get_filter(cb.from_user.id)
    flt = await db.update_filter(cb.from_user.id, pets=0 if flt["pets"] else 1)
    await _edit(cb, format_filter(flt, lang), filter_menu_kb(lang))
    await cb.answer()


@router.callback_query(F.data == "flt:reset")
async def reset_filter(cb: CallbackQuery, db: Database, lang: str) -> None:
    flt = await db.update_filter(cb.from_user.id, price_min=None, price_max=None,
                                 rooms="", districts="", pets=0)
    await _edit(cb, format_filter(flt, lang), filter_menu_kb(lang))
    await cb.answer()


@router.callback_query(F.data == "flt:done")
async def done(cb: CallbackQuery, state: FSMContext, db: Database, lang: str) -> None:
    await state.clear()
    flt = await db.get_filter(cb.from_user.id)
    await _edit(cb, format_filter(flt, lang).rsplit("\n\n", 1)[0] + "\n\n" + t("filter_saved", lang))
    await cb.answer()

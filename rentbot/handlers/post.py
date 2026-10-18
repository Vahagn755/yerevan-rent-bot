"""Landlords post a listing step by step: district → rooms → price → pets → text → photo → phone."""
import time

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ..config import Config
from ..db import Database
from ..districts import DISTRICTS
from ..keyboards import districts_kb, main_menu, phone_kb, rooms_kb, skip_kb, yes_no_kb
from ..parser import normalize_phone, parse_price_input, text_hash
from ..services import broadcast, spawn
from ..texts import t, variants

router = Router(name="post")

DESC_MAX = 800
DUPLICATE_WINDOW = 7 * 86400


class Post(StatesGroup):
    district = State()
    rooms = State()
    price = State()
    pets = State()
    desc = State()
    photo = State()
    phone = State()


@router.message(Command("post"))
@router.message(F.text.in_(variants("btn_post")))
async def post_start(message: Message, state: FSMContext, db: Database, lang: str,
                     cfg: Config) -> None:
    await state.clear()
    n = await db.count_user_listings_since(message.from_user.id, int(time.time()) - 86400)
    if n >= cfg.daily_post_limit:
        await message.answer(t("post_limit", lang, n=n))
        return
    await state.set_state(Post.district)
    await message.answer(t("post_district", lang), reply_markup=districts_kb(lang, set(), "post:d:", False))


@router.callback_query(Post.district, F.data.startswith("post:d:"))
async def post_district(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    key = cb.data.split(":", 2)[2]
    if key not in DISTRICTS:
        await cb.answer()
        return
    await state.update_data(district=key)
    await state.set_state(Post.rooms)
    await cb.message.edit_text(t("post_rooms", lang), reply_markup=rooms_kb(lang, set(), "post:r:", False))
    await cb.answer()


@router.callback_query(Post.rooms, F.data.startswith("post:r:"))
async def post_rooms(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    n = int(cb.data.rsplit(":", 1)[1])
    await state.update_data(rooms=n)
    await state.set_state(Post.price)
    await cb.message.edit_text(t("post_price", lang))
    await cb.answer()


@router.message(Post.price, F.text)
async def post_price(message: Message, state: FSMContext, lang: str, cfg: Config) -> None:
    price = parse_price_input(message.text, cfg.amd_per_usd)
    if not price:
        await message.answer(t("price_bad", lang).replace("300-600", "450$"))
        return
    await state.update_data(price_amount=price.amount, currency=price.currency, price_usd=price.usd)
    await state.set_state(Post.pets)
    await message.answer(t("post_pets", lang), reply_markup=yes_no_kb(lang, "post:p:"))


@router.callback_query(Post.pets, F.data.startswith("post:p:"))
async def post_pets(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.update_data(pets=int(cb.data.rsplit(":", 1)[1]))
    await state.set_state(Post.desc)
    await cb.message.edit_text(t("post_desc", lang))
    await cb.answer()


@router.message(Post.desc, F.text)
async def post_desc(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text.strip()
    if len(text) > DESC_MAX:
        await message.answer(t("desc_long", lang, n=len(text)))
        return
    await state.update_data(description=text)
    await state.set_state(Post.photo)
    await message.answer(t("post_photo", lang), reply_markup=skip_kb(lang))


async def _ask_phone(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(Post.phone)
    await message.answer(t("post_phone", lang), reply_markup=phone_kb(lang))


@router.message(Post.photo, F.photo)
async def post_photo(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(photo_id=message.photo[-1].file_id)
    await _ask_phone(message, state, lang)


@router.callback_query(Post.photo, F.data == "post:skip")
async def post_skip_photo(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.update_data(photo_id=None)
    await cb.message.edit_reply_markup(reply_markup=None)
    await _ask_phone(cb.message, state, lang)
    await cb.answer()


@router.message(Post.phone, F.contact | F.text)
async def post_phone(message: Message, state: FSMContext, db: Database, lang: str,
                     bot: Bot) -> None:
    raw = message.contact.phone_number if message.contact else message.text
    phone = normalize_phone(raw or "")
    if not phone:
        await message.answer(t("phone_bad", lang))
        return

    uid = message.from_user.id
    paused = await db.is_paused(uid)
    menu = main_menu(lang, paused)
    if await db.is_blacklisted(phone):
        await state.clear()
        await message.answer(t("blacklisted", lang), reply_markup=menu)
        return

    data = await state.get_data()
    h = text_hash(f"{phone}|{data['district']}|{data['rooms']}|{round(data['price_usd'])}")
    if await db.is_duplicate(h, int(time.time()) - DUPLICATE_WINDOW):
        await state.clear()
        await message.answer(t("duplicate", lang), reply_markup=menu)
        return

    listing_id = await db.add_listing(
        source="bot", owner_id=uid, district=data["district"], rooms=data["rooms"],
        price_amount=data["price_amount"], currency=data["currency"], price_usd=data["price_usd"],
        pets=data["pets"], description=data["description"], phone=phone,
        photo_id=data.get("photo_id"), text_hash=h,
    )
    await state.clear()
    await message.answer(t("published", lang), reply_markup=menu)

    listing = await db.get_listing(listing_id)

    async def notify() -> None:
        n = await broadcast(bot, db, listing, exclude_user=uid)
        await bot.send_message(uid, t("sent_to", lang, n=n))

    spawn(notify())

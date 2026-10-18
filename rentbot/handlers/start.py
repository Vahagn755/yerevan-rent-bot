from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..db import Database
from ..keyboards import lang_kb, main_menu
from ..texts import LANGS, t, variants

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database, lang: str,
                    is_new_user: bool) -> None:
    await state.clear()
    paused = await db.is_paused(message.from_user.id)
    name = escape(message.from_user.first_name or "")
    await message.answer(t("welcome", lang, name=name), reply_markup=main_menu(lang, paused))
    if is_new_user:
        await message.answer(t("choose_lang", lang), reply_markup=lang_kb())


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t("help", lang))


@router.message(Command("cancel"))
@router.message(F.text.in_(variants("cancel")))
async def cmd_cancel(message: Message, state: FSMContext, db: Database, lang: str) -> None:
    await state.clear()
    paused = await db.is_paused(message.from_user.id)
    await message.answer(t("cancelled", lang), reply_markup=main_menu(lang, paused))


@router.message(Command("lang"))
@router.message(F.text.in_(variants("btn_lang")))
async def cmd_lang(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("choose_lang", lang), reply_markup=lang_kb())


@router.callback_query(F.data.startswith("lang:"))
async def on_lang(cb: CallbackQuery, db: Database) -> None:
    new_lang = cb.data.split(":", 1)[1]
    if new_lang not in LANGS:
        await cb.answer()
        return
    await db.set_lang(cb.from_user.id, new_lang)
    paused = await db.is_paused(cb.from_user.id)
    await cb.message.delete()
    await cb.message.answer(t("lang_set", new_lang), reply_markup=main_menu(new_lang, paused))
    await cb.answer()


@router.message(Command("pause"))
@router.message(F.text.in_(variants("btn_pause")))
async def cmd_pause(message: Message, state: FSMContext, db: Database, lang: str) -> None:
    await state.clear()
    await db.set_paused(message.from_user.id, True)
    await message.answer(t("paused", lang), reply_markup=main_menu(lang, True))


@router.message(Command("resume"))
@router.message(F.text.in_(variants("btn_resume")))
async def cmd_resume(message: Message, state: FSMContext, db: Database, lang: str) -> None:
    await state.clear()
    await db.set_paused(message.from_user.id, False)
    await message.answer(t("resumed", lang), reply_markup=main_menu(lang, False))

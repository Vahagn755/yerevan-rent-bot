from collections.abc import Mapping

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .districts import DISTRICTS, district_name
from .texts import t


def main_menu(lang: str, paused: bool) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text=t("btn_filter", lang)), KeyboardButton(text=t("btn_post", lang))],
            [KeyboardButton(text=t("btn_my", lang)),
             KeyboardButton(text=t("btn_resume" if paused else "btn_pause", lang))],
            [KeyboardButton(text=t("btn_lang", lang))],
        ],
    )


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇦🇲 Հայերեն", callback_data="lang:hy"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    ]])


def filter_menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, data in (("f_price", "flt:price"), ("f_rooms", "flt:rooms"),
                      ("f_districts", "flt:districts"), ("f_pets", "flt:pets"),
                      ("f_reset", "flt:reset"), ("f_done", "flt:done")):
        b.button(text=t(key, lang), callback_data=data)
    b.adjust(2)
    return b.as_markup()


def _mark(selected: bool, text: str) -> str:
    return f"✅ {text}" if selected else text


def rooms_kb(lang: str, selected: set[str], prefix: str, back: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for n in range(1, 6):
        label = "5+" if n == 5 else str(n)
        b.button(text=_mark(str(n) in selected, label), callback_data=f"{prefix}{n}")
    if back:
        b.button(text=t("back", lang), callback_data="flt:menu")
    b.adjust(5, 1)
    return b.as_markup()


def districts_kb(lang: str, selected: set[str], prefix: str, back: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key in DISTRICTS:
        b.button(text=_mark(key in selected, district_name(key, lang)), callback_data=f"{prefix}{key}")
    if back:
        b.button(text=t("back", lang), callback_data="flt:menu")
    b.adjust(2)
    return b.as_markup()


def yes_no_kb(lang: str, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("yes", lang), callback_data=f"{prefix}1"),
        InlineKeyboardButton(text=t("no", lang), callback_data=f"{prefix}0"),
    ]])


def skip_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("skip", lang), callback_data="post:skip"),
    ]])


def phone_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True,
        keyboard=[[KeyboardButton(text=t("share_contact", lang), request_contact=True)],
                  [KeyboardButton(text=t("cancel", lang))]],
    )


def card_kb(lang: str, listing: Mapping) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(text=t("rep_agent", lang), callback_data=f"rep:agent:{listing['id']}"),
        InlineKeyboardButton(text=t("rep_fake", lang), callback_data=f"rep:fake:{listing['id']}"),
    ]]
    if listing["link"]:
        rows.insert(0, [InlineKeyboardButton(text=t("card_source", lang), url=listing["link"])])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def own_listing_kb(lang: str, listing_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("rented", lang), callback_data=f"own:done:{listing_id}"),
    ]])

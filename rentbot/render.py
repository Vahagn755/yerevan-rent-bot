"""Turn database rows into message text."""
from collections.abc import Mapping
from html import escape

from .districts import district_name
from .matching import parse_set
from .parser import format_phone
from .texts import t

DESC_LIMIT = 600


def format_price(listing: Mapping) -> str:
    amount, cur, usd = listing["price_amount"], listing["currency"], listing["price_usd"]
    if amount is None:
        return "—"
    if cur == "AMD":
        return f"{amount:,.0f} ֏ (≈ ${usd:,.0f})".replace(",", " ")
    return f"${amount:,.0f}".replace(",", " ")


def format_card(listing: Mapping, lang: str) -> str:
    head = []
    if listing["rooms"]:
        head.append(t("card_rooms", lang, n=listing["rooms"]))
    if listing["district"]:
        head.append(district_name(listing["district"], lang))
    lines = [f"🏠 <b>{' · '.join(head) or '—'}</b>", f"💰 {format_price(listing)}"]
    if listing["pets"] == 1:
        lines.append(t("card_pets_yes", lang))
    elif listing["pets"] == 0:
        lines.append(t("card_pets_no", lang))

    desc = (listing["description"] or "").strip()
    if desc:
        if len(desc) > DESC_LIMIT:
            desc = desc[:DESC_LIMIT].rstrip() + "…"
        lines += ["", escape(desc)]
    if listing["phone"] and listing["source"] == "bot":
        lines += ["", f"📞 {format_phone(listing['phone'])}"]
    if listing["source"] == "bot":
        lines.append(t("card_owner", lang))
    return "\n".join(lines)


def _price_range(flt: Mapping, lang: str) -> str:
    lo, hi = flt["price_min"], flt["price_max"]
    if lo is None and hi is None:
        return t("any", lang)
    if lo is None:
        return t("upto", lang, v=f"{hi:.0f}")
    if hi is None:
        return t("from", lang, v=f"{lo:.0f}")
    return f"${lo:.0f}–{hi:.0f}"


def format_filter(flt: Mapping, lang: str) -> str:
    rooms = sorted(parse_set(flt["rooms"]))
    districts = sorted(parse_set(flt["districts"]))
    return t(
        "filter_title", lang,
        price=_price_range(flt, lang),
        rooms=", ".join("5+" if r == "5" else r for r in rooms) or t("any", lang),
        districts=", ".join(district_name(d, lang) for d in districts) or t("any", lang),
        pets=t("pets_need", lang) if flt["pets"] else t("any", lang),
    )
